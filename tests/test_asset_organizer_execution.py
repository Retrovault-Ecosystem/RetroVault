import shutil

import pytest

from services.assets import (
    AssetOrganizer,
)
from services.assets import (
    organizer as organizer_module,
)


def make_roots(
    tmp_path,
):
    source = tmp_path / "import"
    overlays = tmp_path / "overlays"
    shaders = tmp_path / "shaders"

    source.mkdir()
    overlays.mkdir()
    shaders.mkdir()

    return source, overlays, shaders


def make_assets(
    source,
):
    overlay_package = (
        source / "bezels" / "nes"
    )
    overlay_package.mkdir(
        parents=True
    )

    image = (
        overlay_package / "frame.png"
    )
    image.write_bytes(
        b"overlay-image"
    )

    config = (
        overlay_package / "duck.cfg"
    )
    config.write_text(
        (
            'overlays = "1"\n'
            'overlay0_overlay = "frame.png"\n'
        ),
        encoding="utf-8",
    )

    shader_package = (
        source / "crt"
    )
    shader_package.mkdir()

    shader = (
        shader_package / "display.slang"
    )
    shader.write_text(
        "shader-content",
        encoding="utf-8",
    )

    return config, image, shader


def test_execute_moves_planned_assets(
    tmp_path,
):
    source, overlays, shaders = (
        make_roots(tmp_path)
    )
    config, image, shader = make_assets(
        source
    )

    organizer = AssetOrganizer()
    plan = organizer.plan(
        source,
        overlays,
        shaders,
    )

    result = organizer.execute(
        plan
    )

    assert result.moved_count == 3
    assert result.overlay_count == 2
    assert result.shader_count == 1

    assert not config.exists()
    assert not image.exists()
    assert not shader.exists()

    assert (
        overlays
        / "bezels"
        / "nes"
        / "duck.cfg"
    ).is_file()

    assert (
        overlays
        / "bezels"
        / "nes"
        / "frame.png"
    ).is_file()

    assert (
        shaders
        / "crt"
        / "display.slang"
    ).is_file()


def test_execute_preserves_file_contents(
    tmp_path,
):
    source, overlays, shaders = (
        make_roots(tmp_path)
    )
    _config, _image, _shader = (
        make_assets(source)
    )

    organizer = AssetOrganizer()
    result = organizer.execute(
        organizer.plan(
            source,
            overlays,
            shaders,
        )
    )

    assert result.moved_count == 3
    assert (
        overlays
        / "bezels"
        / "nes"
        / "frame.png"
    ).read_bytes() == b"overlay-image"

    assert (
        shaders
        / "crt"
        / "display.slang"
    ).read_text(
        encoding="utf-8"
    ) == "shader-content"


def test_execute_rejects_unready_plan(
    tmp_path,
):
    source, overlays, shaders = (
        make_roots(tmp_path)
    )

    organizer = AssetOrganizer()
    plan = organizer.plan(
        source,
        overlays,
        shaders,
    )

    assert not plan.ready

    with pytest.raises(
        ValueError,
        match="Asset plan is not ready",
    ):
        organizer.execute(plan)


def test_missing_source_blocks_all_moves(
    tmp_path,
):
    source, overlays, shaders = (
        make_roots(tmp_path)
    )
    config, image, shader = make_assets(
        source
    )

    organizer = AssetOrganizer()
    plan = organizer.plan(
        source,
        overlays,
        shaders,
    )

    config.unlink()

    with pytest.raises(
        ValueError,
        match=(
            "Planned source no longer exists"
        ),
    ):
        organizer.execute(plan)

    assert image.is_file()
    assert shader.is_file()
    assert not any(
        overlays.rglob("*")
    )
    assert not any(
        shaders.rglob("*")
    )


def test_late_destination_collision_blocks_all_moves(
    tmp_path,
):
    source, overlays, shaders = (
        make_roots(tmp_path)
    )
    config, image, shader = make_assets(
        source
    )

    organizer = AssetOrganizer()
    plan = organizer.plan(
        source,
        overlays,
        shaders,
    )

    collision = (
        overlays
        / "bezels"
        / "nes"
        / "duck.cfg"
    )
    collision.parent.mkdir(
        parents=True
    )
    collision.write_text(
        "existing",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=(
            "Planned destination now exists"
        ),
    ):
        organizer.execute(plan)

    assert config.is_file()
    assert image.is_file()
    assert shader.is_file()
    assert collision.read_text(
        encoding="utf-8"
    ) == "existing"


def test_failure_rolls_back_completed_moves(
    tmp_path,
    monkeypatch,
):
    source, overlays, shaders = (
        make_roots(tmp_path)
    )
    config, image, shader = make_assets(
        source
    )

    organizer = AssetOrganizer()
    plan = organizer.plan(
        source,
        overlays,
        shaders,
    )

    real_move = shutil.move
    calls = 0

    def failing_move(
        source_name,
        destination_name,
    ):
        nonlocal calls
        calls += 1

        if calls == 2:
            raise OSError(
                "simulated move failure"
            )

        return real_move(
            source_name,
            destination_name,
        )

    monkeypatch.setattr(
        organizer_module.shutil,
        "move",
        failing_move,
    )

    with pytest.raises(
        RuntimeError,
        match=(
            "completed moves were rolled back"
        ),
    ):
        organizer.execute(plan)

    assert config.is_file()
    assert image.is_file()
    assert shader.is_file()

    assert not any(
        path.is_file()
        for path in overlays.rglob("*")
    )
    assert not any(
        path.is_file()
        for path in shaders.rglob("*")
    )


def test_executor_requires_asset_plan():
    with pytest.raises(
        TypeError,
        match="Expected an AssetPlan",
    ):
        AssetOrganizer().execute(
            object()
        )
