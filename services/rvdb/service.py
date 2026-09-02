from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from services.rvdb.consumer import RVDBConsumer
from services.rvdb.models import (
    RVDBEntityRef,
    RVDBPlatformMetadata,
    RVDBPlatformSummary,
    RVDBPlatformView,
)


class RVDBService:
    """
    Application-owned boundary over the low-level RVDB consumer.

    RVDBConsumer owns portable-bundle mechanics.

    RVDBService owns the shape presented to the rest of RetroVault.

    UI, controllers, and higher-level application services should
    eventually depend on this boundary instead of directly inspecting
    RVDB bundle nodes or edges.
    """

    def __init__(
        self,
        consumer: RVDBConsumer,
    ) -> None:
        self._consumer = consumer

    @classmethod
    def from_bundle(
        cls,
        bundle_path: str | Path,
    ) -> "RVDBService":
        return cls(
            RVDBConsumer(
                bundle_path
            )
        )

    @property
    def consumer(
        self,
    ) -> RVDBConsumer:
        """
        Expose the underlying consumer for lower-level integration only.

        New application-facing code should prefer RVDBService methods.
        """
        return self._consumer

    @staticmethod
    def _values(
        value: Any,
    ) -> tuple[str, ...]:
        if value is None:
            return ()

        if isinstance(
            value,
            str,
        ):
            return (
                value,
            )

        if isinstance(
            value,
            Iterable,
        ):
            return tuple(
                str(item)
                for item in value
                if item not in (
                    None,
                    "",
                )
            )

        return (
            str(value),
        )

    @staticmethod
    def _refs(
        entities: Iterable[
            Mapping[str, Any]
        ],
    ) -> tuple[RVDBEntityRef, ...]:
        refs = [
            RVDBEntityRef.from_entity(
                entity
            )
            for entity in entities
        ]

        refs.sort(
            key=lambda ref: (
                ref.name.casefold(),
                ref.id,
            )
        )

        return tuple(
            refs
        )

    def _entity_refs(
        self,
        entity_ids: Any,
    ) -> tuple[RVDBEntityRef, ...]:
        refs = []

        for entity_id in self._values(
            entity_ids
        ):
            entity = self._consumer.get_entity(
                entity_id
            )

            if entity is None:
                refs.append(
                    RVDBEntityRef(
                        id=entity_id,
                        entity_type="unknown",
                        name=entity_id,
                    )
                )
                continue

            refs.append(
                RVDBEntityRef.from_entity(
                    entity
                )
            )

        refs.sort(
            key=lambda ref: (
                ref.name.casefold(),
                ref.id,
            )
        )

        return tuple(
            refs
        )

    def platforms(
        self,
    ) -> tuple[RVDBPlatformSummary, ...]:
        """
        Return all Platforms required for Systems-page discovery.

        Raw bundle node dictionaries do not escape this boundary.
        """

        platforms = []

        for entity in self._consumer.nodes.values():
            if entity.get("type") != "platform":
                continue

            platforms.append(
                RVDBPlatformSummary(
                    id=str(
                        entity["id"]
                    ),
                    name=str(
                        entity.get(
                            "name",
                            entity["id"],
                        )
                    ),
                    aliases=self._values(
                        entity.get(
                            "aliases"
                        )
                    ),
                    categories=self._values(
                        entity.get(
                            "category"
                        )
                    ),
                )
            )

        platforms.sort(
            key=lambda platform: (
                platform.name.casefold(),
                platform.id,
            )
        )

        return tuple(
            platforms
        )

    def platform_view(
        self,
        platform_id: str,
    ) -> RVDBPlatformView:
        """
        Return the stable RetroVault read model for one Platform.

        No emulator, Core, or Frontend preference is invented here.
        All RVDB-supported alternatives are preserved.
        """

        raw_view = self._consumer.platform_view(
            platform_id
        )

        raw_platform = raw_view[
            "platform"
        ]

        metadata = raw_platform.get(
            "metadata",
            {}
        )

        if not isinstance(
            metadata,
            Mapping,
        ):
            metadata = {}

        platform = RVDBPlatformMetadata(
            id=str(
                raw_platform["id"]
            ),
            name=str(
                raw_platform.get(
                    "name",
                    raw_platform["id"],
                )
            ),
            aliases=self._values(
                raw_platform.get(
                    "aliases"
                )
            ),
            categories=self._values(
                raw_platform.get(
                    "category"
                )
            ),
            manufacturers=self._entity_refs(
                raw_platform.get(
                    "manufacturer"
                )
            ),
            release_year=raw_platform.get(
                "release_year"
            ),
            generation=raw_platform.get(
                "generation"
            ),
            media=self._values(
                raw_platform.get(
                    "media"
                )
            ),
            extensions=self._values(
                raw_platform.get(
                    "extensions"
                )
            ),
            retroarch_supported=metadata.get(
                "retroarch_supported"
            ),
        )

        cores = self._refs(
            raw_view["cores"]
        )

        emulators = self._refs(
            raw_view["emulators"]
        )

        frontends = self._refs(
            raw_view["frontends"]
        )

        return RVDBPlatformView(
            platform=platform,
            cores=cores,
            emulators=emulators,
            frontends=frontends,
        )
