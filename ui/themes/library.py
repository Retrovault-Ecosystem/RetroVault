"""RetroVault Library presentation-studio theme."""


def _library_base_stylesheet():
    """Return presentation styling owned by the Library surface."""

    return """
    /* ============================================================
       RetroVault Library — presentation studio
       ============================================================ */

    QWidget#LibraryPage {
        background: #0b1119;
    }

    QLabel#LibraryTitle {
        color: #f4f8ff;
        font-size: 26px;
        font-weight: 700;
    }

    QLabel#LibrarySubtitle {
        color: #8fa7c4;
        font-size: 14px;
    }

    QWidget#LibraryToolbar {
        background: #101b29;
        border: 1px solid #22384f;
        border-radius: 11px;
    }

    QWidget#LibraryToolbar QLineEdit,
    QWidget#LibraryToolbar QComboBox {
        min-height: 32px;
        padding: 0 10px;
        color: #edf6ff;
        background: #0d1724;
        border: 1px solid #29425c;
        border-radius: 7px;
    }

    QWidget#LibraryToolbar QLineEdit:hover,
    QWidget#LibraryToolbar QComboBox:hover {
        border-color: #3b6688;
        background: #101d2c;
    }

    QWidget#LibraryToolbar QLineEdit:focus,
    QWidget#LibraryToolbar QComboBox:focus {
        border-color: #55c7e8;
        background: #132437;
    }

    QWidget#LibraryToolbar QPushButton {
        min-height: 32px;
        padding: 0 10px;
        color: #d8e8f7;
        background: #152435;
        border: 1px solid #29445e;
        border-radius: 7px;
        font-weight: 600;
    }

    QWidget#LibraryToolbar QPushButton:hover {
        color: #ffffff;
        background: #1b3147;
        border-color: #55a7d2;
    }

    QWidget#LibraryToolbar QPushButton:checked {
        color: #ffffff;
        background: #176f9f;
        border-color: #55c7e8;
    }

    QWidget#LibraryToolbar QPushButton:disabled {
        color: #53677c;
        background: #111a24;
        border-color: #1e2b38;
    }

    QLabel#libraryRefreshStatus {
        color: #7fd7ff;
        font-size: 11px;
        font-weight: 600;
    }

    QWidget#LibraryViewSelector {
        background: transparent;
    }

    QWidget#LibraryViewSelector QPushButton:checked {
        color: #ffffff;
        background: #155f89;
        border-color: #55c7e8;
    }

    QStackedWidget#LibraryViewStack {
        background: #0d1622;
        border: 1px solid #203247;
        border-radius: 12px;
    }

    QWidget#LibraryGrid,
    QWidget#LibraryGridContainer {
        background: transparent;
    }

    QScrollArea#LibraryGridScroll {
        background: transparent;
        border: none;
    }

    QWidget#LibraryGameCard {
        background: #101b29;
        border: 1px solid #22384f;
        border-radius: 12px;
    }

    QWidget#LibraryGameCard:hover {
        background: #142538;
        border: 1px solid #55c7e8;
    }

    QLabel#LibraryGameCover {
        color: #55c7e8;
        background: #0a121c;
        border: 1px solid #263b51;
        border-radius: 8px;
        font-size: 34px;
    }

    QLabel#LibraryGameTitle {
        color: #f2f7fc;
        font-size: 13px;
        font-weight: 700;
        background: transparent;
        border: none;
    }

    QLabel#LibraryGameInfo {
        color: #88a3be;
        font-size: 11px;
        background: transparent;
        border: none;
    }

    QWidget#LibraryDetailsView,
    QWidget#LibraryCompactView {
        background: transparent;
    }

    QListWidget#LibraryDetailsList,
    QListWidget#LibraryCompactList {
        color: #dce9f7;
        background: #0d1622;
        border: none;
        border-radius: 10px;
        outline: 0;
        padding: 6px;
    }

    QListWidget#LibraryDetailsList::item {
        min-height: 58px;
        padding: 9px 11px;
        margin: 3px;
        border: 1px solid #1d3044;
        border-radius: 8px;
        background: #101c2a;
    }

    QListWidget#LibraryDetailsList::item:hover,
    QListWidget#LibraryCompactList::item:hover {
        color: #ffffff;
        background: #172b40;
    }

    QListWidget#LibraryDetailsList::item:selected,
    QListWidget#LibraryCompactList::item:selected {
        color: #ffffff;
        background: #1d5375;
        border: 1px solid #55c7e8;
    }

    QListWidget#LibraryCompactList::item {
        min-height: 32px;
        padding: 6px 10px;
        margin: 2px;
        border-radius: 6px;
    }

    QWidget#LibraryGameDetails {
        background: #101b29;
        border: 1px solid #22384f;
        border-radius: 12px;
    }

    QLabel#LibraryDetailsCover {
        color: #55c7e8;
        background: #0a121c;
        border: 1px solid #29445e;
        border-radius: 10px;
        font-size: 42px;
    }

    QLabel#LibraryDetailsTitle {
        color: #ffffff;
        font-size: 21px;
        font-weight: 700;
    }

    QLabel#LibraryDetailsMetadata {
        color: #8fa7c4;
        font-size: 12px;
    }

    QTextEdit#LibraryDetailsDescription {
        color: #dce9f7;
        background: #0c1622;
        border: 1px solid #20364c;
        border-radius: 8px;
        padding: 8px;
    }

    QLabel#LibraryLaunchProfile {
        color: #8fdcff;
        font-size: 13px;
        font-weight: 700;
    }

    QLabel#LibraryLaunchStatus {
        color: #91a8c2;
        font-size: 11px;
    }

    QPushButton#LibraryFavoriteAction,
    QPushButton#LibraryCollectionAction,
    QPushButton#LibraryStopAction {
        min-height: 32px;
        color: #d8e8f7;
        background: #152435;
        border: 1px solid #29445e;
        border-radius: 7px;
        font-weight: 600;
    }

    QPushButton#LibraryFavoriteAction:hover,
    QPushButton#LibraryCollectionAction:hover,
    QPushButton#LibraryStopAction:hover {
        color: #ffffff;
        background: #1b3147;
        border-color: #55a7d2;
    }

    QPushButton#LibraryLaunchAction {
        min-height: 36px;
        color: #f7fcff;
        background: #176f9f;
        border: 1px solid #55c7e8;
        border-radius: 7px;
        font-weight: 700;
    }

    QPushButton#LibraryLaunchAction:hover {
        background: #1d83b9;
        border-color: #7ddcff;
    }

    QPushButton#LibraryLaunchAction:pressed {
        background: #135d86;
    }

    QPushButton#LibraryLaunchAction:disabled,
    QPushButton#LibraryFavoriteAction:disabled,
    QPushButton#LibraryCollectionAction:disabled,
    QPushButton#LibraryStopAction:disabled {
        color: #53677c;
        background: #111a24;
        border-color: #1e2b38;
    }
    """


