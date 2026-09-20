import os

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "offscreen",
)

from types import SimpleNamespace

from PyQt6.QtWidgets import QApplication

from services.library.presentation_studio import (
    LibraryPresentationState,
    LibraryPresentationStudioService,
)
from services.presentation import PresentationProfile
from ui.library.widgets.presentation_studio import (
    PresentationStudio,
)
from ui.library.details.game_details import GameDetails
from ui.themes.library import (
    library_stylesheet,
)


_APP = None


def _app():
    global _APP

    _APP = QApplication.instance() or QApplication(
        []
    )

    return _APP


class _Store:
    def __init__(
        self,
        data,
    ):
        self.data = data

    def load(self):
        return self.data


class _Resolver:
    def __init__(
        self,
        profile,
    ):
        self.profile = profile
        self.calls = []

    def resolve(
        self,
        platform,
        game_id,
    ):
        self.calls.append(
            (
                platform,
                game_id,
            )
        )

        return self.profile


def _game():
    return SimpleNamespace(
        name="Mega Man 2",
        platform="Nintendo Entertainment System",
        core="fceumm",
        rvdb_game_id="mega-man-2",
    )


def test_library_presentation_state_projects_effective_profile():
    state = LibraryPresentationState(
        platform="nes",
        game_id="mega-man-2",
        default_profile=PresentationProfile(),
        system_profile=PresentationProfile(),
        game_profile=PresentationProfile(),
        effective_profile=PresentationProfile(
            shader="/shaders/crt.slangp",
            overlay="/overlays/nes.cfg",
        ),
    )

    assert state.shader == "/shaders/crt.slangp"
    assert state.overlay == "/overlays/nes.cfg"
    assert state.source_label == "Automatic / Recommended"


def test_library_presentation_studio_uses_authoritative_resolver():
    resolver = _Resolver(
        PresentationProfile(
            shader="/shaders/nes.slangp",
            overlay="/overlays/nes.cfg",
        )
    )

    service = LibraryPresentationStudioService(
        presentation_store=_Store(
            {
                "default": PresentationProfile(),
                "systems": {},
                "games": {},
            }
        ),
        presentation_resolver_provider=lambda: resolver,
    )

    state = service.state_for(
        _game()
    )

    assert resolver.calls == [
        (
            "Nintendo Entertainment System",
            "mega-man-2",
        )
    ]

    assert state.shader == "/shaders/nes.slangp"
    assert state.overlay == "/overlays/nes.cfg"


def test_library_presentation_source_precedence_is_descriptive_only():
    service = LibraryPresentationStudioService(
        presentation_store=_Store(
            {
                "default": PresentationProfile(
                    shader="/default.slangp"
                ),
                "systems": {
                    "Nintendo Entertainment System":
                        PresentationProfile(
                            overlay="/nes.cfg"
                        )
                },
                "games": {
                    "mega-man-2":
                        PresentationProfile(
                            shader="/mega.slangp"
                        )
                },
            }
        ),
        presentation_resolver_provider=lambda: _Resolver(
            PresentationProfile(
                shader="/mega.slangp",
                overlay="/nes.cfg",
            )
        ),
    )

    state = service.state_for(
        _game()
    )

    assert state.has_game_override is True
    assert state.has_system_override is True
    assert state.source_label == "Game Override"


def test_presentation_studio_widget_semantics():
    _app()

    resolver = _Resolver(
        PresentationProfile(
            shader="/shaders/crt.slangp",
            overlay="/overlays/nes.cfg",
        )
    )

    widget = PresentationStudio(
        presentation_store=_Store(
            {
                "default": PresentationProfile(),
                "systems": {},
                "games": {},
            }
        ),
        presentation_resolver_provider=lambda: resolver,
    )

    assert (
        widget.objectName()
        == "LibraryPresentationStudio"
    )

    assert (
        widget.refresh_button.objectName()
        == "LibraryPresentationRefresh"
    )

    widget.set_game(
        _game()
    )

    assert widget.current_state is not None
    assert (
        widget.source_value.text()
        == "Automatic / Recommended"
    )
    assert (
        widget.overlay_value.text()
        == "nes.cfg"
    )
    assert (
        widget.shader_value.text()
        == "crt.slangp"
    )


