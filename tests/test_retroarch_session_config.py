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


def test_session_baseline_does_not_own_platform_geometry():
    baseline = RetroArchSessionConfig.BASELINE

    forbidden = (
        "aspect_ratio_index",
        "video_force_aspect",
        "video_scale_integer",
        "video_viewport_bias_x",
        "video_viewport_bias_y",
        "custom_viewport_x",
        "custom_viewport_y",
        "custom_viewport_width",
        "custom_viewport_height",
    )

    for directive in forbidden:
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


def test_session_baseline_has_single_responsibility():
    assert RetroArchSessionConfig.BASELINE == (
        'input_overlay_enable = "false"\n'
        'input_overlay = ""\n'
        'video_shader_enable = "false"\n'
        'video_shader = ""\n'
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


def test_session_baseline_still_contains_no_geometry():
    geometry_keys = (
        "aspect_ratio_index",
        "video_force_aspect",
        "video_scale_integer",
        "video_viewport_bias_x",
        "video_viewport_bias_y",
        "custom_viewport_x",
        "custom_viewport_y",
        "custom_viewport_width",
        "custom_viewport_height",
    )

    assert all(
        key not in RetroArchSessionConfig.BASELINE
        for key in geometry_keys
    )
