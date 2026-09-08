from dataclasses import dataclass
from enum import Enum


class VisualAssetType(str, Enum):
    """Presentation asset categories understood by RVV."""

    SHADER = "shader"
    OVERLAY = "overlay"
    ARTWORK = "artwork"


class VisualAssetSource(str, Enum):
    """Ownership/origin classification for visual assets."""

    RVV_NATIVE = "rvv_native"
    RETROARCH = "retroarch"
    THIRD_PARTY = "third_party"
    USER = "user"


@dataclass(frozen=True)
class VisualAsset:
    """
    Curated RVV metadata for one presentation asset.

    This model deliberately describes the visual independently
    of ShaderPreset and Overlay filesystem-discovery models.
    """

    id: str
    display_name: str
    asset_type: VisualAssetType
    source: VisualAssetSource
    reference: str
    author: str = ""
    attribution: str = ""

    def __post_init__(self):
        for field_name in (
            "id",
            "display_name",
            "reference",
        ):
            value = getattr(
                self,
                field_name,
            )

            if not isinstance(value, str):
                raise TypeError(
                    f"{field_name} must be a string."
                )

            if not value.strip():
                raise ValueError(
                    f"{field_name} must not be empty."
                )

        if not isinstance(
            self.asset_type,
            VisualAssetType,
        ):
            raise TypeError(
                "asset_type must be a VisualAssetType."
            )

        if not isinstance(
            self.source,
            VisualAssetSource,
        ):
            raise TypeError(
                "source must be a VisualAssetSource."
            )

        for field_name in (
            "author",
            "attribution",
        ):
            if not isinstance(
                getattr(self, field_name),
                str,
            ):
                raise TypeError(
                    f"{field_name} must be a string."
                )


class VisualAssetCatalog:
    """
    Exact-identity catalog for curated RVV visual metadata.

    The catalog does not scan files, infer ownership, perform
    fuzzy matching, or alter presentation precedence.
    """

    def __init__(
        self,
        assets=(),
    ):
        by_id = {}

        for asset in assets:
            if not isinstance(
                asset,
                VisualAsset,
            ):
                raise TypeError(
                    "Catalog entries must be VisualAsset objects."
                )

            if asset.id in by_id:
                raise ValueError(
                    f"Duplicate visual asset ID: {asset.id}"
                )

            by_id[asset.id] = asset

        self._by_id = by_id

    def all(self):
        return tuple(
            self._by_id.values()
        )

    def get(
        self,
        asset_id,
    ):
        return self._by_id.get(
            asset_id
        )

    def require(
        self,
        asset_id,
    ):
        asset = self.get(
            asset_id
        )

        if asset is None:
            raise KeyError(
                asset_id
            )

        return asset

    def for_type(
        self,
        asset_type,
    ):
        if not isinstance(
            asset_type,
            VisualAssetType,
        ):
            raise TypeError(
                "asset_type must be a VisualAssetType."
            )

        return tuple(
            asset
            for asset in self._by_id.values()
            if asset.asset_type is asset_type
        )

    def for_source(
        self,
        source,
    ):
        if not isinstance(
            source,
            VisualAssetSource,
        ):
            raise TypeError(
                "source must be a VisualAssetSource."
            )

        return tuple(
            asset
            for asset in self._by_id.values()
            if asset.source is source
        )
