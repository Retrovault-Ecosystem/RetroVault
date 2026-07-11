from PyQt6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
)

from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import (
    Qt,
    pyqtSignal,
)



class GameCard(QWidget):


    clicked = pyqtSignal()



    def __init__(self, game):

        super().__init__()


        self.game = game


        layout = QVBoxLayout()


        self.cover = QLabel()


        self.cover.setFixedSize(
            160,
            200
        )


        self.cover.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )


        self.load_cover()



        self.title = QLabel(
            game.name
        )


        self.title.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )



        favorite = ""

        if getattr(
            game,
            "favorite",
            False
        ):

            favorite = " ⭐"



        self.info = QLabel(

            f"{game.platform} • "
            f"{game.year or ''}"
            f"{favorite}"

        )


        self.info.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )



        layout.addWidget(
            self.cover
        )


        layout.addWidget(
            self.title
        )


        layout.addWidget(
            self.info
        )


        self.setLayout(
            layout
        )



        self.setFixedWidth(
            190
        )



        self.setStyleSheet(
    """
    QWidget {

        background-color:#202020;

        border-radius:12px;

        padding:8px;

    }


    QWidget:hover {

        background-color:#3a3a3a;

        border:2px solid #e91e63;

    }


    QLabel {

        color:white;

    }

    """
)



    def load_cover(self):


        if getattr(
            self.game,
            "artwork",
            None
        ):


            pixmap = QPixmap(
                self.game.artwork
            )


            if not pixmap.isNull():


                self.cover.setPixmap(

                    pixmap.scaled(

                        160,

                        200,

                        Qt.AspectRatioMode.KeepAspectRatio

                    )

                )


                return



        self.cover.setText(
            "🎮"
        )



    def mousePressEvent(self, event):

        self.clicked.emit()


        super().mousePressEvent(
            event
        )
