from dataclasses import dataclass

from services.presentation.models import PresentationProfile


@dataclass(frozen=True)
class LibraryPresentationState:
    """
    Read-only game-facing presentation state exposed to the Library.

    This model deliberately does not replace PresentationProfile,
    PresentationStore, or Presentation Composition.  It is the
    Library-facing projection of those existing production contracts.
    """

    platform: str
    game_id: str

    default_profile: PresentationProfile
    system_profile: PresentationProfile
    game_profile: PresentationProfile
    effective_profile: PresentationProfile

    @property
    def shader(self):
        return self.effective_profile.shader

    @property
    def overlay(self):
        return self.effective_profile.overlay

    @property
    def artwork(self):
        return self.effective_profile.artwork

    @property
    def has_game_override(self):
        return bool(
            self.game_profile.shader
            or self.game_profile.overlay
            or self.game_profile.artwork
        )

    @property
    def has_system_override(self):
        return bool(
            self.system_profile.shader
            or self.system_profile.overlay
            or self.system_profile.artwork
        )

    @property
    def source_label(self):
        if self.has_game_override:
            return "Game Override"

        if self.has_system_override:
            return "System Assignment"

        if (
            self.default_profile.shader
            or self.default_profile.overlay
            or self.default_profile.artwork
        ):
            return "Default Assignment"

        if (
            self.effective_profile.shader
            or self.effective_profile.overlay
            or self.effective_profile.artwork
        ):
            return "Automatic / Recommended"

        return "RetroArch Default"


class LibraryPresentationStudioService:
    """
    Library adapter around RetroVault's existing presentation boundary.

    Persistent changes go through PresentationStore.

    Effective presentation always comes from the same resolver provider
    used by GameDetails at launch time.  The Library therefore cannot
    create a second presentation precedence model.
    """

    def __init__(
        self,
        presentation_store=None,
        presentation_resolver_provider=None,
    ):
        self.presentation_store = presentation_store
        self.presentation_resolver_provider = (
            presentation_resolver_provider
        )

    @staticmethod
    def _platform(game):
        return str(
            getattr(game, "platform", "")
            or getattr(game, "system", "")
            or ""
        )

    @staticmethod
    def _game_id(game):
        for attribute in (
            "rvdb_game_id",
            "game_id",
            "id",
        ):
            value = getattr(
                game,
                attribute,
                "",
            )

            if value not in (
                None,
                "",
            ):
                return str(value)

        return ""

    @staticmethod
    def _empty_profile():
        return PresentationProfile()

    def _store_snapshot(self):
        if self.presentation_store is None:
            return {
                "default": self._empty_profile(),
                "systems": {},
                "games": {},
            }

        loader = getattr(
            self.presentation_store,
            "load",
            None,
        )

        if not callable(loader):
            raise RuntimeError(
                "PresentationStore does not expose load()."
            )

        data = loader()

        if not isinstance(data, dict):
            raise RuntimeError(
                "PresentationStore load() must return a mapping."
            )

        return data

    def effective_profile(self, game):
        provider = self.presentation_resolver_provider

        if provider is None:
            return self._empty_profile()

        resolver = provider()

        if resolver is None:
            return self._empty_profile()

        return resolver.resolve(
            self._platform(game),
            self._game_id(game),
        )

    def state_for(self, game):
        data = self._store_snapshot()

        platform = self._platform(game)
        game_id = self._game_id(game)

        default_profile = data.get(
            "default",
            self._empty_profile(),
        )

        systems = data.get(
            "systems",
            {},
        ) or {}

        games = data.get(
            "games",
            {},
        ) or {}

        system_profile = systems.get(
            platform,
            self._empty_profile(),
        )

        game_profile = games.get(
            game_id,
            self._empty_profile(),
        )

        return LibraryPresentationState(
            platform=platform,
            game_id=game_id,
            default_profile=default_profile,
            system_profile=system_profile,
            game_profile=game_profile,
            effective_profile=self.effective_profile(
                game
            ),
        )

    def assign_game_overlay(
        self,
        game,
        overlay,
    ):
        if self.presentation_store is None:
            raise RuntimeError(
                "PresentationStore is unavailable."
            )

        game_id = self._game_id(
            game
        )

        if not game_id:
            raise ValueError(
                "Game identity is unavailable."
            )

        return self.presentation_store.assign_game_overlay(
            game_id,
            overlay,
        )

    def assign_game_shader(
        self,
        game,
        shader,
    ):
        if self.presentation_store is None:
            raise RuntimeError(
                "PresentationStore is unavailable."
            )

        game_id = self._game_id(
            game
        )

        if not game_id:
            raise ValueError(
                "Game identity is unavailable."
            )

        return self.presentation_store.assign_game_shader(
            game_id,
            shader,
        )

    def clear_game_overlay(self, game):
        if self.presentation_store is None:
            raise RuntimeError(
                "PresentationStore is unavailable."
            )

        game_id = self._game_id(game)

        if not game_id:
            raise ValueError(
                "Game identity is unavailable."
            )

        return self.presentation_store.clear_game_overlay(
            game_id
        )

    def clear_game_shader(self, game):
        if self.presentation_store is None:
            raise RuntimeError(
                "PresentationStore is unavailable."
            )

        game_id = self._game_id(game)

        if not game_id:
            raise ValueError(
                "Game identity is unavailable."
            )

        method = getattr(
            self.presentation_store,
            "clear_game_shader",
            None,
        )

        if not callable(method):
            raise RuntimeError(
                "PresentationStore does not support "
                "clearing game shader assignments."
            )

        return method(
            game_id
        )
