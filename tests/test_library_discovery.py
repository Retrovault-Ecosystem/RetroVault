"""USQE 3: discovery must not publish state or mutate live game objects."""
import json
from pathlib import Path
import pytest
from services.library.discovery import DiscoveryControl, DiscoveryCancelled
from controllers.library_controller import LibraryController


@pytest.fixture
def controller(tmp_path, monkeypatch):
    for key in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME']:
        monkeypatch.setenv(key,str(tmp_path/key))
    roms=tmp_path/'roms';roms.mkdir();(roms/'Alpha.nes').write_bytes(b'fixture')
    from config import ConfigWriter
    ConfigWriter().update({'library':{'sources':[dict(id='test',name='Test',type='local',enabled=True,path=str(roms))]}})
    return LibraryController(load_on_start=False)


def durable(controller):
    root=controller.library.identity_registry.path.parent
    return {str(p):p.read_bytes() for p in root.rglob('*') if p.is_file()}


def test_prepare_is_detached_and_cancel_never_writes(controller):
    before=durable(controller)
    request=controller.discovery_request('refresh')
    control=DiscoveryControl()
    result=controller.prepare_discovery(request,control)
    assert controller.get_games()==[] and durable(controller)==before
    control.cancel()
    with pytest.raises(DiscoveryCancelled):control.check()
    assert durable(controller)==before
    assert len(result.visible)==1


def test_publish_preserves_current_favorites_and_identity(controller):
    result=controller.prepare_discovery(controller.discovery_request('refresh'),DiscoveryControl())
    controller.publish_discovery(result)
    game=controller.get_games()[0]
    result=controller.prepare_discovery(controller.discovery_request('refresh'),DiscoveryControl())
    controller.set_favorite(game,True)
    controller.publish_discovery(result)
    assert controller.get_games()[0] is game and game.favorite


def test_changed_sources_reject_result_before_write(controller):
    result=controller.prepare_discovery(controller.discovery_request('refresh'),DiscoveryControl())
    from config import ConfigWriter
    ConfigWriter().update({'library':{'sources':[]}})
    before=durable(controller)
    with pytest.raises(ValueError,match='changed'):
        controller.publish_discovery(result)
    assert controller.get_games()==[] and durable(controller)==before


def test_missing_source_does_not_replace_library(controller):
    controller.publish_discovery(controller.prepare_discovery(controller.discovery_request('refresh'),DiscoveryControl()))
    games=list(controller.get_games())
    path=Path(games[0].rom);path.unlink();path.parent.rmdir()
    with pytest.raises((ValueError,OSError)):
        controller.prepare_discovery(controller.discovery_request('refresh'),DiscoveryControl())
    assert controller.get_games()==games


def test_cancel_during_hashing_does_not_write(controller):
    before=durable(controller)
    control=DiscoveryControl()
    def progress(event):
        if event.phase=='Hashing':control.cancel()
    control.progress=progress
    with pytest.raises(DiscoveryCancelled):
        controller.prepare_discovery(controller.discovery_request('refresh'),control)
    assert durable(controller)==before


def test_import_failure_reports_saved_source_without_publishing(controller, tmp_path, monkeypatch):
    other=tmp_path/'other';other.mkdir();(other/'Beta.nes').write_bytes(b'new')
    result=controller.prepare_discovery(controller.discovery_request('import',str(other)),DiscoveryControl())
    monkeypatch.setattr(controller.library.identity_registry,'commit',lambda data: (_ for _ in ()).throw(OSError('blocked')))
    with pytest.raises(RuntimeError,match='may already be saved'):
        controller.publish_discovery(result)
    assert controller.get_games()==[]
    assert any(s['path']==str(other) for s in controller.import_source_store.sources())


def test_import_retry_preserves_editions_and_latest_state(controller, tmp_path):
    controller.publish_discovery(controller.prepare_discovery(controller.discovery_request('refresh'),DiscoveryControl()))
    first=controller.get_games()[0]
    other=tmp_path/'other';other.mkdir();(other/'Beta.nes').write_bytes(b'new')
    result=controller.prepare_discovery(controller.discovery_request('import',str(other)),DiscoveryControl())
    controller.set_favorite(first,True)
    report=controller.publish_discovery(result)
    assert report['added_count']==1 and len(controller.get_games())==2
    assert first in controller.get_games() and first.favorite
    result=controller.prepare_discovery(controller.discovery_request('import',str(other)),DiscoveryControl())
    report=controller.publish_discovery(result)
    assert report['added_count']==0 and report['skipped_count']==1


def test_walk_error_fails_without_publication(controller, monkeypatch):
    import services.library.scanner as scanner
    def walk(root, onerror=None):
        onerror(PermissionError('unreadable subtree'))
        yield
    monkeypatch.setattr(scanner.os,'walk',walk)
    before=durable(controller)
    with pytest.raises(PermissionError):
        controller.prepare_discovery(controller.discovery_request('refresh'),DiscoveryControl())
    assert durable(controller)==before


