from typing import Protocol

from .hardware_policy import HardwareIndicatorPolicyResolver
from .hardware_runtime import HardwareRuntimeOrchestrator
from .hardware_state import (
    HardwareIndicatorSnapshot,
    HardwareRuntimeState,
)


class ProcessSession(Protocol):
    """
    Minimal process-session surface consumed by RVV.

    RVV depends only on process facts. It does not depend on RetroArch,
    subprocess, Qt, or a concrete launcher implementation.
    """

    @property
    def active_process(self):
        ...

    def process_running(self) -> bool:
        ...

    def clear_exited_process(self):
        ...


class ProcessLifecycleAdapter:
    """
    Translate application/process lifecycle facts into RVV hardware state.

    Responsibilities:

      - accept the user's launch-request event immediately
      - normalize launch success/failure into RVV lifecycle state
      - observe whether the owned emulator process remains alive
      - normalize process exit into RVV EXITED state
      - release ownership of an exited process

    This adapter deliberately does not:

      - launch an emulator
      - issue reset/stop commands
      - create Qt timers
      - sleep or spawn threads
      - render artwork
      - contain platform-specific indicator policy
    """

    def __init__(
        self,
        runtime: HardwareRuntimeOrchestrator,
        session: ProcessSession,
    ) -> None:
        if not isinstance(
            runtime,
            HardwareRuntimeOrchestrator,
        ):
            raise TypeError(
                "Runtime must be a HardwareRuntimeOrchestrator."
            )

        for attribute in (
            "active_process",
            "process_running",
            "clear_exited_process",
        ):
            if not hasattr(session, attribute):
                raise TypeError(
                    "Session does not provide the required "
                    f"process lifecycle surface: {attribute}"
                )

        self._runtime = runtime
        self._session = session
        self._policy_resolver = HardwareIndicatorPolicyResolver()

    @property
    def state(self) -> HardwareRuntimeState:
        return self._runtime.state

    @property
    def snapshot(self) -> HardwareIndicatorSnapshot:
        return self._runtime.snapshot

    def launch_requested(
        self,
        platform_id=None,
    ) -> HardwareIndicatorSnapshot:
        """
        Record the user's Play/Open action before emulator startup.

        Canonical RVDB platform identity selects the RVV hardware policy
        before the launch lifecycle becomes active. Unknown, missing, or
        unsupported platforms deliberately receive the generic all-off
        policy.

        For the NES policy this is the point where power becomes green.
        """

        policy = self._policy_resolver.resolve(
            platform_id
        )

        self._runtime.select_indicator_policy(
            policy
        )

        return self._runtime.launch_requested()

    def launch_failed(self) -> HardwareIndicatorSnapshot:
        """
        Normalize a failure that occurs before process startup.

        This is used when application preparation fails after the user's
        launch request but before the emulator launcher returns a result.
        """

        if self._runtime.state is not HardwareRuntimeState.LAUNCH_REQUESTED:
            raise RuntimeError(
                "Launch failure requires a pending launch request."
            )

        return self._runtime.launch_failed()

    def launch_result(
        self,
        result: dict,
    ) -> HardwareIndicatorSnapshot:
        """
        Translate the launcher's result after a pending launch request.

        Success is accepted as RUNNING only when the process session owns
        a process and that process is currently alive.
        """

        if not isinstance(result, dict):
            raise TypeError("Launch result must be a dictionary.")

        if self._runtime.state is not HardwareRuntimeState.LAUNCH_REQUESTED:
            raise RuntimeError(
                "Launch result requires a pending launch request."
            )

        if not result.get("success", False):
            return self._runtime.launch_failed()

        if (
            self._session.active_process is None
            or not self._session.process_running()
        ):
            self._session.clear_exited_process()
            return self._runtime.launch_failed()

        return self._runtime.running()

    def poll(self) -> HardwareIndicatorSnapshot:
        """
        Observe transient RVV timing and the owned process lifecycle.

        A live process leaves the lifecycle active. A dead owned process
        becomes EXITED and is released from process-session ownership.
        """

        self._runtime.poll()

        process = self._session.active_process

        if process is None:
            return self.snapshot

        if self._session.process_running():
            return self.snapshot

        self._runtime.process_exited()
        self._session.clear_exited_process()

        return self.snapshot

    def return_to_idle(self) -> HardwareIndicatorSnapshot:
        """
        Return an EXITED lifecycle to the RetroVault browsing state.
        """

        return self._runtime.idle()
