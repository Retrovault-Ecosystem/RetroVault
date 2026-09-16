from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QScrollArea,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from services.rvdb import (
    RVDBError,
    RVDBService,
)


class SystemsPage(QWidget):
    """Browse platform metadata and relationships supplied by RVDB."""

    library_requested = pyqtSignal(str)
    library_favorites_requested = pyqtSignal(str)
    library_recent_requested = pyqtSignal(str)
    library_collections_requested = pyqtSignal(str)

    EMPTY = "Not currently recorded"

    def __init__(
        self,
        service: RVDBService | None = None,
        games_provider=None,
        recent_provider=None,
    ):
        super().__init__()

        self.service = service
        self.games_provider = games_provider
        self.recent_provider = recent_provider

        self.title_label = QLabel("Systems")
        self.subtitle_label = QLabel(
            "Platform knowledge from RVDB"
        )
        self.count_label = QLabel()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Search systems..."
        )

        self.category_filter = QComboBox()
        self.category_filter.addItem(
            "All Categories"
        )

        self.system_list = QListWidget()

        self._platforms = []

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

        self.library_games_value = QLabel("—")
        self.library_favorites_value = QLabel("—")
        self.library_recent_value = QLabel("—")
        self.library_collections_value = QLabel("—")

        self.view_library_button = QPushButton(
            "View Games in Library"
        )
        self.view_library_button.setEnabled(
            False
        )

        self.view_favorites_button = QPushButton(
            "View Favorites in Library"
        )
        self.view_favorites_button.setEnabled(
            False
        )

        self.view_recent_button = QPushButton(
            "View Recently Played in Library"
        )
        self.view_recent_button.setEnabled(
            False
        )

        self.view_collections_button = QPushButton(
            "View Collections with Games"
        )
        self.view_collections_button.setEnabled(
            False
        )

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

        browser_controls = QHBoxLayout()
        browser_controls.setSpacing(12)

        browser_controls.addWidget(
            self.search_input,
            2,
        )
        browser_controls.addWidget(
            self.category_filter,
            1,
        )

        main_layout.addLayout(
            browser_controls
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

        details_layout.addSpacing(12)
        details_layout.addWidget(
            self._section_label(
                "Local Library"
            )
        )

        library_grid = QGridLayout()
        library_grid.setHorizontalSpacing(24)
        library_grid.setVerticalSpacing(10)

        for row, (
            label_text,
            value_label,
        ) in enumerate(
            (
                (
                    "Games",
                    self.library_games_value,
                ),
                (
                    "Favorites",
                    self.library_favorites_value,
                ),
                (
                    "Recently Played",
                    self.library_recent_value,
                ),
                (
                    "Collections",
                    self.library_collections_value,
                ),
            )
        ):
            label = QLabel(label_text)
            label.setStyleSheet(
                """
                font-weight: 700;
                color: #b8b8b8;
                """
            )

            value_label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )

            library_grid.addWidget(
                label,
                row,
                0,
                Qt.AlignmentFlag.AlignTop,
            )
            library_grid.addWidget(
                value_label,
                row,
                1,
            )

        library_grid.setColumnStretch(
            1,
            1,
        )

        details_layout.addLayout(
            library_grid
        )

        details_layout.addWidget(
            self.view_library_button
        )
        details_layout.addWidget(
            self.view_favorites_button
        )
        details_layout.addWidget(
            self.view_recent_button
        )

        details_layout.addWidget(
            self.view_collections_button
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

        self.search_input.textChanged.connect(
            self._apply_filters
        )

        self.category_filter.currentTextChanged.connect(
            self._apply_filters
        )

        self.view_library_button.clicked.connect(
            self._request_library
        )

        self.view_favorites_button.clicked.connect(
            self._request_library_favorites
        )

        self.view_recent_button.clicked.connect(
            self._request_library_recent
        )

        self.view_collections_button.clicked.connect(
            self._request_library_collections
        )

    def _load_systems(self) -> None:
        self.system_list.clear()
        self.category_filter.clear()
        self.category_filter.addItem(
            "All Categories"
        )
        self._platforms = []

        if self.service is None:
            self.count_label.setText(
                "RVDB unavailable"
            )
            self.status_label.setText(
                "No RVDB service was supplied."
            )
            return

        platforms = list(
            self.service.platforms()
        )

        self._platforms = platforms

        categories = set()

        for platform in platforms:
            values = platform.categories

            for value in values:
                if value not in (
                    None,
                    "",
                ):
                    categories.add(
                        str(value)
                    )

        for category in sorted(
            categories,
            key=str.casefold,
        ):
            self.category_filter.addItem(
                category
            )

        self.status_label.setText(
            "RVDB bundle loaded successfully."
        )

        self._apply_filters()

    def _apply_filters(self) -> None:
        if self.service is None:
            return

        search_text = (
            self.search_input.text()
            .strip()
            .casefold()
        )

        selected_category = (
            self.category_filter
            .currentText()
        )

        selected_id = None
        current = self.system_list.currentItem()

        if current is not None:
            selected_id = current.data(
                Qt.ItemDataRole.UserRole
            )

        matches = []

        for platform in self._platforms:
            name = platform.name

            entity_id = platform.id

            aliases = (
                platform.aliases
                or []
            )

            if isinstance(aliases, str):
                aliases = [aliases]

            searchable = [
                name,
                entity_id,
                *[
                    str(alias)
                    for alias in aliases
                ],
            ]

            if (
                search_text
                and not any(
                    search_text
                    in value.casefold()
                    for value in searchable
                )
            ):
                continue

            categories = (
                platform.categories
                or []
            )

            if isinstance(
                categories,
                str,
            ):
                categories = [
                    categories
                ]

            if (
                selected_category
                != "All Categories"
                and selected_category
                not in categories
            ):
                continue

            matches.append(
                platform
            )

        self.system_list.clear()

        selected_row = None

        for row, platform in enumerate(
            matches
        ):
            item = QListWidgetItem(
                platform.name
            )

            item.setData(
                Qt.ItemDataRole.UserRole,
                platform.id,
            )

            self.system_list.addItem(
                item
            )

            if (
                platform.id
                == selected_id
            ):
                selected_row = row

        total = len(
            self._platforms
        )
        visible = len(matches)

        if (
            not search_text
            and selected_category
            == "All Categories"
        ):
            self.count_label.setText(
                f"{total} platforms"
            )
        else:
            self.count_label.setText(
                f"{visible} of {total} platforms"
            )

        if matches:
            self.system_list.setCurrentRow(
                selected_row
                if selected_row is not None
                else 0
            )
        else:
            self._clear_details()

    def _system_selected(
        self,
        current: QListWidgetItem | None,
        previous: QListWidgetItem | None,
    ) -> None:
        del previous

        if current is None:
            self._clear_details()
            return

        if self.service is None:
            self._clear_details()
            return

        platform_id = current.data(
            Qt.ItemDataRole.UserRole
        )

        try:
            view = self.service.platform_view(
                platform_id
            )
        except RVDBError as exc:
            self._clear_details()
            self.status_label.setText(
                str(exc)
            )
            return

        platform = view.platform

        self.name_label.setText(
            platform.name
        )
        self.id_label.setText(
            platform.id
        )

        self.category_value.setText(
            self._display_values(
                platform.categories
            )
        )

        self.manufacturer_value.setText(
            self._entity_names(
                platform.manufacturers
            )
        )

        self.release_year_value.setText(
            self._display_scalar(
                platform.release_year
            )
        )

        self.generation_value.setText(
            self._display_scalar(
                platform.generation
            )
        )

        self.media_value.setText(
            self._display_values(
                platform.media
            )
        )

        self.extensions_value.setText(
            self._display_extensions(
                platform.extensions
            )
        )

        self.aliases_value.setText(
            self._display_values(
                platform.aliases
            )
        )

        self.retroarch_value.setText(
            self._display_boolean(
                platform.retroarch_supported
            )
        )

        self.cores_value.setText(
            self._entity_names(
                view.cores
            )
        )
        self.emulators_value.setText(
            self._entity_names(
                view.emulators
            )
        )
        self.frontends_value.setText(
            self._entity_names(
                view.frontends
            )
        )

        self._show_library_counts(
            platform.id
        )

        self.status_label.setText(
            "Showing live data from the "
            "local RVDB development bundle."
        )

    def _request_library(self) -> None:
        current = self.system_list.currentItem()

        if current is None:
            return

        platform_id = current.data(
            Qt.ItemDataRole.UserRole
        )

        if not platform_id:
            return

        self.library_requested.emit(
            str(platform_id)
        )

    def _request_library_favorites(self) -> None:
        current = self.system_list.currentItem()

        if current is None:
            return

        platform_id = current.data(
            Qt.ItemDataRole.UserRole
        )

        if not platform_id:
            return

        self.library_favorites_requested.emit(
            str(platform_id)
        )

    def _request_library_recent(self) -> None:
        current = self.system_list.currentItem()

        if current is None:
            return

        platform_id = current.data(
            Qt.ItemDataRole.UserRole
        )

        if not platform_id:
            return

        self.library_recent_requested.emit(
            str(platform_id)
        )

    def _request_library_collections(self) -> None:
        current = self.system_list.currentItem()

        if current is None:
            return

        platform_id = current.data(
            Qt.ItemDataRole.UserRole
        )

        if not platform_id:
            return

        self.library_collections_requested.emit(
            str(platform_id)
        )

    def refresh_page(self) -> None:
        current = (
            self.system_list.currentItem()
        )

        if current is None:
            return

        platform_id = current.data(
            Qt.ItemDataRole.UserRole
        )

        if not platform_id:
            return

        self._show_library_counts(
            str(platform_id)
        )

    def _show_library_counts(
        self,
        platform_id: str,
    ) -> None:
        if self.games_provider is None:
            self.library_games_value.setText(
                self.EMPTY
            )
            self.library_favorites_value.setText(
                self.EMPTY
            )
            self.library_recent_value.setText(
                self.EMPTY
            )
            self.library_collections_value.setText(
                self.EMPTY
            )
            self.view_library_button.setEnabled(
                False
            )
            self.view_favorites_button.setEnabled(
                False
            )
            self.view_recent_button.setEnabled(
                False
            )
            self.view_collections_button.setEnabled(
                False
            )
            return

        try:
            games = list(
                self.games_provider()
            )
        except Exception:
            self.library_games_value.setText(
                self.EMPTY
            )
            self.library_favorites_value.setText(
                self.EMPTY
            )
            self.library_recent_value.setText(
                self.EMPTY
            )
            self.library_collections_value.setText(
                self.EMPTY
            )
            self.view_library_button.setEnabled(
                False
            )
            self.view_favorites_button.setEnabled(
                False
            )
            self.view_recent_button.setEnabled(
                False
            )
            self.view_collections_button.setEnabled(
                False
            )
            return

        matching = [
            game
            for game in games
            if str(
                getattr(
                    game,
                    "rvdb_platform_id",
                    "",
                )
                or ""
            )
            == platform_id
        ]

        self.library_games_value.setText(
            str(
                len(matching)
            )
        )

        self.view_library_button.setEnabled(
            bool(matching)
        )

        collection_names_provider = getattr(
            self,
            "collection_names_provider",
            None,
        )
        collection_games_provider = getattr(
            self,
            "collection_games_provider",
            None,
        )

        collection_count = 0

        if (
            collection_names_provider is not None
            and collection_games_provider is not None
        ):
            try:
                for collection_name in (
                    collection_names_provider()
                ):
                    collection_games = list(
                        collection_games_provider(
                            collection_name
                        )
                    )

                    if any(
                        str(
                            getattr(
                                game,
                                "rvdb_platform_id",
                                "",
                            )
                            or ""
                        )
                        == platform_id
                        for game in collection_games
                    ):
                        collection_count += 1
            except Exception:
                collection_count = 0

        self.library_collections_value.setText(
            str(collection_count)
        )
        self.view_collections_button.setEnabled(
            collection_count > 0
        )

        favorite_count = sum(
            bool(
                getattr(
                    game,
                    "favorite",
                    False,
                )
            )
            for game in matching
        )

        self.library_favorites_value.setText(
            str(favorite_count)
        )

        self.view_favorites_button.setEnabled(
            favorite_count > 0
        )

        if self.recent_provider is None:
            self.library_recent_value.setText(
                self.EMPTY
            )
            self.view_recent_button.setEnabled(
                False
            )
            return

        try:
            recent_identities = {
                str(identity)
                for identity in self.recent_provider()
            }
        except Exception:
            self.library_recent_value.setText(
                self.EMPTY
            )
            self.view_recent_button.setEnabled(
                False
            )
            return

        recent_count = sum(
            str(
                getattr(
                    game,
                    "rom",
                    "",
                )
                or ""
            )
            in recent_identities
            for game in matching
        )

        self.library_recent_value.setText(
            str(recent_count)
        )
        self.view_recent_button.setEnabled(
            recent_count > 0
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
        entities,
    ) -> str:
        if not entities:
            return cls.EMPTY

        names = [
            entity.name
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
            self.library_games_value,
            self.library_favorites_value,
            self.library_recent_value,
        ):
            label.setText("—")

        self.view_library_button.setEnabled(
            False
        )
        self.view_favorites_button.setEnabled(
            False
        )
        self.view_recent_button.setEnabled(
            False
        )
        self.view_collections_button.setEnabled(
            False
        )
