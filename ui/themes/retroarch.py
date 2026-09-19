"""RetroVault RetroArch core intelligence presentation theme."""


def retroarch_stylesheet():
    """Return presentation styling owned by the RetroArch surface."""

    return """
    /* ============================================================
       RetroVault RetroArch — Core Intelligence Center
       ============================================================ */

    QLabel#RetroArchTitle {
        color: #f4f8ff;
        font-size: 24px;
        font-weight: 700;
    }

    QLabel#RetroArchSubtitle {
        color: #8fa7c4;
        font-size: 15px;
    }

    QLabel#RetroArchSummary {
        color: #bfd2e5;
        background: #0e1926;
        border: 1px solid #20364b;
        border-radius: 9px;
        font-size: 13px;
        padding: 16px 20px;
    }

    QFrame#RetroArchBrowserPanel,
    QFrame#RetroArchDetailsPanel {
        background: #101b29;
        border: 1px solid #22384f;
        border-radius: 12px;
    }

    QLabel#RetroArchSectionTitle {
        color: #8fdcff;
        font-size: 13px;
        font-weight: 700;
        padding: 7px 8px 9px 8px;
    }

    QLabel#RetroArchCoreCount {
        color: #77cbea;
        font-size: 12px;
        font-weight: 700;
        padding: 6px 8px 10px 8px;
    }

    QListWidget#RetroArchCoreList {
        color: #dce9f7;
        background: #0b1420;
        border: 1px solid #22384f;
        border-radius: 10px;
        padding: 6px;
        outline: 0;
    }

    QListWidget#RetroArchCoreList::item {
        min-height: 32px;
        padding: 6px 9px;
        margin: 2px;
        border: 1px solid transparent;
        border-radius: 7px;
    }

    QListWidget#RetroArchCoreList::item:hover {
        color: #ffffff;
        background: #172b40;
        border-color: #294760;
    }

    QListWidget#RetroArchCoreList::item:selected {
        color: #ffffff;
        background: #1d5375;
        border-color: #49b4e5;
    }

    QLabel#RetroArchCoreName {
        color: #ffffff;
        font-size: 22px;
        font-weight: 700;
        padding-bottom: 2px;
    }

    QLabel#RetroArchCoreId {
        color: #7898b7;
        font-size: 12px;
        padding: 5px 8px 11px 8px;
    }

    QLabel#RetroArchFieldLabel {
        color: #819bb5;
        font-size: 12px;
        font-weight: 700;
        padding: 7px 8px 5px 8px;
    }

    QLabel#RetroArchFieldValue {
        color: #d7e4f0;
        background: #0c1621;
        border: 1px solid #1d3043;
        border-radius: 7px;
        font-size: 13px;
        padding: 14px 16px;
    }

    QLabel#RetroArchStatus {
        color: #91a8c2;
        font-size: 12px;
        padding: 10px 12px;
    }
    """
