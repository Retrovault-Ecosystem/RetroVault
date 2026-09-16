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


def test_source_management_rename_preserves_other_sources(
    tmp_path,
):
    import json

    from config import (
        ConfigLoader,
        ConfigWriter,
    )
    from services.library.import_sources import (
        ImportSourceStore,
    )

    runtime = tmp_path / "runtime.json"

    original_sources = [
        {
            "id": "primary",
            "name": "Primary Library",
            "enabled": True,
            "type": "local",
            "path": str(
                tmp_path / "primary"
            ),
        },
        {
            "id": "bulk-import",
            "name": "Bulk Import",
            "enabled": True,
            "type": "local",
            "path": str(
                tmp_path / "bulk"
            ),
        },
    ]

    runtime.write_text(
        json.dumps(
            {
                "library": {
                    "sources": original_sources,
                }
            }
        ),
        encoding="utf-8",
    )

    loader = ConfigLoader(
        runtime_file=runtime
    )
    writer = ConfigWriter(
        runtime_file=runtime
    )

    store = ImportSourceStore(
        config_loader=loader,
        config_writer=writer,
    )

    result = store.rename_source(
        "bulk-import",
        "Imported Games",
    )

    assert (
        result["source"]["name"]
        == "Imported Games"
    )

    saved = json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    )["library"]["sources"]

    assert saved[0] == original_sources[0]

    assert saved[1] == {
        **original_sources[1],
        "name": "Imported Games",
    }


