from pathlib import Path

import pytest

from services.retroarch.shader_runtime import (
    ShaderRuntimeConfig,
    _default_runtime_directory,
)


def _shader(
    tmp_path,
    name="base.slangp",
):
    shader = (
        tmp_path
        / "shaders"
        / name
    )

    shader.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    shader.write_text(
        "# base shader\n",
        encoding="utf-8",
    )

    return shader


def test_empty_shader_passes_through():
    runtime = ShaderRuntimeConfig()

    assert runtime.resolve(
        "",
        {
            "PARAMETER": "1",
        },
    ) == ""


def test_shader_without_parameters_passes_through(
    tmp_path,
):
    shader = _shader(
        tmp_path
    )

    runtime = ShaderRuntimeConfig(
        tmp_path / "runtime"
    )

    result = runtime.resolve(
        str(shader)
    )

    assert result == str(
        shader.resolve()
    )

    assert not runtime.directory.exists()


def test_shader_with_empty_parameter_mapping_passes_through(
    tmp_path,
):
    shader = _shader(
        tmp_path
    )

    runtime = ShaderRuntimeConfig(
        tmp_path / "runtime"
    )

    result = runtime.resolve(
        str(shader),
        {},
    )

    assert result == str(
        shader.resolve()
    )

    assert not runtime.directory.exists()


def test_runtime_creates_transient_reference_wrapper(
    tmp_path,
):
    shader = _shader(
        tmp_path
    )

    runtime = ShaderRuntimeConfig(
        tmp_path / "runtime"
    )

    result = Path(
        runtime.resolve(
            str(shader),
            {
                "PARAM_A": "1.000000",
                "PARAM_B": "-2.500000",
            },
        )
    )

    assert result.is_file()
    assert result.suffix == ".slangp"

    assert result.read_text(
        encoding="utf-8"
    ) == (
        f'#reference "{shader.resolve()}"\n'
        "\n"
        'PARAM_A = "1.000000"\n'
        'PARAM_B = "-2.500000"\n'
    )

    runtime.cleanup()

    assert not result.exists()


def test_runtime_uses_unique_wrapper_files(
    tmp_path,
):
    shader = _shader(
        tmp_path
    )

    runtime = ShaderRuntimeConfig(
        tmp_path / "runtime"
    )

    parameters = {
        "PARAM": "1",
    }

    first = Path(
        runtime.resolve(
            str(shader),
            parameters,
        )
    )

    second = Path(
        runtime.resolve(
            str(shader),
            parameters,
        )
    )

    assert first != second
    assert first.is_file()
    assert second.is_file()

    runtime.cleanup()

    assert not first.exists()
    assert not second.exists()


def test_runtime_rejects_missing_shader(
    tmp_path,
):
    runtime = ShaderRuntimeConfig(
        tmp_path / "runtime"
    )

    with pytest.raises(
        ValueError,
        match="Shader preset does not exist",
    ):
        runtime.resolve(
            str(
                tmp_path
                / "missing.slangp"
            ),
            {
                "PARAM": "1",
            },
        )

    assert not runtime.directory.exists()


def test_runtime_rejects_non_mapping_parameters(
    tmp_path,
):
    shader = _shader(
        tmp_path
    )

    runtime = ShaderRuntimeConfig(
        tmp_path / "runtime"
    )

    with pytest.raises(
        ValueError,
        match=(
            "Shader runtime parameters "
            "must be a mapping"
        ),
    ):
        runtime.resolve(
            str(shader),
            ["PARAM"],
        )


@pytest.mark.parametrize(
    "name",
    [
        "",
        "1PARAM",
        "PARAM-NAME",
        "PARAM NAME",
        "PARAM.NAME",
    ],
)
def test_runtime_rejects_invalid_parameter_names(
    tmp_path,
    name,
):
    shader = _shader(
        tmp_path
    )

    runtime = ShaderRuntimeConfig(
        tmp_path / "runtime"
    )

    with pytest.raises(
        ValueError,
        match=(
            "Shader runtime parameter "
            "name cannot be empty"
            if name == ""
            else "Invalid shader runtime parameter name"
        ),
    ):
        runtime.resolve(
            str(shader),
            {
                name: "1",
            },
        )


