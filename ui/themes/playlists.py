"""RetroVault Playlists collection-showcase presentation theme."""


def playlists_stylesheet():
    """Return presentation styling owned by the Playlists surface."""

    return """
    /* ============================================================
       RetroVault Playlists — curated collection showcase
       ============================================================ */

    QLabel#PlaylistsTitle {
        color: #f4f8ff;
        font-size: 24px;
        font-weight: 700;
    }

    QLabel#PlaylistsSubtitle {
        color: #8fa7c4;
        font-size: 15px;
    }

    QFrame#PlaylistsCollectionPanel,
    QFrame#PlaylistsGamesPanel {
        background: #101b29;
        border: 1px solid #22384f;
        border-radius: 12px;
    }

    QLabel#PlaylistsPanelTitle {
        color: #8fdcff;
        font-size: 12px;
        font-weight: 700;
    }

    QLabel#PlaylistsCollectionTitle {
        color: #ffffff;
        font-size: 18px;
        font-weight: 700;
    }

    QListWidget#PlaylistsCollectionList,
    QListWidget#PlaylistsGameList {
        color: #dce9f7;
        background: #0d1622;
        border: 1px solid #203247;
        border-radius: 9px;
        padding: 5px;
        outline: 0;
    }

    QListWidget#PlaylistsCollectionList::item,
    QListWidget#PlaylistsGameList::item {
        min-height: 32px;
        padding: 5px 9px;
        margin: 2px;
        border-radius: 6px;
    }

    QListWidget#PlaylistsCollectionList::item:hover,
    QListWidget#PlaylistsGameList::item:hover {
        color: #ffffff;
        background: #172b40;
    }

    QListWidget#PlaylistsCollectionList::item:selected,
    QListWidget#PlaylistsGameList::item:selected {
        color: #ffffff;
        background: #1d5375;
        border: 1px solid #3ca6dc;
    }

    QLabel#PlaylistsStatus {
        color: #91a8c2;
        font-size: 11px;
        padding: 2px 4px;
    }

    QPushButton#PlaylistsPrimaryAction {
        min-height: 34px;
        padding: 0 14px;
        color: #f6fbff;
        background: #176f9f;
        border: 1px solid #3299cf;
        border-radius: 7px;
        font-weight: 600;
    }

    QPushButton#PlaylistsPrimaryAction:hover {
        background: #1d83b9;
        border-color: #55b9e8;
    }

    QPushButton#PlaylistsPrimaryAction:pressed {
        background: #135d86;
    }

    QPushButton#PlaylistsSecondaryAction {
        min-height: 32px;
        padding: 0 12px;
        color: #d8e8f7;
        background: #152435;
        border: 1px solid #29445e;
        border-radius: 7px;
        font-weight: 600;
    }

    QPushButton#PlaylistsSecondaryAction:hover {
        color: #ffffff;
        background: #1b3147;
        border-color: #3d6c91;
    }

    QPushButton#PlaylistsSecondaryAction:pressed {
        background: #102033;
    }

    QPushButton#PlaylistsDangerAction {
        min-height: 32px;
        padding: 0 12px;
        color: #f0c4c4;
        background: #2a181c;
        border: 1px solid #593039;
        border-radius: 7px;
        font-weight: 600;
    }

    QPushButton#PlaylistsDangerAction:hover {
        color: #ffffff;
        background: #3a1d23;
        border-color: #8a4654;
    }

    QPushButton#PlaylistsDangerAction:pressed {
        background: #241317;
    }

    QPushButton#PlaylistsPrimaryAction:disabled,
    QPushButton#PlaylistsSecondaryAction:disabled,
    QPushButton#PlaylistsDangerAction:disabled {
        color: #53677c;
        background: #111a24;
        border-color: #1e2b38;
    }
    """
