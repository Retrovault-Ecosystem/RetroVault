from unittest.mock import Mock, patch

from models.launch_profile import LaunchProfile
from services.retroarch.launcher import (
    RetroArchLauncher,
)



class FakePrimaryConfigRuntime:
    """Suppress host-dependent primary runtime in focused process tests."""

    def create(self, *, overlay=None, presentation_config=None):
        return None


class FakeSessionConfig:
    """
    This test module verifies process-handle/session lifecycle,
    not RetroVault presentation isolation.

    Suppress the A.2 appendconfig here so the existing assertions
    remain focused on process ownership. Universal session
    composition is tested independently.
    """

    def create(self, core_options_path=None):
        return ""


def make_profile():
    return LaunchProfile(
        game="Duck Tales 2",
        rom="/roms/duck-tales-2.nes",
        core="/cores/fceumm_libretro.so",
    )


def test_launcher_starts_without_owned_process():
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )

    assert launcher.active_process is None
    assert launcher.process_running() is False


def test_successful_launch_retains_exact_popen_handle():
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
        primary_config_runtime=FakePrimaryConfigRuntime(),
    )
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
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )
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
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )
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
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )
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
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )
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
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )
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
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )
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
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )
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


def test_stop_requests_termination_without_releasing_process():
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )
    profile = make_profile()

    process = Mock()
    process.pid = 12345
    process.poll.return_value = None

    with patch(
        "services.retroarch.launcher.subprocess.Popen",
        return_value=process,
    ):
        launcher.launch(profile)

    with (
        patch(
            "services.retroarch.launcher.os.getpgid",
            return_value=12345,
        ),
        patch(
            "services.retroarch.launcher.os.killpg",
        ) as killpg,
    ):
        assert launcher.stop() is True

    import signal

    killpg.assert_called_once_with(
        12345,
        signal.SIGTERM,
    )

    assert launcher.active_process is process


def test_stop_without_owned_process_is_safe():
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )

    assert launcher.stop() is False


def test_stop_does_not_terminate_already_exited_process():
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )
    profile = make_profile()

    process = Mock()
    process.poll.return_value = None

    with patch(
        "services.retroarch.launcher.subprocess.Popen",
        return_value=process,
    ):
        launcher.launch(profile)

    process.poll.return_value = 0

    assert launcher.stop() is False
    process.terminate.assert_not_called()
    assert launcher.active_process is process


def test_launch_starts_retroarch_in_its_own_process_session():
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
        primary_config_runtime=FakePrimaryConfigRuntime(),
    )
    profile = make_profile()

    process = Mock()
    process.poll.return_value = None

    with patch(
        "services.retroarch.launcher.subprocess.Popen",
        return_value=process,
    ) as popen:
        result = launcher.launch(profile)

    assert result["success"] is True

    popen.assert_called_once_with(
        [
            "retroarch",
            "-L",
            "/cores/fceumm_libretro.so",
            "/roms/duck-tales-2.nes",
        ],
        start_new_session=True,
    )


def test_stop_terminates_complete_owned_process_group():
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )
    profile = make_profile()

    process = Mock()
    process.pid = 43210
    process.poll.return_value = None

    with patch(
        "services.retroarch.launcher.subprocess.Popen",
        return_value=process,
    ):
        launcher.launch(profile)

    with (
        patch(
            "services.retroarch.launcher.os.getpgid",
            return_value=43210,
        ) as getpgid,
        patch(
            "services.retroarch.launcher.os.killpg",
        ) as killpg,
    ):
        assert launcher.stop() is True

    getpgid.assert_called_once_with(43210)

    import signal

    killpg.assert_called_once_with(
        43210,
        signal.SIGTERM,
    )

    assert launcher.active_process is process


def test_stop_returns_false_if_owned_process_group_is_gone():
    launcher = RetroArchLauncher(
        session_config=FakeSessionConfig(),
    )
    profile = make_profile()

    process = Mock()
    process.pid = 43211
    process.poll.return_value = None

    with patch(
        "services.retroarch.launcher.subprocess.Popen",
        return_value=process,
    ):
        launcher.launch(profile)

    with patch(
        "services.retroarch.launcher.os.getpgid",
        side_effect=ProcessLookupError,
    ):
        assert launcher.stop() is False

    assert launcher.active_process is process

def test_stop_reaps_owned_launch_root_after_group_signal(monkeypatch):
    """stop() must synchronously reap its launcher-owned Popen root."""
    from services.retroarch import launcher as launcher_module

    events = []

    class Process:
        pid = 43210

        def poll(self):
            return None

        def wait(self, timeout=None):
            events.append(
                ("wait", timeout)
            )
            return -15

    launcher = launcher_module.RetroArchLauncher()
    launcher._active_process = Process()

    monkeypatch.setattr(
        launcher_module.os,
        "getpgid",
        lambda pid: 43210,
    )

    monkeypatch.setattr(
        launcher_module.os,
        "killpg",
        lambda pgid, sig: events.append(
            (
                "killpg",
                pgid,
                sig,
            )
        ),
    )

    assert launcher.stop() is True

    assert events[0][0] == "killpg"

    assert any(
        event[0] == "wait"
        for event in events
    )

    assert launcher._active_process is not None
