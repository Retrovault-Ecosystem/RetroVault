from pathlib import Path

import pytest

from services.retroarch.content_display_aspect_probe import (
    ContentLoadedDisplayAspectProbe,
)


class FakeProcess:
    def __init__(self):
        self.pid = 4242
        self.returncode = None
        self.wait_calls = []

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
        self.wait_calls.append(timeout)
        self.returncode = 0
        return 0


def _isolate_process_group(monkeypatch):
    state = {
        "alive": True,
    }

    monkeypatch.setattr(
        "services.retroarch.content_display_aspect_probe.os.getpgid",
        lambda pid: pid,
    )

    def killpg(pgid, sig):
        if sig == 0:
            if not state["alive"]:
                raise ProcessLookupError
            return None

        state["alive"] = False
        return None

    monkeypatch.setattr(
        "services.retroarch.content_display_aspect_probe.os.killpg",
        killpg,
    )


def test_probe_builds_verbose_log_command_and_returns_runtime_aspect(
    tmp_path,
    monkeypatch,
):
    process = FakeProcess()
    captured = {}

    clock = {"value": 0.0}

    def monotonic():
        value = clock["value"]
        clock["value"] += 0.05
        return value

    def popen(command, **kwargs):
        captured["command"] = list(command)
        captured["kwargs"] = kwargs
        layers = command[command.index("--appendconfig") + 1].split("|")
        captured["headless_path"] = Path(layers[-1])
        captured["headless"] = Path(layers[-1]).read_text()
        save_directory = Path(layers[-1]).parent / "FCEUmm"
        save_directory.mkdir()
        (save_directory / "probe.srm").write_bytes(b"probe-only")

        log_path = Path(
            command[
                command.index("--log-file") + 1
            ]
        )

        log_path.write_text(
            "[INFO] [Core] Geometry: 256x224, Aspect: 1.306\n",
            encoding="utf-8",
        )

        return process

    _isolate_process_group(
        monkeypatch
    )

    probe = ContentLoadedDisplayAspectProbe(
        directory=tmp_path,
        timeout=1.0,
        settle_time=0.10,
        poll_interval=0.01,
        monotonic_fn=monotonic,
        sleep_fn=lambda value: None,
        popen_factory=popen,
    )

    aspect = probe.acquire(
        command="retroarch",
        core="/core.so",
        content="/game.rom",
        prefix_args=(
            "--config",
            "/primary.cfg",
        ),
        append_configs=(
            "/session.cfg",
            "/overlay.cfg",
        ),
        shader="/shader.slangp",
    )

    assert aspect.ratio == pytest.approx(
        1.306
    )

    command = captured["command"]

    assert command[:3] == [
        "retroarch",
        "--config",
        "/primary.cfg",
    ]

    assert command[3:6] == [
        "-L",
        "/core.so",
        "/game.rom",
    ]

    assert command.count(
        "--appendconfig"
    ) == 1
    layers = command[command.index("--appendconfig") + 1].split("|")
    assert layers[:2] == ["/session.cfg", "/overlay.cfg"]
    assert len(layers) == 3
    for setting in ('video_driver = "null"', 'audio_driver = "null"',
                    'input_driver = "null"', 'video_shader_enable = "false"',
                    'input_overlay_enable = "false"', 'config_save_on_exit = "false"'):
        assert setting in captured["headless"]
    assert not captured["headless_path"].parent.exists()
    assert "--set-shader" not in command
    assert "--verbose" in command
    assert "--log-file" in command

    assert (
        captured["kwargs"][
            "start_new_session"
        ]
        is True
    )

    assert process.returncode == 0


def test_runtime_set_geometry_supersedes_initial_core_geometry(
    tmp_path,
    monkeypatch,
):
    process = FakeProcess()

    clock = {"value": 0.0}

    def monotonic():
        value = clock["value"]
        clock["value"] += 0.05
        return value

    def popen(command, **kwargs):
        log_path = Path(
            command[
                command.index("--log-file") + 1
            ]
        )

        log_path.write_text(
            "[INFO] [Core] Geometry: "
            "256x192, Aspect: 1.524\n"
            "[INFO] [Environ] SET_GEOMETRY: "
            "320x224, Aspect: 1.306\n",
            encoding="utf-8",
        )

        return process

    _isolate_process_group(
        monkeypatch
    )

    probe = ContentLoadedDisplayAspectProbe(
        directory=tmp_path,
        timeout=1.0,
        settle_time=0.10,
        poll_interval=0.01,
        monotonic_fn=monotonic,
        sleep_fn=lambda value: None,
        popen_factory=popen,
    )

    aspect = probe.acquire(
        command="retroarch",
        core="/core.so",
        content="/game.rom",
    )

    assert aspect.ratio == pytest.approx(
        1.306
    )


