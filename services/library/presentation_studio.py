from services.library.identity import game_identity
from dataclasses import dataclass

from services.presentation.models import PresentationProfile, LaunchPresentation
from services.presentation.launch_resolver import LaunchPresentationResolver


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
    launch_decision: LaunchPresentation | None = None
    backend: str = "retroarch"

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
        if self.backend == "snes9x":
            return "Snes9x standalone"
        if self.launch_decision is not None:
            return ("Production Package" if self.launch_decision.authority == "production package"
                    else "Unavailable" if not self.launch_decision.available else "Saved / Recommended")
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
        return str(getattr(game, "rvdb_platform_id", "") or "")

    @staticmethod
    def _game_id(game):
        try:
            return game_identity(game)
        except ValueError:
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

        return resolver.resolve(game)

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

        from config import ConfigLoader
        from services.emulators.models import selected_backend, SNES9X
        backend = selected_backend(ConfigLoader().load(), getattr(game, 'rvdb_platform_id', ''))
        if backend == SNES9X:
            return LibraryPresentationState(
                platform=platform, game_id=game_id, default_profile=default_profile,
                system_profile=system_profile, game_profile=game_profile,
                effective_profile=self._empty_profile(), backend=backend)

        resolver = (self.presentation_resolver_provider()
                    if self.presentation_resolver_provider else None)
        decision = resolver.describe(game) if isinstance(resolver, LaunchPresentationResolver) else None
        effective = (decision.selected if decision is not None else
                     resolver.resolve(game) if resolver is not None else self._empty_profile())
        return LibraryPresentationState(
            platform=platform,
            game_id=game_id,
            default_profile=default_profile,
            system_profile=system_profile,
            game_profile=game_profile,
            effective_profile=effective,
            launch_decision=decision,
        )

    def assign_game_overlay(self, game, overlay):
        return self.assign('overlay', 'game', overlay, game)

    def assign_game_shader(self, game, shader):
        return self.assign('shader', 'game', shader, game)

    def clear_game_overlay(self, game):
        return self.clear_assignment('overlay', 'game', game)

    def clear_game_shader(self, game):
        return self.clear_assignment('shader', 'game', game)

    @staticmethod
    def assignment_target(scope, game=None):
        if scope == 'default':
            return ''
        if game is None:
            raise ValueError('Select a game in the Library first.')
        if scope == 'system':
            identity = str(getattr(game, 'rvdb_platform_id', '') or '')
            if not identity:
                raise ValueError('The selected game does not have a canonical RVDB system identity.')
            return identity
        if scope == 'game':
            try:
                return game_identity(game)
            except ValueError:
                raise ValueError('The selected game does not have a stable RetroVault game identity.') from None
        raise ValueError(f'Unknown assignment scope: {scope}')

    def assign(self, field, scope, reference, game=None):
        if field not in ('overlay', 'shader'):
            raise ValueError(f'Unsupported presentation field: {field}')
        identity = self.assignment_target(scope, game)
        if self.presentation_store is None:
            raise RuntimeError('PresentationStore is unavailable.')
        method = getattr(self.presentation_store, f'assign_{scope}_{field}')
        return method(reference) if scope == 'default' else method(identity, reference)

    def clear_assignment(self, field, scope, game=None):
        if field not in ('overlay', 'shader'):
            raise ValueError(f'Unsupported presentation field: {field}')
        identity = self.assignment_target(scope, game)
        if self.presentation_store is None:
            raise RuntimeError('PresentationStore is unavailable.')
        method = getattr(self.presentation_store, f'clear_{scope}_{field}', None)
        if not callable(method):
            raise ValueError(f'Clearing {scope} {field} is unsupported.')
        return method() if scope == 'default' else method(identity)

    def assignment_display_state(self, game=None):
        """Saved preferences and effective selection are distinct read results."""
        from services.presentation.resolver import PresentationResolver
        data = self._store_snapshot()
        default = data.get('default', self._empty_profile())
        system = data.get('systems', {}).get(self._platform(game), self._empty_profile())
        specific = data.get('games', {}).get(self._game_id(game), self._empty_profile()) if game else self._empty_profile()
        result = dict(default=default, system=system, game=specific,
                      effective=default, error='', launch=False)
        if game is not None:
            provider = self.presentation_resolver_provider or getattr(self.presentation_store, 'resolver', None)
            result['launch'] = self.presentation_resolver_provider is not None
            try:
                resolver = provider() if callable(provider) else PresentationResolver(
                    default=default, systems=data.get('systems'), games=data.get('games'))
                result['effective'] = resolver.resolve(game)
            except (OSError, TypeError, ValueError, RuntimeError) as exc:
                result['error'] = str(exc)
        return result

    def visual_tuning_state(self, game):
        from services.presentation.visual_tuning import controls, resolve_values
        platform = self._platform(game)
        identity = self._game_id(game)
        data = self._store_snapshot().get('visual_tuning', {})
        return dict(controls=controls(platform),
                    systems=data.get('systems', {}).get(platform, {}),
                    games=data.get('games', {}).get(identity, {}).get('values', {}),
                    effective=resolve_values(data, platform, identity))

    def set_visual_adjustment(self, game, scope, key, mode, value=None):
        from services.presentation.visual_tuning import controls
        if scope not in ('systems', 'games') or mode not in ('inherit', 'approved', 'custom'):
            raise ValueError('Invalid CRT adjustment operation.')
        state = self.visual_tuning_state(game)
        if key not in {c.key for c in state['controls']}:
            raise ValueError('This package does not support that CRT control.')
        values = dict(state[scope])
        if mode == 'inherit':
            values.pop(key, None)
        else:
            values[key] = None if mode == 'approved' else value
        platform = self._platform(game)
        identity = platform if scope == 'systems' else self._game_id(game)
        self.presentation_store.set_visual_tuning(scope, identity, platform, values)

    def restore_approved_visuals(self, game, scope):
        from services.presentation.visual_tuning import controls
        platform = self._platform(game)
        identity = platform if scope == 'systems' else self._game_id(game)
        # Game reset explicitly masks platform adjustments; platform reset clears its own.
        values = {c.key: None for c in controls(platform)} if scope == 'games' else {}
        self.presentation_store.set_visual_tuning(scope, identity, platform, values)
