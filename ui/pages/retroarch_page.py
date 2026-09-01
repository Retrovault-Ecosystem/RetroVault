from __future__ import annotations

from typing import Any

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

from services.rvdb import RVDBConsumer


class RetroArchPage(QWidget):
    """RVDB-backed RetroArch frontend and core browser."""

    FRONTEND_ID = "frontend.retroarch"

    def __init__(
        self,
        consumer: RVDBConsumer | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.consumer = consumer
        self._cores: list[dict[str, Any]] = []

        self._build_ui()
        self._connect_signals()
        self._load_retroarch()

    def _build_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(
            32,
            28,
            32,
            28,
        )
        main_layout.setSpacing(
            14
        )

        title = QLabel(
            "RetroArch"
        )
        title.setObjectName(
            "PageTitle"
        )

        subtitle = QLabel(
            "Frontend and core knowledge from RVDB"
        )
        subtitle.setObjectName(
            "PageSubtitle"
        )

        self.status_label = QLabel()
        self.status_label.setObjectName(
            "PageSubtitle"
        )
        self.status_label.setWordWrap(
            True
        )

        self.summary_label = QLabel()
        self.summary_label.setWordWrap(
            True
        )

        main_layout.addWidget(
            title
        )
        main_layout.addWidget(
            subtitle
        )
        main_layout.addWidget(
            self.summary_label
        )

        content_layout = QHBoxLayout()
        content_layout.setSpacing(
            20
        )

        browser_frame = QFrame()
        browser_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        browser_layout = QVBoxLayout(
            browser_frame
        )
        browser_layout.setContentsMargins(
            18,
            18,
            18,
            18,
        )
        browser_layout.setSpacing(
            10
        )

        cores_title = QLabel(
            "Available RVDB Cores"
        )
        cores_title.setObjectName(
            "SectionTitle"
        )

        self.core_count_label = QLabel()
        self.core_count_label.setObjectName(
            "PageSubtitle"
        )

        self.core_list = QListWidget()

        browser_layout.addWidget(
            cores_title
        )
        browser_layout.addWidget(
            self.core_count_label
        )
        browser_layout.addWidget(
            self.core_list,
            1,
        )

        details_frame = QFrame()
        details_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        detail_layout = QVBoxLayout(
            details_frame
        )
        detail_layout.setContentsMargins(
            22,
            22,
            22,
            22,
        )
        detail_layout.setSpacing(
            12
        )

        self.core_name_label = QLabel(
            "Select a core"
        )
        self.core_name_label.setStyleSheet(
            """
            font-size: 22px;
            font-weight: 700;
            """
        )

        self.core_id_label = QLabel()
        self.core_id_label.setObjectName(
            "PageSubtitle"
        )
        self.core_id_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        detail_layout.addWidget(
            self.core_name_label
        )
        detail_layout.addWidget(
            self.core_id_label
        )
        detail_layout.addSpacing(
            8
        )

        compatibility_title = QLabel(
            "Platform Compatibility"
        )
        compatibility_title.setObjectName(
            "SectionTitle"
        )

        detail_layout.addWidget(
            compatibility_title
        )

        self.platforms_label = QLabel(
            "Platforms"
        )
        self.playability_label = QLabel(
            "Playability"
        )
        self.evidence_label = QLabel(
            "Evidence Records"
        )

        for label in (
            self.platforms_label,
            self.playability_label,
            self.evidence_label,
        ):
            label.setStyleSheet(
                """
                font-weight: 700;
                color: #b8b8b8;
                """
            )

        self.platforms_value = QLabel(
            "No core selected."
        )
        self.playability_value = QLabel(
            "No core selected."
        )
        self.evidence_value = QLabel(
            "No core selected."
        )

        for value in (
            self.platforms_value,
            self.playability_value,
            self.evidence_value,
        ):
            value.setWordWrap(
                True
            )
            value.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

        self.details_grid = QGridLayout()
        self.details_grid.setHorizontalSpacing(
            28
        )
        self.details_grid.setVerticalSpacing(
            10
        )

        self.details_grid.addWidget(
            self.platforms_label,
            0,
            0,
            Qt.AlignmentFlag.AlignTop,
        )
        self.details_grid.addWidget(
            self.platforms_value,
            0,
            1,
        )

        self.details_grid.addWidget(
            self.playability_label,
            1,
            0,
            Qt.AlignmentFlag.AlignTop,
        )
        self.details_grid.addWidget(
            self.playability_value,
            1,
            1,
        )

        self.details_grid.addWidget(
            self.evidence_label,
            2,
            0,
            Qt.AlignmentFlag.AlignTop,
        )
        self.details_grid.addWidget(
            self.evidence_value,
            2,
            1,
        )

        self.details_grid.setColumnStretch(
            1,
            1,
        )

        detail_layout.addLayout(
            self.details_grid
        )

        detail_layout.addSpacing(
            12
        )

        frontend_title = QLabel(
            "Frontend Relationship"
        )
        frontend_title.setObjectName(
            "SectionTitle"
        )

        detail_layout.addWidget(
            frontend_title
        )

        self.frontends_label = QLabel(
            "Launched By"
        )
        self.frontends_label.setStyleSheet(
            """
            font-weight: 700;
            color: #b8b8b8;
            """
        )

        self.frontends_value = QLabel(
            "No core selected."
        )
        self.frontends_value.setWordWrap(
            True
        )
        self.frontends_value.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.frontend_grid = QGridLayout()
        self.frontend_grid.setHorizontalSpacing(
            28
        )

        self.frontend_grid.addWidget(
            self.frontends_label,
            0,
            0,
            Qt.AlignmentFlag.AlignTop,
        )
        self.frontend_grid.addWidget(
            self.frontends_value,
            0,
            1,
        )

        self.frontend_grid.setColumnStretch(
            1,
            1,
        )

        detail_layout.addLayout(
            self.frontend_grid
        )
        detail_layout.addStretch(
            1
        )

        detail_scroll = QScrollArea()
        detail_scroll.setWidgetResizable(
            True
        )
        detail_scroll.setFrameShape(
            QFrame.Shape.NoFrame
        )
        detail_scroll.setWidget(
            details_frame
        )

        content_layout.addWidget(
            browser_frame,
            1,
        )
        content_layout.addWidget(
            detail_scroll,
            2,
        )

        main_layout.addLayout(
            content_layout,
            1,
        )

        main_layout.addWidget(
            self.status_label
        )

    def _connect_signals(self) -> None:
        self.core_list.currentItemChanged.connect(
            self._core_selected
        )

    def _load_retroarch(self) -> None:
        self.core_list.clear()
        self._cores = []

        if self.consumer is None:
            self.status_label.setText(
                "RVDB unavailable"
            )
            self.summary_label.setText(
                "No RVDB consumer was supplied."
            )
            self.core_count_label.setText(
                "0 cores"
            )
            self._clear_details()
            return

        frontend = self.consumer.get_entity(
            self.FRONTEND_ID
        )

        if (
            frontend is None
            or frontend.get("type")
            != "frontend"
        ):
            self.status_label.setText(
                "RetroArch unavailable"
            )
            self.summary_label.setText(
                "The RVDB bundle does not contain "
                "the RetroArch frontend entity."
            )
            self.core_count_label.setText(
                "0 cores"
            )
            self._clear_details()
            return

        core_ids = (
            frontend.get(
                "relationships",
                {},
            )
            .get(
                "launches_core",
                [],
            )
        )

        cores = []

        for core_id in core_ids:
            core = self.consumer.get_entity(
                core_id
            )

            if (
                core is None
                or core.get("type")
                != "core"
            ):
                continue

            cores.append(core)

        cores.sort(
            key=lambda entity: (
                str(
                    entity.get(
                        "name",
                        "",
                    )
                ).casefold(),
                entity.get(
                    "id",
                    "",
                ),
            )
        )

        self._cores = cores

        frontend_name = frontend.get(
            "name",
            self.FRONTEND_ID,
        )

        self.status_label.setText(
            "RVDB bundle loaded successfully."
        )

        self.summary_label.setText(
            f"{frontend_name} launches "
            f"{len(cores)} RVDB cores."
        )

        self.core_count_label.setText(
            f"{len(cores)} cores"
        )

        for core in cores:
            item = QListWidgetItem(
                core.get(
                    "name",
                    core["id"],
                )
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                core["id"],
            )

            self.core_list.addItem(
                item
            )

        if cores:
            self.core_list.setCurrentRow(0)
        else:
            self._clear_details()

    def _core_selected(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        del previous

        if (
            current is None
            or self.consumer is None
        ):
            self._clear_details()
            return

        core_id = current.data(
            Qt.ItemDataRole.UserRole
        )

        core = self.consumer.get_entity(
            core_id
        )

        if core is None:
            self._clear_details()
            return

        self._show_core(
            core
        )

    def _show_core(
        self,
        core: dict[str, Any],
    ) -> None:
        if self.consumer is None:
            self._clear_details()
            return

        core_id = core["id"]

        self.core_name_label.setText(
            core.get(
                "name",
                core_id,
            )
        )
        self.core_id_label.setText(
            core_id
        )

        compatibility = [
            entity
            for entity
            in self.consumer.nodes.values()
            if (
                entity.get("type")
                == "compatibility"
                and entity.get("subject")
                == core_id
            )
        ]

        compatibility.sort(
            key=lambda entity: entity.get(
                "id",
                "",
            )
        )

        platform_names = []
        playability_values = []
        evidence_count = 0

        for record in compatibility:
            platform_id = record.get(
                "platform"
            )

            platform = (
                self.consumer.get_entity(
                    platform_id
                )
                if platform_id
                else None
            )

            platform_name = (
                platform.get(
                    "name",
                    platform_id,
                )
                if platform is not None
                else platform_id
            )

            if platform_name:
                platform_names.append(
                    str(platform_name)
                )

            playability = record.get(
                "playability"
            )

            if playability:
                playability_values.append(
                    str(playability)
                )

            evidence = record.get(
                "evidence",
                [],
            )

            if isinstance(evidence, list):
                evidence_count += len(
                    evidence
                )

        platform_names = sorted(
            set(platform_names),
            key=str.casefold,
        )

        playability_values = sorted(
            set(playability_values),
            key=str.casefold,
        )

        self.platforms_value.setText(
            "\n".join(platform_names)
            if platform_names
            else "No compatibility records."
        )

        self.playability_value.setText(
            "\n".join(playability_values)
            if playability_values
            else "Unknown"
        )

        self.evidence_value.setText(
            str(evidence_count)
        )

        frontends = (
            self.consumer.frontends_for_core(
                core_id
            )
        )

        frontend_names = sorted(
            {
                str(
                    frontend.get(
                        "name",
                        frontend["id"],
                    )
                )
                for frontend in frontends
            },
            key=str.casefold,
        )

        self.frontends_value.setText(
            "\n".join(frontend_names)
            if frontend_names
            else "None"
        )

    def _clear_details(self) -> None:
        self.core_name_label.setText(
            "Select a core"
        )
        self.core_id_label.clear()
        self.platforms_value.setText(
            "No core selected."
        )
        self.playability_value.setText(
            "No core selected."
        )
        self.evidence_value.setText(
            "No core selected."
        )
        self.frontends_value.setText(
            "No core selected."
        )
