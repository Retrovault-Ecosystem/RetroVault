from pathlib import Path

from services.presentation import (
    PresentationAssetReferenceResolver,
    PresentationRecommendationManifest,
    PresentationRecommendationResolver,
)


PLATFORM_ID = "platform.nintendo.nes"

SHADER_REFERENCE = (
    "retro-vault://shaders/"
    "retrovault/nes/classic/"
    "RetroVault_NES_Classic_CRT.slangp"
)

OVERLAY_REFERENCE = (
    "retro-vault://overlays/"
    "retrovault/nes/classic/"
    "RetroVault_NES_Classic.cfg"
)


def test_production_manifest_contains_controlled_nes_recommendation():
    catalog = (
        PresentationRecommendationManifest()
        .load()
    )

    profile = catalog.recommend(
        PLATFORM_ID
    )

    assert profile.shader == SHADER_REFERENCE
    assert profile.overlay == OVERLAY_REFERENCE
    assert profile.artwork == ""


def test_controlled_nes_recommendation_resolves_exact_assets(
    tmp_path,
):
    shader_root = (
        tmp_path
        / "shaders"
    )

    overlay_root = (
        tmp_path
        / "overlays"
    )

    shader = (
        shader_root
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic_CRT.slangp"
    )

    overlay = (
        overlay_root
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic.cfg"
    )

    shader.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    overlay.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shader.write_text(
        "shader",
        encoding="utf-8",
    )

    overlay.write_text(
        "overlay",
        encoding="utf-8",
    )

    catalog = (
        PresentationRecommendationManifest()
        .load()
    )

    resolver = PresentationRecommendationResolver(
        catalog=catalog,
        asset_resolver=(
            PresentationAssetReferenceResolver(
                shader_root=shader_root,
                overlay_root=overlay_root,
                artwork_root=(
                    tmp_path
                    / "artwork"
                ),
            )
        ),
    )

    profile = resolver.resolve(
        PLATFORM_ID
    )

    assert profile.shader == str(
        shader.resolve()
    )

    assert profile.overlay == str(
        overlay.resolve()
    )

    assert profile.artwork == ""
