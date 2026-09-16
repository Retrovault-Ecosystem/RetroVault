import subprocess
from pathlib import Path

import pytest

from services.retroarch.archive_runtime import ArchiveRuntime


def _make_7z(
    tmp_path,
    name,
    members,
):
    source = (
        tmp_path
        / "source"
    )
    source.mkdir()

    for relative, content in members:
        path = source / relative
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_bytes(content)

    archive = (
        tmp_path
        / name
    )

    subprocess.run(
        [
            "7z",
            "a",
            "-y",
            str(archive),
            ".",
        ],
        cwd=source,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    return archive


def test_non_archive_is_unchanged(
    tmp_path,
):
    rom = (
        tmp_path
        / "game.nes"
    )
    rom.write_bytes(
        b"NES"
    )

    runtime = ArchiveRuntime(
        cache_root=(
            tmp_path
            / "cache"
        )
    )

    assert runtime.resolve(
        rom
    ) == str(
        rom.resolve()
    )


def test_7z_single_rom_extracts(
    tmp_path,
):
    archive = _make_7z(
        tmp_path,
        "Duck Tales 2.7z",
        [
            (
                "Duck Tales 2.nes",
                b"NES-ROM",
            ),
        ],
    )

    runtime = ArchiveRuntime(
        cache_root=(
            tmp_path
            / "cache"
        )
    )

    resolved = Path(
        runtime.resolve(
            archive
        )
    )

    assert resolved.is_file()
    assert resolved.suffix == ".nes"
    assert resolved.read_bytes() == b"NES-ROM"


def test_nested_7z_rom_extracts(
    tmp_path,
):
    archive = _make_7z(
        tmp_path,
        "Nested Game.7z",
        [
            (
                "folder/Nested Game.sfc",
                b"SNES-ROM",
            ),
        ],
    )

    runtime = ArchiveRuntime(
        cache_root=(
            tmp_path
            / "cache"
        )
    )

    resolved = Path(
        runtime.resolve(
            archive
        )
    )

    assert resolved.is_file()
    assert resolved.name == "Nested Game.sfc"


def test_unsupported_files_are_ignored(
    tmp_path,
):
    archive = _make_7z(
        tmp_path,
        "Game.7z",
        [
            (
                "README.txt",
                b"README",
            ),
            (
                "Game.nes",
                b"NES-ROM",
            ),
        ],
    )

    runtime = ArchiveRuntime(
        cache_root=(
            tmp_path
            / "cache"
        )
    )

    resolved = Path(
        runtime.resolve(
            archive
        )
    )

    assert resolved.name == "Game.nes"


def test_archive_without_rom_is_rejected(
    tmp_path,
):
    archive = _make_7z(
        tmp_path,
        "No ROM.7z",
        [
            (
                "README.txt",
                b"README",
            ),
        ],
    )

    runtime = ArchiveRuntime(
        cache_root=(
            tmp_path
            / "cache"
        )
    )

    with pytest.raises(
        ValueError,
        match="no supported ROM",
    ):
        runtime.resolve(
            archive
        )


def test_multi_rom_archive_is_deterministic(
    tmp_path,
):
    archive = _make_7z(
        tmp_path,
        "Collection.7z",
        [
            (
                "Game B.nes",
                b"B",
            ),
            (
                "Game A.nes",
                b"A",
            ),
        ],
    )

    runtime = ArchiveRuntime(
        cache_root=(
            tmp_path
            / "cache"
        )
    )

    resolved = Path(
        runtime.resolve(
            archive
        )
    )

    assert resolved.name == "Game A.nes"
    assert resolved.read_bytes() == b"A"


def test_goodset_verified_dump_is_preferred(
    tmp_path,
):
    archive = _make_7z(
        tmp_path,
        "GoodSet Game.7z",
        [
            (
                "GoodSet Game (U) [b1].nes",
                b"BAD",
            ),
            (
                "GoodSet Game (U) [!].nes",
                b"GOOD",
            ),
            (
                "GoodSet Game (J).nes",
                b"JAPAN",
            ),
        ],
    )

    runtime = ArchiveRuntime(
        cache_root=(
            tmp_path
            / "cache"
        )
    )

    resolved = Path(
        runtime.resolve(
            archive
        )
    )

    assert (
        resolved.name
        == "GoodSet Game (U) [!].nes"
    )
    assert resolved.read_bytes() == b"GOOD"


def test_goodset_bad_dump_is_deprioritized(
    tmp_path,
):
    archive = _make_7z(
        tmp_path,
        "Ranked Game.7z",
        [
            (
                "Ranked Game (U) [b1].nes",
                b"BAD",
            ),
            (
                "Ranked Game (U).nes",
                b"NORMAL",
            ),
        ],
    )

    runtime = ArchiveRuntime(
        cache_root=(
            tmp_path
            / "cache"
        )
    )

    resolved = Path(
        runtime.resolve(
            archive
        )
    )

    assert (
        resolved.name
        == "Ranked Game (U).nes"
    )
    assert resolved.read_bytes() == b"NORMAL"


def test_matching_archive_stem_wins_multi_rom(
    tmp_path,
):
    archive = _make_7z(
        tmp_path,
        "Mortal Kombat 3.7z",
        [
            (
                "Mortal Kombat 3.nes",
                b"PRIMARY",
            ),
            (
                "Mortal Kombat 3 (Alt).nes",
                b"ALT",
            ),
        ],
    )

    runtime = ArchiveRuntime(
        cache_root=(
            tmp_path
            / "cache"
        )
    )

    resolved = Path(
        runtime.resolve(
            archive
        )
    )

    assert (
        resolved.name
        == "Mortal Kombat 3.nes"
    )

    assert (
        resolved.read_bytes()
        == b"PRIMARY"
    )


def test_extraction_is_cached(
    tmp_path,
):
    archive = _make_7z(
        tmp_path,
        "Cached Game.7z",
        [
            (
                "Cached Game.nes",
                b"CACHED",
            ),
        ],
    )

    runtime = ArchiveRuntime(
        cache_root=(
            tmp_path
            / "cache"
        )
    )

    first = runtime.resolve(
        archive
    )

    second = runtime.resolve(
        archive
    )

    assert first == second
