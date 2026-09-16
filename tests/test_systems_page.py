import json

import pytest

pytest.importorskip(
    "PyQt6"
)

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

from services.rvdb import (
    RVDBConsumer,
    RVDBService,
)
from ui.pages.systems_page import SystemsPage


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()

    if instance is None:
        instance = QApplication([])

    return instance


@pytest.fixture
def service(tmp_path):
    bundle = tmp_path / "rvdb.bundle.json"

    data = {
        "nodes": {
            "manufacturer.test": {
                "id": "manufacturer.test",
                "type": "manufacturer",
                "name": "Test Hardware",
            },
            "platform.test.alpha": {
                "id": "platform.test.alpha",
                "type": "platform",
                "name": "Alpha System",
                "aliases": [
                    "Alpha",
                    "AS",
                ],
                "category": [
                    "console",
                ],
                "manufacturer": [
                    "manufacturer.test",
                ],
                "release_year": 1994,
                "generation": 5,
                "media": [
                    "optical-disc",
                ],
                "extensions": [
                    "cue",
                    "chd",
                ],
                "metadata": {
                    "retroarch_supported": True,
                },
            },
            "platform.test.beta": {
                "id": "platform.test.beta",
                "type": "platform",
                "name": "Beta System",
                "aliases": [],
                "category": [
                    "handheld",
                ],
                "manufacturer": [],
                "release_year": None,
                "metadata": {},
            },
            "core.test.alpha": {
                "id": "core.test.alpha",
                "type": "core",
                "name": "Alpha Core",
            },
            "emulator.test.alpha": {
                "id": "emulator.test.alpha",
                "type": "emulator",
                "name": "Alpha Emulator",
            },
            "frontend.test.alpha": {
                "id": "frontend.test.alpha",
                "type": "frontend",
                "name": "Alpha Frontend",
            },
        },
        "edges": {
            "manufacturer.test": {},
            "platform.test.alpha": {
                "supports_core": [
                    "core.test.alpha",
                ],
            },
            "platform.test.beta": {},
            "core.test.alpha": {},
            "emulator.test.alpha": {
                "supports_platform": [
                    "platform.test.alpha",
                ],
            },
            "frontend.test.alpha": {
                "launches_core": [
                    "core.test.alpha",
                ],
            },
        },
    }

    bundle.write_text(
        json.dumps(data),
        encoding="utf-8",
    )

    return RVDBService(
        RVDBConsumer(bundle)
    )


def test_systems_page_lists_platforms(
    app,
    service,
):
    page = SystemsPage(
        service
    )

    assert page.system_list.count() == 2
    assert page.count_label.text() == (
        "2 platforms"
    )
    assert page.system_list.item(
        0
    ).text() == "Alpha System"
    assert page.system_list.item(
        1
    ).text() == "Beta System"


def test_systems_page_displays_metadata(
    app,
    service,
):
    page = SystemsPage(
        service
    )

    assert page.name_label.text() == (
        "Alpha System"
    )
    assert page.id_label.text() == (
        "platform.test.alpha"
    )
    assert page.category_value.text() == (
        "console"
    )
    assert page.manufacturer_value.text() == (
        "Test Hardware"
    )
    assert page.release_year_value.text() == (
        "1994"
    )
    assert page.generation_value.text() == (
        "5"
    )
    assert page.media_value.text() == (
        "optical-disc"
    )
    assert page.extensions_value.text() == (
        ".chd, .cue"
    )
    assert page.aliases_value.text() == (
        "Alpha, AS"
    )
    assert page.retroarch_value.text() == (
        "Supported"
    )


def test_systems_page_displays_relationships(
    app,
    service,
):
    page = SystemsPage(
        service
    )

    assert page.cores_value.text() == (
        "Alpha Core"
    )
    assert page.emulators_value.text() == (
        "Alpha Emulator"
    )
    assert page.frontends_value.text() == (
        "Alpha Frontend"
    )


