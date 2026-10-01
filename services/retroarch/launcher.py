from config import ConfigLoader
from services.retroarch.process_group import group_exists, terminate_group
from services.retroarch.validator import LaunchValidator
from services.retroarch.diagnostics import LaunchDiagnostics
import os
import shutil
import signal
import subprocess
import time
from pathlib import Path

from models.launch_profile import LaunchProfile
from services.presentation.models import PresentationProfile
from services.presentation.launch_resolver import LaunchPresentationResolver
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
from .adaptive_bezel_runtime import AdaptiveBezelRuntime
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
        adaptive_bezel_runtime=None,
        executable="retroarch",
        presentation_config_provider=None,
    ):
        if not isinstance(executable, str) or not executable.strip():
            raise ValueError("RetroArch executable must be a non-empty string.")
        self.command = os.path.expanduser(executable.strip())
        self.presentation_config_provider = presentation_config_provider
        self.adaptive_bezel_runtime = adaptive_bezel_runtime or AdaptiveBezelRuntime()

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
        self._active_group = None
        self.cleanup_errors = []
        self._active_primary_config = None
        self._active_contain_config = None
        self._active_cheat_config = None

    @property
    def active_process(self):
        """Return the currently owned RetroArch process handle."""

        return self._active_process

    def _cleanup_active_transients(self):
        """Try every owner; retain failed resources for retry, never mask launch errors."""
        self.cleanup_errors = []
        if self.process_running() or self._probe_running():
            self.cleanup_errors.append("Runtime resources remain in use by an owned process.")
            return
        try:
            self.primary_config_runtime.cleanup(self._active_primary_config)
            self._active_primary_config = None
        except (OSError, RuntimeError) as exc:
            self.cleanup_errors.append(f"Primary config cleanup: {exc}")
        except AttributeError:
            # Older injected runtime adapters may have no cleanup method.
            pass
        for runtime in (self.core_options_runtime, self.session_config,
                        self.overlay_runtime, self.adaptive_bezel_runtime,
                        self.contain_runtime, self.shader_runtime, getattr(self, "cheat_runtime", None),
                        getattr(self, "content_display_aspect_probe", None)):
            cleanup = getattr(runtime, "cleanup", None)
            if callable(cleanup):
                try:
                    cleanup()
                    remaining = getattr(runtime, "_created", None)
                    if isinstance(remaining, list) and remaining:
                        self.cleanup_errors.append(f"{type(runtime).__name__}: cleanup pending")
                except (OSError, RuntimeError) as exc:
                    self.cleanup_errors.append(f"{type(runtime).__name__}: {exc}")
        if not self.cleanup_errors:
            self._active_contain_config = None
            self._active_cheat_config = None

    def _probe_running(self):
        running = getattr(getattr(self, "content_display_aspect_probe", None), "process_running", None)
        return callable(running) and running() is True

    def shutdown(self):
        """Idempotent orderly shutdown; failure retains ownership for retry."""
        stop_probe = getattr(self.content_display_aspect_probe, "stop", None)
        if callable(stop_probe):
            stop_probe()
        if self._active_process is not None:
            if self.process_running():
                self.stop()
            else:
                self.clear_exited_process()
        self._cleanup_active_transients()
        if self.cleanup_errors:
            raise RuntimeError("; ".join(self.cleanup_errors))
        return True

    def process_running(self) -> bool:
        """
        Return True only while the owned RetroArch process is alive.

        No process is treated as not running.
        """

        if getattr(self, "_active_process", None) is None:
            return False

        return (self._active_process.poll() is None
                or self._process_group_exists(getattr(self, "_active_group", None)))

    def clear_exited_process(self):
        """
        Release ownership after the RetroArch process has exited.

        A still-running process is never cleared.
        """

        if self._active_process is None:
            return None

        returncode = self._active_process.poll()

        if returncode is None or self._process_group_exists(getattr(self, "_active_group", None)):
            return None

        process = self._active_process
        self._active_process = None
        self._active_group = None
        self._cleanup_active_transients()

        return process

    @staticmethod
    def _process_group_exists(process_group):
        return group_exists(process_group)

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
        process = self._active_process
        if process is None:
            return False
        if not self.process_running():
            self.clear_exited_process()
            return False
        group = getattr(self, "_active_group", None)
        if group is None:
            # Compatibility for process adapters not created by launch().
            try:
                group = os.getpgid(process.pid)
            except ProcessLookupError:
                return False
        terminate_group(process, group, self._wait_for_process_group_exit)
        self._active_process = None
        self._active_group = None
        self._cleanup_active_transients()
        return True

    def launch(
        self,
        profile: LaunchProfile,
    ):
        if self.process_running() or self._probe_running():
            return {"success": False, "error": "RetroArch process is already running."}
        if self._active_process is not None:
            self.clear_exited_process()
        if self.cleanup_errors:
            self._cleanup_active_transients()
        if self.cleanup_errors:
            return {"success": False, "error": "; ".join(self.cleanup_errors)}

        requested_platform = getattr(profile, "platform_id", "")
        known_platform = (
            requested_platform.strip()
            if isinstance(requested_platform, str)
            and requested_platform.strip() in PlatformPresentationPolicyRegistry.canonical_platform_ids()
            else None
        )
        prerequisites = LaunchValidator(self.command, profile.core).validate(
            profile.rom, platform_id=known_platform
        )
        if not prerequisites["ready"]:
            return {"success": False, "error": " ".join(LaunchDiagnostics().explain(prerequisites))}

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

        try:
            launch_config = (self.presentation_config_provider() if self.presentation_config_provider
                             else ConfigLoader().load())
        except (OSError, ValueError) as error:
            return {"success": False, "error": str(error)}

        production_package = None

        if is_canonical_platform:
            platform_id = platform_id.strip()

            try:
                production_package = (
                    LaunchPresentationResolver(config=launch_config).select(
                        platform_id=platform_id,
                        core_identity=canonical_libretro_core_identity(profile.core),
                        requested=PresentationProfile(overlay=profile.overlay, shader=profile.shader),
                    ).package
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
            from services.presentation.visual_tuning import shader_parameters
            adjustments = dict(getattr(profile, 'visual_tuning', ()) or ())
            if adjustments and production_package is None:
                raise ValueError('CRT adjustments require a validated production package.')
            tuning_parameters = shader_parameters(platform_id, adjustments)
        except (TypeError, ValueError) as error:
            return {'success': False, 'error': str(error)}

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
            configured_primary = profile.config or launch_config.get("retroarch", {}).get("primary_config", "")
            primary_source = {"source": configured_primary} if configured_primary else {}
            primary_config = (
                self.primary_config_runtime.create(
                    **primary_source,
                    overlay=(
                        production_package.overlay
                        if production_package is not None
                        else None
                    ),
                )
            )
            if configured_primary and not primary_config:
                raise ValueError("Explicit primary configuration was not isolated.")
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
                    ),
                    shader_enabled=bool(
                        production_package.shader
                        if production_package is not None
                        else profile.shader
                    ),
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

        append_configs = []

        if session_config:
            append_configs.append(session_config)

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

            append_configs.append(append_config)

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

                    parameters.update(tuning_parameters)
                    if parameters:
                        runtime_shader = (
                            self.shader_runtime.resolve(
                                launch_shader,
                                parameters,
                            )
                        )

                runtime_display_aspect = (
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

                if runtime_display_aspect is not None:
                    display_aspect = runtime_display_aspect

                startup_contain_config = (
                    self.contain_runtime.create_for_aspect(
                        profile=glass_profile,
                        display_aspect=display_aspect,
                    )
                )
                self._active_contain_config = startup_contain_config
                geometry = glass_profile.contain_aspect(
                    display_aspect.width, display_aspect.height,
                )
                fitted_overlay = self.adaptive_bezel_runtime.create(
                    package=production_package, glass=glass, geometry=geometry,
                )
                if fitted_overlay != launch_overlay:
                    # The probe used the original package; the visible launch
                    # gets a frame constructed from the same final geometry.
                    append_configs[append_configs.index(append_config)] = (
                        self.overlay_runtime.create(fitted_overlay)
                    )
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

            append_configs.append(cheat_config)

        if startup_contain_config:
            append_configs.append(startup_contain_config)

        # RetroArch replaces repeated --appendconfig arguments. Its CLI
        # accepts the ordered layers as one pipe-delimited argument.
        if append_configs:
            command.extend(["--appendconfig", "|".join(append_configs)])

        if launch_shader:
            runtime_shader = launch_shader

            try:
                parameters = (
                    self.shader_runtime
                    .parameters_for_overlay(
                        launch_overlay
                    )
                )

                parameters.update(tuning_parameters)
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
            self._active_group = process.pid
            if not self.process_running():
                self.clear_exited_process()
                return {"success": False, "error": "RetroArch exited during startup."}

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
