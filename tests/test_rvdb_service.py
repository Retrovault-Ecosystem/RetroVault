from __future__ import annotations

import json

import pytest

from services.rvdb.consumer import (
    RVDBConsumer,
    RVDBError,
)
from services.rvdb.models import (
    RVDBEntityRef,
    RVDBPlatformMetadata,
    RVDBPlatformSummary,
)
from services.rvdb.service import (
    RVDBService,
)


REAL_BUNDLE = (
    "data/rvdb/rvdb.bundle.json"
)


def test_service_real_snes_contract():
    service = RVDBService.from_bundle(
        REAL_BUNDLE
    )

    view = service.platform_view(
        "platform.nintendo.snes"
    )

    assert isinstance(
        view.platform,
        RVDBPlatformMetadata,
    )

    assert view.platform.id == (
        "platform.nintendo.snes"
    )

    assert view.platform.name == (
        "Super Nintendo"
    )

    assert [
        ref.name
        for ref in view.platform.manufacturers
    ] == [
        "Nintendo"
    ]

    assert view.platform.retroarch_supported is True

    assert {
        ref.id
        for ref in view.cores
    } == {
        "core.bsnes",
        "core.snes9x",
    }

    assert {
        ref.id
        for ref in view.emulators
    } == {
        "emulator.bsnes",
        "emulator.snes9x",
    }

    assert [
        ref.id
        for ref in view.frontends
    ] == [
        "frontend.retroarch"
    ]


def test_service_lists_real_platforms():
    service = RVDBService.from_bundle(
        REAL_BUNDLE
    )

    platforms = service.platforms()

    assert platforms

    assert all(
        isinstance(
            platform,
            RVDBPlatformSummary,
        )
        for platform in platforms
    )

    ids = {
        platform.id
        for platform in platforms
    }

    assert "platform.nintendo.snes" in ids

    names = [
        platform.name
        for platform in platforms
    ]

    assert names == sorted(
        names,
        key=str.casefold,
    )


def test_service_platform_summary_preserves_search_fields(
    tmp_path,
):
    bundle = tmp_path / "rvdb.bundle.json"

    bundle.write_text(
        json.dumps(
            {
                "nodes": {
                    "platform.test": {
                        "id": "platform.test",
                        "type": "platform",
                        "name": "Test Platform",
                        "aliases": [
                            "Test Alias",
                        ],
                        "category": [
                            "console",
                        ],
                    },
                },
                "edges": {},
            }
        ),
        encoding="utf-8",
    )

    service = RVDBService.from_bundle(
        bundle
    )

    assert service.platforms() == (
        RVDBPlatformSummary(
            id="platform.test",
            name="Test Platform",
            aliases=(
                "Test Alias",
            ),
            categories=(
                "console",
            ),
        ),
    )


def test_service_resolves_manufacturer_refs(
    tmp_path,
):
    bundle = tmp_path / "rvdb.bundle.json"

    bundle.write_text(
        json.dumps(
            {
                "nodes": {
                    "manufacturer.test": {
                        "id": "manufacturer.test",
                        "type": "manufacturer",
                        "name": "Test Hardware",
                    },
                    "platform.test": {
                        "id": "platform.test",
                        "type": "platform",
                        "name": "Test Platform",
                        "manufacturer": [
                            "manufacturer.test",
                        ],
                        "metadata": {
                            "retroarch_supported": True,
                        },
                    },
                },
                "edges": {},
            }
        ),
        encoding="utf-8",
    )

    service = RVDBService.from_bundle(
        bundle
    )

    view = service.platform_view(
        "platform.test"
    )

    assert view.platform.manufacturers == (
        RVDBEntityRef(
            id="manufacturer.test",
            entity_type="manufacturer",
            name="Test Hardware",
        ),
    )

    assert view.platform.retroarch_supported is True


def test_service_preserves_missing_manufacturer_identity(
    tmp_path,
):
    bundle = tmp_path / "rvdb.bundle.json"

    bundle.write_text(
        json.dumps(
            {
                "nodes": {
                    "platform.test": {
                        "id": "platform.test",
                        "type": "platform",
                        "name": "Test Platform",
                        "manufacturer": [
                            "manufacturer.missing",
                        ],
                    },
                },
                "edges": {},
            }
        ),
        encoding="utf-8",
    )

    service = RVDBService.from_bundle(
        bundle
    )

    view = service.platform_view(
        "platform.test"
    )

    assert view.platform.manufacturers == (
        RVDBEntityRef(
            id="manufacturer.missing",
            entity_type="unknown",
            name="manufacturer.missing",
        ),
    )


