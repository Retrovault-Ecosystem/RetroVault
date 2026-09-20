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

        self.setObjectName(
            "LibraryGameCard"
        )


        layout = QVBoxLayout()


        self.cover = QLabel()

        self.cover.setObjectName(
            "LibraryGameCover"
        )


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

        self.title.setObjectName(
            "LibraryGameTitle"
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

        self.info.setObjectName(
            "LibraryGameInfo"
        )


        variants = list(
            getattr(
                self.game,
                "variants",
                [],
            )
            or []
        )

        self.edition_count = QLabel()

        self.edition_count.setObjectName(
            "LibraryGameEditionCount"
        )

        self.edition_count.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        if len(variants) > 1:
            self.edition_count.setText(
                f"{len(variants)} Editions"
            )
            self.edition_count.setVisible(
                True
            )
        else:
            self.edition_count.setText("")
            self.edition_count.setVisible(
                False
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

        layout.addWidget(
            self.edition_count
        )


        self.setLayout(
            layout
        )



        self.setFixedWidth(
            190
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

                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation,

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
