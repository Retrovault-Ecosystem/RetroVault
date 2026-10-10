from config.library_preferences import LibraryPreferences
from services.library.identity import game_identity
from services.library.identity import project_identities
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
        presentation_store=None,
        launcher=None,
        process_lifecycle=None,
        launch_controller=None,
        display_preferences=None,
    ):

        super().__init__()
        preferences = LibraryPreferences.from_values(
            (display_preferences or LibraryPreferences()).to_dict())

        self.presentation_store = (
            presentation_store
        )

        self.setObjectName(
            "LibraryPage"
        )


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

        self._browsing_order_changed = False
        self.discovery_jobs = None
        self._library_refresh_in_progress = False
        self._bulk_import_in_progress = False

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

        title.setObjectName(
            "LibraryTitle"
        )

        subtitle = QLabel(
            "Browse, curate, launch, and present "
            "your game collection."
        )

        subtitle.setObjectName(
            "LibrarySubtitle"
        )


        main_layout.addWidget(
            title
        )

        main_layout.addWidget(
            subtitle
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
            presentation_store=(
                presentation_store
            ),
            launcher=launcher,
            process_lifecycle=process_lifecycle,
            launch_controller=launch_controller,
        )


        self.grid = GameGrid(
            games,
            self.details,
            card_size=preferences.card_size,
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

        self.library_view_stack.setObjectName(
            "LibraryViewStack"
        )


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


        self.setLayout(main_layout)
        self.display_preferences = LibraryPreferences()
        self.apply_display_preferences(preferences)
        for signal in (self.toolbar.search_changed, self.toolbar.system_changed,
                       self.toolbar.sort_changed, self.toolbar.favorites_changed,
                       self.toolbar.recent_changed):
            signal.connect(self._mark_browsing_order_changed)




    def reload_library(self):
        if self.discovery_jobs is not None:
            self.discovery_jobs.request("refresh")
            return

        if self.refresh_handler is None:
            return

        if (
            self._library_refresh_in_progress
            or self._bulk_import_in_progress
        ):
            return

        self._library_refresh_in_progress = True

        self.toolbar.refresh_button.setEnabled(
            False
        )

        self.toolbar.bulk_import_button.setEnabled(
            False
        )

        self.toolbar.refresh_status.setText(
            "Refreshing..."
        )

        self.toolbar.setToolTip(
            "Refreshing library..."
        )

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
            message = (
                "Library refresh failed: "
                f"{exc}"
            )

            self.toolbar.refresh_status.setText(
                "Refresh failed."
            )

            self.toolbar.refresh_status.setToolTip(
                message
            )

            self.toolbar.setToolTip(
                message
            )

            self._library_refresh_in_progress = False

            self.toolbar.refresh_button.setEnabled(
                True
            )

            self.toolbar.bulk_import_button.setEnabled(
                True
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

        if (
            self.refresh_completed_handler
            is not None
        ):
            try:
                self.refresh_completed_handler(
                    games
                )
            except (
                OSError,
                RuntimeError,
                ValueError,
            ) as exc:
                message = (
                    "Library refreshed, but "
                    "dependent views could not "
                    f"refresh: {exc}"
                )

                self.toolbar.refresh_status.setText(
                    "Refresh partially completed."
                )

                self.toolbar.refresh_status.setToolTip(
                    message
                )

                self.toolbar.setToolTip(
                    message
                )

                self._library_refresh_in_progress = False

                self.toolbar.refresh_button.setEnabled(
                    True
                )

                self.toolbar.bulk_import_button.setEnabled(
                    True
                )

                return

        self.toolbar.refresh_status.setText(
            "Library refreshed."
        )

        self.toolbar.refresh_status.setToolTip(
            "Library refreshed."
        )

        self.toolbar.setToolTip(
            "Library refreshed."
        )

        self._library_refresh_in_progress = False

        self.toolbar.refresh_button.setEnabled(
            True
        )

        self.toolbar.bulk_import_button.setEnabled(
            True
        )


    def bulk_import(self):
        if self.discovery_jobs is not None:
            if self.discovery_jobs.busy:
                return
            directory = QFileDialog.getExistingDirectory(self, 'Bulk Import ROMs')
            if directory:
                self.discovery_jobs.request('import', directory)
            return

        if self.bulk_import_handler is None:
            return

        if (
            self._bulk_import_in_progress
            or self._library_refresh_in_progress
        ):
            return

        directory = QFileDialog.getExistingDirectory(
            self,
            "Bulk Import ROMs",
        )

        if not directory:
            return

        self._bulk_import_in_progress = True

        self.toolbar.bulk_import_button.setEnabled(
            False
        )

        self.toolbar.refresh_button.setEnabled(
            False
        )

        try:
            result = self.bulk_import_handler(
                directory
            )
        except (OSError, ValueError) as exc:
            self._bulk_import_in_progress = False

            self.toolbar.bulk_import_button.setEnabled(
                True
            )

            self.toolbar.refresh_button.setEnabled(
                True
            )

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

        try:
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

            summary = (
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
            )
        except (
            KeyError,
            OSError,
            RuntimeError,
            TypeError,
            ValueError,
        ):
            return
        finally:
            self._bulk_import_in_progress = False

            self.toolbar.bulk_import_button.setEnabled(
                True
            )

            self.toolbar.refresh_button.setEnabled(
                True
            )

        QMessageBox.information(
            self,
            "Bulk Import Complete",
            summary,
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
        *, preserve_initial_order=False,
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

        self.refresh(preserve_order=preserve_initial_order)


    def refresh(self, *, preserve_order=False):

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

            games = project_identities(self.all_games, identities)

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


        if not recent_active and not preserve_order:

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

        self.toolbar.view_selector.set_mode("gallery")

        self.library_view_stack.setCurrentWidget(
            self.grid
        )


    def show_details_view(self):

        self.toolbar.view_selector.set_mode("details")

        self.library_view_stack.setCurrentWidget(
            self.details_view
        )


    def show_compact_view(self):

        self.toolbar.view_selector.set_mode("compact")

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

    def apply_display_preferences(self, preferences):
        """Apply display state only; never rescan, persist or change game policy."""
        preferences = LibraryPreferences.from_values(preferences.to_dict())
        selected = self.details.current_game
        identity = game_identity(selected) if selected is not None else None
        scrolls = [self.grid.scroll, self.details_view.list, self.compact_view.list]
        positions = [(widget.horizontalScrollBar().value(), widget.verticalScrollBar().value())
                     for widget in scrolls]
        self.grid.set_card_size(preferences.card_size)
        sort_text = {'name': 'Name', 'year': 'Year'}[preferences.normal_sort]
        if self.toolbar.sort.currentText() != sort_text:
            self._browsing_order_changed = True
            blocked = self.toolbar.sort.blockSignals(True)
            self.toolbar.sort.setCurrentText(sort_text)
            self.toolbar.sort.blockSignals(blocked)
            lists = [self.details_view.list, self.compact_view.list]
            prior = [widget.blockSignals(True) for widget in lists]
            try:
                self.refresh()
            finally:
                for widget, was_blocked in zip(lists, prior):
                    widget.blockSignals(was_blocked)
        self.details_view.restore_selection(identity)
        self.compact_view.restore_selection(identity)
        {'gallery': self.show_gallery_view, 'details': self.show_details_view,
         'compact': self.show_compact_view}[preferences.opening_view]()
        # Recompute the scroll ranges before restoring/clamping positions.
        for widget, (horizontal, vertical) in zip(scrolls, positions):
            if widget is self.grid.scroll:
                self.grid.layout.activate()
            else:
                widget.doItemsLayout()
            widget.horizontalScrollBar().setValue(horizontal)
            widget.verticalScrollBar().setValue(vertical)
        self.display_preferences = preferences

    def bind_discovery_jobs(self, jobs):
        self.discovery_jobs = jobs
        jobs.status.connect(self.toolbar.refresh_status.setText)
        jobs.failed.connect(self._discovery_failed)
        jobs.busy_changed.connect(self._discovery_busy)
        jobs.published.connect(self._discovery_published)
        self.toolbar.cancel_discovery_requested.connect(jobs.cancel)

    def _discovery_busy(self, busy):
        self.toolbar.bulk_import_button.setEnabled(not busy)
        self.toolbar.cancel_discovery_button.setEnabled(busy and not self.discovery_jobs.committing)
        self.toolbar.refresh_button.setEnabled(True)

    def _discovery_failed(self, message):
        self.toolbar.refresh_status.setText(message)
        self.toolbar.refresh_status.setToolTip(message)

    def _discovery_published(self, result):
        selected = self.details.current_game
        selected_id = game_identity(selected) if selected is not None else None
        direct_platform = self._direct_platform_id
        widgets = [self.grid.scroll, self.details_view.list, self.compact_view.list]
        positions = [(w.horizontalScrollBar().value(), w.verticalScrollBar().value()) for w in widgets]
        lists = [self.details_view.list, self.compact_view.list]
        blocked = [w.blockSignals(True) for w in lists]
        try:
            preserve_order = (result.get('startup', False) and not self._browsing_order_changed
                              and self.toolbar.sort.currentText() == 'Name')
            self.set_games(result['games'], preserve_initial_order=preserve_order)
            # Canonical platform filtering is not equivalent to a display-name combo.
            if direct_platform is not None:
                self._direct_platform_id = direct_platform
                self.refresh()
            games_by_id = {game_identity(game): game for game in self.all_games}
            if selected_id in games_by_id:
                self.details.show_game(games_by_id[selected_id])
            elif selected_id is not None:
                self.details.clear_game()
            self.details_view.restore_selection(selected_id)
            self.compact_view.restore_selection(selected_id)
            for widget, (horizontal, vertical) in zip(widgets, positions):
                if widget is self.grid.scroll:
                    self.grid.layout.activate()
                else:
                    widget.doItemsLayout()
                widget.horizontalScrollBar().setValue(horizontal)
                widget.verticalScrollBar().setValue(vertical)
            callback = (self.bulk_import_completed_handler if result.get('discovered') is not None
                        else self.refresh_completed_handler)
            if callback is not None:
                callback(result if result.get('discovered') is not None else result['games'])
            discovered = result.get('discovered')
            summary = ('Library refreshed.' if discovered is None else
                       f'Import complete: {discovered.discovered_count} discovered; '
                       f'{result["added_count"]} added; {result["skipped_count"]} skipped; '
                       f'{discovered.duplicate_count} duplicate paths.')
            self.toolbar.refresh_status.setText(summary + result.get('warning', ''))
        except Exception as exc:
            self._discovery_failed(f'Library saved, but dependent views could not refresh: {exc}. Retry Refresh.')
        finally:
            for widget, previous in zip(lists, blocked):
                widget.blockSignals(previous)

    def _mark_browsing_order_changed(self, *args):
        self._browsing_order_changed = True
