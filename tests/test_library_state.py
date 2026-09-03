import json
from dataclasses import dataclass

import pytest

from services.library.state import (
    LibraryState,
    game_identity,
)


@dataclass
class FakeGame:
    name: str
    rom: str
    favorite: bool = False


def test_missing_state_defaults_to_no_favorites(
    tmp_path,
):
    state = LibraryState(
        tmp_path
        / "library-state.json"
    )

    assert state.favorites() == set()


def test_game_identity_uses_expanded_rom_path(
    tmp_path,
):
    rom = (
        tmp_path
        / "roms"
        / "Duck Tales 2.nes"
    )

    game = FakeGame(
        name="Duck Tales 2",
        rom=str(rom),
    )

    assert game_identity(game) == str(
        rom.resolve(
            strict=False
        )
    )


def test_game_without_rom_cannot_be_persisted(
    tmp_path,
):
    game = FakeGame(
        name="No ROM",
        rom="",
    )

    with pytest.raises(
        ValueError,
        match="without a ROM path",
    ):
        game_identity(game)


def test_set_favorite_persists_identity(
    tmp_path,
):
    state_file = (
        tmp_path
        / "library-state.json"
    )

    state = LibraryState(
        state_file
    )

    game = FakeGame(
        name="Duck Tales 2",
        rom=str(
            tmp_path
            / "roms"
            / "Duck Tales 2.nes"
        ),
    )

    state.set_favorite(
        game,
        True,
    )

    assert state.is_favorite(
        game
    )

    data = json.loads(
        state_file.read_text(
            encoding="utf-8"
        )
    )

    assert data == {
        "favorites": [
            game_identity(game)
        ],
        "recent": [],
    }


def test_favorite_survives_new_service_instance(
    tmp_path,
):
    state_file = (
        tmp_path
        / "library-state.json"
    )

    game = FakeGame(
        name="Duck Tales 2",
        rom=str(
            tmp_path
            / "roms"
            / "Duck Tales 2.nes"
        ),
    )

    first = LibraryState(
        state_file
    )

    first.set_favorite(
        game,
        True,
    )

    second = LibraryState(
        state_file
    )

    assert second.is_favorite(
        game
    )


def test_clear_favorite_removes_identity(
    tmp_path,
):
    state = LibraryState(
        tmp_path
        / "library-state.json"
    )

    game = FakeGame(
        name="Duck Tales 2",
        rom=str(
            tmp_path
            / "roms"
            / "Duck Tales 2.nes"
        ),
    )

    state.set_favorite(
        game,
        True,
    )

    state.set_favorite(
        game,
        False,
    )

    assert not state.is_favorite(
        game
    )

    assert state.favorites() == set()


def test_multiple_favorites_are_preserved(
    tmp_path,
):
    state = LibraryState(
        tmp_path
        / "library-state.json"
    )

    first = FakeGame(
        name="First",
        rom=str(
            tmp_path
            / "first.nes"
        ),
    )

    second = FakeGame(
        name="Second",
        rom=str(
            tmp_path
            / "second.nes"
        ),
    )

    state.set_favorite(
        first,
        True,
    )

    state.set_favorite(
        second,
        True,
    )

    assert state.is_favorite(
        first
    )

    assert state.is_favorite(
        second
    )


def test_duplicate_stored_favorites_are_normalized(
    tmp_path,
):
    state_file = (
        tmp_path
        / "library-state.json"
    )

    state_file.write_text(
        json.dumps(
            {
                "favorites": [
                    "/roms/game.nes",
                    "/roms/game.nes",
                ]
            }
        ),
        encoding="utf-8",
    )

    state = LibraryState(
        state_file
    )

    assert state.favorites() == {
        "/roms/game.nes"
    }


def test_invalid_json_is_rejected(
    tmp_path,
):
    state_file = (
        tmp_path
        / "library-state.json"
    )

    state_file.write_text(
        "{broken",
        encoding="utf-8",
    )

    state = LibraryState(
        state_file
    )

    with pytest.raises(
        ValueError,
        match="Invalid RetroVault Library state",
    ):
        state.favorites()


def test_non_object_root_is_rejected(
    tmp_path,
):
    state_file = (
        tmp_path
        / "library-state.json"
    )

    state_file.write_text(
        "[]",
        encoding="utf-8",
    )

    state = LibraryState(
        state_file
    )

    with pytest.raises(
        ValueError,
        match="must contain a JSON object",
    ):
        state.favorites()


