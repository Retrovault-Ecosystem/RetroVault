from pathlib import Path

from services.library.scanner import RomScanner
from services.library.source_manager import LibrarySource


class ArchiveAwareResolver:
    class Platform:
        def __init__(self, name, platform_id):
            self.name = name
            self.id = platform_id

    def platform_for_extension(self, extension):
        extension = (
            str(extension)
            .strip()
            .casefold()
            .lstrip(".")
        )

        if extension == "nes":
            return self.Platform(
                "Nintendo Entertainment System",
                "platform.nintendo.nes",
            )

        if extension in {"sfc", "smc"}:
            return self.Platform(
                "Super Nintendo",
                "platform.nintendo.snes",
            )

        return None

    def game_for_name(self, name, platform_id):
        return None


def _source(path):
    return LibrarySource(
        id="test",
        name="Test",
        enabled=True,
        type="local",
        path=str(path),
    )


def test_7z_nes_archive_is_classified_as_nes(
    tmp_path,
):
    import subprocess

    source_dir = tmp_path / "src"
    source_dir.mkdir()

    rom = source_dir / "Example (U) [!].nes"
    rom.write_bytes(b"NES")

    archive = tmp_path / "Example.7z"

    subprocess.run(
        [
            "7z",
            "a",
            "-y",
            str(archive),
            rom.name,
        ],
        cwd=source_dir,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    scanner = RomScanner(
        rvdb_resolver=ArchiveAwareResolver()
    )

    games = scanner.scan(
        _source(tmp_path)
    )

    archive_games = [
        game
        for game in games
        if game.rom.endswith(".7z")
    ]

    assert len(archive_games) == 1

    game = archive_games[0]

    assert (
        game.platform
        == "Nintendo Entertainment System"
    )

    assert (
        game.rvdb_platform_id
        == "platform.nintendo.nes"
    )

    assert game.core == "fceumm_libretro.so"


def test_7z_snes_archive_is_classified_as_snes(
    tmp_path,
):
    import subprocess

    source_dir = tmp_path / "src"
    source_dir.mkdir()

    rom = source_dir / "Example (U) [!].sfc"
    rom.write_bytes(b"SNES")

    archive = tmp_path / "Example.7z"

    subprocess.run(
        [
            "7z",
            "a",
            "-y",
            str(archive),
            rom.name,
        ],
        cwd=source_dir,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    scanner = RomScanner(
        rvdb_resolver=ArchiveAwareResolver()
    )

    games = scanner.scan(
        _source(tmp_path)
    )

    archive_games = [
        game
        for game in games
        if game.rom.endswith(".7z")
    ]

    assert len(archive_games) == 1

    game = archive_games[0]

    assert game.platform == "Super Nintendo"
    assert (
        game.rvdb_platform_id
        == "platform.nintendo.snes"
    )

    assert game.core == "snes9x_libretro.so"
