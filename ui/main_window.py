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


        controller = LibraryController()

        rvdb_consumer = None

        try:
            rvdb_consumer = RVDBConsumer(
                "data/rvdb/rvdb.bundle.json"
            )
        except RVDBError as exc:
            print(
                f"RVDB unavailable: {exc}"
            )


        self.pages = PageManager()


        self.pages.add_page(
            "Library",
            LibraryPage(
                controller.get_games()
            )
        )

        self.pages.add_page(
            "Systems",
            SystemsPage(
                rvdb_consumer
            )
        )

        self.pages.add_page(
            "Playlists",
            PlaylistsPage()
        )

        self.pages.add_page(
            "Overlays",
            OverlaysPage()
        )

        self.pages.add_page(
            "Shaders",
            ShadersPage()
        )

        self.pages.add_page(
            "RetroArch",
            RetroArchPage()
        )

        self.pages.add_page(
            "Settings",
            SettingsPage()
        )


        sidebar = Sidebar(
            self.pages.show_page
        )


        container = QWidget()

        layout = QHBoxLayout()


        layout.addWidget(
            sidebar
        )

        layout.addWidget(
            self.pages
        )


        container.setLayout(
            layout
        )

        self.setCentralWidget(
            container
        )