def library_variant_launcher_stylesheet():
    return """
QDialog#LibraryEditionLauncher {
    background: #0b1119;
}

QLabel#LibraryEditionEyebrow {
    color: #55c7e8;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}

QLabel#LibraryEditionTitle {
    color: #f4f8ff;
    font-size: 24px;
    font-weight: 700;
}

QLabel#LibraryEditionSubtitle {
    color: #8fa7c4;
    font-size: 13px;
}

QScrollArea#LibraryEditionScroll {
    background: transparent;
    border: none;
}

QWidget#LibraryEditionContent {
    background: transparent;
}

QFrame#LibraryEditionGroup {
    background: #101b29;
    border: 1px solid #22384f;
    border-radius: 10px;
}

QLabel#LibraryEditionGroupTitle {
    color: #7fd7ff;
    font-size: 14px;
    font-weight: 700;
}

QFrame#LibraryEditionRow {
    background: #0d1722;
    border: 1px solid #1b3044;
    border-radius: 8px;
}

QFrame#LibraryEditionRow:hover {
    border: 1px solid #55c7e8;
    background: #112131;
}

QRadioButton#LibraryEditionChoice {
    color: #f4f8ff;
    font-size: 13px;
    font-weight: 600;
    spacing: 9px;
}

QRadioButton#LibraryEditionChoice::indicator {
    width: 16px;
    height: 16px;
}

QLabel#LibraryEditionDetail {
    color: #7189a5;
    font-size: 11px;
    padding-left: 25px;
}

QPushButton#LibraryEditionCancel {
    background: #162333;
    color: #b8c8da;
    border: 1px solid #2a4057;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 600;
}

QPushButton#LibraryEditionCancel:hover {
    background: #1b2d40;
    border-color: #3b5875;
    color: #f4f8ff;
}

QPushButton#LibraryEditionLaunch {
    background: #167da1;
    color: #ffffff;
    border: 1px solid #55c7e8;
    border-radius: 8px;
    padding: 9px 20px;
    font-weight: 700;
}

QPushButton#LibraryEditionLaunch:hover {
    background: #1b91b8;
}

QPushButton#LibraryEditionLaunch:disabled {
    background: #152333;
    color: #5f7389;
    border-color: #263b50;
}

QLabel#LibraryGameEditionCount {
    color: #55c7e8;
    background: #102536;
    border: 1px solid #28506a;
    border-radius: 7px;
    padding: 3px 7px;
    font-size: 10px;
    font-weight: 700;
}
"""


