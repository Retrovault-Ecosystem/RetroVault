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



CARD_SIZES = {"small": (170, 140, 175), "default": (190, 160, 200), "large": (230, 200, 250)}


class GameCard(QWidget):


    clicked = pyqtSignal()



    def __init__(self, game, card_size="default"):

        super().__init__()


        self.game = game
        self.card_size = card_size

        self.setObjectName(
            "LibraryGameCard"
        )


        layout = QVBoxLayout()


        self.cover = QLabel()

        self.cover.setObjectName(
            "LibraryGameCover"
        )


        self.cover.setFixedSize(*CARD_SIZES[card_size][1:])


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


        self.title.setTextFormat(Qt.TextFormat.PlainText)
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


        self.info.setTextFormat(Qt.TextFormat.PlainText)
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



        self.setFixedWidth(CARD_SIZES[card_size][0])
        self._fit_candidate_labels()






    def set_card_size(self, card_size):
        width, cover_width, cover_height = CARD_SIZES[card_size]
        self.card_size = card_size
        self.setFixedWidth(width)
        self.cover.setFixedSize(cover_width, cover_height)
        self.load_cover()
        self._fit_candidate_labels()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._fit_candidate_labels()

    def _fit_candidate_labels(self):
        if not hasattr(self, "title"):
            return
        # Keep approved Default text rendering unchanged. Candidate sizes use
        # bounded labels and tooltips rather than clipping the middle of a title.
        if self.card_size == "default":
            self.title.setText(self.game.name)
            self.title.setToolTip("")
            return
        margins = self.layout().contentsMargins()
        available = max(1, self.width() - margins.left() - margins.right())
        self.title.setText(self.title.fontMetrics().elidedText(
            self.game.name, Qt.TextElideMode.ElideRight, available))
        self.title.setToolTip(self.game.name)

    def load_cover(self):
        self.cover.clear()


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

                        self.cover.width(),

                        self.cover.height(),

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
