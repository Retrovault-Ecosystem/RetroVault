"""Detached, cancellable Library preparation. Publication belongs to LibraryService."""
from copy import deepcopy
from dataclasses import dataclass
from threading import Event
from time import monotonic


class DiscoveryCancelled(Exception):
    """Cancellation before the publication boundary; nothing was committed."""


@dataclass(frozen=True)
class DiscoveryProgress:
    phase: str
    count: int


class DiscoveryControl:
    def __init__(self, progress=None):
        self._cancelled = Event()
        self.progress = progress or (lambda event: None)
        self._seen_phases = set()
        self._last_report = 0.0
        self.counts = {}

    def cancel(self):
        self._cancelled.set()

    def check(self):
        if self._cancelled.is_set():
            raise DiscoveryCancelled()

    def report(self, phase, count=None):
        self.check()
        count = self.counts.get(phase, 0) + 1 if count is None else count
        self.counts[phase] = count
        now = monotonic()
        # Bound queued UI events instead of emitting one event per file.
        if phase not in self._seen_phases or now - self._last_report >= .1:
            self.progress(DiscoveryProgress(phase, count))
            self._seen_phases.add(phase)
            self._last_report = now
        self.check()


def relevant_config(config):
    return deepcopy((config.get('library', {}).get('sources', []),
                     config.get('paths', {}).get('artwork', {}).get('directory', '')))


@dataclass(frozen=True)
class DiscoveryRequest:
    kind: str
    directory: str | None
    config: dict
    registry_data: dict
    physical: tuple
    resolver: object
    registry: object


@dataclass(frozen=True)
class PreparedLibrary:
    request: DiscoveryRequest
    physical: tuple
    visible: tuple
    registry_data: dict
    archive_cache: object
    discovered: object = None
    added_count: int = 0
    skipped_count: int = 0


def prepare_library(request, control):
    from services.library.source_manager import SourceManager
    from services.library.library_builder import LibraryBuilder
    from services.library.bulk_import import BulkImporter
    from services.artwork.service import ArtworkService
    from services.library.canonicalization import LibraryCanonicalizer
    from services.library.identity import game_identity, location_key

    control.report('Scanning', 0)
    builder = LibraryBuilder(rvdb_resolver=request.resolver)
    discovered = None
    if request.kind == 'import':
        discovered = BulkImporter(scanner=builder.scanner).import_directory(
            request.directory, control=control)
        incoming = list(discovered.games)
    else:
        incoming = builder.build(SourceManager(config=request.config).sources(), control=control)
    control.report('Preparing identities', 0)
    incoming, staged = request.registry.stage(
        incoming, control=control, original=request.registry_data)
    added, skipped = len(incoming), 0
    if request.kind == 'import':
        physical = list(request.physical)
        known = {game_identity(game) for game in physical}
        added = sum(game_identity(game) not in known for game in incoming)
        skipped = len(discovered.games) - added
        incoming_ids = {game_identity(game) for game in incoming}
        incoming_paths = {location_key(game.rom) for game in incoming}
        physical = [game for game in physical if game_identity(game) not in incoming_ids
                    and location_key(game.rom) not in incoming_paths] + incoming
    else:
        physical = incoming
    artwork = ArtworkService(directory=request.config.get('paths', {}).get('artwork', {}).get('directory', ''),
                             rvdb_resolver=request.resolver, control=control)
    control.report('Artwork', 0)
    for index, game in enumerate(physical):
        control.report('Artwork', index)
        game.artwork = artwork.get_artwork(game) or ''
    control.report('Preparing families', 0)
    visible = LibraryCanonicalizer().canonicalize(physical)
    control.check()
    return PreparedLibrary(request, tuple(physical), tuple(visible), staged,
                           builder.scanner.archive_scan_cache, discovered, added, skipped)
