from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from services.rvdb import RVDBService
from services.rvdb.models import (
    RVDBEntityRef,
    RVDBGameSummary,
    RVDBPlatformSummary,
)


class RVDBLibraryResolver:
    """
    Resolve Library-facing platform knowledge through RVDB.

    This class deliberately does not scan ROM directories and does
    not choose arbitrary answers for ambiguous file extensions.

    It provides a narrow integration boundary between the existing
    Library scanner and the typed RetroVault RVDB service.
    """

    def __init__(
        self,
        service: RVDBService,
    ) -> None:
        self.service = service

        self._platforms = sorted(
            service.platforms(),
            key=lambda platform: (
                platform.name.casefold(),
                platform.id,
            ),
        )

        self._games = sorted(
            service.games(),
            key=lambda game: (
                game.name.casefold(),
                game.id,
            ),
        )

        self._extension_map: dict[
            str,
            list[RVDBPlatformSummary],
        ] = defaultdict(list)

        self._name_map: dict[
            str,
            list[RVDBPlatformSummary],
        ] = defaultdict(list)

        self._game_name_map: dict[
            str,
            list[RVDBGameSummary],
        ] = defaultdict(list)

        self._build_indexes()

    @classmethod
    def from_bundle(
        cls,
        bundle_path: str | Path,
    ) -> "RVDBLibraryResolver":
        return cls(
            RVDBService.from_bundle(
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
            for extension in platform.extensions:
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
                platform.name,
                *platform.aliases,
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

        for game in self._games:
            names = [
                game.name,
                *game.aliases,
            ]

            for name in names:
                if not name:
                    continue

                key = self._normalize_name(
                    name
                )

                if key:
                    self._game_name_map[
                        key
                    ].append(
                        game
                    )

    def platforms_for_extension(
        self,
        extension: str,
    ) -> list[RVDBPlatformSummary]:
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
    ) -> RVDBPlatformSummary | None:
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
    ) -> list[RVDBPlatformSummary]:
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
    ) -> RVDBPlatformSummary | None:
        matches = self.platforms_for_name(
            name
        )

        if len(matches) != 1:
            return None

        return matches[0]

    def games_for_name(
        self,
        name: str,
        platform_id: str,
    ) -> list[RVDBGameSummary]:
        """
        Return canonical RVDB Games matching an exact normalized
        title or alias on one canonical Platform.

        Platform identity is mandatory so cross-platform title
        collisions never become implicit application policy.
        """

        if not platform_id:
            return []

        key = self._normalize_name(
            name
        )

        matches = self._game_name_map.get(
            key,
            [],
        )

        return [
            game
            for game in matches
            if platform_id in game.platforms
        ]

    def game_for_name(
        self,
        name: str,
        platform_id: str,
    ) -> RVDBGameSummary | None:
        """
        Resolve a canonical RVDB Game only when normalized
        title/alias plus Platform identifies exactly one result.

        Missing and ambiguous matches intentionally return None.
        """

        matches = self.games_for_name(
            name,
            platform_id,
        )

        if len(matches) != 1:
            return None

        return matches[0]

    def supported_cores(
        self,
        platform_id: str,
    ) -> list[RVDBEntityRef]:
        view = self.service.platform_view(
            platform_id
        )

        if view is None:
            return []

        return list(
            view.cores
        )

    def preferred_core(
        self,
        platform_id: str,
    ) -> RVDBEntityRef | None:
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
