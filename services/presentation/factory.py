from config import ConfigLoader

from .assets import PresentationAssetReferenceResolver
from .composer import PresentationRecommendationComposer
from .effective_resolver import EffectivePresentationResolver
from .manifest import PresentationRecommendationManifest
from .recommendation_resolver import (
    PresentationRecommendationResolver,
)
from .store import PresentationStore


class PresentationCompositionFactory:
    """
    Build the production RetroVault presentation resolver.

    Each build reloads:

        - effective RetroVault configuration
        - persisted manual presentation assignments
        - curated presentation recommendations

    This preserves the existing launch-time provider behavior while
    keeping presentation composition out of UI and launcher code.
    """

    def __init__(
        self,
        *,
        presentation_store,
        config_loader,
        recommendation_manifest,
    ):
        if not isinstance(
            presentation_store,
            PresentationStore,
        ):
            raise TypeError(
                "Presentation store must be a "
                "PresentationStore."
            )

        if not isinstance(
            config_loader,
            ConfigLoader,
        ):
            raise TypeError(
                "Configuration loader must be a "
                "ConfigLoader."
            )

        if not isinstance(
            recommendation_manifest,
            PresentationRecommendationManifest,
        ):
            raise TypeError(
                "Recommendation manifest must be a "
                "PresentationRecommendationManifest."
            )

        self.presentation_store = (
            presentation_store
        )
        self.config_loader = config_loader
        self.recommendation_manifest = (
            recommendation_manifest
        )

    @staticmethod
    def _configured_directory(
        config,
        name,
    ):
        value = (
            config
            .get("paths", {})
            .get(name, {})
            .get("directory", "")
        )

        if not isinstance(value, str):
            raise ValueError(
                "RetroVault presentation asset "
                f"directory {name!r} must be a string."
            )

        return value or None

    def build(
        self,
    ) -> EffectivePresentationResolver:
        config = self.config_loader.load()

        if not isinstance(config, dict):
            raise ValueError(
                "RetroVault configuration must "
                "contain a mapping."
            )

        catalog = (
            self.recommendation_manifest.load()
        )

        asset_resolver = (
            PresentationAssetReferenceResolver(
                shader_root=(
                    self._configured_directory(
                        config,
                        "shaders",
                    )
                ),
                overlay_root=(
                    self._configured_directory(
                        config,
                        "overlays",
                    )
                ),
                artwork_root=(
                    self._configured_directory(
                        config,
                        "artwork",
                    )
                ),
            )
        )

        recommendation_resolver = (
            PresentationRecommendationResolver(
                catalog=catalog,
                asset_resolver=asset_resolver,
            )
        )

        composer = (
            PresentationRecommendationComposer(
                recommendation_resolver=(
                    recommendation_resolver
                )
            )
        )

        return EffectivePresentationResolver(
            manual_resolver=(
                self.presentation_store.resolver()
            ),
            recommendation_composer=composer,
        )
