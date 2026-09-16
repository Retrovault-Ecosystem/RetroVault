from dataclasses import dataclass
from pathlib import Path

from services.library.scanner import RomScanner
from services.library.source_manager import LibrarySource
from services.library.source_validator import SourceValidator


@dataclass(frozen=True)
class BulkImportResult:
    source: LibrarySource
    games: tuple
    discovered_count: int
    duplicate_count: int


class BulkImporter:
    """
    Discover a ROM library through RetroVault's existing scanner
    architecture without mutating runtime configuration or durable
    Library state.

    This service is the production boundary for bulk-import discovery.
    """

    def __init__(
        self,
        rvdb_resolver=None,
        scanner=None,
        validator=None,
    ):
        self.scanner = (
            scanner
            if scanner is not None
            else RomScanner(
                rvdb_resolver=rvdb_resolver
            )
        )

        self.validator = (
            validator
            if validator is not None
            else SourceValidator()
        )

    def import_directory(
        self,
        path,
        *,
        source_id="bulk-import",
        source_name="Bulk Import",
    ):
        source_path = (
            Path(path)
            .expanduser()
            .resolve(strict=False)
        )

        source = LibrarySource(
            id=str(source_id),
            name=str(source_name),
            enabled=True,
            type="local",
            path=str(source_path),
        )

        problems = self.validator.validate(
            source
        )

        if problems:
            raise ValueError(
                "Invalid bulk-import source: "
                + "; ".join(problems)
            )

        scanned = self.scanner.scan(
            source
        )

        games = []
        identities = set()
        duplicate_count = 0

        for game in scanned:
            rom = getattr(
                game,
                "rom",
                "",
            )

            if not rom:
                continue

            identity = str(
                Path(rom)
                .expanduser()
                .resolve(strict=False)
            )

            if identity in identities:
                duplicate_count += 1
                continue

            identities.add(
                identity
            )

            games.append(
                game
            )

        games.sort(
            key=lambda game: (
                str(
                    getattr(
                        game,
                        "platform",
                        "",
                    )
                ).casefold(),
                str(
                    getattr(
                        game,
                        "name",
                        "",
                    )
                ).casefold(),
                str(
                    getattr(
                        game,
                        "rom",
                        "",
                    )
                ).casefold(),
            )
        )

        return BulkImportResult(
            source=source,
            games=tuple(games),
            discovered_count=len(games),
            duplicate_count=duplicate_count,
        )
