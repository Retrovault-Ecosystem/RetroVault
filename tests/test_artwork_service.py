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


def test_discovers_exact_rom_stem_recursively(
    tmp_path,
):

    root = (
        tmp_path
        / "artwork"
    )

    nested = (
        root
        / "Nintendo Entertainment System"
    )

    nested.mkdir(
        parents=True
    )

    cover = (
        nested
        / "Duck Tales 2 (U).png"
    )

    cover.write_bytes(
        b"cover"
    )

    game = FakeGame(
        name="Duck Tales 2 (U)",
        rom=str(
            tmp_path
            / "Duck Tales 2 (U).nes"
        ),
    )

    service = ArtworkService(
        directory=root
    )

    assert (
        service.get_artwork(
            game
        )
        == str(
            cover
        )
    )


def test_discovery_is_case_insensitive(
    tmp_path,
):

    root = (
        tmp_path
        / "artwork"
    )

    root.mkdir()

    cover = (
        root
        / "DUCK TALES 2 (U).JPG"
    )

    cover.write_bytes(
        b"cover"
    )

    game = FakeGame(
        name="Duck Tales 2 (U)",
        rom=str(
            tmp_path
            / "duck tales 2 (u).nes"
        ),
    )

    service = ArtworkService(
        directory=root
    )

    assert (
        service.get_artwork(
            game
        )
        == str(
            cover
        )
    )


def test_discovery_ignores_wrong_filename(
    tmp_path,
):

    root = (
        tmp_path
        / "artwork"
    )

    root.mkdir()

    (
        root
        / "Duck Tales.png"
    ).write_bytes(
        b"cover"
    )

    game = FakeGame(
        name="Duck Tales 2",
        rom=str(
            tmp_path
            / "Duck Tales 2.nes"
        ),
    )

    service = ArtworkService(
        directory=root
    )

    assert (
        service.get_artwork(
            game
        )
        is None
    )


def test_discovery_ignores_unsupported_image_extension(
    tmp_path,
):

    root = (
        tmp_path
        / "artwork"
    )

    root.mkdir()

    (
        root
        / "Duck Tales 2.bmp"
    ).write_bytes(
        b"cover"
    )

    game = FakeGame(
        name="Duck Tales 2",
        rom=str(
            tmp_path
            / "Duck Tales 2.nes"
        ),
    )

    service = ArtworkService(
        directory=root
    )

    assert (
        service.get_artwork(
            game
        )
        is None
    )


def test_ambiguous_same_stem_artwork_is_not_selected(
    tmp_path,
):

    root = (
        tmp_path
        / "artwork"
    )

    first = (
        root
        / "NES"
    )

    second = (
        root
        / "Arcade"
    )

    first.mkdir(
        parents=True
    )

    second.mkdir(
        parents=True
    )

    (
        first
        / "Same Game.png"
    ).write_bytes(
        b"first"
    )

    (
        second
        / "Same Game.jpg"
    ).write_bytes(
        b"second"
    )

    game = FakeGame(
        name="Same Game",
        rom=str(
            tmp_path
            / "Same Game.nes"
        ),
    )

    service = ArtworkService(
        directory=root
    )

    assert (
        service.get_artwork(
            game
        )
        is None
    )


def test_explicit_valid_artwork_beats_local_discovery(
    tmp_path,
):

    root = (
        tmp_path
        / "artwork"
    )

    root.mkdir()

    discovered = (
        root
        / "Duck Tales 2.png"
    )

    discovered.write_bytes(
        b"discovered"
    )

    explicit = (
        tmp_path
        / "explicit.png"
    )

    explicit.write_bytes(
        b"explicit"
    )

    game = FakeGame(
        name="Duck Tales 2",
        rom=str(
            tmp_path
            / "Duck Tales 2.nes"
        ),
        artwork=str(
            explicit
        ),
    )

    service = ArtworkService(
        directory=root
    )

    assert (
        service.get_artwork(
            game
        )
        == str(
            explicit
        )
    )


def test_missing_artwork_directory_is_safe(
    tmp_path,
):

    game = FakeGame(
        name="Duck Tales 2",
        rom=str(
            tmp_path
            / "Duck Tales 2.nes"
        ),
    )

    service = ArtworkService(
        directory=(
            tmp_path
            / "missing"
        )
    )

    assert (
        service.get_artwork(
            game
        )
        is None
    )
