from pathlib import Path

import pytest

from services.retroarch.primary_config_runtime import (
    PrimaryConfigRuntime,
)


def _source(
    tmp_path,
    *,
    driver="vulkan",
):
    path = (
        tmp_path
        / "retroarch.cfg"
    )

    path.write_text(
        'audio_driver = "pulse"\n'
        f'video_driver = "{driver}"\n'
        'video_fullscreen = "true"\n',
        encoding="utf-8",
    )

    return path


def test_primary_runtime_changes_video_driver_and_establishes_presentation_authority(
    tmp_path,
):
    source = _source(
        tmp_path
    )

    runtime = PrimaryConfigRuntime(
        directory=(
            tmp_path
            / "runtime"
        )
    )

    result = runtime.create(
        source,
        video_driver="glcore",
    )

    expected = (
        'audio_driver = "pulse"\n'
        'video_driver = "glcore"\n'
        'video_fullscreen = "true"\n'
        'auto_overrides_enable = "false"\n'
        'auto_shaders_enable = "false"\n'
        'input_overlay_enable_autopreferred = "false"\n'
    )

    assert (
        Path(result).read_text(
            encoding="utf-8"
        )
        == expected
    )

    assert (
        source.read_text(
            encoding="utf-8"
        )
        ==
        'audio_driver = "pulse"\n'
        'video_driver = "vulkan"\n'
        'video_fullscreen = "true"\n'
    )


def test_primary_runtime_requires_exactly_one_driver(
    tmp_path,
):
    source = (
        tmp_path
        / "retroarch.cfg"
    )

    source.write_text(
        'audio_driver = "pulse"\n',
        encoding="utf-8",
    )

    runtime = PrimaryConfigRuntime(
        directory=(
            tmp_path
            / "runtime"
        )
    )

    with pytest.raises(
        ValueError,
        match="exactly one video_driver",
    ):
        runtime.create(
            source,
            video_driver="glcore",
        )


def test_primary_runtime_rejects_missing_explicit_source(
    tmp_path,
):
    runtime = PrimaryConfigRuntime(
        directory=(
            tmp_path
            / "runtime"
        )
    )

    with pytest.raises(
        ValueError,
        match="does not exist",
    ):
        runtime.create(
            tmp_path
            / "missing.cfg",
            video_driver="glcore",
        )


def test_primary_runtime_no_driver_override_is_noop(
    tmp_path,
):
    source = _source(
        tmp_path
    )

    runtime = PrimaryConfigRuntime(
        directory=(
            tmp_path
            / "runtime"
        )
    )

    assert (
        runtime.create(
            source,
            video_driver="",
        )
        is None
    )


def test_primary_runtime_cleanup_removes_transient_file(
    tmp_path,
):
    source = _source(
        tmp_path
    )

    runtime = PrimaryConfigRuntime(
        directory=(
            tmp_path
            / "runtime"
        )
    )

    result = runtime.create(
        source,
        video_driver="glcore",
    )

    assert Path(result).is_file()

    runtime.cleanup(
        result
    )

    assert not Path(result).exists()


def test_wayland_qualifies_glcore(
    monkeypatch,
):
    monkeypatch.setenv(
        "WAYLAND_DISPLAY",
        "wayland-0",
    )

    assert (
        PrimaryConfigRuntime
        .qualified_video_driver()
        == "glcore"
    )


def test_non_wayland_does_not_force_driver(
    monkeypatch,
):
    monkeypatch.delenv(
        "WAYLAND_DISPLAY",
        raising=False,
    )

    assert (
        PrimaryConfigRuntime
        .qualified_video_driver()
        == ""
    )


def test_primary_runtime_disables_competing_presentation_automation(
    tmp_path,
):
    from pathlib import Path

    from services.retroarch.primary_config_runtime import (
        PrimaryConfigRuntime,
    )

    source = tmp_path / "retroarch.cfg"
    source.write_text(
        "\n".join(
            (
                'video_driver = "vulkan"',
                'auto_overrides_enable = "true"',
                'auto_shaders_enable = "true"',
                'input_overlay_enable_autopreferred = "true"',
                'input_overlay_enable = "true"',
                'input_overlay = "/legacy/user/overlay.cfg"',
                "",
            )
        ),
        encoding="utf-8",
    )

    runtime = PrimaryConfigRuntime(
        directory=tmp_path / "runtime",
    )

    generated = Path(
        runtime.create(
            source,
            video_driver="glcore",
        )
    )

    try:
        text = generated.read_text(encoding="utf-8")

        assert 'video_driver = "glcore"' in text
        assert 'auto_overrides_enable = "false"' in text
        assert 'auto_shaders_enable = "false"' in text
        assert (
            'input_overlay_enable_autopreferred = "false"'
            in text
        )

        # Generic overlay state itself is intentionally left alone here.
        # The later RetroVault overlay-runtime append layer owns the final
        # canonical overlay path/enable/opacity/scale values.
        assert 'input_overlay_enable = "true"' in text
        assert (
            'input_overlay = "/legacy/user/overlay.cfg"'
            in text
        )
    finally:
        runtime.cleanup(generated)

    assert not generated.exists()


def test_primary_runtime_fails_closed_when_presentation_authority_is_ambiguous(
    tmp_path,
):
    import pytest

    from services.retroarch.primary_config_runtime import (
        PrimaryConfigRuntime,
    )

    source = tmp_path / "retroarch.cfg"
    source.write_text(
        "\n".join(
            (
                'video_driver = "vulkan"',
                'auto_overrides_enable = "true"',
                'auto_overrides_enable = "false"',
                'auto_shaders_enable = "true"',
                'input_overlay_enable_autopreferred = "true"',
                "",
            )
        ),
        encoding="utf-8",
    )

    runtime = PrimaryConfigRuntime(
        directory=tmp_path / "runtime",
    )

    with pytest.raises(
        ValueError,
        match="auto_overrides_enable",
    ):
        runtime.create(
            source,
            video_driver="glcore",
        )


def test_primary_runtime_materializes_missing_presentation_authority(
    tmp_path,
):
    from pathlib import Path

    from services.retroarch.primary_config_runtime import (
        PrimaryConfigRuntime,
    )

    source = tmp_path / "minimal-retroarch.cfg"
    source.write_text(
        "\n".join(
            (
                'audio_driver = "pulse"',
                'video_driver = "vulkan"',
                'video_fullscreen = "true"',
                "",
            )
        ),
        encoding="utf-8",
    )

    runtime = PrimaryConfigRuntime(
        directory=tmp_path / "runtime",
    )

    generated = Path(
        runtime.create(
            source,
            video_driver="glcore",
        )
    )

    try:
        text = generated.read_text(encoding="utf-8")

        assert 'video_driver = "glcore"' in text
        assert text.count(
            'auto_overrides_enable = "false"'
        ) == 1
        assert text.count(
            'auto_shaders_enable = "false"'
        ) == 1
        assert text.count(
            'input_overlay_enable_autopreferred = "false"'
        ) == 1

        assert 'audio_driver = "pulse"' in text
        assert 'video_fullscreen = "true"' in text

    finally:
        runtime.cleanup(generated)

    assert not generated.exists()
