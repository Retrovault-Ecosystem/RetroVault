import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
from threading import Event
from time import monotonic
import pytest
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication
from services.library.scanner import RomScanner


@pytest.fixture(scope='module')
def app():return QApplication.instance() or QApplication([])


def wait(app,predicate):
    deadline=monotonic()+4
    while not predicate() and monotonic()<deadline:
        app.processEvents();QTest.qWait(5)
    assert predicate()


@pytest.fixture
def window(app,tmp_path,monkeypatch):
    for key in ['XDG_CONFIG_HOME','XDG_DATA_HOME','XDG_CACHE_HOME']:monkeypatch.setenv(key,str(tmp_path/key))
    import ui.main_window as main
    bundle=tmp_path/'rvdb.json';bundle.write_text('{"nodes":{},"edges":{}}')
    monkeypatch.setattr(main,'RVDB_BUNDLE',bundle)
    source=tmp_path/'roms';source.mkdir()
    (source/'ZZZ.nes').write_bytes(b'NES fixture');(source/'AAA.md').write_bytes(b'MD fixture')
    from config import ConfigWriter
    ConfigWriter().update({'library':{'sources':[dict(id='local',name='Fixture',type='local',enabled=True,path=str(source))]},
                          'paths':{key:{'directory':str(tmp_path/key)} for key in ['artwork','overlays','shaders']}})
    widget=main.MainWindow()
    yield widget
    widget.close();wait(app,lambda:not widget.discovery_jobs.busy);widget.close();widget.deleteLater();app.processEvents()


def test_startup_keeps_original_service_order(window,app):
    page=window.pages.pages['Library']
    assert page.all_games==[]
    wait(app,lambda:len(page.all_games)==2)
    assert [g.name for g in page.compact_view.games]==['ZZZ','AAA']
    page.refresh()
    assert [g.name for g in page.compact_view.games]==['AAA','ZZZ']


def test_current_browsing_state_survives_refresh(window,app,monkeypatch):
    page=window.pages.pages['Library'];wait(app,lambda:len(page.all_games)==2)
    selected=page.all_games[0];page.details.show_game(selected)
    started=Event();release=Event();original=RomScanner.scan
    def scan(scanner,source,**kwargs):
        started.set()
        while not release.wait(.01):kwargs['control'].check()
        return original(scanner,source,**kwargs)
    monkeypatch.setattr(RomScanner,'scan',scan)
    page.reload_library();wait(app,started.is_set)
    page.toolbar.search.setText('ZZZ');page.toolbar.view_selector._select_compact()
    page.set_favorite(selected,True)
    assert len(page.all_games)==2
    release.set();wait(app,lambda:not window.discovery_jobs.busy)
    assert page.details.current_game is selected and selected.favorite
    assert page.toolbar.search.text()=='ZZZ'
    assert page.library_view_stack.currentWidget() is page.compact_view
    assert page.compact_view.list.currentRow()==0


def test_close_waits_for_discovery_ownership(window,app,monkeypatch):
    page=window.pages.pages['Library'];wait(app,lambda:len(page.all_games)==2)
    started=Event()
    def scan(scanner,source,**kwargs):
        started.set()
        while True:
            kwargs['control'].check();Event().wait(.01)
    monkeypatch.setattr(RomScanner,'scan',scan)
    page.reload_library();wait(app,started.is_set)
    window.close();wait(app,lambda:not window.discovery_jobs.busy)
    assert window.discovery_jobs._worker is None


def test_scroll_preferences_and_recent_order_survive_publication(window,app,monkeypatch):
    from pathlib import Path
    from config.library_preferences import LibraryPreferences
    page=window.pages.pages['Library'];wait(app,lambda:len(page.all_games)==2)
    root=Path(page.all_games[0].rom).parent
    for index in range(100):(root/f'Game {index}.nes').write_bytes(str(index).encode())
    page.reload_library();wait(app,lambda:not window.discovery_jobs.busy)
    page.apply_display_preferences(LibraryPreferences('compact','large','year'))
    window.resize(1400,800);window.show();app.processEvents()
    page.compact_view.list.verticalScrollBar().setValue(25)
    position=page.compact_view.list.verticalScrollBar().value()
    assert position>0
    page.reload_library();wait(app,lambda:not window.discovery_jobs.busy)
    app.processEvents()
    assert page.compact_view.list.verticalScrollBar().value()==position
    assert page.grid.card_size=='large' and page.toolbar.sort.currentText()=='Year'
    assert page.library_view_stack.currentWidget() is page.compact_view
    controller=window.discovery_jobs.controller
    first,last=page.all_games[0],page.all_games[-1]
    controller.record_played(first);controller.record_played(last)
    page.toolbar.recent_only.setChecked(True)
    page.reload_library();wait(app,lambda:not window.discovery_jobs.busy)
    assert [g.local_file_id for g in page.compact_view.games]==[last.local_file_id,first.local_file_id]


def test_settings_source_change_supersedes_worker(window,app,monkeypatch):
    from config import ConfigWriter
    page=window.pages.pages['Library'];wait(app,lambda:len(page.all_games)==2)
    started=Event();original=RomScanner.scan
    def scan(scanner,source,**kwargs):
        started.set()
        while True:
            kwargs['control'].check();Event().wait(.01)
    monkeypatch.setattr(RomScanner,'scan',scan)
    page.reload_library();wait(app,started.is_set)
    ConfigWriter().update({'library':{'sources':[]}})
    window.pages.pages['Settings'].library_sources_changed.emit()
    wait(app,lambda:not window.discovery_jobs.busy)
    assert page.all_games==() or page.all_games==[]
