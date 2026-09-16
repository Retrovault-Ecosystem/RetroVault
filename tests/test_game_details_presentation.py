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
