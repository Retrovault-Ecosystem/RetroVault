from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config import ConfigLoader
from services.overlays import (
    OverlayService,
)


class OverlaysPage(QWidget):
    """Browse locally installed RetroArch overlays."""

    def __init__(
        self,
        config_loader=None,
        overlay_service=None,
    ):
        super().__init__()

        self.config_loader = (
            config_loader
            or ConfigLoader()
        )

        self.config = (
            self.config_loader.load()
        )

        configured = (
            self.config
            .get("paths", {})
            .get("overlays", {})
            .get("directory", "")
        )

        self.overlay_directory = Path(
            configured
        ).expanduser()

        self.overlay_service = (
            overlay_service
            or OverlayService(
                self.overlay_directory
            )
        )

        self.overlays = []

        self.title_label = QLabel(
            "Overlays"
        )
        self.title_label.setObjectName(
            "PageTitle"
        )

        self.subtitle_label = QLabel(
            "Browse locally installed "
            "RetroArch overlays."
        )
        self.subtitle_label.setObjectName(
            "PageSubtitle"
        )

        self.path_label = QLabel(
            str(
                self.overlay_directory
            )
        )
        self.path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        self.path_label.setWordWrap(
            True
        )

        self.count_label = QLabel()
        self.status_label = QLabel()

        self.refresh_button = QPushButton(
            "Refresh"
        )

        self.overlay_list = QListWidget()

        self.preview = QLabel(
            "No preview"
        )
        self.preview.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.preview.setMinimumSize(
            320,
            240,
        )

        self.name_value = QLabel(
            "Select an overlay"
        )
        self.name_value.setObjectName(
            "SectionTitle"
        )

        self.config_value = QLabel("—")
        self.config_value.setWordWrap(
            True
        )
        self.config_value.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.images_value = QLabel("—")
        self.missing_value = QLabel("—")
        self.readiness_value = QLabel("—")

        self._build_ui()
        self._connect_signals()
        self.refresh_overlays()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            32,
            28,
            32,
            28,
        )
        layout.setSpacing(14)

        layout.addWidget(
            self.title_label
        )
        layout.addWidget(
            self.subtitle_label
        )

        path_row = QHBoxLayout()
        path_row.setSpacing(10)

        path_row.addWidget(
            QLabel("Overlay directory:")
        )
        path_row.addWidget(
            self.path_label,
            1,
        )
        path_row.addWidget(
            self.refresh_button
        )

        layout.addLayout(
            path_row
        )
        layout.addWidget(
            self.count_label
        )

        content = QHBoxLayout()
        content.setSpacing(20)

        self.overlay_list.setMinimumWidth(
            300
        )
        content.addWidget(
            self.overlay_list,
            1,
        )

        details_frame = QFrame()
        details_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        details = QVBoxLayout(
            details_frame
        )
        details.setContentsMargins(
            20,
            20,
            20,
            20,
        )
        details.setSpacing(10)

        details.addWidget(
            self.name_value
        )
        details.addWidget(
            self.preview,
            1,
        )
        details.addWidget(
            QLabel("Configuration")
        )
        details.addWidget(
            self.config_value
        )
        details.addWidget(
            QLabel("Referenced images")
        )
        details.addWidget(
            self.images_value
        )
        details.addWidget(
            QLabel("Missing images")
        )
        details.addWidget(
            self.missing_value
        )
        details.addWidget(
            QLabel("Status")
        )
        details.addWidget(
            self.readiness_value
        )

        content.addWidget(
            details_frame,
            2,
        )

        layout.addLayout(
            content,
            1,
        )
        layout.addWidget(
            self.status_label
        )

        secondary_style = (
            "color: #9aa0a6;"
        )

        self.count_label.setStyleSheet(
            secondary_style
        )
        self.status_label.setStyleSheet(
            secondary_style
        )

    def _connect_signals(self):
        self.refresh_button.clicked.connect(
            self.refresh_overlays
        )
        self.overlay_list.currentRowChanged.connect(
            self.show_overlay
        )

    def set_directory(
        self,
        directory,
    ):
        self.overlay_directory = Path(
            directory
        ).expanduser()

        self.overlay_service = OverlayService(
            self.overlay_directory
        )

        self.path_label.setText(
            str(
                self.overlay_directory
            )
        )

        self.refresh_overlays()

    def refresh_overlays(self):
        self.overlays = list(
            self.overlay_service.scan()
        )

        self.overlay_list.blockSignals(
            True
        )

        try:
            self.overlay_list.clear()

            for overlay in self.overlays:
                self.overlay_list.addItem(
                    overlay.name
                )
        finally:
            self.overlay_list.blockSignals(
                False
            )

        count = len(
            self.overlays
        )

        self.count_label.setText(
            (
                "1 installed overlay"
                if count == 1
                else (
                    f"{count} installed overlays"
                )
            )
        )

        self.clear_details()

        if count:
            self.status_label.setText(
                "Select an overlay to inspect it."
            )
        elif self.overlay_directory.is_dir():
            self.status_label.setText(
                (
                    "No installed overlay descriptors "
                    "were found in this directory."
                )
            )
        else:
            self.status_label.setText(
                (
                    "The configured overlay directory "
                    "does not exist."
                )
            )

    def clear_details(self):
        self.name_value.setText(
            "Select an overlay"
        )
        self.config_value.setText("—")
        self.images_value.setText("—")
        self.missing_value.setText("—")
        self.readiness_value.setText("—")
        self.preview.clear()
        self.preview.setText(
            "No preview"
        )

    def show_overlay(
        self,
        row,
    ):
        if (
            row < 0
            or row >= len(
                self.overlays
            )
        ):
            self.clear_details()
            return

        overlay = self.overlays[row]

        self.name_value.setText(
            overlay.name
        )
        self.config_value.setText(
            str(
                overlay.relative_config
            )
        )
        self.images_value.setText(
            str(
                overlay.image_count
            )
        )
        self.missing_value.setText(
            str(
                len(
                    overlay.missing_images
                )
            )
        )
        self.readiness_value.setText(
            (
                "Ready"
                if overlay.ready
                else "Missing assets"
            )
        )

        self.preview.clear()
        self.preview.setText(
            "No preview"
        )

        for image in overlay.image_paths:
            if not image.is_file():
                continue

            pixmap = QPixmap(
                str(image)
            )

            if pixmap.isNull():
                continue

            self.preview.setPixmap(
                pixmap.scaled(
                    self.preview.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
            break