def test_non_list_favorites_are_rejected(
    tmp_path,
):
    state_file = (
        tmp_path
        / "library-state.json"
    )

    state_file.write_text(
        json.dumps(
            {
                "favorites": "wrong"
            }
        ),
        encoding="utf-8",
    )

    state = LibraryState(
        state_file
    )

    with pytest.raises(
        ValueError,
        match="must contain a JSON list",
    ):
        state.favorites()


def test_non_string_favorite_identity_is_rejected(
    tmp_path,
):
    state_file = (
        tmp_path
        / "library-state.json"
    )

    state_file.write_text(
        json.dumps(
            {
                "favorites": [
                    123
                ]
            }
        ),
        encoding="utf-8",
    )

    state = LibraryState(
        state_file
    )

    with pytest.raises(
        ValueError,
        match="must contain string identities",
    ):
        state.favorites()


def test_apply_marks_persisted_games_favorite(
    tmp_path,
):
    state = LibraryState(
        tmp_path
        / "library-state.json"
    )

    favorite = FakeGame(
        name="Favorite",
        rom=str(
            tmp_path
            / "favorite.nes"
        ),
    )

    ordinary = FakeGame(
        name="Ordinary",
        rom=str(
            tmp_path
            / "ordinary.nes"
        ),
        favorite=True,
    )

    state.set_favorite(
        favorite,
        True,
    )

    games = state.apply(
        [
            favorite,
            ordinary,
        ]
    )

    assert games[0].favorite is True
    assert games[1].favorite is False


def test_apply_handles_game_without_rom(
    tmp_path,
):
    state = LibraryState(
        tmp_path
        / "library-state.json"
    )

    game = FakeGame(
        name="No ROM",
        rom="",
        favorite=True,
    )

    state.apply(
        [game]
    )

    assert game.favorite is False


def test_write_creates_parent_directory(
    tmp_path,
):
    state_file = (
        tmp_path
        / "nested"
        / "retrovault"
        / "library-state.json"
    )

    state = LibraryState(
        state_file
    )

    game = FakeGame(
        name="Game",
        rom=str(
            tmp_path
            / "game.nes"
        ),
    )

    state.set_favorite(
        game,
        True,
    )

    assert state_file.is_file()


def test_write_leaves_no_temporary_file(
    tmp_path,
):
    state_file = (
        tmp_path
        / "library-state.json"
    )

    state = LibraryState(
        state_file
    )

    game = FakeGame(
        name="Game",
        rom=str(
            tmp_path
            / "game.nes"
        ),
    )

    state.set_favorite(
        game,
        True,
    )

    assert not (
        tmp_path
        / "library-state.json.tmp"
    ).exists()


class FakeBuilder:
    def __init__(
        self,
        games,
    ):
        self.games = games
        self.received_sources = None

    def build(
        self,
        sources,
    ):
        self.received_sources = sources
        return self.games


class FakeSources:
    def __init__(
        self,
        sources=None,
    ):
        self._sources = (
            list(sources)
            if sources is not None
            else []
        )

    def sources(self):
        return self._sources


class FakeState:
    def __init__(self):
        self.applied_games = None

    def apply(
        self,
        games,
    ):
        self.applied_games = games

        for game in games:
            game.favorite = True

        return games


def test_library_service_preserves_injected_state():
    from services.library.library_service import (
        LibraryService,
    )

    state = FakeState()

    service = LibraryService(
        library_state=state
    )

    assert service.state is state


def test_library_service_creates_default_state():
    from services.library.library_service import (
        LibraryService,
    )

    service = LibraryService()

    assert isinstance(
        service.state,
        LibraryState,
    )


def test_library_service_applies_state_after_build():
    from services.library.library_service import (
        LibraryService,
    )

    game = FakeGame(
        name="Adventure Island",
        rom="/roms/adventure-island.nes",
    )

    state = FakeState()

    service = LibraryService(
        library_state=state
    )

    builder = FakeBuilder(
        [game]
    )

    sources = FakeSources(
        ["/roms"]
    )

    service.builder = builder
    service.sources = sources

    games = service.load()

    assert builder.received_sources == [
        "/roms"
    ]

    assert state.applied_games is games

    assert games == [
        game
    ]

    assert game.favorite is True


def test_library_service_returns_state_applied_games():
    from services.library.library_service import (
        LibraryService,
    )

    original = FakeGame(
        name="Original",
        rom="/roms/original.nes",
    )

    replacement = FakeGame(
        name="Replacement",
        rom="/roms/replacement.nes",
    )

    class ReplacingState:
        def apply(
            self,
            games,
        ):
            assert games == [
                original
            ]

            return [
                replacement
            ]

    service = LibraryService(
        library_state=ReplacingState()
    )

    service.builder = FakeBuilder(
        [original]
    )

    service.sources = FakeSources()

    games = service.load()

    assert games == [
        replacement
    ]

    assert service.get_games() == [
        replacement
    ]


