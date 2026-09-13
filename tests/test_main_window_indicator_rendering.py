from pathlib import Path


MAIN = Path(
    "ui/main_window.py"
).read_text(encoding="utf-8")


def test_main_window_imports_hardware_indicator_render_bridge():
    assert (
        "HardwareIndicatorRenderBridge"
        in MAIN
    )


def test_main_window_owns_indicator_render_bridge():
    assert (
        "self.hardware_indicator_render_bridge = ("
        in MAIN
    )

    assert (
        "HardwareIndicatorRenderBridge()"
        in MAIN
    )


def test_main_window_initializes_indicator_render_frame():
    assert (
        "self.hardware_indicator_render_frame = ("
        in MAIN
    )

    assert (
        "self.process_lifecycle.snapshot"
        in MAIN
    )


def test_application_timer_calls_render_aware_poll_adapter():
    assert (
        "self.process_lifecycle_timer.timeout.connect("
        in MAIN
    )

    assert (
        "self._poll_process_lifecycle"
        in MAIN
    )


def test_render_aware_poll_uses_real_lifecycle_snapshot():
    assert (
        "snapshot = self.process_lifecycle.poll()"
        in MAIN
    )


def test_render_aware_poll_updates_current_render_frame():
    assert (
        "self.hardware_indicator_render_bridge.frame_for("
        in MAIN
    )


def test_main_window_does_not_render_artwork_directly():
    method_start = MAIN.index(
        "def _poll_process_lifecycle"
    )

    method_end = MAIN.find(
        "\n    def ",
        method_start + 1,
    )

    if method_end == -1:
        method_end = len(MAIN)

    method = MAIN[
        method_start:
        method_end
    ]

    forbidden = (
        "QPixmap",
        "QPainter",
        "PNG",
        "overlay_runtime",
        "retroarch.cfg",
        "write_text",
        "open(",
    )

    for token in forbidden:
        assert token not in method
