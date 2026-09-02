from dataclasses import dataclass

from services.library.scanner import (
    RomScanner,
)


@dataclass(frozen=True)
class FakePlatform:
    id: str
    name: str


@dataclass
class Source:
    path: str
    name: str = "Test Library"
    enabled: bool = True


class FakeResolver:

    def __init__(
        self,
        platforms=None,
    ):
        self.platforms = (
            platforms
            if platforms is not None
            else {}
        )

    def platform_for_extension(
        self,
        extension,
    ):
        key = (
            str(extension)
            .casefold()
            .lstrip(".")
        )

        return self.platforms.get(
            key
        )


def write_rom(
    root,
    name,
):
    path = root / name

    path.write_bytes(
        b"test"
    )

    return path


def test_unique_rvdb_resolution_enriches_game(
    tmp_path,
):
    write_rom(
        tmp_path,
        "Mario.nes",
    )

    resolver = FakeResolver(
        {
            "nes": FakePlatform(
                id=(
                    "platform.nintendo.nes"
                ),
                name=(
                    "Nintendo Entertainment System"
                ),
            ),
        }
    )

    scanner = RomScanner(
        rvdb_resolver=resolver
    )

    games = scanner.scan(
        Source(
            path=str(tmp_path)
        )
    )

    assert len(games) == 1

    game = games[0]

    assert game.platform == (
        "Nintendo Entertainment System"
    )

    assert game.rvdb_platform_id == (
        "platform.nintendo.nes"
    )


def test_rvdb_canonical_name_drives_existing_core_mapping(
    tmp_path,
):
    write_rom(
        tmp_path,
        "Mario.nes",
    )

    resolver = FakeResolver(
        {
            "nes": FakePlatform(
                id=(
                    "platform.nintendo.nes"
                ),
                name=(
                    "Nintendo Entertainment System"
                ),
            ),
        }
    )

    scanner = RomScanner(
        rvdb_resolver=resolver
    )

    game = scanner.scan(
        Source(
            path=str(tmp_path)
        )
    )[0]

    assert game.core == (
        scanner.core_mapper.get_core(
            "Nintendo Entertainment System"
        )
    )


def test_unresolved_rvdb_extension_preserves_legacy_platform(
    tmp_path,
):
    write_rom(
        tmp_path,
        "SuperMetroid.sfc",
    )

    scanner = RomScanner(
        rvdb_resolver=FakeResolver()
    )

    game = scanner.scan(
        Source(
            path=str(tmp_path)
        )
    )[0]

    assert game.platform == (
        "Super Nintendo"
    )

    assert game.rvdb_platform_id == ""


def test_ambiguous_rvdb_result_preserves_legacy_platform(
    tmp_path,
):
    write_rom(
        tmp_path,
        "Disc.iso",
    )

    scanner = RomScanner(
        rvdb_resolver=FakeResolver()
    )

    game = scanner.scan(
        Source(
            path=str(tmp_path)
        )
    )[0]

    assert game.platform == "Unknown"

    assert game.rvdb_platform_id == ""


def test_missing_rvdb_bundle_falls_back_cleanly(
    tmp_path,
    monkeypatch,
):
    write_rom(
        tmp_path,
        "Sonic.md",
    )

    monkeypatch.chdir(
        tmp_path
    )

    scanner = RomScanner()

    assert scanner.rvdb_resolver is None

    game = scanner.scan(
        Source(
            path=str(tmp_path)
        )
    )[0]

    assert game.platform == (
        "Sega Genesis"
    )

    assert game.rvdb_platform_id == ""


def test_real_rvdb_enriches_nes(
    tmp_path,
):
    write_rom(
        tmp_path,
        "Zelda.nes",
    )

    scanner = RomScanner()

    game = scanner.scan(
        Source(
            path=str(tmp_path)
        )
    )[0]

    assert game.platform == (
        "Nintendo Entertainment System"
    )

    assert game.rvdb_platform_id == (
        "platform.nintendo.nes"
    )


def test_real_rvdb_enriches_nintendo_64(
    tmp_path,
):
    write_rom(
        tmp_path,
        "Mario64.z64",
    )

    scanner = RomScanner()

    game = scanner.scan(
        Source(
            path=str(tmp_path)
        )
    )[0]

    assert game.platform == (
        "Nintendo 64"
    )

    assert game.rvdb_platform_id == (
        "platform.nintendo.n64"
    )


def test_real_rvdb_ambiguous_iso_preserves_unknown(
    tmp_path,
):
    write_rom(
        tmp_path,
        "Disc.iso",
    )

    scanner = RomScanner()

    game = scanner.scan(
        Source(
            path=str(tmp_path)
        )
    )[0]

    assert game.platform == "Unknown"

    assert game.rvdb_platform_id == ""


def test_real_rvdb_unresolved_sfc_preserves_super_nintendo(
    tmp_path,
):
    write_rom(
        tmp_path,
        "SuperMetroid.sfc",
    )

    scanner = RomScanner()

    game = scanner.scan(
        Source(
            path=str(tmp_path)
        )
    )[0]

    assert game.platform == (
        "Super Nintendo"
    )

    assert game.rvdb_platform_id == ""