def test_library_service_set_favorite_persists_and_updates_game(
    tmp_path,
):
    from services.library.library_service import (
        LibraryService,
    )

    state = LibraryState(
        tmp_path
        / "library-state.json"
    )

    service = LibraryService(
        library_state=state
    )

    game = FakeGame(
        name="Adventure Island",
        rom=str(
            tmp_path
            / "Adventure Island.nes"
        ),
    )

    result = service.set_favorite(
        game,
        True,
    )

    assert result is True
    assert game.favorite is True
    assert state.is_favorite(game)


def test_library_service_can_remove_favorite(
    tmp_path,
):
    from services.library.library_service import (
        LibraryService,
    )

    state = LibraryState(
        tmp_path
        / "library-state.json"
    )

    service = LibraryService(
        library_state=state
    )

    game = FakeGame(
        name="Adventure Island",
        rom=str(
            tmp_path
            / "Adventure Island.nes"
        ),
    )

    service.set_favorite(
        game,
        True,
    )

    result = service.set_favorite(
        game,
        False,
    )

    assert result is False
    assert game.favorite is False
    assert not state.is_favorite(game)


def test_missing_state_defaults_to_no_recent_games(
    tmp_path,
):

    state = LibraryState(
        tmp_path
        / "library-state.json"
    )

    assert state.recent() == []


def test_record_played_persists_game_identity(
    tmp_path,
):

    state_file = (
        tmp_path
        / "library-state.json"
    )

    state = LibraryState(
        state_file
    )

    game = FakeGame(
        name="Duck Tales 2",
        rom=str(
            tmp_path
            / "duck-tales-2.nes"
        )
    )

    state.record_played(
        game
    )

    identity = game_identity(
        game
    )

    assert state.recent() == [
        identity
    ]

    data = json.loads(
        state_file.read_text(
            encoding="utf-8"
        )
    )

    assert data["recent"] == [
        identity
    ]


def test_record_played_moves_existing_game_to_front(
    tmp_path,
):

    state = LibraryState(
        tmp_path
        / "library-state.json"
    )

    first = FakeGame(
        name="First",
        rom=str(
            tmp_path
            / "first.nes"
        )
    )

    second = FakeGame(
        name="Second",
        rom=str(
            tmp_path
            / "second.nes"
        )
    )

    state.record_played(
        first
    )

    state.record_played(
        second
    )

    state.record_played(
        first
    )

    assert state.recent() == [
        game_identity(first),
        game_identity(second),
    ]


def test_recent_games_survive_new_state_instance(
    tmp_path,
):

    state_file = (
        tmp_path
        / "library-state.json"
    )

    game = FakeGame(
        name="Persistent",
        rom=str(
            tmp_path
            / "persistent.nes"
        )
    )

    first = LibraryState(
        state_file
    )

    first.record_played(
        game
    )

    second = LibraryState(
        state_file
    )

    assert second.recent() == [
        game_identity(game)
    ]


def test_record_played_preserves_favorites(
    tmp_path,
):

    state = LibraryState(
        tmp_path
        / "library-state.json"
    )

    favorite = FakeGame(
        name="Favorite",
        rom=str(
            tmp_path
            / "favorite.nes"
        )
    )

    played = FakeGame(
        name="Played",
        rom=str(
            tmp_path
            / "played.nes"
        )
    )

    state.set_favorite(
        favorite,
        True,
    )

    state.record_played(
        played
    )

    assert state.is_favorite(
        favorite
    )

    assert state.recent() == [
        game_identity(played)
    ]


def test_set_favorite_preserves_recent_history(
    tmp_path,
):

    state = LibraryState(
        tmp_path
        / "library-state.json"
    )

    played = FakeGame(
        name="Played",
        rom=str(
            tmp_path
            / "played.nes"
        )
    )

    favorite = FakeGame(
        name="Favorite",
        rom=str(
            tmp_path
            / "favorite.nes"
        )
    )

    state.record_played(
        played
    )

    state.set_favorite(
        favorite,
        True,
    )

    assert state.recent() == [
        game_identity(played)
    ]


def test_duplicate_stored_recent_entries_are_normalized(
    tmp_path,
):

    state_file = (
        tmp_path
        / "library-state.json"
    )

    identity = str(
        tmp_path
        / "duplicate.nes"
    )

    state_file.write_text(
        json.dumps(
            {
                "favorites": [],
                "recent": [
                    identity,
                    identity,
                ],
            }
        ),
        encoding="utf-8",
    )

    state = LibraryState(
        state_file
    )

    assert state.recent() == [
        identity
    ]


