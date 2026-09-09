import re
from collections.abc import Iterable

from .visual_catalog import (
    VisualAsset,
    VisualAssetSource,
    VisualAssetType,
)


class VisualAssetDiscovery:
    """
    Query an existing collection of RetroVault visual assets.

    The discovery layer does not own, load, scan, modify, or
    persist the visual catalog.

    Free-text discovery operates only on user-facing metadata.
    Portable asset references are intentionally excluded because
    their URI scheme is application plumbing rather than useful
    visual identity.
    """

    def __init__(
        self,
        assets,
    ):
        if isinstance(
            assets,
            (str, bytes),
        ):
            raise TypeError(
                "Visual discovery assets must be "
                "an iterable of VisualAsset objects."
            )

        if not isinstance(
            assets,
            Iterable,
        ):
            raise TypeError(
                "Visual discovery assets must be "
                "an iterable of VisualAsset objects."
            )

        validated = []

        for asset in assets:
            if not isinstance(
                asset,
                VisualAsset,
            ):
                raise TypeError(
                    "Visual discovery entries must "
                    "be VisualAsset objects."
                )

            validated.append(
                asset
            )

        self.assets = tuple(
            validated
        )

    @staticmethod
    def _normalize_query(
        query,
    ):
        if query is None:
            return ""

        if not isinstance(
            query,
            str,
        ):
            raise TypeError(
                "Visual discovery query must be a string."
            )

        return " ".join(
            query.casefold().split()
        )

    @staticmethod
    def _validate_source(
        source,
    ):
        if (
            source is not None
            and not isinstance(
                source,
                VisualAssetSource,
            )
        ):
            raise TypeError(
                "Visual discovery source filter must "
                "be a VisualAssetSource."
            )

        return source

    @staticmethod
    def _validate_type(
        asset_type,
    ):
        if (
            asset_type is not None
            and not isinstance(
                asset_type,
                VisualAssetType,
            )
        ):
            raise TypeError(
                "Visual discovery type filter must "
                "be a VisualAssetType."
            )

        return asset_type

    @staticmethod
    def _tokenize(
        text,
    ):
        return tuple(
            token
            for token in re.findall(
                r"[a-z0-9]+",
                text.casefold(),
            )
            if token
        )

    @classmethod
    def _search_tokens(
        cls,
        asset,
    ):
        searchable = " ".join(
            (
                asset.id,
                asset.display_name,
                asset.author,
                asset.attribution,
                asset.source.value,
                asset.asset_type.value,
            )
        )

        return cls._tokenize(
            searchable
        )

    @staticmethod
    def _term_matches(
        term,
        tokens,
    ):
        """
        Match from the beginning of a metadata token.

        Prefix matching supports incremental search while
        preventing an otherwise valid term from matching only
        because it appears inside a longer metadata token.
        """

        return any(
            token.startswith(
                term
            )
            for token in tokens
        )

    def query(
        self,
        *,
        text="",
        source=None,
        asset_type=None,
    ):
        normalized = (
            self._normalize_query(
                text
            )
        )

        source = self._validate_source(
            source
        )

        asset_type = self._validate_type(
            asset_type
        )

        terms = self._tokenize(
            normalized
        )

        results = []

        for asset in self.assets:
            if (
                source is not None
                and asset.source is not source
            ):
                continue

            if (
                asset_type is not None
                and asset.asset_type is not asset_type
            ):
                continue

            if terms:
                tokens = (
                    self._search_tokens(
                        asset
                    )
                )

                if not all(
                    self._term_matches(
                        term,
                        tokens,
                    )
                    for term in terms
                ):
                    continue

            results.append(
                asset
            )

        return tuple(
            sorted(
                results,
                key=lambda asset: (
                    asset.display_name.casefold(),
                    asset.id.casefold(),
                ),
            )
        )

    def all(self):
        return self.query()

    def search(
        self,
        text,
    ):
        return self.query(
            text=text
        )

    def for_source(
        self,
        source,
    ):
        return self.query(
            source=source
        )

    def for_type(
        self,
        asset_type,
    ):
        return self.query(
            asset_type=asset_type
        )
