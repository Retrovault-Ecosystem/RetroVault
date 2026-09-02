from pathlib import Path

from PyQt6.QtWidgets import (
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config import (
    ConfigLoader,
    ConfigWriter,
)


class SettingsPage(QWidget):
    """Read-only view of RetroVault's effective runtime configuration."""

    READY = "Ready"
    MISSING = "Missing"

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

        self.retroarch_value = QLabel()
        self.retroarch_status = QLabel()

        runtime_layout.addLayout(
            self._setting_row(
                "RetroArch executable",
                self.retroarch_value,
                self.retroarch_status,
            )
        )

        self.retroarch_edit = QLineEdit()

        runtime_layout.addLayout(
            self._edit_row(
                "Edit executable",
                self.retroarch_edit,
            )
        )

        self.core_directory_value = QLabel()
        self.core_directory_status = QLabel()

        runtime_layout.addLayout(
            self._setting_row(
                "Core directory",
                self.core_directory_value,
                self.core_directory_status,
            )
        )

        self.core_directory_edit = QLineEdit()

        runtime_layout.addLayout(
            self._edit_row(
                "Edit core directory",
                self.core_directory_edit,
            )
        )

        save_layout = QHBoxLayout()

        self.save_button = QPushButton(
            "Save Runtime Settings"
        )

        self.save_button.clicked.connect(
            self.save_runtime_settings
        )

        self.save_status = QLabel()

        save_layout.addWidget(
            self.save_button
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

        self.library_sources_status = QLabel()

        library_layout.addLayout(
            self._setting_row(
                "Configured sources",
                self.library_sources_value,
                self.library_sources_status,
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
    def _edit_row(
        title,
        edit,
    ):
        frame = QFrame()

        frame_layout = QFormLayout(
            frame
        )

        frame_layout.addRow(
            QLabel(title),
            edit,
        )

        wrapper = QVBoxLayout()

        wrapper.addWidget(
            frame
        )

        return wrapper

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

        self.retroarch_value.setText(
            executable
            or "Not configured"
        )

        self.retroarch_status.setText(
            self._file_status(
                executable
            )
        )

        self.retroarch_edit.setText(
            executable
        )

        self.core_directory_value.setText(
            core_directory
            or "Not configured"
        )

        self.core_directory_status.setText(
            self._directory_status(
                core_directory
            )
        )

        self.core_directory_edit.setText(
            core_directory
        )

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

        self.library_sources_status.setText(
            self.READY
            if source_ready
            else self.MISSING
        )

        paths = self.config.get(
            "paths",
            {},
        )

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

        overrides = {
            "retroarch": {
                "executable": executable,
                "cores": {
                    "directory": core_directory,
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
