from unittest.mock import Mock

import pytest

from PyQt6.QtWidgets import QApplication

from services.library.models import Game
from ui.library.details.game_details import GameDetails


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


class ReadyValidator:
    def __init__(self, *_args, **_kwargs):
        pass

    def validate(self, _rom):
        return {
            "ready": True,
            "issues": [],
        }


class NotReadyValidator:
    def __init__(self, *_args, **_kwargs):
        pass

    def validate(self, _rom):
        return {
            "ready": False,
            "issues": ["not ready"],
        }


def make_details(app):
    lifecycle = Mock()

    details = GameDetails(
        process_lifecycle=lifecycle,
    )

    details.show_game(
        make_game()
    )

    details.diagnostics.explain = (
        lambda _report: "diagnostic"
    )

    return details, lifecycle


def test_launch_request_precedes_core_resolution(
    app,
):
    details, lifecycle = make_details(app)

    order = []

    lifecycle.launch_requested.side_effect = (
        lambda: order.append("launch_requested")
    )

    details.core_resolver.find = (
        lambda _core: (
            order.append("core_resolution")
            or None
        )
    )

    details.launch_game()

    assert order == [
        "launch_requested",
        "core_resolution",
    ]

    lifecycle.launch_failed.assert_called_once_with()


def test_missing_core_normalizes_pending_launch(
    app,
):
    details, lifecycle = make_details(app)

    details.core_resolver.find = (
        lambda _core: None
    )

    details.launch_game()

    lifecycle.launch_requested.assert_called_once_with()
    lifecycle.launch_failed.assert_called_once_with()
    lifecycle.launch_result.assert_not_called()


def test_validation_failure_normalizes_pending_launch(
    app,
    monkeypatch,
):
    details, lifecycle = make_details(app)

    details.core_resolver.find = (
        lambda _core: "/cores/fceumm_libretro.so"
    )

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        NotReadyValidator,
    )

    details.launcher.launch = Mock()

    details.launch_game()

    lifecycle.launch_requested.assert_called_once_with()
    lifecycle.launch_failed.assert_called_once_with()
    lifecycle.launch_result.assert_not_called()

    details.launcher.launch.assert_not_called()


def test_failed_launcher_result_reaches_lifecycle(
    app,
    monkeypatch,
):
    details, lifecycle = make_details(app)

    details.core_resolver.find = (
        lambda _core: "/cores/fceumm_libretro.so"
    )

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        ReadyValidator,
    )

    launch_result = {
        "success": False,
        "error": "spawn failed",
    }

    details.launcher.launch = Mock(
        return_value=launch_result
    )

    details.launch_game()

    lifecycle.launch_requested.assert_called_once_with()
    lifecycle.launch_failed.assert_not_called()

    lifecycle.launch_result.assert_called_once_with(
        launch_result
    )


def test_successful_launcher_result_reaches_lifecycle(
    app,
    monkeypatch,
):
    details, lifecycle = make_details(app)

    details.core_resolver.find = (
        lambda _core: "/cores/fceumm_libretro.so"
    )

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        ReadyValidator,
    )

    launch_result = {
        "success": True,
        "command": ["retroarch"],
    }

    details.launcher.launch = Mock(
        return_value=launch_result
    )

    details.launch_game()

    lifecycle.launch_requested.assert_called_once_with()
    lifecycle.launch_failed.assert_not_called()

    lifecycle.launch_result.assert_called_once_with(
        launch_result
    )


def test_no_selected_game_does_not_enter_lifecycle(
    app,
):
    lifecycle = Mock()

    details = GameDetails(
        process_lifecycle=lifecycle,
    )

    details.launch_game()

    lifecycle.launch_requested.assert_not_called()
    lifecycle.launch_failed.assert_not_called()
    lifecycle.launch_result.assert_not_called()


def test_standalone_game_details_remains_safe(
    app,
    monkeypatch,
):
    details = GameDetails()

    details.show_game(
        make_game()
    )

    details.core_resolver.find = (
        lambda _core: "/cores/fceumm_libretro.so"
    )

    details.diagnostics.explain = (
        lambda _report: "diagnostic"
    )

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        ReadyValidator,
    )

    details.launcher.launch = Mock(
        return_value={
            "success": True,
            "command": ["retroarch"],
        }
    )

    details.launch_game()

    details.launcher.launch.assert_called_once()
