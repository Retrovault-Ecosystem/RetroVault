from services.presentation import (
    PresentationAssetReferenceResolver,
    PresentationProfile,
    PresentationRecommendationCatalog,
    PresentationRecommendationComposer,
    PresentationRecommendationResolver,
)


SNES = "platform.nintendo.snes"
SUPER_METROID = "game.super_metroid"


def build_composer():
    catalog = PresentationRecommendationCatalog(
        {
            SNES: PresentationProfile(
                shader="/system.slangp",
                overlay="/system.cfg",
                artwork="/system.png",
            ),
        },
        game_recommendations={
            SUPER_METROID: PresentationProfile(
                overlay="/game.cfg",
                artwork="/game.png",
            ),
        },
    )

    resolver = PresentationRecommendationResolver(
        catalog=catalog,
        asset_resolver=(
            PresentationAssetReferenceResolver()
        ),
    )

    return PresentationRecommendationComposer(
        recommendation_resolver=resolver
    )


def test_composer_uses_system_then_game_automatic_profile():
    composer = build_composer()

    result = composer.compose(
        platform_id=SNES,
        game_id=SUPER_METROID,
        manual=PresentationProfile(),
    )

    assert result == PresentationProfile(
        shader="/system.slangp",
        overlay="/game.cfg",
        artwork="/game.png",
    )


def test_manual_values_remain_authoritative_over_game_automatic():
    composer = build_composer()

    result = composer.compose(
        platform_id=SNES,
        game_id=SUPER_METROID,
        manual=PresentationProfile(
            overlay="/manual.cfg",
        ),
    )

    assert result == PresentationProfile(
        shader="/system.slangp",
        overlay="/manual.cfg",
        artwork="/game.png",
    )


def test_manual_system_shader_can_coexist_with_game_automatic_values():
    composer = build_composer()

    result = composer.compose(
        platform_id=SNES,
        game_id=SUPER_METROID,
        manual=PresentationProfile(
            shader="/manual.slangp",
        ),
    )

    assert result == PresentationProfile(
        shader="/manual.slangp",
        overlay="/game.cfg",
        artwork="/game.png",
    )


def test_missing_game_identity_preserves_existing_system_behavior():
    composer = build_composer()

    result = composer.compose(
        platform_id=SNES,
        manual=PresentationProfile(),
    )

    assert result == PresentationProfile(
        shader="/system.slangp",
        overlay="/system.cfg",
        artwork="/system.png",
    )
