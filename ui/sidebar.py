from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QPushButton,
)


class Sidebar(QWidget):


    def __init__(self, callback):

        super().__init__()


        layout = QVBoxLayout()


        pages = [
            "Library",
            "Systems",
            "Playlists",
            "Overlays",
            "Shaders",
            "RetroArch",
            "Settings",
        ]


        for page in pages:

            button = QPushButton(
                page
            )

            button.clicked.connect(
                lambda checked=False, p=page:
                callback(p)
            )

            layout.addWidget(
                button
            )


        self.setLayout(
            layout
        )
