from PyQt6.QtWidgets import (
    QButtonGroup,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class Sidebar(QWidget):
    """Persistent RetroVault application navigation."""

    PRIMARY_PAGES = [
        "Library",
        "Systems",
        "Playlists",
        "Overlays",
        "Shaders",
        "RetroArch",
    ]

    FOOTER_PAGES = [
        "Settings",
    ]

    def __init__(
        self,
        callback,
    ):
        super().__init__()

        self.callback = callback
        self.buttons = {}

        self.setFixedWidth(
            190
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            12,
            18,
            12,
            16,
        )
        layout.setSpacing(5)

        brand = QLabel(
            "RetroVault"
        )
        brand.setStyleSheet(
            """
            font-size: 20px;
            font-weight: 700;
            padding-left: 8px;
            """
        )

        subtitle = QLabel(
            "Retro gaming workspace"
        )
        subtitle.setStyleSheet(
            """
            color: #8e8e8e;
            font-size: 11px;
            padding-left: 8px;
            padding-bottom: 10px;
            """
        )

        layout.addWidget(
            brand
        )
        layout.addWidget(
            subtitle
        )

        self.button_group = QButtonGroup(
            self
        )
        self.button_group.setExclusive(
            True
        )

        for page in self.PRIMARY_PAGES:
            layout.addWidget(
                self._make_button(
                    page
                )
            )

        layout.addStretch(1)

        for page in self.FOOTER_PAGES:
            layout.addWidget(
                self._make_button(
                    page
                )
            )

        self.set_active_page(
            "Library"
        )

    def _make_button(
        self,
        page: str,
    ) -> QPushButton:
        button = QPushButton(
            page
        )

        button.setObjectName(
            "NavButton"
        )
        button.setCheckable(
            True
        )

        button.clicked.connect(
            lambda checked=False, p=page:
            self._page_clicked(
                p
            )
        )

        self.button_group.addButton(
            button
        )
        self.buttons[
            page
        ] = button

        return button

    def _page_clicked(
        self,
        page: str,
    ) -> None:
        self.set_active_page(
            page
        )

        self.callback(
            page
        )

    def set_active_page(
        self,
        page: str,
    ) -> None:
        button = self.buttons.get(
            page
        )

        if button is None:
            return

        button.setChecked(
            True
        )
