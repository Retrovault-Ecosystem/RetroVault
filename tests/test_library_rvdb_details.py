from types import SimpleNamespace

import pytest

from PyQt6.QtWidgets import QApplication

from services.rvdb import (
    RVDBConsumer,
)

from ui.library.details.game_details import (
    GameDetails,
)

from ui.pages.library_page import (
    LibraryPage,
)


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()

    if instance is None:
        instance = QApplication([])

    return instance


def make_game(
    *,
    name="Test Game",
    platform="Fallback Platform",
    core="test_core",
    rvdb_platform_id=None,
):
    return SimpleNamespace(
        name=name,
        platform=platform,
        year=None,
        genre=None,
        core=core,
        rom="/tmp/test.rom",
        source=None,
        artwork=None,
        favorite=False,
        rvdb_platform_id=rvdb_platform_id,
    )


def test_library_page_propagates_rvdb_consumer(
    app,
):
    consumer = RVDBConsumer(
        "data/rvdb/rvdb.bundle.json"
    )

    page = LibraryPage(
        [],
        consumer,
    )

    assert page.rvdb_consumer is consumer
    assert page.details.rvdb_consumer is consumer


def test_identified_game_displays_canonical_rvdb_platform(
    app,
):
    consumer = RVDBConsumer(
        "data/rvdb/rvdb.bundle.json"
    )

    details = GameDetails(
        rvdb_consumer=consumer
    )

    game = make_game(
        name="Canonical NES Test",
        platform=(
            "Nintendo Entertainment System"
        ),
        core="fceumm_libretro.so",
        rvdb_platform_id=(
            "platform.nintendo.nes"
        ),
    )

    details.show_game(game)

    text = details.metadata.text()

    assert (
        "System: Nintendo Entertainment System"
        in text
    )
    assert "Core: fceumm_libretro.so" in text
    assert "RVDB Platform:" in text
    assert (
        "Nintendo Entertainment System"
        in text
    )
    assert (
        "RVDB ID: platform.nintendo.nes"
        in text
    )
    assert "Platform Release: 1983" in text


def test_n64_identity_uses_same_production_contract(
    app,
):
    consumer = RVDBConsumer(
        "data/rvdb/rvdb.bundle.json"
    )

    details = GameDetails(
        rvdb_consumer=consumer
    )

    game = make_game(
        name="Canonical N64 Test",
        platform="Nintendo 64",
        core="mupen64plus_next_libretro.so",
        rvdb_platform_id=(
            "platform.nintendo.n64"
        ),
    )

    details.show_game(game)

    text = details.metadata.text()

    assert "RVDB Platform:" in text
    assert "Nintendo 64" in text
    assert (
        "RVDB ID: platform.nintendo.n64"
        in text
    )
    assert "Platform Release: 1996" in text


def test_unidentified_game_preserves_fallback_details(
    app,
):
    details = GameDetails(
        rvdb_consumer=None
    )

    game = make_game(
        name="Fallback Test",
        platform="Super Nintendo",
        core="snes9x_libretro.so",
        rvdb_platform_id=None,
    )

    details.show_game(game)

    text = details.metadata.text()

    assert "System: Super Nintendo" in text
    assert "Core: snes9x_libretro.so" in text
    assert "RVDB Platform:" not in text
    assert "RVDB ID:" not in text


def test_identified_game_without_consumer_is_safe(
    app,
):
    details = GameDetails(
        rvdb_consumer=None
    )

    game = make_game(
        platform=(
            "Nintendo Entertainment System"
        ),
        rvdb_platform_id=(
            "platform.nintendo.nes"
        ),
    )

    details.show_game(game)

    text = details.metadata.text()

    assert (
        "System: Nintendo Entertainment System"
        in text
    )
    assert "RVDB Platform:" not in text


class MissingPlatformConsumer:
    def platform_view(
        self,
        platform_id,
    ):
        from services.rvdb import RVDBError

        raise RVDBError(
            f"Missing platform: {platform_id}"
        )


def test_missing_rvdb_entity_preserves_fallback_details(
    app,
):
    details = GameDetails(
        rvdb_consumer=MissingPlatformConsumer()
    )

    game = make_game(
        platform="Fallback Platform",
        rvdb_platform_id=(
            "platform.missing"
        ),
    )

    details.show_game(game)

    text = details.metadata.text()

    assert "System: Fallback Platform" in text
    assert "RVDB Platform:" not in text
    assert "RVDB ID:" not in text
