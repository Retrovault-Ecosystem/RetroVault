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


class MainWindow(QMainWindow):


    def __init__(self):

        super().__init__()


        self.setWindowTitle(
            "RetroVault"
        )

        self.resize(
            1200,
            800
        )


        rvdb_consumer = None
        rvdb_service = None
        rvdb_resolver = None

        try:
            rvdb_consumer = RVDBConsumer(
                "data/rvdb/rvdb.bundle.json"
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
            rvdb_resolver=rvdb_resolver
        )


        self.pages = PageManager()


        library_page = LibraryPage(
            controller.get_games(),
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
        )

        self.pages.add_page(
            "Library",
            library_page
        )

        self.pages.add_page(
            "Systems",
            SystemsPage(
                rvdb_service
            )
        )

        self.pages.add_page(
            "Playlists",
            PlaylistsPage(
                controller,
                rvdb_service=rvdb_service,
            )
        )

        overlays_page = OverlaysPage()

        self.pages.add_page(
            "Overlays",
            overlays_page
        )

        shaders_page = ShadersPage()

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

        settings_page.artwork_directory_saved.connect(
            lambda directory: (
                library_page.set_games(
                    controller.refresh_artwork(
                        directory
                    )
                )
            )
        )

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
