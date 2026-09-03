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


def test_library_starts_in_gallery_view():

    game = FakeGame(
        name="Adventure Island"
    )

    view = GalleryView(
        [game]
    )

    assert (
        view.library_view_stack.currentWidget()
        is view.grid
    )


def test_details_button_switches_to_details_view():

    game = FakeGame(
        name="Adventure Island"
    )

    view = GalleryView(
        [game]
    )

    view.toolbar.view_selector.details.click()

    assert (
        view.library_view_stack.currentWidget()
        is view.details_view
    )


def test_gallery_button_restores_gallery_view():

    game = FakeGame(
        name="Adventure Island"
    )

    view = GalleryView(
        [game]
    )

    view.toolbar.view_selector.details.click()

    assert (
        view.library_view_stack.currentWidget()
        is view.details_view
    )

    view.toolbar.view_selector.gallery.click()

    assert (
        view.library_view_stack.currentWidget()
        is view.grid
    )


def test_details_view_tracks_search_filter():

    adventure = FakeGame(
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

    view = GalleryView(
        [
            adventure,
            mega_man,
        ]
    )

    view.toolbar.search.setText(
        "Adventure"
    )

    assert view.details_view.list.count() == 1

    item = view.details_view.list.item(
        0
    )

    assert "Adventure Island" in item.text()
    assert "Mega Man 2" not in item.text()


def test_details_view_tracks_system_filter():

    adventure = FakeGame(
        name="Adventure Island",
        platform=(
            "Nintendo Entertainment System"
        ),
    )

    chrono = FakeGame(
        name="Chrono Trigger",
        platform="Super Nintendo",
    )

    view = GalleryView(
        [
            adventure,
            chrono,
        ]
    )

    index = (
        view.toolbar.system_filter.findText(
            "Super Nintendo"
        )
    )

    assert index >= 0

    view.toolbar.system_filter.setCurrentIndex(
        index
    )

    assert view.details_view.list.count() == 1

    item = view.details_view.list.item(
        0
    )

    assert "Chrono Trigger" in item.text()
    assert "Adventure Island" not in item.text()


def test_selecting_details_row_updates_game_details():

    adventure = FakeGame(
        name="Adventure Island"
    )

    mega_man = FakeGame(
        name="Mega Man 2"
    )

    view = GalleryView(
        [
            adventure,
            mega_man,
        ]
    )

    view.toolbar.view_selector.details.click()

    view.details_view.list.setCurrentRow(
        1
    )

    assert view.details.current_game is mega_man
    assert view.details.title.text() == (
        "Mega Man 2"
    )


def test_compact_view_is_enabled():

    view = GalleryView(
        [
            FakeGame(
                name="Adventure Island"
            )
        ]
    )

    assert (
        view.toolbar.view_selector.compact.isEnabled()
        is True
    )


def test_compact_button_switches_to_compact_view():

    game = FakeGame(
        name="Adventure Island"
    )

    view = GalleryView(
        [game]
    )

    view.toolbar.view_selector.compact.click()

    assert (
        view.library_view_stack.currentWidget()
        is view.compact_view
    )


def test_compact_view_tracks_search_filter():

    adventure = FakeGame(
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

    view = GalleryView(
        [
            adventure,
            mega_man,
        ]
    )

    view.toolbar.search.setText(
        "Adventure"
    )

    assert view.compact_view.list.count() == 1

    item = view.compact_view.list.item(
        0
    )

    assert "Adventure Island" in item.text()
    assert "Mega Man 2" not in item.text()


def test_compact_view_tracks_system_filter():

    adventure = FakeGame(
        name="Adventure Island",
        platform=(
            "Nintendo Entertainment System"
        ),
    )

    chrono = FakeGame(
        name="Chrono Trigger",
        platform="Super Nintendo",
    )

    view = GalleryView(
        [
            adventure,
            chrono,
        ]
    )

    index = (
        view.toolbar.system_filter.findText(
            "Super Nintendo"
        )
    )

    assert index >= 0

    view.toolbar.system_filter.setCurrentIndex(
        index
    )

    assert view.compact_view.list.count() == 1

    item = view.compact_view.list.item(
        0
    )

    assert "Chrono Trigger" in item.text()
    assert "Adventure Island" not in item.text()


def test_selecting_compact_row_updates_game_details():

    adventure = FakeGame(
        name="Adventure Island"
    )

    mega_man = FakeGame(
        name="Mega Man 2"
    )

    view = GalleryView(
        [
            adventure,
            mega_man,
        ]
    )

    view.toolbar.view_selector.compact.click()

    view.compact_view.list.setCurrentRow(
        1
    )

    assert view.details.current_game is mega_man

    assert view.details.title.text() == (
        "Mega Man 2"
    )


def test_favorite_button_disabled_without_selection():

    view = GalleryView(
        [
            FakeGame(
                name="Adventure Island"
            )
        ]
    )

    assert (
        view.details.favorite_button.isEnabled()
        is False
    )


def test_selecting_game_enables_favorite_button():

    game = FakeGame(
        name="Adventure Island"
    )

    view = GalleryView(
        [game]
    )

    view.details.show_game(
        game
    )

    assert (
        view.details.favorite_button.isEnabled()
        is True
    )

    assert (
        "Add to Favorites"
        in view.details.favorite_button.text()
    )


def test_favorite_button_uses_injected_handler():

    game = FakeGame(
        name="Adventure Island"
    )

    calls = []

    def favorite_handler(
        selected_game,
        favorite,
    ):
        calls.append(
            (
                selected_game,
                favorite,
            )
        )

        selected_game.favorite = favorite

    view = GalleryView(
        [game],
        favorite_handler=favorite_handler,
    )

    view.details.show_game(
        game
    )

    view.details.favorite_button.click()

    assert calls == [
        (
            game,
            True,
        )
    ]

    assert game.favorite is True

    assert (
        "Remove from Favorites"
        in view.details.favorite_button.text()
    )


def test_favorite_button_can_remove_favorite():

    game = FakeGame(
        name="Adventure Island",
        favorite=True,
    )

    calls = []

    def favorite_handler(
        selected_game,
        favorite,
    ):
        calls.append(
            favorite
        )

        selected_game.favorite = favorite

    view = GalleryView(
        [game],
        favorite_handler=favorite_handler,
    )

    view.details.show_game(
        game
    )

    view.details.favorite_button.click()

    assert calls == [
        False
    ]

    assert game.favorite is False

    assert (
        "Add to Favorites"
        in view.details.favorite_button.text()
    )


def test_gallery_refreshes_favorite_star_after_toggle():

    game = FakeGame(
        name="Adventure Island"
    )

    def favorite_handler(
        selected_game,
        favorite,
    ):
        selected_game.favorite = favorite

    view = GalleryView(
        [game],
        favorite_handler=favorite_handler,
    )

    view.details.show_game(
        game
    )

    view.details.favorite_button.click()

    card = (
        view.grid.layout
        .itemAt(0)
        .widget()
    )

    assert "⭐" in card.info.text()


def test_favorites_filter_exists_and_starts_off():

    view = GalleryView(
        [
            FakeGame(
                name="Adventure Island"
            )
        ]
    )

    assert (
        view.toolbar.favorites_only.isCheckable()
        is True
    )

    assert (
        view.toolbar.favorites_only.isChecked()
        is False
    )


def test_favorites_filter_shows_only_favorite_games():

    favorite = FakeGame(
        name="Adventure Island",
        favorite=True,
    )

    ordinary = FakeGame(
        name="Mega Man 2",
        favorite=False,
    )

    view = GalleryView(
        [
            favorite,
            ordinary,
        ]
    )

    view.toolbar.favorites_only.click()

    assert _visible_game_names(
        view
    ) == [
        "Adventure Island"
    ]


def test_favorites_filter_composes_with_search():

    adventure = FakeGame(
        name="Adventure Island",
        favorite=True,
    )

    mega_man = FakeGame(
        name="Mega Man 2",
        favorite=True,
    )

    ordinary = FakeGame(
        name="Adventure II",
        favorite=False,
    )

    view = GalleryView(
        [
            adventure,
            mega_man,
            ordinary,
        ]
    )

    view.toolbar.favorites_only.click()

    view.toolbar.search.setText(
        "Adventure"
    )

    assert _visible_game_names(
        view
    ) == [
        "Adventure Island"
    ]


def test_favorites_filter_composes_with_system():

    nes = FakeGame(
        name="Adventure Island",
        platform=(
            "Nintendo Entertainment System"
        ),
        favorite=True,
    )

    snes = FakeGame(
        name="Chrono Trigger",
        platform="Super Nintendo",
        favorite=True,
    )

    ordinary_nes = FakeGame(
        name="Mega Man 2",
        platform=(
            "Nintendo Entertainment System"
        ),
        favorite=False,
    )

    view = GalleryView(
        [
            nes,
            snes,
            ordinary_nes,
        ]
    )

    view.toolbar.favorites_only.click()

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


def test_favorites_filter_composes_with_search_and_system():

    target = FakeGame(
        name="Adventure Island",
        platform=(
            "Nintendo Entertainment System"
        ),
        favorite=True,
    )

    wrong_system = FakeGame(
        name="Adventure Island II",
        platform="Super Nintendo",
        favorite=True,
    )

    not_favorite = FakeGame(
        name="Adventure Quest",
        platform=(
            "Nintendo Entertainment System"
        ),
        favorite=False,
    )

    view = GalleryView(
        [
            target,
            wrong_system,
            not_favorite,
        ]
    )

    view.toolbar.favorites_only.click()

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
        "Adventure"
    )

    assert _visible_game_names(
        view
    ) == [
        "Adventure Island"
    ]


def test_details_view_tracks_favorites_filter():

    favorite = FakeGame(
        name="Adventure Island",
        favorite=True,
    )

    ordinary = FakeGame(
        name="Mega Man 2",
        favorite=False,
    )

    view = GalleryView(
        [
            favorite,
            ordinary,
        ]
    )

    view.toolbar.favorites_only.click()

    assert view.details_view.list.count() == 1

    assert (
        "Adventure Island"
        in view.details_view.list.item(0).text()
    )


def test_compact_view_tracks_favorites_filter():

    favorite = FakeGame(
        name="Adventure Island",
        favorite=True,
    )

    ordinary = FakeGame(
        name="Mega Man 2",
        favorite=False,
    )

    view = GalleryView(
        [
            favorite,
            ordinary,
        ]
    )

    view.toolbar.favorites_only.click()

    assert view.compact_view.list.count() == 1

    assert (
        "Adventure Island"
        in view.compact_view.list.item(0).text()
    )


def test_random_game_respects_favorites_filter(
    monkeypatch,
):

    favorite = FakeGame(
        name="Adventure Island",
        favorite=True,
    )

    ordinary = FakeGame(
        name="Mega Man 2",
        favorite=False,
    )

    view = GalleryView(
        [
            favorite,
            ordinary,
        ]
    )

    view.toolbar.favorites_only.click()

    monkeypatch.setattr(
        view.randomizer,
        "random_game",
        lambda: (
            view.randomizer.games[0]
            if view.randomizer.games
            else None
        ),
    )

    view.random_game()

    assert view.randomizer.games == [
        favorite
    ]

    assert (
        view.details.current_game
        is favorite
    )


def test_random_game_respects_favorites_search_and_system(
    monkeypatch,
):

    target = FakeGame(
        name="Adventure Island",
        platform=(
            "Nintendo Entertainment System"
        ),
        favorite=True,
    )

    other_favorite = FakeGame(
        name="Chrono Trigger",
        platform="Super Nintendo",
        favorite=True,
    )

    ordinary = FakeGame(
        name="Adventure II",
        platform=(
            "Nintendo Entertainment System"
        ),
        favorite=False,
    )

    view = GalleryView(
        [
            target,
            other_favorite,
            ordinary,
        ]
    )

    view.toolbar.favorites_only.click()

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
        "Adventure"
    )

    monkeypatch.setattr(
        view.randomizer,
        "random_game",
        lambda: (
            view.randomizer.games[0]
            if view.randomizer.games
            else None
        ),
    )

    view.random_game()

    assert view.randomizer.games == [
        target
    ]

    assert (
        view.details.current_game
        is target
    )


