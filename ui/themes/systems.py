"""RetroVault Systems showroom presentation theme."""


def systems_stylesheet():
    """Return presentation styling owned by the Systems surface."""

    return """
    /* ============================================================
       RetroVault Systems — platform showroom
       ============================================================ */

    QLabel#SystemsTitle {
        color: #f4f8ff;
        font-size: 24px;
        font-weight: 700;
    }

    QLabel#SystemsSubtitle {
        color: #8fa7c4;
        font-size: 12px;
    }

    QLabel#SystemsCount {
        color: #7fd7ff;
        font-size: 12px;
        font-weight: 600;
    }

    QLabel#SystemsStatus {
        color: #91a8c2;
        font-size: 11px;
    }

    QLineEdit#SystemsSearch {
        min-height: 34px;
        padding: 0 12px;
        color: #edf6ff;
        background: #111c2b;
        border: 1px solid #263a52;
        border-radius: 8px;
        selection-background-color: #267fb4;
    }

    QLineEdit#SystemsSearch:hover {
        border-color: #355675;
        background: #132133;
    }

    QLineEdit#SystemsSearch:focus {
        border: 1px solid #38a8e0;
        background: #15263a;
    }

    QListWidget#SystemsList {
        color: #dce9f7;
        background: #0d1622;
        border: 1px solid #203247;
        border-radius: 10px;
        padding: 5px;
        outline: 0;
    }

    QListWidget#SystemsList::item {
        min-height: 34px;
        padding: 5px 9px;
        margin: 2px;
        border-radius: 6px;
    }

    QListWidget#SystemsList::item:hover {
        color: #ffffff;
        background: #172b40;
    }

    QListWidget#SystemsList::item:selected {
        color: #ffffff;
        background: #1d5375;
        border: 1px solid #3ca6dc;
    }

    QFrame#SystemsDetailsPanel {
        background: #101b29;
        border: 1px solid #22384f;
        border-radius: 12px;
    }

    QLabel#SystemsPlatformName {
        color: #ffffff;
        font-size: 21px;
        font-weight: 700;
    }

    QLabel#SystemsPlatformId {
        color: #6faed2;
        font-size: 13px;
    }

    QLabel#SystemsSectionTitle {
        color: #8fdcff;
        font-size: 14px;
        font-weight: 700;
    }

    QLabel#SystemsFieldLabel {
        color: #758da8;
        font-size: 13px;
        font-weight: 600;
    }

    QLabel#SystemsFieldValue {
        color: #e3edf8;
        font-size: 14px;
    }

    QFrame#SystemsLibraryPanel {
        background: #0c1723;
        border: 1px solid #1e344a;
        border-radius: 10px;
    }

    QLabel#SystemsMetricLabel {
        color: #7891ac;
        font-size: 12px;
        font-weight: 600;
    }

    QLabel#SystemsMetricValue {
        color: #f2f8ff;
        font-size: 19px;
        font-weight: 700;
    }

    QPushButton#SystemsPrimaryAction {
        min-height: 34px;
        padding: 0 14px;
        color: #f6fbff;
        background: #176f9f;
        border: 1px solid #3299cf;
        border-radius: 7px;
        font-weight: 600;
    }

    QPushButton#SystemsPrimaryAction:hover {
        background: #1d83b9;
        border-color: #55b9e8;
    }

    QPushButton#SystemsPrimaryAction:pressed {
        background: #135d86;
    }

    QPushButton#SystemsSecondaryAction {
        min-height: 32px;
        padding: 0 12px;
        color: #d8e8f7;
        background: #152435;
        border: 1px solid #29445e;
        border-radius: 7px;
        font-weight: 600;
    }

    QPushButton#SystemsSecondaryAction:hover {
        color: #ffffff;
        background: #1b3147;
        border-color: #3d6c91;
    }

    QPushButton#SystemsSecondaryAction:pressed {
        background: #102033;
    }

    QPushButton#SystemsPrimaryAction:disabled,
    QPushButton#SystemsSecondaryAction:disabled {
        color: #53677c;
        background: #111a24;
        border-color: #1e2b38;
    }
    """