def test_service_preserves_relationship_cardinality(
    tmp_path,
):
    bundle = tmp_path / "rvdb.bundle.json"

    bundle.write_text(
        json.dumps(
            {
                "nodes": {
                    "platform.test": {
                        "id": "platform.test",
                        "type": "platform",
                        "name": "Test Platform",
                    },
                    "core.a": {
                        "id": "core.a",
                        "type": "core",
                        "name": "Core A",
                    },
                    "core.b": {
                        "id": "core.b",
                        "type": "core",
                        "name": "Core B",
                    },
                    "emulator.a": {
                        "id": "emulator.a",
                        "type": "emulator",
                        "name": "Emulator A",
                    },
                    "frontend.a": {
                        "id": "frontend.a",
                        "type": "frontend",
                        "name": "Frontend A",
                    },
                },
                "edges": {
                    "platform.test": {
                        "supports_core": [
                            "core.a",
                            "core.b",
                        ],
                    },
                    "core.a": {},
                    "core.b": {},
                    "emulator.a": {
                        "supports_platform": [
                            "platform.test",
                        ],
                    },
                    "frontend.a": {
                        "launches_core": [
                            "core.a",
                            "core.b",
                        ],
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    service = RVDBService.from_bundle(
        bundle
    )

    view = service.platform_view(
        "platform.test"
    )

    assert [
        ref.id
        for ref in view.cores
    ] == [
        "core.a",
        "core.b",
    ]

    assert [
        ref.id
        for ref in view.emulators
    ] == [
        "emulator.a",
    ]

    assert [
        ref.id
        for ref in view.frontends
    ] == [
        "frontend.a",
    ]


def test_service_propagates_consumer_errors(
    tmp_path,
):
    bundle = tmp_path / "rvdb.bundle.json"

    bundle.write_text(
        json.dumps(
            {
                "nodes": {},
                "edges": {},
            }
        ),
        encoding="utf-8",
    )

    service = RVDBService(
        RVDBConsumer(
            bundle
        )
    )

    with pytest.raises(
        RVDBError
    ):
        service.platform_view(
            "platform.missing"
        )


def test_retroarch_view_builds_typed_read_model(
    tmp_path,
):
    bundle = {
        "nodes": {
            "frontend.retroarch": {
                "id": "frontend.retroarch",
                "type": "frontend",
                "name": "RetroArch",
                "aliases": [],
                "metadata": {},
                "relationships": {
                    "launches_core": [
                        "core.beta",
                        "core.alpha",
                    ]
                },
            },
            "core.alpha": {
                "id": "core.alpha",
                "type": "core",
                "name": "Alpha Core",
            },
            "core.beta": {
                "id": "core.beta",
                "type": "core",
                "name": "Beta Core",
            },
            "platform.alpha": {
                "id": "platform.alpha",
                "type": "platform",
                "name": "Alpha System",
            },
            "compatibility.alpha": {
                "id": "compatibility.alpha",
                "type": "compatibility",
                "subject": "core.alpha",
                "platform": "platform.alpha",
                "playability": "playable",
                "evidence": [
                    {
                        "source": "one"
                    },
                    {
                        "source": "two"
                    },
                ],
            },
        },
        "edges": {
            "frontend.retroarch": {
                "launches_core": [
                    "core.beta",
                    "core.alpha",
                ]
            }
        },
    }

    path = (
        tmp_path
        / "rvdb.bundle.json"
    )

    path.write_text(
        json.dumps(
            bundle
        ),
        encoding="utf-8",
    )

    service = RVDBService.from_bundle(
        path
    )

    view = service.retroarch_view()

    assert view is not None

    assert view.frontend.id == (
        "frontend.retroarch"
    )

    assert view.frontend.name == (
        "RetroArch"
    )

    assert [
        core.name
        for core in view.cores
    ] == [
        "Alpha Core",
        "Beta Core",
    ]

    alpha = view.cores[0]

    assert alpha.id == (
        "core.alpha"
    )

    assert alpha.platforms == (
        "Alpha System",
    )

    assert alpha.playability == (
        "playable",
    )

    assert alpha.evidence_count == 2

    assert alpha.frontends == (
        "RetroArch",
    )

    beta = view.cores[1]

    assert beta.id == (
        "core.beta"
    )

    assert beta.platforms == ()

    assert beta.playability == ()

    assert beta.evidence_count == 0

    assert beta.frontends == (
        "RetroArch",
    )


def test_retroarch_view_missing_frontend(
    tmp_path,
):
    bundle = {
        "nodes": {},
        "edges": {},
    }

    path = (
        tmp_path
        / "rvdb.bundle.json"
    )

    path.write_text(
        json.dumps(
            bundle
        ),
        encoding="utf-8",
    )

    service = RVDBService.from_bundle(
        path
    )

    assert (
        service.retroarch_view()
        is None
    )


def test_retroarch_view_real_bundle():
    service = RVDBService.from_bundle(
        REAL_BUNDLE
    )

    view = service.retroarch_view()

    assert view is not None

    assert view.frontend.id == (
        "frontend.retroarch"
    )

    assert view.frontend.name == (
        "RetroArch"
    )

    assert [
        core.name
        for core in view.cores
    ] == [
        "bsnes",
        "Genesis Plus GX",
        "Mesen",
        "Snes9x",
    ]

    bsnes = next(
        core
        for core in view.cores
        if core.id
        == "core.bsnes"
    )

    assert bsnes.platforms == (
        "Super Nintendo",
    )

    assert bsnes.playability == (
        "playable",
    )

    assert bsnes.evidence_count == 3

    assert bsnes.frontends == (
        "RetroArch",
    )

    genesis = next(
        core
        for core in view.cores
        if core.id
        == "core.genesis.plus.gx"
    )

    assert genesis.platforms == (
        "Game Gear",
        "Sega Genesis",
        "Sega Master System",
        "Sega SG-1000",
    )

    assert genesis.playability == (
        "playable",
    )

    assert genesis.evidence_count == 12

    assert genesis.frontends == (
        "RetroArch",
    )
