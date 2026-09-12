from unittest.mock import Mock

import pytest

from services.presentation.hardware_runtime import (
    HardwareRuntimeOrchestrator,
)
from services.presentation.hardware_state import (
    HardwareRuntimeState,
    IndicatorState,
    NESHardwareIndicatorPolicy,
)
from services.presentation.process_lifecycle import (
    ProcessLifecycleAdapter,
)


class FakeSession:
    def __init__(self):
        self.active_process = None
        self.clear_count = 0

    def process_running(self):
        if self.active_process is None:
            return False

        return self.active_process.poll() is None

    def clear_exited_process(self):
        if self.active_process is None:
            return None

        if self.active_process.poll() is None:
            return None

        process = self.active_process
        self.active_process = None
        self.clear_count += 1

        return process


def make_adapter():
    runtime = HardwareRuntimeOrchestrator(
        NESHardwareIndicatorPolicy()
    )
    session = FakeSession()

    adapter = ProcessLifecycleAdapter(
        runtime,
        session,
    )

    return adapter, session


def test_adapter_starts_idle_and_off():
    adapter, _session = make_adapter()

    assert adapter.state is HardwareRuntimeState.IDLE
    assert adapter.snapshot.power is IndicatorState.OFF


def test_launch_request_immediately_turns_nes_power_green():
    adapter, _session = make_adapter()

    snapshot = adapter.launch_requested()

    assert adapter.state is HardwareRuntimeState.LAUNCH_REQUESTED
    assert snapshot.power is IndicatorState.GREEN


def test_successful_live_process_becomes_running():
    adapter, session = make_adapter()

    process = Mock()
    process.poll.return_value = None
    session.active_process = process

    adapter.launch_requested()

    snapshot = adapter.launch_result(
        {"success": True}
    )

    assert adapter.state is HardwareRuntimeState.RUNNING
    assert snapshot.power is IndicatorState.GREEN


def test_failed_launch_returns_to_idle_and_off():
    adapter, _session = make_adapter()

    adapter.launch_requested()

    snapshot = adapter.launch_result(
        {
            "success": False,
            "error": "spawn failed",
        }
    )

    assert adapter.state is HardwareRuntimeState.IDLE
    assert snapshot.power is IndicatorState.OFF


def test_success_without_owned_process_is_treated_as_failed():
    adapter, session = make_adapter()

    adapter.launch_requested()

    snapshot = adapter.launch_result(
        {"success": True}
    )

    assert adapter.state is HardwareRuntimeState.IDLE
    assert snapshot.power is IndicatorState.OFF
    assert session.active_process is None


def test_success_with_already_exited_process_is_treated_as_failed():
    adapter, session = make_adapter()

    process = Mock()
    process.poll.return_value = 7
    session.active_process = process

    adapter.launch_requested()

    snapshot = adapter.launch_result(
        {"success": True}
    )

    assert adapter.state is HardwareRuntimeState.IDLE
    assert snapshot.power is IndicatorState.OFF
    assert session.active_process is None
    assert session.clear_count == 1


def test_poll_keeps_running_process_active():
    adapter, session = make_adapter()

    process = Mock()
    process.poll.return_value = None
    session.active_process = process

    adapter.launch_requested()
    adapter.launch_result(
        {"success": True}
    )

    snapshot = adapter.poll()

    assert adapter.state is HardwareRuntimeState.RUNNING
    assert snapshot.power is IndicatorState.GREEN
    assert session.active_process is process
    assert session.clear_count == 0


def test_poll_detects_process_exit_and_turns_power_off():
    adapter, session = make_adapter()

    process = Mock()
    process.poll.return_value = None
    session.active_process = process

    adapter.launch_requested()
    adapter.launch_result(
        {"success": True}
    )

    process.poll.return_value = 0

    snapshot = adapter.poll()

    assert adapter.state is HardwareRuntimeState.EXITED
    assert snapshot.power is IndicatorState.OFF
    assert session.active_process is None
    assert session.clear_count == 1


def test_nonzero_process_exit_is_still_exit():
    adapter, session = make_adapter()

    process = Mock()
    process.poll.return_value = None
    session.active_process = process

    adapter.launch_requested()
    adapter.launch_result(
        {"success": True}
    )

    process.poll.return_value = 23

    adapter.poll()

    assert adapter.state is HardwareRuntimeState.EXITED
    assert adapter.snapshot.power is IndicatorState.OFF
    assert session.active_process is None


def test_exited_lifecycle_can_return_to_idle():
    adapter, session = make_adapter()

    process = Mock()
    process.poll.return_value = None
    session.active_process = process

    adapter.launch_requested()
    adapter.launch_result(
        {"success": True}
    )

    process.poll.return_value = 0
    adapter.poll()

    snapshot = adapter.return_to_idle()

    assert adapter.state is HardwareRuntimeState.IDLE
    assert snapshot.power is IndicatorState.OFF


def test_launch_result_requires_pending_launch():
    adapter, session = make_adapter()

    process = Mock()
    process.poll.return_value = None
    session.active_process = process

    with pytest.raises(
        RuntimeError,
        match="pending launch request",
    ):
        adapter.launch_result(
            {"success": True}
        )


def test_launch_result_requires_dictionary():
    adapter, _session = make_adapter()

    adapter.launch_requested()

    with pytest.raises(
        TypeError,
        match="dictionary",
    ):
        adapter.launch_result(True)


def test_session_requires_process_lifecycle_surface():
    runtime = HardwareRuntimeOrchestrator(
        NESHardwareIndicatorPolicy()
    )

    with pytest.raises(
        TypeError,
        match="process lifecycle surface",
    ):
        ProcessLifecycleAdapter(
            runtime,
            object(),
        )


def test_runtime_type_is_enforced():
    session = FakeSession()

    with pytest.raises(
        TypeError,
        match="HardwareRuntimeOrchestrator",
    ):
        ProcessLifecycleAdapter(
            object(),
            session,
        )


def test_explicit_launch_failed_returns_pending_request_to_idle():
    adapter, _session = make_adapter()

    adapter.launch_requested()

    snapshot = adapter.launch_failed()

    assert adapter.state is HardwareRuntimeState.IDLE
    assert snapshot.power is IndicatorState.OFF


def test_explicit_launch_failed_requires_pending_request():
    adapter, _session = make_adapter()

    with pytest.raises(
        RuntimeError,
        match="pending launch request",
    ):
        adapter.launch_failed()
