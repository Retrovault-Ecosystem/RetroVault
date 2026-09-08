import json
from pathlib import Path

from .visual_catalog import (
    VisualAsset,
    VisualAssetCatalog,
    VisualAssetSource,
    VisualAssetType,
)


DEFAULT_VISUAL_CATALOG_MANIFEST = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "presentation"
    / "visual_catalog.json"
)


class VisualAssetCatalogManifest:
    """
    Load RetroVault curated visual-asset metadata.

    The manifest is read-only application data. It describes
    presentation assets independently from filesystem discovery.
    Portable asset references are preserved as authored.
    """

    VERSION = 1

    def __init__(
        self,
        manifest_file=None,
    ):
        self.manifest_file = Path(
            manifest_file
            or DEFAULT_VISUAL_CATALOG_MANIFEST
        ).expanduser()

    @staticmethod
    def _asset_from_data(
        data,
        context,
    ) -> VisualAsset:
        if not isinstance(data, dict):
            raise ValueError(
                f"{context} must contain a JSON object."
            )

        allowed = {
            "id",
            "display_name",
            "asset_type",
            "source",
            "reference",
            "author",
            "attribution",
        }

        unknown = set(data) - allowed

        if unknown:
            raise ValueError(
                f"{context} contains unsupported fields."
            )

        required = {
            "id",
            "display_name",
            "asset_type",
            "source",
            "reference",
        }

        missing = required - set(data)

        if missing:
            raise ValueError(
                f"{context} is missing required fields."
            )

        for field in (
            "id",
            "display_name",
            "asset_type",
            "source",
            "reference",
            "author",
            "attribution",
        ):
            if field not in data:
                continue

            if not isinstance(
                data[field],
                str,
            ):
                raise ValueError(
                    f"{context} {field} must be a string."
                )

        try:
            asset_type = VisualAssetType(
                data["asset_type"]
            )
        except ValueError as exc:
            raise ValueError(
                f"{context} contains an unsupported "
                "asset type."
            ) from exc

        try:
            source = VisualAssetSource(
                data["source"]
            )
        except ValueError as exc:
            raise ValueError(
                f"{context} contains an unsupported "
                "asset source."
            ) from exc

        try:
            return VisualAsset(
                id=data["id"],
                display_name=data["display_name"],
                asset_type=asset_type,
                source=source,
                reference=data["reference"],
                author=data.get(
                    "author",
                    "",
                ),
                attribution=data.get(
                    "attribution",
                    "",
                ),
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                f"{context} contains invalid "
                "visual asset metadata."
            ) from exc

    def load(
        self,
    ) -> VisualAssetCatalog:
        if not self.manifest_file.is_file():
            raise ValueError(
                "RetroVault visual catalog manifest "
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
                "Invalid RetroVault visual catalog "
                "manifest: "
                f"{self.manifest_file}"
            ) from exc

        if not isinstance(data, dict):
            raise ValueError(
                "RetroVault visual catalog manifest "
                "must contain a JSON object."
            )

        allowed = {
            "version",
            "assets",
        }

        unknown = set(data) - allowed

        if unknown:
            raise ValueError(
                "RetroVault visual catalog manifest "
                "contains unsupported fields."
            )

        if data.get("version") != self.VERSION:
            raise ValueError(
                "Unsupported RetroVault visual "
                "catalog manifest version."
            )

        if "assets" not in data:
            raise ValueError(
                "RetroVault visual catalog manifest "
                "must contain assets."
            )

        assets = data["assets"]

        if not isinstance(assets, list):
            raise ValueError(
                "RetroVault visual catalog assets "
                "must contain a JSON array."
            )

        loaded = []

        for index, asset_data in enumerate(
            assets
        ):
            loaded.append(
                self._asset_from_data(
                    asset_data,
                    (
                        "RetroVault visual catalog "
                        f"asset #{index + 1}"
                    ),
                )
            )

        try:
            return VisualAssetCatalog(
                loaded
            )
        except (
            TypeError,
            ValueError,
        ) as exc:
            raise ValueError(
                "RetroVault visual catalog manifest "
                "contains invalid catalog data."
            ) from exc
