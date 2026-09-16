from pathlib import Path

path = Path(
    "tests/test_page_manager.py"
)

if path.exists():
    text = path.read_text(
        encoding="utf-8"
    )
else:
    text = '''import pytest

pytest.importorskip(
    "PyQt6"
)

from PyQt6.QtWidgets import (
    QApplication,
    QWidget,
)

from ui.navigation.page_manager import (
    PageManager,
)


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()

    if instance is None:
        instance = QApplication([])

    return instance
'''

test_name = (
    "test_page_manager_refreshes_page_before_activation"
)

if test_name not in text:
    text += '''


def test_page_manager_refreshes_page_before_activation(
    app,
):
    events = []

    class RefreshablePage(QWidget):
        def refresh_page(self):
            events.append(
                "refresh"
            )

    manager = PageManager()

    first = QWidget()
    second = RefreshablePage()

    manager.add_page(
        "First",
        first,
    )
    manager.add_page(
        "Second",
        second,
    )

    manager.setCurrentWidget(
        first
    )

    manager.currentChanged.connect(
        lambda index: events.append(
            "activated"
        )
    )

    manager.show_page(
        "Second"
    )

    assert events == [
        "refresh",
        "activated",
    ]
    assert (
        manager.currentWidget()
        is second
    )


def test_page_manager_supports_page_without_refresh_hook(
    app,
):
    manager = PageManager()
    page = QWidget()

    manager.add_page(
        "Plain",
        page,
    )

    manager.show_page(
        "Plain"
    )

    assert (
        manager.currentWidget()
        is page
    )
'''

path.write_text(
    text,
    encoding="utf-8",
)