def test_presentation_studio_empty_selection_is_safe():
    _app()

    widget = PresentationStudio()

    widget.set_game(
        None
    )

    assert widget.current_game is None
    assert widget.current_state is None
    assert widget.source_value.text() == "—"
    assert (
        widget.refresh_button.isEnabled()
        is False
    )


def test_library_theme_contains_presentation_studio_contract():
    stylesheet = library_stylesheet()

    for object_name in (
        "LibraryPresentationStudio",
        "LibraryPresentationEyebrow",
        "LibraryPresentationTitle",
        "LibraryPresentationStatus",
        "LibraryPresentationPanel",
        "LibraryPresentationCaption",
        "LibraryPresentationValue",
        "LibraryPresentationOverride",
        "LibraryPresentationRefresh",
    ):
        assert object_name in stylesheet


def test_game_details_exposes_presentation_studio():
    from ui.library.details.game_details import (
        GameDetails,
    )

    _app()

    details = GameDetails()

    assert hasattr(
        details,
        "presentation_studio",
    )

    assert isinstance(
        details.presentation_studio,
        PresentationStudio,
    )


def test_game_details_show_game_refreshes_presentation_studio():
    from ui.library.details.game_details import (
        GameDetails,
    )

    _app()

    details = GameDetails()

    seen = []

    details.presentation_studio.set_game = (
        lambda game: seen.append(game)
    )

    game = _game()

    details.show_game(
        game
    )

    assert seen
    assert seen[-1] is game
    assert details.current_game is game


def test_game_details_clear_game_clears_presentation_studio():
    from ui.library.details.game_details import (
        GameDetails,
    )

    _app()

    details = GameDetails()

    game = _game()

    # Avoid recording the initial show_game synchronization so this
    # assertion isolates the clear_game contract.
    details.presentation_studio.set_game = (
        lambda game: None
    )

    details.show_game(
        game
    )

    seen = []

    details.presentation_studio.set_game = (
        lambda game: seen.append(game)
    )

    details.clear_game()

    assert seen
    assert seen[-1] is None
    assert details.current_game is None


def test_game_details_presentation_studio_receives_presentation_store():
    _app()

    store = _Store(
        {
            "default": PresentationProfile(),
            "systems": {},
            "games": {},
        }
    )

    details = GameDetails(
        presentation_store=store,
    )

    assert (
        details.presentation_store
        is store
    )

    assert (
        details.presentation_studio.service.presentation_store
        is store
    )


def test_game_details_presentation_studio_receives_resolver_and_store_together():
    _app()

    profile = PresentationProfile(
        shader="/shaders/library-game.slangp",
        overlay="/overlays/library-game.cfg",
    )

    resolver = _Resolver(
        profile
    )

    store = _Store(
        {
            "default": PresentationProfile(),
            "systems": {},
            "games": {},
        }
    )

    details = GameDetails(
        presentation_resolver_provider=lambda: resolver,
        presentation_store=store,
    )

    details.show_game(
        _game()
    )

    assert (
        details.presentation_studio.service.presentation_store
        is store
    )

    assert (
        details.presentation_studio.shader_value.text()
        == "library-game.slangp"
    )

    assert (
        details.presentation_studio.overlay_value.text()
        == "library-game.cfg"
    )


class _MutableStore(_Store):
    def assign_game_overlay(
        self,
        game_id,
        overlay,
    ):
        profile = self.data["games"].get(
            game_id,
            PresentationProfile(),
        )

        self.data["games"][game_id] = PresentationProfile(
            shader=profile.shader,
            overlay=overlay,
            artwork=profile.artwork,
        )

    def assign_game_shader(
        self,
        game_id,
        shader,
    ):
        profile = self.data["games"].get(
            game_id,
            PresentationProfile(),
        )

        self.data["games"][game_id] = PresentationProfile(
            shader=shader,
            overlay=profile.overlay,
            artwork=profile.artwork,
        )

    def clear_game_overlay(
        self,
        game_id,
    ):
        profile = self.data["games"].get(
            game_id,
            PresentationProfile(),
        )

        updated = PresentationProfile(
            shader=profile.shader,
            artwork=profile.artwork,
        )

        if (
            updated.shader
            or updated.overlay
            or updated.artwork
        ):
            self.data["games"][game_id] = updated
        else:
            self.data["games"].pop(
                game_id,
                None,
            )

    def clear_game_shader(
        self,
        game_id,
    ):
        profile = self.data["games"].get(
            game_id,
            PresentationProfile(),
        )

        updated = PresentationProfile(
            overlay=profile.overlay,
            artwork=profile.artwork,
        )

        if (
            updated.shader
            or updated.overlay
            or updated.artwork
        ):
            self.data["games"][game_id] = updated
        else:
            self.data["games"].pop(
                game_id,
                None,
            )


