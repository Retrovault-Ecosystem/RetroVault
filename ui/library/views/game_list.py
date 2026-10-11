"""On-demand text rows shared by the two Library list presentations."""
from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSignal
from PyQt6.QtWidgets import QListView


class GameListModel(QAbstractListModel):
    def __init__(self, detailed, parent=None):
        super().__init__(parent)
        self.games = []
        self.detailed = detailed

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.games)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole or not index.isValid() or not 0 <= index.row() < len(self.games):
            return None
        game = self.games[index.row()]
        if self.detailed:
            return f'{game.name}\nSystem: {game.platform}\nYear: {game.year}\nCore: {game.core}'
        return '  •  '.join([game.name, game.platform] + ([str(game.year)] if game.year else []))

    def replace(self, games):
        self.beginResetModel()
        self.games = games
        self.endResetModel()


class GameListView(QListView):
    currentRowChanged = pyqtSignal(int)

    def __init__(self, detailed=False):
        super().__init__()
        self.setModel(GameListModel(detailed, self))
        self.setUniformItemSizes(True)
        self.selectionModel().currentChanged.connect(lambda current, previous: self.currentRowChanged.emit(current.row()))

    def set_games(self, games):
        self.model().replace(games)

    def currentRow(self):
        return self.currentIndex().row()

    def setCurrentRow(self, row):
        self.setCurrentIndex(self.model().index(row, 0))
