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
            "🎮 Gallery"
        )


        self.details = QPushButton(
            "📋 Details"
        )


        self.compact = QPushButton(
            "🧱 Compact"
        )


        self.compact.setEnabled(
            True
        )


        self.compact.setToolTip(
            "Show the compact Library view."
        )



        self.gallery.clicked.connect(
            self.gallery_selected.emit
        )


        self.details.clicked.connect(
            self.details_selected.emit
        )


        self.compact.clicked.connect(
            self.compact_selected.emit
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
