from dataclasses import dataclass

from services.library.scanner import (
    RomScanner,
)

from services.library.rvdb_resolver import (
    RVDBLibraryResolver,
)
from services.rvdb import (
    RVDBService,
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


    def game_for_name(
        self,
        name,
        platform_id,
    ):
        # Existing scanner tests exercise only platform
        # enrichment. No canonical game fixture is supplied,
        # so the expanded resolver contract reports no match.
        return None


def write_rom(
    root,
    name,
):
    path = root / name

    path.write_bytes(
        b"test"
    )

    return path


def real_rvdb_resolver():
    return RVDBLibraryResolver(
        RVDBService.from_bundle(
            "data/rvdb/rvdb.bundle.json"
        )
    )


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


def test_missing_rvdb_dependency_falls_back_cleanly(
    tmp_path,
):
    write_rom(
        tmp_path,
        "Sonic.md",
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

    scanner = RomScanner(
        rvdb_resolver=real_rvdb_resolver()
    )

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

    scanner = RomScanner(
        rvdb_resolver=real_rvdb_resolver()
    )

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

    scanner = RomScanner(
        rvdb_resolver=real_rvdb_resolver()
    )

    game = scanner.scan(
        Source(
            path=str(tmp_path)
        )
    )[0]

    assert game.platform == "Unknown"

    assert game.rvdb_platform_id == ""


def test_real_rvdb_sfc_resolves_platform_but_not_unmatched_game(
    tmp_path,
):
    write_rom(
        tmp_path,
        "SuperMetroid.sfc",
    )

    scanner = RomScanner(
        rvdb_resolver=real_rvdb_resolver()
    )

    game = scanner.scan(
        Source(
            path=str(tmp_path)
        )
    )[0]

    assert game.platform == (
        "Super Nintendo"
    )

    assert game.rvdb_platform_id == (
        "platform.nintendo.snes"
    )

    assert game.rvdb_game_id == ""


def test_genesis_scan_selects_production_bezel_from_real_bundle(tmp_path):
    from pathlib import Path
    from services.presentation.launch_resolver import LaunchPresentationResolver
    from services.presentation.models import PresentationProfile

    # Exercise the same metadata boundary as the Library. Supplying a platform
    # ID directly to the launcher previously hid the missing Genesis metadata.
    for extension in ('md', 'gen', 'MD'):
        write_rom(tmp_path, f'Sonic fixture.{extension}')
    games = RomScanner(rvdb_resolver=real_rvdb_resolver()).scan(Source(str(tmp_path)))
    assert len(games) == 3
    root = Path(__file__).resolve().parents[1]
    resolver = LaunchPresentationResolver(config={'paths': {
        kind: {'directory': str(root)} for kind in ('overlays', 'shaders')}})
    for game in games:
        assert game.rvdb_platform_id == 'platform.sega.genesis'
        assert game.core == 'genesis_plus_gx_libretro.so'
        decision = resolver.select(platform_id=game.rvdb_platform_id,
                                   core_identity='genesis_plus_gx',
                                   requested=PresentationProfile())
        assert decision.authority == 'production package'
        assert decision.selected.overlay.endswith('genesis/classic/RetroVault_Genesis_Classic.cfg')
        assert decision.package.fixed_glass().width == 1296


def test_expansion_formats_use_unique_rvdb_platform_and_leave_bin_ambiguous(tmp_path):
    import json
    from services.library.archive_scan_cache import ArchiveScanCache
    formats = {
        'platform.nintendo.nes': ['nes'],
        'platform.nintendo.snes': ['sfc', 'smc', 'bin'],
        'platform.sega.genesis': ['md', 'gen', 'bin'],
    }
    bundle = tmp_path / 'bundle.json'
    bundle.write_text(json.dumps({'nodes': {
        identity: {'id': identity, 'type': 'platform', 'name': identity, 'extensions': extensions}
        for identity, extensions in formats.items()}, 'edges': {}}))
    source = tmp_path / 'roms'
    source.mkdir()
    for extension in ('nes', 'sfc', 'smc', 'md', 'gen', 'bin'):
        (source / ('Same Title.' + extension)).write_bytes(b'fixture')
    scanner = RomScanner(rvdb_resolver=RVDBLibraryResolver.from_bundle(bundle),
                         archive_scan_cache=ArchiveScanCache(tmp_path / 'scan-cache.json'))
    games = scanner.scan(Source(path=str(source)))
    by_extension = {game.rom.rsplit('.', 1)[1]: game for game in games}
    assert len(games) == 6
    for extension in ('sfc', 'smc'):
        assert by_extension[extension].rvdb_platform_id == 'platform.nintendo.snes'
        assert by_extension[extension].core == 'snes9x_libretro.so'
    for extension in ('md', 'gen'):
        assert by_extension[extension].rvdb_platform_id == 'platform.sega.genesis'
        assert by_extension[extension].core == 'genesis_plus_gx_libretro.so'
    assert by_extension['nes'].rvdb_platform_id == 'platform.nintendo.nes'
    assert by_extension['bin'].rvdb_platform_id == ''
    assert by_extension['bin'].core == ''
