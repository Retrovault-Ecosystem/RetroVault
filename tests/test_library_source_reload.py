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
