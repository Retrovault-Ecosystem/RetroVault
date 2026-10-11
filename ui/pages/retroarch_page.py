from __future__ import annotations

from html import escape
from urllib.parse import urlsplit

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QTextBrowser,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from services.rvdb import RVDBService
from services.rvdb.models import RVDBCoreView


class RetroArchPage(QWidget):
    """RVDB-backed RetroArch frontend and core browser."""

    FRONTEND_ID = "frontend.retroarch"

    def __init__(
        self,
        service: RVDBService | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.service = service
        self._cores: list[RVDBCoreView] = []

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
            "RetroArchTitle"
        )

        subtitle = QLabel(
            "Frontend and core knowledge from RVDB"
        )
        subtitle.setObjectName(
            "RetroArchSubtitle"
        )

        self.status_label = QLabel()
        self.status_label.setObjectName(
            "RetroArchStatus"
        )
        self.status_label.setWordWrap(
            True
        )

        self.summary_label = QLabel()
        self.summary_label.setObjectName(
            "RetroArchSummary"
        )
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
        browser_frame.setObjectName(
            "RetroArchBrowserPanel"
        )
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
            "Known RVDB Cores"
        )
        cores_title.setObjectName(
            "RetroArchSectionTitle"
        )

        self.core_count_label = QLabel()
        self.core_count_label.setObjectName(
            "RetroArchCoreCount"
        )

        self.core_list = QListWidget()
        self.core_list.setObjectName(
            "RetroArchCoreList"
        )

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
        details_frame.setObjectName(
            "RetroArchDetailsPanel"
        )
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
        self.core_name_label.setObjectName(
            "RetroArchCoreName"
        )

        self.core_id_label = QLabel()
        self.core_id_label.setObjectName(
            "RetroArchCoreId"
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
            "RetroArchSectionTitle"
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
            label.setObjectName(
                "RetroArchFieldLabel"
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
            value.setObjectName(
                "RetroArchFieldValue"
            )
            value.setWordWrap(
                True
            )
            value.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

        self.compatibility_details = QTextBrowser()
        self.compatibility_details.setObjectName("RetroArchCompatibilityDetails")
        self.compatibility_details.setOpenExternalLinks(True)
        self.compatibility_details.setMinimumHeight(280)
        detail_layout.addWidget(self.compatibility_details)

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
            "RetroArchSectionTitle"
        )

        detail_layout.addWidget(
            frontend_title
        )

        self.frontends_label = QLabel(
            "Launched By"
        )
        self.frontends_label.setObjectName(
            "RetroArchFieldLabel"
        )

        self.frontends_value = QLabel(
            "No core selected."
        )
        self.frontends_value.setObjectName(
            "RetroArchFieldValue"
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

    @staticmethod
    def _core_display_name(name: str) -> str:
        """Return polished UI text without changing RVDB identity."""
        if name.casefold() == "bsnes":
            return "Bsnes"

        return name

    def _load_retroarch(self) -> None:
        self.core_list.clear()
        self._cores = []

        if self.service is None:
            self.status_label.setText(
                "RVDB unavailable"
            )
            self.summary_label.setText(
                "No RVDB service was supplied."
            )
            self.core_count_label.setText(
                "0 cores"
            )
            self._clear_details()
            return

        view = self.service.retroarch_view(
            self.FRONTEND_ID
        )

        if view is None:
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

        self._cores = list(
            view.cores
        )

        self.status_label.setText(
            "RVDB bundle loaded successfully."
        )

        self.summary_label.setText(
            f"RVDB lists {len(self._cores)} cores for {view.frontend.name}."
        )

        self.core_count_label.setText(
            f"{len(self._cores)} cores"
        )

        for core in self._cores:
            item = QListWidgetItem(
                self._core_display_name(
                    core.name
                )
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                core.id,
            )

            self.core_list.addItem(
                item
            )

        if self._cores:
            self.core_list.setCurrentRow(0)
        else:
            self._clear_details()

    def _core_selected(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        del previous

        if current is None:
            self._clear_details()
            return

        core_id = current.data(
            Qt.ItemDataRole.UserRole
        )

        core = next(
            (
                candidate
                for candidate
                in self._cores
                if candidate.id == core_id
            ),
            None,
        )

        if core is None:
            self._clear_details()
            return

        self._show_core(
            core
        )

    def _show_core(
        self,
        core: RVDBCoreView,
    ) -> None:
        self._show_compatibility(core)
        self.core_name_label.setText(
            self._core_display_name(
                core.name
            )
        )

        self.core_id_label.setText(
            core.id
        )

        self.platforms_value.setText(
            "\n".join(
                core.platforms
            )
            if core.platforms
            else "No compatibility records."
        )

        self.playability_value.setText(
            "\n".join(
                core.playability
            )
            if core.playability
            else "Unknown"
        )

        self.evidence_value.setText(
            str(
                core.evidence_count
            )
        )

        self.frontends_value.setText(
            "\n".join(
                core.frontends
            )
            if core.frontends
            else "None"
        )

    def _show_compatibility(self, core):
        sections = ["<p><b>RVDB knowledge — not local readiness</b><br>"
                    "Known means recorded here. Available means a usable local core resolves. "
                    "Configured means local requirements are satisfied. Qualified means a stated "
                    "test scope passed. Supported means RetroVault maintains that workflow. "
                    "This knowledge browser does not establish those local or product states. "
                    "Playable is a platform-level claim, not an every-game guarantee.</p>"]
        for claim in core.compatibility:
            sections.append(f"<h3>{escape(claim.platform_name)}</h3><p>"
                            f"Claim: {escape(claim.playability)}<br>"
                            f"Version: {escape(claim.version or 'Not specified')}<br>"
                            f"{escape(claim.notes or 'No scope notes supplied.')}<br>"
                            f"Record: {escape(claim.id)}</p>")
            for evidence in claim.evidence:
                url = evidence.url
                try:
                    parsed = urlsplit(url)
                    safe = parsed.scheme in ('http', 'https') and bool(parsed.netloc)
                except ValueError:
                    safe = False
                link = f'<a href="{escape(url, quote=True)}">{escape(url)}</a>' if safe else escape(url)
                sections.append(f"<p><b>{escape(evidence.source or 'Unnamed source')}</b><br>"
                                f"{link}<br>Checked: {escape(evidence.checked_at or 'Not supplied')}<br>"
                                f"Evidence version: {escape(evidence.version or 'Not specified')}<br>"
                                f"{escape(evidence.notes)}</p>")
            if not claim.evidence:
                sections.append('<p>No supporting evidence supplied.</p>')
        if not core.compatibility:
            sections.append('<p>No compatibility records. Missing knowledge is not a failure verdict.</p>')
        self.compatibility_details.setHtml(''.join(sections))

    def _clear_details(self) -> None:
        self.compatibility_details.setPlainText("Select a core to inspect RVDB claims and evidence.")
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
