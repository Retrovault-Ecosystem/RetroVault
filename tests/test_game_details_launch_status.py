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


def test_selecting_different_game_resets_launch_status(
    app,
):
    details = GameDetails()

    first = make_game()

    second = Game(
        name="Super Mario Bros.",
        platform="NES",
        year=1985,
        genre="Platformer",
        core="fceumm",
        rom="/roms/Super Mario Bros. (U).nes",
        rvdb_platform_id="platform.nintendo.nes",
    )

    details.show_game(
        first
    )

    details._launch_session_active = True
    details._set_launch_status(
        'Running "Duck Tales 2".'
    )

    details.show_game(
        second
    )

    assert details.current_game is second
    assert details._launch_session_active is False
    assert details.launch_status.text() == (
        "Ready when you are."
    )


def test_refreshing_same_game_preserves_running_status(
    app,
):
    details = GameDetails()
    game = make_game()

    details.show_game(
        game
    )

    details._launch_session_active = True
    details._set_launch_status(
        'Running "Duck Tales 2".'
    )

    details.show_game(
        game
    )

    assert details.current_game is game
    assert details._launch_session_active is True
    assert details.launch_status.text() == (
        'Running "Duck Tales 2".'
    )


def test_refreshing_same_game_preserves_failure_status(
    app,
):
    details = GameDetails()
    game = make_game()

    details.show_game(
        game
    )

    details._set_launch_status(
        "Unable to launch: test failure."
    )

    details.show_game(
        game
    )

    assert details.current_game is game
    assert details.launch_status.text() == (
        "Unable to launch: test failure."
    )


def test_switching_after_completed_session_returns_ready(
    app,
):
    details = GameDetails()
    first = make_game()

    second = Game(
        name="Metroid",
        platform="NES",
        year=1986,
        genre="Action",
        core="fceumm",
        rom="/roms/Metroid (U).nes",
        rvdb_platform_id="platform.nintendo.nes",
    )

    details.show_game(
        first
    )

    details._launch_session_active = True
    details.process_exited()

    assert details.launch_status.text() == (
        "Game session ended."
    )

    details.show_game(
        second
    )

    assert details.launch_status.text() == (
        "Ready when you are."
    )
    assert details._launch_session_active is False


def test_stop_button_starts_disabled(
    app,
):
    details = GameDetails()

    assert details.stop_button.isEnabled() is False


