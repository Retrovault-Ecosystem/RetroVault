import json
from pathlib import Path

from .models import PresentationProfile
from .recommendations import (
    PresentationRecommendationCatalog,
)


DEFAULT_RECOMMENDATION_MANIFEST = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "presentation"
    / "recommendations.json"
)


class PresentationRecommendationManifest:
    """
    Load RetroVault-owned curated presentation recommendations.

    The manifest is read-only application data.

    Platform identities are stable RVDB IDs. Presentation values are
    preserved as authored; path/reference resolution belongs to a
    later presentation asset-resolution boundary.
    """

    VERSION = 1

    def __init__(
        self,
        manifest_file=None,
    ):
        self.manifest_file = Path(
            manifest_file
            or DEFAULT_RECOMMENDATION_MANIFEST
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

        unknown = set(data) - allowed

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

    def load(
        self,
    ) -> PresentationRecommendationCatalog:
        if not self.manifest_file.is_file():
            raise ValueError(
                "RetroVault presentation "
                "recommendation manifest "
                "does not exist: "
                f"{self.manifest_file}"
            )

        try:
            data = json.loads(
                self.manifest_file.read_text(
                    encoding="utf-8"
                )
            )
        except json.JSONDecodeError as exc:
            raise ValueError(
                "Invalid RetroVault presentation "
                "recommendation manifest: "
                f"{self.manifest_file}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "RetroVault presentation "
                "recommendation manifest must "
                "contain a JSON object."
            )

        allowed = {
            "version",
            "systems",
        }

        unknown = set(data) - allowed

        if unknown:
            raise ValueError(
                "RetroVault presentation "
                "recommendation manifest contains "
                "unsupported fields."
            )

        if data.get("version") != self.VERSION:
            raise ValueError(
                "Unsupported RetroVault presentation "
                "recommendation manifest version."
            )

        if "systems" not in data:
            raise ValueError(
                "RetroVault presentation "
                "recommendation manifest must "
                "contain systems."
            )

        systems = data["systems"]

        if not isinstance(systems, dict):
            raise ValueError(
                "Presentation recommendation "
                "systems must contain "
                "a JSON object."
            )

        recommendations = {}

        for platform_id, profile_data in (
            systems.items()
        ):
            if not isinstance(
                platform_id,
                str,
            ):
                raise ValueError(
                    "Presentation recommendation "
                    "platform identities must "
                    "be strings."
                )

            if not platform_id.strip():
                raise ValueError(
                    "Presentation recommendation "
                    "platform identities cannot "
                    "be empty."
                )

            recommendations[platform_id] = (
                self._profile_from_data(
                    profile_data,
                    (
                        "Presentation recommendation "
                        f"{platform_id!r}"
                    ),
                )
            )

        return PresentationRecommendationCatalog(
            recommendations
        )