def test_favorites_filter_empty_result_is_safe():

    ordinary = FakeGame(
        name="Mega Man 2",
        favorite=False,
    )

    view = GalleryView(
        [ordinary]
    )

    view.toolbar.favorites_only.click()

    assert _visible_game_names(
        view
    ) == []

    assert view.randomizer.games == []

    view.random_game()

    assert view.details.current_game is None


def test_removing_favorite_while_filter_active_removes_game():

    game = FakeGame(
        name="Adventure Island",
        favorite=True,
    )

    def favorite_handler(
        selected_game,
        favorite,
    ):
        selected_game.favorite = favorite

    view = GalleryView(
        [game],
        favorite_handler=favorite_handler,
    )

    view.toolbar.favorites_only.click()

    assert _visible_game_names(
        view
    ) == [
        "Adventure Island"
    ]

    view.details.show_game(
        game
    )

    view.details.favorite_button.click()

    assert game.favorite is False

    assert _visible_game_names(
        view
    ) == []


def test_gallery_grid_packs_sparse_results_top_left():

    from PyQt6.QtCore import Qt

    game = FakeGame(
        name="Duck Tales 2 (U)",
        platform=(
            "Nintendo Entertainment System"
        ),
        favorite=True,
    )

    view = GalleryView(
        [game]
    )

    view.toolbar.search.setText(
        "Duck Tales 2"
    )

    alignment = (
        view.grid.layout.alignment()
    )

    assert (
        alignment
        & Qt.AlignmentFlag.AlignTop
    )

    assert (
        alignment
        & Qt.AlignmentFlag.AlignLeft
    )
