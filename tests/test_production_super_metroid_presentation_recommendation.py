from config import ConfigLoader

from services.presentation import (
    PresentationAssetReferenceResolver,
    PresentationCompositionFactory,
    PresentationRecommendationManifest,
    PresentationRecommendationResolver,
)


SNES = "platform.nintendo.snes"
SUPER_METROID = "game.super_metroid"

SNES_REFERENCE = (
    "retro-vault://shaders/"
    "Mega_Bezel_Packs/"
    "Orionsangel-Original-Console-main/"
    "Presets/Standard/Nintendo_SNES/"
    "Nintendo_SNES-[STD].slangp"
)

SUPER_METROID_REFERENCE = (
    "retro-vault://shaders/"
    "Mega_Bezel_Packs/"
    "HSM_Mega_Bezel_Examples/"
    "Presets/Orionsangel_Console/"
    "SuperMetroid__STD.slangp"
)


def production_resolver():
    config = ConfigLoader().load()

    shader_root = (
        PresentationCompositionFactory
        ._configured_directory(
            config,
            "shaders",
        )
    )

    overlay_root = (
        PresentationCompositionFactory
        ._configured_directory(
            config,
            "overlays",
        )
    )

    artwork_root = (
        PresentationCompositionFactory
        ._configured_directory(
            config,
            "artwork",
        )
    )

    return PresentationRecommendationResolver(
        catalog=(
            PresentationRecommendationManifest()
            .load()
        ),
        asset_resolver=(
            PresentationAssetReferenceResolver(
                shader_root=shader_root,
                overlay_root=overlay_root,
                artwork_root=artwork_root,
            )
        ),
    )


def test_production_manifest_contains_snes_system_recommendation():
    catalog = (
        PresentationRecommendationManifest()
        .load()
    )

    profile = catalog.recommend(
        SNES
    )

    assert profile.shader == SNES_REFERENCE
    assert profile.overlay == ""
    assert profile.artwork == ""


def test_production_manifest_contains_super_metroid_recommendation():
    catalog = (
        PresentationRecommendationManifest()
        .load()
    )

    profile = catalog.recommend_game(
        SUPER_METROID
    )

    assert (
        profile.shader
        == SUPER_METROID_REFERENCE
    )

    assert profile.overlay == ""
    assert profile.artwork == ""


def test_snes_system_recommendation_resolves_to_local_asset():
    profile = production_resolver().resolve(
        SNES
    )

    assert profile.shader.endswith(
        "/Nintendo_SNES/"
        "Nintendo_SNES-[STD].slangp"
    )

    assert profile.overlay == ""
    assert profile.artwork == ""


def test_super_metroid_overrides_snes_shader_by_game_identity():
    profile = production_resolver().resolve(
        SNES,
        SUPER_METROID,
    )

    assert profile.shader.endswith(
        "/Orionsangel_Console/"
        "SuperMetroid__STD.slangp"
    )

    assert profile.overlay == ""
    assert profile.artwork == ""


def test_unknown_snes_game_preserves_system_recommendation():
    profile = production_resolver().resolve(
        SNES,
        "game.unknown",
    )

    assert profile.shader.endswith(
        "/Nintendo_SNES/"
        "Nintendo_SNES-[STD].slangp"
    )

    assert profile.overlay == ""
    assert profile.artwork == ""