def test_systems_page_changes_selection(
    app,
    service,
):
    page = SystemsPage(
        service
    )

    page.system_list.setCurrentRow(
        1
    )

    app.processEvents()

    assert page.name_label.text() == (
        "Beta System"
    )
    assert page.category_value.text() == (
        "handheld"
    )
    assert page.manufacturer_value.text() == (
        SystemsPage.EMPTY
    )
    assert page.release_year_value.text() == (
        SystemsPage.EMPTY
    )
    assert page.media_value.text() == (
        SystemsPage.EMPTY
    )
    assert page.extensions_value.text() == (
        SystemsPage.EMPTY
    )
    assert page.aliases_value.text() == (
        SystemsPage.EMPTY
    )
    assert page.retroarch_value.text() == (
        SystemsPage.EMPTY
    )
    assert page.cores_value.text() == (
        SystemsPage.EMPTY
    )
    assert page.emulators_value.text() == (
        SystemsPage.EMPTY
    )
    assert page.frontends_value.text() == (
        SystemsPage.EMPTY
    )


def test_systems_page_handles_no_consumer(
    app,
):
    page = SystemsPage(None)

    assert page.system_list.count() == 0
    assert page.count_label.text() == (
        "RVDB unavailable"
    )
    assert page.status_label.text() == (
        "No RVDB service was supplied."
    )


def test_systems_page_real_snes_contract(
    app,
):
    service = RVDBService.from_bundle(
        "data/rvdb/rvdb.bundle.json"
    )

    page = SystemsPage(
        service
    )

    target = None

    for row in range(
        page.system_list.count()
    ):
        item = page.system_list.item(
            row
        )

        if item.text() == "Super Nintendo":
            target = row
            break

    assert target is not None

    page.system_list.setCurrentRow(
        target
    )

    app.processEvents()

    assert page.name_label.text() == (
        "Super Nintendo"
    )
    assert page.manufacturer_value.text() == (
        "Nintendo"
    )
    assert page.retroarch_value.text() == (
        "Supported"
    )

    assert set(
        page.cores_value
        .text()
        .splitlines()
    ) == {
        "bsnes",
        "Snes9x",
    }

    assert set(
        page.emulators_value
        .text()
        .splitlines()
    ) == {
        "bsnes",
        "Snes9x",
    }
    assert page.frontends_value.text() == (
        "RetroArch"
    )


def test_systems_page_searches_by_name(
    app,
    service,
):
    page = SystemsPage(
        service
    )

    page.search_input.setText(
        "beta"
    )

    app.processEvents()

    assert page.system_list.count() == 1
    assert page.system_list.item(
        0
    ).text() == "Beta System"
    assert page.name_label.text() == (
        "Beta System"
    )
    assert page.count_label.text() == (
        "1 of 2 platforms"
    )


def test_systems_page_searches_by_alias(
    app,
    service,
):
    page = SystemsPage(
        service
    )

    page.search_input.setText(
        "AS"
    )

    app.processEvents()

    assert page.system_list.count() == 1
    assert page.system_list.item(
        0
    ).text() == "Alpha System"


def test_systems_page_filters_by_category(
    app,
    service,
):
    page = SystemsPage(
        service
    )

    index = page.category_filter.findText(
        "handheld"
    )

    assert index >= 0

    page.category_filter.setCurrentIndex(
        index
    )

    app.processEvents()

    assert page.system_list.count() == 1
    assert page.system_list.item(
        0
    ).text() == "Beta System"
    assert page.count_label.text() == (
        "1 of 2 platforms"
    )


def test_systems_page_combines_search_and_category(
    app,
    service,
):
    page = SystemsPage(
        service
    )

    index = page.category_filter.findText(
        "console"
    )

    assert index >= 0

    page.category_filter.setCurrentIndex(
        index
    )
    page.search_input.setText(
        "beta"
    )

    app.processEvents()

    assert page.system_list.count() == 0
    assert page.count_label.text() == (
        "0 of 2 platforms"
    )


def test_systems_page_real_category_contract(
    app,
):
    service = RVDBService.from_bundle(
        "data/rvdb/rvdb.bundle.json"
    )

    page = SystemsPage(
        service
    )

    expected = {
        "All Categories",
        "arcade",
        "computer",
        "console",
        "handheld",
    }

    actual = {
        page.category_filter.itemText(
            index
        )
        for index in range(
            page.category_filter.count()
        )
    }

    assert actual == expected


