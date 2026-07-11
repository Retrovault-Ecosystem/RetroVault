from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel


class BasePage(QWidget):

    def __init__(self, title):

        super().__init__()

        layout = QVBoxLayout()

        label = QLabel(title)

        label.setStyleSheet(
            """
            font-size: 24px;
            font-weight: bold;
            """
        )

        layout.addWidget(label)

        self.setLayout(layout)
