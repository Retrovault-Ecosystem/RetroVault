from pathlib import Path


def test_main_window_bulk_import_synchronizes_application_surfaces():
    source = Path(
        "ui/main_window.py"
    ).read_text(
        encoding="utf-8"
    )

    assert (
        "def bulk_import_completed("
        in source
    )

    assert (
        "systems_page.refresh_page()"
        in source
    )

    assert (
        "playlists_page.refresh_collections("
        in source
    )

    assert (
        "bulk_import_completed_handler=("
        in source
    )

    assert (
        "bulk_import_completed"
        in source
    )


def test_bulk_import_callback_runs_after_library_snapshot_refresh():
    source = Path(
        "ui/library/gallery.py"
    ).read_text(
        encoding="utf-8"
    )

    set_games = source.index(
        "self.set_games(\n"
        "                imported_games"
    )

    callback = source.index(
        "self.bulk_import_completed_handler(\n"
        "                result"
    )

    assert set_games < callback
