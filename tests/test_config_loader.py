import json
from pathlib import Path

import pytest
import yaml

from config.loader import ConfigLoader


DEFAULTS = {
    "retroarch": {
        "executable": "/usr/bin/retroarch",
        "cores": {
            "directory": "/opt/retropie/libretrocores",
        },
    },
    "library": {
        "sources": [
            {
                "id": "dev",
                "name": "Development Library",
                "enabled": True,
                "type": "local",
                "path": "/home/example/roms",
            },
        ],
    },
    "paths": {
        "overlays": {
            "directory": "~/.config/retroarch/overlays",
        },
        "shaders": {
            "directory": "~/.config/retroarch/shaders",
        },
    },
}


def _write_defaults(
    tmp_path: Path,
) -> Path:
    path = (
        tmp_path
        / "defaults.yaml"
    )

    path.write_text(
        yaml.safe_dump(
            DEFAULTS,
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    return path


def test_load_returns_defaults_when_runtime_override_missing(
    tmp_path,
):
    defaults = _write_defaults(
        tmp_path
    )

    runtime = (
        tmp_path
        / "missing-runtime.json"
    )

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )

    assert loader.load() == DEFAULTS


def test_runtime_override_deep_merges_nested_mapping(
    tmp_path,
):
    defaults = _write_defaults(
        tmp_path
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
                        "directory": "/custom/cores",
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

    config = loader.load()

    assert (
        config[
            "retroarch"
        ][
            "executable"
        ]
        == "/usr/bin/retroarch"
    )

    assert (
        config[
            "retroarch"
        ][
            "cores"
        ][
            "directory"
        ]
        == "/custom/cores"
    )

    assert (
        config[
            "paths"
        ]
        == DEFAULTS[
            "paths"
        ]
    )


def test_runtime_override_replaces_list_value(
    tmp_path,
):
    defaults = _write_defaults(
        tmp_path
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    replacement_sources = [
        {
            "id": "user",
            "name": "User Library",
            "enabled": True,
            "type": "local",
            "path": "/games/roms",
        },
    ]

    runtime.write_text(
        json.dumps(
            {
                "library": {
                    "sources": replacement_sources,
                },
            }
        ),
        encoding="utf-8",
    )

    config = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    ).load()

    assert (
        config[
            "library"
        ][
            "sources"
        ]
        == replacement_sources
    )


def test_runtime_override_can_add_new_mapping_key(
    tmp_path,
):
    defaults = _write_defaults(
        tmp_path
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    runtime.write_text(
        json.dumps(
            {
                "retroarch": {
                    "config_file": "/custom/retroarch.cfg",
                },
            }
        ),
        encoding="utf-8",
    )

    config = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    ).load()

    assert (
        config[
            "retroarch"
        ][
            "config_file"
        ]
        == "/custom/retroarch.cfg"
    )


def test_empty_runtime_mapping_preserves_defaults(
    tmp_path,
):
    defaults = _write_defaults(
        tmp_path
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    runtime.write_text(
        "{}",
        encoding="utf-8",
    )

    config = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    ).load()

    assert config == DEFAULTS


def test_invalid_runtime_json_raises_clear_error(
    tmp_path,
):
    defaults = _write_defaults(
        tmp_path
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    runtime.write_text(
        "{ invalid json",
        encoding="utf-8",
    )

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )

    with pytest.raises(
        ValueError,
        match="Invalid RetroVault runtime configuration",
    ):
        loader.load()


def test_runtime_root_must_be_mapping(
    tmp_path,
):
    defaults = _write_defaults(
        tmp_path
    )

    runtime = (
        tmp_path
        / "runtime.json"
    )

    runtime.write_text(
        '["not", "a", "mapping"]',
        encoding="utf-8",
    )

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )

    with pytest.raises(
        ValueError,
        match="must contain a JSON object",
    ):
        loader.load()