def test_library_presentation_service_assigns_game_overlay_and_shader():
    game = _game()

    store = _MutableStore(
        {
            "default": PresentationProfile(),
            "systems": {},
            "games": {},
        }
    )

    service = LibraryPresentationStudioService(
        presentation_store=store,
    )

    service.assign_game_overlay(
        game,
        "/overlays/game.cfg",
    )

    service.assign_game_shader(
        game,
        "/shaders/game.slangp",
    )

    game_id = service._game_id(
        game
    )

    assert (
        store.data["games"][game_id].overlay
        == "/overlays/game.cfg"
    )

    assert (
        store.data["games"][game_id].shader
        == "/shaders/game.slangp"
    )


def test_library_presentation_service_clears_game_overlay_and_shader():
    game = _game()

    service = LibraryPresentationStudioService()

    game_id = service._game_id(
        game
    )

    store = _MutableStore(
        {
            "default": PresentationProfile(),
            "systems": {},
            "games": {
                game_id: PresentationProfile(
                    shader="/shaders/game.slangp",
                    overlay="/overlays/game.cfg",
                ),
            },
        }
    )

    service.presentation_store = store

    service.clear_game_overlay(
        game
    )

    assert (
        store.data["games"][game_id].overlay
        == ""
    )

    assert (
        store.data["games"][game_id].shader
        == "/shaders/game.slangp"
    )

    service.clear_game_shader(
        game
    )

    assert game_id not in store.data["games"]


def test_presentation_studio_game_controls_follow_selection_state():
    _app()

    widget = PresentationStudio()

    for button in (
        widget.use_overlay_button,
        widget.clear_overlay_button,
        widget.use_shader_button,
        widget.clear_shader_button,
    ):
        assert not button.isEnabled()

    assert not widget.refresh_button.isEnabled()

    widget.set_game(
        _game()
    )

    # A selected game enables refresh, but presentation actions
    # remain unavailable until there is an effective asset or
    # an existing game-scoped override to act on.
    assert widget.refresh_button.isEnabled()

    assert not widget.use_overlay_button.isEnabled()
    assert not widget.clear_overlay_button.isEnabled()
    assert not widget.use_shader_button.isEnabled()
    assert not widget.clear_shader_button.isEnabled()

    widget.clear()

    assert not widget.refresh_button.isEnabled()

    for button in (
        widget.use_overlay_button,
        widget.clear_overlay_button,
        widget.use_shader_button,
        widget.clear_shader_button,
    ):
        assert not button.isEnabled()


def test_presentation_studio_assigns_current_effective_assets_to_game():
    _app()

    game = _game()

    profile = PresentationProfile(
        shader="/shaders/effective.slangp",
        overlay="/overlays/effective.cfg",
    )

    resolver = _Resolver(
        profile
    )

    store = _MutableStore(
        {
            "default": PresentationProfile(),
            "systems": {},
            "games": {},
        }
    )

    widget = PresentationStudio(
        presentation_store=store,
        presentation_resolver_provider=lambda: resolver,
    )

    widget.set_game(
        game
    )

    widget.assign_current_overlay()
    widget.assign_current_shader()

    game_id = widget.service._game_id(
        game
    )

    assert (
        store.data["games"][game_id].overlay
        == "/overlays/effective.cfg"
    )

    assert (
        store.data["games"][game_id].shader
        == "/shaders/effective.slangp"
    )


