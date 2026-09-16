from unittest.mock import Mock

from services.presentation.hardware_state import (
    HardwareRuntimeState,
)
from ui.main_window import MainWindow


class PollHarness:
    _poll_process_lifecycle = (
        MainWindow._poll_process_lifecycle
    )


def make_window(
    state,
):
    window = PollHarness()

    lifecycle = Mock()
    lifecycle.state = state
    lifecycle.poll.return_value = Mock(
        name="polled_snapshot"
    )
    lifecycle.return_to_idle.return_value = Mock(
        name="idle_snapshot"
    )

    bridge = Mock()
    bridge.frame_for.side_effect = (
        lambda snapshot: (
            "frame",
            snapshot,
        )
    )

    details_a = Mock()
    details_b = Mock()

    window.process_lifecycle = lifecycle
    window.hardware_indicator_render_bridge = bridge
    window.hardware_indicator_render_frame = None
    window._launch_status_details = (
        details_a,
        details_b,
    )

    return (
        window,
        lifecycle,
        bridge,
        details_a,
        details_b,
    )


def test_exited_poll_notifies_details_then_returns_idle():
    (
        window,
        lifecycle,
        bridge,
        details_a,
        details_b,
    ) = make_window(
        HardwareRuntimeState.EXITED
    )

    window._poll_process_lifecycle()

    details_a.process_exited.assert_called_once_with()
    details_b.process_exited.assert_called_once_with()
    lifecycle.return_to_idle.assert_called_once_with()

    idle_snapshot = (
        lifecycle.return_to_idle.return_value
    )

    assert (
        window.hardware_indicator_render_frame
        == (
            "frame",
            idle_snapshot,
        )
    )

    assert bridge.frame_for.call_count == 2


def test_running_poll_does_not_consume_lifecycle():
    (
        window,
        lifecycle,
        bridge,
        details_a,
        details_b,
    ) = make_window(
        HardwareRuntimeState.RUNNING
    )

    window._poll_process_lifecycle()

    details_a.process_exited.assert_not_called()
    details_b.process_exited.assert_not_called()
    lifecycle.return_to_idle.assert_not_called()

    polled_snapshot = (
        lifecycle.poll.return_value
    )

    assert (
        window.hardware_indicator_render_frame
        == (
            "frame",
            polled_snapshot,
        )
    )

    bridge.frame_for.assert_called_once_with(
        polled_snapshot
    )


def test_idle_poll_does_not_emit_session_end():
    (
        window,
        lifecycle,
        _bridge,
        details_a,
        details_b,
    ) = make_window(
        HardwareRuntimeState.IDLE
    )

    window._poll_process_lifecycle()

    details_a.process_exited.assert_not_called()
    details_b.process_exited.assert_not_called()
    lifecycle.return_to_idle.assert_not_called()


def test_exit_consumption_is_one_shot_across_polls():
    (
        window,
        lifecycle,
        _bridge,
        details_a,
        details_b,
    ) = make_window(
        HardwareRuntimeState.EXITED
    )

    def return_to_idle():
        lifecycle.state = (
            HardwareRuntimeState.IDLE
        )
        return Mock(
            name="idle_snapshot"
        )

    lifecycle.return_to_idle.side_effect = (
        return_to_idle
    )

    window._poll_process_lifecycle()
    window._poll_process_lifecycle()

    details_a.process_exited.assert_called_once_with()
    details_b.process_exited.assert_called_once_with()
    lifecycle.return_to_idle.assert_called_once_with()
