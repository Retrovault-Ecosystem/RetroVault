from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from services.presentation.production_glass import (
    ProductionGlass,
    ProductionGlassResolver,
)


ROOT = Path(__file__).resolve().parents[1]

SPEC = (
    ROOT
    / "data"
    / "presentation"
    / "specifications"
    / "rvv_genesis_classic.json"
)

MANIFEST = (
    ROOT
    / "retrovault"
    / "genesis"
    / "classic"
    / "RetroVault_Genesis_Classic.production.json"
)

ARTWORK = (
    ROOT
    / "retrovault"
    / "genesis"
    / "classic"
    / "RetroVault_Genesis_Classic.png"
)


EXPECTED_GLASS = ProductionGlass(
    canvas_width=1920,
    canvas_height=1080,
    x=330,
    y=90,
    width=1260,
    height=900,
)


def _spec() -> dict:
    return json.loads(
        SPEC.read_text(encoding="utf-8")
    )


def _manifest() -> dict:
    return json.loads(
        MANIFEST.read_text(encoding="utf-8")
    )


def test_genesis_artwork_is_real_1080p_rgba_asset():
    with Image.open(ARTWORK) as image:
        rgba = image.convert("RGBA")

        assert rgba.size == (1920, 1080)

        alpha = rgba.getchannel("A")

        assert alpha.getextrema() == (0, 255)

        histogram = alpha.histogram()

        assert histogram[0] > 0
        assert histogram[255] > 0


def test_genesis_artwork_has_exact_transparent_physical_glass():
    with Image.open(ARTWORK) as image:
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")

        x = EXPECTED_GLASS.x
        y = EXPECTED_GLASS.y
        w = EXPECTED_GLASS.width
        h = EXPECTED_GLASS.height

        glass = alpha.crop(
            (
                x,
                y,
                x + w,
                y + h,
            )
        )

        assert glass.getextrema() == (0, 0)
        assert (
            glass.histogram()[0]
            == w * h
        )

        # Immediate exterior must belong to the physical bezel.
        assert alpha.getpixel((x - 1, y)) == 255
        assert alpha.getpixel((x + w, y)) == 255
        assert alpha.getpixel((x, y - 1)) == 255
        assert alpha.getpixel((x, y + h)) == 255


def test_genesis_manifest_resolves_semantic_fixed_glass():
    glass = ProductionGlassResolver.from_manifest(
        str(MANIFEST),
        expected_platform_id="platform.sega.genesis",
    )

    assert glass == EXPECTED_GLASS


def test_genesis_spec_and_manifest_share_artwork_geometry():
    spec = _spec()
    manifest = _manifest()

    assert spec["geometry"]["canvas"] == manifest["canvas"]
    assert spec["geometry"]["aperture"] == manifest["aperture"]



def test_genesis_artwork_and_runtime_geometry_qualification_remain_separate_authorities():
    spec = _spec()
    manifest = _manifest()

    geometry = spec["geometry"]
    qualification = geometry["qualification"]

    assert geometry["status"] == "runtime_geometry_qualified"

    # Artwork authority owns the transparent physical aperture.
    assert geometry["aperture"] == {
        "x": 330,
        "y": 90,
        "width": 1260,
        "height": 900,
    }

    # Runtime qualification now records a real Genesis Plus GX
    # reference result. It is qualification evidence only; the
    # runtime policy remains loaded-content/core driven.
    assert geometry["viewport"] == {
        "x": 330,
        "y": 126,
        "width": 1260,
        "height": 827,
    }
    assert geometry["aspect_ratio_index"] == 23
    assert geometry["integer_scaling"] is False
    assert geometry["viewport_bias_x"] == 0.5
    assert geometry["viewport_bias_y"] == 0.5
    assert geometry["crop_overscan"] is False

    assert geometry["runtime_geometry_policy"] == (
        "derive_per_loaded_content_display_aspect"
    )

    assert qualification["display_aspect_width"] == 1.524
    assert qualification["display_aspect_height"] == 1.0
    assert qualification["title_specific_geometry"] is False

    dynamic = manifest["dynamic_geometry"]

    assert dynamic["preserve_core_set_geometry"] is True
    assert dynamic["per_game_geometry"] is False
    assert dynamic["per_raster_geometry"] is False
    assert (
        dynamic["force_framebuffer_to_master_envelope"]
        is False
    )

    assert manifest["source_geometry_authority"] == (
        "libretro_core"
    )
    assert manifest["source_display_aspect_authority"] == (
        "libretro_core"
    )
    assert manifest["physical_geometry_authority"] == (
        "platform_package"
    )

    assert manifest["geometry"][
        "runtime_geometry_policy"
    ] == "derive_per_loaded_content_display_aspect"

    assert manifest["geometry"][
        "qualified_reference_viewport"
    ] == {
        "x": 330,
        "y": 126,
        "width": 1260,
        "height": 827,
    }

    assert manifest["geometry"][
        "title_specific_geometry"
    ] is False




def test_genesis_runtime_geometry_qualification_supports_n5c_activation():
    spec = _spec()
    manifest = _manifest()

    qualification = spec[
        "master_presentation_qualification"
    ]
    geometry = spec["geometry"]
    state = spec["production_state"]
    manifest_state = manifest["production_state"]

    assert (
        qualification["physical_runtime_geometry_qualified"]
        is True
    )
    assert (
        qualification["production_policy_activation"]
        is True
    )

    assert geometry["status"] == "runtime_geometry_qualified"
    assert geometry["aperture"] == {
        "x": 330,
        "y": 90,
        "width": 1260,
        "height": 900,
    }
    assert geometry["viewport"] == {
        "x": 330,
        "y": 126,
        "width": 1260,
        "height": 827,
    }
    assert geometry["runtime_geometry_policy"] == (
        "derive_per_loaded_content_display_aspect"
    )
    assert (
        geometry["qualification"]["title_specific_geometry"]
        is False
    )

    assert state["presentation_policy_state"] == "unconfigured"
    assert state["production_package_complete"] is False
    assert state["production_ready"] is True
    assert state["live_calibration_complete"] is True

    assert manifest_state["geometry_qualified"] is True
    assert manifest_state["policy_activation"] is True
    assert manifest_state["production_ready"] is True
    assert manifest_state["live_validation_required"] is False



def test_genesis_artwork_contract_is_system_level_not_title_level():
    spec = _spec()
    manifest = _manifest()

    assert spec["source_preservation"]["title_specific_geometry"] is False

    assert manifest["dynamic_geometry"]["per_game_geometry"] is False
    assert manifest["dynamic_geometry"]["per_raster_geometry"] is False
    assert (
        manifest["dynamic_geometry"]
        ["force_framebuffer_to_master_envelope"]
        is False
    )
    assert (
        manifest["dynamic_geometry"]
        ["preserve_core_set_geometry"]
        is True
    )
