from unittest.mock import Mock, patch

from models.launch_profile import LaunchProfile
from services.retroarch.launcher import (
    RetroArchLauncher,
)


def make_profile():
    return LaunchProfile(
        game="Duck Tales 2",
        rom="/roms/duck-tales-2.nes",
        core="/cores/fceumm_libretro.so",
    )


def test_launcher_starts_without_owned_process():
    launcher = RetroArchLauncher()

    assert launcher.active_process is None
    assert launcher.process_running() is False


def test_successful_launch_retains_exact_popen_handle():
    launcher = RetroArchLauncher()
    profile = make_profile()

    process = Mock()
    process.poll.return_value = None

    with patch(
        "services.retroarch.launcher.subprocess.Popen",
        return_value=process,
    ):
        result = launcher.launch(profile)

    assert result == {
        "success": True,
        "command": [
            "retroarch",
            "-L",
            "/cores/fceumm_libretro.so",
            "/roms/duck-tales-2.nes",
        ],
    }

    assert launcher.active_process is process
    assert launcher.process_running() is True


def test_process_running_uses_real_process_poll_state():
    launcher = RetroArchLauncher()
    profile = make_profile()

    process = Mock()
    process.poll.return_value = None

    with patch(
        "services.retroarch.launcher.subprocess.Popen",
        return_value=process,
    ):
        launcher.launch(profile)

    assert launcher.process_running() is True

    process.poll.return_value = 0

    assert launcher.process_running() is False


def test_clear_exited_process_releases_only_dead_process():
    launcher = RetroArchLauncher()
    profile = make_profile()

    process = Mock()
    process.poll.return_value = None

    with patch(
        "services.retroarch.launcher.subprocess.Popen",
        return_value=process,
    ):
        launcher.launch(profile)

    assert launcher.clear_exited_process() is None
    assert launcher.active_process is process

    process.poll.return_value = 0

    released = launcher.clear_exited_process()

    assert released is process
    assert launcher.active_process is None
    assert launcher.process_running() is False


def test_nonzero_exit_is_still_an_exited_process():
    launcher = RetroArchLauncher()
    profile = make_profile()

    process = Mock()
    process.poll.return_value = None

    with patch(
        "services.retroarch.launcher.subprocess.Popen",
        return_value=process,
    ):
        launcher.launch(profile)

    process.poll.return_value = 7

    released = launcher.clear_exited_process()

    assert released is process
    assert launcher.active_process is None


def test_spawn_failure_does_not_retain_process():
    launcher = RetroArchLauncher()
    profile = make_profile()

    with patch(
        "services.retroarch.launcher.subprocess.Popen",
        side_effect=OSError("spawn failed"),
    ):
        result = launcher.launch(profile)

    assert result == {
        "success": False,
        "error": "spawn failed",
    }

    assert launcher.active_process is None
    assert launcher.process_running() is False


def test_second_launch_is_rejected_while_process_is_running():
    launcher = RetroArchLauncher()
    profile = make_profile()

    process = Mock()
    process.poll.return_value = None

    with patch(
        "services.retroarch.launcher.subprocess.Popen",
        return_value=process,
    ) as popen:
        first_result = launcher.launch(profile)
        second_result = launcher.launch(profile)

    assert first_result["success"] is True

    assert second_result == {
        "success": False,
        "error": "RetroArch process is already running.",
    }

    assert launcher.active_process is process
    assert launcher.process_running() is True

    popen.assert_called_once()


def test_exited_owned_process_is_replaced_by_new_launch():
    launcher = RetroArchLauncher()
    profile = make_profile()

    first = Mock()
    first.poll.return_value = None

    second = Mock()
    second.poll.return_value = None

    with patch(
        "services.retroarch.launcher.subprocess.Popen",
        side_effect=[first, second],
    ):
        first_result = launcher.launch(profile)

        assert first_result["success"] is True
        assert launcher.active_process is first

        first.poll.return_value = 0

        second_result = launcher.launch(profile)

    assert second_result["success"] is True
    assert launcher.active_process is second
    assert launcher.process_running() is True


def test_rejected_second_launch_preserves_original_handle():
    launcher = RetroArchLauncher()
    profile = make_profile()

    process = Mock()
    process.poll.return_value = None

    with patch(
        "services.retroarch.launcher.subprocess.Popen",
        return_value=process,
    ):
        launcher.launch(profile)
        result = launcher.launch(profile)

    assert result["success"] is False
    assert launcher.active_process is process
