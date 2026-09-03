from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
)

from ui.library.widgets.game_grid import GameGrid
from ui.library.widgets.library_toolbar import LibraryToolbar

from ui.library.details.game_details import GameDetails
from ui.library.views.details_view import DetailsView
from ui.library.views.compact_view import CompactView

from services.library.randomizer import GameRandomizer



class GalleryView(QWidget):


    def __init__(
        self,
        games,
        rvdb_service=None,
        favorite_handler=None,
    ):

        super().__init__()


        self.all_games = games

        self.rvdb_service = (
            rvdb_service
        )

        self.favorite_handler = (
            favorite_handler
        )


        self.randomizer = GameRandomizer(
            games
        )


        main_layout = QVBoxLayout()


        self.toolbar = LibraryToolbar()


        systems = sorted(
            {
                game.platform

                for game in self.all_games

                if game.platform
            }
        )


        self.toolbar.system_filter.clear()

        self.toolbar.system_filter.addItem(
            "All Systems"
        )

        self.toolbar.system_filter.addItems(
            systems
        )


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
            rvdb_service=self.rvdb_service,
            favorite_handler=self.set_favorite,
        )


        self.grid = GameGrid(
            games,
            self.details
        )


        self.details_view = DetailsView(
            games,
            details=self.details,
        )


        self.compact_view = CompactView(
            games,
            details=self.details,
        )


        self.library_view_stack = QStackedWidget()


        self.library_view_stack.addWidget(
            self.grid
        )


        self.library_view_stack.addWidget(
            self.details_view
        )


        self.library_view_stack.addWidget(
            self.compact_view
        )


        content_layout.addWidget(
            self.library_view_stack,
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


        self.toolbar.favorites_changed.connect(
            self.refresh
        )


        self.toolbar.sort_changed.connect(
            self.refresh
        )


        self.toolbar.random_requested.connect(
            self.random_game
        )


        (
            self.toolbar.view_selector
            .gallery_selected.connect(
                self.show_gallery_view
            )
        )


        (
            self.toolbar.view_selector
            .details_selected.connect(
                self.show_details_view
            )
        )


        (
            self.toolbar.view_selector
            .compact_selected.connect(
                self.show_compact_view
            )
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


        if self.toolbar.favorites_only.isChecked():

            games = [

                game

                for game in games

                if getattr(
                    game,
                    "favorite",
                    False,
                )

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


        self.randomizer.games = games


        self.grid.update_games(
            games
        )


        self.details_view.update_games(
            games
        )


        self.compact_view.update_games(
            games
        )



    def show_gallery_view(self):

        self.library_view_stack.setCurrentWidget(
            self.grid
        )


    def show_details_view(self):

        self.library_view_stack.setCurrentWidget(
            self.details_view
        )


    def show_compact_view(self):

        self.library_view_stack.setCurrentWidget(
            self.compact_view
        )


    def set_favorite(
        self,
        game,
        favorite,
    ):

        if self.favorite_handler is not None:

            self.favorite_handler(
                game,
                favorite,
            )

        else:

            game.favorite = bool(
                favorite
            )


        self.refresh()


        if self.details.current_game is game:

            self.details.show_game(
                game
            )


    def random_game(self):

        game = (
            self.randomizer.random_game()
        )


        if game:

            self.details.show_game(
                game
            )
