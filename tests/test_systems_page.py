import json

import pytest

pytest.importorskip(
    "PyQt6"
)

from PyQt6.QtWidgets import QApplication

from services.rvdb import RVDBConsumer
from ui.pages.systems_page import SystemsPage


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()

    if instance is None:
        instance = QApplication([])

    return instance


@pytest.fixture
def consumer(tmp_path):
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

    return RVDBConsumer(bundle)


def test_systems_page_lists_platforms(
    app,
    consumer,
):
    page = SystemsPage(
        consumer
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
    consumer,
):
    page = SystemsPage(
        consumer
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
    consumer,
):
    page = SystemsPage(
        consumer
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
    consumer,
):
    page = SystemsPage(
        consumer
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
        "No RVDB consumer was supplied."
    )


def test_systems_page_real_snes_contract(
    app,
):
    consumer = RVDBConsumer(
        "data/rvdb/rvdb.bundle.json"
    )

    page = SystemsPage(
        consumer
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

    assert page.emulators_value.text() == (
        "Snes9x"
    )
    assert page.frontends_value.text() == (
        "RetroArch"
    )
