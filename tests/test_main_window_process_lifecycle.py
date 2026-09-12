from pathlib import Path

from PyQt6.QtCore import QTimer


MAIN = Path(
    "ui/main_window.py"
).read_text(encoding="utf-8")


def test_main_window_imports_qtimer():
    assert "from PyQt6.QtCore import QTimer" in MAIN


def test_process_lifecycle_timer_is_application_owned():
    assert (
        "self.process_lifecycle_timer = QTimer(self)"
        in MAIN
    )


def test_process_lifecycle_timer_uses_250ms_interval():
    assert (
        "self.process_lifecycle_timer.setInterval(250)"
        in MAIN
    )


def test_process_lifecycle_timer_calls_shared_adapter_poll():
    assert (
        "self.process_lifecycle_timer.timeout.connect("
        in MAIN
    )

    assert (
        "self.process_lifecycle.poll"
        in MAIN
    )


def test_process_lifecycle_timer_starts():
    assert (
        "self.process_lifecycle_timer.start()"
        in MAIN
    )


def test_timer_does_not_collapse_exited_into_idle():
    timer_start = MAIN.index(
        "self.process_lifecycle_timer = QTimer(self)"
    )

    timer_end = MAIN.index(
        "presentation_store = PresentationStore()",
        timer_start,
    )

    timer_block = MAIN[
        timer_start:
        timer_end
    ]

    assert "return_to_idle" not in timer_block


def test_qtimer_type_is_real_pyqt_qtimer():
    assert QTimer is not None
