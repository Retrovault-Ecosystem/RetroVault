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
            "games": tuple(
                self.games
            ),
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


def test_gallery_bulk_import_refreshes_from_explicit_result_snapshot(
    monkeypatch,
):
    controller = FakeController()

    def wrapped_import(directory):
        return controller.bulk_import(
            directory
        )

    view = GalleryView(
        controller.get_games(),
        bulk_import_handler=wrapped_import,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: "/roms",
    )

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args: None,
    )

    assert getattr(
        wrapped_import,
        "__self__",
        None,
    ) is None

    view.bulk_import()

    assert controller.calls == [
        "/roms"
    ]

    assert [
        game.name
        for game in view.all_games
    ] == [
        "Existing",
        "Imported",
    ]


def test_gallery_bulk_import_preserves_view_without_snapshot(
    monkeypatch,
):
    existing = FakeGame(
        "Existing",
        "/roms/existing.nes",
    )

    def legacy_handler(directory):
        return {
            "discovered": SimpleNamespace(
                discovered_count=0,
                duplicate_count=0,
            ),
            "added": tuple(),
            "added_count": 0,
            "skipped_count": 0,
        }

    view = GalleryView(
        [existing],
        bulk_import_handler=legacy_handler,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: "/roms",
    )

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args: None,
    )

    view.bulk_import()

    assert view.all_games == [
        existing
    ]


def test_gallery_bulk_import_notifies_application_after_refresh(
    monkeypatch,
):
    controller = FakeController()
    events = []

    def completed(result):
        events.append(
            (
                tuple(
                    game.name
                    for game in result["games"]
                ),
                tuple(
                    game.name
                    for game in view.all_games
                ),
            )
        )

    view = GalleryView(
        controller.get_games(),
        bulk_import_handler=controller.bulk_import,
        bulk_import_completed_handler=completed,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: "/roms",
    )

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args: None,
    )

    view.bulk_import()

    assert events == [
        (
            (
                "Existing",
                "Imported",
            ),
            (
                "Existing",
                "Imported",
            ),
        )
    ]


def test_gallery_bulk_import_does_not_notify_on_failure(
    monkeypatch,
):
    events = []

    def fail(directory):
        raise OSError(
            "import failed"
        )

    view = GalleryView(
        [],
        bulk_import_handler=fail,
        bulk_import_completed_handler=(
            lambda result: events.append(result)
        ),
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: "/roms",
    )

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda *args: None,
    )

    view.bulk_import()

    assert events == []


def test_library_page_propagates_bulk_import_completed_handler():
    def handler(result):
        return None

    page = LibraryPage(
        [],
        bulk_import_completed_handler=handler,
    )

    assert (
        page.bulk_import_completed_handler
        is handler
    )


def test_bulk_import_starts_idle():
    QApplication.instance() or QApplication([])

    view = GalleryView(
        [],
    )

    assert (
        view._bulk_import_in_progress
        is False
    )


def test_bulk_import_disables_refresh_while_handler_runs(
    monkeypatch,
):
    QApplication.instance() or QApplication([])

    observed = []

    view = None

    def handler(_directory):
        observed.append(
            view._bulk_import_in_progress
        )
        observed.append(
            view.toolbar.bulk_import_button.isEnabled()
        )
        observed.append(
            view.toolbar.refresh_button.isEnabled()
        )

        class Discovered:
            discovered_count = 0
            duplicate_count = 0

        return {
            "games": [],
            "discovered": Discovered(),
            "added_count": 0,
            "skipped_count": 0,
            "persisted": {
                "added": False,
            },
        }

    view = GalleryView(
        [],
        bulk_import_handler=handler,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *_args, **_kwargs: "/roms",
    )

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *_args, **_kwargs: None,
    )

    view.bulk_import()

    assert observed == [
        True,
        False,
        False,
    ]

    assert (
        view._bulk_import_in_progress
        is False
    )

    assert (
        view.toolbar.bulk_import_button.isEnabled()
        is True
    )

    assert (
        view.toolbar.refresh_button.isEnabled()
        is True
    )


def test_bulk_import_reentrant_call_is_ignored(
    monkeypatch,
):
    QApplication.instance() or QApplication([])

    calls = []

    view = None

    def handler(_directory):
        calls.append("import")
        view.bulk_import()

        class Discovered:
            discovered_count = 0
            duplicate_count = 0

        return {
            "games": [],
            "discovered": Discovered(),
            "added_count": 0,
            "skipped_count": 0,
            "persisted": {
                "added": False,
            },
        }

    view = GalleryView(
        [],
        bulk_import_handler=handler,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *_args, **_kwargs: "/roms",
    )

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *_args, **_kwargs: None,
    )

    view.bulk_import()

    assert calls == [
        "import",
    ]


