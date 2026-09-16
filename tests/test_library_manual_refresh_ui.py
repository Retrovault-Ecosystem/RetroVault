from pathlib import Path

from PyQt6.QtWidgets import QApplication

from ui.library.gallery import GalleryView
from ui.library.widgets.library_toolbar import (
    LibraryToolbar,
)
from ui.pages.library_page import LibraryPage


_APPLICATION = None


def _app():
    global _APPLICATION

    if _APPLICATION is None:
        _APPLICATION = (
            QApplication.instance()
            or QApplication([])
        )

    return _APPLICATION


def _main_window_text():
    return Path(
        "ui/main_window.py"
    ).read_text(
        encoding="utf-8"
    )


class RefreshGame:

    def __init__(
        self,
        rom,
        *,
        name="Game",
        platform="NES",
    ):
        self.name = name
        self.platform = platform
        self.year = ""
        self.genre = ""
        self.core = ""
        self.rom = rom
        self.source = ""
        self.artwork = ""
        self.favorite = False
        self.rvdb_platform_id = ""
        self.rvdb_game_id = ""
        self.description = ""
        self.developer = ""
        self.publisher = ""


def test_toolbar_exposes_manual_refresh_signal():
    _app()

    toolbar = LibraryToolbar()

    requested = []

    toolbar.refresh_requested.connect(
        lambda: requested.append(True)
    )

    toolbar.refresh_button.click()

    assert requested == [True]
    assert (
        toolbar.refresh_button.text()
        == "Refresh Library"
    )


def test_gallery_manual_refresh_replaces_live_snapshot():
    _app()

    original = RefreshGame(
        "/roms/original.nes",
        name="Original",
    )

    refreshed = RefreshGame(
        "/roms/refreshed.nes",
        name="Refreshed",
    )

    calls = []

    view = GalleryView(
        [original],
        refresh_handler=lambda: (
            calls.append("reload")
            or [refreshed]
        ),
    )

    view.reload_library()

    assert calls == ["reload"]
    assert view.all_games == [refreshed]


def test_gallery_manual_refresh_notifies_after_refresh():
    _app()

    refreshed = RefreshGame(
        "/roms/refreshed.nes",
        name="Refreshed",
    )

    completed = []

    view = GalleryView(
        [],
        refresh_handler=lambda: [refreshed],
        refresh_completed_handler=(
            lambda games: completed.append(
                tuple(games)
            )
        ),
    )

    view.reload_library()

    assert view.all_games == [refreshed]
    assert completed == [
        (refreshed,)
    ]


def test_gallery_manual_refresh_does_not_notify_on_failure():
    _app()

    completed = []

    def fail():
        raise RuntimeError(
            "simulated refresh failure"
        )

    view = GalleryView(
        [],
        refresh_handler=fail,
        refresh_completed_handler=(
            lambda games: completed.append(
                tuple(games)
            )
        ),
    )

    view.reload_library()

    assert completed == []


def test_library_page_propagates_refresh_handlers():
    _app()

    refresh_handler = lambda: []
    completed_handler = lambda games: None

    page = LibraryPage(
        [],
        refresh_handler=refresh_handler,
        refresh_completed_handler=(
            completed_handler
        ),
    )

    assert (
        page.refresh_handler
        is refresh_handler
    )

    assert (
        page.refresh_completed_handler
        is completed_handler
    )


def test_main_window_wires_manual_refresh_to_controller():
    text = _main_window_text()

    assert (
        "refresh_handler=(\n"
        "                controller.reload_sources\n"
        "            )"
        in text
    )


def test_manual_refresh_synchronizes_systems_and_playlists():
    text = _main_window_text()

    start = text.index(
        "        def library_refresh_completed("
    )

    end = text.index(
        "        library_page = LibraryPage(",
        start,
    )

    callback = text[
        start:end
    ]

    assert (
        "systems_page.refresh_page()"
        in callback
    )

    assert (
        "playlists_page.refresh_collections("
        in callback
    )


def test_manual_refresh_failure_uses_no_popup():
    text = Path(
        "ui/library/gallery.py"
    ).read_text(
        encoding="utf-8"
    )

    start = text.index(
        "    def reload_library(self):"
    )

    end = text.index(
        "    def bulk_import(self):",
        start,
    )

    method = text[
        start:end
    ]

    assert "try:" in method
    assert "OSError," in method
    assert "RuntimeError," in method
    assert "ValueError," in method

    assert "QMessageBox" not in method
    assert ".warning(" not in method
    assert ".critical(" not in method


def test_manual_refresh_preserves_search_state():
    _app()

    game = RefreshGame(
        "/roms/game.nes",
        name="Mega Man",
    )

    view = GalleryView(
        [game],
        refresh_handler=lambda: [game],
    )

    view.toolbar.search.setText(
        "mega"
    )

    view.reload_library()

    assert view.toolbar.search.text() == "mega"


def test_manual_refresh_preserves_system_filter():
    _app()

    nes = RefreshGame(
        "/roms/nes.nes",
        name="NES Game",
        platform="NES",
    )

    snes = RefreshGame(
        "/roms/snes.sfc",
        name="SNES Game",
        platform="SNES",
    )

    view = GalleryView(
        [nes, snes],
        refresh_handler=lambda: [
            nes,
            snes,
        ],
    )

    view.toolbar.system_filter.setCurrentText(
        "SNES"
    )

    view.reload_library()

    assert (
        view.toolbar.system_filter.currentText()
        == "SNES"
    )


