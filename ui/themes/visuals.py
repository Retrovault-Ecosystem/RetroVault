"""Premium styling for the RetroVault Visuals production surface."""


def visuals_stylesheet():
    """
    Return page-specific QSS for RetroVault Visuals.

    Object-name selectors keep this presentation layer isolated
    from the functional C.16 Visuals contracts.
    """

    return """
    /* =========================================================
       RetroVault Visuals — premium showroom surface
       ========================================================= */

    QLabel#VisualsCollectionTitle,
    QLabel#VisualsAssignmentTitle {
        color: #f5f5f5;
        font-size: 17px;
        font-weight: 700;
        padding-top: 2px;
        padding-bottom: 2px;
    }

    QLabel#VisualsCount {
        color: #858b93;
        font-size: 12px;
        padding-left: 2px;
        padding-bottom: 2px;
    }

    QLineEdit#VisualsSearch,
    QComboBox#VisualsTypeFilter {
        background-color: #17191c;
        color: #f0f0f0;
        border: 1px solid #353a40;
        border-radius: 8px;
        padding: 8px 11px;
        min-height: 24px;
    }

    QLineEdit#VisualsSearch:hover,
    QComboBox#VisualsTypeFilter:hover {
        background-color: #1b1e22;
        border-color: #484e55;
    }

    QLineEdit#VisualsSearch:focus,
    QComboBox#VisualsTypeFilter:focus {
        background-color: #1c1f23;
        border-color: #727981;
    }

    QPushButton#VisualsClearFiltersButton,
    QPushButton#VisualsRefreshButton {
        background-color: #1b1d20;
        color: #c5c9ce;
        border: 1px solid #34383d;
        border-radius: 8px;
        padding: 8px 13px;
    }

    QPushButton#VisualsClearFiltersButton:hover,
    QPushButton#VisualsRefreshButton:hover {
        background-color: #25282c;
        color: #ffffff;
        border-color: #4b5057;
    }

    QListWidget#VisualsCollectionList {
        background-color: #141619;
        border: 1px solid #30343a;
        border-radius: 10px;
        outline: none;
        padding: 7px;
    }

    QListWidget#VisualsCollectionList::item {
        color: #d9dde1;
        border: 1px solid transparent;
        border-radius: 7px;
        padding: 10px 11px;
        margin: 2px;
    }

    QListWidget#VisualsCollectionList::item:hover {
        background-color: #202328;
        border-color: #30353b;
        color: #ffffff;
    }

    QListWidget#VisualsCollectionList::item:selected {
        background-color: #2b2f35;
        border: 1px solid #626a73;
        color: #ffffff;
    }

    QScrollArea#VisualsDetailsScroll {
        background-color: transparent;
        border: none;
    }

    QFrame#VisualsDetailsPanel {
        background-color: #15171a;
        border: 1px solid #30343a;
        border-radius: 12px;
    }

    QLabel#VisualsName {
        background-color: transparent;
        color: #ffffff;
        font-size: 20px;
        font-weight: 700;
        padding: 1px 2px 4px 2px;
    }

    QLabel#VisualsPreview {
        background-color: #090a0c;
        color: #777e86;
        border: 1px solid #2c3035;
        border-radius: 10px;
        padding: 12px;
    }

    QPushButton#VisualsInstallButton {
        background-color: #e6e8eb;
        color: #111315;
        border: 1px solid #ffffff;
        border-radius: 8px;
        padding: 10px 14px;
        font-weight: 700;
    }

    QPushButton#VisualsInstallButton:hover {
        background-color: #ffffff;
        border-color: #ffffff;
    }

    QPushButton#VisualsInstallButton:pressed {
        background-color: #d2d5d9;
    }

    QPushButton#VisualsInstallButton:disabled {
        background-color: #202327;
        color: #737981;
        border-color: #30343a;
    }

    QPushButton#VisualsAssignDefaultButton,
    QPushButton#VisualsAssignSystemButton,
    QPushButton#VisualsAssignGameButton {
        background-color: #25292e;
        color: #f2f3f4;
        border: 1px solid #464c53;
        border-radius: 8px;
        padding: 9px 13px;
        font-weight: 600;
    }

    QPushButton#VisualsAssignDefaultButton:hover,
    QPushButton#VisualsAssignSystemButton:hover,
    QPushButton#VisualsAssignGameButton:hover {
        background-color: #30353b;
        border-color: #69717a;
    }

    QPushButton#VisualsAssignDefaultButton:disabled,
    QPushButton#VisualsAssignSystemButton:disabled,
    QPushButton#VisualsAssignGameButton:disabled {
        background-color: #1b1d20;
        color: #656a70;
        border-color: #2d3034;
    }

    QPushButton#VisualsClearDefaultButton,
    QPushButton#VisualsClearSystemButton,
    QPushButton#VisualsClearGameButton {
        background-color: transparent;
        color: #9ca2a9;
        border: 1px solid #34383d;
        border-radius: 8px;
        padding: 8px 12px;
    }

    QPushButton#VisualsClearDefaultButton:hover,
    QPushButton#VisualsClearSystemButton:hover,
    QPushButton#VisualsClearGameButton:hover {
        background-color: #24272b;
        color: #e4e6e8;
        border-color: #4b5056;
    }

    QLabel#VisualsStatus {
        background-color: #17191c;
        color: #a8adb3;
        border: 1px solid #292d32;
        border-radius: 7px;
        padding: 7px 10px;
    }

    /* =========================================================
       C.17-A.3 — showroom refinement pass #1
       ========================================================= */

    QLineEdit#VisualsSearch:focus,
    QComboBox#VisualsTypeFilter:focus {
        border: 1px solid #55c7e8;
    }

    QListWidget#VisualsCollectionList::item:selected {
        background-color: #202c33;
        border: 1px solid #55c7e8;
        color: #ffffff;
    }

    QFrame#VisualsDetailsPanel {
        background-color: #131619;
        border: 1px solid #343a40;
    }

    QLabel#VisualsPreview {
        background-color: #07090b;
        border: 1px solid #394149;
        border-radius: 12px;
        color: #78828c;
        padding: 14px;
    }

    QLabel#VisualsMetadataValue {
        background-color: transparent;
        color: #e2e6e9;
        padding: 2px 0px 6px 0px;
    }

    QLabel#VisualsInstallStatus {
        background-color: transparent;
        color: #72d5ee;
        font-weight: 600;
        padding: 2px 0px 6px 0px;
    }

    QLabel#VisualsReferenceValue,
    QLabel#VisualsAttributionValue {
        background-color: transparent;
        color: #aab1b8;
        padding: 2px 0px 7px 0px;
    }

    QFrame#VisualsAssignmentSummary {
        background-color: #101316;
        border: 1px solid #303840;
        border-radius: 10px;
    }

    QLabel#VisualsAssignmentValue {
        background-color: transparent;
        color: #c5cbd1;
        padding: 5px 7px;
    }

    QLabel#VisualsEffectiveAssignment {
        background-color: #17252b;
        color: #8ce7fb;
        border: 1px solid #315867;
        border-radius: 7px;
        padding: 9px 10px;
        font-weight: 700;
    }

    QPushButton#VisualsAssignDefaultButton,
    QPushButton#VisualsAssignSystemButton,
    QPushButton#VisualsAssignGameButton {
        min-height: 24px;
        padding: 6px 10px;
    }

    QPushButton#VisualsClearDefaultButton,
    QPushButton#VisualsClearSystemButton,
    QPushButton#VisualsClearGameButton {
        min-height: 24px;
        padding: 6px 9px;
    }

    QLabel#VisualsStatus {
        border-color: #303840;
    }


    /* =========================================================
       C.17-A.3 — showroom refinement pass #2
       Cyan is RetroVault's interaction accent.
       ========================================================= */

    QListWidget#VisualsCollectionList {
        background-color: #121518;
        border: 1px solid #30363c;
        border-radius: 11px;
        padding: 7px;
    }

    QListWidget#VisualsCollectionList::item {
        min-height: 30px;
        padding: 8px 10px;
        margin: 2px 0px;
        border: 1px solid transparent;
        border-radius: 7px;
        color: #d9dee3;
    }

    QListWidget#VisualsCollectionList::item:hover {
        background-color: #191e22;
        border: 1px solid #343d44;
    }

    QListWidget#VisualsCollectionList::item:selected {
        background-color: #1b2930;
        border: 1px solid #55c7e8;
        color: #ffffff;
    }

    QFrame#VisualsMetadataPanel {
        background-color: #101316;
        border: 1px solid #2c3339;
        border-radius: 10px;
    }

    QLabel#VisualsMetadataLabel {
        background-color: transparent;
        color: #7f8992;
        font-size: 11px;
        font-weight: 600;
        padding: 4px 4px 4px 0px;
        min-width: 104px;
    }

    QLabel#VisualsMetadataValue {
        background-color: transparent;
        color: #e1e6ea;
        padding: 4px 0px;
    }

    QLabel#VisualsInstallStatus {
        background-color: transparent;
        color: #72d5ee;
        font-weight: 700;
        padding: 4px 0px;
    }

    QLabel#VisualsReferenceValue,
    QLabel#VisualsAttributionValue {
        background-color: transparent;
        color: #aab3bb;
        padding: 4px 0px;
    }

    QLabel#VisualsPreview {
        background-color: #06080a;
        border: 1px solid #364149;
        border-radius: 12px;
        color: #71808a;
        font-weight: 600;
        padding: 8px;
    }

    QPushButton#VisualsInstallButton {
        background-color: #dfe5e9;
        color: #101316;
        border: 1px solid #ffffff;
        border-radius: 8px;
        min-height: 30px;
        padding: 7px 18px;
        font-weight: 700;
    }

    QPushButton#VisualsInstallButton:hover {
        background-color: #ffffff;
        border-color: #55c7e8;
    }

    QPushButton#VisualsInstallButton:disabled {
        background-color: #20252a;
        color: #6f7880;
        border-color: #30363c;
    }

    QFrame#VisualsAssignmentSummary {
        background-color: #0f1316;
        border: 1px solid #303941;
        border-radius: 10px;
    }

    QLabel#VisualsEffectiveAssignment {
        background-color: #15252c;
        color: #8ce7fb;
        border: 1px solid #356474;
        border-radius: 7px;
        padding: 8px 10px;
        font-weight: 700;
    }

    QLabel#VisualsAssignmentValue {
        background-color: transparent;
        color: #c9d0d6;
        padding: 6px 8px;
    }

    QPushButton#VisualsAssignDefaultButton,
    QPushButton#VisualsAssignSystemButton,
    QPushButton#VisualsAssignGameButton {
        min-width: 112px;
        min-height: 26px;
        padding: 5px 10px;
    }

    QPushButton#VisualsClearDefaultButton,
    QPushButton#VisualsClearSystemButton,
    QPushButton#VisualsClearGameButton {
        min-width: 76px;
        min-height: 26px;
        padding: 5px 9px;
        background-color: transparent;
    }

    QLabel#VisualsStatus {
        background-color: transparent;
        border: none;
        color: #78828b;
        padding: 5px 2px;
    }

    """
