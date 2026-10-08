from config.library_preferences import LibraryPreferences
from services.emulators.session import EmulatorSession
from controllers.game_launch_controller import GameLaunchController
from config.paths import RVDB_BUNDLE
from PyQt6.QtCore import QTimer
from PyQt6.QtCore import QEvent

from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QHBoxLayout,
)

from ui.sidebar import Sidebar

from ui.navigation.page_manager import (
    PageManager
)

from ui.pages.library_page import LibraryPage
from ui.pages.systems_page import SystemsPage
from ui.pages.playlists_page import PlaylistsPage
from ui.pages.overlays_page import OverlaysPage
from ui.pages.visuals_page import NativeVisualsPage
from ui.pages.shaders_page import ShadersPage
from ui.pages.retroarch_page import RetroArchPage
from ui.pages.settings_page import SettingsPage

from controllers.library_controller import (
    LibraryController
)

from services.rvdb import (
    RVDBConsumer,
    RVDBError,
    RVDBService,
)

from services.library.rvdb_resolver import (
    RVDBLibraryResolver,
)

from config import ConfigLoader

from services.retroarch.launcher import (
    RetroArchLauncher,
)

from services.presentation.hardware_runtime import (
    HardwareRuntimeOrchestrator,
)

from services.presentation.hardware_state import (
    HardwareIndicatorPolicy,
)

from services.presentation.process_lifecycle import (
    ProcessLifecycleAdapter,
)

from services.presentation.indicator_rendering import (
    HardwareIndicatorRenderBridge,
)

from services.presentation import (
    PresentationCompositionFactory,
    PresentationRecommendationManifest,
    PresentationStore,
)


