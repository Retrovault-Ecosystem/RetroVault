import pytest

from services.presentation.hardware_state import (
    HardwareIndicatorPolicy,
    HardwareIndicatorSnapshot,
    HardwareRuntimeState,
    HardwareStateMachine,
    IndicatorState,
    NESHardwareIndicatorPolicy,
)


def test_machine_starts_idle():
    machine = HardwareStateMachine()

    assert machine.state is HardwareRuntimeState.IDLE


def test_launch_to_running_lifecycle():
    machine = HardwareStateMachine()

    assert (
        machine.launch_requested()
        is HardwareRuntimeState.LAUNCH_REQUESTED
    )

    assert (
        machine.running()
        is HardwareRuntimeState.RUNNING
    )


def test_nes_power_is_off_while_idle():
    policy = NESHardwareIndicatorPolicy()

    assert policy.snapshot(
        HardwareRuntimeState.IDLE
    ) == HardwareIndicatorSnapshot()


def test_nes_power_is_green_immediately_on_launch_request():
    policy = NESHardwareIndicatorPolicy()

    snapshot = policy.snapshot(
        HardwareRuntimeState.LAUNCH_REQUESTED
    )

    assert snapshot.power is IndicatorState.GREEN
    assert snapshot.reset is IndicatorState.OFF


def test_nes_power_remains_green_while_running():
    policy = NESHardwareIndicatorPolicy()

    snapshot = policy.snapshot(
        HardwareRuntimeState.RUNNING
    )

    assert snapshot.power is IndicatorState.GREEN


def test_nes_reset_request_temporarily_maps_power_red():
    policy = NESHardwareIndicatorPolicy()

    snapshot = policy.snapshot(
        HardwareRuntimeState.RESET_REQUESTED
    )

    assert snapshot.power is IndicatorState.RED
    assert snapshot.reset is IndicatorState.OFF


def test_nes_reset_transition_maps_power_off():
    policy = NESHardwareIndicatorPolicy()

    snapshot = policy.snapshot(
        HardwareRuntimeState.RESET_TRANSITION
    )

    assert snapshot.power is IndicatorState.OFF


def test_nes_power_returns_green_after_reset_transition():
    machine = HardwareStateMachine()
    policy = NESHardwareIndicatorPolicy()

    machine.launch_requested()
    machine.running()
    machine.reset_requested()

    assert (
        policy.snapshot(machine.state).power
        is IndicatorState.RED
    )

    machine.reset_transition()

    assert (
        policy.snapshot(machine.state).power
        is IndicatorState.OFF
    )

    machine.running()

    assert (
        policy.snapshot(machine.state).power
        is IndicatorState.GREEN
    )


def test_nes_indicators_are_off_after_stop_and_exit():
    machine = HardwareStateMachine()
    policy = NESHardwareIndicatorPolicy()

    machine.launch_requested()
    machine.running()

    machine.stop_requested()

    assert policy.snapshot(
        machine.state
    ) == HardwareIndicatorSnapshot()

    machine.exited()

    assert policy.snapshot(
        machine.state
    ) == HardwareIndicatorSnapshot()

    machine.idle()

    assert policy.snapshot(
        machine.state
    ) == HardwareIndicatorSnapshot()


def test_reset_requires_running_game():
    machine = HardwareStateMachine()

    with pytest.raises(
        RuntimeError,
        match="Reset can only be requested while running",
    ):
        machine.reset_requested()


def test_running_requires_launch_or_reset_transition():
    machine = HardwareStateMachine()

    with pytest.raises(
        RuntimeError,
        match="Running requires launch or reset transition",
    ):
        machine.running()


def test_base_policy_has_no_invented_indicators():
    policy = HardwareIndicatorPolicy()

    for state in HardwareRuntimeState:
        assert policy.snapshot(
            state
        ) == HardwareIndicatorSnapshot()


def test_policy_rejects_untyped_state():
    policy = NESHardwareIndicatorPolicy()

    with pytest.raises(
        TypeError,
        match="Hardware state must be",
    ):
        policy.snapshot("running")
