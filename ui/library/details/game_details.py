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

from models.launch_profile import LaunchProfile

from config import ConfigLoader

from services.retroarch import (
    CoreResolver,
    LaunchDiagnostics,
    LaunchValidator,
)

from services.retroarch.launcher import RetroArchLauncher

from services.rvdb import RVDBError



class GameDetails(QWidget):


    def __init__(
        self,
        rvdb_service=None,
        favorite_handler=None,
        played_handler=None,
        collection_names_provider=None,
        collection_add_handler=None,
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


        self.config = ConfigLoader().load()


        self.core_resolver = CoreResolver(
            self.config
        )


        self.launcher = RetroArchLauncher()


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



        self.description.setText(

            f"""
{game.name}

RetroVault Profile

Future:

• ROM hacks
• Overlays
• Shaders
• Saves
• Config profiles
"""

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


    def launch_game(self):


        if not self.current_game:

            return



        core_path = self.core_resolver.find(

            self.current_game.core

        )



        if not core_path:


            print(

                [
                    "Required core is missing."
                ]

            )

            return



        profile = LaunchProfile(

            game=self.current_game.name,

            rom=self.current_game.rom,

            core=core_path

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

            return



        launch_result = self.launcher.launch(

            profile

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
