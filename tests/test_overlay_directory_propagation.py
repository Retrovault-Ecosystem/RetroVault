import inspect

import yaml
from PyQt6.QtWidgets import (
    QApplication,
)

from config import ConfigLoader
from ui.main_window import MainWindow
from ui.pages.overlays_page import (
    OverlaysPage,
)


_QT_APP = None


def app():
    global _QT_APP

    instance = QApplication.instance()

    if instance is None:
        instance = QApplication([])

    _QT_APP = instance

    return instance


def make_page(
    tmp_path,
    directory,
):
    app()

    defaults = tmp_path / "defaults.yaml"
    runtime = tmp_path / "runtime.json"

    defaults.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "overlays": {
                        "directory": str(
                            directory
                        ),
                    },
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    return OverlaysPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        )
    )


def test_set_directory_updates_page_immediately(
    tmp_path,
):
    original = tmp_path / "original"
    original.mkdir()

    selected = tmp_path / "selected"
    selected.mkdir()

    page = make_page(
        tmp_path,
        original,
    )

    page.set_directory(
        str(selected)
    )

    assert page.overlay_directory == selected
    assert page.path_label.text() == (
        str(selected)
    )
    assert page.count_label.text() == (
        "0 installed overlays"
    )
    assert page.status_label.text() == (
        "No installed overlay descriptors "
        "were found in this directory."
    )


def test_set_directory_clears_stale_selection(
    tmp_path,
):
    original = tmp_path / "original"
    original.mkdir()

    selected = tmp_path / "selected"
    selected.mkdir()

    page = make_page(
        tmp_path,
        original,
    )

    page.name_value.setText(
        "Stale overlay"
    )
    page.config_value.setText(
        "stale.cfg"
    )

    page.set_directory(
        str(selected)
    )

    assert page.name_value.text() == (
        "Select an overlay"
    )
    assert page.config_value.text() == "—"
    assert page.preview.text() == (
        "No preview"
    )


def test_set_missing_directory_updates_state(
    tmp_path,
):
    original = tmp_path / "original"
    original.mkdir()

    missing = tmp_path / "missing"

    page = make_page(
        tmp_path,
        original,
    )

    page.set_directory(
        str(missing)
    )

    assert page.overlay_directory == missing
    assert page.path_label.text() == (
        str(missing)
    )
    assert page.status_label.text() == (
        "The configured overlay directory "
        "does not exist."
    )


def test_main_window_connects_overlay_save_signal():
    source = inspect.getsource(
        MainWindow.__init__
    )

    assert (
        "settings_page."
        "overlay_directory_saved.connect("
        in source
    )
    assert (
        "overlays_page.set_directory"
        in source
    )
