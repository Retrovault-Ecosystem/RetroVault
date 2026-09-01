from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from services.rvdb import (
    RVDBConsumer,
    RVDBError,
)


class SystemsPage(QWidget):
    """Browse platform data supplied by RVDB."""

    def __init__(
        self,
        consumer: RVDBConsumer | None = None,
    ):
        super().__init__()

        self.consumer = consumer

        self.title_label = QLabel(
            "Systems"
        )

        self.subtitle_label = QLabel(
            "Platforms available from RVDB"
        )

        self.count_label = QLabel()

        self.system_list = QListWidget()

        self.name_label = QLabel(
            "Select a system"
        )

        self.id_label = QLabel()

        self.cores_value = QLabel("—")
        self.emulators_value = QLabel("—")
        self.frontends_value = QLabel("—")

        self.status_label = QLabel()

        self._build_ui()
        self._connect_signals()
        self._load_systems()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        main_layout.setContentsMargins(
            32,
            28,
            32,
            28,
        )

        main_layout.setSpacing(16)

        self.title_label.setStyleSheet(
            """
            font-size: 28px;
            font-weight: 700;
            """
        )

        self.subtitle_label.setStyleSheet(
            """
            font-size: 14px;
            color: #9aa0a6;
            """
        )

        self.count_label.setStyleSheet(
            """
            font-size: 13px;
            color: #9aa0a6;
            """
        )

        main_layout.addWidget(
            self.title_label
        )

        main_layout.addWidget(
            self.subtitle_label
        )

        main_layout.addWidget(
            self.count_label
        )

        content_layout = QHBoxLayout()

        content_layout.setSpacing(20)

        self.system_list.setMinimumWidth(
            320
        )

        self.system_list.setAlternatingRowColors(
            True
        )

        content_layout.addWidget(
            self.system_list,
            2,
        )

        details_frame = QFrame()

        details_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        details_layout = QVBoxLayout(
            details_frame
        )

        details_layout.setContentsMargins(
            24,
            24,
            24,
            24,
        )

        details_layout.setSpacing(12)

        self.name_label.setStyleSheet(
            """
            font-size: 24px;
            font-weight: 600;
            """
        )

        self.id_label.setStyleSheet(
            """
            font-size: 12px;
            color: #9aa0a6;
            """
        )

        self.id_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        details_layout.addWidget(
            self.name_label
        )

        details_layout.addWidget(
            self.id_label
        )

        details_layout.addSpacing(12)

        details_layout.addWidget(
            self._section_label(
                "Supported Cores"
            )
        )

        details_layout.addWidget(
            self.cores_value
        )

        details_layout.addSpacing(10)

        details_layout.addWidget(
            self._section_label(
                "Standalone Emulators"
            )
        )

        details_layout.addWidget(
            self.emulators_value
        )

        details_layout.addSpacing(10)

        details_layout.addWidget(
            self._section_label(
                "Frontends"
            )
        )

        details_layout.addWidget(
            self.frontends_value
        )

        details_layout.addStretch()

        scroll = QScrollArea()

        scroll.setWidgetResizable(
            True
        )

        scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )

        scroll.setWidget(
            details_frame
        )

        content_layout.addWidget(
            scroll,
            3,
        )

        main_layout.addLayout(
            content_layout,
            1,
        )

        self.status_label.setStyleSheet(
            """
            font-size: 12px;
            color: #9aa0a6;
            """
        )

        main_layout.addWidget(
            self.status_label
        )

    @staticmethod
    def _section_label(
        text: str,
    ) -> QLabel:
        label = QLabel(text)

        label.setStyleSheet(
            """
            font-size: 13px;
            font-weight: 700;
            """
        )

        return label

    def _connect_signals(self) -> None:
        self.system_list.currentItemChanged.connect(
            self._system_selected
        )

    def _load_systems(self) -> None:
        self.system_list.clear()

        if self.consumer is None:
            self.count_label.setText(
                "RVDB unavailable"
            )

            self.status_label.setText(
                "No RVDB consumer was supplied."
            )

            return

        platforms = [
            entity
            for entity
            in self.consumer.nodes.values()
            if entity.get("type") == "platform"
        ]

        platforms.sort(
            key=lambda entity: (
                entity.get(
                    "name",
                    "",
                ).casefold(),
                entity.get(
                    "id",
                    "",
                ),
            )
        )

        for platform in platforms:
            name = platform.get(
                "name",
                platform["id"],
            )

            item = QListWidgetItem(
                name
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                platform["id"],
            )

            self.system_list.addItem(
                item
            )

        self.count_label.setText(
            f"{len(platforms)} platforms"
        )

        self.status_label.setText(
            "RVDB bundle loaded successfully."
        )

        if platforms:
            self.system_list.setCurrentRow(
                0
            )

    def _system_selected(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        del previous

        if current is None:
            self._clear_details()
            return

        if self.consumer is None:
            self._clear_details()
            return

        platform_id = current.data(
            Qt.ItemDataRole.UserRole
        )

        try:
            view = self.consumer.platform_view(
                platform_id
            )
        except RVDBError as exc:
            self._clear_details()

            self.status_label.setText(
                str(exc)
            )

            return

        platform = view["platform"]

        self.name_label.setText(
            platform.get(
                "name",
                platform["id"],
            )
        )

        self.id_label.setText(
            platform["id"]
        )

        self.cores_value.setText(
            self._entity_names(
                view["cores"]
            )
        )

        self.emulators_value.setText(
            self._entity_names(
                view["emulators"]
            )
        )

        self.frontends_value.setText(
            self._entity_names(
                view["frontends"]
            )
        )

        self.status_label.setText(
            "Showing live data from the "
            "local RVDB development bundle."
        )

    @staticmethod
    def _entity_names(
        entities: list[dict],
    ) -> str:
        if not entities:
            return "None currently recorded"

        names = [
            entity.get(
                "name",
                entity["id"],
            )
            for entity in entities
        ]

        names.sort(
            key=str.casefold
        )

        return "\n".join(names)

    def _clear_details(self) -> None:
        self.name_label.setText(
            "Select a system"
        )

        self.id_label.clear()

        self.cores_value.setText("—")
        self.emulators_value.setText("—")
        self.frontends_value.setText("—")
