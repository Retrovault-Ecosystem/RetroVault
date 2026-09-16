from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QStackedWidget,
    QFileDialog,
    QMessageBox,
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
        played_handler=None,
        recent_provider=None,
        collection_names_provider=None,
        collection_add_handler=None,
        refresh_handler=None,
        refresh_completed_handler=None,
        bulk_import_handler=None,
        bulk_import_completed_handler=None,
        presentation_resolver_provider=None,
        launcher=None,
        process_lifecycle=None,
    ):

        super().__init__()


        self.all_games = games

        self._direct_platform_id = None

        self.rvdb_service = (
            rvdb_service
        )

        self.favorite_handler = (
            favorite_handler
        )

        self.played_handler = (
            played_handler
        )

        self.recent_provider = (
            recent_provider
        )

        self.refresh_handler = (
            refresh_handler
        )

        self.refresh_completed_handler = (
            refresh_completed_handler
        )

        self.bulk_import_handler = (
            bulk_import_handler
        )

        self.bulk_import_completed_handler = (
            bulk_import_completed_handler
        )


        self.randomizer = GameRandomizer(
            games
        )


        main_layout = QVBoxLayout()


        self.toolbar = LibraryToolbar()

        self.toolbar.system_changed.connect(
            self._manual_system_filter_changed
        )


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
            played_handler=self.record_played,
            collection_names_provider=(
                collection_names_provider
            ),
            collection_add_handler=(
                collection_add_handler
            ),
            presentation_resolver_provider=(
                presentation_resolver_provider
            ),
            launcher=launcher,
            process_lifecycle=process_lifecycle,
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


        self.toolbar.recent_changed.connect(
            self.refresh
        )


        self.toolbar.sort_changed.connect(
            self.refresh
        )


        self.toolbar.random_requested.connect(
            self.random_game
        )


        self.toolbar.refresh_requested.connect(
            self.reload_library
        )

        self.toolbar.bulk_import_requested.connect(
            self.bulk_import
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



    def reload_library(self):

        if self.refresh_handler is None:
            return

        selected_game = (
            self.details.current_game
        )

        search_text = (
            self.toolbar.search.text()
        )

        current_system = (
            self.toolbar.system_filter.currentText()
        )

        current_sort = (
            self.toolbar.sort.currentText()
        )

        favorites_only = (
            self.toolbar.favorites_only.isChecked()
        )

        recent_only = (
            self.toolbar.recent_only.isChecked()
        )

        current_view = (
            self.library_view_stack.currentWidget()
        )

        try:
            games = self.refresh_handler()
        except (
            OSError,
            RuntimeError,
            ValueError,
        ) as exc:
            self.toolbar.setToolTip(
                "Library refresh failed: "
                f"{exc}"
            )
            return

        self.set_games(
            games
        )

        self.toolbar.search.setText(
            search_text
        )

        if (
            self.toolbar.system_filter.findText(
                current_system
            )
            >= 0
        ):
            self.toolbar.system_filter.setCurrentText(
                current_system
            )

        self.toolbar.sort.setCurrentText(
            current_sort
        )

        self.toolbar.favorites_only.setChecked(
            favorites_only
        )

        self.toolbar.recent_only.setChecked(
            recent_only
        )

        if current_view is self.details_view:
            self.show_details_view()
        elif current_view is self.compact_view:
            self.show_compact_view()
        else:
            self.show_gallery_view()

        if (
            selected_game is not None
            and selected_game in self.all_games
        ):
            self.details.show_game(
                selected_game
            )
        elif selected_game is not None:
            self.details.clear_game()

        self.toolbar.setToolTip(
            "Library refreshed."
        )

        if (
            self.refresh_completed_handler
            is not None
        ):
            self.refresh_completed_handler(
                games
            )


    def bulk_import(self):

        if self.bulk_import_handler is None:
            return

        directory = QFileDialog.getExistingDirectory(
            self,
            "Bulk Import ROMs",
        )

        if not directory:
            return

        try:
            result = self.bulk_import_handler(
                directory
            )
        except (OSError, ValueError) as exc:
            QMessageBox.critical(
                self,
                "Bulk Import Failed",
                (
                    "RetroVault could not import "
                    "ROMs from the selected folder.\n\n"
                    f"{exc}"
                ),
            )
            return

        imported_games = result.get(
            "games"
        )

        if imported_games is not None:
            self.set_games(
                imported_games
            )

        if (
            self.bulk_import_completed_handler
            is not None
        ):
            self.bulk_import_completed_handler(
                result
            )

        discovered = result["discovered"]
        persisted = result.get(
            "persisted",
            {},
        )

        source_saved = bool(
            persisted.get(
                "added",
                False,
            )
        )

        source_status = (
            "Saved as a library source"
            if source_saved
            else "Already registered as a library source"
        )

        QMessageBox.information(
            self,
            "Bulk Import Complete",
            (
                "RetroVault finished scanning "
                "the selected folder.\n\n"
                f"ROMs discovered: "
                f"{discovered.discovered_count}\n"
                f"Games added: "
                f"{result['added_count']}\n"
                f"Already in library / skipped: "
                f"{result['skipped_count']}\n"
                f"Duplicates inside source: "
                f"{discovered.duplicate_count}\n"
                f"Source: {source_status}"
            ),
        )


    def _manual_system_filter_changed(
        self,
        _system: str,
    ) -> None:
        self._direct_platform_id = None


    def show_platform(
        self,
        platform_id: str,
        *,
        favorites_only: bool = False,
        recent_only: bool = False,
    ) -> bool:
        platform_names = sorted(
            {
                str(game.platform)
                for game in self.all_games
                if (
                    str(
                        getattr(
                            game,
                            "rvdb_platform_id",
                            "",
                        )
                        or ""
                    )
                    == platform_id
                    and getattr(
                        game,
                        "platform",
                        "",
                    )
                )
            },
            key=str.casefold,
        )

        if not platform_names:
            return False

        platform_name = platform_names[0]

        index = (
            self.toolbar.system_filter.findText(
                platform_name
            )
        )

        if index < 0:
            return False

        self.toolbar.search.clear()
        self.toolbar.favorites_only.setChecked(
            favorites_only
        )
        self.toolbar.recent_only.setChecked(
            recent_only
        )

        self.toolbar.system_filter.blockSignals(
            True
        )

        try:
            self.toolbar.system_filter.setCurrentIndex(
                index
            )
        finally:
            self.toolbar.system_filter.blockSignals(
                False
            )

        self._direct_platform_id = platform_id

        self.refresh()

        return True

    def set_games(
        self,
        games,
    ):
        self._direct_platform_id = None

        current_system = (
            self.toolbar.system_filter.currentText()
        )

        self.all_games = games

        systems = sorted(
            {
                game.platform
                for game in self.all_games
                if game.platform
            }
        )

        self.toolbar.system_filter.blockSignals(
            True
        )

        try:
            self.toolbar.system_filter.clear()

            self.toolbar.system_filter.addItem(
                "All Systems"
            )

            self.toolbar.system_filter.addItems(
                systems
            )

            if current_system in systems:
                self.toolbar.system_filter.setCurrentText(
                    current_system
                )
            else:
                self.toolbar.system_filter.setCurrentText(
                    "All Systems"
                )
        finally:
            self.toolbar.system_filter.blockSignals(
                False
            )

        self.refresh()


    def refresh(self):

        recent_active = (
            self.toolbar.recent_only.isChecked()
        )

        if (
            recent_active
            and self.recent_provider is not None
        ):

            identities = list(
                self.recent_provider()
            )

            games_by_identity = {
                str(game.rom): game
                for game in self.all_games
            }

            games = [
                games_by_identity[identity]
                for identity in identities
                if identity in games_by_identity
            ]

        elif recent_active:

            games = []

        else:

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


        if self._direct_platform_id is not None:

            games = [

                game

                for game in games

                if str(
                    getattr(
                        game,
                        "rvdb_platform_id",
                        "",
                    )
                    or ""
                )
                == self._direct_platform_id

            ]

        elif system != "All Systems":

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


        if not recent_active:

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


    def record_played(
        self,
        game,
    ):

        result = None

        if self.played_handler is not None:

            result = self.played_handler(
                game
            )

        self.refresh()

        return result


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
