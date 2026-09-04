import pytest

from PyQt6.QtWidgets import (
    QApplication,
    QInputDialog,
    QMessageBox,
)

from services.library.models import Game
from ui.library.details.game_details import (
    GameDetails,
)


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()

    if instance is None:
        instance = QApplication([])

    return instance


def make_game():
    return Game(
        name="Duck Tales 2",
        platform="NES",
        year=1993,
        genre="Platformer",
        core="fceumm",
        rom="/roms/duck-tales-2.nes",
    )


def test_collection_button_starts_disabled(
    app,
):
    details = GameDetails(
        collection_names_provider=lambda: [
            "NES"
        ],
        collection_add_handler=lambda *args: None,
    )

    assert not (
        details.collection_button.isEnabled()
    )


def test_show_game_enables_collection_button(
    app,
):
    details = GameDetails(
        collection_names_provider=lambda: [
            "NES"
        ],
        collection_add_handler=lambda *args: None,
    )

    details.show_game(
        make_game()
    )

    assert details.collection_button.isEnabled()


def test_romless_game_cannot_be_collected(
    app,
):
    details = GameDetails(
        collection_names_provider=lambda: [
            "NES"
        ],
        collection_add_handler=lambda *args: None,
    )
    game = make_game()
    game.rom = ""

    details.show_game(game)

    assert not (
        details.collection_button.isEnabled()
    )


def test_no_collections_shows_guidance(
    app,
    monkeypatch,
):
    details = GameDetails(
        collection_names_provider=lambda: [],
        collection_add_handler=lambda *args: None,
    )
    details.show_game(
        make_game()
    )

    messages = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: (
            messages.append(args[2])
        ),
    )

    details.add_to_collection()

    assert messages == [
        (
            "Create a collection on the "
            "Playlists page first."
        )
    ]


def test_selected_collection_receives_game(
    app,
    monkeypatch,
):
    recorded = []
    game = make_game()

    details = GameDetails(
        collection_names_provider=lambda: [
            "NES",
            "Weekend",
        ],
        collection_add_handler=(
            lambda name, selected: (
                recorded.append(
                    (name, selected)
                )
            )
        ),
    )
    details.show_game(game)

    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        lambda *args, **kwargs: (
            "Weekend",
            True,
        ),
    )

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: None,
    )

    details.add_to_collection()

    assert recorded == [
        ("Weekend", game)
    ]


def test_cancel_does_not_add_game(
    app,
    monkeypatch,
):
    recorded = []
    details = GameDetails(
        collection_names_provider=lambda: [
            "NES"
        ],
        collection_add_handler=(
            lambda *args: recorded.append(args)
        ),
    )
    details.show_game(
        make_game()
    )

    monkeypatch.setattr(
        QInputDialog,
        "getItem",
        lambda *args, **kwargs: (
            "NES",
            False,
        ),
    )

    details.add_to_collection()

    assert recorded == []


def test_library_page_propagates_collection_handlers(
    app,
):
    from ui.pages.library_page import (
        LibraryPage,
    )

    names = lambda: ["NES"]
    add = lambda *args: None

    page = LibraryPage(
        [],
        collection_names_provider=names,
        collection_add_handler=add,
    )

    assert (
        page.details.collection_names_provider
        is names
    )
    assert (
        page.details.collection_add_handler
        is add
    )
