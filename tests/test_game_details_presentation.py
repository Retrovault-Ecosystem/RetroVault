from PyQt6.QtCore import Qt
import pytest

from PyQt6.QtWidgets import QApplication

from services.library.models import Game
from services.presentation import (
    PresentationProfile,
    PresentationResolver,
)
from ui.library.details.game_details import (
    GameDetails,
)
from PyQt6.QtWidgets import QApplication
from unittest.mock import Mock


# Keep a Python reference alive for the full test module.
# QWidget construction is invalid without QApplication.
_RETROVAULT_TEST_APP = (
    QApplication.instance()
    or QApplication([])
)



@pytest.fixture(autouse=True)
def _continue_without_cheats(
    monkeypatch,
):
    """
    Legacy launch tests validate their original launch boundary,
    not interactive Cheat Studio UX.

    The production launch path retains CheatStudio.choose().
    Headless tests deterministically select the supported
    Continue Without Cheats path.
    """

    monkeypatch.setattr(
        GameDetails,
        "_select_cheats",
        lambda self, launch_game, archive_member="": [],
    )


# RETROVAULT_PRESENTATION_MODAL_TEST_GUARD
# Production presentation warnings remain modal. Automated tests
# intercept QMessageBox.warning so headless development regression
# cannot block on a real popup.
@pytest.fixture(autouse=True)
def _suppress_presentation_warning_popups(monkeypatch):
    from PyQt6.QtWidgets import QMessageBox

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Ok,
    )


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()

    if instance is None:
        instance = QApplication([])

    return instance


def make_game():
    return Game(
        name="Duck Tales 2",
        platform="NES",
        year=1993,
        genre="Platformer",
        core="fceumm",
        rom="/roms/Duck Tales 2 (U).nes",
        rvdb_platform_id="platform.nintendo.nes",
    )


def make_ready(details):
    details.core_resolver.find = (
        lambda _core: "/cores/fceumm_libretro.so"
    )

    details.diagnostics.explain = (
        lambda _report: "Launch validation ready."
    )

    class ReadyValidator:
        def __init__(self, *_args, **_kwargs):
            pass

        def validate(self, _rom):
            return {
                "ready": True,
                "issues": [],
            }

    return ReadyValidator


def test_launch_uses_resolved_system_shader(
    app,
    monkeypatch,
):
    resolver = PresentationResolver(
        systems={
            "platform.nintendo.nes": (
                PresentationProfile(
                    shader="/shaders/nes.slangp",
                )
            )
        }
    )

    calls = []

    details = GameDetails(
        presentation_resolver_provider=(
            lambda: resolver
        )
    )

    details.show_game(make_game())

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        make_ready(details),
    )

    details.core_resolver.find = (
        lambda _core: "/cores/fceumm_libretro.so"
    )

    details.launcher.launch = (
        lambda profile: (
            calls.append(profile)
            or {
                "success": True,
                "command": [],
            }
        )
    )

    details.launch_game()

    assert len(calls) == 1
    assert calls[0].shader == (
        "/shaders/nes.slangp"
    )


def test_launch_uses_game_shader_precedence(
    app,
    monkeypatch,
):
    game = make_game()

    from services.library.state import (
        game_identity,
    )

    resolver = PresentationResolver(
        default=PresentationProfile(
            shader="/shaders/default.slangp",
        ),
        systems={
            "platform.nintendo.nes": (
                PresentationProfile(
                    shader="/shaders/nes.slangp",
                )
            )
        },
        games={
            game_identity(game): (
                PresentationProfile(
                    shader="/shaders/duck.slangp",
                )
            )
        },
    )

    calls = []

    details = GameDetails(
        presentation_resolver_provider=(
            lambda: resolver
        )
    )

    details.show_game(game)

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        make_ready(details),
    )

    details.core_resolver.find = (
        lambda _core: "/cores/fceumm_libretro.so"
    )

    details.launcher.launch = (
        lambda profile: (
            calls.append(profile)
            or {
                "success": True,
                "command": [],
            }
        )
    )

    details.launch_game()

    assert len(calls) == 1
    assert calls[0].shader == (
        "/shaders/duck.slangp"
    )


