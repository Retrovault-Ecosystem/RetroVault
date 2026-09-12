import subprocess

from models.launch_profile import LaunchProfile

from .overlay_runtime import OverlayRuntimeConfig
from .shader_runtime import ShaderRuntimeConfig


class RetroArchLauncher:

    def __init__(
        self,
        overlay_runtime=None,
        shader_runtime=None,
    ):
        self.command = "retroarch"

        self.overlay_runtime = (
            overlay_runtime
            or OverlayRuntimeConfig()
        )

        self.shader_runtime = (
            shader_runtime
            or ShaderRuntimeConfig()
        )

        self._active_process = None

    @property
    def active_process(self):
        """Return the currently owned RetroArch process handle."""

        return self._active_process

    def process_running(self) -> bool:
        """
        Return True only while the owned RetroArch process is alive.

        No process is treated as not running.
        """

        if self._active_process is None:
            return False

        return self._active_process.poll() is None

    def clear_exited_process(self):
        """
        Release ownership after the RetroArch process has exited.

        A still-running process is never cleared.
        """

        if self._active_process is None:
            return None

        returncode = self._active_process.poll()

        if returncode is None:
            return None

        process = self._active_process
        self._active_process = None

        return process

    def launch(
        self,
        profile: LaunchProfile,
    ):
        if self._active_process is not None:
            if self._active_process.poll() is None:
                return {
                    "success": False,
                    "error": (
                        "RetroArch process is already running."
                    ),
                }

            self._active_process = None

        command = [
            self.command,
            "-L",
            profile.core,
            profile.rom,
        ]

        if profile.config:
            command.extend(
                [
                    "--config",
                    profile.config,
                ]
            )

        if profile.overlay:
            try:
                append_config = (
                    self.overlay_runtime.create(
                        profile.overlay
                    )
                )
            except (
                OSError,
                ValueError,
            ) as error:
                return {
                    "success": False,
                    "error": str(error),
                }

            command.extend(
                [
                    "--appendconfig",
                    append_config,
                ]
            )

        if profile.shader:
            runtime_shader = profile.shader

            try:
                parameters = (
                    self.shader_runtime
                    .parameters_for_overlay(
                        profile.overlay
                    )
                )

                if parameters:
                    runtime_shader = (
                        self.shader_runtime.resolve(
                            profile.shader,
                            parameters,
                        )
                    )

            except (
                OSError,
                ValueError,
            ) as error:
                return {
                    "success": False,
                    "error": str(error),
                }

            command.extend(
                [
                    "--set-shader",
                    runtime_shader,
                ]
            )

        try:
            process = subprocess.Popen(
                command
            )

            self._active_process = process

            return {
                "success": True,
                "command": command,
            }

        except Exception as error:
            self._active_process = None

            return {
                "success": False,
                "error": str(error),
            }
