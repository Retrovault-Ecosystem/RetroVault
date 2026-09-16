from types import SimpleNamespace

from PyQt6.QtWidgets import QApplication, QFileDialog, QMessageBox

from ui.library.gallery import GalleryView
from ui.library.widgets.library_toolbar import LibraryToolbar
from ui.pages.library_page import LibraryPage


_app = QApplication.instance()

if _app is None:
    _app = QApplication([])


class FakeGame:
    def __init__(
        self,
        name,
        rom,
        platform="NES",
    ):
        self.name = name
        self.rom = rom
        self.platform = platform
        self.year = 0
        self.genre = ""
        self.core = ""
        self.source = "Bulk Import"
        self.artwork = ""
        self.favorite = False
        self.rvdb_platform_id = ""
        self.rvdb_game_id = ""


class FakeController:
    def __init__(self):
        self.calls = []
        self.games = [
            FakeGame(
                "Existing",
                "/roms/existing.nes",
            )
        ]

    def bulk_import(self, directory):
        self.calls.append(directory)

        added = FakeGame(
            "Imported",
            "/roms/imported.sfc",
            platform="SNES",
        )

        self.games.append(added)

        return {
            "discovered": SimpleNamespace(
                discovered_count=2,
                duplicate_count=1,
            ),
            "added": (added,),
            "added_count": 1,
            "skipped_count": 1,
        }

    def get_games(self):
        return self.games


def test_toolbar_exposes_bulk_import_signal():
    toolbar = LibraryToolbar()

    calls = []

    toolbar.bulk_import_requested.connect(
        lambda: calls.append(True)
    )

    toolbar.bulk_import_button.click()

    assert calls == [True]


def test_gallery_cancel_does_not_import(
    monkeypatch,
):
    controller = FakeController()

    view = GalleryView(
        controller.get_games(),
        bulk_import_handler=controller.bulk_import,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: "",
    )

    view.bulk_import()

    assert controller.calls == []


def test_gallery_bulk_import_refreshes_library(
    monkeypatch,
):
    controller = FakeController()

    view = GalleryView(
        controller.get_games(),
        bulk_import_handler=controller.bulk_import,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: "/roms",
    )

    messages = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args: messages.append(args),
    )

    view.bulk_import()

    assert controller.calls == ["/roms"]

    assert [
        game.name
        for game in view.all_games
    ] == [
        "Existing",
        "Imported",
    ]

    assert len(messages) == 1

    message = messages[0][2]

    assert "ROMs discovered: 2" in message
    assert "Games added: 1" in message
    assert "Already in library / skipped: 1" in message
    assert "Duplicates inside source: 1" in message


def test_gallery_bulk_import_reports_error(
    monkeypatch,
):
    def fail(directory):
        raise ValueError(
            "Invalid bulk-import source"
        )

    view = GalleryView(
        [],
        bulk_import_handler=fail,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: "/bad",
    )

    errors = []

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda *args: errors.append(args),
    )

    view.bulk_import()

    assert len(errors) == 1
    assert (
        "Invalid bulk-import source"
        in errors[0][2]
    )


def test_library_page_propagates_bulk_import_handler():
    handler = lambda directory: None

    page = LibraryPage(
        [],
        bulk_import_handler=handler,
    )

    assert page.bulk_import_handler is handler


def test_gallery_bulk_import_reports_production_summary(
    monkeypatch,
):
    controller = FakeController()

    original_bulk_import = controller.bulk_import

    def import_with_persistence(directory):
        result = original_bulk_import(
            directory
        )
        result["persisted"] = {
            "added": True,
        }
        return result

    view = GalleryView(
        controller.get_games(),
        bulk_import_handler=import_with_persistence,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: "/roms",
    )

    messages = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args: messages.append(args),
    )

    view.bulk_import()

    assert len(messages) == 1
    assert messages[0][1] == (
        "Bulk Import Complete"
    )

    message = messages[0][2]

    assert (
        "RetroVault finished scanning "
        "the selected folder."
        in message
    )
    assert "ROMs discovered: 2" in message
    assert "Games added: 1" in message
    assert (
        "Already in library / skipped: 1"
        in message
    )
    assert (
        "Duplicates inside source: 1"
        in message
    )
    assert (
        "Source: Saved as a library source"
        in message
    )


def test_gallery_bulk_import_reports_existing_source(
    monkeypatch,
):
    controller = FakeController()

    original_bulk_import = controller.bulk_import

    def import_existing_source(directory):
        result = original_bulk_import(
            directory
        )
        result["persisted"] = {
            "added": False,
        }
        return result

    view = GalleryView(
        controller.get_games(),
        bulk_import_handler=import_existing_source,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: "/roms",
    )

    messages = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args: messages.append(args),
    )

    view.bulk_import()

    assert len(messages) == 1

    assert (
        "Source: Already registered "
        "as a library source"
        in messages[0][2]
    )


def test_gallery_bulk_import_error_has_production_context(
    monkeypatch,
):
    def fail(directory):
        raise OSError(
            "permission denied"
        )

    view = GalleryView(
        [],
        bulk_import_handler=fail,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: "/roms",
    )

    errors = []

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda *args: errors.append(args),
    )

    view.bulk_import()

    assert len(errors) == 1
    assert errors[0][1] == (
        "Bulk Import Failed"
    )

    assert (
        "RetroVault could not import "
        "ROMs from the selected folder."
        in errors[0][2]
    )

    assert "permission denied" in errors[0][2]
