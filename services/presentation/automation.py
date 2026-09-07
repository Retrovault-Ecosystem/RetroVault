from .models import PresentationProfile


class PresentationAutomationPolicy:
    """
    Compose automatic presentation choices with an existing
    manually resolved RetroVault presentation.

    Manual presentation properties are authoritative.

    Automation may supply only properties that remain empty after
    normal Default/System/Game presentation resolution.
    """

    @staticmethod
    def compose(
        manual: PresentationProfile,
        automatic: PresentationProfile,
    ) -> PresentationProfile:
        if not isinstance(
            manual,
            PresentationProfile,
        ):
            raise TypeError(
                "Manual presentation must be "
                "a PresentationProfile."
            )

        if not isinstance(
            automatic,
            PresentationProfile,
        ):
            raise TypeError(
                "Automatic presentation must be "
                "a PresentationProfile."
            )

        return PresentationProfile(
            shader=(
                manual.shader
                or automatic.shader
            ),
            overlay=(
                manual.overlay
                or automatic.overlay
            ),
            artwork=(
                manual.artwork
                or automatic.artwork
            ),
        )
