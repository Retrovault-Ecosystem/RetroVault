from PyQt6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
)

from PyQt6.QtCore import pyqtSignal


class ViewSelector(QWidget):


    gallery_selected = pyqtSignal()

    details_selected = pyqtSignal()

    compact_selected = pyqtSignal()


    def __init__(self):

        super().__init__()


        layout = QHBoxLayout()


        self.gallery = QPushButton(
            "● 🎮 Gallery"
        )

        self.details = QPushButton(
            "○ 📋 Details"
        )

        self.compact = QPushButton(
            "○ 🧱 Compact"
        )


        for button in (
            self.gallery,
            self.details,
            self.compact,
        ):

            button.setCheckable(
                True
            )

            button.setAutoExclusive(
                True
            )


        self.gallery.setChecked(
            True
        )


        self.compact.setEnabled(
            True
        )

        self.compact.setToolTip(
            "Show the compact Library view."
        )


        self.gallery.clicked.connect(
            self._select_gallery
        )

        self.details.clicked.connect(
            self._select_details
        )

        self.compact.clicked.connect(
            self._select_compact
        )


        layout.addWidget(
            self.gallery
        )

        layout.addWidget(
            self.details
        )

        layout.addWidget(
            self.compact
        )


        self.setLayout(
            layout
        )


    def _refresh_labels(self):

        self.gallery.setText(
            (
                "● 🎮 Gallery"
                if self.gallery.isChecked()
                else "○ 🎮 Gallery"
            )
        )

        self.details.setText(
            (
                "● 📋 Details"
                if self.details.isChecked()
                else "○ 📋 Details"
            )
        )

        self.compact.setText(
            (
                "● 🧱 Compact"
                if self.compact.isChecked()
                else "○ 🧱 Compact"
            )
        )


    def _select_gallery(self):

        self.gallery.setChecked(
            True
        )

        self._refresh_labels()

        self.gallery_selected.emit()


    def _select_details(self):

        self.details.setChecked(
            True
        )

        self._refresh_labels()

        self.details_selected.emit()


    def _select_compact(self):

        self.compact.setChecked(
            True
        )

        self._refresh_labels()

        self.compact_selected.emit()
