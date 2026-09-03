from dataclasses import dataclass

from PyQt6.QtWidgets import QApplication

from ui.library.gallery import GalleryView


_app = QApplication.instance()

if _app is None:
    _app = QApplication([])


@dataclass
class FakeGame:

    name: str

    platform: str = "Nintendo Entertainment System"

    year: int = 1989

    genre: str = ""

    core: str = "nestopia_libretro.so"

    rom: str = "/roms/test.nes"

    source: str = "Test Library"

    artwork: str = ""

    favorite: bool = False

    rvdb_platform_id: str = ""


def test_random_game_selects_game_in_details(
    monkeypatch,
):

    game = FakeGame(
        name="Duck Tales 2"
    )

    view = GalleryView(
        [game]
    )

    monkeypatch.setattr(
        view.randomizer,
        "random_game",
        lambda: game,
    )

    assert view.details.current_game is None

    view.random_game()

    assert view.details.current_game is game
    assert view.details.title.text() == (
        "Duck Tales 2"
    )


def test_random_game_with_empty_library_is_safe():

    view = GalleryView(
        []
    )

    assert view.details.current_game is None

    view.random_game()

    assert view.details.current_game is None


def test_random_button_requests_visible_selection(
    monkeypatch,
):

    game = FakeGame(
        name="Mega Man 2"
    )

    view = GalleryView(
        [game]
    )

    monkeypatch.setattr(
        view.randomizer,
        "random_game",
        lambda: game,
    )

    view.toolbar.random_button.click()

    assert view.details.current_game is game
    assert view.details.title.text() == (
        "Mega Man 2"
    )