def test_manual_refresh_falls_back_when_system_removed():
    _app()

    nes = RefreshGame(
        "/roms/nes.nes",
        name="NES Game",
        platform="NES",
    )

    snes = RefreshGame(
        "/roms/snes.sfc",
        name="SNES Game",
        platform="SNES",
    )

    view = GalleryView(
        [nes, snes],
        refresh_handler=lambda: [nes],
    )

    view.toolbar.system_filter.setCurrentText(
        "SNES"
    )

    view.reload_library()

    assert (
        view.toolbar.system_filter.currentText()
        == "All Systems"
    )


def test_manual_refresh_preserves_sort_state():
    _app()

    game = RefreshGame(
        "/roms/game.nes"
    )

    view = GalleryView(
        [game],
        refresh_handler=lambda: [game],
    )

    view.toolbar.sort.setCurrentText(
        "Year"
    )

    view.reload_library()

    assert (
        view.toolbar.sort.currentText()
        == "Year"
    )


def test_manual_refresh_preserves_favorites_filter():
    _app()

    game = RefreshGame(
        "/roms/game.nes"
    )

    game.favorite = True

    view = GalleryView(
        [game],
        refresh_handler=lambda: [game],
    )

    view.toolbar.favorites_only.setChecked(
        True
    )

    view.reload_library()

    assert (
        view.toolbar.favorites_only.isChecked()
        is True
    )


def test_manual_refresh_preserves_recent_filter():
    _app()

    game = RefreshGame(
        "/roms/game.nes"
    )

    view = GalleryView(
        [game],
        recent_provider=lambda: [
            game.rom
        ],
        refresh_handler=lambda: [game],
    )

    view.toolbar.recent_only.setChecked(
        True
    )

    view.reload_library()

    assert (
        view.toolbar.recent_only.isChecked()
        is True
    )


def test_manual_refresh_preserves_details_view():
    _app()

    game = RefreshGame(
        "/roms/game.nes"
    )

    view = GalleryView(
        [game],
        refresh_handler=lambda: [game],
    )

    view.show_details_view()

    view.reload_library()

    assert (
        view.library_view_stack.currentWidget()
        is view.details_view
    )


def test_manual_refresh_preserves_compact_view():
    _app()

    game = RefreshGame(
        "/roms/game.nes"
    )

    view = GalleryView(
        [game],
        refresh_handler=lambda: [game],
    )

    view.show_compact_view()

    view.reload_library()

    assert (
        view.library_view_stack.currentWidget()
        is view.compact_view
    )


def test_manual_refresh_preserves_selected_game_identity():
    _app()

    game = RefreshGame(
        "/roms/game.nes",
        name="Selected",
    )

    view = GalleryView(
        [game],
        refresh_handler=lambda: [game],
    )

    view.details.show_game(
        game
    )

    view.reload_library()

    assert (
        view.details.current_game
        is game
    )


def test_manual_refresh_clears_removed_selection():
    _app()

    game = RefreshGame(
        "/roms/removed.nes",
        name="Removed",
    )

    view = GalleryView(
        [game],
        refresh_handler=lambda: [],
    )

    view.details.show_game(
        game
    )

    view.reload_library()

    assert (
        view.details.current_game
        is None
    )


def test_manual_refresh_reports_success_non_modally():
    _app()

    game = RefreshGame(
        "/roms/game.nes"
    )

    view = GalleryView(
        [game],
        refresh_handler=lambda: [game],
    )

    view.reload_library()

    assert (
        view.toolbar.toolTip()
        == "Library refreshed."
    )


def test_toolbar_exposes_non_modal_refresh_status():
    _app()

    toolbar = LibraryToolbar()

    assert toolbar.refresh_status.text() == ""
    assert (
        toolbar.refresh_status.objectName()
        == "libraryRefreshStatus"
    )


def test_manual_refresh_disables_control_while_handler_runs():
    _app()

    game = RefreshGame(
        "/roms/game.nes"
    )

    observed = []

    view = None

    def refresh():
        observed.append(
            view.toolbar.refresh_button.isEnabled()
        )

        observed.append(
            view.toolbar.refresh_status.text()
        )

        return [game]

    view = GalleryView(
        [game],
        refresh_handler=refresh,
    )

    view.reload_library()

    assert observed == [
        False,
        "Refreshing...",
    ]


def test_manual_refresh_reenables_control_after_success():
    _app()

    game = RefreshGame(
        "/roms/game.nes"
    )

    view = GalleryView(
        [game],
        refresh_handler=lambda: [game],
    )

    view.reload_library()

    assert (
        view.toolbar.refresh_button.isEnabled()
        is True
    )

    assert (
        view.toolbar.refresh_status.text()
        == "Library refreshed."
    )

    assert (
        view.toolbar.refresh_status.toolTip()
        == "Library refreshed."
    )


def test_manual_refresh_reenables_control_after_failure():
    _app()

    def fail():
        raise RuntimeError(
            "simulated refresh failure"
        )

    view = GalleryView(
        [],
        refresh_handler=fail,
    )

    view.reload_library()

    assert (
        view.toolbar.refresh_button.isEnabled()
        is True
    )

    assert (
        view.toolbar.refresh_status.text()
        == "Refresh failed."
    )

    assert (
        "simulated refresh failure"
        in view.toolbar.refresh_status.toolTip()
    )


def test_manual_refresh_failure_feedback_is_non_modal():
    text = Path(
        "ui/library/gallery.py"
    ).read_text(
        encoding="utf-8"
    )

    start = text.index(
        "    def reload_library(self):"
    )

    end = text.index(
        "    def bulk_import(self):",
        start,
    )

    method = text[start:end]

    assert (
        'self.toolbar.refresh_status.setText('
        in method
    )

    assert '"Refresh failed."' in method

    assert "QMessageBox" not in method
    assert ".warning(" not in method
    assert ".critical(" not in method
