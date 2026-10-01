"""Coordinate intent and existing production policy without runtime side effects."""
from .models import LaunchPresentation, PresentationProfile
from .production_package_resolver import CanonicalProductionPackageResolver
from services.retroarch.core_identity import canonical_libretro_core_identity


class LaunchPresentationResolver:
    def __init__(self, *, intent_resolver=None, config=None, visual_tuning=None):
        self.intent_resolver = intent_resolver
        self.config = config
        self.visual_tuning = visual_tuning or {}

    def select(self, *, platform_id, core_identity, requested, sources=()):
        package = CanonicalProductionPackageResolver.resolve(
            platform_id=platform_id, core_identity=core_identity, **({"config": self.config} if self.config is not None else {}),
        )
        if package is not None:
            # Suppressed intent is retained for display, not materialized as a
            # prerequisite for a package that does not consume it.
            return LaunchPresentation(requested, PresentationProfile(
                shader=package.shader, overlay=package.overlay,
                artwork=""), tuple(sources), "production package", package)
        selected = (self.intent_resolver.asset_resolver.resolve_profile(requested)
                    if self.intent_resolver is not None else requested)
        return LaunchPresentation(requested, selected, tuple(sources))

    def describe(self, game):
        requested, sources = self.intent_resolver.references_with_sources(game)
        core = getattr(game, "core", "") or ""
        try:
            decision = self.select(
                platform_id=str(getattr(game, "rvdb_platform_id", "") or ""),
                core_identity=canonical_libretro_core_identity(core) if core else "",
                requested=requested, sources=sources.items(),
            )
            from dataclasses import replace
            from services.library.identity import game_identity
            from .visual_tuning import resolve_values
            values = resolve_values(self.visual_tuning, getattr(game, 'rvdb_platform_id', ''),
                                    game_identity(game)) if self.visual_tuning else {}
            if values and decision.package is None:
                raise ValueError('CRT adjustments require a production package.')
            return replace(decision, visual_tuning=tuple(values.items()))
        except (OSError, ValueError) as exc:
            return LaunchPresentation(requested, PresentationProfile(), tuple(sources.items()),
                                      "unavailable", error=str(exc))

    def resolve(self, game):
        decision = self.describe(game)
        if not decision.available:
            raise ValueError(decision.error)
        return decision.selected