def library_stylesheet():
    return (
        _library_base_stylesheet()
        + library_variant_launcher_stylesheet()
        + library_cheat_studio_stylesheet()
    )


def library_cheat_studio_stylesheet():
    return """
QDialog#LibraryCheatStudio {
    background: #0b1119;
}

QLabel#LibraryCheatEyebrow {
    color: #55c7e8;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
}

QLabel#LibraryCheatTitle {
    color: #f4f8ff;
    font-size: 24px;
    font-weight: 700;
}

QLabel#LibraryCheatEdition {
    color: #8fa7c4;
    font-size: 13px;
}

QLabel#LibraryCheatWarning {
    color: #d6c58d;
    background: #1a1a16;
    border: 1px solid #554d2f;
    border-radius: 8px;
    padding: 9px 11px;
    font-size: 11px;
}

QLineEdit#LibraryCheatSearch {
    min-height: 34px;
    color: #edf6ff;
    background: #0d1724;
    border: 1px solid #29425c;
    border-radius: 7px;
    padding: 0 10px;
}

QLineEdit#LibraryCheatSearch:focus {
    border-color: #55c7e8;
    background: #132437;
}

QLineEdit#LibraryCheatManualName,
QLineEdit#LibraryCheatManualCode,
QComboBox#LibraryCheatManualType {
    min-height: 32px;
    color: #edf6ff;
    background: #0d1724;
    border: 1px solid #29425c;
    border-radius: 7px;
    padding: 0 9px;
}

QScrollArea#LibraryCheatScroll {
    background: transparent;
    border: none;
}

QWidget#LibraryCheatContent {
    background: transparent;
}

QFrame#LibraryCheatGroup {
    background: #101b29;
    border: 1px solid #22384f;
    border-radius: 10px;
}

QLabel#LibraryCheatGroupTitle {
    color: #7fd7ff;
    font-size: 14px;
    font-weight: 700;
}

QFrame#LibraryCheatRow {
    background: #0d1722;
    border: 1px solid #1b3044;
    border-radius: 8px;
}

QFrame#LibraryCheatRow:hover {
    background: #112131;
    border-color: #3e7393;
}

QCheckBox#LibraryCheatChoice {
    color: #f4f8ff;
    font-size: 13px;
    font-weight: 600;
    spacing: 9px;
}

QCheckBox#LibraryCheatChoice:disabled {
    color: #66788b;
}

QLabel#LibraryCheatDetail {
    color: #7189a5;
    font-size: 11px;
    padding-left: 25px;
}

QLabel#LibraryCheatIncompatible {
    color: #d29b82;
    font-size: 11px;
    padding-left: 25px;
}

QLabel#LibraryCheatEmpty {
    color: #8fa7c4;
    background: #101b29;
    border: 1px solid #22384f;
    border-radius: 9px;
    padding: 18px;
}

QLabel#LibraryCheatFeedback {
    color: #7fd7ff;
    background: #102536;
    border: 1px solid #28506a;
    border-radius: 7px;
    padding: 7px 9px;
    font-size: 11px;
}

QPushButton#LibraryCheatEnableAll,
QPushButton#LibraryCheatDisableAll,
QPushButton#LibraryCheatAdd,
QPushButton#LibraryCheatImport,
QPushButton#LibraryCheatCancel,
QPushButton#LibraryCheatWithout {
    min-height: 32px;
    color: #d8e8f7;
    background: #152435;
    border: 1px solid #29445e;
    border-radius: 7px;
    padding: 0 11px;
    font-weight: 600;
}

QPushButton#LibraryCheatEnableAll:hover,
QPushButton#LibraryCheatDisableAll:hover,
QPushButton#LibraryCheatAdd:hover,
QPushButton#LibraryCheatImport:hover,
QPushButton#LibraryCheatCancel:hover,
QPushButton#LibraryCheatWithout:hover {
    color: #ffffff;
    background: #1b3147;
    border-color: #55a7d2;
}

QPushButton#LibraryCheatLaunch {
    min-height: 36px;
    color: #ffffff;
    background: #167da1;
    border: 1px solid #55c7e8;
    border-radius: 8px;
    padding: 0 18px;
    font-weight: 700;
}

QPushButton#LibraryCheatLaunch:hover {
    background: #1b91b8;
}
"""


