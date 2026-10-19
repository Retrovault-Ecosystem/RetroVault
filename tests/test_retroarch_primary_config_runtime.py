from pathlib import Path

import pytest

from services.retroarch.primary_config_runtime import (
    PrimaryConfigRuntime,
)


def test_managed_controls_replace_only_transient_copy(tmp_path):
    from config.controller_preferences import defaults, DEFAULT_KEYS
    from services.input.mappings import retroarch_values
    source = tmp_path / 'original.cfg'
    original = ('video_driver = "glcore"\ninput_player1_a = "z" # old mapping\n'
                'input_exit_emulator = "escape"\nvideo_shader_enable = "true"\n')
    source.write_text(original)
    preferences = defaults()
    preferences['retroarch'] = dict(mode='managed', players=[dict(
        kind='keyboard', device={}, bindings=dict(DEFAULT_KEYS))])
    runtime = PrimaryConfigRuntime(directory=tmp_path / 'owned')
    path = Path(runtime.create(source, video_driver='glcore',
                               input_values=retroarch_values({'controllers': preferences})))
    text = path.read_text()
    assert 'input_player1_a = "x"' in text
    assert 'input_exit_emulator = "escape"' in text
    assert 'video_shader_enable = "true"' in text
    assert source.read_text() == original
    runtime.cleanup()
    assert not path.exists()


def test_ambiguous_managed_control_is_rejected_before_output(tmp_path):
    source = tmp_path / 'original.cfg'
    source.write_text('video_driver = "glcore"\ninput_player1_a = "x"\ninput_player1_a = "z"\n')
    runtime = PrimaryConfigRuntime(directory=tmp_path / 'owned')
    with pytest.raises(ValueError, match='Duplicate'):
        runtime.create(source, input_values={'input_player1_a': 'c'})
    assert not (tmp_path / 'owned').exists()


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


def test_explicit_primary_is_isolated_without_changing_driver(
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

    before = source.read_bytes()
    result = Path(runtime.create(source, video_driver=""))
    text = result.read_text()
    assert 'video_driver = "vulkan"' in text
    assert 'auto_overrides_enable = "false"' in text
    assert 'auto_shaders_enable = "false"' in text
    assert source.read_bytes() == before
    runtime.cleanup(str(result))



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


def test_primary_runtime_uses_disposable_xdg_cache(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    runtime = PrimaryConfigRuntime()
    source = _source(tmp_path)
    before = source.read_bytes()
    result = Path(runtime.create(source, video_driver="glcore"))
    assert result.is_relative_to(tmp_path / "cache")
    assert source.read_bytes() == before
    runtime.cleanup(str(result))
    assert not result.exists()


def test_production_overlay_isolates_primary_without_driver_override(tmp_path, monkeypatch):
    from services.retroarch.primary_config_runtime import PrimaryConfigRuntime
    source = tmp_path / 'native.cfg'
    source.write_text('\tvideo_driver\t=\t"gl"\n\tauto_overrides_enable\t=\t"true"\n')
    overlay = tmp_path / 'overlay.cfg'
    overlay.write_text('overlays = "1"\n')
    original = source.read_bytes()
    runtime = PrimaryConfigRuntime(directory=tmp_path / 'runtime')
    monkeypatch.setattr(runtime, 'default_config_candidates', lambda: (source,))
    result = Path(runtime.create(video_driver='', overlay=str(overlay)))
    assert 'auto_overrides_enable = "false"' in result.read_text()
    assert '\tvideo_driver\t=\t"gl"' in result.read_text()
    assert source.read_bytes() == original
    runtime.cleanup()
    assert not result.exists()


def test_tabbed_driver_is_updated_and_includes_fail_before_writing(tmp_path):
    from services.retroarch.primary_config_runtime import PrimaryConfigRuntime
    source = tmp_path / 'source.cfg'
    runtime = PrimaryConfigRuntime(directory=tmp_path / 'runtime')
    source.write_text('\tvideo_driver\t=\t"gl"\n')
    result = Path(runtime.create(source=source, video_driver='glcore'))
    assert 'video_driver = "glcore"' in result.read_text()
    runtime.cleanup()
    source.write_text('#include "other.cfg"\nvideo_driver = "gl"\n')
    with pytest.raises(ValueError, match='includes are unsupported'):
        runtime.create(source=source, video_driver='glcore')
    assert not list(runtime.directory.iterdir())


def test_owned_primary_directory_removes_sidecars_without_touching_other_files(tmp_path):
    source = _source(tmp_path)
    runtime = PrimaryConfigRuntime(directory=tmp_path / 'cache')
    first = Path(runtime.create(source, video_driver='glcore'))
    second = Path(runtime.create(source, video_driver='glcore'))
    assert first.parent != second.parent
    sidecar = first.parent / 'retroarch_qt.cfg'
    sidecar.write_text('desktop preferences')
    unrelated = runtime.directory / 'historical.cfg'
    unrelated.write_text('preserve')
    runtime.cleanup()
    assert not first.parent.exists()
    assert not second.parent.exists()
    assert unrelated.read_text() == 'preserve'
    assert source.exists()
    runtime.cleanup()


def test_owned_primary_directory_cleanup_failure_can_retry(tmp_path, monkeypatch):
    import shutil
    source = _source(tmp_path)
    runtime = PrimaryConfigRuntime(directory=tmp_path / 'cache')
    primary = Path(runtime.create(source, video_driver='glcore'))
    (primary.parent / 'retroarch_qt.cfg').write_text('preferences')
    original = shutil.rmtree
    def fail(*args, **kwargs):
        raise PermissionError('controlled cleanup failure')
    monkeypatch.setattr(shutil, 'rmtree', fail)
    with pytest.raises(OSError, match='cleanup pending'):
        runtime.cleanup()
    monkeypatch.setattr(shutil, 'rmtree', original)
    runtime.cleanup()
    assert not primary.parent.exists()


def test_failed_primary_creation_still_owns_empty_directory(tmp_path, monkeypatch):
    import tempfile
    source = _source(tmp_path)
    runtime = PrimaryConfigRuntime(directory=tmp_path / 'cache')
    def fail(*args, **kwargs):
        raise OSError('controlled create failure')
    monkeypatch.setattr(tempfile, 'NamedTemporaryFile', fail)
    with pytest.raises(OSError, match='create failure'):
        runtime.create(source, video_driver='glcore')
    assert list(runtime.directory.iterdir())
    runtime.cleanup()
    assert not list(runtime.directory.iterdir())


def test_primary_sidecar_symlink_does_not_delete_external_target(tmp_path):
    source = _source(tmp_path)
    runtime = PrimaryConfigRuntime(directory=tmp_path / 'cache')
    primary = Path(runtime.create(source, video_driver='glcore'))
    outside = tmp_path / 'unrelated'
    outside.mkdir()
    (outside / 'keep').write_text('preserve')
    (primary.parent / 'sidecar').symlink_to(outside, target_is_directory=True)
    runtime.cleanup()
    assert (outside / 'keep').read_text() == 'preserve'
