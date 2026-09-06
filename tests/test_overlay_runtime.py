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
