from collections.abc import Mapping

from .models import PresentationProfile


class PresentationRecommendationCatalog:
    """
    Resolve deterministic automatic presentation recommendations
    from stable RVDB platform and game identities.

    System recommendations provide the automatic presentation
    baseline. Game recommendations may override that baseline
    property-by-property.

    The catalog performs no fuzzy identity matching.
    """

    def __init__(
        self,
        recommendations: Mapping[
            str,
            PresentationProfile,
        ]
        | None = None,
        *,
        game_recommendations: Mapping[
            str,
            PresentationProfile,
        ]
        | None = None,
    ):
        self._recommendations = {}
        self._game_recommendations = {}

        if recommendations is not None:
            for platform_id, profile in recommendations.items():
                self._validate_platform_id(platform_id)
                self._validate_profile(profile)

                self._recommendations[
                    platform_id
                ] = profile

        if game_recommendations is not None:
            for game_id, profile in game_recommendations.items():
                self._validate_game_id(game_id)
                self._validate_profile(profile)

                self._game_recommendations[
                    game_id
                ] = profile

    def recommend(
        self,
        platform_id: str,
    ) -> PresentationProfile:
        """
        Return the system-level automatic recommendation.

        This preserves the original system recommendation API.
        """
        self._validate_platform_id(platform_id)

        return self._recommendations.get(
            platform_id,
            PresentationProfile(),
        )

    def recommend_game(
        self,
        game_id: str,
    ) -> PresentationProfile:
        """
        Return the game-level automatic recommendation.
        """
        self._validate_game_id(game_id)

        return self._game_recommendations.get(
            game_id,
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
    def _validate_game_id(
        game_id,
    ):
        if not isinstance(game_id, str):
            raise TypeError(
                "Game ID must be a string."
            )

        if not game_id.strip():
            raise ValueError(
                "Game ID must not be empty."
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
