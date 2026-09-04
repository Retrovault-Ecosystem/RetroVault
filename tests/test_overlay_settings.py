import json

import yaml
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
)

from config import (
    ConfigLoader,
    ConfigWriter,
)
from ui.pages.settings_page import (
    SettingsPage,
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

    retroarch = tmp_path / "retroarch"
    retroarch.write_text(
        (
            "#!/bin/sh\n"
            "echo 'RetroArch libretro test'\n"
        ),
        encoding="utf-8",
    )
    retroarch.chmod(0o755)

    cores = tmp_path / "cores"
    cores.mkdir()
    (
        cores / "test_libretro.so"
    ).write_bytes(b"core")

    library = tmp_path / "roms"
    library.mkdir()

    artwork = tmp_path / "artwork"
    artwork.mkdir()

    overlays = tmp_path / "overlays"
    overlays.mkdir()

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    defaults = tmp_path / "defaults.yaml"
    runtime = tmp_path / "runtime.json"

    defaults.write_text(
        yaml.safe_dump(
            {
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
                            "name": "Test",
                            "enabled": True,
                            "type": "local",
                            "path": str(
                                library
                            ),
                        },
                    ],
                },
                "paths": {
                    "artwork": {
                        "directory": str(
                            artwork
                        ),
                    },
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

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )

    page = SettingsPage(
        config_loader=loader,
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    return page, runtime, overlays


def test_overlay_directory_is_editable(
    tmp_path,
):
    page, _runtime, overlays = (
        make_page(tmp_path)
    )

    assert (
        page.overlay_directory_edit.text()
        == str(overlays)
    )
    assert (
        page.overlay_directory_status.text()
        == page.STATUS_READY_TEXT
    )


def test_editing_does_not_persist(
    tmp_path,
):
    page, runtime, _overlays = (
        make_page(tmp_path)
    )

    selected = tmp_path / "selected"
    selected.mkdir()

    page.overlay_directory_edit.setText(
        str(selected)
    )

    assert not runtime.exists()


def test_browse_does_not_persist(
    tmp_path,
    monkeypatch,
):
    page, runtime, _overlays = (
        make_page(tmp_path)
    )

    selected = tmp_path / "selected"
    selected.mkdir()

    monkeypatch.setattr(
        QFileDialog,
        "getExistingDirectory",
        lambda *args, **kwargs: str(
            selected
        ),
    )

    page._browse_overlay_directory()

    assert (
        page.overlay_directory_edit.text()
        == str(selected)
    )
    assert not runtime.exists()


def test_save_persists_overlay_directory(
    tmp_path,
):
    page, runtime, _overlays = (
        make_page(tmp_path)
    )

    selected = tmp_path / "selected"
    selected.mkdir()

    emitted = []

    page.overlay_directory_saved.connect(
        emitted.append
    )

    page.overlay_directory_edit.setText(
        str(selected)
    )

    page.save_runtime_settings()

    data = json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    )

    assert (
        data["paths"]["overlays"][
            "directory"
        ]
        == str(selected)
    )
    assert emitted == [str(selected)]
    assert page.save_status.text() == (
        "Settings saved"
    )


def test_invalid_overlay_directory_blocks_save(
    tmp_path,
):
    page, runtime, _overlays = (
        make_page(tmp_path)
    )

    page.overlay_directory_edit.setText(
        str(
            tmp_path / "missing"
        )
    )

    page.save_runtime_settings()

    assert not runtime.exists()
    assert page.save_status.text() == (
        "Overlay path is not a readable directory"
    )


def test_restore_defaults_restores_overlay_path(
    tmp_path,
):
    page, _runtime, overlays = (
        make_page(tmp_path)
    )

    selected = tmp_path / "selected"
    selected.mkdir()

    page.overlay_directory_edit.setText(
        str(selected)
    )

    page.restore_default_paths()

    assert (
        page.overlay_directory_edit.text()
        == str(overlays)
    )


def test_save_preserves_unrelated_override(
    tmp_path,
):
    page, runtime, overlays = (
        make_page(tmp_path)
    )

    runtime.write_text(
        json.dumps(
            {
                "custom": {
                    "preserve": True,
                },
            }
        ),
        encoding="utf-8",
    )

    page.save_runtime_settings()

    data = json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    )

    assert data["custom"] == {
        "preserve": True,
    }
    assert (
        data["paths"]["overlays"][
            "directory"
        ]
        == str(overlays)
    )