def test_launch_without_provider_preserves_no_shader(
    app,
    monkeypatch,
):
    calls = []

    details = GameDetails()

    details.show_game(make_game())

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        make_ready(details),
    )

    details.core_resolver.find = (
        lambda _core: "/cores/fceumm_libretro.so"
    )

    details.launcher.launch = (
        lambda profile: (
            calls.append(profile)
            or {
                "success": True,
                "command": [],
            }
        )
    )

    details.launch_game()

    assert len(calls) == 1
    assert calls[0].shader == ""


def test_provider_is_resolved_at_launch_time(
    app,
    monkeypatch,
):
    state = {
        "shader": "/shaders/first.slangp"
    }

    def provider():
        return PresentationResolver(
            default=PresentationProfile(
                shader=state["shader"]
            )
        )

    calls = []

    details = GameDetails(
        presentation_resolver_provider=provider
    )

    details.show_game(make_game())

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        make_ready(details),
    )

    details.core_resolver.find = (
        lambda _core: "/cores/fceumm_libretro.so"
    )

    details.launcher.launch = (
        lambda profile: (
            calls.append(profile)
            or {
                "success": True,
                "command": [],
            }
        )
    )

    details.launch_game()

    state["shader"] = "/shaders/second.slangp"

    details.launch_game()

    assert [
        profile.shader
        for profile in calls
    ] == [
        "/shaders/first.slangp",
        "/shaders/second.slangp",
    ]


def test_presentation_load_failure_falls_back_cleanly(
    app,
    monkeypatch,
):
    def broken_provider():
        raise ValueError(
            "broken presentation state"
        )

    calls = []

    details = GameDetails(
        presentation_resolver_provider=(
            broken_provider
        )
    )

    details.show_game(make_game())

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        make_ready(details),
    )

    details.core_resolver.find = (
        lambda _core: "/cores/fceumm_libretro.so"
    )

    details.launcher.launch = (
        lambda profile: (
            calls.append(profile)
            or {
                "success": True,
                "command": [],
            }
        )
    )

    details.launch_game()

    assert len(calls) == 1
    assert calls[0].shader == ""


def test_resolved_overlay_reaches_launch_profile(
    app,
    monkeypatch,
):
    class Resolver:
        def resolve(
            self,
            _game,
        ):
            from services.presentation import (
                PresentationProfile,
            )

            return PresentationProfile(
                overlay="/overlays/duck.cfg"
            )

    calls = []

    details = GameDetails(
        presentation_resolver_provider=(
            lambda: Resolver()
        )
    )

    details.show_game(
        make_game()
    )

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        make_ready(details),
    )

    details.core_resolver.find = (
        lambda _core:
        "/cores/fceumm_libretro.so"
    )

    details.launcher.launch = (
        lambda profile: (
            calls.append(profile)
            or {
                "success": True,
                "command": [],
            }
        )
    )

    details.launch_game()

    assert len(calls) == 1

    assert calls[0].overlay == (
        "/overlays/duck.cfg"
    )


def test_presentation_resolves_shader_and_overlay_together(
    app,
    monkeypatch,
):
    class Resolver:
        def resolve(
            self,
            _game,
        ):
            from services.presentation import (
                PresentationProfile,
            )

            return PresentationProfile(
                shader="/shaders/crt.slangp",
                overlay="/overlays/duck.cfg",
            )

    calls = []

    details = GameDetails(
        presentation_resolver_provider=(
            lambda: Resolver()
        )
    )

    details.show_game(
        make_game()
    )

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        make_ready(details),
    )

    details.core_resolver.find = (
        lambda _core:
        "/cores/fceumm_libretro.so"
    )

    details.launcher.launch = (
        lambda profile: (
            calls.append(profile)
            or {
                "success": True,
                "command": [],
            }
        )
    )

    details.launch_game()

    assert len(calls) == 1

    assert calls[0].shader == (
        "/shaders/crt.slangp"
    )

    assert calls[0].overlay == (
        "/overlays/duck.cfg"
    )


