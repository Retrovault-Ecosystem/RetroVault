import json
from pathlib import Path

from services.presentation.master_profile import (
    MasterPresentationClass,
    MasterPresentationProfileRegistry,
)
from services.retroarch.overlay_runtime import (
    OverlayRuntimeConfig,
)


ROOT = Path(__file__).resolve().parents[1]

PACKAGE = (
    ROOT
    / "retrovault"
    / "genesis"
    / "classic"
)

OVERLAY = (
    PACKAGE
    / "RetroVault_Genesis_Classic.cfg"
)

RUNTIME = (
    PACKAGE
    / "RetroVault_Genesis_Classic.runtime.cfg"
)

MANIFEST = (
    PACKAGE
    / "RetroVault_Genesis_Classic.production.json"
)

SHADER = (
    PACKAGE
    / "RetroVault_Genesis_Classic_CRT.slangp"
)

IMAGE = (
    PACKAGE
    / "RetroVault_Genesis_Classic.png"
)


def _manifest():
    return json.loads(
        MANIFEST.read_text(
            encoding="utf-8"
        )
    )


def _runtime():
    return RUNTIME.read_text(
        encoding="utf-8"
    )


def test_genesis_preproduction_package_is_structurally_complete():
    for path in (
        OVERLAY,
        RUNTIME,
        MANIFEST,
        SHADER,
        IMAGE,
    ):
        assert path.is_file()


def test_genesis_package_declares_canonical_identity():
    data = _manifest()

    assert (
        data["platform_id"]
        == "platform.sega.genesis"
    )

    assert (
        data["core_identity"]
        == "genesis_plus_gx"
    )


def test_genesis_package_uses_classic_4_3_master_profile():
    data = _manifest()

    assert (
        data["master_presentation_class"]
        == "classic_4_3"
    )

    assert data["fit_policy"] == "contain"

    profile = (
        MasterPresentationProfileRegistry
        .require(
            MasterPresentationClass.CLASSIC_4_3
        )
    )

    assert profile.canvas == (
        1920,
        1080,
    )

    assert profile.envelope == (
        240,
        0,
        1440,
        1080,
    )


def test_genesis_package_preserves_core_dynamic_geometry():
    data = _manifest()

    dynamic = data["dynamic_geometry"]

    assert (
        data["source_geometry_authority"]
        == "libretro_core"
    )

    assert (
        data["source_display_aspect_authority"]
        == "libretro_core"
    )

    assert (
        dynamic["preserve_core_set_geometry"]
        is True
    )

    assert (
        dynamic["per_game_geometry"]
        is False
    )

    assert (
        dynamic["per_raster_geometry"]
        is False
    )

    assert (
        dynamic[
            "force_framebuffer_to_master_envelope"
        ]
        is False
    )


def test_genesis_runtime_preserves_core_aspect():
    runtime = _runtime()

    required = (
        'video_force_aspect = "true"',
        'video_aspect_ratio_auto = "true"',
        'video_crop_overscan = "false"',
        'video_scale_integer = "false"',
    )

    for line in required:
        assert line in runtime


def test_genesis_runtime_does_not_force_fixed_viewport():
    runtime = _runtime()

    forbidden = (
        "aspect_ratio_index",
        "video_aspect_ratio =",
        "custom_viewport_x",
        "custom_viewport_y",
        "custom_viewport_width",
        "custom_viewport_height",
        "video_viewport_bias_x",
        "video_viewport_bias_y",
    )

    for token in forbidden:
        assert token not in runtime


def test_genesis_runtime_descriptor_is_supported_by_overlay_runtime():
    payload = (
        OverlayRuntimeConfig
        ._runtime_descriptor_payload(
            OVERLAY
        )
    )

    assert payload == (
        'video_force_aspect = "true"\n'
        'video_scale_integer = "false"\n'
        'video_aspect_ratio_auto = "true"\n'
        'video_crop_overscan = "false"\n'
    )


def test_genesis_package_does_not_activate_production():
    data = _manifest()

    state = data["production_state"]

    assert state["policy_activation"] is False
    assert state["production_ready"] is False
    assert (
        state["live_validation_required"]
        is True
    )


def test_genesis_package_contains_no_game_identity():
    payload = json.dumps(
        _manifest(),
        sort_keys=True,
    ).casefold()

    forbidden = (
        "game_id",
        "rom_id",
        "rom_path",
        "rom_filename",
        "archive_id",
        "archive_filename",
        "title_id",
        "title_name",
    )

    for token in forbidden:
        assert token not in payload


def test_genesis_shader_source_is_geometry_neutral():
    preset = SHADER.read_text(
        encoding="utf-8"
    )

    source_path = (
        SHADER.parent
        / preset.split(
            'shader0 = "',
            1,
        )[1].split('"', 1)[0]
    ).resolve()

    assert source_path.is_file()

    source = source_path.read_text(
        encoding="utf-8"
    ).casefold()

    forbidden = (
        "custom_viewport",
        "aspect_ratio_index",
        "video_viewport_bias",
        "rom_id",
        "game_id",
        "title_id",
    )

    for token in forbidden:
        assert token not in source
