from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLineEdit,
    QPushButton,
    QComboBox,
    QLabel,
    QSizePolicy,
)

from PyQt6.QtCore import pyqtSignal

from ui.library.widgets.view_selector import ViewSelector


class LibraryToolbar(QWidget):

    search_changed = pyqtSignal(str)
    system_changed = pyqtSignal(str)
    sort_changed = pyqtSignal(str)
    random_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    bulk_import_requested = pyqtSignal()
    favorites_changed = pyqtSignal(bool)
    recent_changed = pyqtSignal(bool)

    def __init__(self):

        super().__init__()

        self.setObjectName(
            "LibraryToolbar"
        )

        # The toolbar is deliberately split by responsibility.
        #
        # Discovery row:
        #   Search | System | Sort | Favorites | Recent
        #
        # Workspace row:
        #   Gallery | Details | Compact
        #   Random | Refresh | Bulk Import | status
        #
        # This is not a fallback caused by clipping. It is the
        # desktop Library composition. Neither row depends on the
        # full application width because the sidebar and details
        # pane reduce the Library client's usable width.
        layout = QVBoxLayout()

        self.primary_row = QHBoxLayout()
        self.secondary_row = QHBoxLayout()

        layout.setContentsMargins(
            10,
            8,
            10,
            8,
        )

        layout.setSpacing(
            6
        )

        self.primary_row.setSpacing(
            6
        )

        self.secondary_row.setSpacing(
            6
        )

        self.search = QLineEdit()

        self.search.setPlaceholderText(
            "Search games..."
        )

        self.search.setObjectName(
            "LibrarySearch"
        )

        # The previous 300px hard minimum propagated excessive
        # minimum width through LibraryPage. Search remains
        # comfortably sized at normal widths but is allowed to
        # contract when the real Library client is narrower.
        self.search.setMinimumWidth(
            180
        )

        self.search.setMaximumWidth(
            300
        )

        self.search.setMinimumHeight(
            38
        )

        self.search.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.Fixed,
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

        self.system_filter.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
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

        self.sort.setSizeAdjustPolicy(
            QComboBox.SizeAdjustPolicy.AdjustToContents
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
            self._favorites_toggled
        )

        self.recent_only = QPushButton(
            "○ Recently Played"
        )

        self.recent_only.setCheckable(
            True
        )

        self.recent_only.toggled.connect(
            self._recent_toggled
        )

        self.random_button = QPushButton(
            "🎲 Random Game"
        )

        self.random_button.clicked.connect(
            self.random_requested.emit
        )

        self.refresh_button = QPushButton(
            "Refresh Library"
        )

        self.refresh_button.clicked.connect(
            self.refresh_requested.emit
        )

        self.bulk_import_button = QPushButton(
            "Bulk Import"
        )

        self.bulk_import_button.clicked.connect(
            self.bulk_import_requested.emit
        )

        self.refresh_status = QLabel()

        self.refresh_status.setObjectName(
            "libraryRefreshStatus"
        )

        self.refresh_status.setMinimumWidth(
            0
        )

        self.refresh_status.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred,
        )

        # Discovery / filtering.
        self.primary_row.addWidget(
            self.search
        )

        self.primary_row.addSpacing(
            12
        )

        self.primary_row.addWidget(
            self.system_filter
        )

        self.primary_row.addWidget(
            self.sort
        )

        self.primary_row.addWidget(
            self.favorites_only
        )

        self.primary_row.addWidget(
            self.recent_only
        )

        self.primary_row.addStretch(
            1
        )

        # View selection and actions remain one continuous group.
        self.secondary_row.addWidget(
            self.view_selector
        )

        self.secondary_row.addSpacing(
            8
        )

        self.secondary_row.addWidget(
            self.random_button
        )

        self.secondary_row.addWidget(
            self.refresh_button
        )

        self.secondary_row.addWidget(
            self.bulk_import_button
        )

        self.secondary_row.addWidget(
            self.refresh_status,
            1,
        )

        layout.addLayout(
            self.primary_row
        )

        layout.addLayout(
            self.secondary_row
        )

        self.setLayout(
            layout
        )

    def _favorites_toggled(
        self,
        checked,
    ):

        self.favorites_only.setText(
            (
                "★ Favorites"
                if checked
                else "☆ Favorites"
            )
        )

        self.favorites_changed.emit(
            checked
        )

    def _recent_toggled(
        self,
        checked,
    ):

        self.recent_only.setText(
            (
                "● Recently Played"
                if checked
                else "○ Recently Played"
            )
        )

        self.recent_changed.emit(
            checked
        )
