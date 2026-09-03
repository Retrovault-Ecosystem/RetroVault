from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
)

from PyQt6.QtCore import pyqtSignal

from ui.library.widgets.view_selector import ViewSelector



class LibraryToolbar(QWidget):


    search_changed = pyqtSignal(str)

    system_changed = pyqtSignal(str)

    sort_changed = pyqtSignal(str)

    random_requested = pyqtSignal()

    favorites_changed = pyqtSignal(bool)



    def __init__(self):

        super().__init__()


        layout = QHBoxLayout()


        self.search = QLineEdit()

        self.search.setPlaceholderText(
            "Search games..."
        )


        self.search.textChanged.connect(
            self.search_changed.emit
        )


        self.system_filter = QComboBox()

        self.system_filter.addItems(
            [
                "All Systems",
                "NES",
                "SNES",
                "Genesis",
                "Arcade",
            ]
        )


        self.system_filter.currentTextChanged.connect(
            self.system_changed.emit
        )


        self.sort = QComboBox()

        self.sort.addItems(
            [
                "Name",
                "Year",
            ]
        )


        self.sort.currentTextChanged.connect(
            self.sort_changed.emit
        )


        self.view_selector = ViewSelector()


        self.favorites_only = QPushButton(
            "☆ Favorites"
        )

        self.favorites_only.setCheckable(
            True
        )

        self.favorites_only.toggled.connect(
            self.favorites_changed.emit
        )


        self.random_button = QPushButton(
            "🎲 Random Game"
        )


        self.random_button.clicked.connect(
            self.random_requested.emit
        )


        layout.addWidget(
            self.search
        )


        layout.addWidget(
            self.system_filter
        )


        layout.addWidget(
            self.sort
        )


        layout.addWidget(
            self.favorites_only
        )


        layout.addWidget(
            self.view_selector
        )


        layout.addWidget(
            self.random_button
        )


        self.setLayout(
            layout
        )
