import json
from pathlib import Path

import pytest

from services.presentation.master_profile import (
    MasterPresentationClass,
)
from services.presentation.production_glass import (
    ProductionGlass,
    ProductionGlassResolver,
)
from services.retroarch.contain_runtime import (
    ContainRuntimeConfig,
)


ROOT = Path(__file__).resolve().parents[1]

NES_MANIFEST = (
    ROOT
    / "retrovault"
    / "nes"
    / "classic"
    / "RetroVault_NES_Classic.production.json"
)


def _write_manifest(
    tmp_path,
    payload,
):
    path = (
        tmp_path
        / "RetroVault_Test.production.json"
    )

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    return path


def test_resolves_real_nes_production_aperture():
    glass = ProductionGlassResolver.from_manifest(
        str(NES_MANIFEST),
        expected_platform_id=(
            "platform.nintendo.nes"
        ),
    )

    assert glass == ProductionGlass(
        canvas_width=1920,
        canvas_height=1080,
        x=355,
        y=100,
        width=1206,
        height=762,
    )


def test_nes_glass_adapts_to_contain_profile():
    glass = ProductionGlassResolver.from_manifest(
        str(NES_MANIFEST),
        expected_platform_id=(
            "platform.nintendo.nes"
        ),
    )

    profile = glass.as_master_profile(
        profile_class=(
            MasterPresentationClass.CLASSIC_4_3
        ),
    )

    assert (
        profile.envelope_x,
        profile.envelope_y,
        profile.envelope_width,
        profile.envelope_height,
    ) == (
        355,
        100,
        1206,
        762,
    )

    geometry = ContainRuntimeConfig.geometry(
        profile=profile,
        display_aspect_width=1.306,
        display_aspect_height=1.0,
    )

    assert (
        geometry.x,
        geometry.y,
        geometry.width,
        geometry.height,
    ) == (
        460,
        100,
        995,
        762,
    )


def test_rejects_platform_identity_mismatch():
    with pytest.raises(
        ValueError,
        match="platform identity",
    ):
        ProductionGlassResolver.from_manifest(
            str(NES_MANIFEST),
            expected_platform_id=(
                "platform.nintendo.snes"
            ),
        )


@pytest.mark.parametrize(
    "canvas,aperture",
    [
        (
            {"width": 0, "height": 1080},
            {
                "x": 0,
                "y": 0,
                "width": 100,
                "height": 100,
            },
        ),
        (
            {"width": 1920, "height": 1080},
            {
                "x": -1,
                "y": 0,
                "width": 100,
                "height": 100,
            },
        ),
        (
            {"width": 1920, "height": 1080},
            {
                "x": 0,
                "y": 0,
                "width": 0,
                "height": 100,
            },
        ),
        (
            {"width": 1920, "height": 1080},
            {
                "x": 1900,
                "y": 0,
                "width": 100,
                "height": 100,
            },
        ),
        (
            {"width": 1920, "height": 1080},
            {
                "x": 0,
                "y": 1000,
                "width": 100,
                "height": 100,
            },
        ),
    ],
)
def test_rejects_invalid_or_out_of_canvas_geometry(
    tmp_path,
    canvas,
    aperture,
):
    path = _write_manifest(
        tmp_path,
        {
            "platform_id": "platform.test",
            "canvas": canvas,
            "aperture": aperture,
        },
    )

    with pytest.raises(ValueError):
        ProductionGlassResolver.from_manifest(
            str(path),
            expected_platform_id="platform.test",
        )


def test_rejects_missing_aperture(
    tmp_path,
):
    path = _write_manifest(
        tmp_path,
        {
            "platform_id": "platform.test",
            "canvas": {
                "width": 1920,
                "height": 1080,
            },
        },
    )

    with pytest.raises(
        ValueError,
        match="aperture",
    ):
        ProductionGlassResolver.from_manifest(
            str(path),
            expected_platform_id="platform.test",
        )


def test_rejects_boolean_geometry_values(
    tmp_path,
):
    path = _write_manifest(
        tmp_path,
        {
            "platform_id": "platform.test",
            "canvas": {
                "width": 1920,
                "height": 1080,
            },
            "aperture": {
                "x": False,
                "y": 0,
                "width": 100,
                "height": 100,
            },
        },
    )

    with pytest.raises(ValueError):
        ProductionGlassResolver.from_manifest(
            str(path),
            expected_platform_id="platform.test",
        )


def test_semantic_glass_module_contains_no_content_identity():
    text = (
        ROOT
        / "services"
        / "presentation"
        / "production_glass.py"
    ).read_text(
        encoding="utf-8"
    ).casefold()

    for forbidden in (
        "duck tales",
        "ducktales",
        "street fighter",
        "sonic the hedgehog",
    ):
        assert forbidden not in text


def test_ready_snes_manifest_exposes_live_approved_semantic_glass():
    from pathlib import Path

    from services.presentation.production_glass import (
        ProductionGlassResolver,
    )

    root = Path(__file__).resolve().parents[1]

    manifest = (
        root
        / "retrovault"
        / "snes"
        / "classic"
        / "RetroVault_SNES_Classic.production.json"
    )

    glass = ProductionGlassResolver.from_manifest(
        str(manifest),
        expected_platform_id="platform.nintendo.snes",
    )

    assert (
        glass.canvas_width,
        glass.canvas_height,
    ) == (
        1920,
        1080,
    )

    assert (
        glass.x,
        glass.y,
        glass.width,
        glass.height,
    ) == (
        438,
        71,
        1044,
        783,
    )


def test_ready_system_semantic_glass_is_system_level_not_game_level():
    from pathlib import Path

    source = Path(
        "services/presentation/production_glass.py"
    ).read_text(
        encoding="utf-8"
    ).casefold()

    for forbidden in (
        "duck tales",
        "ducktales",
        "street fighter",
        "super mario",
        "sonic the hedgehog",
        "rom_name",
        "game_name",
        "title_name",
    ):
        assert forbidden not in source
