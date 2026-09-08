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

        self.manual_resolver = manual_resolver
        self.recommendation_composer = (
            recommendation_composer
        )

    def resolve(
        self,
        game,
    ) -> PresentationProfile:
        manual = self.manual_resolver.resolve(
            game
        )

        platform_id = str(
            getattr(
                game,
                "rvdb_platform_id",
                "",
            )
            or ""
        )

        if not platform_id:
            return manual

        return self.recommendation_composer.compose(
            platform_id=platform_id,
            manual=manual,
        )
