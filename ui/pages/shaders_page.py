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
from services.library.state import game_identity
from services.shaders import (
    ShaderService,
)


class ShadersPage(QWidget):
    """Browse locally installed RetroArch shaders."""

    def __init__(
        self,
        config_loader=None,
        shader_service=None,
        presentation_store=None,
        current_game_provider=None,
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

        self.presentation_store = (
            presentation_store
        )

        self.current_game_provider = (
            current_game_provider
        )

        self.title_label = QLabel(
            "Shaders"
        )
        self.title_label.setObjectName(
            "ShadersTitle"
        )

        self.subtitle_label = QLabel(
            "Browse locally installed "
            "RetroArch shader presets."
        )
        self.subtitle_label.setObjectName(
            "ShadersSubtitle"
        )

        self.path_label = QLabel(
            str(
                self.shader_directory
            )
        )
        self.path_label.setObjectName(
            "ShadersDirectoryValue"
        )
        self.path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag
            .TextSelectableByMouse
        )
        self.path_label.setWordWrap(
            True
        )

        self.count_label = QLabel()
        self.count_label.setObjectName(
            "ShadersCount"
        )

        self.status_label = QLabel()
        self.status_label.setObjectName(
            "ShadersStatus"
        )

        self.refresh_button = QPushButton(
            "Refresh"
        )
        self.refresh_button.setObjectName(
            "ShadersSecondaryAction"
        )

        self.default_button = QPushButton(
            "Set as Default"
        )
        self.default_button.setObjectName(
            "ShadersAssignmentAction"
        )
        self.system_button = QPushButton(
            "Set for System"
        )
        self.system_button.setObjectName(
            "ShadersAssignmentAction"
        )
        self.game_button = QPushButton(
            "Set for Game"
        )
        self.game_button.setObjectName(
            "ShadersAssignmentAction"
        )

        self.default_button.setEnabled(
            False
        )
        self.system_button.setEnabled(
            False
        )
        self.game_button.setEnabled(
            False
        )

        self.shader_list = QListWidget()
        self.shader_list.setObjectName(
            "ShadersPresetList"
        )

        self.name_value = QLabel(
            "Select a shader preset"
        )
        self.name_value.setObjectName(
            "ShadersPresetName"
        )

        self.type_value = QLabel("—")
        self.type_value.setObjectName(
            "ShadersFieldValue"
        )

        self.preset_value = QLabel("—")
        self.preset_value.setObjectName(
            "ShadersPresetPath"
        )
        self.preset_value.setWordWrap(
            True
        )
        self.preset_value.setTextInteractionFlags(
            Qt.TextInteractionFlag
            .TextSelectableByMouse
        )

        self.passes_value = QLabel("—")
        self.passes_value.setObjectName(
            "ShadersFieldValue"
        )

        self.missing_value = QLabel("—")
        self.missing_value.setObjectName(
            "ShadersFieldValue"
        )

        self.readiness_value = QLabel("—")
        self.readiness_value.setObjectName(
            "ShadersReadiness"
        )

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

        directory_label = QLabel(
            "Shader directory:"
        )
        directory_label.setObjectName(
            "ShadersDirectoryLabel"
        )

        path_row.addWidget(
            directory_label
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
        details_frame.setObjectName(
            "ShadersDetailsPanel"
        )
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
        preset_type_label = QLabel(
            "Preset type"
        )
        preset_type_label.setObjectName(
            "ShadersFieldLabel"
        )
        details.addWidget(
            preset_type_label
        )
        details.addWidget(
            self.type_value
        )
        preset_path_label = QLabel(
            "Preset path"
        )
        preset_path_label.setObjectName(
            "ShadersFieldLabel"
        )
        details.addWidget(
            preset_path_label
        )
        details.addWidget(
            self.preset_value
        )
        passes_label = QLabel(
            "Referenced shader passes"
        )
        passes_label.setObjectName(
            "ShadersFieldLabel"
        )
        details.addWidget(
            passes_label
        )
        details.addWidget(
            self.passes_value
        )
        missing_label = QLabel(
            "Missing dependencies"
        )
        missing_label.setObjectName(
            "ShadersFieldLabel"
        )
        details.addWidget(
            missing_label
        )
        details.addWidget(
            self.missing_value
        )
        readiness_label = QLabel(
            "Status"
        )
        readiness_label.setObjectName(
            "ShadersFieldLabel"
        )
        details.addWidget(
            readiness_label
        )
        details.addWidget(
            self.readiness_value
        )

        details.addSpacing(8)

        assignment_label = QLabel(
            "RetroVault Presentation Assignment"
        )
        assignment_label.setObjectName(
            "ShadersAssignmentTitle"
        )

        details.addWidget(
            assignment_label
        )
        details.addWidget(
            self.default_button
        )
        details.addWidget(
            self.system_button
        )
        details.addWidget(
            self.game_button
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


    def _connect_signals(self):
        self.refresh_button.clicked.connect(
            self.refresh_shaders
        )
        self.shader_list.currentRowChanged.connect(
            self.show_shader
        )
        self.default_button.clicked.connect(
            self.assign_default_shader
        )
        self.system_button.clicked.connect(
            self.assign_system_shader
        )
        self.game_button.clicked.connect(
            self.assign_game_shader
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

        self.default_button.setEnabled(
            False
        )
        self.system_button.setEnabled(
            False
        )
        self.game_button.setEnabled(
            False
        )

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

        assignable = (
            shader.ready
            and self.presentation_store
            is not None
        )

        self.default_button.setEnabled(
            assignable
        )
        self.system_button.setEnabled(
            assignable
            and self.current_game_provider
            is not None
        )
        self.game_button.setEnabled(
            assignable
            and self.current_game_provider
            is not None
        )

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

    def _selected_assignable_shader(
        self,
    ):
        row = self.shader_list.currentRow()

        if (
            row < 0
            or row >= len(self.shaders)
        ):
            return None

        shader = self.shaders[row]

        if not shader.ready:
            return None

        return shader

    def _selected_shader_path(
        self,
    ):
        shader = (
            self._selected_assignable_shader()
        )

        if shader is None:
            return ""

        return str(
            shader.preset_path.expanduser().resolve(
                strict=False
            )
        )

    def _current_game(
        self,
    ):
        if self.current_game_provider is None:
            return None

        return self.current_game_provider()

    def assign_default_shader(
        self,
    ):
        if self.presentation_store is None:
            return

        shader = self._selected_shader_path()

        if not shader:
            return

        try:
            self.presentation_store.assign_default_shader(
                shader
            )
        except (
            OSError,
            ValueError,
        ) as exc:
            self.status_label.setText(
                "Unable to assign shader: "
                f"{exc}"
            )
            return

        self.status_label.setText(
            "Assigned selected shader as "
            "RetroVault default."
        )

    def assign_system_shader(
        self,
    ):
        if self.presentation_store is None:
            return

        shader = self._selected_shader_path()

        if not shader:
            return

        game = self._current_game()

        if game is None:
            self.status_label.setText(
                "Select a game in the Library "
                "before assigning a system shader."
            )
            return

        platform_id = str(
            getattr(
                game,
                "rvdb_platform_id",
                "",
            )
            or ""
        )

        if not platform_id:
            self.status_label.setText(
                "The selected game does not have "
                "a canonical RVDB system identity."
            )
            return

        try:
            self.presentation_store.assign_system_shader(
                platform_id,
                shader,
            )
        except (
            OSError,
            ValueError,
        ) as exc:
            self.status_label.setText(
                "Unable to assign shader: "
                f"{exc}"
            )
            return

        self.status_label.setText(
            "Assigned selected shader to "
            f"system {platform_id}."
        )

    def assign_game_shader(
        self,
    ):
        if self.presentation_store is None:
            return

        shader = self._selected_shader_path()

        if not shader:
            return

        game = self._current_game()

        if game is None:
            self.status_label.setText(
                "Select a game in the Library "
                "before assigning a game shader."
            )
            return

        try:
            identity = game_identity(
                game
            )

            self.presentation_store.assign_game_shader(
                identity,
                shader,
            )
        except (
            OSError,
            ValueError,
        ) as exc:
            self.status_label.setText(
                "Unable to assign shader: "
                f"{exc}"
            )
            return

        self.status_label.setText(
            "Assigned selected shader to "
            f"{game.name}."
        )
