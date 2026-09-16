from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
    QInputDialog,
    QMessageBox,
    QVBoxLayout,
    QHBoxLayout,
    QTextEdit,
)

from PyQt6.QtGui import QPixmap

from PyQt6.QtCore import Qt

from pathlib import Path

from models.launch_profile import LaunchProfile

from config import ConfigLoader

from services.retroarch import (
    CoreResolver,
    LaunchDiagnostics,
    LaunchValidator,
)

from services.retroarch.launcher import RetroArchLauncher
from services.retroarch.archive_runtime import ArchiveRuntime
from services.retroarch.archive_variant import ArchiveVariantFormatter

from services.rvdb import RVDBError



class GameDetails(QWidget):


    def __init__(
        self,
        rvdb_service=None,
        favorite_handler=None,
        played_handler=None,
        collection_names_provider=None,
        collection_add_handler=None,
        presentation_resolver_provider=None,
        launcher=None,
        process_lifecycle=None,
        archive_runtime=None,
    ):

        super().__init__()


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


        self.config = ConfigLoader().load()


        self.core_resolver = CoreResolver(
            self.config
        )


        self.launcher = (
            launcher
            if launcher is not None
            else RetroArchLauncher()
        )

        self.process_lifecycle = (
            process_lifecycle
        )

        self.archive_runtime = (
            archive_runtime
            if archive_runtime is not None
            else ArchiveRuntime()
        )


        self.diagnostics = LaunchDiagnostics()



        main = QVBoxLayout()


        top = QHBoxLayout()



        self.cover = QLabel(
            "🎮"
        )


        self.cover.setFixedSize(
            250,
            320
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


        self.metadata = QLabel()


        self.description = QTextEdit()


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


        main.addLayout(
            top
        )



        self.profile = QLabel(
            "Launch Profile"
        )


        main.addWidget(
            self.profile
        )



        self.favorite_button = QPushButton(
            "☆ Add to Favorites"
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

        self.launch_button.setEnabled(
            False
        )


        self.launch_button.clicked.connect(
            self.launch_game
        )


        main.addWidget(
            self.launch_button
        )


        self.setLayout(
            main
        )



    def show_game(
        self,
        game
    ):


        self.current_game = game

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

        self.description.setText(
            "\n".join(
                profile_lines
            )
        )



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

            print(
                "Unable to update Favorite: "
                f"{exc}"
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


    def launch_game(self):


        if not self.current_game:

            return

        archive_member = ""

        if (
            Path(
                self.current_game.rom
            ).suffix.lower()
            == ".7z"
        ):
            try:
                archive_member = (
                    self._select_archive_member(
                        self.current_game.rom
                    )
                )
            except (
                OSError,
                ValueError,
            ) as exc:
                print(
                    "Unable to inspect archive variants: "
                    f"{exc}"
                )
                return

            if archive_member is None:
                return

        if self.process_lifecycle is not None:
            self.process_lifecycle.launch_requested(
                getattr(
                    self.current_game,
                    "rvdb_platform_id",
                    "",
                )
            )



        core_path = self.core_resolver.find(

            self.current_game.core

        )



        if not core_path:


            print(

                [
                    "Required core is missing."
                ]

            )

            if self.process_lifecycle is not None:
                self.process_lifecycle.launch_failed()

            return



        shader = ""
        overlay = ""

        if (
            self.presentation_resolver_provider
            is not None
        ):
            try:
                resolver = (
                    self.presentation_resolver_provider()
                )
                presentation = resolver.resolve(
                    self.current_game
                )
                shader = presentation.shader
                overlay = presentation.overlay
            except (
                OSError,
                ValueError,
            ) as exc:
                print(
                    "Unable to resolve presentation: "
                    f"{exc}"
                )

        profile = LaunchProfile(

            game=self.current_game.name,

            rom=self.current_game.rom,

            core=core_path,

            overlay=overlay,

            shader=shader,

            archive_member=archive_member

        )



        validator = LaunchValidator(

            self.config["retroarch"]["executable"],

            profile.core

        )



        result = validator.validate(

            profile.rom

        )



        print(

            self.diagnostics.explain(
                result
            )

        )



        if not result["ready"]:

            if self.process_lifecycle is not None:
                self.process_lifecycle.launch_failed()

            return



        launch_result = self.launcher.launch(

            profile

        )


        if self.process_lifecycle is not None:
            self.process_lifecycle.launch_result(
                launch_result
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
                    self.current_game
                )

            except (
                OSError,
                ValueError,
            ) as exc:

                print(
                    "Unable to record Recently Played: "
                    f"{exc}"
                )

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
        enabled = (
            self.current_game is not None
            and bool(
                getattr(
                    self.current_game,
                    "rom",
                    "",
                )
            )
        )

        self.launch_button.setEnabled(
            enabled
        )


    def clear_game(
        self,
    ):
        self.current_game = None

        self.title.setText(
            "Select a game"
        )
        self.metadata.clear()
        self.description.clear()
        self.profile.setText(
            "Launch Profile"
        )

        self.cover.clear()
        self.cover.setText(
            "🎮"
        )

        self._refresh_favorite_button()
        self._refresh_collection_button()
        self._refresh_launch_button()
