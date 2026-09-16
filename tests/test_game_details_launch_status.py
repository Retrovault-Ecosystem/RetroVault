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
            "retroarch": True,
            "core": True,
            "rom": True,
            "ready": True,
        }


class NotReadyValidator:
    def __init__(self, *_args, **_kwargs):
        pass

    def validate(self, _rom):
        return {
            "retroarch": True,
            "core": True,
            "rom": False,
            "ready": False,
        }


def make_details(app):
    lifecycle = Mock()

    details = GameDetails(
        process_lifecycle=lifecycle,
    )

    details.show_game(
        make_game()
    )

    return details, lifecycle


def test_launch_status_starts_ready(
    app,
):
    details = GameDetails()

    assert details.launch_status.text() == (
        "Ready when you are."
    )


def test_clear_game_restores_ready_status(
    app,
):
    details = GameDetails()
    details.show_game(
        make_game()
    )

    details._set_launch_status(
        "Running."
    )

    details.clear_game()

    assert details.launch_status.text() == (
        "Ready when you are."
    )


def test_missing_core_reports_user_facing_failure(
    app,
):
    details, lifecycle = make_details(app)

    details.core_resolver.find = (
        lambda _core: None
    )

    details.launch_game()

    assert details.launch_status.text() == (
        "Unable to launch: required emulator core "
        "is missing."
    )

    lifecycle.launch_failed.assert_called_once_with()


def test_validation_failure_reports_diagnostics(
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

    details.launch_game()

    assert details.launch_status.text() == (
        "Unable to launch: ROM file does not exist."
    )

    lifecycle.launch_failed.assert_called_once_with()


def test_launcher_failure_reports_launcher_error(
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

    details.launcher.launch = Mock(
        return_value={
            "success": False,
            "error": "RetroArch process is already running.",
        }
    )

    details.launch_game()

    assert details.launch_status.text() == (
        "Unable to launch: RetroArch process "
        "is already running."
    )

    lifecycle.launch_result.assert_called_once()


def test_successful_launch_reports_running_game(
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

    details.launcher.launch = Mock(
        return_value={
            "success": True,
            "command": ["retroarch"],
        }
    )

    details.launch_game()

    assert details.launch_status.text() == (
        'Running "Duck Tales 2".'
    )

    lifecycle.launch_result.assert_called_once()


def test_successful_launch_marks_session_active(
    app,
    monkeypatch,
):
    details, _lifecycle = make_details(app)

    details.core_resolver.find = (
        lambda _core: "/cores/fceumm_libretro.so"
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

    assert details._launch_session_active is True


def test_process_exit_reports_session_ended(
    app,
    monkeypatch,
):
    details, _lifecycle = make_details(app)

    details.core_resolver.find = (
        lambda _core: "/cores/fceumm_libretro.so"
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
    details.process_exited()

    assert details.launch_status.text() == (
        "Game session ended."
    )
    assert details._launch_session_active is False


def test_process_exit_does_not_change_inactive_details(
    app,
):
    details = GameDetails()

    details.process_exited()

    assert details.launch_status.text() == (
        "Ready when you are."
    )


def test_process_exit_notification_is_idempotent(
    app,
    monkeypatch,
):
    details, _lifecycle = make_details(app)

    details.core_resolver.find = (
        lambda _core: "/cores/fceumm_libretro.so"
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
    details.process_exited()
    details.process_exited()

    assert details.launch_status.text() == (
        "Game session ended."
    )


def test_failed_launch_does_not_mark_session_active(
    app,
    monkeypatch,
):
    details, _lifecycle = make_details(app)

    details.core_resolver.find = (
        lambda _core: "/cores/fceumm_libretro.so"
    )

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        ReadyValidator,
    )

    details.launcher.launch = Mock(
        return_value={
            "success": False,
            "error": "spawn failed",
        }
    )

    details.launch_game()

    assert details._launch_session_active is False


def test_clear_game_cancels_local_session_tracking(
    app,
):
    details = GameDetails()
    details.show_game(
        make_game()
    )

    details._launch_session_active = True
    details.clear_game()
    details.process_exited()

    assert details._launch_session_active is False
    assert details.launch_status.text() == (
        "Ready when you are."
    )