def test_bulk_import_ignores_request_during_refresh(
    monkeypatch,
):
    QApplication.instance() or QApplication([])

    calls = []

    view = GalleryView(
        [],
        bulk_import_handler=lambda directory: (
            calls.append(directory)
        ),
    )

    view._library_refresh_in_progress = True

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *_args, **_kwargs: "/roms",
    )

    view.bulk_import()

    assert calls == []


def test_bulk_import_failure_clears_busy_state(
    monkeypatch,
):
    QApplication.instance() or QApplication([])

    def fail(_directory):
        raise OSError(
            "simulated import failure"
        )

    view = GalleryView(
        [],
        bulk_import_handler=fail,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *_args, **_kwargs: "/roms",
    )

    monkeypatch.setattr(
        QMessageBox,
        "critical",
        lambda *_args, **_kwargs: None,
    )

    view.bulk_import()

    assert (
        view._bulk_import_in_progress
        is False
    )

    assert (
        view.toolbar.bulk_import_button.isEnabled()
        is True
    )

    assert (
        view.toolbar.refresh_button.isEnabled()
        is True
    )


def test_bulk_import_cancel_does_not_enter_busy_state(
    monkeypatch,
):
    QApplication.instance() or QApplication([])

    view = GalleryView(
        [],
        bulk_import_handler=lambda directory: None,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *_args, **_kwargs: "",
    )

    view.bulk_import()

    assert (
        view._bulk_import_in_progress
        is False
    )

    assert (
        view.toolbar.bulk_import_button.isEnabled()
        is True
    )

    assert (
        view.toolbar.refresh_button.isEnabled()
        is True
    )


def test_bulk_import_completion_failure_clears_busy_state(
    monkeypatch,
):
    QApplication.instance() or QApplication([])

    class Discovered:
        discovered_count = 1
        duplicate_count = 0

    def import_handler(_directory):
        return {
            "games": [],
            "discovered": Discovered(),
            "added_count": 1,
            "skipped_count": 0,
            "persisted": {
                "added": True,
            },
        }

    def completed(_result):
        raise RuntimeError(
            "dependent refresh failed"
        )

    view = GalleryView(
        [],
        bulk_import_handler=import_handler,
        bulk_import_completed_handler=completed,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *_args, **_kwargs: "/roms",
    )

    information_calls = []

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: (
            information_calls.append(
                (args, kwargs)
            )
        ),
    )

    view.bulk_import()

    assert (
        view._bulk_import_in_progress
        is False
    )

    assert (
        view.toolbar.bulk_import_button.isEnabled()
        is True
    )

    assert (
        view.toolbar.refresh_button.isEnabled()
        is True
    )

    assert information_calls == []


def test_bulk_import_completion_failure_preserves_imported_snapshot(
    monkeypatch,
):
    QApplication.instance() or QApplication([])

    imported = FakeGame(
        "Completion Failure",
        "/roms/completion-failure.sfc",
        "SNES",
    )

    class Discovered:
        discovered_count = 1
        duplicate_count = 0

    def import_handler(_directory):
        return {
            "games": [imported],
            "discovered": Discovered(),
            "added_count": 1,
            "skipped_count": 0,
            "persisted": {
                "added": True,
            },
        }

    def completed(_result):
        raise ValueError(
            "dependent refresh failed"
        )

    view = GalleryView(
        [],
        bulk_import_handler=import_handler,
        bulk_import_completed_handler=completed,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *_args, **_kwargs: "/roms",
    )

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *_args, **_kwargs: None,
    )

    view.bulk_import()

    assert view.all_games == [
        imported,
    ]

    assert (
        view._bulk_import_in_progress
        is False
    )


def test_bulk_import_can_retry_after_completion_failure(
    monkeypatch,
):
    QApplication.instance() or QApplication([])

    completion_calls = []

    class Discovered:
        discovered_count = 0
        duplicate_count = 0

    def import_handler(_directory):
        return {
            "games": [],
            "discovered": Discovered(),
            "added_count": 0,
            "skipped_count": 0,
            "persisted": {
                "added": False,
            },
        }

    def completed(_result):
        completion_calls.append(
            "completed"
        )

        if len(completion_calls) == 1:
            raise OSError(
                "first completion failed"
            )

    view = GalleryView(
        [],
        bulk_import_handler=import_handler,
        bulk_import_completed_handler=completed,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *_args, **_kwargs: "/roms",
    )

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *_args, **_kwargs: None,
    )

    view.bulk_import()
    view.bulk_import()

    assert completion_calls == [
        "completed",
        "completed",
    ]

    assert (
        view._bulk_import_in_progress
        is False
    )

    assert (
        view.toolbar.bulk_import_button.isEnabled()
        is True
    )

    assert (
        view.toolbar.refresh_button.isEnabled()
        is True
    )


