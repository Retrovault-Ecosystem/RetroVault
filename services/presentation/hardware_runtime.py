from dataclasses import dataclass
from time import monotonic
from typing import Callable

from .hardware_state import (
    HardwareIndicatorPolicy,
    HardwareIndicatorSnapshot,
    HardwareRuntimeState,
    HardwareStateMachine,
)


@dataclass(frozen=True)
class HardwareTimingProfile:
    """
    Timing policy for transient RVV hardware feedback.

    Timing is presentation policy only. It does not issue emulator
    commands and does not depend on Qt, RetroArch, threads, or artwork.
    """

    reset_feedback_seconds: float = 2.0

    def __post_init__(self) -> None:
        if self.reset_feedback_seconds < 0:
            raise ValueError(
                "Reset feedback duration cannot be negative."
            )


class HardwareRuntimeOrchestrator:
    """
    Coordinate real RetroVault lifecycle events with RVV hardware state.

    The orchestrator deliberately separates:

      - application/emulator events
      - deterministic lifecycle state
      - platform-specific indicator policy
      - wall-clock timing
      - rendering

    A future application adapter may call ``poll()`` from a Qt timer,
    process callback, or other event loop without introducing those
    dependencies here.
    """

    def __init__(
        self,
        indicator_policy: HardwareIndicatorPolicy,
        *,
        timing: HardwareTimingProfile | None = None,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        if not isinstance(
            indicator_policy,
            HardwareIndicatorPolicy,
        ):
            raise TypeError(
                "Indicator policy must be a "
                "HardwareIndicatorPolicy."
            )

        if timing is None:
            timing = HardwareTimingProfile()

        if not isinstance(timing, HardwareTimingProfile):
            raise TypeError(
                "Timing must be a HardwareTimingProfile."
            )

        if not callable(clock):
            raise TypeError("Clock must be callable.")

        self._machine = HardwareStateMachine()
        self._policy = indicator_policy
        self._timing = timing
        self._clock = clock
        self._reset_deadline: float | None = None

    @property
    def state(self) -> HardwareRuntimeState:
        return self._machine.state

    @property
    def snapshot(self) -> HardwareIndicatorSnapshot:
        return self._policy.snapshot(
            self._machine.state
        )

    @property
    def reset_deadline(self) -> float | None:
        return self._reset_deadline

    def select_indicator_policy(
        self,
        indicator_policy: HardwareIndicatorPolicy,
    ) -> HardwareIndicatorSnapshot:
        """
        Select the platform policy for the next launch lifecycle.

        Policy selection is allowed only while RetroVault is idle or
        observing a completed EXITED lifecycle. An active emulator
        lifecycle cannot change platform hardware semantics underneath
        itself.
        """
        if not isinstance(
            indicator_policy,
            HardwareIndicatorPolicy,
        ):
            raise TypeError(
                "Indicator policy must be a "
                "HardwareIndicatorPolicy."
            )

        if self._machine.state not in {
            HardwareRuntimeState.IDLE,
            HardwareRuntimeState.EXITED,
        }:
            raise RuntimeError(
                "Indicator policy can only be selected "
                "while idle or exited."
            )

        self._policy = indicator_policy
        return self.snapshot

    def launch_requested(self) -> HardwareIndicatorSnapshot:
        """
        A user chose Play/Open in RetroVault.

        Platform policy may illuminate power immediately, before the
        emulator renders its first frame.
        """

        self._clear_transient_timing()
        self._machine.launch_requested()
        return self.snapshot

    def running(self) -> HardwareIndicatorSnapshot:
        """
        The game/emulator is confirmed running or resumed.

        After reset this is the explicit event that restores the
        platform's normal running indicator state.
        """

        self.poll()
        self._machine.running()
        self._clear_transient_timing()
        return self.snapshot

    def reset_requested(self) -> HardwareIndicatorSnapshot:
        """
        RetroVault issued the reset command.

        The state enters RESET_REQUESTED immediately. The configured
        reset feedback remains active until ``poll()`` observes the
        deadline, at which point the state becomes RESET_TRANSITION.
        """

        self._machine.reset_requested()

        self._reset_deadline = (
            self._clock()
            + self._timing.reset_feedback_seconds
        )

        return self.snapshot

    def poll(self) -> HardwareIndicatorSnapshot:
        """
        Apply time-based state transitions without sleeping.

        This method is deterministic and safe to call frequently from
        an eventual UI/runtime event loop.
        """

        if (
            self._machine.state
            is HardwareRuntimeState.RESET_REQUESTED
            and self._reset_deadline is not None
            and self._clock() >= self._reset_deadline
        ):
            self._machine.reset_transition()
            self._reset_deadline = None

        return self.snapshot

    def stop_requested(self) -> HardwareIndicatorSnapshot:
        """RetroVault requested that the active game stop."""

        self._clear_transient_timing()
        self._machine.stop_requested()
        return self.snapshot

    def process_exited(self) -> HardwareIndicatorSnapshot:
        """
        The emulator process has exited.

        Unexpected process exits are normalized through STOP_REQUESTED
        so the deterministic state machine reaches EXITED safely.
        """

        self._clear_transient_timing()

        if self._machine.state in {
            HardwareRuntimeState.LAUNCH_REQUESTED,
            HardwareRuntimeState.RUNNING,
            HardwareRuntimeState.RESET_REQUESTED,
            HardwareRuntimeState.RESET_TRANSITION,
        }:
            self._machine.stop_requested()

        if (
            self._machine.state
            is HardwareRuntimeState.STOP_REQUESTED
        ):
            self._machine.exited()

        return self.snapshot

    def idle(self) -> HardwareIndicatorSnapshot:
        """
        Return an exited lifecycle to RetroVault browsing/idle state.
        """

        self._clear_transient_timing()
        self._machine.idle()
        return self.snapshot

    def launch_failed(self) -> HardwareIndicatorSnapshot:
        """
        Normalize a failed launch back to IDLE.

        This guarantees that launch-time indicator feedback cannot
        remain illuminated after the emulator fails to start.
        """

        self._clear_transient_timing()

        if (
            self._machine.state
            is not HardwareRuntimeState.LAUNCH_REQUESTED
        ):
            raise RuntimeError(
                "Launch failure requires a pending launch."
            )

        self._machine.stop_requested()
        self._machine.exited()
        self._machine.idle()

        return self.snapshot

    def _clear_transient_timing(self) -> None:
        self._reset_deadline = None