def test_archive_cancellation_reaps_only_owned_listing(tmp_path):
    import subprocess, sys
    from threading import Timer
    from services.retroarch.archive_runtime import ArchiveRuntime
    script=tmp_path/'listing';script.write_text('#!'+sys.executable+'\nimport time\ntime.sleep(20)\n');script.chmod(0o755)
    archive=tmp_path/'test.7z';archive.write_bytes(b'fixture')
    unrelated=subprocess.Popen([sys.executable,'-c','import time; time.sleep(20)'])
    control=DiscoveryControl();timer=Timer(.1,control.cancel);timer.start()
    try:
        with pytest.raises(DiscoveryCancelled):ArchiveRuntime(executable=str(script)).preferred_member(archive,control=control)
        assert unrelated.poll() is None
    finally:
        timer.join();unrelated.terminate();unrelated.wait(timeout=2)


def test_archive_cache_is_not_flushed_by_preparation(controller,tmp_path,monkeypatch):
    from services.retroarch.archive_runtime import ArchiveRuntime
    from config.paths import cache_home
    rom=Path(controller.import_source_store.sources()[0]['path'])/'Box.7z';rom.write_bytes(b'fixture')
    monkeypatch.setattr(ArchiveRuntime,'preferred_member',lambda *a,**kw:'Box.nes')
    result=controller.prepare_discovery(controller.discovery_request('refresh'),DiscoveryControl())
    cache=cache_home()/'retrovault/archive-scan.json'
    assert not cache.exists()
    controller.publish_discovery(result)
    assert cache.exists()


def test_identity_change_rejects_prepared_result(controller):
    request=controller.discovery_request('refresh')
    result=controller.prepare_discovery(request,DiscoveryControl())
    controller.library.identity_registry.commit(result.registry_data)
    before=durable(controller)
    with pytest.raises(ValueError,match='registry changed'):controller.publish_discovery(result)
    assert durable(controller)==before and controller.get_games()==[]


def test_display_preferences_do_not_invalidate_result(controller):
    from config import ConfigWriter
    result=controller.prepare_discovery(controller.discovery_request('refresh'),DiscoveryControl())
    ConfigWriter().update({'library':{'display':{'opening_view':'compact'}}})
    controller.publish_discovery(result)
    assert len(controller.get_games())==1


def test_import_source_write_failure_preserves_registry_and_live_state(controller,tmp_path,monkeypatch):
    other=tmp_path/'other';other.mkdir();(other/'new.nes').write_bytes(b'new')
    result=controller.prepare_discovery(controller.discovery_request('import',str(other)),DiscoveryControl())
    before=durable(controller)
    monkeypatch.setattr(controller.import_source_store,'persist_directory',lambda *a: (_ for _ in ()).throw(OSError('blocked')))
    with pytest.raises(RuntimeError):controller.publish_discovery(result)
    assert durable(controller)==before and not controller.get_games()


def test_progress_is_bounded_and_cancel_checked_even_when_throttled():
    events=[];control=DiscoveryControl(events.append)
    for i in range(5000):
        control.report('Scanning');control.report('Inspecting archive',0)
    assert len(events)<50
    control.cancel()
    with pytest.raises(DiscoveryCancelled):control.report('Scanning')


def test_cached_and_uncached_archives_share_discovery_result(controller,monkeypatch):
    from services.retroarch.archive_runtime import ArchiveRuntime
    rom=Path(controller.import_source_store.sources()[0]['path'])/'Box.7z';rom.write_bytes(b'fixture')
    calls=[]
    def member(*a,**kw):calls.append(1);return 'Box.nes'
    monkeypatch.setattr(ArchiveRuntime,'preferred_member',member)
    first=controller.prepare_discovery(controller.discovery_request('refresh'),DiscoveryControl())
    controller.publish_discovery(first)
    second=controller.prepare_discovery(controller.discovery_request('refresh'),DiscoveryControl())
    assert len(calls)==1
    assert [(g.name,g.platform) for g in first.visible]==[(g.name,g.platform) for g in second.visible]


def test_overlapping_sources_preserve_one_physical_identity(controller):
    from config import ConfigWriter
    sources=controller.import_source_store.sources()
    ConfigWriter().update({'library':{'sources':[sources[0],{**sources[0],'id':'overlap'}]}})
    result=controller.prepare_discovery(controller.discovery_request('refresh'),DiscoveryControl())
    controller.publish_discovery(result)
    assert len(controller.library._physical_games)==1


def test_object_preparation_failure_does_not_partially_mutate_live_snapshot(controller,monkeypatch):
    root=Path(controller.import_source_store.sources()[0]['path'])
    (root/'Beta.nes').write_bytes(b'second')
    controller.publish_discovery(controller.prepare_discovery(controller.discovery_request('refresh'),DiscoveryControl()))
    games=list(controller.get_games());before=[vars(g).copy() for g in games]
    prepared=controller.prepare_discovery(controller.discovery_request('refresh'),DiscoveryControl())
    prepared.visible[0].year=2000;prepared.visible[1].year=2001
    import services.library.library_service as module
    original=module.deepcopy
    def fail(value):
        if value==2001:raise ValueError('copy failed')
        return original(value)
    monkeypatch.setattr(module,'deepcopy',fail)
    with pytest.raises(RuntimeError,match='copy failed'):controller.publish_discovery(prepared)
    assert controller.get_games()==games
    assert [vars(g) for g in games]==before
