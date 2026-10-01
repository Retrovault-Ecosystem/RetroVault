from config.paths import config_file
import json
import os
from dataclasses import replace
from pathlib import Path

from .models import PresentationProfile


def _default_presentation_file() -> Path:
    return config_file('presentation-state.json')



class PresentationStore:
    VERSION = 3

    def __init__(
        self,
        presentation_file=None,
    ):
        self.presentation_file = Path(
            presentation_file
            or _default_presentation_file()
        ).expanduser()

    @staticmethod
    def _profile_from_data(
        data,
        context,
    ) -> PresentationProfile:
        if not isinstance(data, dict):
            raise ValueError(
                f"{context} must contain "
                "a JSON object."
            )

        allowed = {
            "shader",
            "overlay",
            "artwork",
        }

        unknown = (
            set(data)
            - allowed
        )

        if unknown:
            raise ValueError(
                f"{context} contains unsupported "
                "presentation properties."
            )

        values = {}

        for field in (
            "shader",
            "overlay",
            "artwork",
        ):
            value = data.get(
                field,
                "",
            )

            if not isinstance(value, str):
                raise ValueError(
                    f"{context} {field} "
                    "must be a string."
                )

            values[field] = value

        return PresentationProfile(
            **values
        )

    @staticmethod
    def _profile_to_data(
        profile,
    ):
        if not isinstance(
            profile,
            PresentationProfile,
        ):
            raise ValueError(
                "Presentation assignments must "
                "use PresentationProfile."
            )

        return {
            "shader": profile.shader,
            "overlay": profile.overlay,
            "artwork": profile.artwork,
        }

    @classmethod
    def _mapping_from_data(
        cls,
        data,
        context,
    ):
        if not isinstance(data, dict):
            raise ValueError(
                f"{context} must contain "
                "a JSON object."
            )

        result = {}

        for identity, profile_data in (
            data.items()
        ):
            if not isinstance(identity, str):
                raise ValueError(
                    f"{context} identities "
                    "must be strings."
                )

            if not identity:
                raise ValueError(
                    f"{context} identities "
                    "cannot be empty."
                )

            result[identity] = (
                cls._profile_from_data(
                    profile_data,
                    (
                        f"{context} assignment "
                        f"{identity!r}"
                    ),
                )
            )

        return result

    @classmethod
    def _mapping_to_data(
        cls,
        assignments,
    ):
        if not isinstance(
            assignments,
            dict,
        ):
            raise ValueError(
                "Presentation assignments "
                "must be mappings."
            )

        result = {}

        for identity, profile in (
            assignments.items()
        ):
            if not isinstance(identity, str):
                raise ValueError(
                    "Presentation assignment "
                    "identities must be strings."
                )

            if not identity:
                raise ValueError(
                    "Presentation assignment "
                    "identities cannot be empty."
                )

            result[identity] = (
                cls._profile_to_data(
                    profile
                )
            )

        return result

    def _empty_data(self):
        return {
            "version": self.VERSION,
            "default": PresentationProfile(),
            "systems": {},
            "games": {},
        }

    def load(self):
        if not self.presentation_file.is_file():
            return self._empty_data()

        try:
            data = json.loads(
                self.presentation_file.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid RetroVault presentation "
                f"state: {self.presentation_file}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "RetroVault presentation state "
                "must contain a JSON object."
            )

        allowed = {
            "version",
            "default",
            "systems",
            "games",
            "legacy_games",
            "visual_tuning",
        }

        unknown = (
            set(data)
            - allowed
        )

        if unknown:
            raise ValueError(
                "RetroVault presentation state "
                "contains unsupported fields."
            )

        if type(data.get("version")) is not int or data.get("version") not in (1, 2, self.VERSION):
            raise ValueError(
                "Unsupported RetroVault "
                "presentation state version."
            )

        if "default" not in data:
            raise ValueError(
                "RetroVault presentation state "
                "must contain default."
            )

        if "systems" not in data:
            raise ValueError(
                "RetroVault presentation state "
                "must contain systems."
            )

        if "games" not in data:
            raise ValueError(
                "RetroVault presentation state "
                "must contain games."
            )

        result = {
            "version": self.VERSION,
            "default": self._profile_from_data(
                data["default"],
                "Presentation default",
            ),
            "systems": self._mapping_from_data(
                data["systems"],
                "Presentation systems",
            ),
            "games": self._mapping_from_data(
                data["games"],
                "Presentation games",
            ),
        }

        if "legacy_games" in data:
            result["legacy_games"] = self._mapping_from_data(data["legacy_games"], "Legacy game conflicts")
        if "visual_tuning" in data:
            from .visual_tuning import validate_state
            result["visual_tuning"] = validate_state(data["visual_tuning"])
        return result

    def save(
        self,
        *,
        default=None,
        systems=None,
        games=None,
        legacy_games=None,
        visual_tuning=None,
    ):
        default_profile = (
            default
            if default is not None
            else PresentationProfile()
        )

        payload_data = {
            "version": self.VERSION,
            "default": self._profile_to_data(
                default_profile
            ),
            "systems": self._mapping_to_data(
                systems or {}
            ),
            "games": self._mapping_to_data(
                games or {}
            ),
        }

        if legacy_games is None and self.presentation_file.exists():
            legacy_games = self.load().get("legacy_games", {})
        if legacy_games:
            payload_data["legacy_games"] = self._mapping_to_data(legacy_games)

        if visual_tuning is None and self.presentation_file.exists():
            visual_tuning = self.load().get("visual_tuning")
        if visual_tuning is not None:
            from .visual_tuning import validate_state
            payload_data["visual_tuning"] = validate_state(visual_tuning)

        self.presentation_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary = (
            self.presentation_file.parent
            / (
                self.presentation_file.name
                + ".tmp"
            )
        )

        payload = json.dumps(
            payload_data,
            indent=2,
            sort_keys=True,
        ) + "\n"

        try:
            with temporary.open(
                "w",
                encoding="utf-8",
            ) as handle:
                handle.write(
                    payload
                )
                handle.flush()
                os.fsync(
                    handle.fileno()
                )

            os.replace(
                temporary,
                self.presentation_file,
            )
        finally:
            if temporary.exists():
                temporary.unlink()

    @staticmethod
    def _shader_value(
        shader,
    ):
        if not isinstance(shader, str):
            raise ValueError(
                "Presentation shader must be a string."
            )

        return shader

    @staticmethod
    def _overlay_value(
        overlay,
    ):
        if not isinstance(overlay, str):
            raise ValueError(
                "Presentation overlay must be a string."
            )

        return overlay

    def assign_default_shader(
        self,
        shader,
    ):
        shader = self._shader_value(
            shader
        )

        data = self.load()

        self.save(
            default=replace(
                data["default"],
                shader=shader,
            ),
            systems=data["systems"],
            games=data["games"],
        )

    def assign_default_overlay(
        self,
        overlay,
    ):
        overlay = self._overlay_value(
            overlay
        )

        data = self.load()

        self.save(
            default=replace(
                data["default"],
                overlay=overlay,
            ),
            systems=data["systems"],
            games=data["games"],
        )

    def assign_system_shader(
        self,
        platform_id,
        shader,
    ):
        if (
            not isinstance(platform_id, str)
            or not platform_id
        ):
            raise ValueError(
                "Presentation system identity "
                "must be a non-empty string."
            )

        shader = self._shader_value(
            shader
        )

        data = self.load()

        systems = dict(
            data["systems"]
        )

        current = systems.get(
            platform_id,
            PresentationProfile(),
        )

        systems[platform_id] = replace(
            current,
            shader=shader,
        )

        self.save(
            default=data["default"],
            systems=systems,
            games=data["games"],
        )

    def assign_system_overlay(
        self,
        platform_id,
        overlay,
    ):
        if (
            not isinstance(platform_id, str)
            or not platform_id
        ):
            raise ValueError(
                "Presentation system identity "
                "must be a non-empty string."
            )

        overlay = self._overlay_value(
            overlay
        )

        data = self.load()

        systems = dict(
            data["systems"]
        )

        current = systems.get(
            platform_id,
            PresentationProfile(),
        )

        systems[platform_id] = replace(
            current,
            overlay=overlay,
        )

        self.save(
            default=data["default"],
            systems=systems,
            games=data["games"],
        )

    def assign_game_shader(
        self,
        identity,
        shader,
    ):
        if (
            not isinstance(identity, str)
            or not identity
        ):
            raise ValueError(
                "Presentation game identity "
                "must be a non-empty string."
            )

        shader = self._shader_value(
            shader
        )

        data = self.load()

        games = dict(
            data["games"]
        )

        current = games.get(
            identity,
            PresentationProfile(),
        )

        games[identity] = replace(
            current,
            shader=shader,
        )

        self.save(
            default=data["default"],
            systems=data["systems"],
            games=games,
        )

    def assign_game_overlay(
        self,
        identity,
        overlay,
    ):
        if (
            not isinstance(identity, str)
            or not identity
        ):
            raise ValueError(
                "Presentation game identity "
                "must be a non-empty string."
            )

        overlay = self._overlay_value(
            overlay
        )

        data = self.load()

        games = dict(
            data["games"]
        )

        current = games.get(
            identity,
            PresentationProfile(),
        )

        games[identity] = replace(
            current,
            overlay=overlay,
        )

        self.save(
            default=data["default"],
            systems=data["systems"],
            games=games,
        )

    def clear_default_overlay(
        self,
    ):
        data = self.load()

        self.save(
            default=replace(
                data["default"],
                overlay="",
            ),
            systems=data["systems"],
            games=data["games"],
        )

    def clear_system_overlay(
        self,
        platform_id,
    ):
        if (
            not isinstance(platform_id, str)
            or not platform_id
        ):
            raise ValueError(
                "Presentation system identity "
                "must be a non-empty string."
            )

        data = self.load()
        systems = dict(
            data["systems"]
        )

        current = systems.get(
            platform_id
        )

        if current is None:
            return

        updated = replace(
            current,
            overlay="",
        )

        if (
            not updated.shader
            and not updated.overlay
            and not updated.artwork
        ):
            systems.pop(
                platform_id,
                None,
            )
        else:
            systems[platform_id] = updated

        self.save(
            default=data["default"],
            systems=systems,
            games=data["games"],
        )

    def clear_game_shader(
        self,
        game,
    ):
        if not isinstance(game, str):
            raise ValueError(
                "Presentation game identity must be a string."
            )

        if not game:
            raise ValueError(
                "Presentation game identity cannot be empty."
            )

        data = self.load()

        profile = data["games"].get(
            game
        )

        if profile is None:
            return

        updated = replace(
            profile,
            shader="",
        )

        games = dict(
            data["games"]
        )

        if (
            updated.shader
            or updated.overlay
            or updated.artwork
        ):
            games[game] = updated
        else:
            games.pop(
                game,
                None,
            )

        self.save(
            default=data["default"],
            systems=data["systems"],
            games=games,
        )

    def clear_game_overlay(
        self,
        identity,
    ):
        if (
            not isinstance(identity, str)
            or not identity
        ):
            raise ValueError(
                "Presentation game identity "
                "must be a non-empty string."
            )

        data = self.load()
        games = dict(
            data["games"]
        )

        current = games.get(
            identity
        )

        if current is None:
            return

        updated = replace(
            current,
            overlay="",
        )

        if (
            not updated.shader
            and not updated.overlay
            and not updated.artwork
        ):
            games.pop(
                identity,
                None,
            )
        else:
            games[identity] = updated

        self.save(
            default=data["default"],
            systems=data["systems"],
            games=games,
        )

    def resolver(self):
        from .resolver import (
            PresentationResolver,
        )

        data = self.load()

        return PresentationResolver(
            default=data["default"],
            systems=data["systems"],
            games=data["games"],
        )

    def validate_identity_migration(self):
        self.load()

    def migrate_identities(self, mapping):
        from services.library.identity_migration import backup_original
        data = self.load()
        games = dict(data["games"])
        legacy = dict(data.get("legacy_games", {}))
        for old, new in mapping.items():
            if old not in games or old == new:
                continue
            if new not in games:
                games[new] = games.pop(old)
            elif games[new] == games[old]:
                del games[old]
            else:
                # Quarantine conflicts so clearing the new assignment cannot
                # resurrect an old one on the next migration pass.
                legacy[old] = games.pop(old)
        if self.presentation_file.exists():
            raw = json.loads(self.presentation_file.read_text(encoding="utf-8"))
            if games != data["games"] or raw.get("version") != self.VERSION:
                backup_original(self.presentation_file)
                self.save(default=data["default"], systems=data["systems"], games=games, legacy_games=legacy)

    def set_visual_tuning(self, scope, identity, platform_id, values):
        from .visual_tuning import validate_values, validate_state
        from copy import deepcopy
        data = self.load()
        tuning = deepcopy(data.get('visual_tuning', {'systems': {}, 'games': {}}))
        if scope not in ('systems', 'games'):
            raise ValueError('CRT scope must be systems or games.')
        values = validate_values(platform_id, values)
        if scope == 'systems' and identity != platform_id:
            raise ValueError('CRT system identity must match its platform.')
        if values:
            tuning[scope][identity] = (values if scope == 'systems' else
                                      dict(platform_id=platform_id, values=values))
        else:
            tuning[scope].pop(identity, None)
        validate_state(tuning)
        self.save(default=data['default'], systems=data['systems'], games=data['games'],
                  legacy_games=data.get('legacy_games'), visual_tuning=tuning)
