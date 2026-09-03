from PyQt6.QtWidgets import (
    QWidget,
    QListWidget,
    QVBoxLayout,
)


class CompactView(QWidget):


    def __init__(
        self,
        games,
        details=None,
    ):

        super().__init__()


        self.games = []

        self.details = details


        self.list = QListWidget()


        self.list.currentRowChanged.connect(
            self._select_row
        )


        layout = QVBoxLayout()


        layout.addWidget(
            self.list
        )


        self.setLayout(
            layout
        )


        self.update_games(
            games
        )


    def update_games(
        self,
        games,
    ):

        self.games = list(
            games
        )


        self.list.clear()


        for game in self.games:

            parts = [
                game.name,
                game.platform,
            ]


            if game.year:

                parts.append(
                    str(
                        game.year
                    )
                )


            self.list.addItem(
                "  •  ".join(
                    parts
                )
            )


    def _select_row(
        self,
        row,
    ):

        if self.details is None:
            return


        if row < 0:
            return


        if row >= len(
            self.games
        ):
            return


        self.details.show_game(
            self.games[row]
        )
