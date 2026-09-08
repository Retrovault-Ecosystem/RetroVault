from .assets import PresentationAssetReferenceResolver
from .models import PresentationProfile
from .recommendations import PresentationRecommendationCatalog


class PresentationRecommendationResolver:
    """
    Resolve a curated RetroVault presentation recommendation
    into locally usable presentation assets.

    Responsibilities remain deliberately separated:

        PresentationRecommendationCatalog
            -> portable PresentationProfile

        PresentationAssetReferenceResolver
            -> local PresentationProfile

    This boundary performs no fuzzy platform matching, persistence,
    manual/automatic composition, or launch-time mutation.
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

    def resolve(
        self,
        platform_id: str,
    ) -> PresentationProfile:
        recommendation = self.catalog.recommend(
            platform_id
        )

        return self.asset_resolver.resolve_profile(
            recommendation
        )
