from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True, slots=True)
class RVDBEntityRef:
    """
    Stable RetroVault-facing identity for one RVDB entity.

    Application layers should prefer this model over depending directly
    on the portable RVDB bundle dictionary layout.
    """

    id: str
    entity_type: str
    name: str

    @classmethod
    def from_entity(
        cls,
        entity: Mapping[str, Any],
    ) -> "RVDBEntityRef":
        return cls(
            id=str(
                entity["id"]
            ),
            entity_type=str(
                entity["type"]
            ),
            name=str(
                entity.get(
                    "name",
                    entity["id"],
                )
            ),
        )


@dataclass(frozen=True, slots=True)
class RVDBPlatformSummary:
    """
    Stable RetroVault-facing summary for one Platform.

    This model contains the Platform fields required to populate and
    filter the Systems page without exposing raw RVDB bundle nodes.
    """

    id: str
    name: str
    aliases: tuple[str, ...]
    categories: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class RVDBPlatformMetadata:
    """
    RetroVault-owned Platform metadata used by the Systems page.
    """

    id: str
    name: str
    aliases: tuple[str, ...]
    categories: tuple[str, ...]
    manufacturers: tuple[RVDBEntityRef, ...]
    release_year: Any
    generation: Any
    media: tuple[str, ...]
    extensions: tuple[str, ...]
    retroarch_supported: bool | None


@dataclass(frozen=True, slots=True)
class RVDBPlatformView:
    """
    RetroVault-owned read model for one emulation Platform.

    Relationship cardinality is intentionally preserved:

    - one Platform may support multiple Cores
    - one Platform may have multiple standalone Emulators
    - multiple Cores may resolve to the same Frontend
    """

    platform: RVDBPlatformMetadata
    cores: tuple[RVDBEntityRef, ...]
    emulators: tuple[RVDBEntityRef, ...]
    frontends: tuple[RVDBEntityRef, ...]