def test_source_management_enable_disable_preserves_sources(
    tmp_path,
):
    import json

    from config import (
        ConfigLoader,
        ConfigWriter,
    )
    from services.library.import_sources import (
        ImportSourceStore,
    )

    runtime = tmp_path / "runtime.json"

    sources = [
        {
            "id": "primary",
            "name": "Primary",
            "enabled": True,
            "type": "local",
            "path": str(
                tmp_path / "primary"
            ),
        },
        {
            "id": "secondary",
            "name": "Secondary",
            "enabled": True,
            "type": "local",
            "path": str(
                tmp_path / "secondary"
            ),
        },
    ]

    runtime.write_text(
        json.dumps(
            {
                "library": {
                    "sources": sources,
                }
            }
        ),
        encoding="utf-8",
    )

    store = ImportSourceStore(
        config_loader=ConfigLoader(
            runtime_file=runtime
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    disabled = store.set_source_enabled(
        "secondary",
        False,
    )

    assert (
        disabled[
            "source"
        ][
            "enabled"
        ]
        is False
    )

    saved = json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    )["library"]["sources"]

    assert saved[0] == sources[0]
    assert saved[1]["enabled"] is False

    enabled = store.set_source_enabled(
        "secondary",
        True,
    )

    assert (
        enabled[
            "source"
        ][
            "enabled"
        ]
        is True
    )


def test_source_management_cannot_disable_last_enabled_source(
    tmp_path,
):
    import json

    import pytest

    from config import (
        ConfigLoader,
        ConfigWriter,
    )
    from services.library.import_sources import (
        ImportSourceStore,
    )

    runtime = tmp_path / "runtime.json"

    payload = {
        "library": {
            "sources": [
                {
                    "id": "primary",
                    "name": "Primary",
                    "enabled": True,
                    "type": "local",
                    "path": str(
                        tmp_path / "primary"
                    ),
                },
                {
                    "id": "secondary",
                    "name": "Secondary",
                    "enabled": False,
                    "type": "local",
                    "path": str(
                        tmp_path / "secondary"
                    ),
                },
            ],
        }
    }

    runtime.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    store = ImportSourceStore(
        config_loader=ConfigLoader(
            runtime_file=runtime
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    with pytest.raises(
        ValueError,
        match="must remain enabled",
    ):
        store.set_source_enabled(
            "primary",
            False,
        )

    assert json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    ) == payload


def test_source_management_remove_preserves_remaining_sources(
    tmp_path,
):
    import json

    from config import (
        ConfigLoader,
        ConfigWriter,
    )
    from services.library.import_sources import (
        ImportSourceStore,
    )

    runtime = tmp_path / "runtime.json"

    primary = {
        "id": "primary",
        "name": "Primary",
        "enabled": True,
        "type": "local",
        "path": str(
            tmp_path / "primary"
        ),
    }

    secondary = {
        "id": "secondary",
        "name": "Secondary",
        "enabled": False,
        "type": "local",
        "path": str(
            tmp_path / "secondary"
        ),
    }

    runtime.write_text(
        json.dumps(
            {
                "library": {
                    "sources": [
                        primary,
                        secondary,
                    ],
                }
            }
        ),
        encoding="utf-8",
    )

    store = ImportSourceStore(
        config_loader=ConfigLoader(
            runtime_file=runtime
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    result = store.remove_source(
        "secondary"
    )

    assert (
        result[
            "removed"
        ][
            "id"
        ]
        == "secondary"
    )

    saved = json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    )["library"]["sources"]

    assert saved == [
        primary
    ]


def test_source_management_cannot_remove_last_enabled_source(
    tmp_path,
):
    import json

    import pytest

    from config import (
        ConfigLoader,
        ConfigWriter,
    )
    from services.library.import_sources import (
        ImportSourceStore,
    )

    runtime = tmp_path / "runtime.json"

    payload = {
        "library": {
            "sources": [
                {
                    "id": "primary",
                    "name": "Primary",
                    "enabled": True,
                    "type": "local",
                    "path": str(
                        tmp_path / "primary"
                    ),
                },
            ],
        }
    }

    runtime.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    store = ImportSourceStore(
        config_loader=ConfigLoader(
            runtime_file=runtime
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    with pytest.raises(
        ValueError,
        match="must remain enabled",
    ):
        store.remove_source(
            "primary"
        )

    assert json.loads(
        runtime.read_text(
            encoding="utf-8"
        )
    ) == payload


def test_source_management_rejects_unknown_source_without_mutation(
    tmp_path,
):
    import json

    import pytest

    from config import (
        ConfigLoader,
        ConfigWriter,
    )
    from services.library.import_sources import (
        ImportSourceStore,
    )

    runtime = tmp_path / "runtime.json"

    payload = {
        "library": {
            "sources": [
                {
                    "id": "primary",
                    "name": "Primary",
                    "enabled": True,
                    "type": "local",
                    "path": str(
                        tmp_path / "primary"
                    ),
                },
            ],
        }
    }

    runtime.write_text(
        json.dumps(
            payload
        ),
        encoding="utf-8",
    )

    store = ImportSourceStore(
        config_loader=ConfigLoader(
            runtime_file=runtime
        ),
        config_writer=ConfigWriter(
            runtime_file=runtime
        ),
    )

    for operation in (
        lambda: store.rename_source(
            "missing",
            "Missing",
        ),
        lambda: store.set_source_enabled(
            "missing",
            False,
        ),
        lambda: store.remove_source(
            "missing"
        ),
    ):
        with pytest.raises(
            ValueError,
            match="Library source not found",
        ):
            operation()

        assert json.loads(
            runtime.read_text(
                encoding="utf-8"
            )
        ) == payload


def test_bulk_import_persistence_failure_does_not_mutate_live_library(
    tmp_path,
):
    from controllers.library_controller import LibraryController

    class FakeSource:
        path = tmp_path

    class FakeDiscovered:
        source = FakeSource()

    class FakeImporter:
        def import_directory(
            self,
            directory,
            *,
            source_id=None,
            source_name=None,
        ):
            return FakeDiscovered()

    class FakeLibrary:
        def __init__(self):
            self.merge_calls = 0

        def merge_bulk_import(self, discovered):
            self.merge_calls += 1
            raise AssertionError(
                "Live library must not mutate before "
                "source persistence succeeds."
            )

        def get_games(self):
            return []

    class FailingImportSourceStore:
        def persist_directory(
            self,
            directory,
            *,
            source_id=None,
            source_name=None,
        ):
            raise OSError(
                "simulated persistence failure"
            )

    library = FakeLibrary()

    controller = object.__new__(LibraryController)
    controller.library = library
    controller.bulk_importer = FakeImporter()
    controller.import_source_store = (
        FailingImportSourceStore()
    )

    try:
        controller.bulk_import(
            tmp_path,
            source_id="atomic-source",
            source_name="Atomic Source",
        )
    except OSError as exc:
        assert str(exc) == "simulated persistence failure"
    else:
        raise AssertionError(
            "Expected persistence failure to propagate."
        )

    assert library.merge_calls == 0
