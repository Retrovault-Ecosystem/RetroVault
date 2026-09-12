import pytest

from services.presentation.hardware_state import (
    HardwareIndicatorSnapshot,
    IndicatorState,
)
from services.presentation.indicator_rendering import (
    HardwareIndicatorRenderBridge,
    IndicatorRenderFrame,
    IndicatorRenderInstruction,
)


def make_bridge():
    return HardwareIndicatorRenderBridge()


def test_all_off_snapshot_produces_all_off_frame():
    frame = make_bridge().frame_for(
        HardwareIndicatorSnapshot()
    )

    assert isinstance(
        frame,
        IndicatorRenderFrame,
    )

    assert (
        frame.instruction_for("power").state
        is IndicatorState.OFF
    )

    assert (
        frame.instruction_for("reset").state
        is IndicatorState.OFF
    )


def test_nes_launch_snapshot_preserves_green_power():
    frame = make_bridge().frame_for(
        HardwareIndicatorSnapshot(
            power=IndicatorState.GREEN,
            reset=IndicatorState.OFF,
        )
    )

    assert (
        frame.instruction_for("power").state
        is IndicatorState.GREEN
    )

    assert (
        frame.instruction_for("reset").state
        is IndicatorState.OFF
    )


def test_reset_feedback_snapshot_preserves_red_power():
    frame = make_bridge().frame_for(
        HardwareIndicatorSnapshot(
            power=IndicatorState.RED,
            reset=IndicatorState.OFF,
        )
    )

    assert (
        frame.instruction_for("power").state
        is IndicatorState.RED
    )


def test_dim_red_state_is_preserved_without_interpretation():
    frame = make_bridge().frame_for(
        HardwareIndicatorSnapshot(
            power=IndicatorState.OFF,
            reset=IndicatorState.DIM_RED,
        )
    )

    assert (
        frame.instruction_for("reset").state
        is IndicatorState.DIM_RED
    )


def test_frame_contains_deterministic_indicator_order():
    frame = make_bridge().frame_for(
        HardwareIndicatorSnapshot()
    )

    assert tuple(
        instruction.indicator
        for instruction in frame.instructions
    ) == (
        "power",
        "reset",
    )


def test_instruction_lookup_is_case_insensitive():
    frame = make_bridge().frame_for(
        HardwareIndicatorSnapshot(
            power=IndicatorState.GREEN,
        )
    )

    assert (
        frame.instruction_for("POWER").state
        is IndicatorState.GREEN
    )


def test_instruction_lookup_trims_whitespace():
    frame = make_bridge().frame_for(
        HardwareIndicatorSnapshot(
            power=IndicatorState.GREEN,
        )
    )

    assert (
        frame.instruction_for("  power  ").state
        is IndicatorState.GREEN
    )


def test_unknown_indicator_is_rejected():
    frame = make_bridge().frame_for(
        HardwareIndicatorSnapshot()
    )

    with pytest.raises(
        KeyError,
        match="Unknown indicator",
    ):
        frame.instruction_for("drive")


def test_empty_indicator_lookup_is_rejected():
    frame = make_bridge().frame_for(
        HardwareIndicatorSnapshot()
    )

    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        frame.instruction_for("   ")


def test_non_string_indicator_lookup_is_rejected():
    frame = make_bridge().frame_for(
        HardwareIndicatorSnapshot()
    )

    with pytest.raises(
        TypeError,
        match="must be a string",
    ):
        frame.instruction_for(None)


def test_bridge_rejects_non_snapshot_input():
    with pytest.raises(
        TypeError,
        match="HardwareIndicatorSnapshot",
    ):
        make_bridge().frame_for(
            {"power": "green"}
        )


def test_instruction_rejects_empty_name():
    with pytest.raises(
        ValueError,
        match="cannot be empty",
    ):
        IndicatorRenderInstruction(
            indicator=" ",
            state=IndicatorState.OFF,
        )


def test_instruction_rejects_invalid_state():
    with pytest.raises(
        TypeError,
        match="IndicatorState",
    ):
        IndicatorRenderInstruction(
            indicator="power",
            state="green",
        )


def test_frame_is_immutable():
    frame = make_bridge().frame_for(
        HardwareIndicatorSnapshot()
    )

    with pytest.raises(
        AttributeError,
    ):
        frame.instructions = ()
