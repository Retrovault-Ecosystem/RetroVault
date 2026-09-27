import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

from models.launch_profile import LaunchProfile
from services.retroarch.core_identity import (
    canonical_libretro_core_identity,
)
from services.retroarch.primary_config_runtime import PrimaryConfigRuntime
from services.presentation.platform_policy import (
    PlatformPresentationPolicyRegistry,
)
from services.presentation.production_package import (
    ProductionPresentationPackageValidator,
)
from services.presentation.production_package_resolver import (
    CanonicalProductionPackageResolver,
)
from services.retroarch.contain_runtime import (
    ContainRuntimeConfig,
)
from services.retroarch.core_display_aspect import (
    LibretroDisplayAspectProbe,
)
from services.retroarch.content_display_aspect_probe import (
    ContentLoadedDisplayAspectProbe,
)
from services.retroarch.display_aspect import (
    CoreDisplayAspect,
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
        primary_config_runtime=None,
        core_options_runtime=None,
        display_aspect_probe=None,
        content_display_aspect_probe=None,
        contain_runtime=None,
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

        self.primary_config_runtime = (
            primary_config_runtime
            if primary_config_runtime is not None
            else PrimaryConfigRuntime()
        )

        self.session_config = (
            session_config
            or RetroArchSessionConfig()
        )

        self.core_options_runtime = (
            core_options_runtime
            or CoreOptionsRuntimeConfig()
        )

        self.display_aspect_probe = (
            display_aspect_probe
            if display_aspect_probe is not None
            else LibretroDisplayAspectProbe()
        )

        self.content_display_aspect_probe = (
            content_display_aspect_probe
            if content_display_aspect_probe is not None
            else ContentLoadedDisplayAspectProbe()
        )

        self.contain_runtime = (
            contain_runtime
            if contain_runtime is not None
            else ContainRuntimeConfig()
        )

        self._active_process = None
        self._active_primary_config = None
        self._active_contain_config = None
        self._active_cheat_config = None

    @property
    def active_process(self):
        """Return the currently owned RetroArch process handle."""

        return self._active_process

    def _cleanup_active_transients(self):
        """
        Clean every one-launch RetroArch runtime artifact.

        Service-owned runtimes clean their internally tracked paths.
        PrimaryConfigRuntime remains path-owned. CheatRuntime currently
        has no cleanup API, so its unique generated launch directory is
        removed explicitly.

        ArchiveRuntime is intentionally excluded because extracted
        archive content is reusable cache material.
        """
        primary_cleanup = getattr(
            self.primary_config_runtime,
            "cleanup",
            None,
        )

        if callable(primary_cleanup):
            primary_cleanup(
                self._active_primary_config
            )

        for runtime in (
            self.core_options_runtime,
            self.session_config,
            self.overlay_runtime,
            self.contain_runtime,
            self.shader_runtime,
        ):
            cleanup = getattr(
                runtime,
                "cleanup",
                None,
            )

            if callable(cleanup):
                cleanup()

        cheat_config = self._active_cheat_config

        if cheat_config:
            cheat_root = Path(
                cheat_config
            ).expanduser().parent

            if cheat_root.name.startswith(
                "retrovault-cheats-"
            ):
                shutil.rmtree(
                    cheat_root,
                    ignore_errors=True,
                )

        self._active_primary_config = None
        self._active_contain_config = None
        self._active_cheat_config = None

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
        self._cleanup_active_transients()

        return process

    @staticmethod
    def _process_group_exists(
        process_group: int,
    ) -> bool:
        """
        Return True while any process remains in ``process_group``.

        ``Popen.wait()`` only proves that the launcher-owned root
        process has exited. Wrapper/sandbox descendants can remain in
        the same process group after that root exits, so lifecycle
        completion must independently observe the group itself.
        """

        try:
            os.killpg(
                process_group,
                0,
            )
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

        return True

    @classmethod
    def _wait_for_process_group_exit(
        cls,
        process_group: int,
        *,
        timeout: float,
        poll_interval: float = 0.05,
    ) -> bool:
        """
        Wait until the complete owned process group disappears.

        The wait is bounded so a misbehaving emulator or sandbox
        cannot block RetroVault shutdown indefinitely.
        """

        deadline = (
            time.monotonic()
            + max(
                0.0,
                float(timeout),
            )
        )

        while cls._process_group_exists(
            process_group
        ):
            if time.monotonic() >= deadline:
                return False

            time.sleep(
                poll_interval
            )

        return True

    def stop(self) -> bool:
        """
        Terminate and fully drain the process group owned by the
        active RetroArch launch.

        RetroArch may be reached through wrapper/sandbox processes
        such as Flatpak/bwrap. The wrapper can exit immediately after
        SIGTERM while emulator descendants remain alive in the same
        process group. Therefore root-process reaping and process-group
        drainage are separate lifecycle requirements.
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
            pass

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

        group_exited = (
            self._wait_for_process_group_exit(
                process_group,
                timeout=2.0,
            )
        )

        if not group_exited:
            try:
                os.killpg(
                    process_group,
                    signal.SIGKILL,
                )
            except ProcessLookupError:
                pass

            group_exited = (
                self._wait_for_process_group_exit(
                    process_group,
                    timeout=5.0,
                )
            )

        if not group_exited:
            raise RuntimeError(
                "RetroArch process group did not "
                "terminate completely."
            )

        self._active_process = None
        self._cleanup_active_transients()

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
        # READY canonical platforms select their deployed package from
        # platform authority, never from legacy per-content overlay/shader
        # metadata carried by LaunchProfile. Non-canonical/legacy callers
        # retain their historical LaunchProfile presentation semantics.
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

        production_package = None

        if is_canonical_platform:
            platform_id = platform_id.strip()

            try:
                production_package = (
                    CanonicalProductionPackageResolver.resolve(
                        platform_id=platform_id,
                        core_identity=(
                            canonical_libretro_core_identity(
                                profile.core
                            )
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

        primary_config = None

        try:
            primary_config = (
                self.primary_config_runtime.create(
                    overlay=(
                        production_package.overlay
                        if production_package is not None
                        else None
                    ),
                )
            )
            self._active_primary_config = primary_config
        except (OSError, ValueError) as exc:
            self._cleanup_active_transients()

            return {
                "success": False,
                "error": str(exc),
            }

        command = [
            self.command,
        ]

        if primary_config:
            command.extend(
                [
                    "--config",
                    primary_config,
                ]
            )

        command.extend([
            "-L",
            profile.core,
            runtime_rom,
        ])

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
            self._cleanup_active_transients()

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

        launch_overlay = (
            production_package.overlay
            if production_package is not None
            else profile.overlay
        )

        launch_shader = (
            production_package.shader
            if production_package is not None
            else profile.shader
        )

        if launch_overlay:
            try:
                append_config = (
                    self.overlay_runtime.create(
                        launch_overlay
                    )
                )
            except (
                OSError,
                ValueError,
            ) as error:
                self._cleanup_active_transients()

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

        startup_contain_config = None

        if production_package is not None:
            try:
                glass = production_package.fixed_glass()

                platform_profile = (
                    PlatformPresentationPolicyRegistry
                    .master_presentation_profile_for(
                        platform_id
                    )
                )

                glass_profile = glass.as_master_profile(
                    profile_class=platform_profile.profile_class,
                )

                display_aspect = (
                    CoreDisplayAspect.from_launch_profile(
                        profile
                    )
                )

                if display_aspect is None:
                    probe_prefix_args = []

                    if primary_config:
                        probe_prefix_args.extend(
                            [
                                "--config",
                                primary_config,
                            ]
                        )

                    probe_append_configs = []

                    if session_config:
                        probe_append_configs.append(
                            session_config
                        )

                    if launch_overlay:
                        probe_append_configs.append(
                            append_config
                        )

                    runtime_shader = launch_shader or None

                    if launch_shader:
                        parameters = (
                            self.shader_runtime
                            .parameters_for_overlay(
                                launch_overlay
                            )
                        )

                        if parameters:
                            runtime_shader = (
                                self.shader_runtime.resolve(
                                    launch_shader,
                                    parameters,
                                )
                            )

                    display_aspect = (
                        self.content_display_aspect_probe.acquire(
                            command=self.command,
                            core=profile.core,
                            content=runtime_rom,
                            prefix_args=tuple(
                                probe_prefix_args
                            ),
                            append_configs=tuple(
                                probe_append_configs
                            ),
                            shader=runtime_shader,
                        )
                    )

                startup_contain_config = (
                    self.contain_runtime.create_for_aspect(
                        profile=glass_profile,
                        display_aspect=display_aspect,
                    )
                )
                self._active_contain_config = startup_contain_config
            except (
                OSError,
                TypeError,
                ValueError,
            ) as error:
                self._cleanup_active_transients()

                return {
                    "success": False,
                    "error": str(error),
                }

        if profile.cheat_file:
            try:
                cheat_config = (
                    self.cheat_runtime.create(
                        profile.cheat_file,
                        profile.core,
                        runtime_rom,
                    )
                )
                self._active_cheat_config = cheat_config
            except (
                OSError,
                ValueError,
            ) as error:
                self._cleanup_active_transients()

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

        if startup_contain_config:
            command.extend(
                [
                    "--appendconfig",
                    startup_contain_config,
                ]
            )

        if launch_shader:
            runtime_shader = launch_shader

            try:
                parameters = (
                    self.shader_runtime
                    .parameters_for_overlay(
                        launch_overlay
                    )
                )

                if parameters:
                    runtime_shader = (
                        self.shader_runtime.resolve(
                            launch_shader,
                            parameters,
                        )
                    )

            except (
                OSError,
                ValueError,
            ) as error:
                self._cleanup_active_transients()

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
            self._cleanup_active_transients()

            return {
                "success": False,
                "error": str(error),
            }
