from unittest.mock import Mock
from pathlib import Path
import pytest
from services.saves.policy import SavePolicy
from services.emulators.session import EmulatorSession
from services.retroarch.session_config import RetroArchSessionConfig


@pytest.fixture
def session():
    adapters = [Mock(), Mock()]
    for adapter in adapters:
        adapter.process_running.return_value = False
    return EmulatorSession(*adapters)


def test_default_policy_never_creates_or_changes_storage(tmp_path):
    policy = SavePolicy(tmp_path / 'managed')
    assert policy.settings('edition', 'snes9x', 'Game.sfc') == {}
    assert policy.settings('', 'snes9x', 'Game.sfc') == {}
    assert not policy.root.exists()


def test_opt_in_separates_editions_and_cores(tmp_path, session):
    policy = SavePolicy(tmp_path / 'managed')
    a = policy.enable(session, 'edition-a', 'snes9x', 'Game.sfc')
    b = policy.enable(session, 'edition-b', 'snes9x', 'Game.sfc')
    c = policy.enable(session, 'edition-a', 'mesen', 'Game.sfc')
    assert len({x['savefile_directory'] for x in (a, b, c)}) == 3
    assert a['savefiles_in_content_dir'] == 'false'
    assert a['sort_savefiles_enable'] == 'false'
    assert policy.settings('edition-a', '/cores/snes9x_libretro.so', 'Game.sfc') == a


def test_move_keeps_route_but_rename_requires_review(tmp_path, session):
    policy = SavePolicy(tmp_path)
    route = policy.enable(session, 'edition', 'snes9x', '/one/Game.sfc')
    assert policy.settings('edition', 'snes9x', '/two/Game.sfc') == route
    with pytest.raises(ValueError, match='filename or identity changed'):
        policy.settings('edition', 'snes9x', '/two/Renamed.sfc')


def test_no_archive_or_unregistered_guess(tmp_path, session):
    policy = SavePolicy(tmp_path)
    for identity, rom in [('', 'Game.sfc'), ('edition', 'Game.zip')]:
        with pytest.raises(ValueError):
            policy.enable(session, identity, 'snes9x', rom)
    assert list(tmp_path.iterdir()) == []


def test_owned_process_rejects_policy_change(tmp_path, session):
    session.snes9x.process_running.return_value = True
    with pytest.raises(ValueError, match='Quit'):
        SavePolicy(tmp_path).enable(session, 'edition', 'snes9x', 'Game.sfc')
    assert list(tmp_path.iterdir()) == []


def test_session_save_config_does_not_change_presentation_baseline(tmp_path, session):
    values = SavePolicy(tmp_path / 'saves').enable(session, 'edition', 'snes9x', 'Game.sfc')
    runtime = RetroArchSessionConfig(tmp_path / 'runtime')
    filename = runtime.create(save_values=values)
    text = Path(filename).read_text()
    assert text.startswith(runtime.BASELINE)
    assert f'savefile_directory = "{values["savefile_directory"]}"' in text
    runtime.cleanup()
    assert not Path(filename).exists()


def test_disable_and_reenable_preserve_both_storage_sets(tmp_path, session):
    policy = SavePolicy(tmp_path / 'managed')
    legacy = tmp_path / 'legacy.srm'
    legacy.write_bytes(b'legacy')
    values = policy.enable(session, 'edition', 'snes9x', 'Game.sfc')
    save = Path(values['savefile_directory']) / 'Game.srm'
    save.write_bytes(b'isolated')
    policy.disable(session, 'edition', 'snes9x', 'Game.sfc')
    assert policy.settings('edition', 'snes9x', 'Game.sfc') == {}
    assert save.read_bytes() == b'isolated'
    assert legacy.read_bytes() == b'legacy'
    assert policy.enable(session, 'edition', 'snes9x', 'Game.sfc') == values
    assert save.read_bytes() == b'isolated'


def test_managed_subdirectory_symlink_is_rejected(tmp_path, session):
    policy = SavePolicy(tmp_path / 'managed')
    values = policy.enable(session, 'edition', 'snes9x', 'Game.sfc')
    folder = Path(values['savefile_directory'])
    folder.rmdir()
    folder.symlink_to(tmp_path)
    with pytest.raises(ValueError, match='symbolic link'):
        policy.settings('edition', 'snes9x', 'Game.sfc')


def test_save_directives_cannot_override_presentation(tmp_path):
    runtime = RetroArchSessionConfig(tmp_path)
    with pytest.raises(ValueError, match='Unsupported save'):
        runtime.create(save_values={'video_aspect_ratio': '2'})
    assert list(tmp_path.iterdir()) == []
