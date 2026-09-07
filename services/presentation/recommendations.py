from collections.abc import Mapping

from .models import PresentationProfile


class PresentationRecommendationCatalog:
    """
    Resolve deterministic automatic presentation recommendations
    from stable RVDB platform identities.

    The catalog does not perform fuzzy name matching and does not
    choose between ambiguous platform identities.
    """

    def __init__(
        self,
        recommendations: Mapping[
            str,
            PresentationProfile,
        ]
        | None = None,
    ):
        self._recommendations = {}

        if recommendations is None:
            return

        for platform_id, profile in recommendations.items():
            self._validate_platform_id(platform_id)
            self._validate_profile(profile)

            self._recommendations[
                platform_id
            ] = profile

    def recommend(
        self,
        platform_id: str,
    ) -> PresentationProfile:
        self._validate_platform_id(platform_id)

        return self._recommendations.get(
            platform_id,
            PresentationProfile(),
        )

    @staticmethod
    def _validate_platform_id(
        platform_id,
    ):
        if not isinstance(platform_id, str):
            raise TypeError(
                "Platform ID must be a string."
            )

        if not platform_id.strip():
            raise ValueError(
                "Platform ID must not be empty."
            )

    @staticmethod
    def _validate_profile(
        profile,
    ):
        if not isinstance(
            profile,
            PresentationProfile,
        ):
            raise TypeError(
                "Recommendation must be "
                "a PresentationProfile."
            )
