from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QPushButton,
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



class GameDetails(QWidget):


    def __init__(self):

        super().__init__()


        self.current_game = None


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



        self.launch_button = QPushButton(
            "▶ Launch Game"
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


        self.title.setText(
            game.name
        )


        self.metadata.setText(

            f"""
System:
{game.platform}

Core:
{game.core}
"""

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



        self.launcher.launch(

            profile

        )
