import inspect

import yaml
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMessageBox,
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
):
    app()

    overlays = tmp_path / "overlays"
    shaders = tmp_path / "shaders"

    overlays.mkdir()
    shaders.mkdir()

    defaults = tmp_path / "defaults.yaml"
    runtime = tmp_path / "runtime.json"

    defaults.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "overlays": {
                        "directory": str(
                            overlays
                        ),
                    },
                    "shaders": {
                        "directory": str(
                            shaders
                        ),
                    },
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    page = OverlaysPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        )
    )

    return page, overlays, shaders


def make_shader_package(
    tmp_path,
):
    package = tmp_path / "shader-pack"
    package.mkdir()

    (
        package / "display.slangp"
    ).write_text(
        'shader0 = "display.slang"\n',
        encoding="utf-8",
    )

    (
        package / "display.slang"
    ).write_text(
        "shader",
        encoding="utf-8",
    )

    (
        package / "support.params"
    ).write_text(
        "parameters",
        encoding="utf-8",
    )

    return package


def test_organizer_button_is_available(
    tmp_path,
):
    page, _overlays, _shaders = (
        make_page(tmp_path)
    )

    assert page.organize_button.text() == (
        "Organize Assets…"
    )


def test_cancelled_folder_dialog_does_nothing(
    tmp_path,
    monkeypatch,
):
    page, _overlays, _shaders = (
        make_page(tmp_path)
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: "",
    )

    page.choose_organizer_source()

    assert page.status_label.text() == (
        "No installed overlay descriptors "
        "were found in this directory."
    )


def test_declined_shader_package_is_not_moved(
    tmp_path,
    monkeypatch,
):
    page, _overlays, shaders = (
        make_page(tmp_path)
    )
    package = make_shader_package(
        tmp_path
    )

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: (
            QMessageBox.StandardButton.No
        ),
    )

    result = page.organize_directory(
        package
    )

    assert result is None
    assert package.is_dir()
    assert not (
        shaders / package.name
    ).exists()
    assert page.status_label.text() == (
        "Asset organization cancelled."
    )


def test_confirmed_shader_package_moves_and_emits(
    tmp_path,
    monkeypatch,
):
    page, _overlays, shaders = (
        make_page(tmp_path)
    )
    package = make_shader_package(
        tmp_path
    )

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: (
            QMessageBox.StandardButton.Yes
        ),
    )
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: None,
    )

    emissions = []
    page.assets_organized.connect(
        lambda: emissions.append(True)
    )

    result = page.organize_directory(
        package
    )

    destination = (
        shaders / package.name
    )

    assert result is not None
    assert not package.exists()
    assert destination.is_dir()
    assert (
        destination / "display.slangp"
    ).is_file()
    assert (
        destination / "support.params"
    ).is_file()
    assert emissions == [True]
    assert page.status_label.text() == (
        "Moved shader package: 3 files."
    )


def test_confirmed_overlay_import_moves_assets(
    tmp_path,
    monkeypatch,
):
    page, overlays, _shaders = (
        make_page(tmp_path)
    )

    source = tmp_path / "import"
    source.mkdir()

    image = source / "frame.png"
    image.write_bytes(b"image")

    config = source / "console.cfg"
    config.write_text(
        (
            'overlays = "1"\n'
            'overlay0_overlay = "frame.png"\n'
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *args, **kwargs: (
            QMessageBox.StandardButton.Yes
        ),
    )
    monkeypatch.setattr(
        QMessageBox,
        "information",
        lambda *args, **kwargs: None,
    )

    result = page.organize_directory(
        source
    )

    assert result is not None
    assert not config.exists()
    assert not image.exists()
    assert (
        overlays / "console.cfg"
    ).is_file()
    assert (
        overlays / "frame.png"
    ).is_file()
    assert page.overlay_list.count() == 1


def test_invalid_folder_shows_warning(
    tmp_path,
    monkeypatch,
):
    page, _overlays, _shaders = (
        make_page(tmp_path)
    )

    warnings = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args: warnings.append(
            args
        ),
    )

    result = page.organize_directory(
        tmp_path / "missing"
    )

    assert result is None
    assert len(warnings) == 1


def test_main_window_refreshes_shaders_after_move():
    source = inspect.getsource(
        MainWindow.__init__
    )

    assert (
        "overlays_page."
        "assets_organized.connect("
        in source
    )
    assert (
        "shaders_page.refresh_shaders"
        in source
    )
