from PyQt6.QtWidgets import (
    QWidget,
    QGridLayout,
    QScrollArea,
    QVBoxLayout,
)

from PyQt6.QtCore import Qt

from ui.library.widgets.game_card import GameCard



class GameGrid(QWidget):


    def __init__(self, games, details=None, card_size="default"):

        super().__init__()


        self.details = details
        self.card_size = card_size

        self.setObjectName(
            "LibraryGrid"
        )


        self.container = QWidget()

        self.container.setObjectName(
            "LibraryGridContainer"
        )


        self.layout = QGridLayout()

        self.layout.setAlignment(
            Qt.AlignmentFlag.AlignTop
            | Qt.AlignmentFlag.AlignLeft
        )


        self.container.setLayout(
            self.layout
        )


        scroll = self.scroll = QScrollArea()

        scroll.setObjectName(
            "LibraryGridScroll"
        )


        scroll.setWidgetResizable(
            True
        )


        scroll.setWidget(
            self.container
        )


        main = QVBoxLayout()


        main.addWidget(
            scroll
        )


        self.setLayout(
            main
        )


        self.update_games(
            games
        )



    def update_games(self, games):


        while self.layout.count():

            item = self.layout.takeAt(0)

            widget = item.widget()

            if widget:

                widget.deleteLater()



        columns = 5


        row = 0

        col = 0



        for game in games:


            card = GameCard(
                game, card_size=self.card_size
            )


            if self.details:

                card.clicked.connect(

                    lambda checked=False, g=game:
                    self.details.show_game(g)

                )


            self.layout.addWidget(

                card,

                row,

                col

            )


            col += 1


            if col >= columns:

                col = 0

                row += 1

    def set_card_size(self, card_size):
        if self.card_size == card_size:
            return
        self.card_size = card_size
        for index in range(self.layout.count()):
            self.layout.itemAt(index).widget().set_card_size(card_size)
        self.layout.activate()
