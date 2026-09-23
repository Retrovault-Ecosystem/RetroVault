from pathlib import Path

import pytest

from services.retroarch.overlay_runtime import (
    OverlayRuntimeConfig,
)


def test_runtime_config_contains_overlay_directives(
    tmp_path,
):
    overlay = (
        tmp_path
        / "overlays"
        / "NES.cfg"
    )
    overlay.parent.mkdir()

    overlay.write_text(
        'overlays = "1"\n',
        encoding="utf-8",
    )

    runtime = OverlayRuntimeConfig(
        tmp_path / "runtime"
    )

    generated = Path(
        runtime.create(
            str(overlay)
        )
    )

    assert generated.is_file()

    assert generated.read_text(
        encoding="utf-8"
    ) == (
        f'input_overlay = "{overlay.resolve()}"\n'
        'input_overlay_enable = "true"\n'
        'input_overlay_opacity = "1.000000"\n'
        'input_overlay_scale = "1.000000"\n'
    )

    runtime.cleanup()

    assert not generated.exists()


def test_runtime_config_uses_unique_files(
    tmp_path,
):
    overlay = tmp_path / "NES.cfg"

    overlay.write_text(
        'overlays = "1"\n',
        encoding="utf-8",
    )

    runtime = OverlayRuntimeConfig(
        tmp_path / "runtime"
    )

    first = runtime.create(
        str(overlay)
    )
    second = runtime.create(
        str(overlay)
    )

    assert first != second
    assert Path(first).is_file()
    assert Path(second).is_file()

    runtime.cleanup()


def test_runtime_config_rejects_missing_overlay(
    tmp_path,
):
    runtime = OverlayRuntimeConfig(
        tmp_path / "runtime"
    )

    with pytest.raises(
        ValueError,
        match=(
            "Overlay configuration "
            "does not exist"
        ),
    ):
        runtime.create(
            str(
                tmp_path
                / "missing.cfg"
            )
        )

    assert not runtime.directory.exists()


def test_runtime_config_escapes_config_value(
    tmp_path,
):
    overlay = (
        tmp_path
        / 'quoted"name.cfg'
    )

    overlay.write_text(
        'overlays = "1"\n',
        encoding="utf-8",
    )

    runtime = OverlayRuntimeConfig(
        tmp_path / "runtime"
    )

    generated = Path(
        runtime.create(
            str(overlay)
        )
    )

    payload = generated.read_text(
        encoding="utf-8"
    )

    assert '\\"' in payload

    assert (
        'input_overlay_enable = "true"'
        in payload
    )

    runtime.cleanup()


def test_default_runtime_uses_xdg_cache_home(
    monkeypatch,
    tmp_path,
):
    from services.retroarch.overlay_runtime import (
        _default_runtime_directory,
    )

    cache_home = tmp_path / "xdg-cache"

    monkeypatch.setenv(
        "XDG_CACHE_HOME",
        str(cache_home),
    )

    assert (
        _default_runtime_directory()
        == cache_home
        / "retrovault"
        / "overlay-runtime"
    )


def test_default_runtime_falls_back_to_home_cache(
    monkeypatch,
    tmp_path,
):
    from services.retroarch.overlay_runtime import (
        _default_runtime_directory,
    )

    monkeypatch.delenv(
        "XDG_CACHE_HOME",
        raising=False,
    )

    monkeypatch.setattr(
        Path,
        "home",
        classmethod(
            lambda cls: tmp_path
        ),
    )

    assert (
        _default_runtime_directory()
        == tmp_path
        / ".cache"
        / "retrovault"
        / "overlay-runtime"
    )


def test_runtime_config_merges_optional_runtime_descriptor(
    tmp_path,
):
    overlay = tmp_path / "NES.cfg"

    overlay.write_text(
        'overlays = "1"\n',
        encoding="utf-8",
    )

    overlay.with_suffix(
        ".runtime.cfg"
    ).write_text(
        (
            'aspect_ratio_index = "22"\n'
            'video_force_aspect = "true"\n'
            'custom_viewport_x = "0"\n'
            'custom_viewport_y = "0"\n'
            'custom_viewport_width = "1920"\n'
            'custom_viewport_height = "1080"\n'
        ),
        encoding="utf-8",
    )

    runtime = OverlayRuntimeConfig(
        tmp_path / "runtime"
    )

    generated = Path(
        runtime.create(str(overlay))
    )

    assert generated.read_text(
        encoding="utf-8"
    ) == (
        f'input_overlay = "{overlay.resolve()}"\n'
        'input_overlay_enable = "true"\n'
        'input_overlay_opacity = "1.000000"\n'
        'input_overlay_scale = "1.000000"\n'
        'aspect_ratio_index = "22"\n'
        'video_force_aspect = "true"\n'
        'custom_viewport_x = "0"\n'
        'custom_viewport_y = "0"\n'
        'custom_viewport_width = "1920"\n'
        'custom_viewport_height = "1080"\n'
    )


