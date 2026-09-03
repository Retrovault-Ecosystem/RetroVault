from dataclasses import dataclass

from services.artwork import ArtworkService


@dataclass
class FakeGame:

    name: str = "Game"

    platform: str = "NES"

    rom: str = ""

    artwork: str = ""


def test_missing_artwork_returns_none():

    service = ArtworkService()

    game = FakeGame()

    assert (
        service.get_artwork(
            game
        )
        is None
    )


def test_nonexistent_artwork_returns_none(
    tmp_path,
):

    service = ArtworkService()

    game = FakeGame(
        rom=str(
            tmp_path
            / "game.nes"
        ),
        artwork=str(
            tmp_path
            / "missing.png"
        ),
    )

    assert (
        service.get_artwork(
            game
        )
        is None
    )


def test_existing_artwork_is_returned(
    tmp_path,
):

    artwork = (
        tmp_path
        / "cover.png"
    )

    artwork.write_bytes(
        b"cover"
    )

    game = FakeGame(
        rom=str(
            tmp_path
            / "game.nes"
        ),
        artwork=str(
            artwork
        ),
    )

    service = ArtworkService()

    assert (
        service.get_artwork(
            game
        )
        == str(
            artwork
        )
    )


def test_cache_uses_rom_identity_not_name(
    tmp_path,
):

    first_artwork = (
        tmp_path
        / "first.png"
    )

    second_artwork = (
        tmp_path
        / "second.png"
    )

    first_artwork.write_bytes(
        b"first"
    )

    second_artwork.write_bytes(
        b"second"
    )

    first = FakeGame(
        name="Same Name",
        platform="NES",
        rom=str(
            tmp_path
            / "first.nes"
        ),
        artwork=str(
            first_artwork
        ),
    )

    second = FakeGame(
        name="Same Name",
        platform="SNES",
        rom=str(
            tmp_path
            / "second.sfc"
        ),
        artwork=str(
            second_artwork
        ),
    )

    service = ArtworkService()

    assert (
        service.get_artwork(
            first
        )
        == str(
            first_artwork
        )
    )

    assert (
        service.get_artwork(
            second
        )
        == str(
            second_artwork
        )
    )

    assert len(
        service.cache
    ) == 2


def test_cached_artwork_uses_same_game_identity(
    tmp_path,
):

    artwork = (
        tmp_path
        / "cover.png"
    )

    artwork.write_bytes(
        b"cover"
    )

    rom = str(
        tmp_path
        / "game.nes"
    )

    first = FakeGame(
        name="Original Name",
        rom=rom,
        artwork=str(
            artwork
        ),
    )

    service = ArtworkService()

    assert (
        service.get_artwork(
            first
        )
        == str(
            artwork
        )
    )

    second = FakeGame(
        name="Changed Display Name",
        rom=rom,
        artwork="",
    )

    assert (
        service.get_artwork(
            second
        )
        == str(
            artwork
        )
    )
