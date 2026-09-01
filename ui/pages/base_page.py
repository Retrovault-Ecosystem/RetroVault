from PyQt6.QtWidgets import (
    QFrame,
    QLabel,
    QVBoxLayout,
    QWidget,
)


class BasePage(QWidget):
    """Consistent shell for RetroVault pages still under development."""

    def __init__(
        self,
        title,
        subtitle=None,
    ):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            32,
            28,
            32,
            28,
        )
        layout.setSpacing(
            14
        )

        self.title_label = QLabel(
            title
        )
        self.title_label.setObjectName(
            "PageTitle"
        )

        self.subtitle_label = QLabel(
            subtitle
            or (
                "This RetroVault area is "
                "not implemented yet."
            )
        )
        self.subtitle_label.setObjectName(
            "PageSubtitle"
        )
        self.subtitle_label.setWordWrap(
            True
        )

        self.content_frame = QFrame()
        self.content_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        frame_layout = QVBoxLayout(
            self.content_frame
        )
        frame_layout.setContentsMargins(
            22,
            22,
            22,
            22,
        )

        message = QLabel(
            "This section will become available "
            "as its application and RVDB "
            "contracts are implemented."
        )
        message.setWordWrap(
            True
        )

        message.setStyleSheet(
            """
            color: #9aa0a6;
            """
        )

        frame_layout.addWidget(
            message
        )
        frame_layout.addStretch(
            1
        )

        layout.addWidget(
            self.title_label
        )
        layout.addWidget(
            self.subtitle_label
        )
        layout.addSpacing(
            4
        )
        layout.addWidget(
            self.content_frame,
            1,
        )
