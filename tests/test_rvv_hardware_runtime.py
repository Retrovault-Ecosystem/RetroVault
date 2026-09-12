import pytest

from services.presentation.hardware_runtime import (
    HardwareRuntimeOrchestrator,
    HardwareTimingProfile,
)
from services.presentation.hardware_state import (
    HardwareIndicatorSnapshot,
    HardwareRuntimeState,
    IndicatorState,
    NESHardwareIndicatorPolicy,
)


class FakeClock:
    def __init__(self) -> None:
        self.now = 100.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def make_nes_runtime(
    *,
    reset_seconds: float = 2.0,
):
    clock = FakeClock()

    runtime = HardwareRuntimeOrchestrator(
        NESHardwareIndicatorPolicy(),
        timing=HardwareTimingProfile(
            reset_feedback_seconds=reset_seconds,
        ),
        clock=clock,
    )

    return runtime, clock


def test_runtime_starts_idle_with_indicators_off():
    runtime, _ = make_nes_runtime()

    assert runtime.state is HardwareRuntimeState.IDLE
    assert runtime.snapshot == HardwareIndicatorSnapshot()


def test_launch_request_turns_nes_power_green_immediately():
    runtime, _ = make_nes_runtime()

    snapshot = runtime.launch_requested()

    assert (
        runtime.state
        is HardwareRuntimeState.LAUNCH_REQUESTED
    )
    assert snapshot.power is IndicatorState.GREEN


def test_running_keeps_nes_power_green():
    runtime, _ = make_nes_runtime()

    runtime.launch_requested()
    snapshot = runtime.running()

    assert runtime.state is HardwareRuntimeState.RUNNING
    assert snapshot.power is IndicatorState.GREEN


def test_reset_turns_power_red_immediately():
    runtime, clock = make_nes_runtime()

    runtime.launch_requested()
    runtime.running()

    snapshot = runtime.reset_requested()

    assert (
        runtime.state
        is HardwareRuntimeState.RESET_REQUESTED
    )
    assert snapshot.power is IndicatorState.RED
    assert runtime.reset_deadline == pytest.approx(
        clock.now + 2.0
    )


def test_reset_stays_red_before_two_second_deadline():
    runtime, clock = make_nes_runtime()

    runtime.launch_requested()
    runtime.running()
    runtime.reset_requested()

    clock.advance(1.999)

    snapshot = runtime.poll()

    assert (
        runtime.state
        is HardwareRuntimeState.RESET_REQUESTED
    )
    assert snapshot.power is IndicatorState.RED


def test_reset_turns_off_at_two_second_deadline():
    runtime, clock = make_nes_runtime()

    runtime.launch_requested()
    runtime.running()
    runtime.reset_requested()

    clock.advance(2.0)

    snapshot = runtime.poll()

    assert (
        runtime.state
        is HardwareRuntimeState.RESET_TRANSITION
    )
    assert snapshot.power is IndicatorState.OFF
    assert runtime.reset_deadline is None


def test_power_stays_off_until_running_event_after_reset():
    runtime, clock = make_nes_runtime()

    runtime.launch_requested()
    runtime.running()
    runtime.reset_requested()

    clock.advance(2.0)
    runtime.poll()

    clock.advance(30.0)

    snapshot = runtime.poll()

    assert (
        runtime.state
        is HardwareRuntimeState.RESET_TRANSITION
    )
    assert snapshot.power is IndicatorState.OFF


def test_running_event_restores_green_after_reset():
    runtime, clock = make_nes_runtime()

    runtime.launch_requested()
    runtime.running()
    runtime.reset_requested()

    clock.advance(2.0)
    runtime.poll()

    snapshot = runtime.running()

    assert runtime.state is HardwareRuntimeState.RUNNING
    assert snapshot.power is IndicatorState.GREEN


def test_stop_immediately_returns_indicators_off():
    runtime, _ = make_nes_runtime()

    runtime.launch_requested()
    runtime.running()

    snapshot = runtime.stop_requested()

    assert (
        runtime.state
        is HardwareRuntimeState.STOP_REQUESTED
    )
    assert snapshot == HardwareIndicatorSnapshot()


def test_process_exit_reaches_exited_with_indicators_off():
    runtime, _ = make_nes_runtime()

    runtime.launch_requested()
    runtime.running()

    snapshot = runtime.process_exited()

    assert runtime.state is HardwareRuntimeState.EXITED
    assert snapshot == HardwareIndicatorSnapshot()


def test_unexpected_exit_during_reset_clears_timer_and_lights():
    runtime, _ = make_nes_runtime()

    runtime.launch_requested()
    runtime.running()
    runtime.reset_requested()

    snapshot = runtime.process_exited()

    assert runtime.state is HardwareRuntimeState.EXITED
    assert runtime.reset_deadline is None
    assert snapshot == HardwareIndicatorSnapshot()


def test_launch_failure_returns_clean_idle_state():
    runtime, _ = make_nes_runtime()

    runtime.launch_requested()

    snapshot = runtime.launch_failed()

    assert runtime.state is HardwareRuntimeState.IDLE
    assert snapshot == HardwareIndicatorSnapshot()


def test_idle_after_normal_exit():
    runtime, _ = make_nes_runtime()

    runtime.launch_requested()
    runtime.running()
    runtime.stop_requested()
    runtime.process_exited()

    snapshot = runtime.idle()

    assert runtime.state is HardwareRuntimeState.IDLE
    assert snapshot == HardwareIndicatorSnapshot()


def test_reset_duration_is_configurable():
    runtime, clock = make_nes_runtime(
        reset_seconds=5.0
    )

    runtime.launch_requested()
    runtime.running()
    runtime.reset_requested()

    clock.advance(4.99)

    assert (
        runtime.poll().power
        is IndicatorState.RED
    )

    clock.advance(0.01)

    assert (
        runtime.poll().power
        is IndicatorState.OFF
    )


def test_negative_reset_duration_is_rejected():
    with pytest.raises(
        ValueError,
        match="cannot be negative",
    ):
        HardwareTimingProfile(
            reset_feedback_seconds=-1.0
        )


def test_launch_failure_requires_pending_launch():
    runtime, _ = make_nes_runtime()

    with pytest.raises(
        RuntimeError,
        match="requires a pending launch",
    ):
        runtime.launch_failed()