def test_systems_page_displays_local_library_counts(
    app,
    service,
):
    from types import SimpleNamespace

    games = [
        SimpleNamespace(
            rvdb_platform_id=(
                "platform.test.alpha"
            ),
            favorite=True,
        ),
        SimpleNamespace(
            rvdb_platform_id=(
                "platform.test.alpha"
            ),
            favorite=False,
        ),
        SimpleNamespace(
            rvdb_platform_id=(
                "platform.test.beta"
            ),
            favorite=True,
        ),
    ]

    page = SystemsPage(
        service,
        games_provider=lambda: games,
    )

    assert (
        page.library_games_value.text()
        == "2"
    )
    assert (
        page.library_favorites_value.text()
        == "1"
    )

    page.system_list.setCurrentRow(
        1
    )
    app.processEvents()

    assert (
        page.library_games_value.text()
        == "1"
    )
    assert (
        page.library_favorites_value.text()
        == "1"
    )


def test_systems_page_displays_zero_for_platform_not_in_library(
    app,
    service,
):
    page = SystemsPage(
        service,
        games_provider=lambda: [],
    )

    assert (
        page.library_games_value.text()
        == "0"
    )
    assert (
        page.library_favorites_value.text()
        == "0"
    )


def test_systems_page_library_counts_require_canonical_platform_identity(
    app,
    service,
):
    from types import SimpleNamespace

    games = [
        SimpleNamespace(
            platform="Alpha System",
            rvdb_platform_id="",
            favorite=True,
        ),
    ]

    page = SystemsPage(
        service,
        games_provider=lambda: games,
    )

    assert (
        page.library_games_value.text()
        == "0"
    )
    assert (
        page.library_favorites_value.text()
        == "0"
    )


def test_systems_page_without_library_provider_is_safe(
    app,
    service,
):
    page = SystemsPage(
        service
    )

    assert (
        page.library_games_value.text()
        == SystemsPage.EMPTY
    )
    assert (
        page.library_favorites_value.text()
        == SystemsPage.EMPTY
    )


def test_systems_page_library_provider_failure_is_safe(
    app,
    service,
):
    def fail():
        raise RuntimeError(
            "library unavailable"
        )

    page = SystemsPage(
        service,
        games_provider=fail,
    )

    assert (
        page.library_games_value.text()
        == SystemsPage.EMPTY
    )
    assert (
        page.library_favorites_value.text()
        == SystemsPage.EMPTY
    )


def test_systems_page_refresh_page_updates_live_library_counts(
    app,
    service,
):
    from types import SimpleNamespace

    games = [
        SimpleNamespace(
            rvdb_platform_id=(
                "platform.test.alpha"
            ),
            favorite=False,
        ),
    ]

    page = SystemsPage(
        service,
        games_provider=lambda: games,
    )

    assert (
        page.library_games_value.text()
        == "1"
    )
    assert (
        page.library_favorites_value.text()
        == "0"
    )

    games.append(
        SimpleNamespace(
            rvdb_platform_id=(
                "platform.test.alpha"
            ),
            favorite=True,
        )
    )

    page.refresh_page()

    assert (
        page.library_games_value.text()
        == "2"
    )
    assert (
        page.library_favorites_value.text()
        == "1"
    )


def test_systems_page_refresh_page_preserves_selection(
    app,
    service,
):
    from types import SimpleNamespace

    games = [
        SimpleNamespace(
            rvdb_platform_id=(
                "platform.test.beta"
            ),
            favorite=True,
        ),
    ]

    page = SystemsPage(
        service,
        games_provider=lambda: games,
    )

    page.system_list.setCurrentRow(
        1
    )
    app.processEvents()

    selected = (
        page.system_list
        .currentItem()
        .data(
            Qt.ItemDataRole.UserRole
        )
    )

    page.refresh_page()

    assert (
        page.system_list
        .currentItem()
        .data(
            Qt.ItemDataRole.UserRole
        )
        == selected
    )
    assert (
        page.library_games_value.text()
        == "1"
    )
    assert (
        page.library_favorites_value.text()
        == "1"
    )


def test_systems_page_refresh_page_without_selection_is_safe(
    app,
    service,
):
    page = SystemsPage(
        service,
        games_provider=lambda: [],
    )

    page.system_list.clearSelection()
    page.system_list.setCurrentItem(
        None
    )

    page.refresh_page()


