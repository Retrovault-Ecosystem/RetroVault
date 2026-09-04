import json

import pytest

from services.library.collections import (
    CollectionStore,
)


class FakeGame:
    def __init__(
        self,
        rom,
    ):
        self.rom = str(rom)


def test_missing_file_has_no_collections(
    tmp_path,
):
    store = CollectionStore(
        tmp_path / "collections.json"
    )

    assert store.names() == []


def test_create_collection_persists_name(
    tmp_path,
):
    path = tmp_path / "collections.json"
    store = CollectionStore(path)

    assert store.create(
        "Arcade Favorites"
    ) == "Arcade Favorites"

    assert CollectionStore(path).names() == [
        "Arcade Favorites"
    ]


def test_collection_name_is_trimmed(
    tmp_path,
):
    store = CollectionStore(
        tmp_path / "collections.json"
    )

    assert store.create(
        "  Weekend Games  "
    ) == "Weekend Games"


def test_empty_collection_name_is_rejected(
    tmp_path,
):
    store = CollectionStore(
        tmp_path / "collections.json"
    )

    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        store.create("   ")


def test_duplicate_names_are_case_insensitive(
    tmp_path,
):
    store = CollectionStore(
        tmp_path / "collections.json"
    )

    store.create("Favorites")

    with pytest.raises(
        ValueError,
        match="already exists",
    ):
        store.create("favorites")


def test_add_game_persists_rom_identity(
    tmp_path,
):
    path = tmp_path / "collections.json"
    store = CollectionStore(path)
    game = FakeGame(
        tmp_path / "duck-tales-2.nes"
    )

    store.create("NES")
    identity = store.add_game(
        "NES",
        game,
    )

    assert store.identities("NES") == [
        identity
    ]

    assert CollectionStore(path).identities(
        "NES"
    ) == [identity]


def test_add_game_does_not_duplicate_identity(
    tmp_path,
):
    store = CollectionStore(
        tmp_path / "collections.json"
    )
    game = FakeGame(
        tmp_path / "game.nes"
    )

    store.create("Collection")
    store.add_game("Collection", game)
    store.add_game("Collection", game)

    assert len(
        store.identities("Collection")
    ) == 1


def test_collection_preserves_game_order(
    tmp_path,
):
    store = CollectionStore(
        tmp_path / "collections.json"
    )
    first = FakeGame(
        tmp_path / "first.nes"
    )
    second = FakeGame(
        tmp_path / "second.nes"
    )

    store.create("Ordered")
    first_identity = store.add_game(
        "Ordered",
        first,
    )
    second_identity = store.add_game(
        "Ordered",
        second,
    )

    assert store.identities("Ordered") == [
        first_identity,
        second_identity,
    ]


def test_remove_game_preserves_collection(
    tmp_path,
):
    store = CollectionStore(
        tmp_path / "collections.json"
    )
    game = FakeGame(
        tmp_path / "game.nes"
    )

    store.create("Keep Me")
    store.add_game("Keep Me", game)
    store.remove_game("Keep Me", game)

    assert store.names() == ["Keep Me"]
    assert store.identities("Keep Me") == []


def test_rename_preserves_membership(
    tmp_path,
):
    store = CollectionStore(
        tmp_path / "collections.json"
    )
    game = FakeGame(
        tmp_path / "game.nes"
    )

    store.create("Old Name")
    identity = store.add_game(
        "Old Name",
        game,
    )

    assert store.rename(
        "Old Name",
        "New Name",
    ) == "New Name"

    assert store.names() == ["New Name"]
    assert store.identities("New Name") == [
        identity
    ]


def test_delete_removes_collection(
    tmp_path,
):
    store = CollectionStore(
        tmp_path / "collections.json"
    )

    store.create("Temporary")
    store.delete("Temporary")

    assert store.names() == []


def test_unknown_collection_is_rejected(
    tmp_path,
):
    store = CollectionStore(
        tmp_path / "collections.json"
    )

    with pytest.raises(
        KeyError,
        match="Unknown collection",
    ):
        store.identities("Missing")


def test_write_is_atomic_and_leaves_no_temp_file(
    tmp_path,
):
    path = tmp_path / "collections.json"
    store = CollectionStore(path)

    store.create("Atomic")

    assert path.is_file()
    assert not (
        tmp_path / "collections.json.tmp"
    ).exists()


def test_collections_are_separate_from_library_state(
    tmp_path,
):
    path = tmp_path / "collections.json"
    store = CollectionStore(path)

    store.create("Separate")

    data = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    assert data == {
        "collections": [
            {
                "games": [],
                "name": "Separate",
            }
        ],
        "version": 1,
    }
