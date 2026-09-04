from services.library.collections import (
    CollectionStore,
)
from services.library.library_service import (
    LibraryService,
)
from services.library.models import Game


class FakeState:
    def apply(
        self,
        games,
    ):
        return games


class FakeArtwork:
    def get_artwork(
        self,
        game,
    ):
        return None


def make_service(
    tmp_path,
):
    return LibraryService(
        library_state=FakeState(),
        artwork_service=FakeArtwork(),
        collection_store=CollectionStore(
            tmp_path / "collections.json"
        ),
    )


def make_game(
    tmp_path,
    name,
):
    return Game(
        name=name,
        platform="NES",
        year=1990,
        genre="Test",
        core="fceumm",
        rom=str(
            tmp_path
            / f"{name}.nes"
        ),
    )


def test_service_preserves_injected_collection_store(
    tmp_path,
):
    store = CollectionStore(
        tmp_path / "collections.json"
    )

    service = LibraryService(
        library_state=FakeState(),
        artwork_service=FakeArtwork(),
        collection_store=store,
    )

    assert service.collections is store


def test_service_creates_default_collection_store():
    service = LibraryService(
        library_state=FakeState(),
        artwork_service=FakeArtwork(),
    )

    assert isinstance(
        service.collections,
        CollectionStore,
    )


def test_service_collection_lifecycle(
    tmp_path,
):
    service = make_service(tmp_path)

    service.create_collection(
        "Weekend"
    )

    assert service.collection_names() == [
        "Weekend"
    ]

    service.rename_collection(
        "Weekend",
        "Classics",
    )

    assert service.collection_names() == [
        "Classics"
    ]

    service.delete_collection(
        "Classics"
    )

    assert service.collection_names() == []


def test_service_adds_and_removes_game(
    tmp_path,
):
    service = make_service(tmp_path)
    game = make_game(
        tmp_path,
        "Duck Tales 2",
    )

    service.create_collection("NES")
    identity = service.add_to_collection(
        "NES",
        game,
    )

    assert service.collections.identities(
        "NES"
    ) == [identity]

    service.remove_from_collection(
        "NES",
        game,
    )

    assert service.collections.identities(
        "NES"
    ) == []


def test_service_resolves_collection_members_to_games(
    tmp_path,
):
    service = make_service(tmp_path)

    first = make_game(
        tmp_path,
        "First",
    )
    second = make_game(
        tmp_path,
        "Second",
    )

    service.games = [
        second,
        first,
    ]

    service.create_collection("Ordered")
    service.add_to_collection(
        "Ordered",
        first,
    )
    service.add_to_collection(
        "Ordered",
        second,
    )

    assert service.collection_games(
        "Ordered"
    ) == [
        first,
        second,
    ]


def test_service_ignores_missing_collection_members(
    tmp_path,
):
    first = make_service(tmp_path)
    missing = make_game(
        tmp_path,
        "Missing",
    )

    first.create_collection("Portable")
    first.add_to_collection(
        "Portable",
        missing,
    )

    second = make_service(tmp_path)
    second.games = []

    assert second.collection_games(
        "Portable"
    ) == []


def test_service_ignores_library_games_without_rom(
    tmp_path,
):
    service = make_service(tmp_path)
    valid = make_game(
        tmp_path,
        "Valid",
    )
    missing_rom = make_game(
        tmp_path,
        "No ROM",
    )
    missing_rom.rom = ""

    service.games = [
        missing_rom,
        valid,
    ]

    service.create_collection("Safe")
    service.add_to_collection(
        "Safe",
        valid,
    )

    assert service.collection_games(
        "Safe"
    ) == [valid]


def test_collection_store_is_public_library_export():
    from services.library import (
        CollectionStore as ExportedStore,
    )

    assert ExportedStore is CollectionStore
