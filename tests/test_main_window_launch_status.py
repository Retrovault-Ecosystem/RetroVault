from pathlib import Path


MAIN = Path(
    "ui/main_window.py"
).read_text(encoding="utf-8")


def test_main_window_registers_launch_status_details():
    assert (
        "self._launch_status_details = ("
        in MAIN
    )

    assert "library_page.details" in MAIN
    assert "playlists_page.details" in MAIN


def test_process_poll_observes_exited_state():
    start = MAIN.index(
        "def _poll_process_lifecycle"
    )

    end = MAIN.find(
        "\n    def ",
        start + 1,
    )

    if end == -1:
        end = len(MAIN)

    method = MAIN[start:end]

    assert "self.process_lifecycle.poll()" in method
    assert '== "EXITED"' in method
    assert "details.process_exited()" in method


def test_process_poll_does_not_force_idle():
    start = MAIN.index(
        "def _poll_process_lifecycle"
    )

    end = MAIN.find(
        "\n    def ",
        start + 1,
    )

    if end == -1:
        end = len(MAIN)

    method = MAIN[start:end]

    assert "return_to_idle" not in method


def test_process_poll_keeps_indicator_render_update():
    start = MAIN.index(
        "def _poll_process_lifecycle"
    )

    end = MAIN.find(
        "\n    def ",
        start + 1,
    )

    if end == -1:
        end = len(MAIN)

    method = MAIN[start:end]

    assert (
        "self.hardware_indicator_render_bridge.frame_for("
        in method
    )
