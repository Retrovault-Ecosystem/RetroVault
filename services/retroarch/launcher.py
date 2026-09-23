import os
import signal
import subprocess

from models.launch_profile import LaunchProfile
from services.presentation.platform_policy import (
    PlatformPresentationPolicyRegistry,
)
from services.presentation.production_package import (
    ProductionPresentationPackageValidator,
)

from .archive_runtime import ArchiveRuntime
from .cheat_runtime import CheatRuntimeConfig
from .core_options_runtime import CoreOptionsRuntimeConfig
from .overlay_runtime import OverlayRuntimeConfig
from .session_config import RetroArchSessionConfig
from .shader_runtime import ShaderRuntimeConfig


class RetroArchLauncher:

    def __init__(
        self,
        overlay_runtime=None,
        shader_runtime=None,
        archive_runtime=None,
        cheat_runtime=None,
        session_config=None,
        core_options_runtime=None,
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

        self.archive_runtime = (
            archive_runtime
            or ArchiveRuntime()
        )

        self.cheat_runtime = (
            cheat_runtime
            or CheatRuntimeConfig()
        )

        self.session_config = (
            session_config
            or RetroArchSessionConfig()
        )

        self.core_options_runtime = (
            core_options_runtime
            or CoreOptionsRuntimeConfig()
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

    def stop(self) -> bool:
        """
        Terminate the complete process group owned by the active
        RetroArch launch and synchronously reap the Popen root.

        The process-group signal terminates wrapper/sandbox/emulator
        descendants. wait() then reaps the launcher-owned root so a
        terminated child cannot remain observable as a zombie.
        """

        process = self._active_process

        if process is None:
            return False

        if process.poll() is not None:
            return False

        try:
            process_group = os.getpgid(
                process.pid
            )
        except (
            ProcessLookupError,
            OSError,
        ):
            return False

        try:
            os.killpg(
                process_group,
                signal.SIGTERM,
            )
        except ProcessLookupError:
            return False

        try:
            process.wait(
                timeout=5.0
            )
        except subprocess.TimeoutExpired:
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

        return True


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

        # Canonical RetroVault production presentation authority.
        #
        # Only an explicit canonical string platform identity can
        # activate this boundary. Legacy callers retain their
        # historical overlay/shader semantics unchanged.
        platform_id = getattr(
            profile,
            "platform_id",
            None,
        )

        canonical_platform_ids = set(
            PlatformPresentationPolicyRegistry
            .canonical_platform_ids()
        )

        is_canonical_platform = (
            isinstance(platform_id, str)
            and platform_id.strip()
            in canonical_platform_ids
        )

        if is_canonical_platform:
            platform_id = platform_id.strip()

            overlay = getattr(
                profile,
                "overlay",
                None,
            )
            shader = getattr(
                profile,
                "shader",
                None,
            )

            has_overlay = (
                isinstance(overlay, str)
                and bool(overlay.strip())
            )
            has_shader = (
                isinstance(shader, str)
                and bool(shader.strip())
            )

            if has_overlay or has_shader:
                try:
                    ProductionPresentationPackageValidator.validate(
                        platform_id=platform_id,
                        core_identity=profile.core,
                        overlay=overlay,
                        shader=shader,
                    )
                except (
                    OSError,
                    ValueError,
                ) as error:
                    return {
                        "success": False,
                        "error": str(error),
                    }

        try:
            runtime_rom = (
                self.archive_runtime
                .resolve(
                    profile.rom,
                    member=(
                        profile.archive_member
                        or None
                    ),
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

        command = [
            self.command,
            "-L",
            profile.core,
            runtime_rom,
        ]

        try:
            core_options_config = (
                self.core_options_runtime.create(
                    profile.core,
                    platform_id=(
                        getattr(
                            profile,
                            "platform_id",
                            "",
                        )
                        or None
                    ),
                )
            )

            session_config = (
                self.session_config.create(
                    core_options_path=(
                        core_options_config
                    )
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

        if session_config:
            command.extend(
                [
                    "--appendconfig",
                    session_config,
                ]
            )

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

        if profile.cheat_file:
            try:
                cheat_config = (
                    self.cheat_runtime.create(
                        profile.cheat_file,
                        profile.core,
                        runtime_rom,
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
                    cheat_config,
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
                command,
                start_new_session=True,
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
