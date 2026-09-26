from __future__ import annotations

import os
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from .display_aspect import CoreDisplayAspect
from .runtime_display_aspect import (
    RuntimeDisplayAspectObserver,
)


class ContentLoadedDisplayAspectProbe:
    """
    Resolve libretro display-aspect authority after content has loaded.

    A short-lived isolated RetroArch process is started with the exact
    core/content pair selected for the launch.  RetroArch's verbose log
    supplies the generic libretro geometry evidence:

      * initial [Core] Geometry
      * later RETRO_ENVIRONMENT_SET_GEOMETRY

    The latest valid runtime geometry observed during a bounded settle
    window is authoritative.

    This class never derives presentation geometry from ROM names,
    titles, archive-member names, game state, or raster lookup tables.
    It returns only CoreDisplayAspect.

    The probe process owns a new process group and is synchronously
    terminated/reaped before this method returns.
    """

    def __init__(
        self,
        *,
        directory=None,
        timeout=2.0,
        settle_time=0.20,
        poll_interval=0.02,
        monotonic_fn=None,
        sleep_fn=None,
        popen_factory=None,
    ):
        self.directory = Path(
            directory
            if directory is not None
            else (
                Path.home()
                / ".cache"
                / "retrovault"
                / "aspect-probe"
            )
        ).expanduser()

        self.timeout = float(timeout)
        self.settle_time = float(settle_time)
        self.poll_interval = float(poll_interval)

        if self.timeout <= 0:
            raise ValueError(
                "timeout must be positive."
            )

        if self.settle_time < 0:
            raise ValueError(
                "settle_time cannot be negative."
            )

        if self.poll_interval <= 0:
            raise ValueError(
                "poll_interval must be positive."
            )

        self._monotonic = (
            monotonic_fn
            if monotonic_fn is not None
            else time.monotonic
        )

        self._sleep = (
            sleep_fn
            if sleep_fn is not None
            else time.sleep
        )

        self._popen = (
            popen_factory
            if popen_factory is not None
            else subprocess.Popen
        )

    @staticmethod
    def _terminate_and_reap(process) -> None:
        if process is None:
            return

        if process.poll() is not None:
            process.wait()
            return

        try:
            process_group = os.getpgid(
                process.pid
            )
        except (
            ProcessLookupError,
            OSError,
        ):
            process.wait()
            return

        try:
            os.killpg(
                process_group,
                signal.SIGTERM,
            )
        except ProcessLookupError:
            pass

        try:
            process.wait(
                timeout=5.0
            )
            return
        except subprocess.TimeoutExpired:
            pass

        try:
            os.killpg(
                process_group,
                signal.SIGKILL,
            )
        except ProcessLookupError:
            pass

        process.wait(
            timeout=5.0
        )

    def acquire(
        self,
        *,
        command,
        core,
        content,
        prefix_args=(),
        append_configs=(),
        shader=None,
    ) -> CoreDisplayAspect:
        if (
            not isinstance(command, str)
            or not command.strip()
        ):
            raise ValueError(
                "RetroArch command must be a non-empty string."
            )

        if (
            not isinstance(core, str)
            or not core.strip()
        ):
            raise ValueError(
                "Core path must be a non-empty string."
            )

        if (
            not isinstance(content, str)
            or not content.strip()
        ):
            raise ValueError(
                "Content path must be a non-empty string."
            )

        self.directory.mkdir(
            parents=True,
            exist_ok=True,
        )

        session_directory = Path(
            tempfile.mkdtemp(
                prefix="probe-",
                dir=str(self.directory),
            )
        )

        log_path = (
            session_directory
            / "retroarch.log"
        )

        observer = RuntimeDisplayAspectObserver(
            log_path
        )

        probe_command = [
            command,
            *tuple(prefix_args),
            "-L",
            core,
            content,
        ]

        for config in append_configs:
            if config:
                probe_command.extend(
                    [
                        "--appendconfig",
                        config,
                    ]
                )

        if shader:
            probe_command.extend(
                [
                    "--set-shader",
                    shader,
                ]
            )

        probe_command.extend(
            [
                "--verbose",
                "--log-file",
                str(log_path),
            ]
        )

        process = None
        aspect = None
        first_aspect_time = None

        try:
            process = self._popen(
                probe_command,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            started = self._monotonic()
            deadline = (
                started
                + self.timeout
            )

            while True:
                now = self._monotonic()

                observed = observer.poll()

                if observed is not None:
                    if (
                        aspect is None
                        or abs(
                            observed.ratio
                            - aspect.ratio
                        ) > 1e-12
                    ):
                        aspect = observed
                        first_aspect_time = now

                    elif first_aspect_time is None:
                        first_aspect_time = now

                if (
                    aspect is not None
                    and first_aspect_time is not None
                    and (
                        now
                        - first_aspect_time
                    ) >= self.settle_time
                ):
                    return aspect

                if process.poll() is not None:
                    observer.poll()

                    if observer.display_aspect is not None:
                        return observer.display_aspect

                    raise ValueError(
                        "RetroArch display-aspect probe exited "
                        "before reporting valid libretro geometry."
                    )

                if now >= deadline:
                    if aspect is not None:
                        return aspect

                    raise ValueError(
                        "RetroArch display-aspect probe timed out "
                        "before reporting valid libretro geometry."
                    )

                self._sleep(
                    self.poll_interval
                )
        finally:
            self._terminate_and_reap(
                process
            )

            try:
                for candidate in (
                    session_directory
                    .iterdir()
                ):
                    try:
                        candidate.unlink()
                    except (
                        FileNotFoundError,
                        IsADirectoryError,
                    ):
                        pass

                session_directory.rmdir()
            except (
                FileNotFoundError,
                OSError,
            ):
                pass
