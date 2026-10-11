"""Five-column Gallery with cards limited to a buffered viewport."""
from math import ceil
from PyQt6.QtWidgets import QWidget, QGridLayout, QScrollArea, QVBoxLayout
from PyQt6.QtCore import Qt, QEvent
from ui.library.widgets.game_card import GameCard, CARD_SIZES


class GameGrid(QWidget):
    COLUMNS = 5
    BUFFER_ROWS = 2

    def __init__(self, games, details=None, card_size='default'):
        super().__init__()
        self.details = details
        self.card_size = card_size
        self.games = []
        self._range = None
        self._cards = {}
        self.setObjectName('LibraryGrid')
        self.container = QWidget()
        self.container.setObjectName('LibraryGridContainer')
        self.canvas = QWidget(self.container)
        self.layout = QGridLayout(self.canvas)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.scroll = QScrollArea()
        self.scroll.setObjectName('LibraryGridScroll')
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.container)
        main = QVBoxLayout(self)
        main.addWidget(self.scroll)
        self.scroll.verticalScrollBar().valueChanged.connect(self._render)
        self.scroll.viewport().installEventFilter(self)
        self.update_games(games)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.Resize:
            self._render()
        return super().eventFilter(obj, event)

    def _clear(self):
        self._cards = {}
        while self.layout.count():
            widget = self.layout.takeAt(0).widget()
            if widget:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()

    def update_games(self, games):
        self.games = list(games)
        self._range = None
        # One representative determines font/style-aware row extent. Reserve an
        # edition-label row when needed, without instantiating every game card.
        self._clear()
        if self.games:
            sample = next((g for g in self.games if len(getattr(g, 'variants', []) or []) > 1), self.games[0])
            probe = GameCard(sample, card_size=self.card_size)
            self._row_height = probe.sizeHint().height() + max(0, self.layout.verticalSpacing())
            self._cards[id(sample)] = probe
        else:
            self._row_height = 1
        margins = self.layout.contentsMargins()
        height = ceil(len(self.games) / self.COLUMNS) * self._row_height + margins.top() + margins.bottom()
        columns = min(self.COLUMNS, len(self.games))
        width = columns * CARD_SIZES[self.card_size][0] + max(0, columns - 1) * max(0, self.layout.horizontalSpacing()) + margins.left() + margins.right()
        self.container.setMinimumSize(width, height)
        self._render()

    def _render(self, *_):
        if not hasattr(self, '_row_height'):
            return
        top = self.scroll.verticalScrollBar().value() // self._row_height
        first = max(0, top - self.BUFFER_ROWS)
        last = min(ceil(len(self.games) / self.COLUMNS),
                   top + ceil(self.scroll.viewport().height() / self._row_height) + 1 + self.BUFFER_ROWS)
        key = (first, last)
        if key == self._range:
            return
        self._range = key
        previous = self._cards
        self._cards = {}
        while self.layout.count():
            self.layout.takeAt(0)
        for row in range(self.layout.rowCount()):
            self.layout.setRowMinimumHeight(row, 0)
        for row in range(last - first):
            self.layout.setRowMinimumHeight(row, self._row_height - max(0, self.layout.verticalSpacing()))
        for offset, game in enumerate(self.games[first * self.COLUMNS:last * self.COLUMNS]):
            card = previous.pop(id(game), None)
            if card is None:
                card = GameCard(game, card_size=self.card_size)
                if self.details:
                    card.clicked.connect(lambda g=game: self.details.show_game(g))
            elif card.parent() is None and self.details:
                card.clicked.connect(lambda g=game: self.details.show_game(g))
            self._cards[id(game)] = card
            self.layout.addWidget(card, offset // self.COLUMNS, offset % self.COLUMNS)
            card.show()
        for card in previous.values():
            card.hide()
            card.setParent(None)
            card.deleteLater()
        self.canvas.setGeometry(0, first * self._row_height,
                                self.container.minimumWidth(),
                                max(1, (last-first) * self._row_height + self.layout.contentsMargins().top() + self.layout.contentsMargins().bottom()))
        self.layout.activate()

    def set_card_size(self, card_size):
        if self.card_size != card_size:
            height_delta = CARD_SIZES[card_size][2] - CARD_SIZES[self.card_size][2]
            self.card_size = card_size
            for card in self._cards.values():
                card.set_card_size(card_size)
            if self.games:
                self._row_height += height_delta
            margins = self.layout.contentsMargins()
            columns = min(self.COLUMNS, len(self.games))
            self.container.setMinimumSize(columns * CARD_SIZES[card_size][0] + max(0, columns - 1) * max(0, self.layout.horizontalSpacing()) + margins.left() + margins.right(),
                ceil(len(self.games)/5) * self._row_height + margins.top() + margins.bottom())
            self._range = None
            self._render()