def test_systems_page_library_action_emits_selected_platform(
    app,
    service,
):
    from types import SimpleNamespace

    games = [
        SimpleNamespace(
            rvdb_platform_id=(
                "platform.test.alpha"
            ),
            favorite=False,
        ),
    ]

    page = SystemsPage(
        service,
        games_provider=lambda: games,
    )

    requested = []

    page.library_requested.connect(
        requested.append
    )

    assert (
        page.view_library_button.isEnabled()
        is True
    )

    page.view_library_button.click()

    assert requested == [
        "platform.test.alpha"
    ]


def test_systems_page_library_action_disabled_without_games(
    app,
    service,
):
    page = SystemsPage(
        service,
        games_provider=lambda: [],
    )

    requested = []

    page.library_requested.connect(
        requested.append
    )

    assert (
        page.view_library_button.isEnabled()
        is False
    )

    page.view_library_button.click()

    assert requested == []


def test_systems_page_favorites_action_emits_selected_platform(
    app,
    service,
):
    from types import SimpleNamespace

    games = [
        SimpleNamespace(
            rvdb_platform_id=(
                "platform.test.alpha"
            ),
            favorite=True,
        ),
    ]

    page = SystemsPage(
        service,
        games_provider=lambda: games,
    )

    requested = []

    page.library_favorites_requested.connect(
        requested.append
    )

    assert (
        page.view_favorites_button.isEnabled()
        is True
    )

    page.view_favorites_button.click()

    assert requested == [
        "platform.test.alpha"
    ]


def test_systems_page_favorites_action_disabled_without_favorites(
    app,
    service,
):
    from types import SimpleNamespace

    games = [
        SimpleNamespace(
            rvdb_platform_id=(
                "platform.test.alpha"
            ),
            favorite=False,
        ),
    ]

    page = SystemsPage(
        service,
        games_provider=lambda: games,
    )

    requested = []

    page.library_favorites_requested.connect(
        requested.append
    )

    assert (
        page.view_library_button.isEnabled()
        is True
    )

    assert (
        page.view_favorites_button.isEnabled()
        is False
    )

    page.view_favorites_button.click()

    assert requested == []


def test_systems_page_recent_action_emits_selected_platform(
    app,
    service,
):
    from types import SimpleNamespace

    game = SimpleNamespace(
        rvdb_platform_id=(
            "platform.test.alpha"
        ),
        favorite=False,
        rom="/roms/alpha-recent.rom",
    )

    page = SystemsPage(
        service,
        games_provider=lambda: [
            game
        ],
        recent_provider=lambda: [
            game.rom
        ],
    )

    requested = []

    page.library_recent_requested.connect(
        requested.append
    )

    assert (
        page.library_recent_value.text()
        == "1"
    )

    assert (
        page.view_recent_button.isEnabled()
        is True
    )

    page.view_recent_button.click()

    assert requested == [
        "platform.test.alpha"
    ]


def test_systems_page_recent_action_disabled_without_local_games(
    app,
    service,
):
    page = SystemsPage(
        service,
        games_provider=lambda: [],
    )

    requested = []

    page.library_recent_requested.connect(
        requested.append
    )

    assert (
        page.view_recent_button.isEnabled()
        is False
    )

    page.view_recent_button.click()

    assert requested == []


def test_systems_page_shows_live_recent_count_for_selected_platform(
    app,
    service,
):
    from types import SimpleNamespace

    alpha_recent = SimpleNamespace(
        rvdb_platform_id="platform.test.alpha",
        favorite=False,
        rom="/roms/alpha-recent.rom",
    )
    alpha_other = SimpleNamespace(
        rvdb_platform_id="platform.test.alpha",
        favorite=False,
        rom="/roms/alpha-other.rom",
    )
    beta_recent = SimpleNamespace(
        rvdb_platform_id="platform.test.beta",
        favorite=False,
        rom="/roms/beta-recent.rom",
    )

    games = [
        alpha_recent,
        alpha_other,
        beta_recent,
    ]

    page = SystemsPage(
        service,
        games_provider=lambda: games,
        recent_provider=lambda: [
            beta_recent.rom,
            alpha_recent.rom,
        ],
    )

    assert page.library_recent_value.text() == "1"
    assert page.view_recent_button.isEnabled() is True


