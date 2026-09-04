import shutil

import pytest

from services.assets import (
    AssetOrganizer,
)
from services.assets import (
    organizer as organizer_module,
)


def make_layout(
    tmp_path,
):
    source = tmp_path / "orions_angel"
    source.mkdir()

    mega_wrapper = (
        source
        / "Mega_Bezel_V1.17.1_2024-04-14"
    )
    mega = mega_wrapper / "Mega_Bezel"
    mega.mkdir(
        parents=True
    )
    (
        mega / "base.slangp"
    ).write_text(
        "base",
        encoding="utf-8",
    )

    examples_wrapper = (
        source
        / (
            "HSM_Mega_Bezel_Examples_"
            "V1.5.0_2023-04-19"
        )
    )
    examples = (
        examples_wrapper
        / "HSM_Mega_Bezel_Examples"
    )
    examples.mkdir(
        parents=True
    )
    (
        examples / "example.slangp"
    ).write_text(
        "example",
        encoding="utf-8",
    )

    console = (
        source
        / "Orionsangel-Original-Console-main"
    )
    console.mkdir()
    (
        console / "console.slangp"
    ).write_text(
        "console",
        encoding="utf-8",
    )

    shaders = tmp_path / "shaders"
    shaders.mkdir()

    return (
        source,
        shaders,
        mega,
        examples,
        console,
    )


def test_layout_maps_documented_destinations(
    tmp_path,
):
    (
        source,
        shaders,
        mega,
        examples,
        console,
    ) = make_layout(tmp_path)

    plan = (
        AssetOrganizer()
        .plan_mega_bezel_layout(
            source,
            shaders,
        )
    )

    assert plan.ready
    assert len(plan.moves) == 3

    destinations = {
        move.source: move.destination
        for move in plan.moves
    }

    assert destinations[mega] == (
        shaders
        / "shaders_slang"
        / "bezel"
        / "Mega_Bezel"
    )
    assert destinations[examples] == (
        shaders
        / "Mega_Bezel_Packs"
        / "HSM_Mega_Bezel_Examples"
    )
    assert destinations[console] == (
        shaders
        / "Mega_Bezel_Packs"
        / (
            "Orionsangel-"
            "Original-Console-main"
        )
    )


def test_layout_reports_complete_totals(
    tmp_path,
):
    source, shaders, *_rest = (
        make_layout(tmp_path)
    )

    plan = (
        AssetOrganizer()
        .plan_mega_bezel_layout(
            source,
            shaders,
        )
    )

    assert plan.file_count == 3
    assert plan.total_bytes == (
        len(b"base")
        + len(b"example")
        + len(b"console")
    )


def test_layout_execution_moves_components(
    tmp_path,
):
    (
        source,
        shaders,
        mega,
        examples,
        console,
    ) = make_layout(tmp_path)

    organizer = AssetOrganizer()
    plan = organizer.plan_mega_bezel_layout(
        source,
        shaders,
    )
    result = organizer.execute_layout(
        plan
    )

    assert result.file_count == 3
    assert not mega.exists()
    assert not examples.exists()
    assert not console.exists()

    assert (
        shaders
        / "shaders_slang"
        / "bezel"
        / "Mega_Bezel"
        / "base.slangp"
    ).is_file()
    assert (
        shaders
        / "Mega_Bezel_Packs"
        / "HSM_Mega_Bezel_Examples"
        / "example.slangp"
    ).is_file()
    assert (
        shaders
        / "Mega_Bezel_Packs"
        / (
            "Orionsangel-"
            "Original-Console-main"
        )
        / "console.slangp"
    ).is_file()


def test_existing_destination_blocks_layout(
    tmp_path,
):
    source, shaders, *_rest = (
        make_layout(tmp_path)
    )

    destination = (
        shaders
        / "shaders_slang"
        / "bezel"
        / "Mega_Bezel"
    )
    destination.mkdir(
        parents=True
    )

    plan = (
        AssetOrganizer()
        .plan_mega_bezel_layout(
            source,
            shaders,
        )
    )

    assert not plan.ready
    assert any(
        "destination already exists"
        in error
        for error in plan.errors
    )


def test_missing_component_blocks_layout(
    tmp_path,
):
    (
        source,
        shaders,
        _mega,
        _examples,
        console,
    ) = make_layout(tmp_path)

    shutil.rmtree(console)

    plan = (
        AssetOrganizer()
        .plan_mega_bezel_layout(
            source,
            shaders,
        )
    )

    assert not plan.ready
    assert any(
        "was not found uniquely"
        in error
        for error in plan.errors
    )


def test_layout_change_blocks_execution(
    tmp_path,
):
    source, shaders, mega, *_rest = (
        make_layout(tmp_path)
    )

    organizer = AssetOrganizer()
    plan = organizer.plan_mega_bezel_layout(
        source,
        shaders,
    )

    (
        mega / "changed.txt"
    ).write_text(
        "changed",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="changed after planning",
    ):
        organizer.execute_layout(
            plan
        )


def test_layout_failure_rolls_back(
    tmp_path,
    monkeypatch,
):
    (
        source,
        shaders,
        mega,
        examples,
        console,
    ) = make_layout(tmp_path)

    organizer = AssetOrganizer()
    plan = organizer.plan_mega_bezel_layout(
        source,
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
                "simulated failure"
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
        match="were rolled back",
    ):
        organizer.execute_layout(
            plan
        )

    assert mega.is_dir()
    assert examples.is_dir()
    assert console.is_dir()

    assert not (
        shaders
        / "shaders_slang"
        / "bezel"
        / "Mega_Bezel"
    ).exists()


def test_layout_executor_requires_layout_plan():
    with pytest.raises(
        TypeError,
        match="Expected an AssetLayoutPlan",
    ):
        AssetOrganizer().execute_layout(
            object()
        )
