from pathlib import Path

from services.retroarch.session_config import (
    RetroArchSessionConfig,
)


def test_session_config_creates_clean_presentation_baseline(
    tmp_path,
):
    runtime = RetroArchSessionConfig(
        tmp_path
    )

    generated = Path(
        runtime.create()
    )

    assert generated.is_file()

    assert generated.read_text(
        encoding="utf-8"
    ) == RetroArchSessionConfig.BASELINE

def test_session_config_uses_unique_transient_files(
    tmp_path,
):
    runtime = RetroArchSessionConfig(
        tmp_path
    )

    first = Path(
        runtime.create()
    )

    second = Path(
        runtime.create()
    )

    assert first != second

    assert first.is_file()
    assert second.is_file()


def test_session_config_cleanup_removes_owned_files(
    tmp_path,
):
    runtime = RetroArchSessionConfig(
        tmp_path
    )

    first = Path(
        runtime.create()
    )

    second = Path(
        runtime.create()
    )

    runtime.cleanup()

    assert not first.exists()
    assert not second.exists()


def test_session_config_does_not_modify_external_config(
    tmp_path,
):
    external = (
        tmp_path
        / "retroarch.cfg"
    )

    original = (
        'input_overlay_enable = "true"\n'
        'input_overlay = "/external/bezel.cfg"\n'
        'video_shader_enable = "true"\n'
        'video_shader = "/external/shader.slangp"\n'
    )

    external.write_text(
        original,
        encoding="utf-8",
    )

    runtime = RetroArchSessionConfig(
        tmp_path / "runtime"
    )

    runtime.create()

    assert external.read_text(
        encoding="utf-8"
    ) == original


def test_session_baseline_neutralizes_inherited_geometry_without_owning_platform_geometry():
    baseline = RetroArchSessionConfig.BASELINE

    # A.7 establishes a reusable session-level neutralization boundary.
    # These values clear inherited RetroArch geometry before any
    # platform package is appended; they are not platform calibration.
    expected = (
        'aspect_ratio_index = "0"',
        'video_force_aspect = "true"',
        'video_aspect_ratio = "-1.000000"',
        'video_aspect_ratio_auto = "true"',
        'video_scale_integer = "false"',
        'video_viewport_bias_x = "0.500000"',
        'video_viewport_bias_y = "0.500000"',
        'custom_viewport_x = "0"',
        'custom_viewport_y = "0"',
        'custom_viewport_width = "0"',
        'custom_viewport_height = "0"',
        'video_crop_overscan = "false"',
    )

    for directive in expected:
        assert directive in baseline

    # The baseline must remain generic. Calibrated physical geometry
    # belongs to the later platform package runtime descriptor.
    forbidden_calibration_values = (
        'custom_viewport_x = "355"',
        'custom_viewport_y = "100"',
        'custom_viewport_width = "1206"',
        'custom_viewport_height = "762"',
        'custom_viewport_width = "1044"',
        'custom_viewport_height = "783"',
        'video_viewport_bias_y = "0.239057239"',
    )

    for directive in forbidden_calibration_values:
        assert directive not in baseline
def test_session_baseline_neutralizes_external_presentation_authority():
    baseline = RetroArchSessionConfig.BASELINE

    required = (
        'input_overlay_enable = "false"',
        'input_overlay = ""',
        'video_shader_enable = "false"',
        'video_shader = ""',
    )

    for directive in required:
        assert baseline.count(directive) == 1


def test_session_baseline_has_session_isolation_responsibility():
    assert RetroArchSessionConfig.BASELINE == (
        'input_overlay_enable = "false"\n'
        'input_overlay = ""\n'
        'video_shader_enable = "false"\n'
        'video_shader = ""\n'
        'aspect_ratio_index = "0"\n'
        'video_force_aspect = "true"\n'
        'video_aspect_ratio = "-1.000000"\n'
        'video_aspect_ratio_auto = "true"\n'
        'video_scale_integer = "false"\n'
        'video_viewport_bias_x = "0.500000"\n'
        'video_viewport_bias_y = "0.500000"\n'
        'custom_viewport_x = "0"\n'
        'custom_viewport_y = "0"\n'
        'custom_viewport_width = "0"\n'
        'custom_viewport_height = "0"\n'
        'video_crop_overscan = "false"\n'
    )
def test_session_can_own_transient_core_options_path(
    tmp_path,
):
    from pathlib import Path

    options = (
        tmp_path
        / "core-options.cfg"
    )

    options.write_text(
        'fceumm_overscan_v_bottom = "0"\n',
        encoding="utf-8",
    )

    runtime = RetroArchSessionConfig(
        directory=(
            tmp_path
            / "sessions"
        )
    )

    result = runtime.create(
        core_options_path=str(
            options
        )
    )

    payload = Path(
        result
    ).read_text(
        encoding="utf-8"
    )

    assert (
        f'core_options_path = "{options.resolve()}"\n'
        in payload
    )

    assert (
        'global_core_options = "true"\n'
        in payload
    )

    assert payload.startswith(
        RetroArchSessionConfig.BASELINE
    )

    runtime.cleanup()


def test_session_baseline_contains_only_neutral_geometry_not_platform_calibration():
    baseline = RetroArchSessionConfig.BASELINE

    neutral_geometry = (
        'aspect_ratio_index = "0"',
        'video_aspect_ratio = "-1.000000"',
        'video_aspect_ratio_auto = "true"',
        'custom_viewport_x = "0"',
        'custom_viewport_y = "0"',
        'custom_viewport_width = "0"',
        'custom_viewport_height = "0"',
        'video_viewport_bias_x = "0.500000"',
        'video_viewport_bias_y = "0.500000"',
    )

    for directive in neutral_geometry:
        assert directive in baseline

    # Known calibrated NES/SNES values must never migrate into the
    # generic session-isolation baseline.
    platform_specific = (
        'aspect_ratio_index = "22"',
        'aspect_ratio_index = "23"',
        'custom_viewport_x = "355"',
        'custom_viewport_y = "100"',
        'custom_viewport_width = "1206"',
        'custom_viewport_height = "762"',
        'custom_viewport_width = "1044"',
        'custom_viewport_height = "783"',
        'video_viewport_bias_y = "0.239057239"',
    )

    for directive in platform_specific:
        assert directive not in baseline