def test_systems_page_recent_count_uses_rom_identity_not_game_name(
    app,
    service,
):
    from types import SimpleNamespace

    game = SimpleNamespace(
        name="Recent Game",
        rvdb_platform_id="platform.test.alpha",
        favorite=False,
        rom="/roms/recent-game.rom",
    )

    page = SystemsPage(
        service,
        games_provider=lambda: [game],
        recent_provider=lambda: [
            "Recent Game"
        ],
    )

    assert page.library_recent_value.text() == "0"
    assert page.view_recent_button.isEnabled() is False


def test_systems_page_recent_count_without_provider_is_safe(
    app,
    service,
):
    from types import SimpleNamespace

    game = SimpleNamespace(
        rvdb_platform_id="platform.test.alpha",
        favorite=False,
        rom="/roms/alpha.rom",
    )

    page = SystemsPage(
        service,
        games_provider=lambda: [game],
    )

    assert (
        page.library_recent_value.text()
        == page.EMPTY
    )
    assert page.view_recent_button.isEnabled() is False


def test_systems_page_recent_provider_failure_is_safe(
    app,
    service,
):
    from types import SimpleNamespace

    game = SimpleNamespace(
        rvdb_platform_id="platform.test.alpha",
        favorite=False,
        rom="/roms/alpha.rom",
    )

    def failing_recent_provider():
        raise RuntimeError(
            "recent state unavailable"
        )

    page = SystemsPage(
        service,
        games_provider=lambda: [game],
        recent_provider=failing_recent_provider,
    )

    assert (
        page.library_recent_value.text()
        == page.EMPTY
    )
    assert page.view_recent_button.isEnabled() is False


def test_systems_page_refresh_updates_recent_count_live(
    app,
    service,
):
    from types import SimpleNamespace

    game = SimpleNamespace(
        rvdb_platform_id="platform.test.alpha",
        favorite=False,
        rom="/roms/alpha.rom",
    )

    recent = []

    page = SystemsPage(
        service,
        games_provider=lambda: [game],
        recent_provider=lambda: list(recent),
    )

    assert page.library_recent_value.text() == "0"
    assert page.view_recent_button.isEnabled() is False

    recent.append(
        game.rom
    )

    page.refresh_page()

    assert page.library_recent_value.text() == "1"
    assert page.view_recent_button.isEnabled() is True


def test_systems_page_collection_action_emits_selected_platform(
    app,
    service,
):
    from types import SimpleNamespace

    page = SystemsPage(
        service,
        games_provider=lambda: [
            SimpleNamespace(
                rvdb_platform_id="platform.test.alpha",
                favorite=False,
                rom="/roms/alpha.rom",
            )
        ],
    )

    current = page.system_list.currentItem()

    assert current is not None

    platform_id = str(
        current.data(
            Qt.ItemDataRole.UserRole
        )
    )

    page.collection_names_provider = (
        lambda: ["Classics"]
    )
    page.collection_games_provider = (
        lambda name: [
            SimpleNamespace(
                rvdb_platform_id=platform_id,
                rom="/roms/alpha.rom",
            )
        ]
    )

    page.refresh_page()

    assert page.library_collections_value.text() == "1"
    assert page.view_collections_button.isEnabled()

    emitted = []

    page.library_collections_requested.connect(
        emitted.append
    )

    page.view_collections_button.click()

    assert emitted == [platform_id]


def test_systems_page_collection_action_disabled_without_matching_collection(
    app,
    service,
):
    from types import SimpleNamespace

    page = SystemsPage(
        service,
        games_provider=lambda: [
            SimpleNamespace(
                rvdb_platform_id="platform.test.alpha",
                favorite=False,
                rom="/roms/alpha.rom",
            )
        ],
    )

    current = page.system_list.currentItem()

    assert current is not None

    platform_id = str(
        current.data(
            Qt.ItemDataRole.UserRole
        )
    )

    page.collection_names_provider = (
        lambda: ["Other"]
    )
    page.collection_games_provider = (
        lambda name: [
            SimpleNamespace(
                rvdb_platform_id="platform.other",
                rom="/roms/other.rom",
            )
        ]
    )

    page.refresh_page()

    assert page.library_collections_value.text() == "0"
    assert not page.view_collections_button.isEnabled()

    emitted = []

    page.library_collections_requested.connect(
        emitted.append
    )

    page.view_collections_button.click()

    assert emitted == []
