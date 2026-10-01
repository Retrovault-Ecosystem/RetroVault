from .automation import PresentationAutomationPolicy
from .assets import PresentationAssetReferenceResolver
from .composer import PresentationRecommendationComposer
from .models import PresentationProfile
from .resolver import PresentationResolver


class EffectivePresentationResolver:
    """
    Resolve the final effective RetroVault presentation for a game.

    Resolution order:

        PresentationResolver
            -> manually resolved Default/System/Game profile

        PresentationRecommendationComposer
            -> locally resolved automatic recommendation
            -> manual values remain authoritative by property

        EffectivePresentationResolver
            -> final PresentationProfile

    This adapter deliberately preserves the existing ``resolve(game)``
    consumer contract. It performs no persistence and no launch mutation.
    """

    def __init__(
        self,
        *,
        manual_resolver,
        recommendation_composer,
        asset_resolver,
    ):
        if not isinstance(
            manual_resolver,
            PresentationResolver,
        ):
            raise TypeError(
                "Manual resolver must be a "
                "PresentationResolver."
            )

        if not isinstance(
            recommendation_composer,
            PresentationRecommendationComposer,
        ):
            raise TypeError(
                "Recommendation composer must be a "
                "PresentationRecommendationComposer."
            )

        if not isinstance(
            asset_resolver,
            PresentationAssetReferenceResolver,
        ):
            raise TypeError(
                "Asset resolver must be a "
                "PresentationAssetReferenceResolver."
            )

        self.manual_resolver = manual_resolver
        self.recommendation_composer = (
            recommendation_composer
        )
        self.asset_resolver = asset_resolver

    def resolve(
        self,
        game,
    ) -> PresentationProfile:
        manual = self.manual_resolver.resolve(game)
        platform_id = str(getattr(game, "rvdb_platform_id", "") or "")
        if not platform_id:
            return self.asset_resolver.resolve_profile(manual)
        effective = self.recommendation_composer.compose(
            platform_id=platform_id, game_id=str(getattr(game, "rvdb_game_id", "") or ""), manual=manual)
        return self.asset_resolver.resolve_profile(effective)

    def references_with_sources(self, game):
        manual, sources = self.manual_resolver.resolve_with_sources(game)
        platform_id = str(getattr(game, "rvdb_platform_id", "") or "")
        game_id = str(getattr(game, "rvdb_game_id", "") or "")
        if not platform_id:
            return manual, sources
        automatic_resolver = self.recommendation_composer.recommendation_resolver
        automatic = automatic_resolver.references(platform_id, game_id)
        game_recommendation = (automatic_resolver.catalog.recommend_game(game_id)
                               if game_id else PresentationProfile())
        for field in sources:
            if not getattr(manual, field) and getattr(automatic, field):
                sources[field] = ("game recommendation" if getattr(game_recommendation, field)
                                  else "platform recommendation")
        return PresentationAutomationPolicy.compose(manual, automatic), sources
