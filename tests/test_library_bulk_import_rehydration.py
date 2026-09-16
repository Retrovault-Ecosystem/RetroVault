from pathlib import Path

from config import ConfigLoader, ConfigWriter
from services.library.import_sources import (
    ImportSourceStore,
)
from services.library.library_service import (
    LibraryService,
)
from services.library.source_manager import (
    SourceManager,
)


class RecordingBuilder:
    def __init__(self):
        self.sources = None

    def build(self, sources):
        self.sources = tuple(sources)
        return []


def _write_defaults(path):
    path.write_text(
        """
library:
  sources: []
paths:
  artwork:
    directory: ""
""".lstrip(),
        encoding="utf-8",
    )


def test_persisted_bulk_import_source_rehydrates_after_restart(
    tmp_path,
):
    defaults = tmp_path / "defaults.yaml"
    runtime = tmp_path / "runtime.json"
    roms = tmp_path / "Imported ROMs"

    roms.mkdir()
    _write_defaults(defaults)

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )
    writer = ConfigWriter(
        runtime_file=runtime,
    )

    store = ImportSourceStore(
        config_loader=loader,
        config_writer=writer,
    )

    persisted = store.persist_directory(
        roms
    )

    assert persisted["added"] is True
    assert runtime.is_file()

    restarted_sources = SourceManager.__new__(
        SourceManager
    )
    restarted_sources.config = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    ).load()

    sources = restarted_sources.sources()

    assert len(sources) == 1

    source = sources[0]

    assert source.id == "bulk-import"
    assert source.name == "Bulk Import"
    assert source.enabled is True
    assert source.type == "local"
    assert Path(source.path) == roms.resolve()

    service = LibraryService.__new__(
        LibraryService
    )
    service.sources = restarted_sources
    service.builder = RecordingBuilder()

    class State:
        @staticmethod
        def apply(games):
            return list(games)

    class Artwork:
        @staticmethod
        def get_artwork(game):
            return None

    service.state = State()
    service.artwork = Artwork()
    service.games = []

    loaded = service.load()

    assert loaded == []
    assert service.builder.sources is not None
    assert len(service.builder.sources) == 1

    rebuilt_source = (
        service.builder.sources[0]
    )

    assert rebuilt_source.id == "bulk-import"
    assert rebuilt_source.enabled is True
    assert Path(
        rebuilt_source.path
    ) == roms.resolve()


def test_duplicate_persist_does_not_duplicate_restart_source(
    tmp_path,
):
    defaults = tmp_path / "defaults.yaml"
    runtime = tmp_path / "runtime.json"
    roms = tmp_path / "ROMs"

    roms.mkdir()
    _write_defaults(defaults)

    loader = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    )
    writer = ConfigWriter(
        runtime_file=runtime,
    )

    store = ImportSourceStore(
        config_loader=loader,
        config_writer=writer,
    )

    first = store.persist_directory(
        roms
    )
    second = store.persist_directory(
        roms
    )

    assert first["added"] is True
    assert second["added"] is False

    restarted_sources = SourceManager.__new__(
        SourceManager
    )
    restarted_sources.config = ConfigLoader(
        default_file=defaults,
        runtime_file=runtime,
    ).load()

    sources = restarted_sources.sources()

    assert len(sources) == 1
    assert Path(
        sources[0].path
    ) == roms.resolve()
