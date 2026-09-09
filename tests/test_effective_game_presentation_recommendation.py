from dataclasses import dataclass

from services.presentation import (
    EffectivePresentationResolver,
    PresentationAssetReferenceResolver,
    PresentationProfile,
    PresentationRecommendationCatalog,
    PresentationRecommendationComposer,
    PresentationRecommendationResolver,
    PresentationResolver,
)


SNES = "platform.nintendo.snes"
SUPER_METROID = "game.super_metroid"


@dataclass
class Game:
    name: str = "Super Metroid"
    platform: str = "Super Nintendo Entertainment System"
    rom: str = "/roms/Super Metroid.sfc"
    rvdb_platform_id: str = SNES
    rvdb_game_id: str = SUPER_METROID


class FakeManualResolver(PresentationResolver):

    def __init__(self, profile):
        self._profile = profile

    def resolve(self, game):
        return self._profile


def build_effective(
    manual,
):
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

    automatic = PresentationRecommendationResolver(
        catalog=catalog,
        asset_resolver=(
            PresentationAssetReferenceResolver()
        ),
    )

    composer = PresentationRecommendationComposer(
        recommendation_resolver=automatic
    )

    return EffectivePresentationResolver(
        manual_resolver=FakeManualResolver(
            manual
        ),
        recommendation_composer=composer,
        asset_resolver=(
            PresentationAssetReferenceResolver()
        ),
    )


def test_effective_resolver_consumes_rvdb_game_identity():
    resolver = build_effective(
        PresentationProfile()
    )

    assert resolver.resolve(
        Game()
    ) == PresentationProfile(
        shader="/system.slangp",
        overlay="/game.cfg",
        artwork="/game.png",
    )


def test_manual_profile_remains_final_authority():
    resolver = build_effective(
        PresentationProfile(
            shader="/manual.slangp",
            artwork="/manual.png",
        )
    )

    assert resolver.resolve(
        Game()
    ) == PresentationProfile(
        shader="/manual.slangp",
        overlay="/game.cfg",
        artwork="/manual.png",
    )


def test_missing_game_identity_uses_system_automatic_only():
    resolver = build_effective(
        PresentationProfile()
    )

    game = Game(
        rvdb_game_id="",
    )

    assert resolver.resolve(
        game
    ) == PresentationProfile(
        shader="/system.slangp",
        overlay="/system.cfg",
        artwork="/system.png",
    )


def test_missing_platform_identity_still_returns_manual_only():
    manual = PresentationProfile(
        shader="/manual.slangp",
    )

    resolver = build_effective(
        manual
    )

    game = Game(
        rvdb_platform_id="",
        rvdb_game_id=SUPER_METROID,
    )

    assert resolver.resolve(
        game
    ) == manual
