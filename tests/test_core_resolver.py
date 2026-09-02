from pathlib import Path

import pytest

from services.retroarch.core_resolver import (
    CoreResolver,
)


def _config(
    core_directory: Path,
) -> dict:
    return {
        "retroarch": {
            "cores": {
                "directory": str(
                    core_directory
                ),
            },
        },
    }


@pytest.mark.parametrize(
    "name",
    [
        None,
        "",
        " ",
        "   ",
        "\t",
        "\n",
    ],
)
def test_find_rejects_missing_or_blank_core_name(
    tmp_path,
    name,
):
    core_directory = (
        tmp_path
        / "cores"
    )

    core_directory.mkdir()

    arbitrary_core = (
        core_directory
        / "arbitrary_libretro.so"
    )

    arbitrary_core.write_text(
        "",
        encoding="utf-8",
    )

    resolver = CoreResolver(
        _config(
            core_directory
        )
    )

    assert resolver.find(name) is None


def test_find_returns_matching_core(
    tmp_path,
):
    core_directory = (
        tmp_path
        / "cores"
    )

    nested = (
        core_directory
        / "lr-snes9x"
    )

    nested.mkdir(
        parents=True
    )

    expected = (
        nested
        / "snes9x_libretro.so"
    )

    expected.write_text(
        "",
        encoding="utf-8",
    )

    resolver = CoreResolver(
        _config(
            core_directory
        )
    )

    assert (
        resolver.find(
            "snes9x_libretro.so"
        )
        == str(expected)
    )


def test_find_returns_none_for_missing_named_core(
    tmp_path,
):
    core_directory = (
        tmp_path
        / "cores"
    )

    core_directory.mkdir()

    installed = (
        core_directory
        / "fceumm_libretro.so"
    )

    installed.write_text(
        "",
        encoding="utf-8",
    )

    resolver = CoreResolver(
        _config(
            core_directory
        )
    )

    assert (
        resolver.find(
            "missing_libretro.so"
        )
        is None
    )
