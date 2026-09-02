from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable, Mapping

from services.rvdb.consumer import RVDBConsumer
from services.rvdb.models import (
    RVDBEntityRef,
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

        platform = RVDBEntityRef.from_entity(
            raw_view["platform"]
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
