from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QComboBox,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from services.library.state import game_identity

from services.presentation.service import (
    NativeVisualInstallStatus,
    NativeVisualService,
)

from services.presentation.visual_catalog import (
    VisualAssetType,
)
from services.presentation.visual_discovery import (
    VisualAssetDiscovery,
)


class NativeVisualsPage(QWidget):
    """
    Curated RetroVault-native visual collection.

    This page deliberately consumes NativeVisualService rather than
    scanning RetroArch visual directories.

    Installed RetroArch, third-party, and user overlays remain the
    responsibility of the existing OverlaysPage.
    """

    def __init__(
        self,
        native_visual_service=None,
        presentation_store=None,
        current_game_provider=None,
    ):
        super().__init__()

        self.native_visual_service = (
            native_visual_service
            or NativeVisualService()
        )

        self.presentation_store = (
            presentation_store
        )

        self.current_game_provider = (
            current_game_provider
        )

        self.assets = []
        self.statuses = []
        self._all_statuses = []

        self.title_label = QLabel(
            "RetroVault Visuals"
        )
        self.title_label.setObjectName(
            "PageTitle"
        )

        self.subtitle_label = QLabel(
            "Curated visual presentations created "
            "for RetroVault."
        )
        self.subtitle_label.setObjectName(
            "PageSubtitle"
        )
        self.subtitle_label.setWordWrap(
            True
        )

        self.collection_label = QLabel(
            "RetroVault Collection"
        )
        self.collection_label.setObjectName(
            "SectionTitle"
        )

        self.count_label = QLabel()
        self.status_label = QLabel()

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText(
            "Search RetroVault visuals…"
        )
        self.search_edit.setClearButtonEnabled(
            True
        )

        self.type_filter = QComboBox()
        self.type_filter.addItem(
            "All Visual Types",
            "",
        )

        for asset_type in VisualAssetType:
            self.type_filter.addItem(
                asset_type.value.title(),
                asset_type.value,
            )

        self.clear_filters_button = QPushButton(
            "Clear Filters"
        )
        self.clear_filters_button.setEnabled(
            False
        )

        self.visual_list = QListWidget()
        self.visual_list.setMinimumWidth(
            320
        )

        self.preview = QLabel(
            "Select a RetroVault visual"
        )
        self.preview.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        self.preview.setMinimumSize(
            420,
            240,
        )

        self.name_value = QLabel(
            "Select a RetroVault visual"
        )
        self.name_value.setObjectName(
            "SectionTitle"
        )
        self.name_value.setWordWrap(
            True
        )

        self.source_value = QLabel("—")
        self.type_value = QLabel("—")
        self.author_value = QLabel("—")
        self.install_status_value = QLabel("—")

        self.reference_value = QLabel("—")
        self.reference_value.setWordWrap(
            True
        )
        self.reference_value.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.attribution_value = QLabel("—")
        self.attribution_value.setWordWrap(
            True
        )

        self.install_button = QPushButton(
            "Install"
        )
        self.install_button.setEnabled(
            False
        )

        self.refresh_button = QPushButton(
            "Refresh"
        )

        self.default_button = QPushButton(
            "Set as Default"
        )

        self.system_button = QPushButton(
            "Set for System"
        )

        self.game_button = QPushButton(
            "Set for Game"
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

        self._build_ui()
        self._connect_signals()
        self.refresh_visuals()

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

        discovery_controls = QHBoxLayout()
        discovery_controls.setSpacing(
            10
        )

        discovery_controls.addWidget(
            self.search_edit,
            1,
        )

        discovery_controls.addWidget(
            self.type_filter
        )

        discovery_controls.addWidget(
            self.clear_filters_button
        )

        layout.addLayout(
            discovery_controls
        )

        header = QHBoxLayout()
        header.setSpacing(10)

        header.addWidget(
            self.collection_label
        )

        header.addStretch(1)

        header.addWidget(
            self.refresh_button
        )

        layout.addLayout(
            header
        )

        layout.addWidget(
            self.count_label
        )

        content = QHBoxLayout()
        content.setSpacing(20)

        content.addWidget(
            self.visual_list,
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
            QLabel("Collection")
        )

        details.addWidget(
            self.source_value
        )

        details.addWidget(
            QLabel("Visual type")
        )

        details.addWidget(
            self.type_value
        )

        details.addWidget(
            QLabel("Author")
        )

        details.addWidget(
            self.author_value
        )

        details.addWidget(
            QLabel("Installation")
        )

        details.addWidget(
            self.install_status_value
        )

        details.addWidget(
            QLabel("Portable reference")
        )

        details.addWidget(
            self.reference_value
        )

        details.addWidget(
            QLabel("Attribution")
        )

        details.addWidget(
            self.attribution_value
        )

        details.addSpacing(8)

        details.addWidget(
            self.install_button
        )

        details.addSpacing(8)

        assignment_label = QLabel(
            "RetroVault Presentation Assignment"
        )
        assignment_label.setObjectName(
            "SectionTitle"
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

        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(
            True
        )
        self.details_scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )
        self.details_scroll.setWidget(
            details_frame
        )

        content.addWidget(
            self.details_scroll,
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
        self.search_edit.textChanged.connect(
            self._apply_filters
        )

        self.type_filter.currentIndexChanged.connect(
            self._apply_filters
        )

        self.clear_filters_button.clicked.connect(
            self.clear_filters
        )

        self.visual_list.currentRowChanged.connect(
            self.show_visual
        )

        self.install_button.clicked.connect(
            self.install_selected_visual
        )

        self.refresh_button.clicked.connect(
            self.refresh_visuals
        )

        self.default_button.clicked.connect(
            self.assign_default_visual
        )

        self.system_button.clicked.connect(
            self.assign_system_visual
        )

        self.game_button.clicked.connect(
            self.assign_game_visual
        )

    @staticmethod
    def _status_display(
        status,
    ):
        if (
            status
            is NativeVisualInstallStatus.CURRENT
        ):
            return "Installed"

        if (
            status
            is NativeVisualInstallStatus.OUTDATED
        ):
            return "Update available"

        return "Not installed"

    @staticmethod
    def _button_display(
        status,
    ):
        if (
            status
            is NativeVisualInstallStatus.CURRENT
        ):
            return "Installed"

        if (
            status
            is NativeVisualInstallStatus.OUTDATED
        ):
            return "Update"

        return "Install"

    def _selected_asset_id(
        self,
    ):
        row = self.visual_list.currentRow()

        if (
            row < 0
            or row >= len(
                self.statuses
            )
        ):
            return ""

        return str(
            self.statuses[
                row
            ].asset.id
            or ""
        )

    def _selected_type_filter(
        self,
    ):
        value = str(
            self.type_filter.currentData()
            or ""
        ).strip()

        if not value:
            return None

        return VisualAssetType(
            value
        )

    def _filters_active(
        self,
    ):
        return bool(
            self.search_edit.text().strip()
            or self.type_filter.currentData()
        )

    def clear_filters(
        self,
    ):
        if not self._filters_active():
            return

        preserve_asset_id = (
            self._selected_asset_id()
        )

        self.search_edit.blockSignals(
            True
        )
        self.type_filter.blockSignals(
            True
        )

        try:
            self.search_edit.clear()
            self.type_filter.setCurrentIndex(
                0
            )
        finally:
            self.search_edit.blockSignals(
                False
            )
            self.type_filter.blockSignals(
                False
            )

        self._apply_filters(
            preserve_asset_id=(
                preserve_asset_id
            ),
        )

    def _count_text(
        self,
        visible,
        total,
    ):
        if self._filters_active():
            return (
                f"{visible} of {total} "
                "RetroVault visuals"
            )

        return (
            "1 RetroVault visual"
            if visible == 1
            else (
                f"{visible} "
                "RetroVault visuals"
            )
        )

    def _populate_visual_list(
        self,
        *,
        preserve_asset_id="",
    ):
        self.visual_list.blockSignals(
            True
        )

        selected_row = -1

        try:
            self.visual_list.clear()

            for row, (
                asset,
                status,
            ) in enumerate(
                zip(
                    self.assets,
                    self.statuses,
                )
            ):
                label = (
                    f"{asset.display_name}  —  "
                    f"{self._status_display(status.status)}"
                )

                self.visual_list.addItem(
                    label
                )

                if (
                    preserve_asset_id
                    and asset.id
                    == preserve_asset_id
                ):
                    selected_row = row

        finally:
            self.visual_list.blockSignals(
                False
            )

        visible = len(
            self.assets
        )

        total = len(
            self._all_statuses
        )

        self.clear_filters_button.setEnabled(
            self._filters_active()
        )

        self.count_label.setText(
            self._count_text(
                visible,
                total,
            )
        )

        self.clear_details()

        if selected_row >= 0:
            self.visual_list.setCurrentRow(
                selected_row
            )

            self.show_visual(
                selected_row
            )

        if visible:
            if self._filters_active():
                self.status_label.setText(
                    f"Showing {visible} of {total} "
                    "RetroVault visuals. "
                    "Select one to preview and manage it."
                )
            else:
                self.status_label.setText(
                    "Select a RetroVault visual "
                    "to preview and manage it."
                )

        elif total:
            self.status_label.setText(
                f"No RetroVault visuals match "
                f"the current filters "
                f"(0 of {total})."
            )

        else:
            self.status_label.setText(
                "No RetroVault-native visuals "
                "are currently cataloged."
            )

    def _apply_filters(
        self,
        *_signal_args,
        preserve_asset_id=None,
    ):
        selected_id = (
            preserve_asset_id
            if preserve_asset_id is not None
            else self._selected_asset_id()
        )

        if not self._all_statuses:
            self.assets = []
            self.statuses = []

            self._populate_visual_list(
                preserve_asset_id="",
            )
            return

        discovery = VisualAssetDiscovery(
            tuple(
                status.asset
                for status
                in self._all_statuses
            )
        )

        discovered = discovery.query(
            text=self.search_edit.text(),
            asset_type=(
                self._selected_type_filter()
            ),
        )

        status_by_id = {
            status.asset.id: status
            for status
            in self._all_statuses
        }

        self.assets = list(
            discovered
        )

        self.statuses = [
            status_by_id[
                asset.id
            ]
            for asset in discovered
        ]

        self._populate_visual_list(
            preserve_asset_id=(
                selected_id
            ),
        )

    def refresh_visuals(self):
        preserve_asset_id = (
            self._selected_asset_id()
        )

        try:
            assets = tuple(
                self.native_visual_service.native_assets()
            )

            statuses = tuple(
                self.native_visual_service.status(
                    asset.id
                )
                for asset in assets
            )

        except (
            KeyError,
            OSError,
            TypeError,
            ValueError,
            RuntimeError,
        ) as exc:
            self.assets = []
            self.statuses = []
            self._all_statuses = []

            self.visual_list.clear()
            self.clear_details()

            self.count_label.setText(
                "0 RetroVault visuals"
            )

            self.status_label.setText(
                "Unable to load RetroVault visuals: "
                f"{exc}"
            )

            return

        self._all_statuses = list(
            statuses
        )

        self._apply_filters(
            preserve_asset_id=(
                preserve_asset_id
            ),
        )

    def clear_details(self):
        self.name_value.setText(
            "Select a RetroVault visual"
        )

        self.source_value.setText("—")
        self.type_value.setText("—")
        self.author_value.setText("—")
        self.install_status_value.setText("—")
        self.reference_value.setText("—")
        self.attribution_value.setText("—")

        self.preview.clear()
        self.preview.setText(
            "Select a RetroVault visual"
        )

        self.install_button.setText(
            "Install"
        )

        self.install_button.setEnabled(
            False
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

    def _selected_status(self):
        row = self.visual_list.currentRow()

        if (
            row < 0
            or row >= len(
                self.statuses
            )
        ):
            return None

        return self.statuses[row]

    def show_visual(
        self,
        row,
    ):
        if (
            row < 0
            or row >= len(
                self.statuses
            )
        ):
            self.clear_details()
            return

        status = self.statuses[row]
        asset = status.asset

        self.name_value.setText(
            asset.display_name
        )

        self.source_value.setText(
            "RetroVault Visuals"
        )

        self.type_value.setText(
            asset.asset_type.value.title()
        )

        self.author_value.setText(
            asset.author or "RetroVault"
        )

        self.install_status_value.setText(
            self._status_display(
                status.status
            )
        )

        self.reference_value.setText(
            asset.reference
        )

        self.attribution_value.setText(
            asset.attribution or "—"
        )

        self.install_button.setText(
            self._button_display(
                status.status
            )
        )

        self.install_button.setEnabled(
            status.status
            is not NativeVisualInstallStatus.CURRENT
        )

        assignable = (
            status.status
            is NativeVisualInstallStatus.CURRENT
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

        self._show_preview(
            status
        )

    def _show_preview(
        self,
        status,
    ):
        self.preview.clear()
        self.preview.setText(
            "Preview unavailable"
        )

        image_extensions = {
            ".jpeg",
            ".jpg",
            ".png",
            ".webp",
        }

        for source in (
            status.deployment.source_files
        ):
            path = Path(
                source
            )

            if (
                path.suffix.casefold()
                not in image_extensions
            ):
                continue

            if not path.is_file():
                continue

            pixmap = QPixmap(
                str(path)
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

            return

    def _current_game(
        self,
    ):
        if self.current_game_provider is None:
            return None

        return self.current_game_provider()

    def _selected_assignable_status(
        self,
    ):
        selected = self._selected_status()

        if selected is None:
            return None

        if (
            selected.status
            is not NativeVisualInstallStatus.CURRENT
        ):
            return None

        if self.presentation_store is None:
            return None

        return selected

    def assign_default_visual(
        self,
    ):
        selected = (
            self._selected_assignable_status()
        )

        if selected is None:
            return

        try:
            self.presentation_store.assign_default_overlay(
                selected.asset.reference
            )
        except (
            OSError,
            TypeError,
            ValueError,
            RuntimeError,
        ) as exc:
            QMessageBox.warning(
                self,
                "RetroVault Visual Assignment Failed",
                str(exc),
            )
            return

        self.status_label.setText(
            "Assigned "
            f"{selected.asset.display_name} "
            "as RetroVault default."
        )

    def assign_system_visual(
        self,
    ):
        selected = (
            self._selected_assignable_status()
        )

        if selected is None:
            return

        game = self._current_game()

        if game is None:
            self.status_label.setText(
                "Select a game in the Library "
                "before assigning a system visual."
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
            self.presentation_store.assign_system_overlay(
                platform_id,
                selected.asset.reference,
            )
        except (
            OSError,
            TypeError,
            ValueError,
            RuntimeError,
        ) as exc:
            QMessageBox.warning(
                self,
                "RetroVault Visual Assignment Failed",
                str(exc),
            )
            return

        self.status_label.setText(
            "Assigned "
            f"{selected.asset.display_name} "
            f"to system {platform_id}."
        )

    def assign_game_visual(
        self,
    ):
        selected = (
            self._selected_assignable_status()
        )

        if selected is None:
            return

        game = self._current_game()

        if game is None:
            self.status_label.setText(
                "Select a game in the Library "
                "before assigning a game visual."
            )
            return

        try:
            identity = game_identity(
                game
            )
        except ValueError:
            self.status_label.setText(
                "The selected game does not have "
                "a stable RetroVault game identity."
            )
            return

        try:
            self.presentation_store.assign_game_overlay(
                identity,
                selected.asset.reference,
            )
        except (
            OSError,
            TypeError,
            ValueError,
            RuntimeError,
        ) as exc:
            QMessageBox.warning(
                self,
                "RetroVault Visual Assignment Failed",
                str(exc),
            )
            return

        self.status_label.setText(
            "Assigned "
            f"{selected.asset.display_name} "
            f'to game "{getattr(game, "name", identity)}".'
        )

    def install_selected_visual(
        self,
    ):
        selected = self._selected_status()

        if selected is None:
            return

        if (
            selected.status
            is NativeVisualInstallStatus.CURRENT
        ):
            return

        asset = selected.asset

        action = (
            "Update"
            if (
                selected.status
                is NativeVisualInstallStatus.OUTDATED
            )
            else "Install"
        )

        answer = QMessageBox.question(
            self,
            f"{action} RetroVault Visual",
            (
                f"{action} this RetroVault visual?\n\n"
                f"{asset.display_name}\n\n"
                "The visual will be installed into "
                "the configured RetroArch overlay "
                "directory."
            ),
            (
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
            ),
            QMessageBox.StandardButton.No,
        )

        if (
            answer
            != QMessageBox.StandardButton.Yes
        ):
            self.status_label.setText(
                f"{action} cancelled."
            )
            return

        try:
            result = (
                self.native_visual_service.install(
                    asset.id
                )
            )

        except (
            KeyError,
            OSError,
            TypeError,
            ValueError,
            RuntimeError,
        ) as exc:
            QMessageBox.warning(
                self,
                "RetroVault Visual Installation Failed",
                str(exc),
            )

            self.status_label.setText(
                "Unable to install RetroVault visual."
            )

            return

        if (
            result.status
            is not NativeVisualInstallStatus.CURRENT
        ):
            self.status_label.setText(
                "RetroVault visual did not reach "
                "Installed state."
            )
            return

        selected_row = (
            self.visual_list.currentRow()
        )

        self.refresh_visuals()

        if (
            0 <= selected_row
            < self.visual_list.count()
        ):
            self.visual_list.setCurrentRow(
                selected_row
            )

        self.status_label.setText(
            f"Installed {asset.display_name}."
        )
