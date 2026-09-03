import json
from pathlib import Path

import yaml
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import (
    QApplication,
)

from config.loader import ConfigLoader
from ui.pages.settings_page import (
    SettingsPage,
)


_QT_APP = None


def _user_edit(
    field,
    value,
):
    field.setFocus()
    field.selectAll()

    QTest.keyClicks(
        field,
        str(value),
    )


def _app():
    global _QT_APP

    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    _QT_APP = app

    return app


def _make_valid_retroarch(
    path,
):
    path.write_text(
        (
            "#!/bin/sh\n"
            "echo 'RetroArch - Frontend for libretro'\n"
            "echo 'Version: test'\n"
        ),
        encoding="utf-8",
    )

    path.chmod(0o755)

    return path


def _make_valid_core_directory(
    path,
):
    path.mkdir(
        parents=True,
        exist_ok=True,
    )

    core = (
        path
        / "test_libretro.so"
    )

    if not core.exists():
        core.write_bytes(
            b"test"
        )

    return path


def _write_defaults(
    tmp_path: Path,
    *,
    retroarch: Path,
    cores: Path,
    library: Path,
    overlays: Path,
    shaders: Path,
    artwork: Path = None,
    semantic_valid=True,
) -> Path:
    if semantic_valid:
        _make_valid_retroarch(
            retroarch
        )

        _make_valid_core_directory(
            cores
        )

    if artwork is None:
        artwork = (
            tmp_path
            / "artwork"
        )

    path = (
        tmp_path
        / "defaults.yaml"
    )

    data = {
        "retroarch": {
            "executable": str(
                retroarch
            ),
            "cores": {
                "directory": str(
                    cores
                ),
            },
        },
        "library": {
            "sources": [
                {
                    "id": "test",
                    "name": "Test Library",
                    "enabled": True,
                    "type": "local",
                    "path": str(
                        library
                    ),
                },
            ],
        },
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
            "artwork": {
                "directory": str(
                    artwork
                ),
            },
        },
    }

    path.write_text(
        yaml.safe_dump(
            data,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    return path


def test_settings_page_displays_effective_configuration(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )

    page = SettingsPage(
        config_loader=loader
    )

    assert (
        page.retroarch_edit.text()
        == str(retroarch)
    )

    assert (
        page.core_directory_edit.text()
        == str(cores)
    )

    assert (
        page.library_sources_value.text()
        == (
            f"Test Library — {library}"
        )
    )

    assert (
        page.overlays_value.text()
        == str(overlays)
    )

    assert (
        page.shaders_value.text()
        == str(shaders)
    )

    assert (
        page.runtime_config_value.text()
        == str(runtime)
    )

    assert (
        page.retroarch_status.text()
        == "Ready ✓"
    )

    assert (
        page.core_directory_status.text()
        == "Ready ✓"
    )

    assert (
        page.library_sources_status.text()
        == "Ready ✓"
    )

    assert (
        page.overlays_status.text()
        == "Ready"
    )

    assert (
        page.shaders_status.text()
        == "Ready"
    )

    assert (
        page.runtime_config_status.text()
        == "Defaults active"
    )

    assert not runtime.exists()


def test_settings_page_reports_missing_paths(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "missing-retroarch"
    )

    cores = (
        tmp_path
        / "missing-cores"
    )

    library = (
        tmp_path
        / "missing-roms"
    )

    overlays = (
        tmp_path
        / "missing-overlays"
    )

    shaders = (
        tmp_path
        / "missing-shaders"
    )

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
        semantic_valid=False,
    )

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=(
            tmp_path
            / "runtime.json"
        ),
    )

    page = SettingsPage(
        config_loader=loader
    )

    assert (
        page.retroarch_status.text()
        == "Missing !"
    )

    assert (
        page.core_directory_status.text()
        == "Missing !"
    )

    assert (
        page.library_sources_status.text()
        == "Missing !"
    )

    assert (
        page.overlays_status.text()
        == "Missing"
    )

    assert (
        page.shaders_status.text()
        == "Missing"
    )


