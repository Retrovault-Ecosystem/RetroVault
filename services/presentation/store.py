import json
import os
from pathlib import Path

from .models import PresentationProfile


def _default_presentation_file() -> Path:
    xdg_config_home = os.environ.get(
        "XDG_CONFIG_HOME"
    )

    if xdg_config_home:
        config_home = Path(
            xdg_config_home
        ).expanduser()
    else:
        config_home = (
            Path.home()
            / ".config"
        )

    return (
        config_home
        / "retrovault"
        / "presentation-state.json"
    )


class PresentationStore:
    VERSION = 1

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

        if data.get("version") != self.VERSION:
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

        return {
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

    def save(
        self,
        *,
        default=None,
        systems=None,
        games=None,
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
