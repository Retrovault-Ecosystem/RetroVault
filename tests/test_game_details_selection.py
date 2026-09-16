import pytest

from PyQt6.QtWidgets import (
    QApplication,
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


def make_game(
    rom="/roms/duck-tales-2.nes",
):
    return Game(
        name="Duck Tales 2",
        platform="NES",
        year=1993,
        genre="Platformer",
        core="fceumm",
        rom=rom,
    )


def test_launch_starts_disabled(
    app,
):
    details = GameDetails()

    assert details.current_game is None
    assert not details.launch_button.isEnabled()


def test_show_launchable_game_enables_launch(
    app,
):
    details = GameDetails()

    details.show_game(
        make_game()
    )

    assert details.launch_button.isEnabled()


def test_romless_game_keeps_launch_disabled(
    app,
):
    details = GameDetails()

    details.show_game(
        make_game(
            rom=""
        )
    )

    assert not details.launch_button.isEnabled()


def test_clear_game_resets_complete_selection(
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
    details.clear_game()

    assert details.current_game is None
    assert details.title.text() == (
        "Select a game"
    )
    assert details.metadata.text() == ""
    assert details.description.toPlainText() == ""
    assert details.cover.text() == "🎮"
    assert not details.favorite_button.isEnabled()
    assert not details.collection_button.isEnabled()
    assert not details.launch_button.isEnabled()


def test_clear_game_is_repeatable(
    app,
):
    details = GameDetails()

    details.clear_game()
    details.clear_game()

    assert details.current_game is None
    assert not details.launch_button.isEnabled()


def test_favorite_update_failure_is_reported_to_user(
    monkeypatch,
):
    from unittest.mock import Mock

    from PyQt6.QtWidgets import QMessageBox

    from ui.library.details.game_details import (
        GameDetails,
    )

    game = Mock()
    game.name = "Failure Test"
    game.favorite = False

    def fail_update(
        _game,
        _favorite,
    ):
        raise OSError(
            "favorite persistence failed"
        )

    warnings = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda parent, title, message: (
            warnings.append(
                (
                    parent,
                    title,
                    message,
                )
            )
        ),
    )

    details = GameDetails(
        favorite_handler=fail_update
    )
    details.current_game = game

    details.toggle_favorite()

    assert len(warnings) == 1

    parent, title, message = warnings[0]

    assert parent is details
    assert title == "Favorite Update Failed"

    assert (
        "RetroVault could not update "
        "this game's Favorite status."
        in message
    )

    assert (
        "favorite persistence failed"
        in message
    )

    assert game.favorite is False
