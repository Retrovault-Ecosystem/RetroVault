import inspect

import yaml
from PyQt6.QtWidgets import (
    QApplication,
)

from config import ConfigLoader
from services.library.models import Game
from services.library.state import game_identity
from services.presentation import (
    PresentationStore,
)
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
    presentation_store=None,
    current_game_provider=None,
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
        ),
        presentation_store=(
            presentation_store
        ),
        current_game_provider=(
            current_game_provider
        ),
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


def assignment_game(tmp_path):
    rom = tmp_path / "Duck Tales 2 (U).nes"

    return Game(
        name="Duck Tales 2",
        platform="NES",
        year=1993,
        genre="Platformer",
        core="fceumm",
        rom=str(rom),
        rvdb_platform_id="platform.nintendo.nes",
    )


def test_assignment_buttons_require_ready_selected_shader(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    make_shader(
        root,
        "broken",
        missing=True,
    )

    store = PresentationStore(
        tmp_path
        / "presentation-state.json"
    )

    game = assignment_game(
        tmp_path
    )

    page = make_page(
        tmp_path,
        root,
        presentation_store=store,
        current_game_provider=lambda: game,
    )

    page.shader_list.setCurrentRow(0)

    assert not page.default_button.isEnabled()
    assert not page.system_button.isEnabled()
    assert not page.game_button.isEnabled()


def test_default_shader_assignment_persists_selected_preset(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    preset = make_shader(
        root,
        "default-crt",
    )

    store = PresentationStore(
        tmp_path
        / "presentation-state.json"
    )

    page = make_page(
        tmp_path,
        root,
        presentation_store=store,
    )

    page.shader_list.setCurrentRow(0)
    page.default_button.click()

    data = store.load()

    assert data["default"].shader == str(
        preset.resolve(
            strict=False
        )
    )

    assert page.status_label.text() == (
        "Assigned selected shader as "
        "RetroVault default."
    )


def test_system_shader_assignment_uses_rvdb_platform_id(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    preset = make_shader(
        root,
        "nes-crt",
    )

    store = PresentationStore(
        tmp_path
        / "presentation-state.json"
    )

    game = assignment_game(
        tmp_path
    )

    page = make_page(
        tmp_path,
        root,
        presentation_store=store,
        current_game_provider=lambda: game,
    )

    page.shader_list.setCurrentRow(0)
    page.system_button.click()

    data = store.load()

    assert data["systems"][
        "platform.nintendo.nes"
    ].shader == str(
        preset.resolve(
            strict=False
        )
    )


def test_game_shader_assignment_uses_game_identity(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    preset = make_shader(
        root,
        "duck-crt",
    )

    store = PresentationStore(
        tmp_path
        / "presentation-state.json"
    )

    game = assignment_game(
        tmp_path
    )

    page = make_page(
        tmp_path,
        root,
        presentation_store=store,
        current_game_provider=lambda: game,
    )

    page.shader_list.setCurrentRow(0)
    page.game_button.click()

    data = store.load()

    identity = game_identity(
        game
    )

    assert data["games"][
        identity
    ].shader == str(
        preset.resolve(
            strict=False
        )
    )


def test_system_assignment_requires_canonical_rvdb_id(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    make_shader(
        root,
        "system-crt",
    )

    store = PresentationStore(
        tmp_path
        / "presentation-state.json"
    )

    game = assignment_game(
        tmp_path
    )
    game.rvdb_platform_id = None

    page = make_page(
        tmp_path,
        root,
        presentation_store=store,
        current_game_provider=lambda: game,
    )

    page.shader_list.setCurrentRow(0)
    page.system_button.click()

    assert not (
        store.presentation_file.exists()
    )

    assert page.status_label.text() == (
        "The selected game does not have "
        "a canonical RVDB system identity."
    )


def test_assignment_is_immediately_visible_to_lazy_resolver(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    preset = make_shader(
        root,
        "live-crt",
    )

    store = PresentationStore(
        tmp_path
        / "presentation-state.json"
    )

    game = assignment_game(
        tmp_path
    )

    page = make_page(
        tmp_path,
        root,
        presentation_store=store,
        current_game_provider=lambda: game,
    )

    page.shader_list.setCurrentRow(0)
    page.game_button.click()

    resolved = (
        store.resolver()
        .resolve(game)
    )

    assert resolved.shader == str(
        preset.resolve(
            strict=False
        )
    )
