import json
from pathlib import Path
from typing import Any


class RVDBError(Exception):
    """Raised when RetroVault cannot consume an RVDB bundle."""


class RVDBConsumer:
    """Read-only consumer for the portable RVDB JSON bundle."""

    def __init__(self, bundle_path: str | Path):
        self.bundle_path = Path(bundle_path)
        self._nodes: dict[str, dict[str, Any]] = {}
        self._edges: dict[str, dict[str, list[str]]] = {}

        self.reload()

    @property
    def nodes(self) -> dict[str, dict[str, Any]]:
        return self._nodes

    @property
    def edges(self) -> dict[str, dict[str, list[str]]]:
        return self._edges

    def reload(self) -> None:
        if not self.bundle_path.is_file():
            raise RVDBError(
                f"RVDB bundle not found: {self.bundle_path}"
            )

        try:
            data = json.loads(
                self.bundle_path.read_text(
                    encoding="utf-8"
                )
            )
        except (OSError, json.JSONDecodeError) as exc:
            raise RVDBError(
                f"Unable to read RVDB bundle: {self.bundle_path}"
            ) from exc

        if not isinstance(data, dict):
            raise RVDBError(
                "RVDB bundle root must be an object."
            )

        if set(data) != {"nodes", "edges"}:
            raise RVDBError(
                "RVDB bundle must contain exactly "
                "'nodes' and 'edges'."
            )

        nodes = data["nodes"]
        edges = data["edges"]

        if not isinstance(nodes, dict):
            raise RVDBError(
                "RVDB 'nodes' must be an object."
            )

        if not isinstance(edges, dict):
            raise RVDBError(
                "RVDB 'edges' must be an object."
            )

        self._nodes = nodes
        self._edges = edges

    def get_entity(
        self,
        entity_id: str,
    ) -> dict[str, Any] | None:
        return self._nodes.get(entity_id)

    def require_entity(
        self,
        entity_id: str,
    ) -> dict[str, Any]:
        entity = self.get_entity(entity_id)

        if entity is None:
            raise RVDBError(
                f"RVDB entity not found: {entity_id}"
            )

        return entity

    def relationship_targets(
        self,
        entity_id: str,
        relationship: str,
    ) -> list[str]:
        relationships = self._edges.get(
            entity_id,
            {},
        )

        targets = relationships.get(
            relationship,
            [],
        )

        return list(targets)

    def entities_pointing_to(
        self,
        target_id: str,
        relationship: str,
        *,
        entity_type: str | None = None,
    ) -> list[dict[str, Any]]:
        matches: list[dict[str, Any]] = []

        for entity_id, relationships in self._edges.items():
            targets = relationships.get(
                relationship,
                [],
            )

            if target_id not in targets:
                continue

            entity = self._nodes.get(
                entity_id
            )

            if entity is None:
                continue

            if (
                entity_type is not None
                and entity.get("type") != entity_type
            ):
                continue

            matches.append(entity)

        return matches

    def supported_cores(
        self,
        platform_id: str,
    ) -> list[dict[str, Any]]:
        core_ids = self.relationship_targets(
            platform_id,
            "supports_core",
        )

        cores: list[dict[str, Any]] = []

        for core_id in core_ids:
            core = self._nodes.get(
                core_id
            )

            if core is None:
                continue

            if core.get("type") != "core":
                continue

            cores.append(core)

        return cores

    def supported_emulators(
        self,
        platform_id: str,
    ) -> list[dict[str, Any]]:
        return self.entities_pointing_to(
            platform_id,
            "supports_platform",
            entity_type="emulator",
        )

    def frontends_for_core(
        self,
        core_id: str,
    ) -> list[dict[str, Any]]:
        return self.entities_pointing_to(
            core_id,
            "launches_core",
            entity_type="frontend",
        )

    def platform_view(
        self,
        platform_id: str,
    ) -> dict[str, Any]:
        platform = self.require_entity(
            platform_id
        )

        if platform.get("type") != "platform":
            raise RVDBError(
                f"Entity is not a platform: {platform_id}"
            )

        cores = self.supported_cores(
            platform_id
        )

        emulators = self.supported_emulators(
            platform_id
        )

        frontends: list[dict[str, Any]] = []
        seen_frontends: set[str] = set()

        for core in cores:
            for frontend in self.frontends_for_core(
                core["id"]
            ):
                frontend_id = frontend["id"]

                if frontend_id in seen_frontends:
                    continue

                seen_frontends.add(
                    frontend_id
                )

                frontends.append(
                    frontend
                )

        return {
            "platform": platform,
            "cores": cores,
            "emulators": emulators,
            "frontends": frontends,
        }
