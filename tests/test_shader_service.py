from services.shaders import (
    ShaderService,
)


def test_missing_directory_returns_empty(
    tmp_path,
):
    service = ShaderService(
        tmp_path / "missing"
    )

    assert service.scan() == []


def test_empty_directory_returns_empty(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    assert ShaderService(
        root
    ).scan() == []


def test_discovers_preset_recursively(
    tmp_path,
):
    root = tmp_path / "shaders"
    package = root / "crt" / "presets"
    package.mkdir(
        parents=True
    )

    preset = package / "display.slangp"
    preset.write_text(
        'shaders = "0"\n',
        encoding="utf-8",
    )

    shaders = ShaderService(
        root
    ).scan()

    assert len(shaders) == 1
    assert shaders[0].preset_path == preset
    assert shaders[0].relative_preset == (
        preset.relative_to(root)
    )


def test_supported_preset_types(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    for filename in (
        "one.slangp",
        "two.glslp",
        "three.cgp",
    ):
        (
            root / filename
        ).write_text(
            'shaders = "0"\n',
            encoding="utf-8",
        )

    presets = ShaderService(
        root
    ).scan()

    assert {
        preset.preset_type
        for preset in presets
    } == {
        "Slang",
        "GLSL",
        "CG",
    }


def test_resolves_relative_shader_pass(
    tmp_path,
):
    root = tmp_path / "shaders"
    preset_directory = root / "preset"
    pass_directory = root / "passes"

    preset_directory.mkdir(
        parents=True
    )
    pass_directory.mkdir()

    shader = (
        pass_directory / "display.slang"
    )
    shader.write_text(
        "void main() {}\n",
        encoding="utf-8",
    )

    preset = (
        preset_directory / "display.slangp"
    )
    preset.write_text(
        'shader0 = "../passes/display.slang"\n',
        encoding="utf-8",
    )

    result = ShaderService(
        root
    ).scan()[0]

    assert result.shader_paths == (
        shader.resolve(),
    )
    assert result.missing_shaders == ()
    assert result.ready


def test_reports_missing_shader_pass(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    (
        root / "broken.slangp"
    ).write_text(
        'shader0 = "missing.slang"\n',
        encoding="utf-8",
    )

    result = ShaderService(
        root
    ).scan()[0]

    assert not result.ready
    assert len(
        result.missing_shaders
    ) == 1


def test_reference_preset_is_resolved(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    base = root / "base.slangp"
    base.write_text(
        'shaders = "0"\n',
        encoding="utf-8",
    )

    child = root / "child.slangp"
    child.write_text(
        '#reference "base.slangp"\n',
        encoding="utf-8",
    )

    results = {
        item.preset_path.name: item
        for item in ShaderService(
            root
        ).scan()
    }

    assert results[
        "child.slangp"
    ].shader_paths == (
        base.resolve(),
    )


def test_duplicate_references_are_normalized(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    shader = root / "pass.slang"
    shader.write_text(
        "shader",
        encoding="utf-8",
    )

    (
        root / "preset.slangp"
    ).write_text(
        (
            'shader0 = "pass.slang"\n'
            'shader1 = "pass.slang"\n'
        ),
        encoding="utf-8",
    )

    result = ShaderService(
        root
    ).scan()[0]

    assert result.shader_paths == (
        shader.resolve(),
    )


def test_ignores_non_shader_files(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    (
        root / "notes.txt"
    ).write_text(
        "notes",
        encoding="utf-8",
    )
    (
        root / "pass.slang"
    ).write_text(
        "shader",
        encoding="utf-8",
    )

    assert ShaderService(
        root
    ).scan() == []


def test_display_name_normalizes_separators(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    (
        root / "crt-royale_fast.slangp"
    ).write_text(
        'shaders = "0"\n',
        encoding="utf-8",
    )

    result = ShaderService(
        root
    ).scan()[0]

    assert result.name == (
        "crt royale fast"
    )


def test_scan_order_is_deterministic(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    for filename in (
        "Zulu.slangp",
        "alpha.slangp",
        "Middle.slangp",
    ):
        (
            root / filename
        ).write_text(
            'shaders = "0"\n',
            encoding="utf-8",
        )

    results = ShaderService(
        root
    ).scan()

    assert [
        result.preset_path.name
        for result in results
    ] == [
        "alpha.slangp",
        "Middle.slangp",
        "Zulu.slangp",
    ]


def test_preset_extension_is_case_insensitive(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    (
        root / "DISPLAY.SLANGP"
    ).write_text(
        'shaders = "0"\n',
        encoding="utf-8",
    )

    assert len(
        ShaderService(root).scan()
    ) == 1
