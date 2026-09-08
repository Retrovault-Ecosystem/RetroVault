from services.presentation import (
    PresentationAssetReferenceResolver,
    PresentationProfile,
    PresentationRecommendationCatalog,
    PresentationRecommendationResolver,
)


SNES = "platform.nintendo.snes"
SUPER_METROID = "game.super_metroid"


def resolver_for(
    *,
    system=None,
    game=None,
):
    return PresentationRecommendationResolver(
        catalog=PresentationRecommendationCatalog(
            {
                SNES: (
                    system
                    or PresentationProfile()
                ),
            },
            game_recommendations={
                SUPER_METROID: (
                    game
                    or PresentationProfile()
                ),
            },
        ),
        asset_resolver=(
            PresentationAssetReferenceResolver()
        ),
    )


def test_system_only_recommendation_remains_supported():
    resolver = resolver_for(
        system=PresentationProfile(
            shader="/system.slangp",
            overlay="/system.cfg",
            artwork="/system.png",
        )
    )

    assert resolver.resolve(
        SNES
    ) == PresentationProfile(
        shader="/system.slangp",
        overlay="/system.cfg",
        artwork="/system.png",
    )


def test_game_values_override_system_by_property():
    resolver = resolver_for(
        system=PresentationProfile(
            shader="/system.slangp",
            overlay="/system.cfg",
            artwork="/system.png",
        ),
        game=PresentationProfile(
            overlay="/game.cfg",
            artwork="/game.png",
        ),
    )

    assert resolver.resolve(
        SNES,
        SUPER_METROID,
    ) == PresentationProfile(
        shader="/system.slangp",
        overlay="/game.cfg",
        artwork="/game.png",
    )


def test_empty_game_values_inherit_system_values():
    resolver = resolver_for(
        system=PresentationProfile(
            shader="/system.slangp",
            overlay="/system.cfg",
            artwork="/system.png",
        ),
        game=PresentationProfile(
            shader="",
            overlay="/game.cfg",
            artwork="",
        ),
    )

    assert resolver.resolve(
        SNES,
        SUPER_METROID,
    ) == PresentationProfile(
        shader="/system.slangp",
        overlay="/game.cfg",
        artwork="/system.png",
    )


def test_unknown_game_identity_preserves_system_profile():
    resolver = resolver_for(
        system=PresentationProfile(
            shader="/system.slangp",
            overlay="/system.cfg",
        ),
    )

    assert resolver.resolve(
        SNES,
        "game.unknown",
    ) == PresentationProfile(
        shader="/system.slangp",
        overlay="/system.cfg",
    )


def test_empty_game_identity_preserves_system_profile():
    resolver = resolver_for(
        system=PresentationProfile(
            shader="/system.slangp",
        ),
    )

    assert resolver.resolve(
        SNES,
        "",
    ) == PresentationProfile(
        shader="/system.slangp",
    )


def test_game_recommendation_can_supply_missing_system_property():
    resolver = resolver_for(
        system=PresentationProfile(
            shader="/system.slangp",
        ),
        game=PresentationProfile(
            artwork="/game.png",
        ),
    )

    assert resolver.resolve(
        SNES,
        SUPER_METROID,
    ) == PresentationProfile(
        shader="/system.slangp",
        artwork="/game.png",
    )
