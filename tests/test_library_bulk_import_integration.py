from pathlib import Path
from types import SimpleNamespace

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
from services.library.state import (
    game_identity,
)


class MemoryState:
    def __init__(
        self,
        favorite_identities=(),
    ):
        self.favorite_identities = set(
            favorite_identities
        )

    def apply(
        self,
        games,
    ):
        for game in games:
            game.favorite = (
                game_identity(game)
                in self.favorite_identities
            )

        return games

    def recent(
        self,
        limit=20,
    ):
        return []


class NullArtwork:
    def get_artwork(
        self,
        game,
    ):
        return None

    def set_directory(
        self,
        directory,
    ):
        return None


class MemoryCollections:
    def names(self):
        return []

    def identities(
        self,
        name,
    ):
        return []


def make_game(
    root,
    name,
    filename,
    platform="Nintendo Entertainment System",
):
    return Game(
        name=name,
        platform=platform,
        year=0,
        genre="",
        core="fceumm",
        rom=str(
            Path(root)
            / filename
        ),
        source="Test",
    )


def make_result(
    root,
    games,
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


def make_service(
    state=None,
    artwork=None,
):
    service = LibraryService(
        library_state=(
            state
            if state is not None
            else MemoryState()
        ),
        artwork_service=(
            artwork
            if artwork is not None
            else NullArtwork()
        ),
        collection_store=MemoryCollections(),
    )

    service.games = []

    return service


def test_merge_bulk_import_adds_new_games(
    tmp_path,
):
    service = make_service()

    mario = make_game(
        tmp_path,
        "Mario",
        "Mario.nes",
    )

    result = make_result(
        tmp_path,
        [mario],
    )

    merged = service.merge_bulk_import(
        result
    )

    assert merged["added_count"] == 1
    assert merged["skipped_count"] == 0
    assert merged["added"] == (mario,)
    assert service.get_games() == [mario]


def test_merge_bulk_import_preserves_existing_game_object(
    tmp_path,
):
    service = make_service()

    existing = make_game(
        tmp_path,
        "DuckTales 2",
        "Duck Tales 2 (U).nes",
    )

    duplicate = make_game(
        tmp_path,
        "Different Display Name",
        "Duck Tales 2 (U).nes",
    )

    service.games = [
        existing
    ]

    result = make_result(
        tmp_path,
        [duplicate],
    )

    merged = service.merge_bulk_import(
        result
    )

    assert merged["added_count"] == 0
    assert merged["skipped_count"] == 1
    assert service.get_games() == [
        existing
    ]

    assert service.get_games()[0] is existing


def test_merge_bulk_import_two_game_seed_does_not_duplicate(
    tmp_path,
):
    service = make_service()

    duck = make_game(
        tmp_path,
        "DuckTales 2",
        "Duck Tales 2 (U).nes",
    )

    street_fighter = make_game(
        tmp_path,
        "Street Fighter II Turbo",
        "Street Fighter II Turbo (USA) (Rev 1).sfc",
        platform=(
            "Super Nintendo Entertainment System"
        ),
    )

    service.games = [
        duck,
        street_fighter,
    ]

    duplicate_duck = make_game(
        tmp_path,
        "DuckTales 2",
        "Duck Tales 2 (U).nes",
    )

    duplicate_sf = make_game(
        tmp_path,
        "Street Fighter II Turbo",
        "Street Fighter II Turbo (USA) (Rev 1).sfc",
        platform=(
            "Super Nintendo Entertainment System"
        ),
    )

    result = make_result(
        tmp_path,
        [
            duplicate_duck,
            duplicate_sf,
        ],
    )

    merged = service.merge_bulk_import(
        result
    )

    assert merged["added_count"] == 0
    assert merged["skipped_count"] == 2
    assert len(service.get_games()) == 2

    assert service.get_games()[0] in (
        duck,
        street_fighter,
    )

    assert set(
        map(
            game_identity,
            service.get_games(),
        )
    ) == {
        game_identity(duck),
        game_identity(street_fighter),
    }


def test_merge_bulk_import_adds_only_new_game_to_seed(
    tmp_path,
):
    service = make_service()

    duck = make_game(
        tmp_path,
        "DuckTales 2",
        "Duck Tales 2 (U).nes",
    )

    street_fighter = make_game(
        tmp_path,
        "Street Fighter II Turbo",
        "Street Fighter II Turbo (USA) (Rev 1).sfc",
        platform=(
            "Super Nintendo Entertainment System"
        ),
    )

    mario = make_game(
        tmp_path,
        "Mario",
        "Mario.nes",
    )

    service.games = [
        duck,
        street_fighter,
    ]

    result = make_result(
        tmp_path,
        [
            make_game(
                tmp_path,
                "DuckTales 2",
                "Duck Tales 2 (U).nes",
            ),
            make_game(
                tmp_path,
                "Street Fighter II Turbo",
                "Street Fighter II Turbo (USA) (Rev 1).sfc",
                platform=(
                    "Super Nintendo Entertainment System"
                ),
            ),
            mario,
        ],
    )

    merged = service.merge_bulk_import(
        result
    )

    assert merged["added_count"] == 1
    assert merged["skipped_count"] == 2
    assert merged["added"] == (mario,)
    assert len(service.get_games()) == 3


def test_merge_bulk_import_applies_existing_favorite_state(
    tmp_path,
):
    mario = make_game(
        tmp_path,
        "Mario",
        "Mario.nes",
    )

    state = MemoryState(
        favorite_identities=[
            game_identity(mario)
        ]
    )

    service = make_service(
        state=state
    )

    result = make_result(
        tmp_path,
        [mario],
    )

    service.merge_bulk_import(
        result
    )

    assert mario.favorite is True


class Artwork:
    def get_artwork(
        self,
        game,
    ):
        return (
            "/artwork/"
            + Path(game.rom).stem
            + ".png"
        )

    def set_directory(
        self,
        directory,
    ):
        return None


def test_merge_bulk_import_enriches_new_game_artwork(
    tmp_path,
):
    service = make_service(
        artwork=Artwork()
    )

    mario = make_game(
        tmp_path,
        "Mario",
        "Mario.nes",
    )

    result = make_result(
        tmp_path,
        [mario],
    )

    service.merge_bulk_import(
        result
    )

    assert mario.artwork == (
        "/artwork/Mario.png"
    )


def test_merge_bulk_import_deterministically_sorts_library(
    tmp_path,
):
    service = make_service()

    zelda = make_game(
        tmp_path,
        "Zelda",
        "Zelda.nes",
    )

    service.games = [
        zelda
    ]

    mario = make_game(
        tmp_path,
        "Mario",
        "Mario.nes",
    )

    result = make_result(
        tmp_path,
        [mario],
    )

    service.merge_bulk_import(
        result
    )

    assert [
        game.name
        for game in service.get_games()
    ] == [
        "Mario",
        "Zelda",
    ]


def test_merge_bulk_import_skips_game_without_rom_identity(
    tmp_path,
):
    service = make_service()

    invalid = SimpleNamespace(
        name="Invalid",
        platform="Unknown",
        rom="",
    )

    result = make_result(
        tmp_path,
        [invalid],
    )

    merged = service.merge_bulk_import(
        result
    )

    assert merged["added_count"] == 0
    assert merged["skipped_count"] == 1
    assert service.get_games() == []


def test_merge_bulk_import_does_not_mutate_result(
    tmp_path,
):
    service = make_service()

    mario = make_game(
        tmp_path,
        "Mario",
        "Mario.nes",
    )

    result = make_result(
        tmp_path,
        [mario],
    )

    before = result.games

    service.merge_bulk_import(
        result
    )

    assert result.games == before
