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


def test_visuals_showroom_theme_contract(
    app,
):
    """
    C.17-A.3 composes the approved RetroVault Visuals
    showroom styling through stable semantic selectors.
    """
    apply_theme(
        app
    )

    stylesheet = app.styleSheet()

    required_selectors = (
        "QLabel#VisualsCollectionTitle",
        "QLabel#VisualsAssignmentTitle",
        "QLabel#VisualsCount",
        "QLineEdit#VisualsSearch",
        "QComboBox#VisualsTypeFilter",
        "QPushButton#VisualsClearFiltersButton",
        "QPushButton#VisualsRefreshButton",
        "QListWidget#VisualsCollectionList",
        "QScrollArea#VisualsDetailsScroll",
        "QFrame#VisualsDetailsPanel",
        "QLabel#VisualsName",
        "QLabel#VisualsPreview",
        "QPushButton#VisualsInstallButton",
        "QPushButton#VisualsAssignDefaultButton",
        "QPushButton#VisualsAssignSystemButton",
        "QPushButton#VisualsAssignGameButton",
        "QPushButton#VisualsClearDefaultButton",
        "QPushButton#VisualsClearSystemButton",
        "QPushButton#VisualsClearGameButton",
        "QLabel#VisualsStatus",
    )

    for selector in required_selectors:
        assert selector in stylesheet


def test_visuals_showroom_refinement_theme_contract(
    app,
):
    apply_theme(
        app
    )

    stylesheet = app.styleSheet()

    required = (
        "QLabel#VisualsMetadataValue",
        "QLabel#VisualsInstallStatus",
        "QLabel#VisualsReferenceValue",
        "QLabel#VisualsAttributionValue",
        "QFrame#VisualsAssignmentSummary",
        "QLabel#VisualsAssignmentValue",
        "QLabel#VisualsEffectiveAssignment",
        "#55c7e8",
    )

    for token in required:
        assert token in stylesheet


def test_visuals_showroom_pass2_theme_contract(
    app,
):
    apply_theme(
        app
    )

    stylesheet = app.styleSheet()

    required = (
        "showroom refinement pass #2",
        "QFrame#VisualsMetadataPanel",
        "QLabel#VisualsMetadataLabel",
        "QListWidget#VisualsCollectionList::item:hover",
        "QPushButton#VisualsInstallButton",
        "QLabel#VisualsStatus",
        "#55c7e8",
    )

    for token in required:
        assert token in stylesheet


def test_systems_showroom_theme_contract():
    from ui.themes.systems import systems_stylesheet

    stylesheet = systems_stylesheet()

    expected_selectors = (
        "QLabel#SystemsTitle",
        "QLabel#SystemsSubtitle",
        "QLabel#SystemsCount",
        "QLabel#SystemsStatus",
        "QLineEdit#SystemsSearch",
        "QListWidget#SystemsList",
        "QFrame#SystemsDetailsPanel",
        "QLabel#SystemsPlatformName",
        "QLabel#SystemsPlatformId",
        "QLabel#SystemsSectionTitle",
        "QLabel#SystemsFieldLabel",
        "QLabel#SystemsFieldValue",
        "QFrame#SystemsLibraryPanel",
        "QLabel#SystemsMetricLabel",
        "QLabel#SystemsMetricValue",
        "QPushButton#SystemsPrimaryAction",
        "QPushButton#SystemsSecondaryAction",
    )

    for selector in expected_selectors:
        assert selector in stylesheet


def test_playlists_showcase_theme_contract():
    from ui.themes.playlists import playlists_stylesheet

    stylesheet = playlists_stylesheet()

    expected_selectors = (
        "QLabel#PlaylistsTitle",
        "QLabel#PlaylistsSubtitle",
        "QFrame#PlaylistsCollectionPanel",
        "QFrame#PlaylistsGamesPanel",
        "QLabel#PlaylistsPanelTitle",
        "QLabel#PlaylistsCollectionTitle",
        "QListWidget#PlaylistsCollectionList",
        "QListWidget#PlaylistsGameList",
        "QLabel#PlaylistsStatus",
        "QPushButton#PlaylistsPrimaryAction",
        "QPushButton#PlaylistsSecondaryAction",
        "QPushButton#PlaylistsDangerAction",
    )

    for selector in expected_selectors:
        assert selector in stylesheet


def test_overlays_control_center_theme_contract():
    from ui.themes.overlays import overlays_stylesheet

    stylesheet = overlays_stylesheet()

    expected_selectors = (
        "QLabel#OverlaysTitle",
        "QLabel#OverlaysSubtitle",
        "QLabel#OverlaysDirectoryLabel",
        "QLabel#OverlaysDirectoryValue",
        "QLabel#OverlaysCount",
        "QListWidget#OverlaysAssetList",
        "QFrame#OverlaysDetailsPanel",
        "QLabel#OverlaysAssetName",
        "QLabel#OverlaysPreview",
        "QLabel#OverlaysFieldLabel",
        "QLabel#OverlaysFieldValue",
        "QLabel#OverlaysReadiness",
        "QLabel#OverlaysAssignmentTitle",
        "QLabel#OverlaysStatus",
        "QPushButton#OverlaysPrimaryAction",
        "QPushButton#OverlaysSecondaryAction",
        "QPushButton#OverlaysAssignmentAction",
    )

    for selector in expected_selectors:
        assert selector in stylesheet
