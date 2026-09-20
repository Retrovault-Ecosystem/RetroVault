from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from services.cheats import (
    CheatCategory,
    CheatCode,
    CheatCodeType,
    CheatCollection,
    CheatService,
)


_CATEGORY_ORDER = tuple(
    CheatCategory
)


class CheatStudio(QDialog):
    """
    RetroVault's physical-edition-aware pre-launch Cheat Studio.

    The dialog works only with the selected launch-time Game copy.
    Canonical Library identity is never mutated.
    """

    def __init__(
        self,
        game,
        archive_member="",
        cheat_service=None,
        parent=None,
    ):
        super().__init__(parent)

        self.game = game
        self.archive_member = str(
            archive_member or ""
        )

        self.cheat_service = (
            cheat_service
            or CheatService()
        )

        self.collection = (
            self.cheat_service.discover(
                game,
                self.archive_member,
            )
        )

        self._result_cheats = []
        self._checkboxes = []
        self._launch_without_cheats = False

        self.setObjectName(
            "LibraryCheatStudio"
        )

        self.setWindowTitle(
            "RetroVault Cheat Studio"
        )

        self.setModal(True)
        self.setMinimumSize(
            760,
            600,
        )
        self.resize(
            900,
            720,
        )

        self._build_ui()
        self._refresh_catalog()

    @property
    def selected_cheats(self):
        return list(
            self._result_cheats
        )

    @property
    def launch_without_cheats(self):
        return self._launch_without_cheats

    @staticmethod
    def _type_title(code_type):
        if not isinstance(
            code_type,
            CheatCodeType,
        ):
            try:
                code_type = CheatCodeType(
                    str(code_type)
                )
            except ValueError:
                return str(code_type)

        titles = {
            CheatCodeType.RETROARCH:
                "RetroArch / libretro",
            CheatCodeType.GAME_GENIE:
                "Game Genie",
            CheatCodeType.GAMESHARK:
                "GameShark",
            CheatCodeType.ACTION_REPLAY:
                "Action Replay",
            CheatCodeType.PRO_ACTION_REPLAY:
                "Pro Action Replay",
            CheatCodeType.CODEBREAKER:
                "CodeBreaker",
            CheatCodeType.RAW:
                "Raw",
            CheatCodeType.CUSTOM:
                "Custom",
        }

        return titles[code_type]

    @staticmethod
    def _identity_line(
        collection: CheatCollection,
    ):
        identity = collection.identity

        parts = [
            identity.platform,
            identity.region,
            identity.language,
            identity.revision,
        ]

        parts = [
            str(value).strip()
            for value in parts
            if str(value).strip()
        ]

        return (
            " • ".join(parts)
            or "Physical game edition"
        )

    @staticmethod
    def _search_text(cheat):
        return " ".join(
            (
                cheat.name,
                cheat.category.value,
                cheat.code_type.value,
                cheat.code,
                cheat.source,
                cheat.compatibility_note,
            )
        ).casefold()

    def _build_ui(self):
        root = QVBoxLayout(self)

        root.setContentsMargins(
            24,
            22,
            24,
            22,
        )

        root.setSpacing(12)

        eyebrow = QLabel(
            "RETROVAULT CHEAT STUDIO"
        )
        eyebrow.setObjectName(
            "LibraryCheatEyebrow"
        )
        root.addWidget(eyebrow)

        title = QLabel(
            str(
                getattr(
                    self.game,
                    "name",
                    "Game",
                )
            )
        )
        title.setObjectName(
            "LibraryCheatTitle"
        )
        title.setWordWrap(True)
        root.addWidget(title)

        edition = QLabel(
            self._identity_line(
                self.collection
            )
        )
        edition.setObjectName(
            "LibraryCheatEdition"
        )
        root.addWidget(edition)

        warning = QLabel(
            "Cheats are matched to this exact physical edition. "
            "Codes for another revision, language, region, hack, "
            "or archive member may be incompatible."
        )
        warning.setObjectName(
            "LibraryCheatWarning"
        )
        warning.setWordWrap(True)
        root.addWidget(warning)

        search_row = QHBoxLayout()

        self.search = QLineEdit()
        self.search.setObjectName(
            "LibraryCheatSearch"
        )
        self.search.setPlaceholderText(
            "Search cheats, categories, types, or codes..."
        )
        self.search.setClearButtonEnabled(
            True
        )
        self.search.textChanged.connect(
            self._refresh_catalog
        )

        search_row.addWidget(
            self.search,
            1,
        )

        self.enable_all_button = QPushButton(
            "Enable All Compatible"
        )
        self.enable_all_button.setObjectName(
            "LibraryCheatEnableAll"
        )
        self.enable_all_button.clicked.connect(
            self._enable_all
        )
        search_row.addWidget(
            self.enable_all_button
        )

        self.disable_all_button = QPushButton(
            "Disable All"
        )
        self.disable_all_button.setObjectName(
            "LibraryCheatDisableAll"
        )
        self.disable_all_button.clicked.connect(
            self._disable_all
        )
        search_row.addWidget(
            self.disable_all_button
        )

        root.addLayout(
            search_row
        )

        utility_row = QHBoxLayout()

        self.manual_name = QLineEdit()
        self.manual_name.setObjectName(
            "LibraryCheatManualName"
        )
        self.manual_name.setPlaceholderText(
            "Custom cheat name"
        )

        self.manual_code = QLineEdit()
        self.manual_code.setObjectName(
            "LibraryCheatManualCode"
        )
        self.manual_code.setPlaceholderText(
            "Code"
        )

        self.manual_type = QComboBox()
        self.manual_type.setObjectName(
            "LibraryCheatManualType"
        )

        for code_type in CheatCodeType:
            self.manual_type.addItem(
                self._type_title(
                    code_type
                ),
                code_type,
            )

        self.add_button = QPushButton(
            "＋ Add Code"
        )
        self.add_button.setObjectName(
            "LibraryCheatAdd"
        )
        self.add_button.clicked.connect(
            self._add_manual
        )

        self.import_button = QPushButton(
            "Import .cht"
        )
        self.import_button.setObjectName(
            "LibraryCheatImport"
        )
        self.import_button.clicked.connect(
            self._import_file
        )

        utility_row.addWidget(
            self.manual_name,
            2,
        )
        utility_row.addWidget(
            self.manual_code,
            2,
        )
        utility_row.addWidget(
            self.manual_type,
            1,
        )
        utility_row.addWidget(
            self.add_button,
        )
        utility_row.addWidget(
            self.import_button,
        )

        root.addLayout(
            utility_row
        )

        self.feedback = QLabel()
        self.feedback.setObjectName(
            "LibraryCheatFeedback"
        )
        self.feedback.setWordWrap(True)
        self.feedback.hide()

        root.addWidget(
            self.feedback
        )

        self.scroll = QScrollArea()
        self.scroll.setObjectName(
            "LibraryCheatScroll"
        )
        self.scroll.setWidgetResizable(
            True
        )

        self.content = QWidget()
        self.content.setObjectName(
            "LibraryCheatContent"
        )

        self.catalog_layout = QVBoxLayout(
            self.content
        )
        self.catalog_layout.setContentsMargins(
            0,
            0,
            0,
            0,
        )
        self.catalog_layout.setSpacing(
            10
        )

        self.scroll.setWidget(
            self.content
        )

        root.addWidget(
            self.scroll,
            1,
        )

        footer = QHBoxLayout()

        self.cancel_button = QPushButton(
            "Cancel"
        )
        self.cancel_button.setObjectName(
            "LibraryCheatCancel"
        )
        self.cancel_button.clicked.connect(
            self.reject
        )

        self.without_button = QPushButton(
            "Continue Without Cheats"
        )
        self.without_button.setObjectName(
            "LibraryCheatWithout"
        )
        self.without_button.clicked.connect(
            self._accept_without
        )

        self.launch_button = QPushButton(
            "▶ Launch With Selected Cheats"
        )
        self.launch_button.setObjectName(
            "LibraryCheatLaunch"
        )
        self.launch_button.clicked.connect(
            self._accept_selected
        )

        footer.addWidget(
            self.cancel_button
        )
        footer.addStretch(1)
        footer.addWidget(
            self.without_button
        )
        footer.addWidget(
            self.launch_button
        )

        root.addLayout(
            footer
        )

    def _clear_catalog(self):
        while self.catalog_layout.count():
            item = (
                self.catalog_layout
                .takeAt(0)
            )

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

        self._checkboxes = []

    def _filtered_cheats(self):
        query = (
            self.search.text()
            .strip()
            .casefold()
        )

        if not query:
            return list(
                self.collection.cheats
            )

        return [
            cheat
            for cheat
            in self.collection.cheats
            if query in self._search_text(
                cheat
            )
        ]

    def _refresh_catalog(self):
        self._clear_catalog()

        visible = (
            self._filtered_cheats()
        )

        if not visible:
            empty = QLabel(
                "No matching cheats are available for this edition. "
                "You can add a custom code, import a .cht file, "
                "or continue without cheats."
            )
            empty.setObjectName(
                "LibraryCheatEmpty"
            )
            empty.setWordWrap(True)

            self.catalog_layout.addWidget(
                empty
            )
            self.catalog_layout.addStretch(
                1
            )
            return

        grouped = {}

        for cheat in visible:
            grouped.setdefault(
                cheat.category,
                [],
            ).append(
                cheat
            )

        for category in _CATEGORY_ORDER:
            cheats = grouped.get(
                category,
                [],
            )

            if not cheats:
                continue

            group = QFrame()
            group.setObjectName(
                "LibraryCheatGroup"
            )

            group_layout = QVBoxLayout(
                group
            )
            group_layout.setContentsMargins(
                14,
                12,
                14,
                12,
            )
            group_layout.setSpacing(
                8
            )

            heading = QLabel(
                category.value
            )
            heading.setObjectName(
                "LibraryCheatGroupTitle"
            )

            group_layout.addWidget(
                heading
            )

            for cheat in cheats:
                row = QFrame()
                row.setObjectName(
                    "LibraryCheatRow"
                )

                row_layout = QVBoxLayout(
                    row
                )
                row_layout.setContentsMargins(
                    10,
                    9,
                    10,
                    9,
                )
                row_layout.setSpacing(
                    4
                )

                checkbox = QCheckBox(
                    cheat.name
                )
                checkbox.setObjectName(
                    "LibraryCheatChoice"
                )
                checkbox.setChecked(
                    bool(
                        cheat.enabled
                        and cheat.compatible
                    )
                )
                checkbox.setEnabled(
                    bool(
                        cheat.compatible
                    )
                )
                checkbox.setProperty(
                    "cheatRecord",
                    cheat,
                )

                row_layout.addWidget(
                    checkbox
                )

                details = [
                    self._type_title(
                        cheat.code_type
                    ),
                    cheat.code,
                ]

                if cheat.source:
                    details.append(
                        cheat.source
                    )

                detail = QLabel(
                    " • ".join(
                        value
                        for value in details
                        if value
                    )
                )
                detail.setObjectName(
                    "LibraryCheatDetail"
                )
                detail.setWordWrap(True)

                row_layout.addWidget(
                    detail
                )

                if not cheat.compatible:
                    note = QLabel(
                        cheat.compatibility_note
                        or "Not compatible with this edition."
                    )
                    note.setObjectName(
                        "LibraryCheatIncompatible"
                    )
                    note.setWordWrap(True)
                    row_layout.addWidget(
                        note
                    )

                group_layout.addWidget(
                    row
                )

                self._checkboxes.append(
                    checkbox
                )

            self.catalog_layout.addWidget(
                group
            )

        self.catalog_layout.addStretch(
            1
        )

    def _apply_checkbox_state(self):
        state = {
            id(
                checkbox.property(
                    "cheatRecord"
                )
            ): checkbox.isChecked()
            for checkbox
            in self._checkboxes
        }

        self.collection.cheats = [
            replace(
                cheat,
                enabled=(
                    state.get(
                        id(cheat),
                        cheat.enabled,
                    )
                    if cheat.compatible
                    else False
                ),
            )
            for cheat in self.collection.cheats
        ]

    def _enable_all(self):
        self._apply_checkbox_state()

        self.collection.cheats = (
            self.cheat_service
            .enable_all_compatible(
                self.collection.cheats
            )
        )

        self._refresh_catalog()

    def _disable_all(self):
        self._apply_checkbox_state()

        self.collection.cheats = (
            self.cheat_service
            .disable_all(
                self.collection.cheats
            )
        )

        self._refresh_catalog()

    def _show_feedback(
        self,
        message,
    ):
        self.feedback.setText(
            str(message)
        )
        self.feedback.show()

    def _add_manual(self):
        name = (
            self.manual_name.text()
            .strip()
        )
        code = (
            self.manual_code.text()
            .strip()
        )

        code_type = (
            self.manual_type.currentData()
        )

        try:
            cheat = (
                self.cheat_service
                .manual_cheat(
                    name=name,
                    code=code,
                    code_type=code_type,
                    category=(
                        CheatCategory.CUSTOM
                    ),
                )
            )
        except (
            ValueError,
            TypeError,
        ) as exc:
            self._show_feedback(
                exc
            )
            return

        cheat = replace(
            cheat,
            enabled=True,
        )

        self.collection.cheats.append(
            cheat
        )

        self.manual_name.clear()
        self.manual_code.clear()
        self.feedback.hide()

        self._refresh_catalog()

    def _import_file(self):
        path, _ = (
            QFileDialog.getOpenFileName(
                self,
                "Import RetroArch Cheat File",
                "",
                "RetroArch Cheat Files (*.cht)",
            )
        )

        if not path:
            return

        try:
            persisted = (
                self.cheat_service
                .import_file(
                    path,
                    self.collection.identity,
                )
            )

            imported = (
                self.cheat_service
                .discover(
                    self.game,
                    self.archive_member,
                )
            )
        except (
            OSError,
            ValueError,
        ) as exc:
            self._show_feedback(
                f"Unable to import cheat file: {exc}"
            )
            return

        self.collection = imported

        self._show_feedback(
            "Imported: "
            + Path(
                persisted
            ).name
        )

        self._refresh_catalog()

    def _accept_without(self):
        self._launch_without_cheats = True
        self._result_cheats = []
        self.accept()

    def _accept_selected(self):
        self._apply_checkbox_state()

        self._launch_without_cheats = False
        self._result_cheats = [
            cheat
            for cheat
            in self.collection.cheats
            if (
                cheat.enabled
                and cheat.compatible
            )
        ]

        self.accept()

    @classmethod
    def choose(
        cls,
        game,
        archive_member="",
        cheat_service=None,
        parent=None,
    ):
        dialog = cls(
            game=game,
            archive_member=archive_member,
            cheat_service=cheat_service,
            parent=parent,
        )

        if (
            dialog.exec()
            != QDialog.DialogCode.Accepted
        ):
            return None

        return dialog.selected_cheats
