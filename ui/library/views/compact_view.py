from ui.library.views.game_list import GameListView
from PyQt6.QtWidgets import (
    QWidget,
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

        self.setObjectName(
            "LibraryCompactView"
        )

        self.details = details


        self.list = GameListView(detailed=False)

        self.list.setObjectName(
            "LibraryCompactList"
        )


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


        self.list.set_games(self.games)


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

    def restore_selection(self, identity):
        from services.library.identity import game_identity
        previous = self.list.blockSignals(True)
        try:
            row = next((i for i, game in enumerate(self.games)
                        if identity is not None and game_identity(game) == identity), -1)
            self.list.setCurrentRow(row)
        finally:
            self.list.blockSignals(previous)
