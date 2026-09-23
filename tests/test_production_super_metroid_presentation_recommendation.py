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
    "retrovault/snes/classic/"
    "RetroVault_SNES_Classic_CRT.slangp"
)

SNES_OVERLAY_REFERENCE = (
    "retro-vault://overlays/"
    "retrovault/snes/classic/"
    "RetroVault_SNES_Classic.cfg"
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
    assert profile.overlay == SNES_OVERLAY_REFERENCE
    assert profile.artwork == ""


def test_super_metroid_has_no_independent_presentation_authority():
    catalog = (
        PresentationRecommendationManifest()
        .load()
    )

    profile = catalog.recommend_game(
        SUPER_METROID
    )

    assert profile.shader == ""
    assert profile.overlay == ""
    assert profile.artwork == ""


def test_snes_system_recommendation_resolves_to_native_crt():
    profile = production_resolver().resolve(
        SNES
    )

    assert profile.shader.endswith(
        "/retrovault/snes/classic/"
        "RetroVault_SNES_Classic_CRT.slangp"
    )

    assert profile.overlay.endswith(
        "/retrovault/snes/classic/"
        "RetroVault_SNES_Classic.cfg"
    )

    assert profile.artwork == ""


def test_super_metroid_inherits_snes_system_presentation():
    profile = production_resolver().resolve(
        SNES,
        SUPER_METROID,
    )

    assert profile.shader.endswith(
        "/retrovault/snes/classic/"
        "RetroVault_SNES_Classic_CRT.slangp"
    )

    assert profile.overlay.endswith(
        "/retrovault/snes/classic/"
        "RetroVault_SNES_Classic.cfg"
    )

    assert profile.artwork == ""


def test_unknown_snes_game_preserves_system_recommendation():
    profile = production_resolver().resolve(
        SNES,
        "game.unknown",
    )

    assert profile.shader.endswith(
        "/retrovault/snes/classic/"
        "RetroVault_SNES_Classic_CRT.slangp"
    )

    assert profile.overlay.endswith(
        "/retrovault/snes/classic/"
        "RetroVault_SNES_Classic.cfg"
    )

    assert profile.artwork == ""
