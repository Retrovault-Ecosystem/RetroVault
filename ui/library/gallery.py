from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
)

from ui.library.widgets.game_grid import GameGrid
from ui.library.widgets.library_toolbar import LibraryToolbar

from ui.library.details.game_details import GameDetails

from services.library.randomizer import GameRandomizer



class GalleryView(QWidget):


    def __init__(
        self,
        games,
        rvdb_service=None,
    ):

        super().__init__()


        self.all_games = games

        self.rvdb_service = (
            rvdb_service
        )


        self.randomizer = GameRandomizer(
            games
        )


        main_layout = QVBoxLayout()


        self.toolbar = LibraryToolbar()


        main_layout.addWidget(
            self.toolbar
        )


        title = QLabel(
            "RetroVault Library"
        )


        main_layout.addWidget(
            title
        )


        content_layout = QHBoxLayout()


        self.details = GameDetails(
            rvdb_service=self.rvdb_service
        )


        self.grid = GameGrid(
            games,
            self.details
        )


        content_layout.addWidget(
            self.grid,
            3
        )


        content_layout.addWidget(
            self.details,
            1
        )


        main_layout.addLayout(
            content_layout
        )


        self.toolbar.search_changed.connect(
            self.refresh
        )


        self.toolbar.system_changed.connect(
            self.refresh
        )


        self.toolbar.sort_changed.connect(
            self.refresh
        )


        self.toolbar.random_requested.connect(
            self.random_game
        )


        self.setLayout(
            main_layout
        )



    def refresh(self):

        games = self.all_games


        text = (
            self.toolbar.search.text()
            .lower()
        )


        if text:

            games = [

                game

                for game in games

                if text in game.name.lower()

            ]


        system = (
            self.toolbar.system_filter.currentText()
        )


        if system != "All Systems":

            games = [

                game

                for game in games

                if game.platform == system

            ]


        sort = (
            self.toolbar.sort.currentText()
        )


        if sort == "Name":

            games = sorted(
                games,
                key=lambda g: g.name
            )


        elif sort == "Year":

            games = sorted(
                games,
                key=lambda g: g.year or 0
            )


        self.grid.update_games(
            games
        )



    def random_game(self):

        game = (
            self.randomizer.random_game()
        )


        if game:

            print(
                f"Random game selected: {game.name}"
            )
