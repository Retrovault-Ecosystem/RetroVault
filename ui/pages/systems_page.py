from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
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
    """Browse platform metadata and relationships supplied by RVDB."""

    EMPTY = "Not currently recorded"

    def __init__(
        self,
        consumer: RVDBConsumer | None = None,
    ):
        super().__init__()

        self.consumer = consumer

        self.title_label = QLabel("Systems")
        self.subtitle_label = QLabel(
            "Platform knowledge from RVDB"
        )
        self.count_label = QLabel()

        self.system_list = QListWidget()

        self.name_label = QLabel(
            "Select a system"
        )
        self.id_label = QLabel()

        self.category_value = QLabel("—")
        self.manufacturer_value = QLabel("—")
        self.release_year_value = QLabel("—")
        self.generation_value = QLabel("—")
        self.media_value = QLabel("—")
        self.extensions_value = QLabel("—")
        self.aliases_value = QLabel("—")
        self.retroarch_value = QLabel("—")

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

        secondary_style = """
            font-size: 13px;
            color: #9aa0a6;
        """

        self.subtitle_label.setStyleSheet(
            secondary_style
        )
        self.count_label.setStyleSheet(
            secondary_style
        )
        self.status_label.setStyleSheet(
            secondary_style
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
            secondary_style
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

        details_layout.addSpacing(8)
        details_layout.addWidget(
            self._section_label(
                "Platform Information"
            )
        )

        info_grid = QGridLayout()
        info_grid.setHorizontalSpacing(24)
        info_grid.setVerticalSpacing(10)

        fields = [
            (
                "Category",
                self.category_value,
            ),
            (
                "Manufacturer",
                self.manufacturer_value,
            ),
            (
                "Release Year",
                self.release_year_value,
            ),
            (
                "Generation",
                self.generation_value,
            ),
            (
                "Media",
                self.media_value,
            ),
            (
                "File Extensions",
                self.extensions_value,
            ),
            (
                "Aliases",
                self.aliases_value,
            ),
            (
                "RetroArch",
                self.retroarch_value,
            ),
        ]

        for row, (
            label_text,
            value_label,
        ) in enumerate(fields):
            label = QLabel(label_text)

            label.setStyleSheet(
                """
                font-weight: 700;
                color: #b8b8b8;
                """
            )

            value_label.setWordWrap(True)
            value_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

            info_grid.addWidget(
                label,
                row,
                0,
                Qt.AlignmentFlag.AlignTop,
            )

            info_grid.addWidget(
                value_label,
                row,
                1,
            )

        info_grid.setColumnStretch(
            1,
            1,
        )

        details_layout.addLayout(
            info_grid
        )

        details_layout.addSpacing(12)
        details_layout.addWidget(
            self._section_label(
                "Emulation Relationships"
            )
        )

        details_layout.addWidget(
            self._relationship_label(
                "Supported Cores"
            )
        )
        details_layout.addWidget(
            self.cores_value
        )

        details_layout.addSpacing(6)

        details_layout.addWidget(
            self._relationship_label(
                "Standalone Emulators"
            )
        )
        details_layout.addWidget(
            self.emulators_value
        )

        details_layout.addSpacing(6)

        details_layout.addWidget(
            self._relationship_label(
                "Frontends"
            )
        )
        details_layout.addWidget(
            self.frontends_value
        )

        details_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
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
            font-size: 15px;
            font-weight: 700;
            """
        )

        return label

    @staticmethod
    def _relationship_label(
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
            item = QListWidgetItem(
                platform.get(
                    "name",
                    platform["id"],
                )
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

        self.category_value.setText(
            self._display_values(
                platform.get("category")
            )
        )

        self.manufacturer_value.setText(
            self._manufacturer_names(
                platform.get("manufacturer")
            )
        )

        self.release_year_value.setText(
            self._display_scalar(
                platform.get("release_year")
            )
        )

        self.generation_value.setText(
            self._display_scalar(
                platform.get("generation")
            )
        )

        self.media_value.setText(
            self._display_values(
                platform.get("media")
            )
        )

        self.extensions_value.setText(
            self._display_extensions(
                platform.get("extensions")
            )
        )

        self.aliases_value.setText(
            self._display_values(
                platform.get("aliases")
            )
        )

        metadata = platform.get(
            "metadata"
        )

        if not isinstance(
            metadata,
            dict,
        ):
            metadata = {}

        self.retroarch_value.setText(
            self._display_boolean(
                metadata.get(
                    "retroarch_supported"
                )
            )
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

    def _manufacturer_names(
        self,
        manufacturer_ids,
    ) -> str:
        if not manufacturer_ids:
            return self.EMPTY

        if self.consumer is None:
            return self.EMPTY

        names = []

        for entity_id in manufacturer_ids:
            entity = self.consumer.get_entity(
                entity_id
            )

            if entity is None:
                names.append(
                    entity_id
                )
            else:
                names.append(
                    entity.get(
                        "name",
                        entity_id,
                    )
                )

        return self._display_values(
            names
        )

    @classmethod
    def _display_values(
        cls,
        values,
    ) -> str:
        if values is None:
            return cls.EMPTY

        if isinstance(
            values,
            str,
        ):
            values = [values]

        values = [
            str(value)
            for value in values
            if value not in (
                None,
                "",
            )
        ]

        if not values:
            return cls.EMPTY

        values.sort(
            key=str.casefold
        )

        return ", ".join(values)

    @classmethod
    def _display_extensions(
        cls,
        values,
    ) -> str:
        if not values:
            return cls.EMPTY

        extensions = [
            f".{str(value).lstrip('.')}"
            for value in values
        ]

        extensions.sort(
            key=str.casefold
        )

        return ", ".join(
            extensions
        )

    @classmethod
    def _display_scalar(
        cls,
        value,
    ) -> str:
        if value is None or value == "":
            return cls.EMPTY

        return str(value)

    @classmethod
    def _display_boolean(
        cls,
        value,
    ) -> str:
        if value is True:
            return "Supported"

        if value is False:
            return "Not supported"

        return cls.EMPTY

    @classmethod
    def _entity_names(
        cls,
        entities: list[dict],
    ) -> str:
        if not entities:
            return cls.EMPTY

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

        for label in (
            self.category_value,
            self.manufacturer_value,
            self.release_year_value,
            self.generation_value,
            self.media_value,
            self.extensions_value,
            self.aliases_value,
            self.retroarch_value,
            self.cores_value,
            self.emulators_value,
            self.frontends_value,
        ):
            label.setText("—")