def library_presentation_studio_stylesheet():
    return """
QWidget#LibraryPresentationStudio {
    background: #0d1722;
    border: 1px solid #29445e;
    border-radius: 10px;
}

QLabel#LibraryPresentationEyebrow {
    color: #55c7e8;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}

QLabel#LibraryPresentationTitle {
    color: #f4f8ff;
    font-size: 17px;
    font-weight: 700;
}

QLabel#LibraryPresentationStatus {
    color: #8fa7c4;
    font-size: 11px;
}

QFrame#LibraryPresentationPanel {
    background: #0a131e;
    border: 1px solid #20364c;
    border-radius: 8px;
}

QLabel#LibraryPresentationCaption {
    color: #7189a5;
    font-size: 10px;
    font-weight: 600;
}

QLabel#LibraryPresentationValue {
    color: #e8f4ff;
    font-size: 11px;
    font-weight: 600;
}

QLabel#LibraryPresentationOverride {
    color: #7fd7ff;
    font-size: 10px;
    font-weight: 600;
}

QPushButton#LibraryPresentationRefresh {
    min-height: 30px;
    padding: 0 12px;
    color: #d8e8f7;
    background: #152435;
    border: 1px solid #29445e;
    border-radius: 7px;
    font-weight: 600;
}

QPushButton#LibraryPresentationRefresh:hover {
    color: #ffffff;
    background: #1b3147;
    border-color: #55c7e8;
}

QPushButton#LibraryPresentationRefresh:disabled {
    color: #53677c;
    background: #111a24;
    border-color: #1e2b38;
}
"""


_original_library_stylesheet = library_stylesheet


def library_stylesheet():
    return (
        _original_library_stylesheet()
        + library_presentation_studio_stylesheet()
    )