def test_presentation_load_failure_is_reported_to_user(
    app,
    monkeypatch,
):
    from unittest.mock import Mock

    from PyQt6.QtWidgets import QMessageBox

    from services.library.models import Game
    from ui.library.details.game_details import (
        GameDetails,
    )

    def broken_provider():
        raise ValueError(
            "broken presentation state"
        )

    warnings = []

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda parent, title, message: (
            warnings.append(
                (
                    parent,
                    title,
                    message,
                )
            )
        ),
    )

    details = GameDetails(
        presentation_resolver_provider=(
            broken_provider
        )
    )

    details.current_game = Game(
        name="Presentation Failure",
        platform="NES",
        year="",
        genre="",
        core="fceumm",
        rom="/library/Presentation Failure.nes",
        source="",
        artwork="",
    )

    details.core_resolver.find = Mock(
        return_value="/cores/fceumm_libretro.so"
    )

    class ReadyValidator:
        def __init__(
            self,
            *_args,
            **_kwargs,
        ):
            pass

        def validate(
            self,
            _rom,
        ):
            return {
                "retroarch": True,
                "core": True,
                "rom": True,
                "ready": True,
            }

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        ReadyValidator,
    )

    details.launcher.launch = Mock(
        return_value={
            "success": False,
            "error": "test launch stopped",
        }
    )

    details.launch_game()

    assert len(warnings) == 1

    parent, title, message = warnings[0]

    assert parent is details
    assert title == "Visual Presentation Unavailable"

    assert (
        "RetroVault could not load "
        "the selected visual presentation."
        in message
    )

    assert (
        "The game will continue without "
        "the assigned shader or overlay."
        in message
    )

    assert (
        "broken presentation state"
        in message
    )

    profile = details.launcher.launch.call_args.args[0]

    assert profile.shader == ""
    assert profile.overlay == ""


def test_cheat_selection_occurs_before_presentation_and_launch(
    monkeypatch,
):
    from services.library.models import Game

    details = GameDetails(
        presentation_resolver_provider=(
            lambda: resolver
        )
    )

    details.current_game = Game(
        name="Exact Edition (USA) (Rev A)",
        platform="NES",
        year=1987,
        genre="Platform",
        rom="/games/exact.nes",
        core="lr-fceumm",
        canonical_title="Exact Edition",
        variant_category="revision",
        variant_region="USA",
        variant_language="English",
        variant_revision="Rev A",
    )

    details.current_game.variants = [
        {
            "name": details.current_game.name,
            "rom": details.current_game.rom,
            "source": "",
            "category": "Revisions",
            "label": "USA • English • Rev A",
            "region": "USA",
            "language": "English",
            "revision": "Rev A",
            "preferred": True,
        }
    ]

    events = []

    details._select_game_edition = Mock(
        return_value=(
            details.current_game.variants[0]
        )
    )

    details._select_cheats = Mock(
        side_effect=lambda game, archive_member: (
            events.append(
                (
                    "cheats",
                    game.rom,
                    archive_member,
                )
            )
            or []
        )
    )

    details._cheat_runtime_file = Mock(
        return_value=""
    )

    details.core_resolver.find = Mock(
        return_value="/cores/nes.so"
    )

    class Presentation:
        shader = ""
        overlay = ""

    class Resolver:
        def resolve(
            self,
            game,
        ):
            events.append(
                (
                    "presentation",
                    game.rom,
                )
            )
            return Presentation()

    details.presentation_resolver_provider = (
        lambda: Resolver()
    )

    monkeypatch.setattr(
        "ui.library.details.game_details."
        "LaunchValidator.validate",
        lambda self, rom: {
            "ready": True,
        },
    )

    monkeypatch.setattr(
        "ui.library.details.game_details."
        "LaunchDiagnostics.explain",
        lambda self, result: [],
    )

    details.launcher.launch = Mock(
        side_effect=lambda profile: (
            events.append(
                (
                    "launch",
                    profile.rom,
                    profile.cheat_file,
                )
            )
            or {
                "success": True,
            }
        )
    )

    details.launch_game()

    assert [
        event[0]
        for event in events
    ] == [
        "cheats",
        "presentation",
        "launch",
    ]

    assert events[0][1] == (
        "/games/exact.nes"
    )


def test_game_details_uses_vertical_scroll_boundary_for_presentation_studio():
    app = QApplication.instance() or QApplication([])

    details = GameDetails()

    assert (
        details.details_scroll.objectName()
        == "LibraryGameDetailsScroll"
    )

    assert details.details_scroll.widgetResizable()

    assert (
        details.details_scroll.horizontalScrollBarPolicy()
        == Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    )

    assert (
        details.details_scroll.verticalScrollBarPolicy()
        == Qt.ScrollBarPolicy.ScrollBarAsNeeded
    )

    assert (
        details.details_scroll.widget()
        is details.details_content
    )


