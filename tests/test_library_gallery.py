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


def _visible_game_names(view):

    return [
        view.grid.layout.itemAt(index)
        .widget()
        .game
        .name

        for index in range(
            view.grid.layout.count()
        )
    ]


def test_system_filter_uses_loaded_library_platforms():

    games = [
        FakeGame(
            name="Adventure Island",
            platform=(
                "Nintendo Entertainment System"
            ),
        ),
        FakeGame(
            name="Chrono Trigger",
            platform="Super Nintendo",
        ),
        FakeGame(
            name="Sonic the Hedgehog",
            platform="Sega Genesis",
        ),
        FakeGame(
            name="Galaga",
            platform="Arcade",
        ),
    ]

    view = GalleryView(
        games
    )

    systems = [
        view.toolbar.system_filter.itemText(
            index
        )

        for index in range(
            view.toolbar.system_filter.count()
        )
    ]

    assert systems == [
        "All Systems",
        "Arcade",
        "Nintendo Entertainment System",
        "Sega Genesis",
        "Super Nintendo",
    ]

    assert "NES" not in systems
    assert "SNES" not in systems
    assert "Genesis" not in systems


def test_system_filter_shows_matching_games():

    adventure_island = FakeGame(
        name="Adventure Island",
        platform=(
            "Nintendo Entertainment System"
        ),
    )

    chrono_trigger = FakeGame(
        name="Chrono Trigger",
        platform="Super Nintendo",
    )

    view = GalleryView(
        [
            adventure_island,
            chrono_trigger,
        ]
    )

    index = (
        view.toolbar.system_filter.findText(
            "Nintendo Entertainment System"
        )
    )

    assert index >= 0

    view.toolbar.system_filter.setCurrentIndex(
        index
    )

    assert _visible_game_names(
        view
    ) == [
        "Adventure Island"
    ]


def test_random_game_respects_system_filter():

    nes_game = FakeGame(
        name="Adventure Island",
        platform=(
            "Nintendo Entertainment System"
        ),
    )

    snes_game = FakeGame(
        name="Chrono Trigger",
        platform="Super Nintendo",
    )

    view = GalleryView(
        [
            nes_game,
            snes_game,
        ]
    )

    index = (
        view.toolbar.system_filter.findText(
            "Nintendo Entertainment System"
        )
    )

    assert index >= 0

    view.toolbar.system_filter.setCurrentIndex(
        index
    )

    assert view.randomizer.games == [
        nes_game
    ]

    view.random_game()

    assert view.details.current_game is nes_game


def test_random_game_respects_search_filter():

    adventure_island = FakeGame(
        name="Adventure Island",
        platform=(
            "Nintendo Entertainment System"
        ),
    )

    mega_man = FakeGame(
        name="Mega Man 2",
        platform=(
            "Nintendo Entertainment System"
        ),
    )

    chrono_trigger = FakeGame(
        name="Chrono Trigger",
        platform="Super Nintendo",
    )

    view = GalleryView(
        [
            adventure_island,
            mega_man,
            chrono_trigger,
        ]
    )

    view.toolbar.search.setText(
        "adventure island"
    )

    assert _visible_game_names(
        view
    ) == [
        "Adventure Island"
    ]

    assert view.randomizer.games == [
        adventure_island
    ]

    view.random_game()

    assert (
        view.details.current_game
        is adventure_island
    )


def test_random_game_respects_combined_search_and_system_filter():

    nes_adventure = FakeGame(
        name="Adventure Island",
        platform=(
            "Nintendo Entertainment System"
        ),
    )

    snes_adventure = FakeGame(
        name="Adventure Island II",
        platform="Super Nintendo",
    )

    nes_other = FakeGame(
        name="Mega Man 2",
        platform=(
            "Nintendo Entertainment System"
        ),
    )

    view = GalleryView(
        [
            nes_adventure,
            snes_adventure,
            nes_other,
        ]
    )

    index = (
        view.toolbar.system_filter.findText(
            "Nintendo Entertainment System"
        )
    )

    assert index >= 0

    view.toolbar.system_filter.setCurrentIndex(
        index
    )

    view.toolbar.search.setText(
        "Adventure Island"
    )

    assert _visible_game_names(
        view
    ) == [
        "Adventure Island"
    ]

    assert view.randomizer.games == [
        nes_adventure
    ]

    view.random_game()

    assert (
        view.details.current_game
        is nes_adventure
    )


def test_random_game_is_safe_when_filters_match_nothing():

    game = FakeGame(
        name="Adventure Island",
        platform=(
            "Nintendo Entertainment System"
        ),
    )

    view = GalleryView(
        [game]
    )

    view.toolbar.search.setText(
        "definitely-not-a-game"
    )

    assert _visible_game_names(
        view
    ) == []

    assert view.randomizer.games == []

    assert view.details.current_game is None

    view.random_game()

    assert view.details.current_game is None