def library_presentation_studio_polish_stylesheet():
    return """
QWidget#LibraryPresentationStudio {
    background: #0b1621;
    border: 1px solid #31506b;
    border-radius: 12px;
}

QLabel#LibraryPresentationEyebrow {
    color: #5dd7f7;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1px;
}

QLabel#LibraryPresentationTitle {
    color: #f7fbff;
    font-size: 18px;
    font-weight: 800;
}

QLabel#LibraryPresentationStatus {
    color: #9cb2c9;
    font-size: 11px;
}

QLabel#LibraryPresentationSection {
    color: #55c7e8;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1px;
    padding-top: 3px;
}

QLabel#LibraryPresentationHint {
    color: #7189a5;
    font-size: 10px;
    padding-bottom: 2px;
}

QFrame#LibraryPresentationPanel {
    background: #08121c;
    border: 1px solid #274159;
    border-radius: 9px;
}

QLabel#LibraryPresentationCaption {
    color: #7891aa;
    font-size: 10px;
    font-weight: 700;
}

QLabel#LibraryPresentationValue {
    color: #edf8ff;
    font-size: 11px;
    font-weight: 700;
}

QLabel#LibraryPresentationOverride {
    color: #8de5ff;
    background: #102434;
    border: 1px solid #25475e;
    border-radius: 6px;
    padding: 6px 9px;
    font-size: 10px;
    font-weight: 700;
}

QPushButton#LibraryPresentationAssignOverlay,
QPushButton#LibraryPresentationAssignShader {
    min-height: 32px;
    color: #ffffff;
    background: #167da1;
    border: 1px solid #55c7e8;
    border-radius: 7px;
    padding: 0 10px;
    font-weight: 700;
}

QPushButton#LibraryPresentationAssignOverlay:hover,
QPushButton#LibraryPresentationAssignShader:hover {
    background: #1b91b8;
    border-color: #8de5ff;
}

QPushButton#LibraryPresentationClearOverlay,
QPushButton#LibraryPresentationClearShader {
    min-height: 32px;
    color: #c8d8e8;
    background: #142333;
    border: 1px solid #36516a;
    border-radius: 7px;
    padding: 0 10px;
    font-weight: 650;
}

QPushButton#LibraryPresentationClearOverlay:hover,
QPushButton#LibraryPresentationClearShader:hover {
    color: #ffffff;
    background: #1b3147;
    border-color: #55c7e8;
}

QPushButton#LibraryPresentationRefresh {
    min-height: 30px;
    color: #cfe3f4;
    background: transparent;
    border: 1px solid #31506b;
    border-radius: 7px;
    padding: 0 12px;
    font-weight: 650;
}

QPushButton#LibraryPresentationRefresh:hover {
    color: #ffffff;
    background: #162b3e;
    border-color: #55c7e8;
}

QPushButton#LibraryPresentationAssignOverlay:disabled,
QPushButton#LibraryPresentationAssignShader:disabled,
QPushButton#LibraryPresentationClearOverlay:disabled,
QPushButton#LibraryPresentationClearShader:disabled,
QPushButton#LibraryPresentationRefresh:disabled {
    color: #52687b;
    background: #101a24;
    border-color: #1d2d3b;
}
"""


_library_stylesheet_with_presentation_studio = library_stylesheet


def library_stylesheet():
    return (
        _library_stylesheet_with_presentation_studio()
        + library_presentation_studio_polish_stylesheet()
    )


def library_game_details_scroll_stylesheet():
    return """
QScrollArea#LibraryGameDetailsScroll {
    background: transparent;
    border: none;
}

QScrollArea#LibraryGameDetailsScroll > QWidget > QWidget {
    background: transparent;
}

QWidget#LibraryGameDetailsContent {
    background: transparent;
}

QScrollBar:vertical {
    width: 8px;
    background: #0b141e;
    margin: 0;
}

QScrollBar::handle:vertical {
    min-height: 28px;
    background: #29445e;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #3a607e;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: transparent;
}
"""


_library_stylesheet_with_game_details_scroll = library_stylesheet


def library_stylesheet():
    return (
        _library_stylesheet_with_game_details_scroll()
        + library_game_details_scroll_stylesheet()
    )
