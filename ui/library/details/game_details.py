from controllers.game_launch_controller import GameLaunchController
from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QInputDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
)

from PyQt6.QtGui import QPixmap

from PyQt6.QtCore import Qt

from pathlib import Path




from services.retroarch.archive_variant import ArchiveVariantFormatter
from ui.library.widgets.game_edition_launcher import GameEditionLauncher
from ui.library.widgets.cheat_studio import CheatStudio

from services.rvdb import RVDBError
from ui.library.widgets.presentation_studio import PresentationStudio



class _GameDetailsScrollContent(QWidget):

    def minimumSizeHint(
        self
    ):
        hint = super().minimumSizeHint()

        hint.setWidth(
            0
        )

        return hint


class GameDetails(QWidget):


    def __init__(
        self,
        rvdb_service=None,
        favorite_handler=None,
        played_handler=None,
        collection_names_provider=None,
        collection_add_handler=None,
        presentation_resolver_provider=None,
        presentation_store=None,
        launcher=None,
        process_lifecycle=None,
        archive_runtime=None,
        cheat_service=None,
        launch_controller=None,
    ):

        super().__init__()

        self.setObjectName(
            "LibraryGameDetails"
        )


        self.current_game = None

        self.rvdb_service = (
            rvdb_service
        )

        self.favorite_handler = (
            favorite_handler
        )

        self.played_handler = (
            played_handler
        )

        self.collection_names_provider = (
            collection_names_provider
        )

        self.collection_add_handler = (
            collection_add_handler
        )

        self.presentation_resolver_provider = (
            presentation_resolver_provider
        )

        self.presentation_store = (
            presentation_store
        )


        self.launch_controller = launch_controller or GameLaunchController(
            launcher=launcher, process_lifecycle=process_lifecycle,
            archive_runtime=archive_runtime, cheat_service=cheat_service)
        for name in ('config', 'core_resolver', 'launcher', 'process_lifecycle',
                     'archive_runtime', 'cheat_service', 'diagnostics'):
            setattr(self, name, getattr(self.launch_controller, name))

        outer = QVBoxLayout(
            self
        )

        outer.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        outer.setSpacing(
            0
        )

        self.details_scroll = QScrollArea(
            self
        )

        self.details_scroll.setObjectName(
            "LibraryGameDetailsScroll"
        )

        self.details_scroll.setWidgetResizable(
            True
        )

        self.details_scroll.setFrameShape(
            QScrollArea.Shape.NoFrame
        )

        self.details_scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )

        self.details_scroll.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )

        self.details_content = _GameDetailsScrollContent()

        self.details_content.setObjectName(
            "LibraryGameDetailsContent"
        )

        self.details_content.setMinimumWidth(
            0
        )

        self.details_content.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )

        main = QVBoxLayout(
            self.details_content
        )


        top = QVBoxLayout()

        top.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        top.setSpacing(
            10
        )



        self.cover = QLabel(
            "🎮"
        )

        self.cover.setObjectName(
            "LibraryDetailsCover"
        )


        self.cover.setMinimumHeight(
            220
        )

        self.cover.setMaximumHeight(
            300
        )

        self.cover.setMinimumWidth(
            0
        )

        self.cover.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )


        self.cover.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )


        top.addWidget(
            self.cover
        )



        info = QVBoxLayout()


        self.title = QLabel(
            "Select a game"
        )

        self.title.setTextFormat(Qt.TextFormat.PlainText)
        self.title.setObjectName(
            "LibraryDetailsTitle"
        )

        self.title.setWordWrap(
            True
        )

        self.title.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )


        self.metadata = QLabel()
        self.metadata.setTextFormat(Qt.TextFormat.PlainText)

        self.metadata.setObjectName(
            "LibraryDetailsMetadata"
        )

        self.metadata.setWordWrap(
            True
        )

        self.metadata.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )


        self.description = QTextEdit()

        self.description.setObjectName(
            "LibraryDetailsDescription"
        )


        self.description.setReadOnly(
            True
        )


        info.addWidget(
            self.title
        )


        info.addWidget(
            self.metadata
        )


        info.addWidget(
            self.description
        )


        top.addLayout(
            info
        )

        top.setStretch(
            0,
            0,
        )

        top.setStretch(
            1,
            0,
        )


        main.addLayout(
            top
        )



        self.profile = QLabel(
            "Launch Profile"
        )

        self.profile.setObjectName(
            "LibraryLaunchProfile"
        )


        main.addWidget(
            self.profile
        )



        self.favorite_button = QPushButton(
            "☆ Add to Favorites"
        )

        self.favorite_button.setObjectName(
            "LibraryFavoriteAction"
        )

        self.favorite_button.setEnabled(
            False
        )

        self.favorite_button.clicked.connect(
            self.toggle_favorite
        )

        main.addWidget(
            self.favorite_button
        )


        self.collection_button = QPushButton(
            "＋ Add to Collection"
        )

        self.collection_button.setObjectName(
            "LibraryCollectionAction"
        )

        self.collection_button.setEnabled(
            False
        )

        self.collection_button.clicked.connect(
            self.add_to_collection
        )

        main.addWidget(
            self.collection_button
        )


        self.launch_button = QPushButton(
            "▶ Launch Game"
        )

        self.launch_button.setObjectName(
            "LibraryLaunchAction"
        )

        self.launch_button.setEnabled(
            False
        )


        self.launch_button.clicked.connect(
            self.launch_game
        )


        main.addWidget(
            self.launch_button
        )


        self.stop_button = QPushButton(
            "■ Stop Game"
        )

        self.stop_button.setObjectName(
            "LibraryStopAction"
        )

        self.stop_button.setEnabled(
            False
        )

        self.stop_button.clicked.connect(
            self.stop_game
        )

        main.addWidget(
            self.stop_button
        )


        self._launch_session_active = False

        self.launch_status = QLabel(
            "Ready when you are."
        )

        self.launch_status.setObjectName(
            "LibraryLaunchStatus"
        )

        self.launch_status.setWordWrap(
            True
        )

        main.addWidget(
            self.launch_status
        )



        self.presentation_studio = PresentationStudio(
            presentation_store=(
                self.presentation_store
            ),
            presentation_resolver_provider=(
                self.presentation_resolver_provider
            ),
            parent=self,
        )

        main.addWidget(
            self.presentation_studio
        )

        main.addStretch(
            1
        )

        self.details_scroll.setWidget(
            self.details_content
        )

        outer.addWidget(
            self.details_scroll
        )



    def _reset_details_scroll_position(
        self
    ):
        """
        Start a newly-selected Game Details context at the top.

        The inspector is intentionally vertically scrollable.
        Scroll position belongs to the current inspection
        context and must not leak into the next selected game
        or the empty-selection state.
        """

        bar = (
            self.details_scroll
            .verticalScrollBar()
        )

        bar.setValue(
            bar.minimum()
        )


    def show_game(
        self,
        game
    ):


        selection_changed = (
            self.current_game is not game
        )

        self.current_game = game

        if selection_changed:
            self._launch_session_active = False

            if self._process_session_running():
                self._set_launch_status(
                    "Another game session is running."
                )
            else:
                self._set_launch_status(
                    "Ready when you are."
                )

        self._refresh_favorite_button()
        self._refresh_collection_button()
        self._refresh_launch_button()

        self._refresh_cover()


        self.title.setText(
            game.name
        )


        metadata_lines = [
            f"System: {game.platform}",
            f"Core: {game.core}",
        ]

        rvdb_platform_id = getattr(
            game,
            "rvdb_platform_id",
            None,
        )

        rvdb_platform = None

        if (
            rvdb_platform_id
            and self.rvdb_service is not None
        ):
            try:
                view = (
                    self.rvdb_service
                    .platform_view(
                        rvdb_platform_id
                    )
                )
            except RVDBError:
                view = None

            if view is not None:
                rvdb_platform = (
                    view.platform
                )

        if rvdb_platform is not None:
            canonical_name = (
                rvdb_platform.name
                or rvdb_platform_id
            )

            metadata_lines.extend(
                [
                    "",
                    "RVDB Platform:",
                    canonical_name,
                    (
                        "RVDB ID: "
                        f"{rvdb_platform_id}"
                    ),
                ]
            )

            release_year = (
                rvdb_platform.release_year
            )

            if release_year not in (
                None,
                "",
            ):
                metadata_lines.append(
                    "Platform Release: "
                    f"{release_year}"
                )

        self.metadata.setText(
            "\n".join(
                metadata_lines
            )
        )



        profile_lines = [
            game.name,
            "",
            "RetroVault Game Profile",
        ]

        rvdb_game_id = getattr(
            game,
            "rvdb_game_id",
            "",
        )

        if (
            isinstance(
                rvdb_game_id,
                str,
            )
            and rvdb_game_id.strip()
        ):
            canonical_game = None

            if self.rvdb_service is not None:
                try:
                    canonical_game = (
                        self.rvdb_service.game(
                            rvdb_game_id.strip()
                        )
                    )
                except RVDBError:
                    canonical_game = None

            profile_lines.extend(
                [
                    "",
                    "RVDB Game:",
                ]
            )

            if canonical_game is not None:
                profile_lines.append(
                    canonical_game.name
                )

            profile_lines.append(
                f"RVDB ID: {rvdb_game_id.strip()}"
            )

        profile_metadata = []

        year = getattr(
            game,
            "year",
            None,
        )

        if year not in (
            None,
            "",
            0,
        ):
            profile_metadata.append(
                f"Release Year: {year}"
            )

        genre = getattr(
            game,
            "genre",
            "",
        )

        if (
            isinstance(
                genre,
                str,
            )
            and genre.strip()
        ):
            profile_metadata.append(
                f"Genre: {genre.strip()}"
            )

        developer = getattr(
            game,
            "developer",
            "",
        )

        if (
            isinstance(
                developer,
                str,
            )
            and developer.strip()
        ):
            profile_metadata.append(
                "Developer: "
                f"{developer.strip()}"
            )

        publisher = getattr(
            game,
            "publisher",
            "",
        )

        if (
            isinstance(
                publisher,
                str,
            )
            and publisher.strip()
        ):
            profile_metadata.append(
                "Publisher: "
                f"{publisher.strip()}"
            )

        if profile_metadata:
            profile_lines.extend(
                [
                    "",
                    *profile_metadata,
                ]
            )

        description = getattr(
            game,
            "description",
            "",
        )

        if (
            isinstance(
                description,
                str,
            )
            and description.strip()
        ):
            profile_lines.extend(
                [
                    "",
                    description.strip(),
                ]
            )

        self.description.setPlainText(
            "\n".join(
                profile_lines
            )
        )

        self.presentation_studio.set_game(
            self.current_game
        )

        self._reset_details_scroll_position()

    def _refresh_cover(self):

        self.cover.clear()

        artwork = getattr(
            self.current_game,
            "artwork",
            "",
        )

        if artwork:

            pixmap = QPixmap(
                artwork
            )

            if not pixmap.isNull():

                self.cover.setPixmap(
                    pixmap.scaled(
                        self.cover.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )

                return

        self.cover.setText(
            "🎮"
        )


    def _refresh_favorite_button(self):

        if self.current_game is None:

            self.favorite_button.setEnabled(
                False
            )

            self.favorite_button.setText(
                "☆ Add to Favorites"
            )

            return


        self.favorite_button.setEnabled(
            True
        )


        if getattr(
            self.current_game,
            "favorite",
            False,
        ):

            self.favorite_button.setText(
                "★ Remove from Favorites"
            )

        else:

            self.favorite_button.setText(
                "☆ Add to Favorites"
            )


    def toggle_favorite(self):

        if self.current_game is None:
            return


        favorite = not bool(
            getattr(
                self.current_game,
                "favorite",
                False,
            )
        )


        try:

            if self.favorite_handler is not None:

                self.favorite_handler(
                    self.current_game,
                    favorite,
                )

            else:

                self.current_game.favorite = (
                    favorite
                )

        except (
            OSError,
            ValueError,
        ) as exc:

            QMessageBox.warning(
                self,
                "Favorite Update Failed",
                "RetroVault could not update "
                "this game's Favorite status.\n\n"
                f"{exc}",
            )

            return


        self._refresh_favorite_button()


    def _select_archive_member(
        self,
        rom,
    ):
        """
        Return the archive member selected for this launch.

        A single playable member launches directly. Multi-member
        archives expose every playable variant, with RetroVault's
        preferred member preselected. Cancelling the selector aborts
        the launch without changing durable Library identity.
        """
        members = (
            self.archive_runtime
            .playable_members(
                rom
            )
        )

        if not members:
            return ""

        if len(members) == 1:
            return members[0]

        preferred = (
            self.archive_runtime
            .preferred_from_members(
                rom,
                members,
            )
        )

        default_index = 0

        if preferred in members:
            default_index = members.index(
                preferred
            )

        variants = [
            ArchiveVariantFormatter.describe(
                member,
                preferred=(
                    member == preferred
                ),
            )
            for member in members
        ]

        labels = []
        label_counts = {}

        for variant in variants:
            base_label = variant.display_name

            occurrence = (
                label_counts.get(
                    base_label,
                    0,
                )
                + 1
            )

            label_counts[
                base_label
            ] = occurrence

            if occurrence == 1:
                labels.append(
                    base_label
                )
            else:
                labels.append(
                    f"{base_label} "
                    f"[Variant {occurrence}]"
                )

        selected, accepted = (
            QInputDialog.getItem(
                self,
                "Select Game Version",
                "Choose the version to launch:",
                labels,
                default_index,
                False,
            )
        )

        if not accepted:
            return None

        try:
            selected_index = labels.index(
                selected
            )
        except ValueError:
            raise ValueError(
                "Archive variant selector returned "
                "an unknown display value."
            ) from None

        if not (
            0
            <= selected_index
            < len(variants)
        ):
            raise ValueError(
                "Archive variant selector returned "
                "an invalid member index."
            )

        return variants[
            selected_index
        ].member


    def _set_launch_status(
        self,
        message: str,
    ) -> None:
        self.launch_status.setText(
            message
        )


    def _process_session_running(self) -> bool:
        self.launch_controller.launcher = self.launcher
        return self.launch_controller._process_session_running()


    def sync_process_session(
        self,
    ) -> None:
        """
        Synchronize controls with shared emulator process ownership.

        A details pane owns launch-status text only for the game it
        launched. Launch availability, however, follows the single
        shared RetroArch process session across every details pane.
        """

        self._refresh_launch_button()


    def process_exited(
        self,
    ) -> None:
        if not self._launch_session_active:
            return

        self._launch_session_active = False
        self._refresh_launch_button()

        self._set_launch_status(
            "Game session ended."
        )


    def stop_game(
        self,
    ) -> None:
        if not self._launch_session_active:
            return

        if self.process_lifecycle is None:
            return

        try:
            self.launch_controller.stop()
        except (OSError, RuntimeError) as exc:
            self._set_launch_status(
                f"Unable to stop game: {exc}"
            )
            return

        self._set_launch_status(
            "Stopping game..."
        )
        self._refresh_launch_button()


    def _select_game_edition(
        self,
    ):
        """
        Return the physical edition selected for this launch.

        Canonical Library entries with one physical edition launch
        directly. Multi-edition families use RetroVault's grouped
        Game Edition Launcher.

        Cancelling selection aborts only this launch attempt and does
        not alter canonical Library identity.
        """

        if self.current_game is None:
            return None

        return GameEditionLauncher.choose(
            self.current_game,
            self,
        )


    def _launch_target_from_variant(self, variant):
        # Compatibility entry point for callers inspecting an edition before launch.
        self.launch_controller.current_game = self.current_game
        try:
            return self.launch_controller._launch_target_from_variant(variant)
        finally:
            self.launch_controller.current_game = None


    def _select_cheats(
        self,
        launch_game,
        archive_member="",
    ):
        """
        Run Cheat Studio against the exact physical launch target.

        Returning None means the user cancelled the launch.
        Returning an empty list means continue without cheats.
        """

        return CheatStudio.choose(
            game=launch_game,
            archive_member=archive_member,
            cheat_service=self.cheat_service,
            parent=self,
        )


    def _cheat_runtime_file(self, cheats):
        return self.launch_controller._cheat_runtime_file(cheats)


    def launch_game(self):
        controller = self.launch_controller
        for name in ('config', 'core_resolver', 'launcher', 'process_lifecycle',
                     'archive_runtime', 'cheat_service', 'diagnostics'):
            setattr(controller, name, getattr(self, name))
        self._launch_session_active = controller.launch(
            self.current_game,
            choose_edition=self._select_game_edition,
            choose_archive=self._select_archive_member,
            choose_cheats=self._select_cheats,
            status=self._set_launch_status,
            warning=lambda title, message: QMessageBox.warning(self, title, message),
            played=self.played_handler,
            presentation_provider=self.presentation_resolver_provider,
        )
        self._refresh_launch_button()

    def _refresh_collection_button(
        self,
    ):
        enabled = (
            self.current_game is not None
            and bool(
                getattr(
                    self.current_game,
                    "rom",
                    "",
                )
            )
            and self.collection_names_provider
            is not None
            and self.collection_add_handler
            is not None
        )

        self.collection_button.setEnabled(
            enabled
        )


    def add_to_collection(
        self,
    ):
        if (
            self.current_game is None
            or self.collection_names_provider
            is None
            or self.collection_add_handler
            is None
        ):
            return

        names = list(
            self.collection_names_provider()
        )

        if not names:
            QMessageBox.information(
                self,
                "Collections",
                (
                    "Create a collection on the "
                    "Playlists page first."
                ),
            )
            return

        name, accepted = QInputDialog.getItem(
            self,
            "Add to Collection",
            "Collection:",
            names,
            0,
            False,
        )

        if not accepted:
            return

        try:
            self.collection_add_handler(
                name,
                self.current_game,
            )
        except (
            KeyError,
            ValueError,
            OSError,
        ) as exc:
            QMessageBox.warning(
                self,
                "Collections",
                str(exc),
            )
            return

        QMessageBox.information(
            self,
            "Collections",
            (
                f'Added "{self.current_game.name}" '
                f'to "{name}".'
            ),
        )

    def _refresh_launch_button(
        self,
    ):
        process_running = (
            self._process_session_running()
        )

        launch_enabled = (
            self.current_game is not None
            and bool(
                getattr(
                    self.current_game,
                    "rom",
                    "",
                )
            )
            and not self._launch_session_active
            and not process_running
        )

        from services.emulators.models import selected_backend, SNES9X, STANDALONE_NOTICE
        try:
            backend = selected_backend(self.launch_controller.config_loader.load(),
                                       getattr(self.current_game, 'rvdb_platform_id', ''))
            self.launch_button.setText('▶ Launch with Snes9x' if backend == SNES9X else '▶ Launch Game')
            self.launch_button.setToolTip(STANDALONE_NOTICE if backend == SNES9X else 'Launch with RetroArch')
        except (OSError, ValueError):
            self.launch_button.setToolTip('Unable to read emulator backend settings')

        self.launch_button.setEnabled(
            launch_enabled
        )

        self.stop_button.setEnabled(
            self._launch_session_active
            and process_running
        )


    def clear_game(
        self,
    ):
        self.current_game = None
        self._launch_session_active = False

        self.title.setText(
            "Select a game"
        )
        self.metadata.clear()
        self.description.clear()
        self.profile.setText(
            "Launch Profile"
        )

        self._set_launch_status(
            "Ready when you are."
        )

        self.cover.clear()
        self.cover.setText(
            "🎮"
        )

        self._refresh_favorite_button()
        self._refresh_collection_button()
        self._refresh_launch_button()

        self.presentation_studio.set_game(
            None
        )

        self._reset_details_scroll_position()