def test_runtime_rejects_non_string_parameter_name(
    tmp_path,
):
    shader = _shader(
        tmp_path
    )

    runtime = ShaderRuntimeConfig(
        tmp_path / "runtime"
    )

    with pytest.raises(
        ValueError,
        match=(
            "Shader runtime parameter "
            "name must be a string"
        ),
    ):
        runtime.resolve(
            str(shader),
            {
                1: "1",
            },
        )


def test_runtime_rejects_null_parameter_value(
    tmp_path,
):
    shader = _shader(
        tmp_path
    )

    runtime = ShaderRuntimeConfig(
        tmp_path / "runtime"
    )

    with pytest.raises(
        ValueError,
        match=(
            "Shader runtime parameter "
            "value cannot be null"
        ),
    ):
        runtime.resolve(
            str(shader),
            {
                "PARAM": None,
            },
        )


def test_runtime_escapes_reference_and_parameter_values(
    tmp_path,
):
    shader = _shader(
        tmp_path,
        'quoted"name.slangp',
    )

    runtime = ShaderRuntimeConfig(
        tmp_path / "runtime"
    )

    result = Path(
        runtime.resolve(
            str(shader),
            {
                "PARAM": 'quoted"value',
            },
        )
    )

    payload = result.read_text(
        encoding="utf-8"
    )

    assert '\\"' in payload

    runtime.cleanup()


def test_default_runtime_uses_xdg_cache_home(
    monkeypatch,
    tmp_path,
):
    cache_home = (
        tmp_path
        / "xdg-cache"
    )

    monkeypatch.setenv(
        "XDG_CACHE_HOME",
        str(cache_home),
    )

    assert (
        _default_runtime_directory()
        == cache_home
        / "retrovault"
        / "shader-runtime"
    )


def test_default_runtime_falls_back_to_home_cache(
    monkeypatch,
    tmp_path,
):
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
        / "shader-runtime"
    )


def test_parameters_for_overlay_without_overlay():
    assert (
        ShaderRuntimeConfig
        .parameters_for_overlay("")
        == {}
    )


def test_parameters_for_overlay_without_sidecar(
    tmp_path,
):
    overlay = tmp_path / "Overlay.cfg"

    overlay.write_text(
        'overlays = "1"\n',
        encoding="utf-8",
    )

    assert (
        ShaderRuntimeConfig
        .parameters_for_overlay(
            str(overlay)
        )
        == {}
    )


def test_parameters_for_overlay_reads_sidecar(
    tmp_path,
):
    overlay = tmp_path / "Overlay.cfg"

    overlay.write_text(
        'overlays = "1"\n',
        encoding="utf-8",
    )

    overlay.with_suffix(
        ".shader.cfg"
    ).write_text(
        (
            'PARAM_A = "1.000000"\n'
            'PARAM_B = "-2.500000"\n'
        ),
        encoding="utf-8",
    )

    assert (
        ShaderRuntimeConfig
        .parameters_for_overlay(
            str(overlay)
        )
        == {
            "PARAM_A": "1.000000",
            "PARAM_B": "-2.500000",
        }
    )


def test_parameters_for_overlay_rejects_duplicate(
    tmp_path,
):
    overlay = tmp_path / "Overlay.cfg"

    overlay.write_text(
        'overlays = "1"\n',
        encoding="utf-8",
    )

    overlay.with_suffix(
        ".shader.cfg"
    ).write_text(
        (
            'PARAM = "1"\n'
            'PARAM = "2"\n'
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Duplicate shader runtime parameter"
        ),
    ):
        ShaderRuntimeConfig.parameters_for_overlay(
            str(overlay)
        )


def test_parameters_for_overlay_rejects_unquoted_value(
    tmp_path,
):
    overlay = tmp_path / "Overlay.cfg"

    overlay.write_text(
        'overlays = "1"\n',
        encoding="utf-8",
    )

    overlay.with_suffix(
        ".shader.cfg"
    ).write_text(
        "PARAM = 1\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="values must be quoted",
    ):
        ShaderRuntimeConfig.parameters_for_overlay(
            str(overlay)
        )
