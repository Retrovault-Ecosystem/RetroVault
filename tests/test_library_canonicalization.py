from types import SimpleNamespace

from services.library.canonicalization import (
    LibraryCanonicalizer,
)
from services.library.models import Game


def _game(
    name,
    rom,
    *,
    platform="Nintendo Entertainment System",
    rvdb_platform_id="platform.nes",
    rvdb_game_id="",
):
    return Game(
        name=name,
        platform=platform,
        year=0,
        genre="",
        core="nestopia",
        rom=rom,
        source="Test",
        rvdb_platform_id=rvdb_platform_id,
        rvdb_game_id=rvdb_game_id,
    )


def test_single_game_remains_visible():
    canonicalizer = LibraryCanonicalizer()

    games = canonicalizer.canonicalize(
        [
            _game(
                "Example Game (USA)",
                "/roms/Example Game (USA).nes",
            )
        ]
    )

    assert len(games) == 1

    game = games[0]

    assert game.canonical_title
    assert game.family_key
    assert game.is_primary_variant is True
    assert len(game.variants) == 1
    assert game.variants[0]["preferred"] is True


def test_region_variants_collapse_to_one_visible_family():
    canonicalizer = LibraryCanonicalizer()

    games = canonicalizer.canonicalize(
        [
            _game(
                "Example Game (Japan)",
                "/roms/Example Game (Japan).nes",
            ),
            _game(
                "Example Game (USA)",
                "/roms/Example Game (USA).nes",
            ),
        ]
    )

    assert len(games) == 1

    game = games[0]

    assert len(game.variants) == 2

    roms = {
        variant["rom"]
        for variant in game.variants
    }

    assert roms == {
        "/roms/Example Game (Japan).nes",
        "/roms/Example Game (USA).nes",
    }


def test_revision_is_preserved_as_hidden_variant():
    canonicalizer = LibraryCanonicalizer()

    games = canonicalizer.canonicalize(
        [
            _game(
                "Example Game (USA)",
                "/roms/Example Game (USA).nes",
            ),
            _game(
                "Example Game (USA) (Rev 1)",
                "/roms/Example Game (USA) (Rev 1).nes",
            ),
        ]
    )

    assert len(games) == 1
    assert len(games[0].variants) == 2


def test_hack_is_preserved_as_hidden_variant():
    canonicalizer = LibraryCanonicalizer()

    games = canonicalizer.canonicalize(
        [
            _game(
                "Example Game (USA)",
                "/roms/Example Game (USA).nes",
            ),
            _game(
                "Example Game (USA) [h1]",
                "/roms/Example Game (USA) [h1].nes",
            ),
        ]
    )

    assert len(games) == 1
    assert len(games[0].variants) == 2


def test_translation_is_preserved_as_hidden_variant():
    canonicalizer = LibraryCanonicalizer()

    games = canonicalizer.canonicalize(
        [
            _game(
                "Example Game (Japan)",
                "/roms/Example Game (Japan).nes",
            ),
            _game(
                "Example Game (J) [T+Eng]",
                "/roms/Example Game (J) [T+Eng].nes",
            ),
        ]
    )

    assert len(games) == 1
    assert len(games[0].variants) == 2


def test_rvdb_identity_groups_differently_named_editions():
    canonicalizer = LibraryCanonicalizer()

    games = canonicalizer.canonicalize(
        [
            _game(
                "Localized Name",
                "/roms/Localized Name (USA).nes",
                rvdb_game_id="game.example",
            ),
            _game(
                "Original Name",
                "/roms/Original Name (Japan).nes",
                rvdb_game_id="game.example",
            ),
        ]
    )

    assert len(games) == 1
    assert len(games[0].variants) == 2
    assert games[0].family_key.startswith(
        "rvdb|"
    )


def test_different_platforms_do_not_merge():
    canonicalizer = LibraryCanonicalizer()

    games = canonicalizer.canonicalize(
        [
            _game(
                "Example Game (USA)",
                "/nes/Example Game (USA).nes",
            ),
            _game(
                "Example Game (USA)",
                "/snes/Example Game (USA).sfc",
                platform="Super Nintendo",
                rvdb_platform_id="platform.snes",
            ),
        ]
    )

    assert len(games) == 2


def test_game_model_defaults_are_backward_compatible():
    game = Game(
        name="Legacy",
        platform="NES",
        year=0,
        genre="",
        core="nestopia",
    )

    assert game.canonical_title == ""
    assert game.family_key == ""
    assert game.variant_category == ""
    assert game.variant_label == ""
    assert game.variant_region == ""
    assert game.variant_language == ""
    assert game.variant_revision == ""
    assert game.is_primary_variant is True
    assert game.variants == []
