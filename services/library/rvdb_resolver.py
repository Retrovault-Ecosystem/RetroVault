from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from services.rvdb import RVDBConsumer


class RVDBLibraryResolver:
    """
    Resolve Library-facing platform knowledge through RVDB.

    This class deliberately does not scan ROM directories and does
    not choose arbitrary answers for ambiguous file extensions.

    It provides a narrow integration boundary between the existing
    Library scanner and canonical RVDB knowledge.
    """

    def __init__(
        self,
        consumer: RVDBConsumer,
    ) -> None:
        self.consumer = consumer

        self._platforms = sorted(
            (
                entity
                for entity in consumer.nodes.values()
                if entity.get("type") == "platform"
            ),
            key=lambda entity: (
                str(
                    entity.get(
                        "name",
                        "",
                    )
                ).casefold(),
                entity["id"],
            ),
        )

        self._extension_map: dict[
            str,
            list[dict[str, Any]],
        ] = defaultdict(list)

        self._name_map: dict[
            str,
            list[dict[str, Any]],
        ] = defaultdict(list)

        self._build_indexes()

    @classmethod
    def from_bundle(
        cls,
        bundle_path: str | Path,
    ) -> "RVDBLibraryResolver":
        return cls(
            RVDBConsumer(
                bundle_path
            )
        )

    @staticmethod
    def _normalize_extension(
        extension: str,
    ) -> str:
        return str(
            extension
        ).strip().casefold().lstrip(".")

    @staticmethod
    def _normalize_name(
        value: str,
    ) -> str:
        return " ".join(
            str(value)
            .strip()
            .casefold()
            .split()
        )

    def _build_indexes(self) -> None:
        for platform in self._platforms:
            for extension in (
                platform.get("extensions")
                or []
            ):
                key = self._normalize_extension(
                    extension
                )

                if key:
                    self._extension_map[
                        key
                    ].append(
                        platform
                    )

            names = [
                platform.get("name"),
                *(
                    platform.get("aliases")
                    or []
                ),
            ]

            for name in names:
                if not name:
                    continue

                key = self._normalize_name(
                    name
                )

                if key:
                    self._name_map[
                        key
                    ].append(
                        platform
                    )

    def platforms_for_extension(
        self,
        extension: str,
    ) -> list[dict[str, Any]]:
        key = self._normalize_extension(
            extension
        )

        return list(
            self._extension_map.get(
                key,
                []
            )
        )

    def platform_for_extension(
        self,
        extension: str,
    ) -> dict[str, Any] | None:
        """
        Return a platform only when the extension identifies exactly
        one RVDB platform.

        Ambiguous extensions intentionally return None.
        """

        matches = (
            self.platforms_for_extension(
                extension
            )
        )

        if len(matches) != 1:
            return None

        return matches[0]

    def platforms_for_name(
        self,
        name: str,
    ) -> list[dict[str, Any]]:
        key = self._normalize_name(
            name
        )

        return list(
            self._name_map.get(
                key,
                []
            )
        )

    def platform_for_name(
        self,
        name: str,
    ) -> dict[str, Any] | None:
        matches = self.platforms_for_name(
            name
        )

        if len(matches) != 1:
            return None

        return matches[0]

    def supported_cores(
        self,
        platform_id: str,
    ) -> list[dict[str, Any]]:
        return self.consumer.supported_cores(
            platform_id
        )

    def preferred_core(
        self,
        platform_id: str,
    ) -> dict[str, Any] | None:
        """
        Return a core only when RVDB currently provides exactly one
        supported core.

        Multiple supported cores are policy choices, not knowledge
        ambiguities, so this resolver refuses to choose between them.
        """

        cores = self.supported_cores(
            platform_id
        )

        if len(cores) != 1:
            return None

        return cores[0]
