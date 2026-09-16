from pathlib import Path
from types import SimpleNamespace

from controllers.library_controller import (
    LibraryController,
)
from services.library.bulk_import import (
    BulkImportResult,
)
from services.library.library_service import (
    LibraryService,
)
from services.library.models import Game
from services.library.source_manager import (
    LibrarySource,
)


class FakeImporter:
    def __init__(
        self,
        result,
    ):
        self.result = result
        self.calls = []

    def import_directory(
        self,
        directory,
        *,
        source_id="bulk-import",
        source_name="Bulk Import",
    ):
        self.calls.append(
            {
                "directory": directory,
                "source_id": source_id,
                "source_name": source_name,
            }
        )

        return self.result


class FakeLibrary:
    def __init__(
        self,
        merge_result,
    ):
        self.merge_result = merge_result
        self.calls = []

    def merge_bulk_import(
        self,
        result,
    ):
        self.calls.append(
            result
        )

        return self.merge_result

    def get_games(self):
        return []


def make_game(
    root,
    name="Mario",
    filename="Mario.nes",
):
    return Game(
        name=name,
        platform=(
            "Nintendo Entertainment System"
        ),
        year=0,
        genre="",
        core="fceumm",
        rom=str(
            Path(root)
            / filename
        ),
        source="Bulk Import",
    )


def make_result(
    root,
    games=(),
):
    source = LibrarySource(
        id="bulk-import",
        name="Bulk Import",
        enabled=True,
        type="local",
        path=str(root),
    )

    return BulkImportResult(
        source=source,
        games=tuple(games),
        discovered_count=len(games),
        duplicate_count=0,
    )


def make_controller_without_init(
    importer,
    library,
):
    controller = object.__new__(
        LibraryController
    )

    controller.bulk_importer = importer
    controller.library = library

    return controller


def test_controller_bulk_import_runs_discovery_then_merge(
    tmp_path,
):
    mario = make_game(
        tmp_path
    )

    discovered = make_result(
        tmp_path,
        [mario],
    )

    importer = FakeImporter(
        discovered
    )

    library = FakeLibrary(
        {
            "added": (mario,),
            "added_count": 1,
            "skipped_count": 0,
        }
    )

    controller = make_controller_without_init(
        importer,
        library,
    )

    result = controller.bulk_import(
        tmp_path
    )

    assert importer.calls == [
        {
            "directory": tmp_path,
            "source_id": "bulk-import",
            "source_name": "Bulk Import",
        }
    ]

    assert library.calls == [
        discovered
    ]

    assert result["discovered"] is discovered
    assert result["added"] == (mario,)
    assert result["added_count"] == 1
    assert result["skipped_count"] == 0


def test_controller_bulk_import_forwards_source_metadata(
    tmp_path,
):
    discovered = make_result(
        tmp_path
    )

    importer = FakeImporter(
        discovered
    )

    library = FakeLibrary(
        {
            "added": (),
            "added_count": 0,
            "skipped_count": 0,
        }
    )

    controller = make_controller_without_init(
        importer,
        library,
    )

    controller.bulk_import(
        tmp_path,
        source_id="starter-suite",
        source_name="Starter Suite",
    )

    assert importer.calls == [
        {
            "directory": tmp_path,
            "source_id": "starter-suite",
            "source_name": "Starter Suite",
        }
    ]


def test_controller_bulk_import_preserves_discovery_counts(
    tmp_path,
):
    discovered = BulkImportResult(
        source=LibrarySource(
            id="bulk-import",
            name="Bulk Import",
            enabled=True,
            type="local",
            path=str(tmp_path),
        ),
        games=(),
        discovered_count=7,
        duplicate_count=2,
    )

    importer = FakeImporter(
        discovered
    )

    library = FakeLibrary(
        {
            "added": (),
            "added_count": 0,
            "skipped_count": 5,
        }
    )

    controller = make_controller_without_init(
        importer,
        library,
    )

    result = controller.bulk_import(
        tmp_path
    )

    assert (
        result["discovered"].discovered_count
        == 7
    )

    assert (
        result["discovered"].duplicate_count
        == 2
    )

    assert result["added_count"] == 0
    assert result["skipped_count"] == 5


def test_controller_accepts_injected_bulk_importer(
    monkeypatch,
):
    importer = SimpleNamespace()

    monkeypatch.setattr(
        LibraryService,
        "load",
        lambda self: [],
    )

    controller = LibraryController(
        bulk_importer=importer
    )

    assert controller.bulk_importer is importer


def test_controller_default_bulk_importer_preserves_resolver(
    monkeypatch,
):
    resolver = object()

    monkeypatch.setattr(
        LibraryService,
        "load",
        lambda self: [],
    )

    controller = LibraryController(
        rvdb_resolver=resolver
    )

    assert (
        controller.bulk_importer
        .scanner
        .rvdb_resolver
        is resolver
    )

    assert (
        controller.library
        .builder
        .scanner
        .rvdb_resolver
        is resolver
    )


def test_controller_bulk_import_propagates_discovery_error(
    tmp_path,
):
    class FailingImporter:
        def import_directory(
            self,
            directory,
            **kwargs,
        ):
            raise ValueError(
                "invalid import directory"
            )

    library = FakeLibrary(
        {
            "added": (),
            "added_count": 0,
            "skipped_count": 0,
        }
    )

    controller = make_controller_without_init(
        FailingImporter(),
        library,
    )

    try:
        controller.bulk_import(
            tmp_path
        )
    except ValueError as exc:
        assert str(exc) == (
            "invalid import directory"
        )
    else:
        raise AssertionError(
            "ValueError was not propagated."
        )

    assert library.calls == []
