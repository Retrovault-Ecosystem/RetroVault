import inspect

import yaml
from PyQt6.QtWidgets import (
    QApplication,
)

from config import ConfigLoader
from ui.pages.shaders_page import (
    ShadersPage,
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
    shader_directory,
):
    app()

    defaults = tmp_path / "defaults.yaml"
    runtime = tmp_path / "runtime.json"

    defaults.write_text(
        yaml.safe_dump(
            {
                "paths": {
                    "shaders": {
                        "directory": str(
                            shader_directory
                        ),
                    },
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    return ShadersPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        )
    )


def make_shader(
    root,
    name="display",
    missing=False,
):
    package = root / "crt"
    package.mkdir(
        parents=True,
        exist_ok=True,
    )

    shader = package / f"{name}.slang"

    if not missing:
        shader.write_text(
            "shader",
            encoding="utf-8",
        )

    preset = package / f"{name}.slangp"
    preset.write_text(
        f'shader0 = "{name}.slang"\n',
        encoding="utf-8",
    )

    return preset


def test_page_shows_effective_directory(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    page = make_page(
        tmp_path,
        root,
    )

    assert page.path_label.text() == str(root)


def test_empty_directory_has_clear_state(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    page = make_page(
        tmp_path,
        root,
    )

    assert page.shader_list.count() == 0
    assert page.count_label.text() == (
        "0 installed shader presets"
    )
    assert page.status_label.text() == (
        "No installed shader presets "
        "were found in this directory."
    )


def test_missing_directory_has_clear_state(
    tmp_path,
):
    root = tmp_path / "missing"

    page = make_page(
        tmp_path,
        root,
    )

    assert page.status_label.text() == (
        "The configured shader directory "
        "does not exist."
    )


def test_page_lists_recursive_presets(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    make_shader(
        root,
        "display",
    )

    page = make_page(
        tmp_path,
        root,
    )

    assert page.shader_list.count() == 1
    assert page.shader_list.item(
        0
    ).text() == "display"
    assert page.count_label.text() == (
        "1 installed shader preset"
    )


def test_selecting_shader_shows_details(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    preset = make_shader(
        root,
        "crt-royale",
    )

    page = make_page(
        tmp_path,
        root,
    )

    page.shader_list.setCurrentRow(0)

    assert page.name_value.text() == (
        "crt royale"
    )
    assert page.type_value.text() == "Slang"
    assert page.preset_value.text() == str(
        preset.relative_to(root)
    )
    assert page.passes_value.text() == "1"
    assert page.missing_value.text() == "0"
    assert page.readiness_value.text() == (
        "Ready"
    )


def test_missing_dependency_is_reported(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    make_shader(
        root,
        "broken",
        missing=True,
    )

    page = make_page(
        tmp_path,
        root,
    )

    page.shader_list.setCurrentRow(0)

    assert page.missing_value.text() == "1"
    assert page.readiness_value.text() == (
        "Missing dependencies"
    )


def test_refresh_clears_stale_details(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    preset = make_shader(
        root,
        "temporary",
    )

    page = make_page(
        tmp_path,
        root,
    )

    page.shader_list.setCurrentRow(0)
    preset.unlink()
    page.refresh_button.click()

    assert page.shader_list.count() == 0
    assert page.name_value.text() == (
        "Select a shader preset"
    )
    assert page.preset_value.text() == "—"


def test_set_directory_refreshes_immediately(
    tmp_path,
):
    original = tmp_path / "original"
    original.mkdir()

    selected = tmp_path / "selected"
    selected.mkdir()
    make_shader(
        selected,
        "new-shader",
    )

    page = make_page(
        tmp_path,
        original,
    )

    page.set_directory(
        str(selected)
    )

    assert page.shader_directory == selected
    assert page.path_label.text() == (
        str(selected)
    )
    assert page.shader_list.count() == 1
    assert page.shader_list.item(
        0
    ).text() == "new shader"


def test_page_uses_shader_service_boundary():
    source = inspect.getsource(
        ShadersPage
    )

    assert "ShaderService" in source
    assert ".rglob(" not in source
    assert ".read_text(" not in source
