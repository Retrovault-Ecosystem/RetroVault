from .assets import PresentationAssetReferenceResolver
from .models import PresentationProfile
from .recommendations import (
    PresentationRecommendationCatalog,
)


class PresentationRecommendationResolver:
    """
    Resolve portable RetroVault automatic recommendations
    into local PresentationProfile values.

    System recommendations form the automatic baseline.

    When a canonical RVDB game identity is supplied, non-empty
    game recommendation properties override the corresponding
    system recommendation properties.

    This resolver performs no manual presentation composition,
    persistence, or launch-time mutation.
    """

    def __init__(
        self,
        *,
        catalog,
        asset_resolver,
    ):
        if not isinstance(
            catalog,
            PresentationRecommendationCatalog,
        ):
            raise TypeError(
                "Recommendation catalog must be a "
                "PresentationRecommendationCatalog."
            )

        if not isinstance(
            asset_resolver,
            PresentationAssetReferenceResolver,
        ):
            raise TypeError(
                "Asset resolver must be a "
                "PresentationAssetReferenceResolver."
            )

        self.catalog = catalog
        self.asset_resolver = asset_resolver

    @staticmethod
    def _compose_automatic(
        system: PresentationProfile,
        game: PresentationProfile,
    ) -> PresentationProfile:
        """
        Compose the automatic recommendation hierarchy.

        Game values override system values only when the
        game property is non-empty.
        """
        if not isinstance(
            system,
            PresentationProfile,
        ):
            raise TypeError(
                "System recommendation must be a "
                "PresentationProfile."
            )

        if not isinstance(
            game,
            PresentationProfile,
        ):
            raise TypeError(
                "Game recommendation must be a "
                "PresentationProfile."
            )

        return PresentationProfile(
            shader=(
                game.shader
                or system.shader
            ),
            overlay=(
                game.overlay
                or system.overlay
            ),
            artwork=(
                game.artwork
                or system.artwork
            ),
        )

    def resolve(
        self,
        platform_id: str,
        game_id: str = "",
    ) -> PresentationProfile:
        system = self.catalog.recommend(
            platform_id
        )

        game = PresentationProfile()

        if game_id:
            game = self.catalog.recommend_game(
                game_id
            )

        automatic = self._compose_automatic(
            system,
            game,
        )

        return self.asset_resolver.resolve_profile(
            automatic
        )
