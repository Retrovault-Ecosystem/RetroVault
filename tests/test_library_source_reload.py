from controllers.library_controller import (
    LibraryController,
)
from services.library.library_service import (
    LibraryService,
)


class ReloadableSources:

    generations = []

    def __init__(self):
        generation = len(
            self.__class__.generations
        )

        self.generation = generation

        self.__class__.generations.append(
            self
        )

    def sources(self):
        return [
            f"source-{self.generation}"
        ]


class RecordingBuilder:

    def __init__(self):
        self.calls = []

    def build(self, sources):
        sources = list(sources)

        self.calls.append(
            sources
        )

        return []


class IdentityState:

    def apply(self, games):
        return list(games)


class NullArtwork:

    def get_artwork(self, game):
        return None


def make_service():
    ReloadableSources.generations = []

    service = LibraryService.__new__(
        LibraryService
    )

    service.sources = ReloadableSources()
    service.builder = RecordingBuilder()
    service.state = IdentityState()
    service.artwork = NullArtwork()
    service.games = []

    return service


def test_reload_sources_recreates_source_manager_and_rebuilds_library():
    service = make_service()

    original_sources = service.sources

    result = service.reload_sources()

    assert result == []
    assert service.sources is not original_sources
    assert service.sources.generation == 1
    assert service.builder.calls == [
        ["source-1"]
    ]


def test_reload_sources_replaces_previous_live_library_snapshot():
    service = make_service()

    class GameBuilder:
        def build(self, sources):
            source = list(sources)[0]

            game = type(
                "Game",
                (),
                {},
            )()

            game.name = source
            game.artwork = ""

            return [game]

    service.builder = GameBuilder()

    service.games = [
        object(),
        object(),
    ]

    result = service.reload_sources()

    assert len(result) == 1
    assert len(service.get_games()) == 1
    assert service.get_games()[0].name == "source-1"


def test_reload_sources_restores_previous_source_manager_when_load_fails():
    service = make_service()

    original_sources = service.sources

    class FailingBuilder:
        def build(self, sources):
            raise RuntimeError(
                "simulated reload failure"
            )

    service.builder = FailingBuilder()

    try:
        service.reload_sources()
    except RuntimeError as exc:
        assert str(exc) == (
            "simulated reload failure"
        )
    else:
        raise AssertionError(
            "Expected reload failure."
        )

    assert service.sources is original_sources


def test_controller_exposes_library_source_reload_boundary():
    controller = LibraryController.__new__(
        LibraryController
    )

    class FakeLibrary:
        def __init__(self):
            self.calls = 0

        def reload_sources(self):
            self.calls += 1
            return ["reloaded"]

    controller.library = FakeLibrary()

    result = controller.reload_sources()

    assert result == ["reloaded"]
    assert controller.library.calls == 1


def test_reload_sources_restores_previous_games_when_state_apply_fails():
    service = make_service()

    original_games = [
        object(),
        object(),
    ]

    service.games = original_games

    class Game:
        def __init__(self):
            self.artwork = ""

    class SuccessfulBuilder:
        def build(self, sources):
            list(sources)
            return [
                Game(),
            ]

    class FailingState:
        def apply(self, games):
            raise RuntimeError(
                "simulated state failure"
            )

    service.builder = SuccessfulBuilder()
    service.state = FailingState()

    try:
        service.reload_sources()
    except RuntimeError as exc:
        assert str(exc) == (
            "simulated state failure"
        )
    else:
        raise AssertionError(
            "Expected state failure."
        )

    assert service.games is original_games


def test_reload_sources_restores_previous_games_when_artwork_fails():
    service = make_service()

    original_games = [
        object(),
    ]

    service.games = original_games

    class Game:
        def __init__(self):
            self.artwork = ""

    class SuccessfulBuilder:
        def build(self, sources):
            list(sources)
            return [
                Game(),
            ]

    class FailingArtwork:
        def get_artwork(self, game):
            raise RuntimeError(
                "simulated artwork failure"
            )

    service.builder = SuccessfulBuilder()
    service.artwork = FailingArtwork()

    try:
        service.reload_sources()
    except RuntimeError as exc:
        assert str(exc) == (
            "simulated artwork failure"
        )
    else:
        raise AssertionError(
            "Expected artwork failure."
        )

    assert service.games is original_games