def test_game_details_scroll_content_contains_presentation_studio():
    app = QApplication.instance() or QApplication([])

    details = GameDetails()

    layout = details.details_content.layout()

    assert layout is not None

    widgets = []

    for index in range(
        layout.count()
    ):
        item = layout.itemAt(
            index
        )

        widget = item.widget()

        if widget is not None:
            widgets.append(
                widget
            )

    assert details.presentation_studio in widgets


def test_game_details_header_is_responsive_at_narrow_sidebar_width():
    app = QApplication.instance() or QApplication([])

    details = GameDetails()

    details.resize(
        300,
        800,
    )

    details.show()
    app.processEvents()

    # The scroll content must no longer force the historical
    # 365 px horizontal header minimum into a 300 px inspector.
    viewport_width = (
        details.details_scroll.viewport().width()
    )

    assert (
        details.details_content.width()
        <= viewport_width
    )

    assert (
        details.cover.width()
        <= details.details_content.width()
    )

    assert (
        details.title.x()
        < details.details_content.width()
    )

    assert (
        details.metadata.x()
        < details.details_content.width()
    )

    assert details.title.wordWrap()
    assert details.metadata.wordWrap()

    details.close()


def test_game_details_scroll_content_does_not_propagate_studio_minimum_width():
    app = QApplication.instance() or QApplication([])

    details = GameDetails()

    details.resize(
        300,
        800,
    )

    details.show()
    app.processEvents()

    viewport_width = (
        details.details_scroll.viewport().width()
    )

    assert (
        details.details_content.minimumSizeHint().width()
        == 0
    )

    assert (
        details.presentation_studio.minimumWidth()
        == 0
    )

    assert (
        details.details_content.width()
        <= viewport_width
    )

    assert (
        details.presentation_studio.width()
        <= details.details_content.width()
    )

    details.close()


def test_game_details_cover_is_not_fixed_to_250_by_320():
    app = QApplication.instance() or QApplication([])

    details = GameDetails()

    assert not (
        details.cover.minimumWidth() == 250
        and details.cover.maximumWidth() == 250
        and details.cover.minimumHeight() == 320
        and details.cover.maximumHeight() == 320
    )

    assert (
        details.cover.minimumWidth()
        == 0
    )

    assert (
        details.cover.minimumHeight()
        == 220
    )

    assert (
        details.cover.maximumHeight()
        == 300
    )


def test_game_details_new_game_context_resets_vertical_scroll_to_top():
    app = QApplication.instance() or QApplication([])

    details = GameDetails()

    details.resize(
        330,
        500,
    )

    details.show()
    app.processEvents()

    bar = details.details_scroll.verticalScrollBar()

    assert bar.maximum() > 0

    bar.setValue(
        bar.maximum()
    )

    assert bar.value() > 0

    game = make_game()

    details.show_game(
        game
    )

    app.processEvents()

    assert (
        bar.value()
        == bar.minimum()
        == 0
    )

    details.close()


def test_game_details_empty_context_resets_vertical_scroll_to_top():
    app = QApplication.instance() or QApplication([])

    details = GameDetails()

    details.resize(
        330,
        500,
    )

    details.show()
    app.processEvents()

    bar = details.details_scroll.verticalScrollBar()

    assert bar.maximum() > 0

    bar.setValue(
        bar.maximum()
    )

    assert bar.value() > 0

    details.clear_game()

    app.processEvents()

    assert (
        bar.value()
        == bar.minimum()
        == 0
    )

    details.close()


def test_game_details_header_starts_at_top_after_context_reset():
    app = QApplication.instance() or QApplication([])

    details = GameDetails()

    details.resize(
        330,
        500,
    )

    details.show()
    app.processEvents()

    bar = details.details_scroll.verticalScrollBar()

    bar.setValue(
        bar.maximum()
    )

    details.clear_game()
    app.processEvents()

    assert bar.value() == 0

    # The complete header must begin before Launch Profile.
    assert details.cover.y() < details.title.y()
    assert details.title.y() < details.metadata.y()
    assert details.metadata.y() < details.description.y()
    assert details.description.y() < details.profile.y()

    # The first header element must begin inside the initial
    # visible viewport when scroll position is zero.
    assert (
        details.cover.y()
        < details.details_scroll.viewport().height()
    )

    details.close()
