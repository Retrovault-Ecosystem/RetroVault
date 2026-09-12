from dataclasses import dataclass
from enum import Enum


class HardwareRuntimeState(str, Enum):
    """
    Emulator lifecycle state visible to RVV interactive hardware.

    This model is presentation-facing and emulator-agnostic.
    It does not contain NES-, RetroArch-, Qt-, or artwork-specific policy.
    """

    IDLE = "idle"
    LAUNCH_REQUESTED = "launch_requested"
    RUNNING = "running"
    RESET_REQUESTED = "reset_requested"
    RESET_TRANSITION = "reset_transition"
    STOP_REQUESTED = "stop_requested"
    EXITED = "exited"


class IndicatorState(str, Enum):
    """Visual state of one interactive hardware indicator."""

    OFF = "off"
    GREEN = "green"
    RED = "red"
    DIM_RED = "dim_red"


@dataclass(frozen=True)
class HardwareIndicatorSnapshot:
    """
    Immutable presentation snapshot.

    A platform-specific policy converts HardwareRuntimeState into
    one of these snapshots. Rendering is deliberately outside this
    foundation.
    """

    power: IndicatorState = IndicatorState.OFF
    reset: IndicatorState = IndicatorState.OFF


class HardwareIndicatorPolicy:
    """
    Base policy for RVV interactive hardware feedback.

    Platforms override indicator behavior only when the represented
    hardware actually exposes an appropriate visual indicator.
    """

    def snapshot(
        self,
        state: HardwareRuntimeState,
    ) -> HardwareIndicatorSnapshot:
        if not isinstance(state, HardwareRuntimeState):
            raise TypeError(
                "Hardware state must be a HardwareRuntimeState."
            )

        return HardwareIndicatorSnapshot()


class NESHardwareIndicatorPolicy(HardwareIndicatorPolicy):
    """
    RetroVault NES interactive presentation policy.

    RetroVault presentation behavior:

      IDLE
          indicators off

      LAUNCH_REQUESTED
          power immediately green

      RUNNING
          power green

      RESET_REQUESTED
          power red

      RESET_TRANSITION
          power briefly off

      STOP_REQUESTED
          indicators off

      EXITED
          indicators off

    Timing and emulator lifecycle events are owned by later runtime
    orchestration. This class only maps state to presentation.
    """

    def snapshot(
        self,
        state: HardwareRuntimeState,
    ) -> HardwareIndicatorSnapshot:
        if not isinstance(state, HardwareRuntimeState):
            raise TypeError(
                "Hardware state must be a HardwareRuntimeState."
            )

        if state in {
            HardwareRuntimeState.LAUNCH_REQUESTED,
            HardwareRuntimeState.RUNNING,
        }:
            return HardwareIndicatorSnapshot(
                power=IndicatorState.GREEN,
            )

        if state is HardwareRuntimeState.RESET_REQUESTED:
            return HardwareIndicatorSnapshot(
                power=IndicatorState.RED,
            )

        return HardwareIndicatorSnapshot()


class HardwareStateMachine:
    """
    Small deterministic lifecycle model for RVV hardware feedback.

    Event sources are intentionally external. RetroVault launch,
    emulator process lifecycle, reset, and stop integration will drive
    this model through the explicit transition methods below.
    """

    def __init__(self) -> None:
        self._state = HardwareRuntimeState.IDLE

    @property
    def state(self) -> HardwareRuntimeState:
        return self._state

    def launch_requested(self) -> HardwareRuntimeState:
        if self._state not in {
            HardwareRuntimeState.IDLE,
            HardwareRuntimeState.EXITED,
        }:
            raise RuntimeError(
                "Launch can only be requested from idle or exited."
            )

        self._state = HardwareRuntimeState.LAUNCH_REQUESTED
        return self._state

    def running(self) -> HardwareRuntimeState:
        if self._state not in {
            HardwareRuntimeState.LAUNCH_REQUESTED,
            HardwareRuntimeState.RESET_TRANSITION,
        }:
            raise RuntimeError(
                "Running requires launch or reset transition."
            )

        self._state = HardwareRuntimeState.RUNNING
        return self._state

    def reset_requested(self) -> HardwareRuntimeState:
        if self._state is not HardwareRuntimeState.RUNNING:
            raise RuntimeError(
                "Reset can only be requested while running."
            )

        self._state = HardwareRuntimeState.RESET_REQUESTED
        return self._state

    def reset_transition(self) -> HardwareRuntimeState:
        if self._state is not HardwareRuntimeState.RESET_REQUESTED:
            raise RuntimeError(
                "Reset transition requires a reset request."
            )

        self._state = HardwareRuntimeState.RESET_TRANSITION
        return self._state

    def stop_requested(self) -> HardwareRuntimeState:
        if self._state not in {
            HardwareRuntimeState.LAUNCH_REQUESTED,
            HardwareRuntimeState.RUNNING,
            HardwareRuntimeState.RESET_REQUESTED,
            HardwareRuntimeState.RESET_TRANSITION,
        }:
            raise RuntimeError(
                "Stop requires an active launch lifecycle."
            )

        self._state = HardwareRuntimeState.STOP_REQUESTED
        return self._state

    def exited(self) -> HardwareRuntimeState:
        if self._state is not HardwareRuntimeState.STOP_REQUESTED:
            raise RuntimeError(
                "Exit requires a stop request."
            )

        self._state = HardwareRuntimeState.EXITED
        return self._state

    def idle(self) -> HardwareRuntimeState:
        if self._state is not HardwareRuntimeState.EXITED:
            raise RuntimeError(
                "Idle requires an exited lifecycle."
            )

        self._state = HardwareRuntimeState.IDLE
        return self._state
