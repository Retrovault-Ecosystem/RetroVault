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

    # SessionConfig clears inherited overlay/shader/aspect-auto state only.
    # Physical viewport geometry is deliberately absent: the canonical
    # production CONTAIN layer owns it after display-aspect resolution.
    expected_session_neutralization = (
        'input_overlay_enable = "false"',
        'input_overlay = ""',
        'video_shader_enable = "false"',
        'video_shader = ""',
        'aspect_ratio_index = "0"',
        'video_force_aspect = "true"',
        'video_aspect_ratio = "-1.000000"',
        'video_aspect_ratio_auto = "true"',
    )

    forbidden_viewport_authority = (
        "video_scale_integer",
        "video_viewport_bias_x",
        "video_viewport_bias_y",
        "custom_viewport_x",
        "custom_viewport_y",
        "custom_viewport_width",
        "custom_viewport_height",
        "video_crop_overscan",
    )

    for directive in expected_session_neutralization:
        assert directive in baseline

    for key in forbidden_viewport_authority:
        assert key not in baseline
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

    session_level = (
        'aspect_ratio_index = "0"',
        'video_force_aspect = "true"',
        'video_aspect_ratio = "-1.000000"',
        'video_aspect_ratio_auto = "true"',
    )

    viewport_authority = (
        "video_scale_integer",
        "video_viewport_bias_x",
        "video_viewport_bias_y",
        "custom_viewport_x",
        "custom_viewport_y",
        "custom_viewport_width",
        "custom_viewport_height",
        "video_crop_overscan",
    )

    for directive in session_level:
        assert directive in baseline

    for key in viewport_authority:
        assert key not in baseline


def test_session_config_does_not_own_presentation_viewport_geometry(
    tmp_path,
):
    """
    Generic session state must not compete with the production
    presentation layer. Dynamic viewport geometry belongs to
    ContainRuntimeConfig after core display-aspect resolution.
    """
    from pathlib import Path

    from services.retroarch.session_config import (
        RetroArchSessionConfig,
    )

    runtime = RetroArchSessionConfig(
        directory=tmp_path,
    )

    path = runtime.create()

    if path is None:
        return

    payload = Path(path).read_text(
        encoding="utf-8"
    )

    forbidden = (
        "video_scale_integer",
        "video_viewport_bias_x",
        "video_viewport_bias_y",
        "custom_viewport_x",
        "custom_viewport_y",
        "custom_viewport_width",
        "custom_viewport_height",
        "video_crop_overscan",
    )

    for key in forbidden:
        assert key not in payload
