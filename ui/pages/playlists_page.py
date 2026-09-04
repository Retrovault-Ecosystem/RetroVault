from PyQt6.QtCore import Qt
from ui.library.details.game_details import (
    GameDetails,
)

from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PlaylistsPage(QWidget):
    """Create and manage manual game collections."""

    def __init__(
        self,
        controller,
        rvdb_service=None,
    ):
        super().__init__()

        self.controller = controller

        self.title_label = QLabel(
            "Playlists"
        )
        self.title_label.setObjectName(
            "PageTitle"
        )

        self.subtitle_label = QLabel(
            "Organize your library into manual "
            "collections."
        )
        self.subtitle_label.setObjectName(
            "PageSubtitle"
        )

        self.collection_list = QListWidget()
        self.game_list = QListWidget()

        self.create_button = QPushButton(
            "New Collection"
        )
        self.rename_button = QPushButton(
            "Rename"
        )
        self.delete_button = QPushButton(
            "Delete"
        )

        self.remove_game_button = QPushButton(
            "Remove Selected Game"
        )
        self.remove_game_button.setEnabled(
            False
        )

        self._displayed_games = []

        self.details = GameDetails(
            rvdb_service=rvdb_service,
            favorite_handler=getattr(
                controller,
                "set_favorite",
                None,
            ),
            played_handler=getattr(
                controller,
                "record_played",
                None,
            ),
            collection_names_provider=getattr(
                controller,
                "collection_names",
                None,
            ),
            collection_add_handler=getattr(
                controller,
                "add_to_collection",
                None,
            ),
        )

        self.collection_title = QLabel(
            "Select a collection"
        )
        self.collection_title.setObjectName(
            "SectionTitle"
        )

        self.status_label = QLabel()

        self._build_ui()
        self._connect_signals()
        self.refresh_collections()

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

        actions = QHBoxLayout()
        actions.setSpacing(8)

        actions.addWidget(
            self.create_button
        )
        actions.addWidget(
            self.rename_button
        )
        actions.addWidget(
            self.delete_button
        )
        actions.addStretch(1)

        layout.addLayout(actions)

        content = QHBoxLayout()
        content.setSpacing(20)

        collection_frame = QFrame()
        collection_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        collection_layout = QVBoxLayout(
            collection_frame
        )
        collection_layout.addWidget(
            QLabel("Collections")
        )
        collection_layout.addWidget(
            self.collection_list
        )

        games_frame = QFrame()
        games_frame.setFrameShape(
            QFrame.Shape.StyledPanel
        )

        games_layout = QVBoxLayout(
            games_frame
        )
        games_layout.addWidget(
            self.collection_title
        )
        games_layout.addWidget(
            self.game_list
        )
        games_layout.addWidget(
            self.remove_game_button
        )

        content.addWidget(
            collection_frame,
            1,
        )
        content.addWidget(
            games_frame,
            1,
        )
        content.addWidget(
            self.details,
            2,
        )

        layout.addLayout(
            content,
            1,
        )
        layout.addWidget(
            self.status_label
        )

        self.collection_list.setMinimumWidth(
            260
        )

        self.status_label.setStyleSheet(
            "color: #9aa0a6;"
        )

    def _connect_signals(self):
        self.collection_list.currentTextChanged.connect(
            self.show_collection
        )
        self.create_button.clicked.connect(
            self.create_collection
        )
        self.rename_button.clicked.connect(
            self.rename_collection
        )
        self.delete_button.clicked.connect(
            self.delete_collection
        )
        self.game_list.currentRowChanged.connect(
            self._update_game_action
        )
        self.game_list.currentRowChanged.connect(
            self._show_selected_game
        )
        self.remove_game_button.clicked.connect(
            self.remove_selected_game
        )

    def selected_collection(self):
        item = self.collection_list.currentItem()

        if item is None:
            return None

        return item.text()

    def refresh_collections(
        self,
        select_name=None,
    ):
        names = list(
            self.controller.collection_names()
        )

        self.collection_list.blockSignals(
            True
        )

        try:
            self.collection_list.clear()
            self.collection_list.addItems(
                names
            )

            target = (
                select_name
                if select_name in names
                else (
                    names[0]
                    if names
                    else None
                )
            )

            if target is not None:
                matches = (
                    self.collection_list.findItems(
                        target,
                        Qt.MatchFlag.MatchExactly,
                    )
                )

                if matches:
                    self.collection_list.setCurrentItem(
                        matches[0]
                    )
        finally:
            self.collection_list.blockSignals(
                False
            )

        if names:
            self.show_collection(
                self.selected_collection()
            )
        else:
            self.collection_title.setText(
                "No collections yet"
            )
            self.game_list.clear()
            self.status_label.setText(
                "Create a collection to begin."
            )

        self._update_actions()

    def _update_actions(self):
        enabled = (
            self.selected_collection()
            is not None
        )

        self.rename_button.setEnabled(
            enabled
        )
        self.delete_button.setEnabled(
            enabled
        )

    def show_collection(
        self,
        name,
    ):
        self.game_list.clear()
        self._displayed_games = []
        self.details.clear_game()
        self._update_game_action()

        if not name:
            self.collection_title.setText(
                "Select a collection"
            )
            self.status_label.clear()
            self._update_actions()
            return

        games = list(
            self.controller.collection_games(
                name
            )
        )

        self._displayed_games = games

        self.collection_title.setText(
            name
        )

        for game in games:
            platform = getattr(
                game,
                "platform",
                "",
            )

            label = game.name

            if platform:
                label = (
                    f"{game.name} — {platform}"
                )

            self.game_list.addItem(
                label
            )

        count = len(games)

        self.status_label.setText(
            (
                "1 game"
                if count == 1
                else f"{count} games"
            )
        )

        self._update_actions()

    def _warning(
        self,
        message,
    ):
        QMessageBox.warning(
            self,
            "Playlists",
            str(message),
        )

    def create_collection(self):
        name, accepted = QInputDialog.getText(
            self,
            "New Collection",
            "Collection name:",
        )

        if not accepted:
            return

        try:
            created = (
                self.controller.create_collection(
                    name
                )
            )
        except (ValueError, OSError) as exc:
            self._warning(exc)
            return

        self.refresh_collections(
            select_name=created
        )

    def rename_collection(self):
        current = self.selected_collection()

        if current is None:
            return

        name, accepted = QInputDialog.getText(
            self,
            "Rename Collection",
            "Collection name:",
            text=current,
        )

        if not accepted:
            return

        try:
            renamed = (
                self.controller.rename_collection(
                    current,
                    name,
                )
            )
        except (ValueError, OSError) as exc:
            self._warning(exc)
            return

        self.refresh_collections(
            select_name=renamed
        )

    def delete_collection(self):
        current = self.selected_collection()

        if current is None:
            return

        answer = QMessageBox.question(
            self,
            "Delete Collection",
            (
                f'Delete "{current}"? '
                "The games will remain in "
                "your Library."
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
            return

        try:
            self.controller.delete_collection(
                current
            )
        except (KeyError, OSError) as exc:
            self._warning(exc)
            return

        self.refresh_collections()

    def showEvent(
        self,
        event,
    ):
        self.refresh_collections()
        super().showEvent(event)

    def _update_game_action(
        self,
        row=None,
    ):
        if row is None:
            row = self.game_list.currentRow()

        self.remove_game_button.setEnabled(
            (
                self.selected_collection()
                is not None
                and 0 <= row
                < len(self._displayed_games)
            )
        )


    def remove_selected_game(
        self,
    ):
        collection = self.selected_collection()
        row = self.game_list.currentRow()

        if (
            collection is None
            or row < 0
            or row >= len(
                self._displayed_games
            )
        ):
            return

        game = self._displayed_games[row]

        answer = QMessageBox.question(
            self,
            "Remove Game",
            (
                f'Remove "{game.name}" from '
                f'"{collection}"? '
                "The game will remain in "
                "your Library."
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
            return

        try:
            self.controller.remove_from_collection(
                collection,
                game,
            )
        except (
            KeyError,
            ValueError,
            OSError,
        ) as exc:
            self._warning(exc)
            return

        self.show_collection(
            collection
        )

    def _show_selected_game(
        self,
        row,
    ):
        if (
            row < 0
            or row >= len(
                self._displayed_games
            )
        ):
            self.details.clear_game()
            return

        self.details.show_game(
            self._displayed_games[row]
        )