def test_runtime_config_without_descriptor_is_unchanged(
    tmp_path,
):
    overlay = tmp_path / "plain.cfg"

    overlay.write_text(
        'overlays = "1"\n',
        encoding="utf-8",
    )

    runtime = OverlayRuntimeConfig(
        tmp_path / "runtime"
    )

    generated = Path(
        runtime.create(str(overlay))
    )

    assert generated.read_text(
        encoding="utf-8"
    ) == (
        f'input_overlay = "{overlay.resolve()}"\n'
        'input_overlay_enable = "true"\n'
        'input_overlay_opacity = "1.000000"\n'
        'input_overlay_scale = "1.000000"\n'
    )


def test_runtime_config_rejects_unsupported_runtime_key(
    tmp_path,
):
    overlay = tmp_path / "NES.cfg"

    overlay.write_text(
        'overlays = "1"\n',
        encoding="utf-8",
    )

    overlay.with_suffix(
        ".runtime.cfg"
    ).write_text(
        'unexpected_setting = "1"\n',
        encoding="utf-8",
    )

    runtime = OverlayRuntimeConfig(
        tmp_path / "runtime"
    )

    with pytest.raises(
        ValueError,
        match="Unsupported overlay runtime setting",
    ):
        runtime.create(str(overlay))


def test_runtime_config_rejects_duplicate_runtime_key(
    tmp_path,
):
    overlay = tmp_path / "NES.cfg"

    overlay.write_text(
        'overlays = "1"\n',
        encoding="utf-8",
    )

    overlay.with_suffix(
        ".runtime.cfg"
    ).write_text(
        (
            'custom_viewport_width = "1920"\n'
            'custom_viewport_width = "1280"\n'
        ),
        encoding="utf-8",
    )

    runtime = OverlayRuntimeConfig(
        tmp_path / "runtime"
    )

    with pytest.raises(
        ValueError,
        match="Duplicate overlay runtime setting",
    ):
        runtime.create(str(overlay))


def test_runtime_descriptor_accepts_production_viewport_controls(
    tmp_path,
):
    overlay = tmp_path / "RetroVault_SNES_Classic.cfg"
    overlay.write_text(
        'overlays = "1"\n',
        encoding="utf-8",
    )

    runtime = overlay.with_suffix(".runtime.cfg")
    runtime.write_text(
        'aspect_ratio_index = "23"\n'
        'video_force_aspect = "true"\n'
        'video_scale_integer = "false"\n'
        'custom_viewport_width = "1044"\n'
        'custom_viewport_height = "783"\n'
        'video_viewport_bias_x = "0.500000"\n'
        'video_viewport_bias_y = "0.239057239"\n',
        encoding="utf-8",
    )

    payload = OverlayRuntimeConfig._runtime_descriptor_payload(
        overlay
    )

    assert payload == (
        'aspect_ratio_index = "23"\n'
        'video_force_aspect = "true"\n'
        'video_scale_integer = "false"\n'
        'video_viewport_bias_x = "0.500000"\n'
        'video_viewport_bias_y = "0.239057239"\n'
        'custom_viewport_width = "1044"\n'
        'custom_viewport_height = "783"\n'
    )

def test_overlay_runtime_propagates_complete_geometry_authority(tmp_path):
    from services.retroarch.overlay_runtime import OverlayRuntimeConfig

    overlay = tmp_path / "RetroVault_Test.cfg"
    runtime = tmp_path / "RetroVault_Test.runtime.cfg"

    overlay.write_text(
        'overlays = 1\n'
        'overlay0_overlay = "test.png"\n',
        encoding="utf-8",
    )

    runtime.write_text(
        'aspect_ratio_index = "22"\n'
        'video_force_aspect = "true"\n'
        'video_aspect_ratio = "-1.000000"\n'
        'video_aspect_ratio_auto = "false"\n'
        'video_crop_overscan = "false"\n'
        'video_scale_integer = "false"\n'
        'video_viewport_bias_x = "0.500000"\n'
        'video_viewport_bias_y = "0.500000"\n'
        'custom_viewport_x = "355"\n'
        'custom_viewport_y = "100"\n'
        'custom_viewport_width = "1206"\n'
        'custom_viewport_height = "762"\n',
        encoding="utf-8",
    )

    generated = Path(
        OverlayRuntimeConfig(
            tmp_path / "generated"
        ).create(
            str(overlay)
        )
    )

    text = generated.read_text(
        encoding="utf-8"
    )

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
