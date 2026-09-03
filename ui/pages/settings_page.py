import os
import subprocess

from pathlib import Path

from PyQt6.QtCore import (
    Qt,
)
from PyQt6.QtGui import (
    QColor,
    QPainter,
)
from PyQt6.QtWidgets import (
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from config import (
    ConfigLoader,
    ConfigWriter,
)


class ReadyCheckButton(QPushButton):
    """Status button with a green Ready check mark."""

    READY_TEXT = "Ready ✓"
    READY_LABEL = "Ready"
    READY_CHECK = "✓"

    def __init__(
        self,
        text="",
        parent=None,
    ):
        super().__init__(
            text,
            parent,
        )

        self._ready_check_color = QColor(
            46,
            204,
            113,
        )

    def ready_check_visible(self):
        return (
            self.text()
            == self.READY_TEXT
        )

    def ready_check_color(self):
        return QColor(
            self._ready_check_color
        )

    def paintEvent(self, event):
        if not self.ready_check_visible():
            super().paintEvent(
                event
            )
            return

        original_text = self.text()

        self.setText(
            ""
        )

        try:
            super().paintEvent(
                event
            )
        finally:
            self.setText(
                original_text
            )

        painter = QPainter(
            self
        )

        painter.setRenderHint(
            QPainter.RenderHint.TextAntialiasing,
            True,
        )

        font = self.font()

        painter.setFont(
            font
        )

        metrics = painter.fontMetrics()

        spacing = metrics.horizontalAdvance(
            " "
        )

        ready_width = metrics.horizontalAdvance(
            self.READY_LABEL
        )

        check_width = metrics.horizontalAdvance(
            self.READY_CHECK
        )

        total_width = (
            ready_width
            + spacing
            + check_width
        )

        start_x = (
            self.rect().center().x()
            - total_width // 2
        )

        text_rect = self.rect()

        normal_color = (
            self.palette()
            .buttonText()
            .color()
        )

        if not self.isEnabled():
            normal_color = (
                self.palette()
                .color(
                    self.palette()
                    .ColorGroup.Disabled,
                    self.palette()
                    .ColorRole.ButtonText,
                )
            )

        painter.setPen(
            normal_color
        )

        ready_rect = text_rect.adjusted(
            start_x - text_rect.left(),
            0,
            0,
            0,
        )

        ready_rect.setWidth(
            ready_width
        )

        painter.drawText(
            ready_rect,
            int(
                Qt.AlignmentFlag.AlignVCenter
                | Qt.AlignmentFlag.AlignLeft
            ),
            self.READY_LABEL,
        )

        check_rect = text_rect.adjusted(
            (
                start_x
                + ready_width
                + spacing
                - text_rect.left()
            ),
            0,
            0,
            0,
        )

        check_rect.setWidth(
            check_width
        )

        painter.setPen(
            self._ready_check_color
        )

        painter.drawText(
            check_rect,
            int(
                Qt.AlignmentFlag.AlignVCenter
                | Qt.AlignmentFlag.AlignLeft
            ),
            self.READY_CHECK,
        )


class SettingsPage(QWidget):
    """Read-only view of RetroVault's effective runtime configuration."""

    READY = "Ready"
    MISSING = "Missing"

    STATUS_READY_TEXT = "Ready ✓"
    STATUS_MISSING_TEXT = "Missing !"
    STATUS_CHECK_TEXT = "Check"

    PATH_EDITOR_MIN_WIDTH = 240
    PATH_EDITOR_MAX_WIDTH = 760
    PATH_EDITOR_PADDING = 34

    def __init__(
        self,
        config_loader=None,
        config_writer=None,
    ):
        super().__init__()

        self.config_loader = (
            config_loader
            or ConfigLoader()
        )

        self.config_writer = (
            config_writer
            or ConfigWriter(
                runtime_file=(
                    self.config_loader.runtime_file
                )
            )
        )

        self.config = (
            self.config_loader.load()
        )

        self._build_ui()
        self._populate()

    def _build_ui(self):
        layout = QVBoxLayout(
            self
        )

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
            "Settings"
        )

        self.title_label.setObjectName(
            "PageTitle"
        )

        self.subtitle_label = QLabel(
            "Effective RetroVault runtime "
            "configuration and environment status."
        )

        self.subtitle_label.setObjectName(
            "PageSubtitle"
        )

        self.subtitle_label.setWordWrap(
            True
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

        runtime_group = QGroupBox(
            "RetroArch Runtime"
        )

        runtime_layout = QVBoxLayout(
            runtime_group
        )

        self.retroarch_status = ReadyCheckButton(
            self.STATUS_CHECK_TEXT
        )

        self.retroarch_status.setToolTip(
            "Validate the RetroArch executable path"
        )

        self.retroarch_status.clicked.connect(
            self._validate_retroarch_path
        )

        self.retroarch_edit = QLineEdit()

        self.retroarch_edit.setPlaceholderText(
            "RetroArch executable"
        )

        self.retroarch_browse_button = QPushButton(
            "Browse…"
        )

        self.retroarch_browse_button.clicked.connect(
            self._browse_retroarch
        )

        self._configure_path_editor(
            self.retroarch_edit
        )

        self.retroarch_edit.textEdited.connect(
            lambda _text:
                self._mark_status_unchecked(
                    self.retroarch_status,
                    "Validate the RetroArch executable path",
                )
        )

        runtime_layout.addLayout(
            self._path_editor_row(
                self.retroarch_edit,
                self.retroarch_browse_button,
                self.retroarch_status,
            )
        )

        self.core_directory_status = ReadyCheckButton(
            self.STATUS_CHECK_TEXT
        )

        self.core_directory_status.setToolTip(
            "Validate the RetroArch core directory"
        )

        self.core_directory_status.clicked.connect(
            self._validate_core_directory
        )

        self.core_directory_edit = QLineEdit()

        self.core_directory_edit.setPlaceholderText(
            "Core directory"
        )

        self.core_directory_browse_button = QPushButton(
            "Browse…"
        )

        self.core_directory_browse_button.clicked.connect(
            self._browse_core_directory
        )

        self._configure_path_editor(
            self.core_directory_edit
        )

        self.core_directory_edit.textEdited.connect(
            lambda _text:
                self._mark_status_unchecked(
                    self.core_directory_status,
                    "Validate the RetroArch core directory",
                )
        )

        runtime_layout.addLayout(
            self._path_editor_row(
                self.core_directory_edit,
                self.core_directory_browse_button,
                self.core_directory_status,
            )
        )

        runtime_layout.addSpacing(
            10
        )

        save_layout = QHBoxLayout()

        save_layout.setSpacing(
            8
        )

        self.save_button = QPushButton(
            "Save Runtime Settings"
        )

        self.save_button.clicked.connect(
            self.save_runtime_settings
        )

        self.restore_defaults_button = QPushButton(
            "Restore Default Paths"
        )

        self.restore_defaults_button.clicked.connect(
            self.restore_default_paths
        )

        self.save_status = QLabel()

        save_layout.addWidget(
            self.save_button
        )

        save_layout.addWidget(
            self.restore_defaults_button
        )

        save_layout.addWidget(
            self.save_status
        )

        save_layout.addStretch(
            1
        )

        runtime_layout.addLayout(
            save_layout
        )

        layout.addWidget(
            runtime_group
        )

        library_group = QGroupBox(
            "Library"
        )

        library_layout = QVBoxLayout(
            library_group
        )

        self.library_sources_value = QLabel()
        self.library_sources_value.setWordWrap(
            True
        )

        self.library_sources_status = ReadyCheckButton(
            self.STATUS_CHECK_TEXT
        )

        self.library_sources_status.setToolTip(
            "Validate the library directory"
        )

        self.library_sources_status.clicked.connect(
            self._validate_library_directory
        )

        self.library_path_edit = QLineEdit()

        self.library_path_edit.setPlaceholderText(
            "Library path"
        )

        self.library_browse_button = QPushButton(
            "Browse…"
        )

        self.library_browse_button.clicked.connect(
            self._browse_library
        )

        self._configure_path_editor(
            self.library_path_edit
        )

        self.library_path_edit.textEdited.connect(
            lambda _text:
                self._mark_status_unchecked(
                    self.library_sources_status,
                    "Validate the library directory",
                )
        )

        library_layout.addLayout(
            self._path_editor_row(
                self.library_path_edit,
                self.library_browse_button,
                self.library_sources_status,
            )
        )

        self.artwork_directory_status = ReadyCheckButton(
            self.STATUS_CHECK_TEXT
        )

        self.artwork_directory_status.setToolTip(
            "Validate the artwork directory"
        )

        self.artwork_directory_status.clicked.connect(
            self._validate_artwork_directory
        )

        self.artwork_directory_edit = QLineEdit()

        self.artwork_directory_edit.setPlaceholderText(
            "Artwork directory"
        )

        self.artwork_directory_browse_button = QPushButton(
            "Browse…"
        )

        self.artwork_directory_browse_button.clicked.connect(
            self._browse_artwork_directory
        )

        self._configure_path_editor(
            self.artwork_directory_edit
        )

        self.artwork_directory_edit.textEdited.connect(
            lambda _text:
                self._mark_status_unchecked(
                    self.artwork_directory_status,
                    "Validate the artwork directory",
                )
        )

        library_layout.addLayout(
            self._path_editor_row(
                self.artwork_directory_edit,
                self.artwork_directory_browse_button,
                self.artwork_directory_status,
            )
        )

        layout.addWidget(
            library_group
        )

        assets_group = QGroupBox(
            "RetroArch Assets"
        )

        assets_layout = QVBoxLayout(
            assets_group
        )

        self.overlays_value = QLabel()
        self.overlays_status = QLabel()

        assets_layout.addLayout(
            self._setting_row(
                "Overlays",
                self.overlays_value,
                self.overlays_status,
            )
        )

        self.shaders_value = QLabel()
        self.shaders_status = QLabel()

        assets_layout.addLayout(
            self._setting_row(
                "Shaders",
                self.shaders_value,
                self.shaders_status,
            )
        )

        layout.addWidget(
            assets_group
        )

        config_group = QGroupBox(
            "User Configuration"
        )

        config_layout = QVBoxLayout(
            config_group
        )

        self.runtime_config_value = QLabel()
        self.runtime_config_value.setWordWrap(
            True
        )

        self.runtime_config_status = QLabel()

        config_layout.addLayout(
            self._setting_row(
                "Runtime override",
                self.runtime_config_value,
                self.runtime_config_status,
            )
        )

        note = QLabel(
            "Settings are currently read-only. "
            "RetroVault does not create or modify "
            "runtime.json from this page."
        )

        note.setWordWrap(
            True
        )

        note.setStyleSheet(
            "color: #9aa0a6;"
        )

        config_layout.addWidget(
            note
        )

        layout.addWidget(
            config_group
        )

        layout.addStretch(
            1
        )

    @staticmethod
    def _path_editor_row(
        edit,
        browse_button,
        status_label,
    ):
        row = QHBoxLayout()

        row.setContentsMargins(
            0,
            0,
            0,
            0,
        )

        row.setSpacing(
            8
        )

        row.addWidget(
            edit
        )

        row.addWidget(
            browse_button
        )

        status_label.setMinimumWidth(
            70
        )

        row.addWidget(
            status_label
        )

        row.addStretch(
            1
        )

        return row

    def _configure_path_editor(
        self,
        edit,
    ):
        edit.setSizePolicy(
            QSizePolicy.Policy.Fixed,
            QSizePolicy.Policy.Fixed,
        )

        edit.textChanged.connect(
            lambda _text, field=edit:
                self._resize_path_editor(
                    field
                )
        )

        self._resize_path_editor(
            edit
        )

    def _resize_path_editor(
        self,
        edit,
    ):
        content = (
            edit.text()
            or edit.placeholderText()
        )

        measured = (
            edit.fontMetrics()
            .horizontalAdvance(
                content
            )
            + self.PATH_EDITOR_PADDING
        )

        width = max(
            self.PATH_EDITOR_MIN_WIDTH,
            min(
                measured,
                self.PATH_EDITOR_MAX_WIDTH,
            ),
        )

        edit.setFixedWidth(
            width
        )

    @staticmethod
    def _setting_row(
        title,
        value_label,
        status_label,
    ):
        frame = QFrame()

        frame_layout = QFormLayout(
            frame
        )

        title_label = QLabel(
            title
        )

        value_label.setTextInteractionFlags(
            value_label.textInteractionFlags()
        )

        status_label.setMinimumWidth(
            120
        )

        frame_layout.addRow(
            title_label,
            value_label,
        )

        frame_layout.addRow(
            QLabel("Status"),
            status_label,
        )

        wrapper = QVBoxLayout()

        wrapper.addWidget(
            frame
        )

        return wrapper

    @staticmethod
    def _expanded_path(
        value,
    ):
        if not value:
            return None

        return Path(
            value
        ).expanduser()

    @classmethod
    def _file_status(
        cls,
        value,
    ):
        path = cls._expanded_path(
            value
        )

        if (
            path is not None
            and path.is_file()
        ):
            return cls.READY

        return cls.MISSING

    @classmethod
    def _directory_status(
        cls,
        value,
    ):
        path = cls._expanded_path(
            value
        )

        if (
            path is not None
            and path.is_dir()
        ):
            return cls.READY

        return cls.MISSING

    def _mark_status_unchecked(
        self,
        button,
        tooltip,
    ):
        button.setText(
            self.STATUS_CHECK_TEXT
        )

        button.setToolTip(
            tooltip
        )

    def _set_path_validation_result(
        self,
        button,
        *,
        ready,
        path_value,
        description,
    ):
        path_text = (
            str(path_value)
            if path_value
            else "(not configured)"
        )

        if ready:
            button.setText(
                self.STATUS_READY_TEXT
            )

            button.setToolTip(
                (
                    f"{description} is valid.\n"
                    f"{path_text}\n"
                    "Click to check again."
                )
            )
        else:
            button.setText(
                self.STATUS_MISSING_TEXT
            )

            button.setToolTip(
                (
                    f"{description} is missing, "
                    "invalid, or unreadable.\n"
                    f"{path_text}\n"
                    "Choose another path or click "
                    "to check again."
                )
            )

    @classmethod
    def _is_retroarch_executable(
        cls,
        value,
    ):
        path = cls._expanded_path(
            value
        )

        if (
            path is None
            or not path.is_file()
            or not os.access(
                path,
                os.X_OK,
            )
        ):
            return False

        try:
            result = subprocess.run(
                [
                    str(path),
                    "--version",
                ],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
        except (
            OSError,
            subprocess.SubprocessError,
        ):
            return False

        output = (
            result.stdout
            + "\n"
            + result.stderr
        ).lower()

        return (
            "retroarch" in output
            and "libretro" in output
        )

    def _validate_retroarch_path(self):
        value = (
            self.retroarch_edit
            .text()
            .strip()
        )

        ready = (
            self._is_retroarch_executable(
                value
            )
        )

        self._set_path_validation_result(
            self.retroarch_status,
            ready=ready,
            path_value=value,
            description="RetroArch executable",
        )

        return ready

    @classmethod
    def _contains_libretro_core(
        cls,
        value,
    ):
        path = cls._expanded_path(
            value
        )

        if (
            path is None
            or not path.is_dir()
            or not os.access(
                path,
                os.R_OK,
            )
        ):
            return False

        patterns = (
            "*_libretro.so",
            "*_libretro.dylib",
            "*_libretro.dll",
        )

        try:
            for pattern in patterns:
                if next(
                    path.rglob(pattern),
                    None,
                ) is not None:
                    return True
        except OSError:
            return False

        return False

    def _validate_directory_control(
        self,
        edit,
        button,
        description,
    ):
        value = (
            edit
            .text()
            .strip()
        )

        path = self._expanded_path(
            value
        )

        ready = bool(
            path is not None
            and path.is_dir()
            and os.access(
                path,
                os.R_OK,
            )
        )

        self._set_path_validation_result(
            button,
            ready=ready,
            path_value=value,
            description=description,
        )

        return ready

    def _validate_core_directory(self):
        value = (
            self.core_directory_edit
            .text()
            .strip()
        )

        ready = (
            self._contains_libretro_core(
                value
            )
        )

        self._set_path_validation_result(
            self.core_directory_status,
            ready=ready,
            path_value=value,
            description=(
                "RetroArch core directory"
            ),
        )

        return ready

    def _validate_library_directory(self):
        return self._validate_directory_control(
            self.library_path_edit,
            self.library_sources_status,
            "Library directory",
        )

    def _validate_artwork_directory(self):
        return self._validate_directory_control(
            self.artwork_directory_edit,
            self.artwork_directory_status,
            "Artwork directory",
        )

    def _populate(self):
        retroarch = (
            self.config
            .get(
                "retroarch",
                {},
            )
        )

        executable = retroarch.get(
            "executable",
            "",
        )

        core_directory = (
            retroarch
            .get(
                "cores",
                {},
            )
            .get(
                "directory",
                "",
            )
        )

        self.retroarch_edit.setText(
            executable
        )

        self._validate_retroarch_path()

        self.core_directory_edit.setText(
            core_directory
        )

        self._validate_core_directory()

        sources = (
            self.config
            .get(
                "library",
                {},
            )
            .get(
                "sources",
                [],
            )
        )

        enabled_sources = [
            source
            for source in sources
            if source.get(
                "enabled",
                False,
            )
        ]

        source_lines = []

        source_ready = (
            bool(
                enabled_sources
            )
        )

        for source in enabled_sources:
            name = source.get(
                "name",
                source.get(
                    "id",
                    "Library",
                ),
            )

            path_value = source.get(
                "path",
                "",
            )

            source_lines.append(
                (
                    f"{name} — {path_value}"
                    if path_value
                    else str(name)
                )
            )

            if (
                self._directory_status(
                    path_value
                )
                != self.READY
            ):
                source_ready = False

        if source_lines:
            source_text = "\n".join(
                source_lines
            )
        else:
            source_text = (
                "No enabled library sources"
            )

        self.library_sources_value.setText(
            source_text
        )

        if enabled_sources:
            self.library_path_edit.setText(
                str(
                    enabled_sources[0]
                    .get(
                        "path",
                        "",
                    )
                )
            )
        else:
            self.library_path_edit.setText(
                ""
            )

        self._validate_library_directory()

        paths = self.config.get(
            "paths",
            {},
        )

        artwork_directory = (
            paths
            .get(
                "artwork",
                {},
            )
            .get(
                "directory",
                "",
            )
        )

        self.artwork_directory_edit.setText(
            str(
                artwork_directory
                or ""
            )
        )

        self._validate_artwork_directory()

        overlays = (
            paths
            .get(
                "overlays",
                {},
            )
            .get(
                "directory",
                "",
            )
        )

        shaders = (
            paths
            .get(
                "shaders",
                {},
            )
            .get(
                "directory",
                "",
            )
        )

        self.overlays_value.setText(
            overlays
            or "Not configured"
        )

        self.overlays_status.setText(
            self._directory_status(
                overlays
            )
        )

        self.shaders_value.setText(
            shaders
            or "Not configured"
        )

        self.shaders_status.setText(
            self._directory_status(
                shaders
            )
        )

        runtime_file = (
            self.config_loader.runtime_file
        )

        self.runtime_config_value.setText(
            str(runtime_file)
        )

        self.runtime_config_status.setText(
            (
                "User overrides active"
                if runtime_file.is_file()
                else "Defaults active"
            )
        )

    def restore_default_paths(self):
        defaults = (
            self.config_loader
            ._load_defaults()
        )

        retroarch = (
            defaults
            .get(
                "retroarch",
                {},
            )
        )

        executable = retroarch.get(
            "executable",
            "",
        )

        core_directory = (
            retroarch
            .get(
                "cores",
                {},
            )
            .get(
                "directory",
                "",
            )
        )

        sources = (
            defaults
            .get(
                "library",
                {},
            )
            .get(
                "sources",
                [],
            )
        )

        library_path = ""

        enabled_sources = [
            source
            for source in sources
            if source.get(
                "enabled",
                False,
            )
        ]

        if enabled_sources:
            library_path = str(
                enabled_sources[0]
                .get(
                    "path",
                    "",
                )
            )
        elif sources:
            library_path = str(
                sources[0]
                .get(
                    "path",
                    "",
                )
            )

        self.retroarch_edit.setText(
            str(
                executable
                or ""
            )
        )

        self.core_directory_edit.setText(
            str(
                core_directory
                or ""
            )
        )

        self.library_path_edit.setText(
            library_path
        )

        default_paths = defaults.get(
            "paths",
            {},
        )

        artwork_directory = (
            default_paths
            .get(
                "artwork",
                {},
            )
            .get(
                "directory",
                "",
            )
        )

        self.artwork_directory_edit.setText(
            str(
                artwork_directory
                or ""
            )
        )

        self._resize_path_editor(
            self.retroarch_edit
        )

        self._resize_path_editor(
            self.core_directory_edit
        )

        self._resize_path_editor(
            self.library_path_edit
        )

        self._resize_path_editor(
            self.artwork_directory_edit
        )

        self._validate_retroarch_path()

        self._validate_core_directory()

        self._validate_library_directory()

        self._validate_artwork_directory()

        self.save_status.setText(
            "Default paths restored — save to apply"
        )

    @staticmethod
    def _browse_start_path(
        value,
    ):
        if not value:
            return str(
                Path.home()
            )

        expanded = Path(
            value
        ).expanduser()

        if expanded.is_dir():
            return str(
                expanded
            )

        if expanded.parent.exists():
            return str(
                expanded.parent
            )

        return str(
            Path.home()
        )

    def _browse_retroarch(self):
        selected, _filter = (
            QFileDialog.getOpenFileName(
                self,
                "Choose RetroArch executable",
                self._browse_start_path(
                    self.retroarch_edit.text()
                ),
                options=(
                    QFileDialog.Option
                    .DontUseNativeDialog
                ),
            )
        )

        if selected:
            self.retroarch_edit.setText(
                selected
            )

            self._validate_retroarch_path()

    def _browse_core_directory(self):
        selected = (
            QFileDialog.getExistingDirectory(
                self,
                "Choose RetroArch core directory",
                self._browse_start_path(
                    self.core_directory_edit.text()
                ),
                options=(
                    QFileDialog.Option.ShowDirsOnly
                    |
                    QFileDialog.Option
                    .DontUseNativeDialog
                ),
            )
        )

        if selected:
            self.core_directory_edit.setText(
                selected
            )

            self._validate_core_directory()

    def _browse_library(self):
        selected = (
            QFileDialog.getExistingDirectory(
                self,
                "Choose library directory",
                self._browse_start_path(
                    self.library_path_edit.text()
                ),
                options=(
                    QFileDialog.Option.ShowDirsOnly
                    |
                    QFileDialog.Option
                    .DontUseNativeDialog
                ),
            )
        )

        if selected:
            self.library_path_edit.setText(
                selected
            )

            self._validate_library_directory()

    def _browse_artwork_directory(self):
        selected = (
            QFileDialog.getExistingDirectory(
                self,
                "Choose artwork directory",
                self._browse_start_path(
                    self.artwork_directory_edit.text()
                ),
                options=(
                    QFileDialog.Option.ShowDirsOnly
                    |
                    QFileDialog.Option
                    .DontUseNativeDialog
                ),
            )
        )

        if selected:
            self.artwork_directory_edit.setText(
                selected
            )

            self._validate_artwork_directory()

    def save_runtime_settings(self):
        executable = (
            self.retroarch_edit
            .text()
            .strip()
        )

        core_directory = (
            self.core_directory_edit
            .text()
            .strip()
        )

        library_path = (
            self.library_path_edit
            .text()
            .strip()
        )

        artwork_directory = (
            self.artwork_directory_edit
            .text()
            .strip()
        )

        if not self._validate_retroarch_path():
            self.save_status.setText(
                "RetroArch executable is invalid"
            )
            return

        if not self._validate_core_directory():
            self.save_status.setText(
                "RetroArch core directory is invalid"
            )
            return

        if not self._validate_library_directory():
            self.save_status.setText(
                "Library path is not a readable directory"
            )
            return

        self._validate_artwork_directory()

        library_directory = (
            Path(
                library_path
            )
            .expanduser()
        )

        if not (
            library_path
            and library_directory.is_dir()
            and library_directory.exists()
        ):
            self.save_status.setText(
                "Library path is not a readable directory"
            )
            return

        sources = (
            self.config
            .get(
                "library",
                {},
            )
            .get(
                "sources",
                [],
            )
        )

        if len(sources) != 1:
            self.save_status.setText(
                "Exactly one library source is required"
            )
            return

        source = dict(
            sources[0]
        )

        source[
            "path"
        ] = library_path

        overrides = {
            "retroarch": {
                "executable": executable,
                "cores": {
                    "directory": core_directory,
                },
            },
            "library": {
                "sources": [
                    source,
                ],
            },
            "paths": {
                "artwork": {
                    "directory": artwork_directory,
                },
            },
        }

        try:
            self.config_writer.update(
                overrides
            )
        except ValueError as exc:
            self.save_status.setText(
                str(exc)
            )
            return

        self.config = (
            self.config_loader.load()
        )

        self._populate()

        self.save_status.setText(
            "Settings saved"
        )
