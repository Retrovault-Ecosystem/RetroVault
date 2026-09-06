from services.library.state import game_identity

from .models import PresentationProfile


class PresentationResolver:
    """
    Resolve RetroVault presentation assignments.

    Precedence:

        game
        -> system
        -> default
        -> empty profile

    Precedence is applied independently to each presentation field.
    """

    def __init__(
        self,
        default=None,
        systems=None,
        games=None,
    ):
        self.default = (
            default
            if default is not None
            else PresentationProfile()
        )

        self.systems = dict(
            systems or {}
        )

        self.games = dict(
            games or {}
        )

    @staticmethod
    def _merge(
        base: PresentationProfile,
        override: PresentationProfile,
    ) -> PresentationProfile:
        return PresentationProfile(
            shader=(
                override.shader
                or base.shader
            ),
            overlay=(
                override.overlay
                or base.overlay
            ),
            artwork=(
                override.artwork
                or base.artwork
            ),
        )

    def resolve(
        self,
        game,
    ) -> PresentationProfile:
        result = self.default

        platform_id = str(
            getattr(
                game,
                "rvdb_platform_id",
                "",
            )
            or ""
        )

        if platform_id:
            system_profile = self.systems.get(
                platform_id
            )

            if system_profile is not None:
                result = self._merge(
                    result,
                    system_profile,
                )

        try:
            identity = game_identity(
                game
            )
        except ValueError:
            identity = ""

        if identity:
            game_profile = self.games.get(
                identity
            )

            if game_profile is not None:
                result = self._merge(
                    result,
                    game_profile,
                )

        return result
