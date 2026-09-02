import json
from pathlib import Path

import yaml
from PyQt6.QtWidgets import (
    QApplication,
)

from config.loader import ConfigLoader
from ui.pages.settings_page import (
    SettingsPage,
)


_QT_APP = None


def _app():
    global _QT_APP

    app = QApplication.instance()

    if app is None:
        app = QApplication([])

    _QT_APP = app

    return app


def _write_defaults(
    tmp_path: Path,
    *,
    retroarch: Path,
    cores: Path,
    library: Path,
    overlays: Path,
    shaders: Path,
) -> Path:
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
        page.retroarch_value.text()
        == str(retroarch)
    )

    assert (
        page.core_directory_value.text()
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
        == "Ready"
    )

    assert (
        page.core_directory_status.text()
        == "Ready"
    )

    assert (
        page.library_sources_status.text()
        == "Ready"
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
        == "Missing"
    )

    assert (
        page.core_directory_status.text()
        == "Missing"
    )

    assert (
        page.library_sources_status.text()
        == "Missing"
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
