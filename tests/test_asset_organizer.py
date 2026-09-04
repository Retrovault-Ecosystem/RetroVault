from services.assets import (
    AssetOrganizer,
)


def make_roots(
    tmp_path,
):
    source = tmp_path / "import"
    overlays = tmp_path / "managed-overlays"
    shaders = tmp_path / "managed-shaders"

    source.mkdir()
    overlays.mkdir()
    shaders.mkdir()

    return source, overlays, shaders


def make_overlay(
    source,
):
    package = source / "bezels" / "nes"
    package.mkdir(
        parents=True
    )

    image = package / "frame.png"
    image.write_bytes(b"image")

    config = package / "duck.cfg"
    config.write_text(
        (
            'overlays = "1"\n'
            'overlay0_overlay = "frame.png"\n'
        ),
        encoding="utf-8",
    )

    return config, image


def test_missing_source_is_rejected(
    tmp_path,
):
    plan = AssetOrganizer().plan(
        tmp_path / "missing",
        tmp_path / "overlays",
        tmp_path / "shaders",
    )

    assert not plan.ready
    assert not plan.moves
    assert plan.errors == (
        "Import source is not a readable directory.",
    )


def test_overlay_package_is_discovered_recursively(
    tmp_path,
):
    source, overlays, shaders = (
        make_roots(tmp_path)
    )
    config, image = make_overlay(
        source
    )

    plan = AssetOrganizer().plan(
        source,
        overlays,
        shaders,
    )

    assert plan.ready
    assert {
        move.source
        for move in plan.moves
    } == {
        config,
        image,
    }
    assert {
        move.category
        for move in plan.moves
    } == {
        "overlay",
    }


def test_overlay_structure_is_preserved(
    tmp_path,
):
    source, overlays, shaders = (
        make_roots(tmp_path)
    )
    config, image = make_overlay(
        source
    )

    plan = AssetOrganizer().plan(
        source,
        overlays,
        shaders,
    )

    destinations = {
        move.source: move.destination
        for move in plan.moves
    }

    assert destinations[config] == (
        overlays
        / "bezels"
        / "nes"
        / "duck.cfg"
    )
    assert destinations[image] == (
        overlays
        / "bezels"
        / "nes"
        / "frame.png"
    )


def test_shader_files_are_discovered_recursively(
    tmp_path,
):
    source, overlays, shaders = (
        make_roots(tmp_path)
    )

    shader_directory = (
        source
        / "crt"
        / "passes"
    )
    shader_directory.mkdir(
        parents=True
    )

    preset = (
        source
        / "crt"
        / "display.slangp"
    )
    preset.write_text(
        'shaders = "1"\n',
        encoding="utf-8",
    )

    pass_file = (
        shader_directory
        / "display.slang"
    )
    pass_file.write_text(
        "void main() {}\n",
        encoding="utf-8",
    )

    plan = AssetOrganizer().plan(
        source,
        overlays,
        shaders,
    )

    shader_moves = [
        move
        for move in plan.moves
        if move.category == "shader"
    ]

    assert {
        move.source
        for move in shader_moves
    } == {
        preset,
        pass_file,
    }
    assert {
        move.destination
        for move in shader_moves
    } == {
        shaders / "crt" / "display.slangp",
        (
            shaders
            / "crt"
            / "passes"
            / "display.slang"
        ),
    }


def test_unrecognized_files_are_skipped(
    tmp_path,
):
    source, overlays, shaders = (
        make_roots(tmp_path)
    )

    unrelated = source / "notes.txt"
    unrelated.write_text(
        "not an asset",
        encoding="utf-8",
    )

    standalone_image = (
        source / "unknown.png"
    )
    standalone_image.write_bytes(
        b"image"
    )

    plan = AssetOrganizer().plan(
        source,
        overlays,
        shaders,
    )

    assert not plan.ready
    assert not plan.moves
    assert set(plan.skipped) == {
        unrelated,
        standalone_image,
    }


def test_non_overlay_cfg_is_skipped(
    tmp_path,
):
    source, overlays, shaders = (
        make_roots(tmp_path)
    )

    config = source / "retroarch.cfg"
    config.write_text(
        'video_driver = "gl"\n',
        encoding="utf-8",
    )

    plan = AssetOrganizer().plan(
        source,
        overlays,
        shaders,
    )

    assert config in plan.skipped
    assert not plan.moves


def test_missing_overlay_image_blocks_plan(
    tmp_path,
):
    source, overlays, shaders = (
        make_roots(tmp_path)
    )

    config = source / "broken.cfg"
    config.write_text(
        (
            'overlays = "1"\n'
            'overlay0_overlay = "missing.png"\n'
        ),
        encoding="utf-8",
    )

    plan = AssetOrganizer().plan(
        source,
        overlays,
        shaders,
    )

    assert not plan.ready
    assert any(
        "Overlay image is missing:"
        in error
        for error in plan.errors
    )


def test_reference_outside_source_blocks_plan(
    tmp_path,
):
    source, overlays, shaders = (
        make_roots(tmp_path)
    )

    outside = tmp_path / "outside.png"
    outside.write_bytes(b"image")

    config = source / "escape.cfg"
    config.write_text(
        (
            'overlays = "1"\n'
            'overlay0_overlay = "../outside.png"\n'
        ),
        encoding="utf-8",
    )

    plan = AssetOrganizer().plan(
        source,
        overlays,
        shaders,
    )

    assert not plan.ready
    assert any(
        "escapes the import source"
        in error
        for error in plan.errors
    )


def test_existing_destination_blocks_plan(
    tmp_path,
):
    source, overlays, shaders = (
        make_roots(tmp_path)
    )
    config, _image = make_overlay(
        source
    )

    destination = (
        overlays
        / config.relative_to(source)
    )
    destination.parent.mkdir(
        parents=True
    )
    destination.write_text(
        "existing",
        encoding="utf-8",
    )

    plan = AssetOrganizer().plan(
        source,
        overlays,
        shaders,
    )

    assert not plan.ready
    assert any(
        "Destination already exists:"
        in error
        for error in plan.errors
    )


def test_source_destination_overlap_is_rejected(
    tmp_path,
):
    source = tmp_path / "import"
    source.mkdir()

    plan = AssetOrganizer().plan(
        source,
        source / "overlays",
        tmp_path / "shaders",
    )

    assert not plan.ready
    assert (
        "Overlay destination overlaps "
        "the import source."
        in plan.errors
    )


def test_planning_never_moves_files(
    tmp_path,
):
    source, overlays, shaders = (
        make_roots(tmp_path)
    )
    config, image = make_overlay(
        source
    )

    plan = AssetOrganizer().plan(
        source,
        overlays,
        shaders,
    )

    assert plan.ready
    assert config.is_file()
    assert image.is_file()
    assert not any(
        move.destination.exists()
        for move in plan.moves
    )
