"""Synthetic Qt fixtures exercise browsing preferences without real user state."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from types import SimpleNamespace
import pytest
from PyQt6.QtWidgets import QApplication
from config.loader import ConfigLoader
from config.library_preferences import LibraryPreferences
from ui.library.gallery import GalleryView
from ui.pages.settings_page import SettingsPage


@pytest.fixture(scope='module')
def app():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def games():
    return [SimpleNamespace(name=name, platform='NES', year=year, core='', rom=f'/synthetic/{i}.nes',
                            local_file_id=f'fixture-{i}', artwork='', favorite=True, variants=[])
            for i, (name, year) in enumerate([('Zulu', 1992), ('Alpha', None), ('Beta', 1990), ('Equal', 1990)])]


@pytest.fixture
def page(app, tmp_path):
    defaults = tmp_path / 'defaults.yaml'
    defaults.write_text('retroarch:\n  executable: retroarch\n')
    widget = SettingsPage(ConfigLoader(defaults, tmp_path / 'runtime.json'))
    yield widget
    widget.close(); widget.deleteLater(); app.processEvents()


def names(view):
    return [g.name for g in view.compact_view.games]


def test_startup_compatibility_and_restoration(app, games):
    view = GalleryView(games)
    assert names(view) == ['Zulu', 'Alpha', 'Beta', 'Equal']
    assert view.library_view_stack.currentWidget() is view.grid
    prefs = LibraryPreferences('compact', 'large', 'year')
    other = GalleryView(games, display_preferences=prefs)
    assert names(other) == ['Alpha', 'Beta', 'Equal', 'Zulu']
    assert other.toolbar.view_selector.compact.isChecked()
    assert other.grid.layout.itemAt(0).widget().width() == 230
    view.close();other.close()


def test_preview_cancel_reset_apply_restart(page, app, games):
    view = GalleryView(games)
    page.library_preferences_previewed.connect(view.apply_display_preferences)
    page.library_preferences_applied.connect(view.apply_display_preferences)
    page.library_preference_controls['opening_view'].setCurrentIndex(1)
    page.library_preference_controls['card_size'].setCurrentIndex(2)
    assert view.library_view_stack.currentWidget() is view.details_view
    assert not page.config_loader.runtime_file.exists()
    page.apply_library_preferences()
    saved = page.config_loader.runtime_file.read_bytes()
    page.reset_library_preferences()
    assert view.library_view_stack.currentWidget() is view.grid
    page.cancel_library_preferences()
    assert view.library_view_stack.currentWidget() is view.details_view
    assert page.config_loader.runtime_file.read_bytes() == saved
    page.reset_library_preferences();page.apply_library_preferences()
    assert LibraryPreferences.from_config(page.config_loader.load()) == LibraryPreferences()
    view.close()


def test_sort_preview_preserves_context_and_recent(app, games):
    view = GalleryView(games, recent_provider=lambda: ['fixture-0', 'fixture-2', 'fixture-1'])
    selected = games[2]
    view.details.show_game(selected)
    view.toolbar.search.setText('a')
    view.toolbar.favorites_only.setChecked(True)
    view.apply_display_preferences(LibraryPreferences('details', 'small', 'year'))
    assert view.details.current_game is selected
    assert view.details_view.games[view.details_view.list.currentRow()] is selected
    assert view.toolbar.search.text() == 'a'
    view.toolbar.search.clear()
    view.toolbar.recent_only.setChecked(True)
    view.apply_display_preferences(LibraryPreferences(normal_sort='name'))
    assert names(view) == ['Zulu', 'Beta', 'Alpha']
    view.close()


def test_card_size_updates_existing_cards(app, games):
    view = GalleryView(games)
    card = view.grid.layout.itemAt(0).widget()
    for size, width, cover in [('small',170,(140,175)), ('large',230,(200,250)), ('default',190,(160,200))]:
        view.apply_display_preferences(LibraryPreferences(card_size=size))
        assert view.grid.layout.itemAt(0).widget() is card
        assert card.width() == width
        assert (card.cover.width(),card.cover.height()) == cover
    view.close()


def test_unrelated_population_keeps_draft_and_session_changes_do_not_edit_it(page, app, games):
    view = GalleryView(games)
    page.library_preferences_previewed.connect(view.apply_display_preferences)
    page.library_preference_controls['opening_view'].setCurrentIndex(2)
    page._populate()
    assert page.library_preference_controls['opening_view'].currentData() == 'compact'
    view.toolbar.view_selector._select_details()
    view.toolbar.sort.setCurrentText('Year')
    assert page.library_preference_controls['opening_view'].currentData() == 'compact'
    assert page.library_preference_controls['normal_sort'].currentData() == 'name'
    page.cancel_library_preferences()
    assert view.library_view_stack.currentWidget() is view.grid
    assert view.toolbar.sort.currentText() == 'Name'
    view.close()


def test_failed_save_keeps_unsaved_preview(page, app, games, monkeypatch):
    view = GalleryView(games)
    page.library_preferences_previewed.connect(view.apply_display_preferences)
    page.library_preference_controls['opening_view'].setCurrentIndex(2)
    monkeypatch.setattr(page.settings_service.config_writer, 'update', lambda *a: (_ for _ in ()).throw(OSError('blocked')))
    page.apply_library_preferences()
    assert 'not saved' in page.library_preferences_status.text().lower()
    assert view.library_view_stack.currentWidget() is view.compact_view
    page.cancel_library_preferences()
    assert view.library_view_stack.currentWidget() is view.grid
    view.close()


@pytest.mark.parametrize('mode', ['gallery','details','compact'])
def test_scroll_and_identity_survive_sort_and_size(app, games, mode):
    many = [SimpleNamespace(**{**vars(games[i % 4]), 'name': f'Game {199-i:03}',
                             'rom': f'/synthetic/{i}.nes', 'local_file_id': f'item-{i}'}) for i in range(200)]
    view = GalleryView(many, display_preferences=LibraryPreferences(mode))
    view.resize(1400, 700);view.show();app.processEvents()
    selected = many[50]
    view.details.show_game(selected)
    widget = {'gallery': view.grid.scroll, 'details': view.details_view.list, 'compact': view.compact_view.list}[mode]
    widget.verticalScrollBar().setValue(120)
    before = widget.verticalScrollBar().value()
    view.apply_display_preferences(LibraryPreferences(mode, 'large', 'year'))
    app.processEvents()
    assert view.details.current_game is selected
    assert widget.verticalScrollBar().value() == min(before,widget.verticalScrollBar().maximum())
    for child in [view.details_view,view.compact_view]:
        assert child.games[child.list.currentRow()].local_file_id == selected.local_file_id
    view.apply_display_preferences(LibraryPreferences(mode, 'small', 'name'));app.processEvents()
    assert widget.verticalScrollBar().value() == min(before,widget.verticalScrollBar().maximum())
    view.close()


@pytest.mark.parametrize('size,expected', [('small',(170,140,175)),('default',(190,160,200)),('large',(230,200,250))])
@pytest.mark.parametrize('width', [640, 1500])
def test_card_layout_artwork_edges(app, tmp_path, games, size, expected, width):
    from PyQt6.QtGui import QImage, QColor
    from ui.library.widgets.game_grid import GameGrid
    fixtures = []
    for i, (w,h) in enumerate([(600,150),(150,600)]):
        path=tmp_path / f'{i}.png'
        image=QImage(w,h,QImage.Format.Format_RGB32);image.fill(QColor('blue'));image.save(str(path))
        fixtures.append(str(path))
    invalid=tmp_path/'invalid.png';invalid.write_text('not an image')
    fixtures += [str(tmp_path/'missing.png'),str(invalid),'']
    items=[SimpleNamespace(**{**vars(games[0]),'artwork':art,'name':'A very long game title that must remain bounded',
                             'variants':[1,2,3]}) for art in fixtures]
    grid=GameGrid(items,card_size=size);grid.resize(width,600);grid.show();app.processEvents()
    assert grid.layout.columnCount()==5
    for i in range(5):
        card=grid.layout.itemAt(i).widget()
        assert (card.width(),card.cover.width(),card.cover.height()) == expected
        assert card.edition_count.text()=='3 Editions'
        assert card.edition_count.isVisible()
        if i<2:
            pixmap=card.cover.pixmap()
            assert pixmap.width()<=expected[1] and pixmap.height()<=expected[2]
            ratio=4 if i==0 else .25
            assert abs(pixmap.width()/pixmap.height()-ratio)<.1
        else:
            assert card.cover.text()=='🎮'
    grid.set_card_size('small');grid.set_card_size('large');grid.set_card_size('default')
    assert grid.layout.itemAt(0).widget().cover.pixmap().width()==160
    grid.close()


def test_empty_library_and_multiple_changes(app):
    view=GalleryView([])
    for mode in ['compact','details','gallery']:
        for size in ['small','large','default']:
            view.apply_display_preferences(LibraryPreferences(mode,size,'year'))
            assert view.grid.layout.count()==0
    view.close()


def test_saved_reread_warning_sets_cancel_baseline(page, monkeypatch):
    original=page.config_loader.load
    calls=0
    def load():
        nonlocal calls
        calls+=1
        if calls==2:
            raise OSError('read blocked')
        return original()
    page.library_preference_controls['opening_view'].setCurrentIndex(2)
    monkeypatch.setattr(page.config_loader,'load',load)
    page.apply_library_preferences()
    assert 'saved' in page.library_preferences_status.text()
    assert 'Unable to refresh' in page.library_preferences_status.text()
    page.reset_library_preferences();page.cancel_library_preferences()
    assert page.library_preference_controls['opening_view'].currentData()=='compact'


def test_main_window_real_wiring_and_restart(app, tmp_path, monkeypatch):
    # Real composition, empty sources and isolated roots: no user Library scan.
    import json
    for key,folder in [('XDG_CONFIG_HOME','config'),('XDG_DATA_HOME','data'),('XDG_CACHE_HOME','cache')]:
        monkeypatch.setenv(key,str(tmp_path/folder))
    runtime=tmp_path/'config/retrovault/runtime.json';runtime.parent.mkdir(parents=True)
    runtime.write_text(json.dumps({'library':{'sources':[]},'paths':{
        key:{'directory':str(tmp_path/key)} for key in ['overlays','shaders','artwork']}}))
    from ui.main_window import MainWindow
    window=MainWindow()
    settings=window.pages.pages['Settings'];library=window.pages.pages['Library']
    settings.library_preference_controls['opening_view'].setCurrentIndex(2)
    settings.library_preference_controls['card_size'].setCurrentIndex(2)
    assert library.library_view_stack.currentWidget() is library.compact_view
    window.pages.show_page('Library');window.pages.show_page('Settings')
    assert settings.library_preference_controls['card_size'].currentData()=='large'
    settings.apply_library_preferences()
    settings.library_preference_controls['opening_view'].setCurrentIndex(1)
    window.close();window.deleteLater();app.processEvents()
    restarted=MainWindow()
    restored=restarted.pages.pages['Library']
    assert restored.library_view_stack.currentWidget() is restored.compact_view
    assert restored.grid.card_size=='large'
    restarted.close();restarted.deleteLater();app.processEvents()


def test_candidate_title_readability_and_default_compatibility(app, games):
    from ui.library.widgets.game_card import GameCard
    game=SimpleNamespace(**{**vars(games[0]), 'name':'An Extremely Long Game Title That Cannot Fit'})
    card=GameCard(game);card.show();app.processEvents()
    assert card.title.text()==game.name
    for size in ['small','large']:
        card.set_card_size(size);app.processEvents()
        assert card.title.text().endswith('…')
        assert card.title.toolTip()==game.name
    card.set_card_size('default');app.processEvents()
    assert card.title.text()==game.name and card.title.toolTip()==''
    card.close()


def test_keyboard_and_repeated_cancel_preserve_user_selection(page, app, games):
    from PyQt6.QtTest import QTest
    from PyQt6.QtCore import Qt
    view=GalleryView(games)
    page.library_preferences_previewed.connect(view.apply_display_preferences)
    page.show();app.processEvents()
    control=page.library_preference_controls['opening_view']
    page.settings_scroll.ensureWidgetVisible(control)
    control.setFocus();QTest.keyClick(control,Qt.Key.Key_Down)
    assert control.currentData()=='details'
    QTest.keyClick(control,Qt.Key.Key_Tab)
    assert page.library_preference_controls['card_size'].hasFocus()
    view.details.show_game(games[1])
    view.toolbar.search.setText('Alpha')
    page.cancel_library_preferences();page.cancel_library_preferences()
    assert view.details.current_game is games[1]
    assert view.toolbar.search.text()=='Alpha'
    view.close()


def test_normal_filters_sort_and_ties(app, games):
    view=GalleryView(games)
    view.toolbar.system_filter.setCurrentText('NES')
    view.toolbar.favorites_only.setChecked(True)
    view.apply_display_preferences(LibraryPreferences(normal_sort='year'))
    assert names(view)==['Alpha','Beta','Equal','Zulu']
    view.apply_display_preferences(LibraryPreferences(normal_sort='name'))
    assert names(view)==['Alpha','Beta','Equal','Zulu']
    view.toolbar.search.setText('Zulu')
    view.apply_display_preferences(LibraryPreferences('compact','large','year'))
    assert names(view)==['Zulu']
    view.close()


def test_startup_card_preference_used_on_first_construction(app, games, monkeypatch):
    from ui.library.widgets.game_card import GameCard
    seen=[]
    original=GameCard.load_cover
    def load(card):
        seen.append(card.card_size)
        return original(card)
    monkeypatch.setattr(GameCard,'load_cover',load)
    view=GalleryView(games,display_preferences=LibraryPreferences(card_size='large'))
    assert seen==['large']*len(games)
    view.close()
