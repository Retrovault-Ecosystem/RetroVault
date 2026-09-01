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
            "platform.test.alpha": {
                "id": "platform.test.alpha",
                "type": "platform",
                "name": "Alpha System",
            },
            "platform.test.beta": {
                "id": "platform.test.beta",
                "type": "platform",
                "name": "Beta System",
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


def test_systems_page_initial_selection(
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

    assert page.cores_value.text() == (
        "None currently recorded"
    )

    assert page.emulators_value.text() == (
        "None currently recorded"
    )

    assert page.frontends_value.text() == (
        "None currently recorded"
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
