from pathlib import Path

from services.cheats import (
    CheatCategory,
    CheatCode,
    CheatCodeType,
    CheatService,
)
from services.cheats.retroarch import (
    RetroArchCheatParser,
)
from services.library.models import Game


def _game(
    rom="/games/Super Mario Bros. (USA).nes",
):
    return Game(
        name="Super Mario Bros.",
        platform="NES",
        year=1985,
        genre="Platform",
        rom=rom,
        core="lr-fceumm",
        canonical_title="Super Mario Bros.",
        variant_category="standard",
        variant_region="USA",
        variant_language="English",
        rvdb_game_id="game.super-mario-bros",
    )


def test_identity_uses_physical_variant():
    game = _game(
        "/games/Super Mario Bros. (Japan) (Rev A).nes"
    )

    game.variant_category = "revision"
    game.variant_region = "Japan"
    game.variant_revision = "Rev A"

    identity = CheatService.identity_for(
        game
    )

    assert (
        identity.filename
        == "Super Mario Bros. (Japan) (Rev A).nes"
    )
    assert identity.region == "Japan"
    assert identity.revision == "Rev A"
    assert (
        identity.rvdb_game_id
        == "game.super-mario-bros"
    )


def test_identity_tracks_archive_member():
    identity = CheatService.identity_for(
        _game(
            "/games/Super Mario Bros.7z"
        ),
        (
            "Super Mario Bros. "
            "(USA) (Rev A).nes"
        ),
    )

    assert (
        identity.filename
        == "Super Mario Bros. (USA) (Rev A).nes"
    )


def test_parser_reads_retroarch_cheats():
    cheats = RetroArchCheatParser.parse_text(
        '''
cheats = 2

cheat0_desc = "Infinite Lives"
cheat0_code = "SXIOPO"
cheat0_enable = false

cheat1_desc = "Level Select"
cheat1_code = "AAAAAA"
cheat1_enable = true
'''
    )

    assert len(cheats) == 2
    assert cheats[0].name == "Infinite Lives"
    assert cheats[0].code == "SXIOPO"
    assert not cheats[0].enabled
    assert (
        cheats[0].category
        == CheatCategory.LIVES_HEALTH
    )

    assert cheats[1].enabled
    assert (
        cheats[1].category
        == CheatCategory.LEVEL_STAGE
    )


def test_parser_serialization_round_trip():
    original = [
        CheatCode(
            name="Invincibility",
            code="AAAA-BBBB",
            category=(
                CheatCategory.INVINCIBILITY
            ),
            enabled=True,
        ),
        CheatCode(
            name="Level Select",
            code="CCCC-DDDD",
            category=(
                CheatCategory.LEVEL_STAGE
            ),
            enabled=False,
        ),
    ]

    text = RetroArchCheatParser.serialize(
        original
    )

    parsed = RetroArchCheatParser.parse_text(
        text
    )

    assert len(parsed) == 2
    assert parsed[0].name == "Invincibility"
    assert parsed[0].code == "AAAA-BBBB"
    assert parsed[0].enabled
    assert parsed[1].name == "Level Select"
    assert not parsed[1].enabled


def test_enable_all_only_enables_compatible():
    cheats = [
        CheatCode(
            name="Compatible",
            code="AAAA",
            compatible=True,
        ),
        CheatCode(
            name="Wrong Revision",
            code="BBBB",
            compatible=False,
        ),
    ]

    enabled = (
        CheatService
        .enable_all_compatible(
            cheats
        )
    )

    assert enabled[0].enabled
    assert not enabled[1].enabled


def test_disable_all():
    cheats = [
        CheatCode(
            name="One",
            code="AAAA",
            enabled=True,
        ),
        CheatCode(
            name="Two",
            code="BBBB",
            enabled=True,
        ),
    ]

    disabled = (
        CheatService.disable_all(
            cheats
        )
    )

    assert not any(
        cheat.enabled
        for cheat in disabled
    )


