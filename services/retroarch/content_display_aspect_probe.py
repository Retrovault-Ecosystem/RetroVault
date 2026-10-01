from __future__ import annotations

from config.paths import runtime_directory

import os
import signal
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from .display_aspect import CoreDisplayAspect
from .process_group import group_exists, terminate_group
from .runtime_display_aspect import (
    RuntimeDisplayAspectObserver,
)


class ContentLoadedDisplayAspectProbe:
    """
    Resolve libretro display-aspect authority after content has loaded.

    A short-lived headless RetroArch process is started with the exact
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
                runtime_directory("aspect-probe")
            )
        ).expanduser()

        self._active_process = None
        self._session_directory = None
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
    def _process_group_exists(process_group):
        return group_exists(process_group)

    def _wait_for_process_group_exit(
        self,
        process_group,
        *,
        timeout,
    ) -> bool:
        deadline = (
            self._monotonic()
            + float(timeout)
        )

        while self._process_group_exists(
            process_group
        ):
            if self._monotonic() >= deadline:
                return False

            self._sleep(
                self.poll_interval
            )

        return True

    def _terminate_and_reap(self, process, *, process_group=None):
        if process is None:
            return
        try:
            terminate_group(process, process_group or process.pid, self._wait_for_process_group_exit)
        except RuntimeError as exc:
            raise OSError(str(exc)) from exc

    def process_running(self):
        process = self._active_process
        return process is not None and (process.poll() is None or self._process_group_exists(process.pid))

    def stop(self):
        if self._active_process is not None:
            self._terminate_and_reap(self._active_process, process_group=self._active_process.pid)
            self._active_process = None
        if self._session_directory is not None:
            try:
                shutil.rmtree(self._session_directory)
            except FileNotFoundError:
                pass
            self._session_directory = None

    def cleanup(self):
        self.stop()

    def acquire(self, **kwargs):
        if self.process_running():
            raise OSError("Previous display-aspect probe still owns a process group.")
        self.stop()
        try:
            return self._acquire(**kwargs)
        finally:
            self.stop()

    def _acquire(
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

        self._session_directory = session_directory
        log_path = (
            session_directory
            / "retroarch.log"
        )

        observer = RuntimeDisplayAspectObserver(
            log_path
        )

        # Geometry acquisition must never create a second visible game
        # window. Keep core options from the launch, then override only
        # presentation and probe side effects in the final config layer.
        headless_config = session_directory / "headless.cfg"
        settings = {
            "video_driver": "null",
            "audio_driver": "null",
            "input_driver": "null",
            "video_threaded": "false",
            "video_fullscreen": "false",
            "video_shader_enable": "false",
            "input_overlay_enable": "false",
            "audio_enable": "false",
            "config_save_on_exit": "false",
            "history_list_enable": "false",
            "content_runtime_log": "false",
            "content_runtime_log_aggregate": "false",
            "savestate_auto_save": "false",
            "savestate_auto_load": "false",
            "savefile_directory": str(session_directory),
            "savestate_directory": str(session_directory),
        }
        headless_config.write_text("".join(
            f'{key} = "{value}"\n' for key, value in settings.items()
        ), encoding="utf-8")

        probe_command = [
            command,
            *tuple(prefix_args),
            "-L",
            core,
            content,
        ]

        # Match the visible launch: repeated options retain only the last
        # layer in RetroArch, losing the session's core-options authority.
        configs = [config for config in append_configs if config]
        configs.append(str(headless_config))
        probe_command.extend(["--appendconfig", "|".join(configs)])
        # The shader argument remains accepted for caller compatibility;
        # a display-aspect probe has no rendered surface to shade.

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

            self._active_process = process
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
            # Outer acquire() retains ownership and performs cleanup even when
            # configuration writing or process creation fails.
            pass