def test_bulk_import_completion_failure_adds_no_new_popup():
    from pathlib import Path
    import ast

    text = Path(
        "ui/library/gallery.py"
    ).read_text(
        encoding="utf-8"
    )

    tree = ast.parse(text)

    gallery = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "GalleryView"
    )

    method = next(
        node
        for node in gallery.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "bulk_import"
    )

    post_handler_try = next(
        node
        for node in method.body
        if (
            isinstance(node, ast.Try)
            and node.finalbody
        )
    )

    source = ast.get_source_segment(
        text,
        post_handler_try,
    )

    assert source is not None

    assert (
        "self.bulk_import_completed_handler("
        in source
    )

    for forbidden in (
        "QMessageBox",
        ".critical(",
        ".warning(",
        ".information(",
    ):
        assert forbidden not in source

def test_bulk_import_malformed_result_clears_busy_state(
    monkeypatch,
):
    QApplication.instance() or QApplication([])

    view = GalleryView([])

    calls = []

    view.bulk_import_handler = lambda directory: {
        "games": [],
        "persisted": {
            "added": True,
        },
    }

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: "/roms",
    )

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: calls.append(
            "information"
        ),
    )

    view.bulk_import()

    assert (
        view._bulk_import_in_progress
        is False
    )

    assert (
        view.toolbar.bulk_import_button.isEnabled()
        is True
    )

    assert (
        view.toolbar.refresh_button.isEnabled()
        is True
    )

    assert calls == []


def test_bulk_import_malformed_result_can_retry(
    monkeypatch,
):
    QApplication.instance() or QApplication([])

    view = GalleryView([])

    attempts = []

    class Discovered:
        discovered_count = 0
        duplicate_count = 0

    def handler(directory):
        attempts.append(directory)

        if len(attempts) == 1:
            return {
                "games": [],
            }

        return {
            "games": [],
            "discovered": Discovered(),
            "added_count": 0,
            "skipped_count": 0,
            "persisted": {
                "added": False,
            },
        }

    view.bulk_import_handler = handler

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: "/roms",
    )

    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: None,
    )

    view.bulk_import()
    view.bulk_import()

    assert attempts == [
        "/roms",
        "/roms",
    ]

    assert (
        view._bulk_import_in_progress
        is False
    )


def test_bulk_import_snapshot_failure_finalizes_controls(
    monkeypatch,
):
    QApplication.instance() or QApplication([])

    view = GalleryView([])

    class BrokenGames:
        def __iter__(self):
            raise RuntimeError(
                "snapshot failed"
            )

    class Discovered:
        discovered_count = 1
        duplicate_count = 0

    view.bulk_import_handler = lambda directory: {
        "games": BrokenGames(),
        "discovered": Discovered(),
        "added_count": 1,
        "skipped_count": 0,
        "persisted": {
            "added": True,
        },
    }

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: "/roms",
    )

    view.bulk_import()

    assert (
        view._bulk_import_in_progress
        is False
    )

    assert (
        view.toolbar.bulk_import_button.isEnabled()
        is True
    )

    assert (
        view.toolbar.refresh_button.isEnabled()
        is True
    )


def test_bulk_import_post_handler_failure_adds_no_popup_contract():
    from pathlib import Path
    import ast

    text = Path(
        "ui/library/gallery.py"
    ).read_text(
        encoding="utf-8"
    )

    tree = ast.parse(text)

    gallery = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef)
        and node.name == "GalleryView"
    )

    method = next(
        node
        for node in gallery.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "bulk_import"
    )

    post_handler_try = next(
        node
        for node in method.body
        if (
            isinstance(node, ast.Try)
            and node.finalbody
        )
    )

    assert len(
        post_handler_try.handlers
    ) == 1

    handler = post_handler_try.handlers[0]

    assert isinstance(
        handler.type,
        ast.Tuple,
    )

    caught = {
        item.id
        for item in handler.type.elts
        if isinstance(item, ast.Name)
    }

    assert caught == {
        "KeyError",
        "OSError",
        "RuntimeError",
        "TypeError",
        "ValueError",
    }

    source = ast.get_source_segment(
        text,
        post_handler_try,
    )

    assert source is not None

    assert "QMessageBox" not in source

    final_source = "\n".join(
        ast.get_source_segment(
            text,
            node,
        )
        or ""
        for node in post_handler_try.finalbody
    )

    assert (
        "self._bulk_import_in_progress = False"
        in final_source
    )

    assert (
        "self.toolbar.bulk_import_button.setEnabled"
        in final_source
    )

    assert (
        "self.toolbar.refresh_button.setEnabled"
        in final_source
    )
