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


GENESIS_A6_PACKAGE = (
    Path("retrovault")
    / "genesis"
    / "classic"
)

GENESIS_A6_OVERLAY = (
    GENESIS_A6_PACKAGE
    / "RetroVault_Genesis_Classic.cfg"
)

GENESIS_A6_RUNTIME = (
    GENESIS_A6_PACKAGE
    / "RetroVault_Genesis_Classic.runtime.cfg"
)

GENESIS_A6_PRODUCTION_MANIFEST = (
    GENESIS_A6_PACKAGE
    / "RetroVault_Genesis_Classic.production.json"
)

def test_genesis_dynamic_runtime_requires_no_fixed_custom_viewport():
    """
    Genesis differs intentionally from the calibrated NES/SNES packages.

    Genesis Plus GX may change source geometry during a session through
    libretro SET_GEOMETRY. The production-package architecture must not
    convert those source modes into fixed per-raster or per-title
    RetroArch custom viewports.
    """

    payload = (
        OverlayRuntimeConfig
        ._runtime_descriptor_payload(
            GENESIS_A6_OVERLAY
        )
    )

    required = (
        'video_force_aspect = "true"',
        'video_scale_integer = "false"',
        'video_aspect_ratio_auto = "true"',
        'video_crop_overscan = "false"',
    )

    for setting in required:
        assert setting in payload

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

    for setting in forbidden:
        assert setting not in payload


def test_genesis_dynamic_geometry_contract_is_system_level_not_content_level():
    data = json.loads(
        GENESIS_A6_PRODUCTION_MANIFEST.read_text(
            encoding="utf-8"
        )
    )

    assert data["platform_id"] == "platform.sega.genesis"
    assert data["core_identity"] == "genesis_plus_gx"

    assert (
        data["source_geometry_authority"]
        == "libretro_core"
    )

    assert (
        data["source_display_aspect_authority"]
        == "libretro_core"
    )

    assert (
        data["physical_geometry_authority"]
        == "platform_package"
    )

    assert data["fit_policy"] == "contain"

    dynamic = data["dynamic_geometry"]

    assert dynamic["preserve_core_set_geometry"] is True
    assert dynamic["per_game_geometry"] is False
    assert dynamic["per_raster_geometry"] is False

    assert (
        dynamic["force_framebuffer_to_master_envelope"]
        is False
    )

    serialized = json.dumps(
        data,
        sort_keys=True,
    ).casefold()

    forbidden_identity = (
        '"game_id"',
        '"rom_id"',
        '"title_id"',
        '"content_id"',
        '"archive_id"',
    )

    for token in forbidden_identity:
        assert token not in serialized


def test_genesis_package_validator_has_no_fixed_viewport_requirement():
    """
    Production package validation owns package coherence and canonical
    identity. Physical geometry remains package-owned, but a package is
    not required to express that authority through fixed custom viewport
    coordinates.

    This distinction permits Genesis to retain core-driven dynamic
    geometry while NES/SNES retain their already-qualified fixed
    viewport contracts.
    """

    import inspect

    from services.presentation.production_package import (
        ProductionPresentationPackageValidator,
    )

    source = inspect.getsource(
        ProductionPresentationPackageValidator
    )

    fixed_geometry_tokens = (
        "custom_viewport_x",
        "custom_viewport_y",
        "custom_viewport_width",
        "custom_viewport_height",
        "video_viewport_bias_x",
        "video_viewport_bias_y",
        "aspect_ratio_index",
    )

    for token in fixed_geometry_tokens:
        assert token not in source


def test_genesis_preproduction_state_remains_fail_closed_after_dynamic_qualification():
    """
    A.6 qualification must not accidentally promote Genesis into the
    READY launch boundary before physical/live validation.
    """

    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
        PlatformPresentationPolicyState,
    )

    platform_id = "platform.sega.genesis"

    assert (
        PlatformPresentationPolicyRegistry.state_for(
            platform_id
        )
        is PlatformPresentationPolicyState.UNCONFIGURED
    )

    assert (
        PlatformPresentationPolicyRegistry.for_platform(
            platform_id
        )
        is None
    )

    assert (
        PlatformPresentationPolicyRegistry
        .master_presentation_class_for(
            platform_id
        )
        is None
    )


def test_genesis_master_envelope_is_not_a_forced_framebuffer():
    """
    CLASSIC_4_3 defines the reusable glass/safe envelope. It must not
    be interpreted as an instruction to force Genesis Plus GX source
    raster dimensions to 1440x1080.
    """

    from services.presentation.master_profile import (
        MasterPresentationClass,
        MasterPresentationProfileRegistry,
    )

    profile = (
        MasterPresentationProfileRegistry.require(
            MasterPresentationClass.CLASSIC_4_3
        )
    )

    assert profile.canvas == (1920, 1080)
    assert profile.envelope == (240, 0, 1440, 1080)

    manifest = json.loads(
        GENESIS_A6_PRODUCTION_MANIFEST.read_text(
            encoding="utf-8"
        )
    )

    assert (
        manifest["dynamic_geometry"]
        ["force_framebuffer_to_master_envelope"]
        is False
    )

    runtime_payload = (
        GENESIS_A6_RUNTIME.read_text(
            encoding="utf-8"
        )
    )

    assert 'custom_viewport_width = "1440"' not in runtime_payload
    assert 'custom_viewport_height = "1080"' not in runtime_payload


def test_genesis_dynamic_contract_does_not_copy_nes_or_snes_geometry():
    payload = GENESIS_A6_RUNTIME.read_text(
        encoding="utf-8"
    )

    protected_foreign_geometry = (
        'custom_viewport_x = "355"',
        'custom_viewport_y = "100"',
        'custom_viewport_width = "1206"',
        'custom_viewport_height = "762"',
        'custom_viewport_width = "1044"',
        'custom_viewport_height = "783"',
        'video_viewport_bias_y = "0.239057239"',
        'aspect_ratio_index = "22"',
        'aspect_ratio_index = "23"',
    )

    for setting in protected_foreign_geometry:
        assert setting not in payload
