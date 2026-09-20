from types import SimpleNamespace

from services.library.canonicalization import (
    LibraryCanonicalizer,
)
from services.library.library_service import (
    LibraryService,
)
from services.library.models import Game


class IdentityState:
    def apply(self, games):
        return list(games)


class NullArtwork:
    def get_artwork(self, game):
        return None


class StaticSources:
    def sources(self):
        return []


def make_game(
    filename,
    *,
    name=None,
):
    return Game(
        name=(
            name
            if name is not None
            else filename.rsplit(".", 1)[0]
        ),
        platform=(
            "Nintendo Entertainment System"
        ),
        year=0,
        genre="",
        core="nestopia",
        rom=f"/roms/{filename}",
        source="Validation",
        rvdb_platform_id="platform.nes",
    )


def make_service(games=None):
    service = LibraryService.__new__(
        LibraryService
    )

    service.sources = StaticSources()
    service.state = IdentityState()
    service.artwork = NullArtwork()
    service.canonicalizer = (
        LibraryCanonicalizer()
    )
    service.games = list(
        games or []
    )

    return service


def variant_roms(game):
    return {
        variant["rom"]
        for variant in game.variants
    }


def test_repeated_bulk_import_preserves_existing_hidden_editions():
    usa = make_game(
        "Example Game (USA).nes"
    )

    japan = make_game(
        "Example Game (Japan).nes"
    )

    revision = make_game(
        "Example Game (USA) (Rev 1).nes"
    )

    service = make_service(
        LibraryCanonicalizer().canonicalize(
            [
                usa,
                japan,
            ]
        )
    )

    assert len(service.games) == 1
    assert len(service.games[0].variants) == 2

    service.merge_bulk_import(
        SimpleNamespace(
            games=[
                revision,
            ]
        )
    )

    assert len(service.games) == 1

    roms = variant_roms(
        service.games[0]
    )

    assert usa.rom in roms
    assert japan.rom in roms
    assert revision.rom in roms
    assert len(roms) == 3


def test_sequential_bulk_imports_accumulate_all_editions():
    usa = make_game(
        "Example Game (USA).nes"
    )

    service = make_service(
        LibraryCanonicalizer().canonicalize(
            [usa]
        )
    )

    editions = [
        make_game(
            "Example Game (Japan).nes"
        ),
        make_game(
            "Example Game (USA) (Rev 1).nes"
        ),
        make_game(
            "Example Game (J) [T+Eng].nes"
        ),
        make_game(
            "Example Game (USA) [h1].nes"
        ),
    ]

    for edition in editions:
        service.merge_bulk_import(
            SimpleNamespace(
                games=[
                    edition,
                ]
            )
        )

    assert len(service.games) == 1

    roms = variant_roms(
        service.games[0]
    )

    expected = {
        usa.rom,
        *(
            edition.rom
            for edition in editions
        ),
    }

    assert roms == expected


def test_canonicalizer_variant_records_keep_physical_paths():
    games = [
        make_game(
            "Example Game (USA).nes"
        ),
        make_game(
            "Example Game (Japan).nes"
        ),
        make_game(
            "Example Game (USA) (Rev 1).nes"
        ),
    ]

    visible = (
        LibraryCanonicalizer()
        .canonicalize(games)
    )

    assert len(visible) == 1

    assert variant_roms(
        visible[0]
    ) == {
        game.rom
        for game in games
    }


def test_multi_edition_family_keeps_one_preferred_variant():
    games = [
        make_game(
            "Example Game (USA).nes"
        ),
        make_game(
            "Example Game (Japan).nes"
        ),
        make_game(
            "Example Game (USA) (Rev 1).nes"
        ),
    ]

    visible = (
        LibraryCanonicalizer()
        .canonicalize(games)
    )

    preferred = [
        variant
        for variant in visible[0].variants
        if variant["preferred"]
    ]

    assert len(preferred) == 1

    assert preferred[0]["rom"].endswith(
        "Example Game (USA).nes"
    )

def test_empty_physical_store_bootstraps_from_seeded_games():
    existing = make_game(
        "Seeded Game (USA).nes"
    )

    service = make_service()

    service._physical_games = []
    service.games = [
        existing
    ]

    physical = (
        service._physical_inventory()
    )

    assert len(physical) == 1
    assert physical[0] is existing
    assert (
        service._physical_games[0]
        is existing
    )


def test_seeded_canonical_family_bootstrap_restores_hidden_editions():
    usa = make_game(
        "Example Game (USA).nes"
    )

    japan = make_game(
        "Example Game (Japan).nes"
    )

    visible = (
        LibraryCanonicalizer()
        .canonicalize(
            [
                usa,
                japan,
            ]
        )
    )

    service = make_service()

    service._physical_games = []
    service.games = visible

    physical = (
        service._physical_inventory()
    )

    assert {
        game.rom
        for game in physical
    } == {
        usa.rom,
        japan.rom,
    }


def test_nonempty_physical_store_remains_authoritative():
    usa = make_game(
        "Example Game (USA).nes"
    )

    japan = make_game(
        "Example Game (Japan).nes"
    )

    service = make_service()

    service._physical_games = [
        usa,
        japan,
    ]

    service.games = [
        usa
    ]

    physical = (
        service._physical_inventory()
    )

    assert physical is (
        service._physical_games
    )

    assert {
        game.rom
        for game in physical
    } == {
        usa.rom,
        japan.rom,
    }



def test_load_preserves_state_list_when_projection_is_identity_equivalent():
    game = make_game(
        "Singleton Game (USA).nes",
        name="Curated Singleton Name",
    )

    class Builder:
        def build(self, sources):
            return [game]

    class Sources:
        def sources(self):
            return ["/roms"]

    class State:
        def __init__(self):
            self.applied_games = None

        def apply(self, games):
            self.applied_games = list(
                games
            )
            return self.applied_games

    state = State()

    service = LibraryService.__new__(
        LibraryService
    )

    service.builder = Builder()
    service.sources = Sources()
    service.state = state
    service.artwork = NullArtwork()
    service.canonicalizer = (
        LibraryCanonicalizer()
    )
    service.games = []
    service._physical_games = []

    loaded = service.load()

    assert loaded is (
        state.applied_games
    )
    assert service.games is loaded
    assert loaded[0] is game
    assert (
        loaded[0].name
        == "Curated Singleton Name"
    )


def test_load_uses_canonical_projection_when_family_collapses():
    usa = make_game(
        "Example Game (USA).nes"
    )

    japan = make_game(
        "Example Game (Japan).nes"
    )

    class Builder:
        def build(self, sources):
            return [
                usa,
                japan,
            ]

    class Sources:
        def sources(self):
            return ["/roms"]

    class State:
        def __init__(self):
            self.applied_games = None

        def apply(self, games):
            self.applied_games = list(
                games
            )
            return self.applied_games

    state = State()

    service = LibraryService.__new__(
        LibraryService
    )

    service.builder = Builder()
    service.sources = Sources()
    service.state = state
    service.artwork = NullArtwork()
    service.canonicalizer = (
        LibraryCanonicalizer()
    )
    service.games = []
    service._physical_games = []

    loaded = service.load()

    assert len(
        state.applied_games
    ) == 2

    assert len(
        service._physical_games
    ) == 2

    assert len(loaded) == 1
    assert loaded is service.games
    assert loaded is not (
        state.applied_games
    )

    assert {
        variant["rom"]
        for variant in loaded[0].variants
    } == {
        usa.rom,
        japan.rom,
    }
