from pathlib import Path


MAIN = Path(
    "ui/main_window.py"
).read_text(encoding="utf-8")


def poll_method():
    start = MAIN.index(
        "def _poll_process_lifecycle"
    )

    end = MAIN.find(
        "\n    def ",
        start + 1,
    )

    if end == -1:
        end = len(MAIN)

    return MAIN[start:end]


def test_main_window_registers_launch_status_details():
    assert (
        "self._launch_status_details = ("
        in MAIN
    )

    assert "library_page.details" in MAIN
    assert "playlists_page.details" in MAIN


def test_process_poll_observes_exited_state():
    method = poll_method()

    assert "self.process_lifecycle.poll()" in method
    assert '== "EXITED"' in method
    assert "details.process_exited()" in method


def test_process_poll_returns_consumed_exit_to_idle():
    method = poll_method()

    assert (
        "self.process_lifecycle"
        in method
    )
    assert (
        ".return_to_idle()"
        in method
    )

    exit_check = method.index(
        '== "EXITED"'
    )
    notify = method.index(
        "details.process_exited()"
    )
    idle = method.index(
        ".return_to_idle()"
    )

    assert exit_check < notify < idle


def test_process_poll_renders_idle_snapshot_after_exit():
    method = poll_method()

    idle = method.index(
        ".return_to_idle()"
    )

    render = method.index(
        "self.hardware_indicator_render_bridge.frame_for(",
        idle,
    )

    assert render > idle
    assert "snapshot" in method[render:]


def test_process_poll_keeps_primary_indicator_render_update():
    method = poll_method()

    first_render = method.index(
        "self.hardware_indicator_render_bridge.frame_for("
    )

    exit_check = method.index(
        '== "EXITED"'
    )

    assert first_render < exit_check


def test_exit_is_consumed_only_inside_exited_branch():
    method = poll_method()

    exit_check = method.index(
        '== "EXITED"'
    )

    idle = method.index(
        ".return_to_idle()"
    )

    assert idle > exit_check
