import json

from config import ConfigLoader, ConfigWriter
from controllers.library_controller import LibraryController
from services.library.import_sources import ImportSourceStore


def _defaults(
    tmp_path,
    source_path,
):
    defaults = (
        tmp_path
        / "defaults.json"
    )

    defaults.write_text(
        json.dumps(
            {
                "library": {
                    "sources": [
                        {
                            "id": "dev",
                            "name": "Development Library",
                            "enabled": True,
                            "type": "local",
                            "path": str(source_path),
                        }
                    ]
                }
            }
        ),
        encoding="utf-8",
    )

    return defaults


def _store(
    tmp_path,
    source_path,
):
    runtime = (
        tmp_path
        / "runtime.json"
    )

    loader = ConfigLoader(
        default_file=_defaults(
            tmp_path,
            source_path,
        ),
        runtime_file=runtime,
    )

    writer = ConfigWriter(
        runtime_file=runtime
    )

    return (
        ImportSourceStore(
            config_loader=loader,
            config_writer=writer,
        ),
        runtime,
        loader,
    )


def test_persist_directory_adds_source(
    tmp_path,
):
    original = (
        tmp_path
        / "original"
    )
    original.mkdir()

    imported = (
        tmp_path
        / "imported"
    )
    imported.mkdir()

    store, runtime, loader = _store(
        tmp_path,
        original,
    )

    result = store.persist_directory(
        imported
    )

    assert result["added"] is True
    assert runtime.is_file()

    sources = (
        loader.load()
        ["library"]
        ["sources"]
    )

    assert len(sources) == 2
    assert sources[0]["path"] == str(
        original
    )
    assert sources[1]["path"] == str(
        imported.resolve()
    )


def test_persist_directory_is_idempotent(
    tmp_path,
):
    original = (
        tmp_path
        / "original"
    )
    original.mkdir()

    imported = (
        tmp_path
        / "imported"
    )
    imported.mkdir()

    store, runtime, loader = _store(
        tmp_path,
        original,
    )

    first = store.persist_directory(
        imported
    )

    second = store.persist_directory(
        imported
    )

    assert first["added"] is True
    assert second["added"] is False

    sources = (
        loader.load()
        ["library"]
        ["sources"]
    )

    assert len(sources) == 2


def test_persist_directory_preserves_existing_source(
    tmp_path,
):
    original = (
        tmp_path
        / "original"
    )
    original.mkdir()

    imported = (
        tmp_path
        / "imported"
    )
    imported.mkdir()

    store, runtime, loader = _store(
        tmp_path,
        original,
    )

    store.persist_directory(
        imported
    )

    sources = (
        loader.load()
        ["library"]
        ["sources"]
    )

    assert sources[0] == {
        "id": "dev",
        "name": "Development Library",
        "enabled": True,
        "type": "local",
        "path": str(original),
    }


def test_persist_directory_generates_unique_id(
    tmp_path,
):
    original = (
        tmp_path
        / "original"
    )
    original.mkdir()

    imported_one = (
        tmp_path
        / "one"
    )
    imported_one.mkdir()

    imported_two = (
        tmp_path
        / "two"
    )
    imported_two.mkdir()

    store, runtime, loader = _store(
        tmp_path,
        original,
    )

    first = store.persist_directory(
        imported_one,
        source_id="bulk-import",
    )

    second = store.persist_directory(
        imported_two,
        source_id="bulk-import",
    )

    assert (
        first["source"]["id"]
        == "bulk-import"
    )

    assert (
        second["source"]["id"]
        == "bulk-import-2"
    )


class FakeImporter:
    def __init__(
        self,
        source,
    ):
        self.source = source

    def import_directory(
        self,
        directory,
        *,
        source_id,
        source_name,
    ):
        return type(
            "Result",
            (),
            {
                "source": self.source,
                "games": tuple(),
                "discovered_count": 0,
                "duplicate_count": 0,
            },
        )()


class FakeLibrary:
    def merge_bulk_import(
        self,
        result,
    ):
        return {
            "added": tuple(),
            "added_count": 0,
            "skipped_count": 0,
        }

    def get_games(self):
        return []


class FakeStore:
    def __init__(self):
        self.calls = []

    def persist_directory(
        self,
        directory,
        *,
        source_id,
        source_name,
    ):
        self.calls.append(
            (
                directory,
                source_id,
                source_name,
            )
        )

        return {
            "added": True,
        }


def test_controller_persists_successful_import(
    tmp_path,
    monkeypatch,
):
    imported = (
        tmp_path
        / "roms"
    )
    imported.mkdir()

    source = type(
        "Source",
        (),
        {
            "path": str(imported),
        },
    )()

    store = FakeStore()

    controller = LibraryController.__new__(
        LibraryController
    )

    controller.bulk_importer = FakeImporter(
        source
    )

    controller.library = FakeLibrary()

    controller.import_source_store = store

    result = controller.bulk_import(
        str(imported),
        source_id="batch",
        source_name="Batch ROM Import",
    )

    assert store.calls == [
        (
            str(imported),
            "batch",
            "Batch ROM Import",
        )
    ]

    assert result["persisted"] == {
        "added": True,
    }
