from pathlib import Path

import pytest

from services.rvdb.consumer import (
    RVDBError,
)
from services.rvdb.models import (
    RVDBEntityRef,
    RVDBPlatformView,
)
from services.rvdb.service import (
    RVDBService,
)


REAL_BUNDLE = Path(
    "data/rvdb/rvdb.bundle.json"
)


def test_real_snes_platform_view_is_typed():
    service = RVDBService.from_bundle(
        REAL_BUNDLE
    )

    view = service.platform_view(
        "platform.nintendo.snes"
    )

    assert isinstance(
        view,
        RVDBPlatformView,
    )

    assert isinstance(
        view.platform,
        RVDBEntityRef,
    )

    assert view.platform == RVDBEntityRef(
        id="platform.nintendo.snes",
        entity_type="platform",
        name="Super Nintendo",
    )


def test_real_snes_preserves_multiple_cores_and_emulators():
    service = RVDBService.from_bundle(
        REAL_BUNDLE
    )

    view = service.platform_view(
        "platform.nintendo.snes"
    )

    assert {
        core.id
        for core in view.cores
    } == {
        "core.bsnes",
        "core.snes9x",
    }

    assert {
        emulator.id
        for emulator in view.emulators
    } == {
        "emulator.bsnes",
        "emulator.snes9x",
    }


def test_real_snes_frontend_is_deduplicated():
    service = RVDBService.from_bundle(
        REAL_BUNDLE
    )

    view = service.platform_view(
        "platform.nintendo.snes"
    )

    assert [
        frontend.id
        for frontend in view.frontends
    ] == [
        "frontend.retroarch",
    ]


def test_missing_platform_preserves_consumer_error():
    service = RVDBService.from_bundle(
        REAL_BUNDLE
    )

    with pytest.raises(
        RVDBError,
        match="entity not found",
    ):
        service.platform_view(
            "platform.missing"
        )
