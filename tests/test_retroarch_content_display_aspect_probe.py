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
    monkeypatch.setattr(
        "services.retroarch.content_display_aspect_probe.os.getpgid",
        lambda pid: pid,
    )
    monkeypatch.setattr(
        "services.retroarch.content_display_aspect_probe.os.killpg",
        lambda pgid, sig: None,
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
    ) == 2

    assert "--set-shader" in command
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
