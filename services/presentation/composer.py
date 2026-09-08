from .automation import PresentationAutomationPolicy
from .models import PresentationProfile
from .recommendation_resolver import (
    PresentationRecommendationResolver,
)


class PresentationRecommendationComposer:
    """
    Compose an existing manually resolved presentation with a
    locally resolved automatic RetroVault recommendation.

    Responsibilities:

        manual PresentationProfile
            +
        PresentationRecommendationResolver
            -> local automatic PresentationProfile
            +
        PresentationAutomationPolicy
            -> effective PresentationProfile

    This boundary performs no persistence, Default/System/Game
    resolution, catalog parsing, asset discovery, or launch mutation.
    """

    def __init__(
        self,
        *,
        recommendation_resolver,
    ):
        if not isinstance(
            recommendation_resolver,
            PresentationRecommendationResolver,
        ):
            raise TypeError(
                "Recommendation resolver must be a "
                "PresentationRecommendationResolver."
            )

        self.recommendation_resolver = (
            recommendation_resolver
        )

    def compose(
        self,
        *,
        platform_id: str,
        manual: PresentationProfile,
    ) -> PresentationProfile:
        if not isinstance(
            manual,
            PresentationProfile,
        ):
            raise TypeError(
                "Manual presentation must be a "
                "PresentationProfile."
            )

        automatic = (
            self.recommendation_resolver.resolve(
                platform_id
            )
        )

        return PresentationAutomationPolicy.compose(
            manual,
            automatic,
        )
