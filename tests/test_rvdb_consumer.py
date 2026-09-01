import json

import pytest

from services.rvdb.consumer import (
    RVDBConsumer,
    RVDBError,
)


@pytest.fixture
def bundle_path(tmp_path):
    path = tmp_path / "rvdb.bundle.json"

    data = {
        "nodes": {
            "platform.test.system": {
                "id": "platform.test.system",
                "type": "platform",
                "name": "Test System",
            },
            "core.test.core": {
                "id": "core.test.core",
                "type": "core",
                "name": "Test Core",
            },
            "emulator.test.emulator": {
                "id": "emulator.test.emulator",
                "type": "emulator",
                "name": "Test Emulator",
            },
            "frontend.test.frontend": {
                "id": "frontend.test.frontend",
                "type": "frontend",
                "name": "Test Frontend",
            },
        },
        "edges": {
            "platform.test.system": {
                "supports_core": [
                    "core.test.core",
                ],
            },
            "core.test.core": {},
            "emulator.test.emulator": {
                "supports_platform": [
                    "platform.test.system",
                ],
                "supports_core": [
                    "core.test.core",
                ],
            },
            "frontend.test.frontend": {
                "launches_core": [
                    "core.test.core",
                ],
            },
        },
    }

    path.write_text(
        json.dumps(data),
        encoding="utf-8",
    )

    return path


def test_load_bundle(bundle_path):
    consumer = RVDBConsumer(
        bundle_path
    )

    assert len(consumer.nodes) == 4
    assert len(consumer.edges) == 4


def test_get_entity(bundle_path):
    consumer = RVDBConsumer(
        bundle_path
    )

    entity = consumer.get_entity(
        "platform.test.system"
    )

    assert entity is not None
    assert entity["name"] == "Test System"


def test_supported_cores(bundle_path):
    consumer = RVDBConsumer(
        bundle_path
    )

    cores = consumer.supported_cores(
        "platform.test.system"
    )

    assert [
        core["id"]
        for core in cores
    ] == [
        "core.test.core",
    ]


def test_supported_emulators(bundle_path):
    consumer = RVDBConsumer(
        bundle_path
    )

    emulators = (
        consumer.supported_emulators(
            "platform.test.system"
        )
    )

    assert [
        emulator["id"]
        for emulator in emulators
    ] == [
        "emulator.test.emulator",
    ]


def test_frontends_for_core(bundle_path):
    consumer = RVDBConsumer(
        bundle_path
    )

    frontends = (
        consumer.frontends_for_core(
            "core.test.core"
        )
    )

    assert [
        frontend["id"]
        for frontend in frontends
    ] == [
        "frontend.test.frontend",
    ]


def test_platform_view(bundle_path):
    consumer = RVDBConsumer(
        bundle_path
    )

    view = consumer.platform_view(
        "platform.test.system"
    )

    assert (
        view["platform"]["id"]
        == "platform.test.system"
    )

    assert [
        core["id"]
        for core in view["cores"]
    ] == [
        "core.test.core",
    ]

    assert [
        emulator["id"]
        for emulator in view["emulators"]
    ] == [
        "emulator.test.emulator",
    ]

    assert [
        frontend["id"]
        for frontend in view["frontends"]
    ] == [
        "frontend.test.frontend",
    ]


def test_missing_bundle(tmp_path):
    with pytest.raises(
        RVDBError,
        match="bundle not found",
    ):
        RVDBConsumer(
            tmp_path / "missing.json"
        )


def test_invalid_contract(tmp_path):
    path = tmp_path / "invalid.json"

    path.write_text(
        json.dumps(
            {
                "nodes": {},
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        RVDBError,
        match="exactly 'nodes' and 'edges'",
    ):
        RVDBConsumer(path)