def test_non_list_recent_history_is_rejected(
    tmp_path,
):

    state_file = (
        tmp_path
        / "library-state.json"
    )

    state_file.write_text(
        json.dumps(
            {
                "favorites": [],
                "recent": "wrong",
            }
        ),
        encoding="utf-8",
    )

    state = LibraryState(
        state_file
    )

    with pytest.raises(
        ValueError,
        match=(
            "RetroVault Library recent "
            "history must contain a JSON list"
        ),
    ):
        state.recent()


def test_non_string_recent_identity_is_rejected(
    tmp_path,
):

    state_file = (
        tmp_path
        / "library-state.json"
    )

    state_file.write_text(
        json.dumps(
            {
                "favorites": [],
                "recent": [
                    123,
                ],
            }
        ),
        encoding="utf-8",
    )

    state = LibraryState(
        state_file
    )

    with pytest.raises(
        ValueError,
        match=(
            "RetroVault Library recent "
            "history must contain string identities"
        ),
    ):
        state.recent()


def test_recent_history_is_bounded(
    tmp_path,
):

    state = LibraryState(
        tmp_path
        / "library-state.json"
    )

    games = [
        FakeGame(
            name=f"Game {index}",
            rom=str(
                tmp_path
                / f"game-{index}.nes"
            )
        )
        for index in range(30)
    ]

    for game in games:
        state.record_played(
            game
        )

    recent = state.recent()

    assert len(recent) == 20

    assert recent[0] == (
        game_identity(
            games[-1]
        )
    )

    assert recent[-1] == (
        game_identity(
            games[-20]
        )
    )


class FakeRecordingState:
    def __init__(self):
        self.recorded = []

    def apply(
        self,
        games,
    ):
        return games

    def record_played(
        self,
        game,
    ):
        self.recorded.append(
            game
        )

        return (
            f"recorded:{game.name}"
        )


def test_library_service_record_played_delegates_to_state():

    from services.library.library_service import (
        LibraryService,
    )

    state = FakeRecordingState()

    service = LibraryService(
        library_state=state
    )

    game = FakeGame(
        name="Duck Tales 2",
        rom="/roms/duck-tales-2.nes",
    )

    result = service.record_played(
        game
    )

    assert state.recorded == [
        game
    ]

    assert result == (
        "recorded:Duck Tales 2"
    )


def test_library_service_recent_delegates_to_state():

    class RecentState:
        def apply(
            self,
            games,
        ):
            return games

        def recent(
            self,
            limit=20,
        ):
            return [
                f"recent:{limit}"
            ]

    from services.library.library_service import (
        LibraryService,
    )

    service = LibraryService(
        library_state=RecentState()
    )

    assert service.recent(
        limit=7
    ) == [
        "recent:7"
    ]


class FakeArtworkService:


    def __init__(
        self,
        artwork=None,
    ):

        self.artwork = artwork

        self.games = []


    def get_artwork(
        self,
        game,
    ):

        self.games.append(
            game
        )

        return self.artwork


def test_library_service_applies_artwork_after_build(
    monkeypatch,
    tmp_path,
):

    from services.library.library_service import (
        LibraryService,
    )

    game = FakeGame(
        name="Artwork Game",
        rom=str(
            tmp_path
            / "artwork-game.nes"
        ),
    )

    builder = FakeBuilder(
        [
            game
        ]
    )

    artwork_path = str(
        tmp_path
        / "cover.png"
    )

    artwork_service = FakeArtworkService(
        artwork_path
    )

    service = LibraryService(
        library_state=FakeState(),
        artwork_service=artwork_service,
    )

    service.builder = builder

    games = service.load()

    assert games == [
        game
    ]

    assert (
        game.artwork
        == artwork_path
    )

    assert artwork_service.games == [
        game
    ]


def test_library_service_clears_invalid_artwork(
    monkeypatch,
    tmp_path,
):

    from services.library.library_service import (
        LibraryService,
    )

    game = FakeGame(
        name="Missing Artwork",
        rom=str(
            tmp_path
            / "missing-artwork.nes"
        ),
    )

    game.artwork = "stale.png"

    builder = FakeBuilder(
        [
            game
        ]
    )

    artwork_service = FakeArtworkService(
        None
    )

    service = LibraryService(
        library_state=FakeState(),
        artwork_service=artwork_service,
    )

    service.builder = builder

    games = service.load()

    assert games == [
        game
    ]

    assert game.artwork == ""
