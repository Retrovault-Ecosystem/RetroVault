from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

NES_RUNTIME = (
    ROOT
    / "retrovault"
    / "nes"
    / "classic"
    / "RetroVault_NES_Classic.runtime.cfg"
)

NES_SHADER = (
    ROOT
    / "retrovault"
    / "nes"
    / "classic"
    / "RetroVault_NES_Classic.shader.cfg"
)

NES_PRESET = (
    ROOT
    / "retrovault"
    / "nes"
    / "classic"
    / "RetroVault_NES_Classic_CRT.slangp"
)

CORE_OPTIONS = (
    ROOT
    / "services"
    / "retroarch"
    / "core_options_runtime.py"
)


def _hsm_parameters(text: str) -> dict[str, str]:
    result = {}

    for line in text.splitlines():
        stripped = line.strip()

        if not stripped.startswith("HSM_"):
            continue

        if "=" not in stripped:
            continue

        key, value = stripped.split("=", 1)

        result[key.strip()] = value.strip().strip('"')

    return result


def test_nes_runtime_is_the_single_final_viewport_authority():
    text = NES_RUNTIME.read_text(encoding="utf-8")

    required = (
        'aspect_ratio_index = "22"',
        'video_force_aspect = "true"',
        'video_aspect_ratio = "-1.000000"',
        'video_aspect_ratio_auto = "false"',
        'video_crop_overscan = "false"',
        'video_scale_integer = "false"',
        'video_viewport_bias_x = "0.500000"',
        'video_viewport_bias_y = "0.500000"',
        'custom_viewport_x = "355"',
        'custom_viewport_y = "100"',
        'custom_viewport_width = "1206"',
        'custom_viewport_height = "762"',
    )

    for line in required:
        assert line in text


def test_nes_shader_runtime_descriptor_is_minimal_and_neutral():
    text = NES_SHADER.read_text(encoding="utf-8")

    assert "minimal" in text.lower()
    assert "no unwanted thick black inset" in text.lower()

    assert _hsm_parameters(text) == {
        "HSM_NON_INTEGER_SCALE": "100.000000",
        "HSM_SCREEN_POSITION_Y": "0.000000",
    }

    assert 'HSM_NON_INTEGER_SCALE = "80.000000"' not in text
    assert 'HSM_SCREEN_POSITION_Y = "15.000000"' not in text


def test_nes_full_crt_preset_cannot_create_secondary_geometry():
    text = NES_PRESET.read_text(encoding="utf-8")

    expected = (
        'HSM_INT_SCALE_MODE = "0.000000"',
        'HSM_NON_INTEGER_SCALE = "100.000000"',
        'HSM_ASPECT_RATIO_MODE = "0.000000"',
        'HSM_SCREEN_POSITION_X = "0.000000"',
        'HSM_SCREEN_POSITION_Y = "0.000000"',
        'HSM_CROP_PERCENT_ZOOM = "0.000000"',
        'HSM_CROP_PERCENT_TOP = "0.000000"',
        'HSM_CROP_PERCENT_BOTTOM = "0.000000"',
        'HSM_CROP_PERCENT_LEFT = "0.000000"',
        'HSM_CROP_PERCENT_RIGHT = "0.000000"',
    )

    for line in expected:
        assert line in text

    assert 'HSM_NON_INTEGER_SCALE = "80.000000"' not in text
    assert 'HSM_SCREEN_POSITION_Y = "15.000000"' not in text


def test_fceumm_runtime_preserves_all_four_frame_edges():
    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
    )
    from services.retroarch.core_options_runtime import (
        CoreOptionsRuntimeConfig,
    )

    expected = {
        "fceumm_overscan_h_left": "0",
        "fceumm_overscan_h_right": "0",
        "fceumm_overscan_v_top": "0",
        "fceumm_overscan_v_bottom": "0",
    }

    policy = PlatformPresentationPolicyRegistry.resolve(
        platform_id="platform.nintendo.nes",
        core_identity="fceumm",
    )

    assert policy is not None
    assert dict(policy.core_options) == expected

    assert (
        CoreOptionsRuntimeConfig.policy_for(
            "/opt/retropie/libretrocores/"
            "lr-fceumm/fceumm_libretro.so",
            platform_id="platform.nintendo.nes",
        )
        == expected
    )