def test_presentation_studio_clear_actions_preserve_other_game_field():
    _app()

    game = _game()

    service = LibraryPresentationStudioService()

    game_id = service._game_id(
        game
    )

    store = _MutableStore(
        {
            "default": PresentationProfile(),
            "systems": {},
            "games": {
                game_id: PresentationProfile(
                    shader="/shaders/game.slangp",
                    overlay="/overlays/game.cfg",
                ),
            },
        }
    )

    widget = PresentationStudio(
        presentation_store=store,
    )

    widget.set_game(
        game
    )

    widget.clear_game_overlay()

    assert (
        store.data["games"][game_id].shader
        == "/shaders/game.slangp"
    )

    assert (
        store.data["games"][game_id].overlay
        == ""
    )

    widget.clear_game_shader()

    assert game_id not in store.data["games"]


def test_presentation_studio_polish_has_semantic_sections():
    _app()

    widget = PresentationStudio()

    assert (
        widget.assets_label.text()
        == "EFFECTIVE VISUAL STACK"
    )

    assert (
        widget.actions_label.text()
        == "GAME OVERRIDES"
    )

    assert (
        widget.assets_label.objectName()
        == "LibraryPresentationSection"
    )

    assert (
        widget.action_hint.objectName()
        == "LibraryPresentationHint"
    )


def test_presentation_studio_actions_reflect_effective_and_override_state():
    _app()

    game = _game()

    profile = PresentationProfile(
        shader="/shaders/effective.slangp",
        overlay="/overlays/effective.cfg",
    )

    resolver = _Resolver(
        profile
    )

    store = _MutableStore(
        {
            "default": PresentationProfile(),
            "systems": {},
            "games": {},
        }
    )

    widget = PresentationStudio(
        presentation_store=store,
        presentation_resolver_provider=lambda: resolver,
    )

    widget.set_game(
        game
    )

    assert widget.use_overlay_button.isEnabled()
    assert widget.use_shader_button.isEnabled()

    assert not widget.clear_overlay_button.isEnabled()
    assert not widget.clear_shader_button.isEnabled()

    widget.assign_current_overlay()
    widget.assign_current_shader()

    assert widget.clear_overlay_button.isEnabled()
    assert widget.clear_shader_button.isEnabled()


def test_presentation_studio_clear_controls_disable_after_override_removed():
    _app()

    game = _game()

    service = LibraryPresentationStudioService()

    game_id = service._game_id(
        game
    )

    store = _MutableStore(
        {
            "default": PresentationProfile(),
            "systems": {},
            "games": {
                game_id: PresentationProfile(
                    shader="/shaders/game.slangp",
                    overlay="/overlays/game.cfg",
                ),
            },
        }
    )

    resolver = _Resolver(
        PresentationProfile(
            shader="/shaders/game.slangp",
            overlay="/overlays/game.cfg",
        )
    )

    widget = PresentationStudio(
        presentation_store=store,
        presentation_resolver_provider=lambda: resolver,
    )

    widget.set_game(
        game
    )

    assert widget.clear_overlay_button.isEnabled()
    assert widget.clear_shader_button.isEnabled()

    widget.clear_game_overlay()

    assert not widget.clear_overlay_button.isEnabled()
    assert widget.clear_shader_button.isEnabled()

    widget.clear_game_shader()

    assert not widget.clear_overlay_button.isEnabled()
    assert not widget.clear_shader_button.isEnabled()


def test_presentation_studio_action_buttons_fit_narrow_inspector():
    app = QApplication.instance() or QApplication([])

    widget = PresentationStudio()

    widget.resize(
        300,
        700,
    )

    widget.show()
    app.processEvents()

    for button in (
        widget.use_overlay_button,
        widget.clear_overlay_button,
        widget.use_shader_button,
        widget.clear_shader_button,
    ):
        text_width = (
            button.fontMetrics()
            .horizontalAdvance(
                button.text()
            )
        )

        # Preserve enough room for the complete label plus
        # normal horizontal button padding.
        assert (
            button.width()
            >= text_width + 20
        )

        assert (
            button.x()
            + button.width()
            <= widget.width()
        )

    widget.close()


def test_presentation_studio_refresh_button_is_centered():
    app = QApplication.instance() or QApplication([])

    widget = PresentationStudio()

    widget.resize(
        340,
        700,
    )

    widget.show()
    app.processEvents()

    button_center = (
        widget.refresh_button.x()
        + (
            widget.refresh_button.width()
            / 2
        )
    )

    widget_center = (
        widget.width()
        / 2
    )

    assert abs(
        button_center
        - widget_center
    ) <= 2

    widget.close()
