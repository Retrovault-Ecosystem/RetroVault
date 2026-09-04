from pathlib import Path

from PyQt6.QtCore import Qt
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
from services.shaders import (
    ShaderService,
)


class ShadersPage(QWidget):
    """Browse locally installed RetroArch shaders."""

    def __init__(
        self,
        config_loader=None,
        shader_service=None,
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
            .get("shaders", {})
            .get("directory", "")
        )

        self.shader_directory = Path(
            configured
        ).expanduser()

        self.shader_service = (
            shader_service
            or ShaderService(
                self.shader_directory
            )
        )

        self.shaders = []

        self.title_label = QLabel(
            "Shaders"
        )
        self.title_label.setObjectName(
            "PageTitle"
        )

        self.subtitle_label = QLabel(
            "Browse locally installed "
            "RetroArch shader presets."
        )
        self.subtitle_label.setObjectName(
            "PageSubtitle"
        )

        self.path_label = QLabel(
            str(
                self.shader_directory
            )
        )
        self.path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag
            .TextSelectableByMouse
        )
        self.path_label.setWordWrap(
            True
        )

        self.count_label = QLabel()
        self.status_label = QLabel()

        self.refresh_button = QPushButton(
            "Refresh"
        )

        self.shader_list = QListWidget()

        self.name_value = QLabel(
            "Select a shader preset"
        )
        self.name_value.setObjectName(
            "SectionTitle"
        )

        self.type_value = QLabel("—")

        self.preset_value = QLabel("—")
        self.preset_value.setWordWrap(
            True
        )
        self.preset_value.setTextInteractionFlags(
            Qt.TextInteractionFlag
            .TextSelectableByMouse
        )

        self.passes_value = QLabel("—")
        self.missing_value = QLabel("—")
        self.readiness_value = QLabel("—")

        self._build_ui()
        self._connect_signals()
        self.refresh_shaders()

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
            QLabel("Shader directory:")
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

        self.shader_list.setMinimumWidth(
            360
        )
        content.addWidget(
            self.shader_list,
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
            QLabel("Preset type")
        )
        details.addWidget(
            self.type_value
        )
        details.addWidget(
            QLabel("Preset path")
        )
        details.addWidget(
            self.preset_value
        )
        details.addWidget(
            QLabel("Referenced shader passes")
        )
        details.addWidget(
            self.passes_value
        )
        details.addWidget(
            QLabel("Missing dependencies")
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
        details.addStretch(1)

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
            self.refresh_shaders
        )
        self.shader_list.currentRowChanged.connect(
            self.show_shader
        )

    def set_directory(
        self,
        directory,
    ):
        self.shader_directory = Path(
            directory
        ).expanduser()

        self.shader_service = ShaderService(
            self.shader_directory
        )

        self.path_label.setText(
            str(
                self.shader_directory
            )
        )

        self.refresh_shaders()

    def refresh_shaders(self):
        self.shaders = list(
            self.shader_service.scan()
        )

        self.shader_list.blockSignals(
            True
        )

        try:
            self.shader_list.clear()

            for shader in self.shaders:
                self.shader_list.addItem(
                    shader.name
                )
        finally:
            self.shader_list.blockSignals(
                False
            )

        count = len(
            self.shaders
        )

        self.count_label.setText(
            (
                "1 installed shader preset"
                if count == 1
                else (
                    f"{count} installed "
                    "shader presets"
                )
            )
        )

        self.clear_details()

        if count:
            self.status_label.setText(
                "Select a shader preset "
                "to inspect it."
            )
        elif self.shader_directory.is_dir():
            self.status_label.setText(
                (
                    "No installed shader presets "
                    "were found in this directory."
                )
            )
        else:
            self.status_label.setText(
                (
                    "The configured shader directory "
                    "does not exist."
                )
            )

    def clear_details(self):
        self.name_value.setText(
            "Select a shader preset"
        )
        self.type_value.setText("—")
        self.preset_value.setText("—")
        self.passes_value.setText("—")
        self.missing_value.setText("—")
        self.readiness_value.setText("—")

    def show_shader(
        self,
        row,
    ):
        if (
            row < 0
            or row >= len(
                self.shaders
            )
        ):
            self.clear_details()
            return

        shader = self.shaders[row]

        self.name_value.setText(
            shader.name
        )
        self.type_value.setText(
            shader.preset_type
        )
        self.preset_value.setText(
            str(
                shader.relative_preset
            )
        )
        self.passes_value.setText(
            str(
                shader.shader_count
            )
        )
        self.missing_value.setText(
            str(
                len(
                    shader.missing_shaders
                )
            )
        )
        self.readiness_value.setText(
            (
                "Ready"
                if shader.ready
                else "Missing dependencies"
            )
        )