def test_settings_page_reports_runtime_override_active(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    runtime.write_text(
        json.dumps(
            {
                "retroarch": {
                    "cores": {
                        "directory": str(
                            cores
                        ),
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        )
    )

    assert (
        page.runtime_config_status.text()
        == "User overrides active"
    )


def test_settings_page_does_not_create_runtime_config(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        )
    )

    assert not runtime.exists()


def test_settings_page_can_save_retroarch_runtime_overrides(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )

    from config import ConfigWriter

    writer = ConfigWriter(
        runtime_file=runtime
    )

    page = SettingsPage(
        config_loader=loader,
        config_writer=writer,
    )

    new_retroarch = (
        tmp_path
        / "custom-retroarch"
    )

    _make_valid_retroarch(
        new_retroarch
    )

    new_cores = (
        tmp_path
        / "custom-cores"
    )

    _make_valid_core_directory(
        new_cores
    )

    page.retroarch_edit.setText(
        str(new_retroarch)
    )

    page.core_directory_edit.setText(
        str(new_cores)
    )

    page.save_runtime_settings()

    assert runtime.is_file()

    saved = json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    )

    assert (
        saved[
            "retroarch"
        ][
            "executable"
        ]
        == str(new_retroarch)
    )

    assert (
        saved[
            "retroarch"
        ][
            "cores"
        ][
            "directory"
        ]
        == str(new_cores)
    )

    assert (
        page.retroarch_edit.text()
        == str(new_retroarch)
    )

    assert (
        page.core_directory_edit.text()
        == str(new_cores)
    )

    assert (
        page.retroarch_status.text()
        == "Ready ✓"
    )

    assert (
        page.core_directory_status.text()
        == "Ready ✓"
    )

    assert (
        page.runtime_config_status.text()
        == "User overrides active"
    )

    assert (
        page.save_status.text()
        == "Settings saved"
    )


def test_settings_page_save_preserves_unrelated_runtime_overrides(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    runtime.write_text(
        json.dumps(
            {
                "paths": {
                    "shaders": {
                        "directory": "/existing/shaders",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )

    from config import ConfigWriter

    writer = ConfigWriter(
        runtime_file=runtime
    )

    page = SettingsPage(
        config_loader=loader,
        config_writer=writer,
    )

    page.save_runtime_settings()

    saved = json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    )

    assert (
        saved[
            "paths"
        ][
            "shaders"
        ][
            "directory"
        ]
        == "/existing/shaders"
    )


def test_settings_page_does_not_write_until_save_is_called(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )

    from config import ConfigWriter

    writer = ConfigWriter(
        runtime_file=runtime
    )

    page = SettingsPage(
        config_loader=loader,
        config_writer=writer,
    )

    page.retroarch_edit.setText(
        "/changed/in/ui"
    )

    page.core_directory_edit.setText(
        "/changed/cores/in/ui"
    )

    assert not runtime.exists()


def test_settings_page_displays_library_path_editor(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )

    from config import ConfigWriter

    writer = ConfigWriter(
        runtime_file=runtime
    )

    page = SettingsPage(
        config_loader=loader,
        config_writer=writer,
    )

    assert (
        page.library_path_edit.text()
        == str(library)
    )

    assert not runtime.exists()


def test_settings_page_can_save_library_path_override(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )

    from config import ConfigWriter

    writer = ConfigWriter(
        runtime_file=runtime
    )

    page = SettingsPage(
        config_loader=loader,
        config_writer=writer,
    )

    new_library = (
        tmp_path
        / "new-roms"
    )

    new_library.mkdir()

    page.library_path_edit.setText(
        str(new_library)
    )

    page.save_runtime_settings()

    assert runtime.is_file()

    saved = json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    )

    assert (
        saved[
            "library"
        ][
            "sources"
        ][0][
            "id"
        ]
        == "test"
    )

    assert (
        saved[
            "library"
        ][
            "sources"
        ][0][
            "name"
        ]
        == "Test Library"
    )

    assert (
        saved[
            "library"
        ][
            "sources"
        ][0][
            "enabled"
        ]
        is True
    )

    assert (
        saved[
            "library"
        ][
            "sources"
        ][0][
            "type"
        ]
        == "local"
    )

    assert (
        saved[
            "library"
        ][
            "sources"
        ][0][
            "path"
        ]
        == str(new_library)
    )

    assert (
        page.library_path_edit.text()
        == str(new_library)
    )

    assert (
        page.library_sources_value.text()
        == (
            "Test Library — "
            f"{new_library}"
        )
    )

    assert (
        page.library_sources_status.text()
        == "Ready ✓"
    )

    assert (
        page.runtime_config_status.text()
        == "User overrides active"
    )

    assert (
        page.save_status.text()
        == "Settings saved"
    )


def test_settings_page_library_save_preserves_retroarch_overrides(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    persisted_retroarch = (
        tmp_path
        / "persisted-retroarch"
    )

    _make_valid_retroarch(
        persisted_retroarch
    )

    persisted_cores = (
        tmp_path
        / "persisted-cores"
    )

    _make_valid_core_directory(
        persisted_cores
    )

    runtime.write_text(
        json.dumps(
            {
                "retroarch": {
                    "executable": str(
                        persisted_retroarch
                    ),
                    "cores": {
                        "directory": str(
                            persisted_cores
                        ),
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )

    from config import ConfigWriter

    writer = ConfigWriter(
        runtime_file=runtime
    )

    page = SettingsPage(
        config_loader=loader,
        config_writer=writer,
    )

    new_library = (
        tmp_path
        / "new-roms"
    )

    new_library.mkdir()

    page.library_path_edit.setText(
        str(new_library)
    )

    page.save_runtime_settings()

    saved = json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    )

    assert (
        saved[
            "retroarch"
        ][
            "executable"
        ]
        == str(
            persisted_retroarch
        )
    )

    assert (
        saved[
            "retroarch"
        ][
            "cores"
        ][
            "directory"
        ]
        == str(
            persisted_cores
        )
    )

    assert (
        saved[
            "library"
        ][
            "sources"
        ][0][
            "path"
        ]
        == str(new_library)
    )


def test_settings_page_rejects_missing_library_directory(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )

    from config import ConfigWriter

    writer = ConfigWriter(
        runtime_file=runtime
    )

    page = SettingsPage(
        config_loader=loader,
        config_writer=writer,
    )

    page.library_path_edit.setText(
        str(
            tmp_path
            / "missing-roms"
        )
    )

    page.save_runtime_settings()

    assert not runtime.exists()

    assert (
        page.save_status.text()
        == "Library path is not a readable directory"
    )


def test_settings_page_library_edit_does_not_write_until_save(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )

    from config import ConfigWriter

    writer = ConfigWriter(
        runtime_file=runtime
    )

    page = SettingsPage(
        config_loader=loader,
        config_writer=writer,
    )

    page.library_path_edit.setText(
        "/changed/in/ui"
    )

    assert not runtime.exists()


def test_settings_path_editors_use_internal_placeholders(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    assert (
        page.retroarch_edit.placeholderText()
        == "RetroArch executable"
    )

    assert (
        page.core_directory_edit.placeholderText()
        == "Core directory"
    )

    assert (
        page.library_path_edit.placeholderText()
        == "Library path"
    )

    assert not runtime.exists()


def test_settings_path_editors_have_browse_buttons(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    assert (
        page.retroarch_browse_button.text()
        == "Browse…"
    )

    assert (
        page.core_directory_browse_button.text()
        == "Browse…"
    )

    assert (
        page.library_browse_button.text()
        == "Browse…"
    )

    assert not runtime.exists()


def test_path_editor_width_grows_for_longer_path(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    page.library_path_edit.setText(
        "/short/path"
    )

    short_width = (
        page.library_path_edit.width()
    )

    page.library_path_edit.setText(
        (
            "/this/is/a/considerably/longer/"
            "library/path/selected/by/the/user"
        )
    )

    long_width = (
        page.library_path_edit.width()
    )

    assert long_width > short_width

    assert (
        long_width
        <= page.PATH_EDITOR_MAX_WIDTH
    )

    assert not runtime.exists()


def test_browsing_executable_changes_field_only(
    tmp_path,
    monkeypatch,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    selected = (
        tmp_path
        / "selected-retroarch"
    )

    selected.write_text(
        "",
        encoding="utf-8",
    )

    from PyQt6.QtWidgets import QFileDialog

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        lambda *args, **kwargs: (
            str(selected),
            "",
        ),
    )

    page._browse_retroarch()

    assert (
        page.retroarch_edit.text()
        == str(selected)
    )

    assert not runtime.exists()


def test_browsing_core_directory_changes_field_only(
    tmp_path,
    monkeypatch,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    selected = (
        tmp_path
        / "selected-cores"
    )

    selected.mkdir()

    from PyQt6.QtWidgets import QFileDialog

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: str(
            selected
        ),
    )

    page._browse_core_directory()

    assert (
        page.core_directory_edit.text()
        == str(selected)
    )

    assert not runtime.exists()


def test_browsing_library_directory_changes_field_only(
    tmp_path,
    monkeypatch,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    selected = (
        tmp_path
        / "selected-library"
    )

    selected.mkdir()

    from PyQt6.QtWidgets import QFileDialog

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: str(
            selected
        ),
    )

    page._browse_library()

    assert (
        page.library_path_edit.text()
        == str(selected)
    )

    assert not runtime.exists()


def test_settings_page_has_restore_default_paths_button(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    assert (
        page.restore_defaults_button.text()
        == "Restore Default Paths"
    )

    assert not runtime.exists()


def test_restore_default_paths_restores_bundled_values_only(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    page.retroarch_edit.setText(
        "/changed/retroarch"
    )

    page.core_directory_edit.setText(
        "/changed/cores"
    )

    page.library_path_edit.setText(
        "/changed/library"
    )

    page.restore_default_paths()

    assert (
        page.retroarch_edit.text()
        == str(retroarch)
    )

    assert (
        page.core_directory_edit.text()
        == str(cores)
    )

    assert (
        page.library_path_edit.text()
        == str(library)
    )

    assert (
        page.save_status.text()
        == "Default paths restored — save to apply"
    )

    assert not runtime.exists()


def test_restore_default_paths_does_not_overwrite_existing_runtime(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    original = {
        "retroarch": {
            "executable": "/persisted/retroarch",
            "cores": {
                "directory": "/persisted/cores",
            },
        },
        "library": {
            "sources": [
                {
                    "id": "test",
                    "name": "Test Library",
                    "enabled": True,
                    "type": "local",
                    "path": "/persisted/library",
                },
            ],
        },
    }

    runtime.write_text(
        json.dumps(
            original,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    before = runtime.read_bytes()

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    page.restore_default_paths()

    after = runtime.read_bytes()

    assert after == before

    assert (
        page.retroarch_edit.text()
        == str(retroarch)
    )

    assert (
        page.core_directory_edit.text()
        == str(cores)
    )

    assert (
        page.library_path_edit.text()
        == str(library)
    )


def test_restore_default_paths_uses_actual_default_file(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "special-retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "special-cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "special-roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "special-overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "special-shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    page.retroarch_edit.setText(
        "/wrong/executable"
    )

    page.core_directory_edit.setText(
        "/wrong/cores"
    )

    page.library_path_edit.setText(
        "/wrong/library"
    )

    page.restore_default_paths()

    assert (
        page.retroarch_edit.text()
        == str(retroarch)
    )

    assert (
        page.core_directory_edit.text()
        == str(cores)
    )

    assert (
        page.library_path_edit.text()
        == str(library)
    )


def test_restore_default_paths_recalculates_field_widths(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    page.library_path_edit.setText(
        (
            "/this/is/a/very/long/path/"
            "temporarily/entered/by/the/user/"
            "before/restoring/defaults"
        )
    )

    long_width = (
        page.library_path_edit.width()
    )

    page.restore_default_paths()

    restored_width = (
        page.library_path_edit.width()
    )

    assert restored_width < long_width

    assert (
        restored_width
        >= page.PATH_EDITOR_MIN_WIDTH
    )

    assert not runtime.exists()


def test_settings_path_rows_use_inline_status(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = tmp_path / "cores"
    cores.mkdir()

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    assert (
        page.retroarch_status.text()
        == "Ready ✓"
    )

    assert (
        page.core_directory_status.text()
        == "Ready ✓"
    )

    assert (
        page.library_sources_status.text()
        == "Ready ✓"
    )

    assert not hasattr(
        page,
        "retroarch_value",
    )

    assert not hasattr(
        page,
        "core_directory_value",
    )

    assert not runtime.exists()


def test_restore_default_paths_repopulates_fields_without_writing(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = tmp_path / "cores"
    cores.mkdir()

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    page.retroarch_edit.setText(
        "/changed/retroarch"
    )

    page.core_directory_edit.setText(
        "/changed/cores"
    )

    page.library_path_edit.setText(
        "/changed/library"
    )

    page.restore_default_paths()

    assert (
        page.retroarch_edit.text()
        == str(retroarch)
    )

    assert (
        page.core_directory_edit.text()
        == str(cores)
    )

    assert (
        page.library_path_edit.text()
        == str(library)
    )

    assert (
        page.save_status.text()
        == "Default paths restored — save to apply"
    )

    assert not runtime.exists()


def test_restore_default_paths_uses_bundled_defaults_not_runtime_override(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = tmp_path / "cores"
    cores.mkdir()

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    custom_retroarch = (
        tmp_path
        / "custom-retroarch"
    )
    custom_retroarch.write_text(
        "",
        encoding="utf-8",
    )

    custom_cores = (
        tmp_path
        / "custom-cores"
    )
    custom_cores.mkdir()

    runtime = tmp_path / "runtime.json"

    runtime.write_text(
        json.dumps(
            {
                "retroarch": {
                    "executable": str(
                        custom_retroarch
                    ),
                    "cores": {
                        "directory": str(
                            custom_cores
                        ),
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    assert (
        page.retroarch_edit.text()
        == str(custom_retroarch)
    )

    assert (
        page.core_directory_edit.text()
        == str(custom_cores)
    )

    before = runtime.read_bytes()

    page.restore_default_paths()

    assert (
        page.retroarch_edit.text()
        == str(retroarch)
    )

    assert (
        page.core_directory_edit.text()
        == str(cores)
    )

    assert (
        page.library_path_edit.text()
        == str(library)
    )

    assert runtime.read_bytes() == before


def test_restore_default_button_label(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = tmp_path / "cores"
    cores.mkdir()

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    assert (
        page.restore_defaults_button.text()
        == "Restore Default Paths"
    )

    assert not runtime.exists()


def test_path_status_controls_are_buttons(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = tmp_path / "cores"
    cores.mkdir()

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter
    from PyQt6.QtWidgets import QPushButton

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    assert isinstance(
        page.retroarch_status,
        QPushButton,
    )

    assert isinstance(
        page.core_directory_status,
        QPushButton,
    )

    assert isinstance(
        page.library_sources_status,
        QPushButton,
    )

    assert (
        page.retroarch_status.text()
        == "Ready ✓"
    )

    assert (
        page.core_directory_status.text()
        == "Ready ✓"
    )

    assert (
        page.library_sources_status.text()
        == "Ready ✓"
    )

    assert not runtime.exists()


def test_editing_path_marks_validation_stale(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = tmp_path / "cores"
    cores.mkdir()

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    _user_edit(
        page.library_path_edit,
        "/a/new/unvalidated/path",
    )

    assert (
        page.library_sources_status.text()
        == "Check"
    )

    assert (
        "Validate" in
        page.library_sources_status.toolTip()
    )

    assert not runtime.exists()


def test_retroarch_check_reports_missing(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = tmp_path / "cores"
    cores.mkdir()

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    missing = (
        tmp_path
        / "missing-retroarch"
    )

    _user_edit(
        page.retroarch_edit,
        missing,
    )

    assert (
        page.retroarch_status.text()
        == "Check"
    )

    page.retroarch_status.click()

    assert (
        page.retroarch_status.text()
        == "Missing !"
    )

    assert (
        str(missing)
        in page.retroarch_status.toolTip()
    )

    assert not runtime.exists()


def test_core_check_reports_ready(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = tmp_path / "cores"
    cores.mkdir()

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    selected = tmp_path / "new-cores"

    _make_valid_core_directory(
        selected
    )

    _user_edit(
        page.core_directory_edit,
        selected,
    )

    assert (
        page.core_directory_status.text()
        == "Check"
    )

    page.core_directory_status.click()

    assert (
        page.core_directory_status.text()
        == "Ready ✓"
    )

    assert (
        str(selected)
        in page.core_directory_status.toolTip()
    )

    assert not runtime.exists()


def test_library_check_reports_ready_without_writing(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = tmp_path / "cores"
    cores.mkdir()

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    selected = tmp_path / "new-library"
    selected.mkdir()

    _user_edit(
        page.library_path_edit,
        selected,
    )

    assert (
        page.library_sources_status.text()
        == "Check"
    )

    page.library_sources_status.click()

    assert (
        page.library_sources_status.text()
        == "Ready ✓"
    )

    assert (
        str(selected)
        in page.library_sources_status.toolTip()
    )

    assert not runtime.exists()


def test_path_validation_buttons_do_not_save_runtime(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = tmp_path / "cores"
    cores.mkdir()

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    page.retroarch_status.click()
    page.core_directory_status.click()
    page.library_sources_status.click()

    assert not runtime.exists()




def test_restore_default_paths_reports_missing_defaults_immediately(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "missing-retroarch"
    )

    cores = (
        tmp_path
        / "missing-cores"
    )

    library = (
        tmp_path
        / "missing-library"
    )

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
        semantic_valid=False,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    page.restore_default_paths()

    assert (
        page.retroarch_status.text()
        == "Missing !"
    )

    assert (
        page.core_directory_status.text()
        == "Missing !"
    )

    assert (
        page.library_sources_status.text()
        == "Missing !"
    )

    assert (
        str(retroarch)
        in page.retroarch_status.toolTip()
    )

    assert (
        str(cores)
        in page.core_directory_status.toolTip()
    )

    assert (
        str(library)
        in page.library_sources_status.toolTip()
    )

    assert (
        page.save_status.text()
        == "Default paths restored — save to apply"
    )

    assert not runtime.exists()








def test_restore_default_paths_immediately_revalidates_all_paths(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    page.retroarch_edit.setText(
        "/changed/retroarch"
    )

    page.core_directory_edit.setText(
        "/changed/cores"
    )

    page.library_path_edit.setText(
        "/changed/library"
    )

    page._mark_status_unchecked(
        page.retroarch_status,
        "Validate the RetroArch executable path",
    )

    page._mark_status_unchecked(
        page.core_directory_status,
        "Validate the RetroArch core directory",
    )

    page._mark_status_unchecked(
        page.library_sources_status,
        "Validate the library directory",
    )

    assert (
        page.retroarch_status.text()
        == "Check"
    )

    assert (
        page.core_directory_status.text()
        == "Check"
    )

    assert (
        page.library_sources_status.text()
        == "Check"
    )

    page.restore_default_paths()

    assert (
        page.retroarch_edit.text()
        == str(retroarch)
    )

    assert (
        page.core_directory_edit.text()
        == str(cores)
    )

    assert (
        page.library_path_edit.text()
        == str(library)
    )

    assert (
        page.retroarch_status.text()
        == "Ready ✓"
    )

    assert (
        page.core_directory_status.text()
        == "Ready ✓"
    )

    assert (
        page.library_sources_status.text()
        == "Ready ✓"
    )

    assert (
        str(retroarch)
        in page.retroarch_status.toolTip()
    )

    assert (
        str(cores)
        in page.core_directory_status.toolTip()
    )

    assert (
        str(library)
        in page.library_sources_status.toolTip()
    )

    assert (
        page.save_status.text()
        == "Default paths restored — save to apply"
    )

    assert not runtime.exists()


def test_restore_default_revalidation_does_not_write_existing_runtime(
    tmp_path,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    runtime.write_text(
        (
            '{\n'
            '  "unrelated": {\n'
            '    "preserve": true\n'
            '  }\n'
            '}\n'
        ),
        encoding="utf-8",
    )

    before = runtime.read_bytes()

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    page.restore_default_paths()

    after = runtime.read_bytes()

    assert after == before

    assert (
        page.retroarch_status.text()
        == "Ready ✓"
    )

    assert (
        page.core_directory_status.text()
        == "Ready ✓"
    )

    assert (
        page.library_sources_status.text()
        == "Ready ✓"
    )


def test_path_status_controls_use_ready_check_button():
    _app()

    from ui.pages.settings_page import (
        ReadyCheckButton,
    )

    page = SettingsPage()

    assert isinstance(
        page.retroarch_status,
        ReadyCheckButton,
    )

    assert isinstance(
        page.core_directory_status,
        ReadyCheckButton,
    )

    assert isinstance(
        page.library_sources_status,
        ReadyCheckButton,
    )


def test_ready_check_button_preserves_status_text_contract():
    _app()

    from ui.pages.settings_page import (
        ReadyCheckButton,
    )

    button = ReadyCheckButton(
        "Ready ✓"
    )

    assert (
        button.text()
        == "Ready ✓"
    )

    assert button.ready_check_visible()

    button.setText(
        "Check"
    )

    assert (
        button.text()
        == "Check"
    )

    assert not button.ready_check_visible()

    button.setText(
        "Missing !"
    )

    assert (
        button.text()
        == "Missing !"
    )

    assert not button.ready_check_visible()

    button.setText(
        "Ready ✓"
    )

    assert button.ready_check_visible()


def test_ready_check_button_uses_green_check_color():
    _app()

    from ui.pages.settings_page import (
        ReadyCheckButton,
    )

    button = ReadyCheckButton(
        "Ready ✓"
    )

    color = button.ready_check_color()

    assert color.isValid()

    assert (
        color.green()
        > color.red()
    )

    assert (
        color.green()
        > color.blue()
    )


def test_retroarch_validation_rejects_non_retroarch_executable(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = tmp_path / "cores"
    cores.mkdir()

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    page.retroarch_edit.setText(
        "/bin/ls"
    )

    ready = page._validate_retroarch_path()

    assert ready is False

    assert (
        page.retroarch_status.text()
        == page.STATUS_MISSING_TEXT
    )

    assert not runtime.exists()


def test_retroarch_validation_accepts_identifying_executable(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"

    retroarch.write_text(
        (
            "#!/bin/sh\n"
            "echo 'RetroArch - Frontend for libretro'\n"
            "echo 'Version: 1.22.2'\n"
        ),
        encoding="utf-8",
    )

    retroarch.chmod(0o755)

    cores = tmp_path / "cores"
    cores.mkdir()

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    ready = page._validate_retroarch_path()

    assert ready is True

    assert (
        page.retroarch_status.text()
        == page.STATUS_READY_TEXT
    )

    assert not runtime.exists()


def test_core_validation_rejects_directory_without_libretro_core(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = tmp_path / "cores"
    cores.mkdir()

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
        semantic_valid=False,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    ready = page._validate_core_directory()

    assert ready is False

    assert (
        page.core_directory_status.text()
        == page.STATUS_MISSING_TEXT
    )

    assert not runtime.exists()


def test_core_validation_accepts_nested_libretro_core(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = tmp_path / "cores"
    cores.mkdir()

    nested = cores / "lr-example"
    nested.mkdir()

    (
        nested
        / "example_libretro.so"
    ).write_bytes(
        b"test"
    )

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    ready = page._validate_core_directory()

    assert ready is True

    assert (
        page.core_directory_status.text()
        == page.STATUS_READY_TEXT
    )

    assert not runtime.exists()


def test_save_rejects_non_retroarch_executable(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"

    retroarch.write_text(
        (
            "#!/bin/sh\n"
            "echo 'not retroarch'\n"
        ),
        encoding="utf-8",
    )

    retroarch.chmod(0o755)

    cores = tmp_path / "cores"
    cores.mkdir()

    nested = cores / "lr-example"
    nested.mkdir()

    (
        nested
        / "example_libretro.so"
    ).write_bytes(
        b"test"
    )

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
        semantic_valid=False,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    page.save_runtime_settings()

    assert not runtime.exists()

    assert "RetroArch" in (
        page.save_status.text()
    )


def test_save_rejects_directory_without_libretro_core(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"

    retroarch.write_text(
        (
            "#!/bin/sh\n"
            "echo 'RetroArch - Frontend for libretro'\n"
            "echo 'Version: 1.22.2'\n"
        ),
        encoding="utf-8",
    )

    retroarch.chmod(0o755)

    cores = tmp_path / "cores"
    cores.mkdir()

    library = tmp_path / "roms"
    library.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
        semantic_valid=False,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    page.save_runtime_settings()

    assert not runtime.exists()

    assert "core" in (
        page.save_status.text().lower()
    )


def test_browse_dialogs_use_non_native_qt_dialogs(
    tmp_path,
    monkeypatch,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )

    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    from PyQt6.QtWidgets import QFileDialog

    calls = []

    def fake_open(
        *args,
        **kwargs,
    ):
        calls.append(
            (
                "file",
                kwargs.get(
                    "options"
                ),
            )
        )

        return (
            "",
            "",
        )

    def fake_directory(
        *args,
        **kwargs,
    ):
        calls.append(
            (
                "directory",
                kwargs.get(
                    "options"
                ),
            )
        )

        return ""

    monkeypatch.setattr(
        QFileDialog,
        "getOpenFileName",
        fake_open,
    )

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        fake_directory,
    )

    page._browse_retroarch()
    page._browse_core_directory()
    page._browse_library()

    assert len(calls) == 3

    dont_use_native = (
        QFileDialog.Option
        .DontUseNativeDialog
    )

    show_dirs_only = (
        QFileDialog.Option
        .ShowDirsOnly
    )

    file_options = calls[0][1]

    core_options = calls[1][1]

    library_options = calls[2][1]

    assert (
        file_options
        & dont_use_native
    )

    assert (
        core_options
        & dont_use_native
    )

    assert (
        library_options
        & dont_use_native
    )

    assert (
        core_options
        & show_dirs_only
    )

    assert (
        library_options
        & show_dirs_only
    )

    assert not runtime.exists()


def test_settings_page_displays_artwork_directory_editor(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    cores = tmp_path / "cores"
    library = tmp_path / "roms"
    overlays = tmp_path / "overlays"
    shaders = tmp_path / "shaders"
    artwork = tmp_path / "artwork"

    library.mkdir()
    overlays.mkdir()
    shaders.mkdir()
    artwork.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
        artwork=artwork,
    )

    runtime = tmp_path / "runtime.json"

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        )
    )

    assert (
        page.artwork_directory_edit.text()
        == str(artwork)
    )

    assert (
        page.artwork_directory_status.text()
        == "Ready ✓"
    )

    assert (
        page.artwork_directory_browse_button.text()
        == "Browse…"
    )

    assert not runtime.exists()


def test_settings_page_can_save_artwork_directory_override(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    cores = tmp_path / "cores"
    library = tmp_path / "roms"
    overlays = tmp_path / "overlays"
    shaders = tmp_path / "shaders"
    artwork = tmp_path / "artwork"

    library.mkdir()
    overlays.mkdir()
    shaders.mkdir()
    artwork.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
        artwork=artwork,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    new_artwork = (
        tmp_path
        / "custom-artwork"
    )

    new_artwork.mkdir()

    page.artwork_directory_edit.setText(
        str(new_artwork)
    )

    page.save_runtime_settings()

    assert runtime.is_file()

    saved = json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    )

    assert (
        saved[
            "paths"
        ][
            "artwork"
        ][
            "directory"
        ]
        == str(new_artwork)
    )

    assert (
        page.artwork_directory_edit.text()
        == str(new_artwork)
    )

    assert (
        page.artwork_directory_status.text()
        == "Ready ✓"
    )

    assert (
        page.save_status.text()
        == "Settings saved"
    )


def test_settings_page_allows_missing_artwork_directory(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    cores = tmp_path / "cores"
    library = tmp_path / "roms"
    overlays = tmp_path / "overlays"
    shaders = tmp_path / "shaders"
    artwork = tmp_path / "artwork"

    library.mkdir()
    overlays.mkdir()
    shaders.mkdir()
    artwork.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
        artwork=artwork,
    )

    runtime = tmp_path / "runtime.json"

    from config import ConfigWriter

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    missing = (
        tmp_path
        / "missing-artwork"
    )

    page.artwork_directory_edit.setText(
        str(missing)
    )

    page.save_runtime_settings()

    assert runtime.is_file()

    saved = json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    )

    assert (
        saved[
            "paths"
        ][
            "artwork"
        ][
            "directory"
        ]
        == str(missing)
    )

    assert (
        page.artwork_directory_status.text()
        == "Missing !"
    )

    assert (
        page.save_status.text()
        == "Settings saved"
    )


def test_settings_page_browses_artwork_with_non_native_dialog(
    tmp_path,
    monkeypatch,
):
    _app()

    retroarch = tmp_path / "retroarch"
    cores = tmp_path / "cores"
    library = tmp_path / "roms"
    overlays = tmp_path / "overlays"
    shaders = tmp_path / "shaders"
    artwork = tmp_path / "artwork"

    library.mkdir()
    overlays.mkdir()
    shaders.mkdir()
    artwork.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
        artwork=artwork,
    )

    runtime = tmp_path / "runtime.json"

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        )
    )

    selected = (
        tmp_path
        / "selected-artwork"
    )

    selected.mkdir()

    captured = {}

    from PyQt6.QtWidgets import QFileDialog

    def fake_get_existing_directory(
        parent,
        caption,
        directory,
        *,
        options,
    ):
        captured["parent"] = parent
        captured["caption"] = caption
        captured["directory"] = directory
        captured["options"] = options

        return str(selected)

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        fake_get_existing_directory,
    )

    page._browse_artwork_directory()

    assert (
        page.artwork_directory_edit.text()
        == str(selected)
    )

    assert (
        page.artwork_directory_status.text()
        == "Ready ✓"
    )

    assert (
        captured["caption"]
        == "Choose artwork directory"
    )

    assert (
        captured["options"]
        & QFileDialog.Option.ShowDirsOnly
    )

    assert (
        captured["options"]
        & QFileDialog.Option.DontUseNativeDialog
    )

    assert not runtime.exists()


def test_restore_default_paths_restores_artwork_directory(
    tmp_path,
):
    _app()

    retroarch = tmp_path / "retroarch"
    cores = tmp_path / "cores"
    library = tmp_path / "roms"
    overlays = tmp_path / "overlays"
    shaders = tmp_path / "shaders"
    artwork = tmp_path / "artwork"

    library.mkdir()
    overlays.mkdir()
    shaders.mkdir()
    artwork.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
        artwork=artwork,
    )

    runtime = tmp_path / "runtime.json"

    page = SettingsPage(
        config_loader=ConfigLoader(
            default_file=defaults,
            runtime_file=runtime,
        )
    )

    page.artwork_directory_edit.setText(
        "/changed/artwork"
    )

    page.restore_default_paths()

    assert (
        page.artwork_directory_edit.text()
        == str(artwork)
    )

    assert (
        page.artwork_directory_status.text()
        == "Ready ✓"
    )

    assert not runtime.exists()


def test_successful_save_emits_effective_artwork_directory(
    tmp_path,
    monkeypatch,
):
    _app()

    retroarch = (
        tmp_path
        / "retroarch"
    )
    retroarch.write_text(
        "",
        encoding="utf-8",
    )

    cores = (
        tmp_path
        / "cores"
    )
    cores.mkdir()

    library = (
        tmp_path
        / "roms"
    )
    library.mkdir()

    overlays = (
        tmp_path
        / "overlays"
    )
    overlays.mkdir()

    shaders = (
        tmp_path
        / "shaders"
    )
    shaders.mkdir()

    artwork = (
        tmp_path
        / "artwork"
    )
    artwork.mkdir()

    defaults = _write_defaults(
        tmp_path,
        retroarch=retroarch,
        cores=cores,
        library=library,
        overlays=overlays,
        shaders=shaders,
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )

    from config import ConfigWriter

    writer = ConfigWriter(
        runtime_file=runtime
    )

    page = SettingsPage(
        config_loader=loader,
        config_writer=writer,
    )

    page.artwork_directory_edit.setText(
        str(artwork)
    )

    emitted = []

    page.artwork_directory_saved.connect(
        emitted.append
    )

    page.save_runtime_settings()

    assert (
        page.save_status.text()
        == "Settings saved"
    )

    assert emitted == [
        str(artwork)
    ]
