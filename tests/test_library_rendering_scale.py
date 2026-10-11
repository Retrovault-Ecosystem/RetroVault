from math import ceil
from types import SimpleNamespace
import pytest
from PyQt6.QtCore import QCoreApplication, QEvent
from PyQt6.QtWidgets import QApplication
from ui.library.widgets.game_grid import GameGrid
from ui.library.widgets.game_card import GameCard
from ui.library.views.game_list import GameListView


@pytest.fixture
def app():
    return QApplication.instance() or QApplication([])


def games(n):
    return [SimpleNamespace(name=f'Game {i}', platform='NES', year=1990, core='',
            artwork='', variants=[], favorite=False, local_file_id=f'id-{i}') for i in range(n)]


@pytest.mark.parametrize('count', [100, 2000, 10000, 50000])
def test_cards_bounded_and_last_game_clickable(app, count):
    selected=[]
    grid=GameGrid(games(count), details=SimpleNamespace(show_game=selected.append))
    grid.resize(1400,800);grid.show();app.processEvents()
    bound=5*(ceil(grid.scroll.viewport().height()/grid._row_height)+5)
    assert len(grid.findChildren(GameCard)) <= bound
    grid.scroll.verticalScrollBar().setValue(grid.scroll.verticalScrollBar().maximum())
    app.processEvents()
    cards=grid.findChildren(GameCard)
    assert len(cards)<=bound
    last=next(c for c in cards if c.game is grid.games[-1])
    last.clicked.emit()
    assert selected==[grid.games[-1]]
    assert last.mapTo(grid.container,last.rect().bottomLeft()).y() <= grid.container.height()
    grid.close();grid.deleteLater()


def test_repeated_scroll_and_replace_releases_retired_cards(app):
    grid=GameGrid(games(2000));grid.resize(1400,800);grid.show();app.processEvents()
    for i in range(20):
        grid.scroll.verticalScrollBar().setValue(i*1000)
        grid.update_games(games(2000))
        app.processEvents();QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
        assert len(grid.findChildren(GameCard))<=50
        assert not [w for w in app.topLevelWidgets() if isinstance(w,GameCard)]
    grid.close();grid.deleteLater()


def test_list_model_projects_current_rows_without_items(app):
    view=GameListView();items=games(50000);view.set_games(items)
    assert view.model().rowCount()==50000
    view.setCurrentRow(49999)
    assert view.currentRow()==49999
    assert view.model().index(49999,0).data().startswith('Game 49999')
    view.set_games(items[:1]);assert view.model().rowCount()==1
    assert view.model().index(10,0).data() is None
    view.deleteLater()


def test_sort_preserves_selected_identity_and_latest_query(app):
    from ui.library.gallery import GalleryView
    items=games(100)
    view=GalleryView(items)
    selected=items[70];view.details.show_game(selected)
    view.toolbar.sort.setCurrentText('Year')
    assert view.compact_view.games[view.compact_view.list.currentRow()] is selected
    for text in ['Game 1','Game 20','Game 70']:
        view.toolbar.search.setText(text)
    assert view.compact_view.games==[selected]
    assert view.details.current_game is selected
    view.close();view.deleteLater()


def test_mixed_edition_rows_have_stable_scroll_coordinates(app):
    items=games(1000);items[0].variants=[1,2]
    grid=GameGrid(items);grid.resize(1400,800);grid.show();app.processEvents()
    for size in ['large','small','default']:
        grid.set_card_size(size)
        grid.scroll.verticalScrollBar().setValue(4000);app.processEvents()
        cards=[grid.layout.itemAt(i).widget() for i in range(grid.layout.count())]
        for first,second in zip(cards,cards[5:]):
            assert second.y()-first.y()==grid._row_height
    grid.close();grid.deleteLater()


@pytest.mark.parametrize('count', [0,1])
def test_small_library_does_not_reserve_empty_columns(app, count):
    grid=GameGrid(games(count));grid.resize(640,600);grid.show();app.processEvents()
    assert grid.scroll.horizontalScrollBar().maximum()==0
    grid.set_card_size('large');app.processEvents()
    assert grid.scroll.horizontalScrollBar().maximum()==0
    grid.close();grid.deleteLater()