def test_reload_failure_restores_sources_and_games_as_one_live_snapshot():
    service = make_service()

    original_sources = service.sources
    original_games = [
        object(),
    ]

    service.games = original_games

    class FailingBuilder:
        def build(self, sources):
            list(sources)

            service.games = [
                object(),
            ]

            raise RuntimeError(
                "simulated partial reload"
            )

    service.builder = FailingBuilder()

    try:
        service.reload_sources()
    except RuntimeError as exc:
        assert str(exc) == (
            "simulated partial reload"
        )
    else:
        raise AssertionError(
            "Expected partial reload failure."
        )

    assert service.sources is original_sources
    assert service.games is original_games


class ReloadGame:

    def __init__(
        self,
        rom,
        *,
        name="Game",
        platform="NES",
    ):
        self.name = name
        self.platform = platform
        self.year = ""
        self.genre = ""
        self.core = ""
        self.rom = rom
        self.source = ""
        self.artwork = ""
        self.favorite = False
        self.rvdb_platform_id = ""
        self.rvdb_game_id = ""
        self.description = ""
        self.developer = ""
        self.publisher = ""


def test_reload_sources_preserves_existing_game_object_identity():
    service = make_service()

    existing = ReloadGame(
        "/roms/existing.nes",
        name="Old Name",
    )

    service.games = [
        existing
    ]

    class Builder:
        def build(self, sources):
            list(sources)

            game = ReloadGame(
                "/roms/existing.nes",
                name="Updated Name",
            )

            game.description = (
                "Updated metadata"
            )

            return [
                game
            ]

    service.builder = Builder()

    result = service.reload_sources()

    assert len(result) == 1
    assert result[0] is existing
    assert service.games[0] is existing
    assert existing.name == "Updated Name"
    assert existing.description == (
        "Updated metadata"
    )


def test_reload_sources_keeps_newly_discovered_game_object():
    service = make_service()

    existing = ReloadGame(
        "/roms/existing.nes"
    )

    service.games = [
        existing
    ]

    discovered = ReloadGame(
        "/roms/new.nes",
        name="New Game",
    )

    class Builder:
        def build(self, sources):
            list(sources)

            return [
                ReloadGame(
                    "/roms/existing.nes"
                ),
                discovered,
            ]

    service.builder = Builder()

    result = service.reload_sources()

    assert len(result) == 2
    assert result[0] is existing
    assert result[1] is discovered


def test_reload_sources_prunes_games_removed_from_enabled_sources():
    service = make_service()

    retained = ReloadGame(
        "/roms/retained.nes"
    )

    removed = ReloadGame(
        "/roms/removed.nes"
    )

    service.games = [
        retained,
        removed,
    ]

    class Builder:
        def build(self, sources):
            list(sources)

            return [
                ReloadGame(
                    "/roms/retained.nes"
                )
            ]

    service.builder = Builder()

    result = service.reload_sources()

    assert len(result) == 1
    assert result[0] is retained
    assert removed not in result


def test_reload_sources_preserves_reloaded_metadata_on_existing_identity():
    service = make_service()

    existing = ReloadGame(
        "/roms/game.nes",
        name="Before",
    )

    existing.favorite = False
    existing.artwork = "old.png"

    service.games = [
        existing
    ]

    refreshed = ReloadGame(
        "/roms/game.nes",
        name="After",
    )

    refreshed.favorite = True
    refreshed.artwork = "builder-artwork.png"
    refreshed.year = "1990"
    refreshed.genre = "Platform"
    refreshed.core = "fceumm"
    refreshed.source = "source-1"
    refreshed.rvdb_platform_id = "nes"
    refreshed.rvdb_game_id = "game-id"
    refreshed.description = "Description"
    refreshed.developer = "Developer"
    refreshed.publisher = "Publisher"

    class Builder:
        def build(self, sources):
            list(sources)
            return [
                refreshed
            ]

    service.builder = Builder()

    result = service.reload_sources()

    assert result[0] is existing
    assert existing.name == "After"
    assert existing.favorite is True
    # LibraryService.load() owns final artwork enrichment.
    # The default test artwork service returns an empty result,
    # so identity preservation must copy that final live value
    # rather than the builder's intermediate artwork value.
    assert existing.artwork == ""
    assert existing.year == "1990"
    assert existing.genre == "Platform"
    assert existing.core == "fceumm"
    assert existing.source == "source-1"
    assert existing.rvdb_platform_id == "nes"
    assert existing.rvdb_game_id == "game-id"
    assert existing.description == "Description"
    assert existing.developer == "Developer"
    assert existing.publisher == "Publisher"
