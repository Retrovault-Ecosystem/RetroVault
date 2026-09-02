from controllers.library_controller import (
    LibraryController,
)
from services.library.library_builder import (
    LibraryBuilder,
)
from services.library.library_service import (
    LibraryService,
)
from services.library.scanner import (
    RomScanner,
)


class FakeResolver:
    pass


def test_scanner_preserves_injected_resolver():
    resolver = FakeResolver()

    scanner = RomScanner(
        rvdb_resolver=resolver
    )

    assert scanner.rvdb_resolver is resolver


def test_scanner_without_resolver_stays_unconfigured():
    scanner = RomScanner()

    assert scanner.rvdb_resolver is None


def test_library_builder_propagates_resolver():
    resolver = FakeResolver()

    builder = LibraryBuilder(
        rvdb_resolver=resolver
    )

    assert builder.scanner.rvdb_resolver is resolver


def test_library_service_propagates_resolver():
    resolver = FakeResolver()

    service = LibraryService(
        rvdb_resolver=resolver
    )

    assert (
        service.builder.scanner.rvdb_resolver
        is resolver
    )


def test_library_controller_propagates_resolver(
    monkeypatch,
):
    resolver = FakeResolver()

    monkeypatch.setattr(
        LibraryService,
        "load",
        lambda self: [],
    )

    controller = LibraryController(
        rvdb_resolver=resolver
    )

    assert (
        controller.library
        .builder
        .scanner
        .rvdb_resolver
        is resolver
    )
