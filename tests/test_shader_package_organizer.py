import shutil

import pytest

from services.assets import (
    AssetOrganizer,
)
from services.assets import (
    organizer as organizer_module,
)


def make_package(
    tmp_path,
):
    source = tmp_path / "orions_angel"
    source.mkdir()

    presets = source / "Presets"
    presets.mkdir()

    shaders = source / "shaders"
    shaders.mkdir()

    includes = shaders / "include"
    includes.mkdir()

    graphics = source / "Graphics"
    graphics.mkdir()

    preset = presets / "console.slangp"
    preset.write_text(
        (
            'shaders = "1"\n'
            'shader0 = '
            '"../shaders/display.slang"\n'
        ),
        encoding="utf-8",
    )

    shader = shaders / "display.slang"
    shader.write_text(
        '#include "include/common.inc"\n',
        encoding="utf-8",
    )

    include = includes / "common.inc"
    include.write_text(
        "shared dependency\n",
        encoding="utf-8",
    )

    params = source / "global.params"
    params.write_text(
        "parameter data\n",
        encoding="utf-8",
    )

    image = graphics / "console.png"
    image.write_bytes(
        b"image-data"
    )

    readme = source / "README.md"
    readme.write_text(
        "package documentation\n",
        encoding="utf-8",
    )

    destination_root = (
        tmp_path / "managed-shaders"
    )
    destination_root.mkdir()

    return source, destination_root


def test_shader_package_plan_includes_all_files(
    tmp_path,
):
    source, destination_root = (
        make_package(tmp_path)
    )

    plan = (
        AssetOrganizer()
        .plan_shader_package(
            source,
            destination_root,
        )
    )

    assert plan.ready
    assert plan.category == "shader"
    assert plan.file_count == 6
    assert plan.total_bytes > 0
    assert plan.destination == (
        destination_root
        / "orions_angel"
    )


def test_shader_package_move_preserves_tree(
    tmp_path,
):
    source, destination_root = (
        make_package(tmp_path)
    )

    organizer = AssetOrganizer()
    plan = organizer.plan_shader_package(
        source,
        destination_root,
    )

    result = organizer.execute_package(
        plan
    )

    destination = (
        destination_root
        / "orions_angel"
    )

    assert result.file_count == 6
    assert result.destination == destination
    assert not source.exists()

    assert (
        destination
        / "Presets"
        / "console.slangp"
    ).is_file()
    assert (
        destination
        / "shaders"
        / "display.slang"
    ).is_file()
    assert (
        destination
        / "shaders"
        / "include"
        / "common.inc"
    ).is_file()
    assert (
        destination
        / "global.params"
    ).is_file()
    assert (
        destination
        / "Graphics"
        / "console.png"
    ).is_file()
    assert (
        destination
        / "README.md"
    ).is_file()


def test_existing_destination_blocks_package(
    tmp_path,
):
    source, destination_root = (
        make_package(tmp_path)
    )

    destination = (
        destination_root
        / source.name
    )
    destination.mkdir()

    plan = (
        AssetOrganizer()
        .plan_shader_package(
            source,
            destination_root,
        )
    )

    assert not plan.ready
    assert any(
        "destination already exists"
        in error
        for error in plan.errors
    )


def test_package_without_preset_is_rejected(
    tmp_path,
):
    source = tmp_path / "not-a-shader"
    source.mkdir()

    (
        source / "display.slang"
    ).write_text(
        "shader",
        encoding="utf-8",
    )

    destination = tmp_path / "shaders"
    destination.mkdir()

    plan = (
        AssetOrganizer()
        .plan_shader_package(
            source,
            destination,
        )
    )

    assert not plan.ready
    assert (
        "Directory contains no supported "
        "shader presets."
        in plan.errors
    )


def test_mixed_overlay_package_is_rejected(
    tmp_path,
):
    source, destination_root = (
        make_package(tmp_path)
    )

    (
        source / "mixed.cfg"
    ).write_text(
        (
            'overlays = "1"\n'
            'overlay0_overlay = '
            '"Graphics/console.png"\n'
        ),
        encoding="utf-8",
    )

    plan = (
        AssetOrganizer()
        .plan_shader_package(
            source,
            destination_root,
        )
    )

    assert not plan.ready
    assert any(
        "also contains overlay descriptors"
        in error
        for error in plan.errors
    )


def test_symbolic_link_package_is_rejected(
    tmp_path,
):
    source, destination_root = (
        make_package(tmp_path)
    )

    target = source / "README.md"
    link = source / "linked-readme"
    link.symlink_to(target)

    plan = (
        AssetOrganizer()
        .plan_shader_package(
            source,
            destination_root,
        )
    )

    assert not plan.ready
    assert (
        "Shader package contains "
        "symbolic links."
        in plan.errors
    )


def test_changed_package_is_not_moved(
    tmp_path,
):
    source, destination_root = (
        make_package(tmp_path)
    )

    organizer = AssetOrganizer()
    plan = organizer.plan_shader_package(
        source,
        destination_root,
    )

    (
        source / "new-file.txt"
    ).write_text(
        "changed",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Package contents changed"
        ),
    ):
        organizer.execute_package(
            plan
        )

    assert source.is_dir()
    assert not (
        destination_root
        / source.name
    ).exists()


def test_failed_package_move_preserves_source(
    tmp_path,
    monkeypatch,
):
    source, destination_root = (
        make_package(tmp_path)
    )

    organizer = AssetOrganizer()
    plan = organizer.plan_shader_package(
        source,
        destination_root,
    )

    def fail_move(
        source_name,
        destination_name,
    ):
        raise OSError(
            "simulated failure"
        )

    monkeypatch.setattr(
        organizer_module.shutil,
        "move",
        fail_move,
    )

    with pytest.raises(
        RuntimeError,
        match="Shader package move failed",
    ):
        organizer.execute_package(
            plan
        )

    assert source.is_dir()
    assert not (
        destination_root
        / source.name
    ).exists()


def test_package_executor_requires_package_plan():
    with pytest.raises(
        TypeError,
        match=(
            "Expected an AssetPackagePlan"
        ),
    ):
        AssetOrganizer().execute_package(
            object()
        )
