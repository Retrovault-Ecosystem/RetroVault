import subprocess
from pathlib import Path

import pytest

from unittest.mock import patch
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


def test_playable_members_exposes_archive_variants(
    tmp_path,
):
    archive = _make_7z(
        tmp_path,
        "Variant Game.7z",
        [
            (
                "Variant Game (U) [!].nes",
                b"GOOD",
            ),
            (
                "Variant Game (J).nes",
                b"JAPAN",
            ),
            (
                "Variant Game (U) [h1].nes",
                b"HACK",
            ),
        ],
    )

    runtime = ArchiveRuntime(
        cache_root=(
            tmp_path
            / "cache"
        )
    )

    members = runtime.playable_members(
        archive
    )

    assert members == [
        "Variant Game (J).nes",
        "Variant Game (U) [!].nes",
        "Variant Game (U) [h1].nes",
    ] or sorted(members) == sorted(
        [
            "Variant Game (J).nes",
            "Variant Game (U) [!].nes",
            "Variant Game (U) [h1].nes",
        ]
    )


def test_preferred_member_exposes_default_variant(
    tmp_path,
):
    archive = _make_7z(
        tmp_path,
        "Variant Game.7z",
        [
            (
                "Variant Game (J).nes",
                b"JAPAN",
            ),
            (
                "Variant Game (U) [!].nes",
                b"GOOD",
            ),
            (
                "Variant Game (U) [h1].nes",
                b"HACK",
            ),
        ],
    )

    runtime = ArchiveRuntime(
        cache_root=(
            tmp_path
            / "cache"
        )
    )

    assert (
        runtime.preferred_member(
            archive
        )
        == "Variant Game (U) [!].nes"
    )


def test_playable_members_rejects_unsafe_archive_paths(
    tmp_path,
):
    archive = tmp_path / "Unsafe Members.7z"
    archive.write_bytes(b"archive")

    runtime = ArchiveRuntime(
        cache_root=tmp_path / "cache",
        executable="7z",
    )

    members = [
        "Safe Game (U) [!].nes",
        "nested/Safe Game (J).nes",
        "../escape.nes",
        "nested/../../escape.nes",
        "/tmp/absolute.nes",
        r"C:\temp\drive.nes",
        r"\\server\share\unc.nes",
        r"..\backslash-escape.nes",
    ]

    with patch.object(
        runtime,
        "_list_members",
        return_value=members,
    ):
        assert runtime.playable_members(
            archive
        ) == [
            "Safe Game (U) [!].nes",
            "nested/Safe Game (J).nes",
        ]


def test_preferred_member_cannot_select_unsafe_variant(
    tmp_path,
):
    archive = tmp_path / "Ranked Game.7z"
    archive.write_bytes(b"archive")

    runtime = ArchiveRuntime(
        cache_root=tmp_path / "cache",
        executable="7z",
    )

    members = [
        "../Ranked Game (U) [!].nes",
        "Ranked Game (U) [b1].nes",
    ]

    with patch.object(
        runtime,
        "_list_members",
        return_value=members,
    ):
        assert runtime.preferred_member(
            archive
        ) == "Ranked Game (U) [b1].nes"


def test_resolve_refuses_archive_with_only_unsafe_rom_members(
    tmp_path,
):
    archive = tmp_path / "Unsafe Only.7z"
    archive.write_bytes(b"archive")

    runtime = ArchiveRuntime(
        cache_root=tmp_path / "cache",
        executable="7z",
    )

    members = [
        "../escape.nes",
        r"..\escape-too.nes",
        "/tmp/absolute.nes",
        r"C:\temp\drive.nes",
        r"\\server\share\unc.nes",
    ]

    with patch.object(
        runtime,
        "_list_members",
        return_value=members,
    ):
        with pytest.raises(
            ValueError,
            match="contains no supported ROM content",
        ):
            runtime.resolve(archive)


@pytest.mark.parametrize(
    "member",
    [
        "../escape.nes",
        "nested/../../escape.nes",
        "/tmp/absolute.nes",
        r"C:\temp\drive.nes",
        r"\\server\share\unc.nes",
        r"..\backslash-escape.nes",
    ],
)
def test_archive_member_path_safety_rejects_escape_forms(
    member,
):
    assert (
        ArchiveRuntime._member_is_safe(member)
        is False
    )


@pytest.mark.parametrize(
    "member",
    [
        "Game.nes",
        "nested/Game.nes",
        "nested/deeper/Game.sfc",
    ],
)
def test_archive_member_path_safety_accepts_relative_members(
    member,
):
    assert (
        ArchiveRuntime._member_is_safe(member)
        is True
    )


def test_resolve_can_extract_explicit_archive_member(
    tmp_path,
):
    archive = tmp_path / "Variant Game.7z"
    archive.write_bytes(b"archive")

    executable = tmp_path / "fake-7z"
    executable.write_text("", encoding="utf-8")

    runtime = ArchiveRuntime(
        cache_root=tmp_path / "cache",
        executable=str(executable),
    )

    members = [
        "Variant Game (U) [!].nes",
        "Variant Game (J).nes",
    ]

    selected = "Variant Game (J).nes"

    def fake_run(command, **_kwargs):
        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        if "x" in command:
            output = next(
                item[2:]
                for item in command
                if item.startswith("-o")
            )
            destination = Path(output)
            extracted = destination / selected
            extracted.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            extracted.write_bytes(b"rom")

        return Result()

    with patch.object(
        runtime,
        "_list_members",
        return_value=members,
    ), patch(
        "services.retroarch.archive_runtime.subprocess.run",
        side_effect=fake_run,
    ):
        resolved = runtime.resolve(
            archive,
            member=selected,
        )

    assert Path(resolved).name == selected
    assert Path(resolved).read_bytes() == b"rom"


def test_resolve_rejects_unknown_explicit_archive_member(
    tmp_path,
):
    archive = tmp_path / "Variant Game.7z"
    archive.write_bytes(b"archive")

    runtime = ArchiveRuntime(
        cache_root=tmp_path / "cache",
        executable="7z",
    )

    with patch.object(
        runtime,
        "_list_members",
        return_value=[
            "Variant Game (U) [!].nes",
            "Variant Game (J).nes",
        ],
    ):
        with pytest.raises(
            ValueError,
            match="not playable or is not present",
        ):
            runtime.resolve(
                archive,
                member="Variant Game (E).nes",
            )


def test_resolve_rejects_unsafe_explicit_archive_member(
    tmp_path,
):
    archive = tmp_path / "Variant Game.7z"
    archive.write_bytes(b"archive")

    runtime = ArchiveRuntime(
        cache_root=tmp_path / "cache",
        executable="7z",
    )

    with patch.object(
        runtime,
        "_list_members",
        return_value=[
            "Variant Game (U) [!].nes",
        ],
    ):
        with pytest.raises(
            ValueError,
            match="unsafe path",
        ):
            runtime.resolve(
                archive,
                member="../Variant Game (U) [!].nes",
            )
