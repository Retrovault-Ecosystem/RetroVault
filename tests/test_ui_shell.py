import pytest

from PyQt6.QtWidgets import QApplication

from ui.sidebar import Sidebar
from ui.theme import apply_theme


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()

    if instance is None:
        instance = QApplication([])

    return instance


def test_sidebar_has_clear_active_navigation(
    app,
):
    visited = []

    sidebar = Sidebar(
        visited.append
    )

    assert list(
        sidebar.buttons
    ) == [
        "Library",
        "Systems",
        "Playlists",
        "Overlays",
        "RetroVault Visuals",
        "Shaders",
        "RetroArch",
        "Settings",
    ]

    assert (
        sidebar.buttons[
            "Library"
        ].isChecked()
    )

    sidebar.buttons[
        "Systems"
    ].click()

    app.processEvents()

    assert visited == [
        "Systems"
    ]

    assert (
        sidebar.buttons[
            "Systems"
        ].isChecked()
    )

    assert not (
        sidebar.buttons[
            "Library"
        ].isChecked()
    )


def test_theme_covers_navigation_and_browser_controls(
    app,
):
    apply_theme(
        app
    )

    stylesheet = app.styleSheet()

    assert "QPushButton#NavButton:checked" in (
        stylesheet
    )

    assert "QLineEdit" in stylesheet
    assert "QComboBox" in stylesheet
    assert "QListWidget" in stylesheet
    assert "QScrollArea" in stylesheet
