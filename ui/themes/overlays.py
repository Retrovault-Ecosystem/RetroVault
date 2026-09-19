"""RetroVault Overlays visual-asset control-center theme."""


def overlays_stylesheet():
    """Return presentation styling owned by the Overlays surface."""

    return """
    /* ============================================================
       RetroVault Overlays — visual asset control center
       ============================================================ */

    QLabel#OverlaysTitle {
        color: #f4f8ff;
        font-size: 24px;
        font-weight: 700;
    }

    QLabel#OverlaysSubtitle {
        color: #8fa7c4;
        font-size: 12px;
    }

    QLabel#OverlaysDirectoryLabel {
        color: #8198b2;
        font-size: 12px;
        font-weight: 600;
    }

    QLabel#OverlaysDirectoryValue {
        color: #b9cce0;
        background: #0d1621;
        border: 1px solid #203247;
        border-radius: 7px;
        font-size: 13px;
        padding: 13px 16px;
    }

    QLabel#OverlaysCount {
        color: #77cbea;
        font-size: 11px;
        font-weight: 700;
        padding: 2px 3px;
    }

    QListWidget#OverlaysAssetList {
        color: #dce9f7;
        background: #0d1622;
        border: 1px solid #22384f;
        border-radius: 11px;
        padding: 6px;
        outline: 0;
    }

    QListWidget#OverlaysAssetList::item {
        min-height: 32px;
        padding: 6px 9px;
        margin: 2px;
        border: 1px solid transparent;
        border-radius: 7px;
    }

    QListWidget#OverlaysAssetList::item:hover {
        color: #ffffff;
        background: #172b40;
        border-color: #294760;
    }

    QListWidget#OverlaysAssetList::item:selected {
        color: #ffffff;
        background: #1d5375;
        border-color: #49b4e5;
    }

    QFrame#OverlaysDetailsPanel {
        background: #101b29;
        border: 1px solid #22384f;
        border-radius: 12px;
    }

    QLabel#OverlaysAssetName {
        color: #ffffff;
        font-size: 18px;
        font-weight: 700;
        padding-bottom: 2px;
    }

    QLabel#OverlaysPreview {
        color: #71889e;
        background: #070d13;
        border: 1px solid #2b4358;
        border-radius: 11px;
        padding: 8px;
    }

    QLabel#OverlaysFieldLabel {
        color: #7892ac;
        font-size: 12px;
        font-weight: 700;
        padding: 8px 8px 4px 8px;
    }

    QLabel#OverlaysFieldValue {
        color: #d7e3ee;
        background: transparent;
        font-size: 13px;
        padding: 7px 10px 12px 10px;
    }

    QLabel#OverlaysReadiness {
        color: #7ed9f1;
        font-size: 13px;
        font-weight: 700;
        padding: 8px 10px;
    }

    QLabel#OverlaysAssignmentTitle {
        color: #8fdcff;
        font-size: 13px;
        font-weight: 700;
        padding: 8px 6px 3px 6px;
    }

    QLabel#OverlaysStatus {
        color: #91a8c2;
        font-size: 12px;
        padding: 9px 12px;
    }

    QPushButton#OverlaysPrimaryAction {
        min-height: 34px;
        padding: 0 14px;
        color: #f6fbff;
        background: #176f9f;
        border: 1px solid #3299cf;
        border-radius: 7px;
        font-weight: 700;
    }

    QPushButton#OverlaysPrimaryAction:hover {
        background: #1d83b9;
        border-color: #55b9e8;
    }

    QPushButton#OverlaysPrimaryAction:pressed {
        background: #135d86;
    }

    QPushButton#OverlaysSecondaryAction {
        min-height: 32px;
        padding: 0 12px;
        color: #d8e8f7;
        background: #152435;
        border: 1px solid #29445e;
        border-radius: 7px;
        font-weight: 600;
    }

    QPushButton#OverlaysSecondaryAction:hover {
        color: #ffffff;
        background: #1b3147;
        border-color: #3d6c91;
    }

    QPushButton#OverlaysSecondaryAction:pressed {
        background: #102033;
    }

    QPushButton#OverlaysAssignmentAction {
        min-height: 32px;
        padding: 0 12px;
        color: #e8f7fc;
        background: #153140;
        border: 1px solid #2c647b;
        border-radius: 7px;
        font-weight: 600;
    }

    QPushButton#OverlaysAssignmentAction:hover {
        color: #ffffff;
        background: #1b4356;
        border-color: #55b9e8;
    }

    QPushButton#OverlaysAssignmentAction:pressed {
        background: #112b38;
    }

    QPushButton#OverlaysPrimaryAction:disabled,
    QPushButton#OverlaysSecondaryAction:disabled,
    QPushButton#OverlaysAssignmentAction:disabled {
        color: #53677c;
        background: #111a24;
        border-color: #1e2b38;
    }
    """