def test_successful_launch_enables_stop_and_disables_launch(
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
    process_running = Mock(
        side_effect=[False, True]
    )
    details.launcher.process_running = (
        process_running
    )

    details.launch_game()

    assert details.launch_button.isEnabled() is False
    assert details.stop_button.isEnabled() is True


def test_stop_game_requests_lifecycle_stop(
    app,
):
    details, lifecycle = make_details(app)

    details.launcher.process_running = Mock(
        return_value=True
    )
    details._launch_session_active = True
    details._refresh_launch_button()

    details.stop_game()

    lifecycle.stop_requested.assert_called_once_with()

    assert details.launch_status.text() == (
        "Stopping game..."
    )
    assert details.launch_button.isEnabled() is False
    assert details.stop_button.isEnabled() is True


def test_process_exit_restores_launch_control(
    app,
):
    details = GameDetails()
    details.show_game(
        make_game()
    )

    details._launch_session_active = True
    details._refresh_launch_button()

    details.process_exited()

    assert details._launch_session_active is False
    assert details.launch_button.isEnabled() is True
    assert details.stop_button.isEnabled() is False
    assert details.launch_status.text() == (
        "Game session ended."
    )


def test_stop_failure_remains_user_visible(
    app,
):
    details, lifecycle = make_details(app)

    details._launch_session_active = True
    details._refresh_launch_button()

    lifecycle.stop_requested.side_effect = (
        RuntimeError("stop failed")
    )

    details.stop_game()

    assert details.launch_status.text() == (
        "Unable to stop game: stop failed"
    )


def test_selecting_different_game_during_shared_session_disables_launch(
    app,
):
    details = GameDetails()

    first = make_game()
    second = make_game()
    second.name = "Mega Man 2"
    second.rom = "/roms/mega-man-2.nes"

    details.show_game(first)

    details.launcher.process_running = Mock(
        return_value=True
    )

    details._launch_session_active = True
    details.show_game(second)

    assert details._launch_session_active is False
    assert details.launch_button.isEnabled() is False
    assert details.stop_button.isEnabled() is False
    assert details.launch_status.text() == (
        "Another game session is running."
    )


def test_shared_running_process_disables_launch_without_local_ownership(
    app,
):
    details = GameDetails()
    details.show_game(
        make_game()
    )

    details.launcher.process_running = Mock(
        return_value=True
    )

    details._launch_session_active = False
    details.sync_process_session()

    assert details.launch_button.isEnabled() is False
    assert details.stop_button.isEnabled() is False


def test_launch_guard_rejects_shared_active_process_before_lifecycle_request(
    app,
):
    details, lifecycle = make_details(app)

    details.launcher.process_running = Mock(
        return_value=True
    )

    details.launch_game()

    lifecycle.launch_requested.assert_not_called()

    assert details.launch_status.text() == (
        "Unable to launch: another game session is running."
    )
    assert details.launch_button.isEnabled() is False


def test_shared_session_exit_restores_non_owner_launch_availability(
    app,
):
    details = GameDetails()
    details.show_game(
        make_game()
    )

    details.launcher.process_running = Mock(
        return_value=True
    )
    details.sync_process_session()

    assert details.launch_button.isEnabled() is False

    details.launcher.process_running.return_value = False
    details.sync_process_session()

    assert details.launch_button.isEnabled() is True
    assert details.stop_button.isEnabled() is False


def test_local_session_owner_keeps_stop_control_while_process_runs(
    app,
):
    details = GameDetails()
    details.show_game(
        make_game()
    )

    details.launcher.process_running = Mock(
        return_value=True
    )
    details._launch_session_active = True
    details.sync_process_session()

    assert details.launch_button.isEnabled() is False
    assert details.stop_button.isEnabled() is True


def test_generic_launcher_mock_does_not_invent_running_session(
    app,
):
    launcher = Mock()

    details = GameDetails(
        launcher=launcher,
    )

    details.show_game(
        make_game()
    )

    assert (
        details._process_session_running()
        is False
    )
    assert details.launch_button.isEnabled() is True
    assert details.stop_button.isEnabled() is False


def test_missing_core_failure_is_reported_to_user(
    app,
    monkeypatch,
):
    from PyQt6.QtWidgets import QMessageBox

    details, lifecycle = make_details(app)

    details.core_resolver.find = (
        lambda _core: None
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

    details.launch_game()

    assert len(warnings) == 1

    parent, title, message = warnings[0]

    assert parent is details
    assert title == "Emulator Core Missing"

    assert (
        "RetroVault could not start this game "
        "because its required emulator core "
        "could not be found."
        in message
    )

    assert (
        f"Required core: "
        f"{details.current_game.core}"
        in message
    )

    assert details.launch_status.text() == (
        "Unable to launch: required emulator core "
        "is missing."
    )

    lifecycle.launch_failed.assert_called_once_with()
    lifecycle.launch_result.assert_not_called()


def test_recently_played_update_failure_is_reported_to_user(
    app,
    monkeypatch,
):
    from PyQt6.QtWidgets import QMessageBox

    details, lifecycle = make_details(app)

    details.core_resolver.find = (
        lambda _core: "/cores/fceumm_libretro.so"
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
                "ready": True,
                "issues": [],
            }

    monkeypatch.setattr(
        "ui.library.details.game_details.LaunchValidator",
        ReadyValidator,
    )

    details.diagnostics.explain = (
        lambda _report: ["Launch validation ready."]
    )

    launch_result = {
        "success": True,
        "command": ["retroarch"],
    }

    monkeypatch.setattr(
        details.launcher,
        "launch",
        lambda _profile: launch_result,
    )

    def fail_recent(
        _game,
    ):
        raise OSError(
            "recent persistence failed"
        )

    details.played_handler = fail_recent

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

    details.launch_game()

    assert len(warnings) == 1

    parent, title, message = warnings[0]

    assert parent is details
    assert title == (
        "Recently Played Update Failed"
    )

    assert (
        "RetroVault started the game, but "
        "could not update Recently Played."
        in message
    )

    assert (
        "recent persistence failed"
        in message
    )

    assert details.launch_status.text() == (
        f'Running "{details.current_game.name}".'
    )

    lifecycle.launch_result.assert_called_once_with(
        launch_result
    )
    lifecycle.launch_failed.assert_not_called()