def test_probe_fails_closed_when_process_exits_without_geometry(
    tmp_path,
    monkeypatch,
):
    class ExitedProcess(FakeProcess):
        def poll(self):
            return 1

    process = ExitedProcess()

    def popen(command, **kwargs):
        return process

    _isolate_process_group(
        monkeypatch
    )

    probe = ContentLoadedDisplayAspectProbe(
        directory=tmp_path,
        timeout=1.0,
        settle_time=0.10,
        poll_interval=0.01,
        monotonic_fn=lambda: 0.0,
        sleep_fn=lambda value: None,
        popen_factory=popen,
    )

    with pytest.raises(
        ValueError,
        match="before reporting valid libretro geometry",
    ):
        probe.acquire(
            command="retroarch",
            core="/core.so",
            content="/game.rom",
        )


def test_probe_is_content_identity_independent():
    import inspect

    source = inspect.getsource(
        ContentLoadedDisplayAspectProbe
    ).casefold()

    for forbidden in (
        "duck tales",
        "ducktales",
        "street fighter",
        "sonic the hedgehog",
    ):
        assert forbidden not in source


def test_reap_checks_group_after_direct_wrapper_has_exited(
    monkeypatch,
):
    import signal

    class ExitedProcess:
        pid = 7001

        def poll(self):
            return 0

        def wait(self, timeout=None):
            return 0

    probe = ContentLoadedDisplayAspectProbe(
        timeout=1.0,
        settle_time=0.0,
        poll_interval=0.01,
    )

    state = {"alive": True}
    signals = []

    def exists(group):
        assert group == 7001
        return state["alive"]

    def killpg(group, sig):
        assert group == 7001
        signals.append(sig)
        state["alive"] = False

    monkeypatch.setattr(
        probe,
        "_process_group_exists",
        exists,
    )
    monkeypatch.setattr(
        "services.retroarch.content_display_aspect_probe.os.killpg",
        killpg,
    )

    probe._terminate_and_reap(
        ExitedProcess(),
        process_group=7001,
    )

    assert signals == [signal.SIGTERM]
    assert state["alive"] is False


def test_reap_escalates_when_group_survives_sigterm(
    monkeypatch,
):
    import signal

    class ExitedProcess:
        pid = 7002

        def poll(self):
            return 0

        def wait(self, timeout=None):
            return 0

    clock = {"value": 0.0}

    probe = ContentLoadedDisplayAspectProbe(
        timeout=1.0,
        settle_time=0.0,
        poll_interval=1.0,
        monotonic_fn=lambda: clock["value"],
        sleep_fn=lambda value: clock.__setitem__(
            "value",
            clock["value"] + value,
        ),
    )

    state = {"alive": True}
    signals = []

    monkeypatch.setattr(
        probe,
        "_process_group_exists",
        lambda group: state["alive"],
    )

    def killpg(group, sig):
        signals.append(sig)
        if sig == signal.SIGKILL:
            state["alive"] = False

    monkeypatch.setattr(
        "services.retroarch.content_display_aspect_probe.os.killpg",
        killpg,
    )

    probe._terminate_and_reap(
        ExitedProcess(),
        process_group=7002,
    )

    assert signals == [
        signal.SIGTERM,
        signal.SIGKILL,
    ]
    assert state["alive"] is False


def test_reap_fails_closed_if_owned_group_survives_sigkill(
    monkeypatch,
):
    class ExitedProcess:
        pid = 7003

        def poll(self):
            return 0

        def wait(self, timeout=None):
            return 0

    clock = {"value": 0.0}

    probe = ContentLoadedDisplayAspectProbe(
        timeout=1.0,
        settle_time=0.0,
        poll_interval=1.0,
        monotonic_fn=lambda: clock["value"],
        sleep_fn=lambda value: clock.__setitem__(
            "value",
            clock["value"] + value,
        ),
    )

    monkeypatch.setattr(
        probe,
        "_process_group_exists",
        lambda group: True,
    )

    monkeypatch.setattr(
        "services.retroarch.content_display_aspect_probe.os.killpg",
        lambda group, sig: None,
    )

    with pytest.raises(
        OSError,
        match="process group did not terminate",
    ):
        probe._terminate_and_reap(
            ExitedProcess(),
            process_group=7003,
        )
