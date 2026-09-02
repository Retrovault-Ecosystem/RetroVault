import json
from pathlib import Path

from config.writer import ConfigWriter


def test_writer_creates_runtime_file_atomically(
    tmp_path,
):
    runtime = (
        tmp_path
        / "retrovault"
        / "runtime.json"
    )

    writer = ConfigWriter(
        runtime_file=runtime
    )

    writer.write(
        {
            "retroarch": {
                "executable": "/custom/retroarch",
            },
        }
    )

    assert runtime.is_file()

    data = json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    )

    assert data == {
        "retroarch": {
            "executable": "/custom/retroarch",
        },
    }

    assert not (
        runtime.parent
        / "runtime.json.tmp"
    ).exists()


def test_writer_preserves_existing_unrelated_keys(
    tmp_path,
):
    runtime = (
        tmp_path
        / "runtime.json"
    )

    runtime.write_text(
        json.dumps(
            {
                "paths": {
                    "overlays": {
                        "directory": "/old/overlays",
                    },
                },
                "library": {
                    "sources": [
                        {
                            "id": "existing",
                            "name": "Existing",
                            "enabled": True,
                            "type": "local",
                            "path": "/roms",
                        },
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    writer = ConfigWriter(
        runtime_file=runtime
    )

    writer.update(
        {
            "retroarch": {
                "cores": {
                    "directory": "/new/cores",
                },
            },
        }
    )

    data = json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    )

    assert data[
        "retroarch"
    ][
        "cores"
    ][
        "directory"
    ] == "/new/cores"

    assert data[
        "paths"
    ][
        "overlays"
    ][
        "directory"
    ] == "/old/overlays"

    assert data[
        "library"
    ][
        "sources"
    ][0][
        "id"
    ] == "existing"


def test_writer_deep_merges_nested_mappings(
    tmp_path,
):
    runtime = (
        tmp_path
        / "runtime.json"
    )

    runtime.write_text(
        json.dumps(
            {
                "retroarch": {
                    "executable": "/usr/bin/retroarch",
                    "cores": {
                        "directory": "/old/cores",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    writer = ConfigWriter(
        runtime_file=runtime
    )

    writer.update(
        {
            "retroarch": {
                "cores": {
                    "directory": "/new/cores",
                },
            },
        }
    )

    data = json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    )

    assert (
        data[
            "retroarch"
        ][
            "executable"
        ]
        == "/usr/bin/retroarch"
    )

    assert (
        data[
            "retroarch"
        ][
            "cores"
        ][
            "directory"
        ]
        == "/new/cores"
    )


def test_writer_replaces_lists_atomically(
    tmp_path,
):
    runtime = (
        tmp_path
        / "runtime.json"
    )

    writer = ConfigWriter(
        runtime_file=runtime
    )

    writer.write(
        {
            "library": {
                "sources": [
                    {
                        "id": "old",
                    },
                ],
            },
        }
    )

    writer.update(
        {
            "library": {
                "sources": [
                    {
                        "id": "new",
                    },
                ],
            },
        }
    )

    data = json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    )

    assert data[
        "library"
    ][
        "sources"
    ] == [
        {
            "id": "new",
        },
    ]


def test_writer_rejects_non_mapping_root(
    tmp_path,
):
    runtime = (
        tmp_path
        / "runtime.json"
    )

    writer = ConfigWriter(
        runtime_file=runtime
    )

    try:
        writer.write(
            [
                "invalid",
            ]
        )
    except ValueError as exc:
        assert (
            "must be a mapping"
            in str(exc)
        )
    else:
        raise AssertionError(
            "expected ValueError"
        )

    assert not runtime.exists()


def test_writer_rejects_invalid_existing_runtime(
    tmp_path,
):
    runtime = (
        tmp_path
        / "runtime.json"
    )

    runtime.write_text(
        "{ invalid json",
        encoding="utf-8",
    )

    writer = ConfigWriter(
        runtime_file=runtime
    )

    try:
        writer.update(
            {
                "retroarch": {
                    "executable": "/custom",
                },
            }
        )
    except ValueError as exc:
        assert (
            "Invalid RetroVault runtime configuration"
            in str(exc)
        )
    else:
        raise AssertionError(
            "expected ValueError"
        )


def test_writer_creates_parent_directory(
    tmp_path,
):
    runtime = (
        tmp_path
        / "nested"
        / "retrovault"
        / "runtime.json"
    )

    writer = ConfigWriter(
        runtime_file=runtime
    )

    writer.write(
        {}
    )

    assert runtime.is_file()


def test_writer_formats_json_stably(
    tmp_path,
):
    runtime = (
        tmp_path
        / "runtime.json"
    )

    writer = ConfigWriter(
        runtime_file=runtime
    )

    writer.write(
        {
            "retroarch": {
                "executable": "/usr/bin/retroarch",
            },
        }
    )

    text = runtime.read_text(
        encoding="utf-8"
    )

    assert text.endswith("\n")

    assert (
        '"retroarch": {'
        in text
    )
