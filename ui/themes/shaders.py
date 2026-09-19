"""RetroVault Shaders laboratory presentation theme."""


def shaders_stylesheet():
    """Return presentation styling owned by the Shaders surface."""

    return """
    /* ============================================================
       RetroVault Shaders — shader laboratory
       ============================================================ */

    QLabel#ShadersTitle {
        color: #f4f8ff;
        font-size: 24px;
        font-weight: 700;
    }

    QLabel#ShadersSubtitle {
        color: #8fa7c4;
        font-size: 15px;
    }

    QLabel#ShadersDirectoryLabel {
        color: #8198b2;
        font-size: 12px;
        font-weight: 600;
    }

    QLabel#ShadersDirectoryValue {
        color: #b9cce0;
        background: #0d1621;
        border: 1px solid #203247;
        border-radius: 7px;
        font-size: 13px;
        padding: 13px 16px;
    }

    QLabel#ShadersCount {
        color: #77cbea;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 3px;
    }

    QListWidget#ShadersPresetList {
        color: #dce9f7;
        background: #0b1420;
        border: 1px solid #22384f;
        border-radius: 11px;
        padding: 6px;
        outline: 0;
    }

    QListWidget#ShadersPresetList::item {
        min-height: 32px;
        padding: 6px 9px;
        margin: 2px;
        border: 1px solid transparent;
        border-radius: 7px;
    }

    QListWidget#ShadersPresetList::item:hover {
        color: #ffffff;
        background: #172b40;
        border-color: #294760;
    }

    QListWidget#ShadersPresetList::item:selected {
        color: #ffffff;
        background: #1d5375;
        border-color: #49b4e5;
    }

    QFrame#ShadersDetailsPanel {
        background: #101b29;
        border: 1px solid #22384f;
        border-radius: 12px;
    }

    QLabel#ShadersPresetName {
        color: #ffffff;
        font-size: 18px;
        font-weight: 700;
        padding-bottom: 4px;
    }

    QLabel#ShadersFieldLabel {
        color: #7892ac;
        font-size: 12px;
        font-weight: 700;
        padding: 8px 8px 4px 8px;
    }

    QLabel#ShadersFieldValue {
        color: #d7e3ee;
        background: transparent;
        font-size: 13px;
        padding: 7px 10px 12px 10px;
    }

    QLabel#ShadersPresetPath {
        color: #b8cde0;
        background: #0a121c;
        border: 1px solid #1d3043;
        border-radius: 6px;
        font-size: 13px;
        padding: 13px 15px;
    }

    QLabel#ShadersReadiness {
        color: #7ed9f1;
        font-size: 13px;
        font-weight: 700;
        padding: 9px 10px;
    }

    QLabel#ShadersAssignmentTitle {
        color: #8fdcff;
        font-size: 13px;
        font-weight: 700;
        padding: 9px 6px 3px 6px;
    }

    QLabel#ShadersStatus {
        color: #91a8c2;
        font-size: 12px;
        padding: 9px 12px;
    }

    QPushButton#ShadersSecondaryAction {
        min-height: 32px;
        padding: 0 12px;
        color: #d8e8f7;
        background: #152435;
        border: 1px solid #29445e;
        border-radius: 7px;
        font-weight: 600;
    }

    QPushButton#ShadersSecondaryAction:hover {
        color: #ffffff;
        background: #1b3147;
        border-color: #3d6c91;
    }

    QPushButton#ShadersSecondaryAction:pressed {
        background: #102033;
    }

    QPushButton#ShadersAssignmentAction {
        min-height: 32px;
        padding: 0 12px;
        color: #e8f7fc;
        background: #153140;
        border: 1px solid #2c647b;
        border-radius: 7px;
        font-weight: 600;
    }

    QPushButton#ShadersAssignmentAction:hover {
        color: #ffffff;
        background: #1b4356;
        border-color: #55b9e8;
    }

    QPushButton#ShadersAssignmentAction:pressed {
        background: #112b38;
    }

    QPushButton#ShadersSecondaryAction:disabled,
    QPushButton#ShadersAssignmentAction:disabled {
        color: #53677c;
        background: #111a24;
        border-color: #1e2b38;
    }
    """
