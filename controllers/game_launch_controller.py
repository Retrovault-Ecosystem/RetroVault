"""Qt-independent launch workflow; registered adapters retain execution ownership."""
import copy
from pathlib import Path
from config import ConfigLoader
from models.launch_profile import LaunchProfile
from services.library.game_variants import normalize_variant_category
from services.presentation.launch_resolver import LaunchPresentationResolver
from services.presentation.hardware_state import HardwareRuntimeState
from services.retroarch import CoreResolver, LaunchDiagnostics, LaunchValidator
from services.retroarch.launcher import RetroArchLauncher
from services.retroarch.archive_runtime import ArchiveRuntime
from services.cheats import CheatService
from services.emulators.models import selected_backend, SNES, SNES9X, StandaloneRequest
from services.emulators.session import EmulatorSession


class GameLaunchController:
    def __init__(self, *, launcher=None, process_lifecycle=None, archive_runtime=None,
                 cheat_service=None, config_loader=None):
        self.config_loader = config_loader or ConfigLoader()
        self.config = self.config_loader.load()
        self.core_resolver = CoreResolver(self.config)
        self.launcher = launcher if launcher is not None else EmulatorSession(RetroArchLauncher(
            executable=self.config['retroarch']['executable']))
        self.process_lifecycle = process_lifecycle
        self.archive_runtime = archive_runtime if archive_runtime is not None else ArchiveRuntime()
        self.cheat_service = cheat_service if cheat_service is not None else CheatService()
        self.diagnostics = LaunchDiagnostics()
        self.validator_factory = None
        self._launch_session_active = False
        self._launch_in_progress = False
        self._pending_cheat_inputs = set()

    def cleanup_inputs(self):
        errors = []
        for path in tuple(self._pending_cheat_inputs):
            try:
                Path(path).unlink(missing_ok=True)
                self._pending_cheat_inputs.remove(path)
            except OSError as exc:
                errors.append(str(exc))
        if errors:
            raise OSError("; ".join(errors))

    def launch(self, game, *, choose_edition, choose_archive, choose_cheats,
               status, warning, played=None, presentation_provider=None):
        if self._launch_in_progress:
            status('Unable to launch: another launch is being prepared.')
            return False
        self._launch_in_progress = True
        # Dialog callbacks contain UI interaction only. All preparation and ownership
        # stay here. Calls are synchronous and guarded by the shared launcher.
        self.current_game = game
        self._select_game_edition = choose_edition
        self._select_archive_member = choose_archive
        self._select_cheats = choose_cheats
        self._set_launch_status = status
        self.warning = warning
        self.played_handler = played
        self.presentation_resolver_provider = presentation_provider
        self._owned_cheat_input = ''
        self._launch_session_active = False
        self.last_result = {'success': False, 'error': 'Launch cancelled or preparation failed.'}
        try:
            self.cleanup_inputs()
            self._launch()
            return self._launch_session_active
        except (OSError, ValueError, RuntimeError) as exc:
            self.last_result = {'success': False, 'error': str(exc)}
            status(f'Unable to launch: {exc}')
            if (self.process_lifecycle is not None
                    and self.process_lifecycle.state is HardwareRuntimeState.LAUNCH_REQUESTED):
                self.process_lifecycle.launch_failed()
            return False
        finally:
            if self._owned_cheat_input:
                self._pending_cheat_inputs.add(self._owned_cheat_input)
            try:
                self.cleanup_inputs()
            except OSError as exc:
                warning('Cheat Input Cleanup Failed', str(exc))
            self._launch_in_progress = False
            # Do not retain bound widgets between launches in the shared controller.
            self.current_game = None
            self._select_game_edition = self._select_archive_member = self._select_cheats = None
            self._set_launch_status = self.warning = self.played_handler = None
            self.presentation_resolver_provider = None

    def stop(self):
        if self.process_lifecycle is not None:
            self.process_lifecycle.stop_requested()
        else:
            self.launcher.stop()

    def _process_session_running(
        self,
    ) -> bool:
        if self.launcher is None:
            return False

        process_running = getattr(
            self.launcher,
            "process_running",
            None,
        )

        if process_running is None:
            return False

        try:
            running = process_running()
        except (
            OSError,
            RuntimeError,
        ):
            return False

        if not isinstance(
            running,
            bool,
        ):
            return False

        return running

    def _launch_target_from_variant(
        self,
        variant,
    ):
        """
        Build a launch-time game view for a selected physical edition.

        The canonical Library object remains untouched. Presentation
        resolution, core selection, validation and launch all receive
        the selected edition's ROM while inheriting canonical metadata
        that is shared by the game family.
        """

        if (
            self.current_game is None
            or not isinstance(
                variant,
                dict,
            )
        ):
            return self.current_game

        from copy import copy

        launch_game = copy(
            self.current_game
        )

        launch_game.local_file_id = str(variant.get("local_file_id", "") or "")

        variant_name = str(
            variant.get(
                "name",
                "",
            )
            or ""
        ).strip()

        variant_rom = str(
            variant.get(
                "rom",
                "",
            )
            or ""
        ).strip()

        variant_source = str(
            variant.get(
                "source",
                "",
            )
            or ""
        ).strip()

        if variant_name:
            launch_game.name = (
                variant_name
            )

        if variant_rom:
            launch_game.rom = (
                variant_rom
            )

        if variant_source:
            launch_game.source = (
                variant_source
            )

        launch_game.variant_category = (
            normalize_variant_category(
                variant.get(
                    "category",
                    "other",
                )
            )
        )

        launch_game.variant_label = str(
            variant.get(
                "label",
                "",
            )
            or ""
        )

        launch_game.variant_region = str(
            variant.get(
                "region",
                "",
            )
            or ""
        )

        launch_game.variant_language = str(
            variant.get(
                "language",
                "",
            )
            or ""
        )

        launch_game.variant_revision = str(
            variant.get(
                "revision",
                "",
            )
            or ""
        )

        launch_game.is_primary_variant = bool(
            variant.get(
                "preferred",
                False,
            )
        )

        return launch_game

    def _cheat_runtime_file(
        self,
        cheats,
    ):
        if not cheats:
            return ""

        return self.cheat_service.runtime_file(
            cheats
        )

    def _launch(self):


        if not self.current_game:

            return

        if self._process_session_running():
            self._set_launch_status(
                "Unable to launch: another game session is running."
            )
            return

        selected_variant = (
            self._select_game_edition()
        )

        if selected_variant is None:
            self._set_launch_status(
                "Launch cancelled."
            )
            return

        launch_game = (
            self._launch_target_from_variant(
                selected_variant
            )
        )

        if launch_game is None:
            return

        self._set_launch_status(
            f'Preparing "{launch_game.name}"...'
        )

        platform_id = getattr(launch_game, 'rvdb_platform_id', '')
        if platform_id == SNES:
            current_config = self.config_loader.load()
            if selected_backend(current_config, platform_id) == SNES9X:
                self._launch_standalone(launch_game, current_config)
                return

        archive_member = ""

        if (
            Path(
                launch_game.rom
            ).suffix.lower()
            == ".7z"
        ):
            try:
                archive_member = (
                    self._select_archive_member(
                        launch_game.rom
                    )
                )
            except (
                OSError,
                ValueError,
            ) as exc:
                message = (
                    "Unable to inspect archive variants: "
                    f"{exc}"
                )
                self.warning(
                    "Archive Inspection Failed",
                    (
                        "RetroVault could not inspect "
                        "the archive variants.\n\n"
                        f"{exc}"
                    ),
                )
                self._set_launch_status(
                    message
                )
                return

            if archive_member is None:
                self._set_launch_status(
                    "Launch cancelled."
                )
                return

        cheat_game = launch_game
        runtime_rom = ""

        if archive_member:
            try:
                runtime_rom = (
                    self.archive_runtime
                    .resolve(
                        launch_game.rom,
                        member=archive_member,
                    )
                )
            except (
                OSError,
                ValueError,
            ) as exc:
                self._set_launch_status(
                    "Unable to prepare archive variant: "
                    f"{exc}"
                )
                return

            cheat_game = copy.copy(
                launch_game
            )
            cheat_game.rom = runtime_rom

        try:
            selected_cheats = (
                self._select_cheats(
                    cheat_game,
                    "",
                )
            )
        except (
            OSError,
            ValueError,
        ) as exc:
            self._set_launch_status(
                "Unable to load Cheat Studio: "
                f"{exc}"
            )
            return

        if selected_cheats is None:
            self._set_launch_status(
                "Launch cancelled."
            )
            return

        try:
            cheat_file = (
                self._cheat_runtime_file(
                    selected_cheats
                )
            )
        except (
            OSError,
            ValueError,
        ) as exc:
            self._set_launch_status(
                "Unable to prepare cheats: "
                f"{exc}"
            )
            return

        self._owned_cheat_input = cheat_file

        if self.process_lifecycle is not None:
            self.process_lifecycle.launch_requested(
                getattr(
                    launch_game,
                    "rvdb_platform_id",
                    "",
                )
            )



        # Re-read directory settings without changing the active launcher's command.
        try:
            current_config = self.config_loader.load()
            self.core_resolver.core_directory = current_config.get("retroarch", {}).get("cores", {}).get("directory", "")
            resolution = self.core_resolver.resolve(
                launch_game.core,
                platform_id=getattr(launch_game, "rvdb_platform_id", ""),
            )
        except (OSError, ValueError, TypeError, AttributeError) as exc:
            self._set_launch_status(f"Unable to load core settings: {exc}")
            if self.process_lifecycle is not None:
                self.process_lifecycle.launch_failed()
            return
        core_path = resolution.path
        if not core_path:
            message = "Unable to launch: " + resolution.message
            self.warning( "Emulator Core Unavailable", resolution.message)

            self._set_launch_status(
                message
            )

            if self.process_lifecycle is not None:
                self.process_lifecycle.launch_failed()

            return



        shader = ""
        overlay = ""
        resolver = None
        visual_tuning = ()

        if (
            self.presentation_resolver_provider
            is not None
        ):
            try:
                resolver = (
                    self.presentation_resolver_provider()
                )
                presentation = resolver.resolve(
                    launch_game
                )
                if isinstance(resolver, LaunchPresentationResolver):
                    visual_tuning = resolver.describe(launch_game).visual_tuning
                shader = presentation.shader
                overlay = presentation.overlay
            except (
                OSError,
                ValueError,
            ) as exc:
                if isinstance(resolver, LaunchPresentationResolver):
                    self._set_launch_status(f"Launch presentation unavailable: {exc}")
                    if self.process_lifecycle is not None:
                        self.process_lifecycle.launch_failed()
                    return
                self.warning(
                    "Visual Presentation Unavailable",
                    (
                        "RetroVault could not load "
                        "the selected visual presentation.\n\n"
                        "The game may still use its system's default visuals.\n\n"
                        f"{exc}"
                    ),
                )

        profile = LaunchProfile(

            game=launch_game.name,

            rom=(
                runtime_rom
                or launch_game.rom
            ),

            core=core_path,

            overlay=overlay,

            shader=shader,
            visual_tuning=visual_tuning,

            archive_member=(
                ""
                if runtime_rom
                else archive_member
            ),

            cheat_file=cheat_file

        )

        profile.platform_id = str(
            getattr(
                launch_game,
                "rvdb_platform_id",
                "",
            )
            or ""
        ).strip()



        executable = getattr(self.launcher, "command", None)
        if not isinstance(executable, str) or not executable:
            executable = self.config["retroarch"]["executable"]

        validator = (self.validator_factory or LaunchValidator)(

            executable,

            profile.core

        )



        result = validator.validate(

            profile.rom

        )



        if not result["ready"]:

            messages = self.diagnostics.explain(
                result
            )

            self._set_launch_status(
                "Unable to launch: "
                + " ".join(messages)
            )

            if self.process_lifecycle is not None:
                self.process_lifecycle.launch_failed()

            return



        launch_result = self.launcher.launch(

            profile

        )


        self._complete_launch(launch_game, launch_result, 'RetroArch')

    def _launch_standalone(self, game, config):
        if not callable(getattr(self.launcher, 'launch_standalone', None)):
            raise ValueError('Standalone session adapter is unavailable.')
        if self.process_lifecycle is not None:
            self.process_lifecycle.launch_requested(game.rvdb_platform_id)
        request = StandaloneRequest(
            game=game.name, rom=game.rom, platform_id=game.rvdb_platform_id,
            local_file_id=getattr(game, 'local_file_id', ''),
            executable=config.get('emulation', {}).get('snes9x_executable', ''))
        result = self.launcher.launch_standalone(request)
        self._complete_launch(game, result, 'Snes9x standalone')

    def _complete_launch(self, launch_game, launch_result, backend):
        if self.process_lifecycle is not None:
            self.process_lifecycle.launch_result(
                launch_result
            )
            state_name = getattr(getattr(self.process_lifecycle, "state", None), "name", None)
            if isinstance(state_name, str) and state_name != "RUNNING" and launch_result.get("success"):
                launch_result = {"success": False, "error": f"{backend} exited during startup."}

        self.last_result = launch_result

        if launch_result.get(
            "success",
            False,
        ):
            self._launch_session_active = True

            self._set_launch_status(
                f'Running "{launch_game.name}".' if backend == 'RetroArch' else f'Running "{launch_game.name}" with {backend}.'
            )
        else:
            self._launch_session_active = False
            error = str(
                launch_result.get(
                    "error",
                    "Unknown launch error.",
                )
            ).strip()

            if not error:
                error = "Unknown launch error."

            self._set_launch_status(
                f"Unable to launch: {error}"
            )

        if (
            launch_result.get(
                "success",
                False,
            )
            and self.played_handler is not None
        ):

            try:

                self.played_handler(
                    launch_game
                )

            except (
                OSError,
                ValueError,
            ) as exc:

                self.warning(
                    "Recently Played Update Failed",
                    (
                        "RetroVault started the game, but "
                        "could not update Recently Played."
                        "\n\n"
                        f"{exc}"
                    ),
                )
