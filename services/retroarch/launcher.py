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

    def launch(
        self,
        profile: LaunchProfile,
    ):
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
            subprocess.Popen(
                command
            )

            return {
                "success": True,
                "command": command,
            }

        except Exception as error:
            return {
                "success": False,
                "error": str(error),
            }