def test_manual_cheat_supports_code_formats():
    for code_type in (
        CheatCodeType.GAME_GENIE,
        CheatCodeType.GAMESHARK,
        CheatCodeType.ACTION_REPLAY,
        CheatCodeType.PRO_ACTION_REPLAY,
        CheatCodeType.CODEBREAKER,
        CheatCodeType.RAW,
        CheatCodeType.CUSTOM,
    ):
        cheat = (
            CheatService.manual_cheat(
                "Custom",
                "AAAA-BBBB",
                code_type,
            )
        )

        assert cheat.code_type == code_type


def test_discovery_reads_matching_cht(
    tmp_path,
):
    root = tmp_path / "cheats"
    root.mkdir()

    path = (
        root
        / "Super Mario Bros.cht"
    )

    path.write_text(
        '''
cheats = 1
cheat0_desc = "Infinite Lives"
cheat0_code = "SXIOPO"
cheat0_enable = false
'''
    )

    service = CheatService(
        roots=[root],
        user_root=(
            tmp_path
            / "user"
        ),
    )

    collection = service.discover(
        _game()
    )

    assert len(
        collection.cheats
    ) == 1

    assert (
        collection.cheats[0].name
        == "Infinite Lives"
    )


def test_discovery_prefers_physical_archive_member_name(
    tmp_path,
):
    root = tmp_path / "cheats"
    root.mkdir()

    (
        root
        / "Super Mario Bros.cht"
    ).write_text(
        '''
cheats = 1
cheat0_desc = "Infinite Lives"
cheat0_code = "AAAA"
cheat0_enable = false
'''
    )

    service = CheatService(
        roots=[root],
        user_root=(
            tmp_path
            / "user"
        ),
    )

    collection = service.discover(
        _game(
            "/games/Super Mario Bros.7z"
        ),
        (
            "Super Mario Bros. "
            "(USA) (Rev A).nes"
        ),
    )

    assert (
        collection.identity.archive_member
        == "Super Mario Bros. (USA) (Rev A).nes"
    )

    assert len(
        collection.cheats
    ) == 1


def test_import_file_persists_user_cheats(
    tmp_path,
):
    source = (
        tmp_path
        / "incoming.cht"
    )

    source.write_text(
        '''
cheats = 1
cheat0_desc = "Invincibility"
cheat0_code = "AAAA"
cheat0_enable = false
'''
    )

    service = CheatService(
        roots=[],
        user_root=(
            tmp_path
            / "user-cheats"
        ),
    )

    identity = (
        service.identity_for(
            _game()
        )
    )

    destination = (
        service.import_file(
            source,
            identity,
        )
    )

    assert destination.is_file()
    assert (
        "invincibility"
        in destination
        .read_text()
        .casefold()
    )


def test_runtime_file_contains_only_enabled_compatible(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setattr(
        "tempfile.tempdir",
        str(tmp_path),
    )

    path = CheatService.runtime_file(
        [
            CheatCode(
                name="Enabled",
                code="AAAA",
                enabled=True,
                compatible=True,
            ),
            CheatCode(
                name="Disabled",
                code="BBBB",
                enabled=False,
                compatible=True,
            ),
            CheatCode(
                name="Incompatible",
                code="CCCC",
                enabled=True,
                compatible=False,
            ),
        ]
    )

    assert path is not None

    text = Path(path).read_text()

    assert "Enabled" in text
    assert "AAAA" in text
    assert "Disabled" not in text
    assert "Incompatible" not in text


def test_flatpak_database_is_default_discovery_provider():
    from services.cheats.service import CheatService

    assert (
        CheatService.FLATPAK_DATABASE_ROOT
        in CheatService.DEFAULT_ROOTS
    )


def test_enable_all_compatible_excludes_uncertain_cheats():
    from services.cheats.models import CheatCode
    from services.cheats.service import CheatService

    cheats = [
        CheatCode(
            name="Exact",
            code="AAAA-BBBB",
            compatible=True,
        ),
        CheatCode(
            name="Uncertain",
            code="CCCC-DDDD",
            compatible=False,
        ),
    ]

    enabled = (
        CheatService.enable_all_compatible(
            cheats
        )
    )

    assert enabled[0].enabled is True
    assert enabled[1].enabled is False
