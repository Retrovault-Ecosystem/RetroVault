from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from services.library.presentation_studio import (
    LibraryPresentationStudioService,
)


class PresentationStudio(QWidget):
    """
    Compact Library-native view of the effective RVV presentation.

    This surface intentionally edits no filesystem assets and performs
    no manual shader/overlay composition.  It reflects the authoritative
    Presentation Composition result used by launch.
    """

    def __init__(
        self,
        presentation_store=None,
        presentation_resolver_provider=None,
        parent=None,
    ):
        super().__init__(
            parent
        )

        self.setObjectName(
            "LibraryPresentationStudio"
        )

        self.setMinimumWidth(
            0
        )

        self.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Preferred,
        )

        self.service = LibraryPresentationStudioService(
            presentation_store=presentation_store,
            presentation_resolver_provider=(
                presentation_resolver_provider
            ),
        )

        self.current_game = None
        self.current_state = None

        self.eyebrow = QLabel(
            "RVV PRESENTATION"
        )
        self.eyebrow.setObjectName(
            "LibraryPresentationEyebrow"
        )

        self.title = QLabel(
            "Presentation Studio"
        )
        self.title.setObjectName(
            "LibraryPresentationTitle"
        )

        self.status = QLabel(
            "Select a game to inspect its visual presentation."
        )
        self.status.setObjectName(
            "LibraryPresentationStatus"
        )
        self.status.setWordWrap(
            True
        )

        self.source_caption = QLabel(
            "Effective source"
        )
        self.source_caption.setObjectName(
            "LibraryPresentationCaption"
        )

        self.source_value = QLabel(
            "—"
        )
        self.source_value.setObjectName(
            "LibraryPresentationValue"
        )

        self.overlay_caption = QLabel(
            "Overlay / Bezel"
        )
        self.overlay_caption.setObjectName(
            "LibraryPresentationCaption"
        )

        self.overlay_value = QLabel(
            "RetroArch Default"
        )
        self.overlay_value.setObjectName(
            "LibraryPresentationValue"
        )
        self.overlay_value.setWordWrap(
            True
        )
        self.overlay_value.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.shader_caption = QLabel(
            "Shader / Filter"
        )
        self.shader_caption.setObjectName(
            "LibraryPresentationCaption"
        )

        self.shader_value = QLabel(
            "RetroArch Default"
        )
        self.shader_value.setObjectName(
            "LibraryPresentationValue"
        )
        self.shader_value.setWordWrap(
            True
        )
        self.shader_value.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.assets_label = QLabel(
            "EFFECTIVE VISUAL STACK"
        )
        self.assets_label.setObjectName(
            "LibraryPresentationSection"
        )

        self.actions_label = QLabel(
            "GAME OVERRIDES"
        )
        self.actions_label.setObjectName(
            "LibraryPresentationSection"
        )

        self.game_override = QLabel(
            "No game-specific visual override"
        )
        self.game_override.setObjectName(
            "LibraryPresentationOverride"
        )

        self.use_overlay_button = QPushButton(
            "Use Current Overlay for Game"
        )
        self.use_overlay_button.setObjectName(
            "LibraryPresentationAssignOverlay"
        )
        self.use_overlay_button.clicked.connect(
            self.assign_current_overlay
        )

        self.clear_overlay_button = QPushButton(
            "Clear Game Overlay"
        )
        self.clear_overlay_button.setObjectName(
            "LibraryPresentationClearOverlay"
        )
        self.clear_overlay_button.clicked.connect(
            self.clear_game_overlay
        )

        self.use_shader_button = QPushButton(
            "Use Current Shader for Game"
        )
        self.use_shader_button.setObjectName(
            "LibraryPresentationAssignShader"
        )
        self.use_shader_button.clicked.connect(
            self.assign_current_shader
        )

        self.clear_shader_button = QPushButton(
            "Clear Game Shader"
        )
        self.clear_shader_button.setObjectName(
            "LibraryPresentationClearShader"
        )
        self.clear_shader_button.clicked.connect(
            self.clear_game_shader
        )

        self.action_hint = QLabel(
            "Pin the effective visual stack to this game, "
            "or clear an existing game override."
        )
        self.action_hint.setObjectName(
            "LibraryPresentationHint"
        )
        self.action_hint.setWordWrap(
            True
        )

        self.refresh_button = QPushButton(
            "Refresh Presentation"
        )
        self.refresh_button.setObjectName(
            "LibraryPresentationRefresh"
        )
        self.refresh_button.clicked.connect(
            self.refresh
        )

        for button in (
            self.use_overlay_button,
            self.clear_overlay_button,
            self.use_shader_button,
            self.clear_shader_button,
            self.refresh_button,
        ):
            button.setMinimumHeight(
                32
            )
            button.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Fixed,
            )

        self._build_ui()
        self.set_game(
            None
        )

    def _build_ui(self):
        root = QVBoxLayout(
            self
        )

        root.setContentsMargins(
            14,
            14,
            14,
            14,
        )
        root.setSpacing(
            8
        )

        root.addWidget(
            self.eyebrow
        )
        root.addWidget(
            self.title
        )
        root.addWidget(
            self.status
        )

        root.addWidget(
            self.assets_label
        )

        panel = QFrame()
        panel.setObjectName(
            "LibraryPresentationPanel"
        )

        grid = QGridLayout(
            panel
        )
        grid.setContentsMargins(
            12,
            12,
            12,
            12,
        )
        grid.setHorizontalSpacing(
            12
        )
        grid.setVerticalSpacing(
            8
        )

        grid.addWidget(
            self.source_caption,
            0,
            0,
        )
        grid.addWidget(
            self.source_value,
            0,
            1,
        )

        grid.addWidget(
            self.overlay_caption,
            1,
            0,
        )
        grid.addWidget(
            self.overlay_value,
            1,
            1,
        )

        grid.addWidget(
            self.shader_caption,
            2,
            0,
        )
        grid.addWidget(
            self.shader_value,
            2,
            1,
        )

        grid.setColumnStretch(
            1,
            1,
        )

        root.addWidget(
            panel
        )

        root.addWidget(
            self.actions_label
        )

        root.addWidget(
            self.game_override
        )

        root.addWidget(
            self.action_hint
        )

        # The Game Details inspector is intentionally narrow.
        # Keep each presentation action on its own row so the
        # complete label remains readable without forcing the
        # inspector wider than its viewport.
        overlay_actions = QVBoxLayout()
        overlay_actions.setSpacing(
            6
        )
        overlay_actions.addWidget(
            self.use_overlay_button
        )
        overlay_actions.addWidget(
            self.clear_overlay_button
        )

        shader_actions = QVBoxLayout()
        shader_actions.setSpacing(
            6
        )
        shader_actions.addWidget(
            self.use_shader_button
        )
        shader_actions.addWidget(
            self.clear_shader_button
        )

        utility_actions = QHBoxLayout()
        utility_actions.addStretch(
            1
        )
        utility_actions.addWidget(
            self.refresh_button
        )
        utility_actions.addStretch(
            1
        )

        root.addLayout(
            overlay_actions
        )
        root.addLayout(
            shader_actions
        )
        root.addLayout(
            utility_actions
        )

    @staticmethod
    def _display_asset(value):
        if not value:
            return "RetroArch Default"

        text = str(value)

        if text.startswith(
            "retro-vault://"
        ):
            return text

        try:
            path = Path(
                text
            )

            if path.name:
                return path.name
        except (
            TypeError,
            ValueError,
        ):
            pass

        return text

    def _sync_action_state(self):
        has_game = (
            self.current_game is not None
        )

        state = self.current_state

        has_effective_overlay = bool(
            state is not None
            and state.overlay
        )

        has_effective_shader = bool(
            state is not None
            and state.shader
        )

        has_game_overlay = bool(
            state is not None
            and state.game_profile.overlay
        )

        has_game_shader = bool(
            state is not None
            and state.game_profile.shader
        )

        self.use_overlay_button.setEnabled(
            has_game
            and has_effective_overlay
        )

        self.use_shader_button.setEnabled(
            has_game
            and has_effective_shader
        )

        self.clear_overlay_button.setEnabled(
            has_game
            and has_game_overlay
        )

        self.clear_shader_button.setEnabled(
            has_game
            and has_game_shader
        )

        self.refresh_button.setEnabled(
            has_game
        )

    def clear(self):
        self.current_game = None
        self.current_state = None

        self.source_value.setText(
            "—"
        )
        self.overlay_value.setText(
            "RetroArch Default"
        )
        self.shader_value.setText(
            "RetroArch Default"
        )
        self.game_override.setText(
            "No game-specific visual override"
        )
        self.status.setText(
            "Select a game to inspect its visual presentation."
        )
        self._sync_action_state()

    def set_game(
        self,
        game,
    ):
        self.current_game = game

        if game is None:
            self.clear()
            return

        self.refresh()

    def _action_error(
        self,
        action,
        exc,
    ):
        self.status.setText(
            f"{action}: {exc}"
        )

    def assign_current_overlay(self):
        game = self.current_game
        state = self.current_state

        if game is None or state is None:
            return

        overlay = state.overlay

        if not overlay:
            self.status.setText(
                "No effective overlay is available to assign."
            )
            return

        try:
            self.service.assign_game_overlay(
                game,
                overlay,
            )
        except (
            OSError,
            TypeError,
            ValueError,
            RuntimeError,
        ) as exc:
            self._action_error(
                "Unable to assign game overlay",
                exc,
            )
            return

        self.refresh()

        self.status.setText(
            "Current effective overlay assigned "
            "as this game's override."
        )

    def assign_current_shader(self):
        game = self.current_game
        state = self.current_state

        if game is None or state is None:
            return

        shader = state.shader

        if not shader:
            self.status.setText(
                "No effective shader is available to assign."
            )
            return

        try:
            self.service.assign_game_shader(
                game,
                shader,
            )
        except (
            OSError,
            TypeError,
            ValueError,
            RuntimeError,
        ) as exc:
            self._action_error(
                "Unable to assign game shader",
                exc,
            )
            return

        self.refresh()

        self.status.setText(
            "Current effective shader assigned "
            "as this game's override."
        )

    def clear_game_overlay(self):
        game = self.current_game

        if game is None:
            return

        try:
            self.service.clear_game_overlay(
                game
            )
        except (
            OSError,
            TypeError,
            ValueError,
            RuntimeError,
        ) as exc:
            self._action_error(
                "Unable to clear game overlay",
                exc,
            )
            return

        self.refresh()

        self.status.setText(
            "Game overlay override cleared."
        )

    def clear_game_shader(self):
        game = self.current_game

        if game is None:
            return

        try:
            self.service.clear_game_shader(
                game
            )
        except (
            OSError,
            TypeError,
            ValueError,
            RuntimeError,
        ) as exc:
            self._action_error(
                "Unable to clear game shader",
                exc,
            )
            return

        self.refresh()

        self.status.setText(
            "Game shader override cleared."
        )

    def refresh(self):
        game = self.current_game

        if game is None:
            self.clear()
            return

        try:
            state = self.service.state_for(
                game
            )
        except Exception as exc:
            self.current_state = None

            self.source_value.setText(
                "Unavailable"
            )
            self.overlay_value.setText(
                "Unavailable"
            )
            self.shader_value.setText(
                "Unavailable"
            )
            self.game_override.setText(
                "Presentation state could not be resolved."
            )
            self.status.setText(
                f"Presentation unavailable: {exc}"
            )
            return

        self.current_state = state

        self.source_value.setText(
            state.source_label
        )

        self.overlay_value.setText(
            self._display_asset(
                state.overlay
            )
        )

        self.shader_value.setText(
            self._display_asset(
                state.shader
            )
        )

        if state.has_game_override:
            self.game_override.setText(
                "Game-specific presentation override active"
            )
        elif state.has_system_override:
            self.game_override.setText(
                "Using the system presentation assignment"
            )
        else:
            self.game_override.setText(
                "No game-specific visual override"
            )

        self._sync_action_state()

        name = str(
            getattr(
                game,
                "name",
                "",
            )
            or getattr(
                game,
                "title",
                "",
            )
            or "Selected game"
        )

        self.status.setText(
            f"{name} is using the authoritative "
            "RetroVault presentation composition."
        )
