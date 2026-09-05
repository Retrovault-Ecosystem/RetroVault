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


def test_runtime_wildcard_reference_is_not_missing(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    preset = root / "wildcard.slangp"
    preset.write_text(
        (
            '#reference "'
            'referenced-presets/'
            'Ref_$CORE$.slangp"\n'
        ),
        encoding="utf-8",
    )

    result = ShaderService(
        root
    ).scan()[0]

    assert result.missing_shaders == ()
    assert result.ready


def test_multiple_retroarch_runtime_tokens_are_dynamic(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    preset = root / "wildcards.slangp"
    preset.write_text(
        (
            '#reference "'
            'Ref_$CONTENT-DIR$_'
            '$VID-DRV-SHADER-EXT$.slangp"\n'
        ),
        encoding="utf-8",
    )

    result = ShaderService(
        root
    ).scan()[0]

    assert result.missing_shaders == ()
    assert result.ready


def test_shader_root_reference_resolves_from_root(
    tmp_path,
):
    root = tmp_path / "shaders"

    base = (
        root
        / "shaders_slang"
        / "bezel"
        / "Mega_Bezel"
        / "Presets"
        / "base.slangp"
    )
    base.parent.mkdir(
        parents=True
    )
    base.write_text(
        'shaders = "0"\n',
        encoding="utf-8",
    )

    pack = (
        root
        / "Mega_Bezel_Packs"
        / "Example"
    )
    pack.mkdir(
        parents=True
    )

    preset = pack / "console.slangp"
    preset.write_text(
        (
            '#reference "'
            'shaders_slang/bezel/'
            'Mega_Bezel/Presets/'
            'base.slangp"\n'
        ),
        encoding="utf-8",
    )

    result = {
        item.preset_path: item
        for item in ShaderService(
            root
        ).scan()
    }[preset]

    assert result.shader_paths == (
        base.resolve(),
    )
    assert result.missing_shaders == ()
    assert result.ready


def test_colon_shader_root_reference_resolves(
    tmp_path,
):
    root = tmp_path / "shaders"

    shader = (
        root
        / "shaders_slang"
        / "passes"
        / "display.slang"
    )
    shader.parent.mkdir(
        parents=True
    )
    shader.write_text(
        "shader",
        encoding="utf-8",
    )

    preset = root / "display.slangp"
    preset.write_text(
        (
            'shader0 = "'
            ':/shaders/'
            'shaders_slang/passes/'
            'display.slang"\n'
        ),
        encoding="utf-8",
    )

    result = {
        item.preset_path: item
        for item in ShaderService(
            root
        ).scan()
    }[preset]

    assert result.shader_paths == (
        shader.resolve(),
    )
    assert result.missing_shaders == ()


def test_foreign_retroarch_shader_path_is_portable(
    tmp_path,
):
    root = tmp_path / "shaders"

    dependency = (
        root
        / "blurs"
        / "shaders"
        / "royale"
        / "blur9x9.slang"
    )
    dependency.parent.mkdir(
        parents=True
    )
    dependency.write_text(
        "shader",
        encoding="utf-8",
    )

    preset = root / "portable.slangp"
    preset.write_text(
        (
            'shader0 = "'
            '/opt/retropie/configs/all/'
            'retroarch/shaders/'
            'blurs/shaders/royale/'
            'blur9x9.slang"\n'
        ),
        encoding="utf-8",
    )

    result = {
        item.preset_path: item
        for item in ShaderService(
            root
        ).scan()
    }[preset]

    assert result.shader_paths == (
        dependency.resolve(),
    )
    assert result.missing_shaders == ()


def test_unique_casefold_match_resolves_on_linux(
    tmp_path,
):
    root = tmp_path / "shaders"
    package = (
        root
        / "shaders_slang"
        / "hyllian"
    )
    package.mkdir(
        parents=True
    )

    shader = (
        package
        / "custom-bicubic-x.slang"
    )
    shader.write_text(
        "shader",
        encoding="utf-8",
    )

    preset = root / "case.slangp"
    preset.write_text(
        (
            'shader0 = "'
            'shaders_slang/hyllian/'
            'custom-bicubic-X.slang"\n'
        ),
        encoding="utf-8",
    )

    result = {
        item.preset_path: item
        for item in ShaderService(
            root
        ).scan()
    }[preset]

    assert result.shader_paths == (
        shader.resolve(),
    )
    assert result.missing_shaders == ()
    assert result.ready


def test_real_root_dependency_remains_missing(
    tmp_path,
):
    root = tmp_path / "shaders"
    root.mkdir()

    preset = root / "dependency.slangp"
    preset.write_text(
        (
            'shader0 = "'
            'blurs/shaders/royale/'
            'blur9x9.slang"\n'
        ),
        encoding="utf-8",
    )

    result = ShaderService(
        root
    ).scan()[0]

    assert not result.ready
    assert result.missing_shaders == (
        (
            root
            / "blurs"
            / "shaders"
            / "royale"
            / "blur9x9.slang"
        ).resolve(),
    )


def test_ambiguous_casefold_match_stays_missing(
    tmp_path,
):
    root = tmp_path / "shaders"
    package = root / "passes"
    package.mkdir(
        parents=True
    )

    (
        package / "PASS.slang"
    ).write_text(
        "one",
        encoding="utf-8",
    )
    (
        package / "Pass.slang"
    ).write_text(
        "two",
        encoding="utf-8",
    )

    preset = root / "ambiguous.slangp"
    preset.write_text(
        (
            'shader0 = "'
            'passes/pass.slang"\n'
        ),
        encoding="utf-8",
    )

    result = {
        item.preset_path: item
        for item in ShaderService(
            root
        ).scan()
    }[preset]

    assert not result.ready
    assert len(
        result.missing_shaders
    ) == 1


def test_mega_bezel_variation_uses_bounded_base_crt_fallback(
    tmp_path,
):
    root = tmp_path / "shaders"

    base = (
        root
        / "shaders_slang"
        / "bezel"
        / "Mega_Bezel"
        / "Presets"
        / "Base_CRT_Presets"
        / "MBZ__3__STD__GDV.slangp"
    )
    base.parent.mkdir(
        parents=True
    )
    base.write_text(
        'shaders = "0"\n',
        encoding="utf-8",
    )

    variation = (
        root
        / "shaders_slang"
        / "bezel"
        / "Mega_Bezel"
        / "Presets"
        / "Variations"
        / "FBNEO-Vertical__STD.slangp"
    )
    variation.parent.mkdir(
        parents=True
    )
    variation.write_text(
        (
            '#reference "'
            '../../../Base_CRT_Presets/'
            'MBZ__3__STD__GDV.slangp"\n'
        ),
        encoding="utf-8",
    )

    result = {
        item.preset_path: item
        for item in ShaderService(
            root
        ).scan()
    }[variation]

    assert result.shader_paths == (
        base.resolve(),
    )
    assert result.missing_shaders == ()
    assert result.ready


def test_mega_bezel_base_crt_fallback_is_not_global(
    tmp_path,
):
    root = tmp_path / "shaders"

    base = (
        root
        / "shaders_slang"
        / "bezel"
        / "Mega_Bezel"
        / "Presets"
        / "Base_CRT_Presets"
        / "MBZ__3__STD__GDV.slangp"
    )
    base.parent.mkdir(
        parents=True
    )
    base.write_text(
        'shaders = "0"\n',
        encoding="utf-8",
    )

    unrelated = (
        root
        / "unrelated"
        / "preset.slangp"
    )
    unrelated.parent.mkdir(
        parents=True
    )
    unrelated.write_text(
        (
            '#reference "'
            '../../../Base_CRT_Presets/'
            'MBZ__3__STD__GDV.slangp"\n'
        ),
        encoding="utf-8",
    )

    result = {
        item.preset_path: item
        for item in ShaderService(
            root
        ).scan()
    }[unrelated]

    assert not result.ready
    assert len(
        result.missing_shaders
    ) == 1
    assert result.shader_paths != (
        base.resolve(),
    )


def test_crt_super_xbr_uses_bounded_sibling_fallback(
    tmp_path,
):
    root = tmp_path / "shaders"

    package = (
        root
        / "shaders_slang"
        / "bezel"
        / "Mega_Bezel"
        / "shaders"
        / "hyllian"
        / "crt-super-xbr"
    )
    package.mkdir(
        parents=True
    )

    shader = (
        package
        / "linearize.slang"
    )
    shader.write_text(
        "shader",
        encoding="utf-8",
    )

    preset = (
        package
        / "crt-super-xbr.slangp"
    )
    preset.write_text(
        (
            'shader0 = "'
            'shaders/linearize.slang"\n'
        ),
        encoding="utf-8",
    )

    result = {
        item.preset_path: item
        for item in ShaderService(
            root
        ).scan()
    }[preset]

    assert result.shader_paths == (
        shader.resolve(),
    )
    assert result.missing_shaders == ()
    assert result.ready


def test_crt_super_xbr_fallback_is_not_package_wide(
    tmp_path,
):
    root = tmp_path / "shaders"

    package = (
        root
        / "shaders_slang"
        / "bezel"
        / "Mega_Bezel"
        / "shaders"
        / "hyllian"
        / "crt-super-xbr"
    )
    package.mkdir(
        parents=True
    )

    shader = (
        package
        / "linearize.slang"
    )
    shader.write_text(
        "shader",
        encoding="utf-8",
    )

    preset = (
        package
        / "other.slangp"
    )
    preset.write_text(
        (
            'shader0 = "'
            'shaders/linearize.slang"\n'
        ),
        encoding="utf-8",
    )

    result = {
        item.preset_path: item
        for item in ShaderService(
            root
        ).scan()
    }[preset]

    assert not result.ready
    assert len(
        result.missing_shaders
    ) == 1
    assert result.shader_paths != (
        shader.resolve(),
    )


def test_structural_fallback_does_not_hide_absent_dependency(
    tmp_path,
):
    root = tmp_path / "shaders"

    package = (
        root
        / "shaders_slang"
        / "bezel"
        / "Mega_Bezel"
        / "shaders"
        / "hyllian"
        / "crt-super-xbr"
    )
    package.mkdir(
        parents=True
    )

    preset = (
        package
        / "crt-super-xbr.slangp"
    )
    preset.write_text(
        (
            'shader0 = "'
            'shaders/not-installed.slang"\n'
        ),
        encoding="utf-8",
    )

    result = {
        item.preset_path: item
        for item in ShaderService(
            root
        ).scan()
    }[preset]

    assert not result.ready
    assert result.missing_shaders == (
        (
            package
            / "shaders"
            / "not-installed.slang"
        ).resolve(),
    )
