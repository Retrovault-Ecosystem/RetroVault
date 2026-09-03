from dataclasses import dataclass

import pytest

from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QColor,
    QImage,
)
from PyQt6.QtWidgets import QApplication

from ui.library.widgets.game_card import (
    GameCard,
)
from ui.library.widgets.game_grid import (
    GameGrid,
)


@dataclass
class FakeGame:

    name: str = "Test Game"
    platform: str = "Test Platform"
    year: int = 1990
    artwork: str = ""
    favorite: bool = False


@pytest.fixture(scope="session")
def app():

    instance = QApplication.instance()

    if instance is None:

        instance = QApplication(
            []
        )

    return instance


def _write_image(
    path,
    width=320,
    height=160,
):

    image = QImage(
        width,
        height,
        QImage.Format.Format_RGB32,
    )

    image.fill(
        QColor(
            "white"
        )
    )

    assert image.save(
        str(path)
    )

    return path


def _cards(grid):

    result = []

    for index in range(
        grid.layout.count()
    ):

        item = grid.layout.itemAt(
            index
        )

        widget = item.widget()

        if isinstance(
            widget,
            GameCard,
        ):
            result.append(
                widget
            )

    return result


def test_game_card_displays_valid_artwork(
    app,
    tmp_path,
):

    artwork = _write_image(
        tmp_path / "cover.png"
    )

    game = FakeGame(
        artwork=str(
            artwork
        )
    )

    card = GameCard(
        game
    )

    pixmap = card.cover.pixmap()

    assert pixmap is not None
    assert not pixmap.isNull()

    assert card.cover.text() == ""

    assert pixmap.width() <= 160
    assert pixmap.height() <= 200


def test_game_card_preserves_artwork_aspect_ratio(
    app,
    tmp_path,
):

    artwork = _write_image(
        tmp_path / "wide.png",
        width=320,
        height=160,
    )

    game = FakeGame(
        artwork=str(
            artwork
        )
    )

    card = GameCard(
        game
    )

    pixmap = card.cover.pixmap()

    assert pixmap is not None
    assert not pixmap.isNull()

    assert pixmap.width() == 160
    assert pixmap.height() == 80


def test_game_card_missing_artwork_uses_placeholder(
    app,
):

    game = FakeGame(
        artwork=""
    )

    card = GameCard(
        game
    )

    pixmap = card.cover.pixmap()

    assert (
        pixmap is None
        or pixmap.isNull()
    )

    assert (
        card.cover.text()
        == "🎮"
    )


def test_game_card_invalid_artwork_uses_placeholder(
    app,
    tmp_path,
):

    invalid = (
        tmp_path
        / "invalid.png"
    )

    invalid.write_bytes(
        b"not-an-image"
    )

    game = FakeGame(
        artwork=str(
            invalid
        )
    )

    card = GameCard(
        game
    )

    pixmap = card.cover.pixmap()

    assert (
        pixmap is None
        or pixmap.isNull()
    )

    assert (
        card.cover.text()
        == "🎮"
    )


def test_game_grid_rebuild_reflects_updated_artwork(
    app,
    tmp_path,
):

    artwork = _write_image(
        tmp_path / "cover.png"
    )

    game = FakeGame(
        artwork=""
    )

    grid = GameGrid(
        [game]
    )

    first_cards = _cards(
        grid
    )

    assert len(
        first_cards
    ) == 1

    first_card = first_cards[0]

    assert (
        first_card.cover.text()
        == "🎮"
    )

    game.artwork = str(
        artwork
    )

    grid.update_games(
        [game]
    )

    refreshed_cards = _cards(
        grid
    )

    assert len(
        refreshed_cards
    ) == 1

    refreshed_card = (
        refreshed_cards[0]
    )

    assert (
        refreshed_card
        is not first_card
    )

    pixmap = (
        refreshed_card
        .cover
        .pixmap()
    )

    assert pixmap is not None
    assert not pixmap.isNull()

    assert (
        refreshed_card.cover.text()
        == ""
    )