class MainWindow(QMainWindow):


    def shutdown_runtime(self):
        """Stop only this application's owned launch tree and resources."""
        try:
            getattr(self, 'emulator_session', self.retroarch_launcher).shutdown()
            controller = getattr(self, "game_launch_controller", None)
            if controller is not None:
                controller.cleanup_inputs()
        except (OSError, RuntimeError) as exc:
            self.statusBar().showMessage(f"Runtime shutdown incomplete: {exc}")
            return False
        self.process_lifecycle_timer.stop()
        return True

    def eventFilter(self, watched, event):
        if event.type() == QEvent.Type.Quit:
            return not self.shutdown_runtime()
        return super().eventFilter(watched, event)

    def closeEvent(self, event):
        if self.shutdown_runtime():
            event.accept()
        else:
            event.ignore()

    def _poll_process_lifecycle(self):
        try:
            snapshot = self.process_lifecycle.poll()
        except (OSError, RuntimeError) as exc:
            self.statusBar().showMessage(f"Runtime lifecycle error: {exc}")
            return

        self.hardware_indicator_render_frame = (
            self.hardware_indicator_render_bridge.frame_for(
                snapshot
            )
        )

        if (
            self.process_lifecycle.state.name
            == "EXITED"
        ):
            for details in getattr(
                self,
                "_launch_status_details",
                (),
            ):
                details.process_exited()

            snapshot = (
                self.process_lifecycle
                .return_to_idle()
            )

            self.hardware_indicator_render_frame = (
                self.hardware_indicator_render_bridge.frame_for(
                    snapshot
                )
            )

        for details in getattr(
            self,
            "_launch_status_details",
            (),
        ):
            details.sync_process_session()


    def __init__(self):

        super().__init__()


        self.setWindowTitle(
            "RetroVault"
        )

        rvdb_consumer = None
        rvdb_service = None
        rvdb_resolver = None

        try:
            rvdb_consumer = RVDBConsumer(
                RVDB_BUNDLE
            )
            rvdb_service = RVDBService(
                rvdb_consumer
            )
            rvdb_resolver = RVDBLibraryResolver(
                rvdb_service
            )
        except RVDBError as exc:
            print(
                f"RVDB unavailable: {exc}"
            )

        controller = LibraryController(
            rvdb_resolver=rvdb_resolver,
            library_enabled=rvdb_resolver is not None,
        )

        self.retroarch_launcher = (
            RetroArchLauncher(
                executable=ConfigLoader().load()["retroarch"]["executable"],
                presentation_config_provider=ConfigLoader().load
            )
        )

        self.emulator_session = EmulatorSession(self.retroarch_launcher)

        self.hardware_runtime = (
            HardwareRuntimeOrchestrator(
                HardwareIndicatorPolicy()
            )
        )

        self.process_lifecycle = (
            ProcessLifecycleAdapter(
                self.hardware_runtime,
                self.emulator_session,
            )
        )

        self.game_launch_controller = GameLaunchController(
            launcher=self.emulator_session, process_lifecycle=self.process_lifecycle)

        self.hardware_indicator_render_bridge = (
            HardwareIndicatorRenderBridge()
        )

        self.hardware_indicator_render_frame = (
            self.hardware_indicator_render_bridge.frame_for(
                self.process_lifecycle.snapshot
            )
        )

        self.process_lifecycle_timer = QTimer(self)
        self.process_lifecycle_timer.setInterval(250)
        self.process_lifecycle_timer.timeout.connect(
            self._poll_process_lifecycle
        )
        self.process_lifecycle_timer.start()

        presentation_store = PresentationStore()

        presentation_composition_factory = (
            PresentationCompositionFactory(
                presentation_store=(
                    presentation_store
                ),
                config_loader=ConfigLoader(),
                recommendation_manifest=(
                    PresentationRecommendationManifest()
                ),
            )
        )


        self.pages = PageManager()


        def bulk_import_completed(
            _result,
        ) -> None:
            systems_page.refresh_page()
            playlists_page.refresh_collections(
                select_name=(
                    playlists_page
                    .selected_collection()
                )
            )

        def library_refresh_completed(
            _games,
        ) -> None:
            systems_page.refresh_page()
            playlists_page.refresh_collections(
                select_name=(
                    playlists_page
                    .selected_collection()
                )
            )

        library_page = LibraryPage(
            controller.get_games(),
            display_preferences=LibraryPreferences.from_config(ConfigLoader().load()),
            rvdb_service=rvdb_service,
            favorite_handler=(
                controller.set_favorite
            ),
            played_handler=(
                controller.record_played
            ),
            recent_provider=(
                controller.recent
            ),
            collection_names_provider=(
                controller.collection_names
            ),
            collection_add_handler=(
                controller.add_to_collection
            ),
            refresh_handler=(
                controller.reload_sources
            ),
            refresh_completed_handler=(
                library_refresh_completed
            ),
            bulk_import_handler=(
                controller.bulk_import
            ),
            bulk_import_completed_handler=(
                bulk_import_completed
            ),
            presentation_resolver_provider=(
                presentation_composition_factory.build_launch
            ),
            presentation_store=(
                presentation_store
            ),
            launcher=self.emulator_session,
            process_lifecycle=self.process_lifecycle,
            launch_controller=self.game_launch_controller,
        )

        self.pages.add_page(
            "Library",
            library_page
        )

        systems_page = SystemsPage(
            rvdb_service,
            games_provider=(
                controller.get_games
            ),
            recent_provider=(
                controller.recent
            ),
        )

        self.pages.add_page(
            "Systems",
            systems_page
        )

        systems_page.statistics_provider = controller.platform_statistics

        systems_page.collection_names_provider = (
            controller.collection_names
        )
        systems_page.collection_games_provider = (
            controller.collection_games
        )

        def show_system_library(
            platform_id: str,
        ) -> None:
            library_page.set_games(
                controller.get_games()
            )

            if library_page.show_platform(
                platform_id
            ):
                self.pages.show_page(
                    "Library"
                )

        systems_page.library_requested.connect(
            show_system_library
        )

        def show_system_favorites(
            platform_id: str,
        ) -> None:
            library_page.set_games(
                controller.get_games()
            )

            if library_page.show_platform(
                platform_id,
                favorites_only=True,
            ):
                self.pages.show_page(
                    "Library"
                )

        systems_page.library_favorites_requested.connect(
            show_system_favorites
        )

        def show_system_recent(
            platform_id: str,
        ) -> None:
            library_page.set_games(
                controller.get_games()
            )

            if library_page.show_platform(
                platform_id,
                recent_only=True,
            ):
                self.pages.show_page(
                    "Library"
                )

        systems_page.library_recent_requested.connect(
            show_system_recent
        )

        playlists_page = PlaylistsPage(
            controller,
            presentation_store=presentation_store,
            presentation_resolver_provider=presentation_composition_factory.build_launch,
            rvdb_service=rvdb_service,
            launcher=self.emulator_session,
            process_lifecycle=self.process_lifecycle,
            launch_controller=self.game_launch_controller,
        )

        self.pages.add_page(
            "Playlists",
            playlists_page
        )

        self._launch_status_details = (
            library_page.details,
            playlists_page.details,
        )

        def show_system_collections(
            platform_id: str,
        ) -> None:
            if playlists_page.show_platform_collections(
                platform_id
            ):
                self.pages.show_page(
                    "Playlists"
                )

        systems_page.library_collections_requested.connect(
            show_system_collections
        )

        overlays_page = OverlaysPage(
            presentation_store=(
                presentation_store
            ),
            current_game_provider=(
                lambda: (
                    library_page
                    .details
                    .current_game
                )
            ),
        )

        self.pages.add_page(
            "Overlays",
            overlays_page
        )

        self.pages.add_page(
            "RetroVault Visuals",
            NativeVisualsPage(
                presentation_resolver_provider=presentation_composition_factory.build_launch,
                presentation_store=(
                    presentation_store
                ),
                current_game_provider=(
                    lambda: (
                        library_page
                        .details
                        .current_game
                    )
                ),
            )
        )

        shaders_page = ShadersPage(
            presentation_store=(
                presentation_store
            ),
            current_game_provider=(
                lambda: (
                    library_page
                    .details
                    .current_game
                )
            ),
        )

        self.pages.add_page(
            "Shaders",
            shaders_page
        )

        overlays_page.assets_organized.connect(
            shaders_page.refresh_shaders
        )

        self.pages.add_page(
            "RetroArch",
            RetroArchPage(
                rvdb_service
            )
        )

        settings_page = SettingsPage()
        settings_page.library_preferences_previewed.connect(library_page.apply_display_preferences)
        settings_page.library_preferences_applied.connect(library_page.apply_display_preferences)

        def library_sources_changed() -> None:
            try:
                games = controller.reload_sources()
            except (
                OSError,
                RuntimeError,
                ValueError,
            ) as exc:
                settings_page.save_status.setText(
                    "Library source saved, but live "
                    f"reload failed: {exc}"
                )
                return

            library_page.set_games(
                games
            )

            systems_page.refresh_page()

            playlists_page.refresh_collections(
                select_name=(
                    playlists_page
                    .selected_collection()
                )
            )

        settings_page.library_sources_changed.connect(
            library_sources_changed
        )

        def artwork_directory_changed(directory):
            library_page.set_games(controller.refresh_artwork(directory))
            playlists_page.refresh_collections(
                select_name=playlists_page.selected_collection())

        settings_page.artwork_directory_saved.connect(artwork_directory_changed)

        settings_page.overlay_directory_saved.connect(
            overlays_page.set_directory
        )

        self.pages.add_page(
            "Settings",
            settings_page
        )


        sidebar = Sidebar(
            self.pages.show_page
        )


        container = QWidget()

        layout = QHBoxLayout()

        layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        layout.setSpacing(
            0
        )


        layout.addWidget(
            sidebar
        )

        layout.addWidget(
            self.pages,
            1,
        )


        container.setLayout(
            layout
        )

        self.setCentralWidget(
            container
        )
        if rvdb_resolver is None or not controller.get_games():
            self.pages.show_page("Settings")
        if rvdb_resolver is None:
            self.statusBar().showMessage("RVDB unavailable. Install a validated bundle and restart; Library scanning is disabled.")
