"""RetroVault Settings presentation theme."""


def settings_stylesheet():
    """Return the Settings Configuration Console stylesheet."""

    return r"""
/* ============================================================
   RETROVAULT SETTINGS — CONFIGURATION CONSOLE
   ============================================================ */


QScrollArea#SettingsScrollArea {
    background-color: transparent;
    border: none;
}

QScrollArea#SettingsScrollArea > QWidget > QWidget {
    background-color: transparent;
}

QWidget#SettingsScrollContent {
    background-color: #121212;
}

QLabel#SettingsTitle {
    color: #f5f8ff;
    font-size: 26px;
    font-weight: 700;
}

QLabel#SettingsSubtitle {
    color: #8fa8c7;
    font-size: 15px;
    padding: 0px 0px 6px 0px;
}

/* ------------------------------------------------------------
   Configuration zones
   ------------------------------------------------------------ */

QGroupBox#SettingsRuntimeGroup,
QGroupBox#SettingsLibraryGroup,
QGroupBox#SettingsAssetsGroup,
QGroupBox#SettingsConfigGroup {
    background-color: #09131f;
    border: 1px solid #168ab8;
    border-radius: 10px;
    margin-top: 18px;
    padding: 20px 16px 16px 16px;
    color: #eaf2ff;
    font-size: 14px;
    font-weight: 600;
}

QGroupBox#SettingsRuntimeGroup::title,
QGroupBox#SettingsLibraryGroup::title,
QGroupBox#SettingsAssetsGroup::title,
QGroupBox#SettingsConfigGroup::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;

    /*
       Cut-in tab:
       same fill as the page/panel, bordered on top and sides.
       The group-box top border terminates naturally at the title.
    */
    background-color: #09131f;
    color: #48d7ff;

    border: 1px solid #168ab8;
    border-bottom: 0px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;

    padding: 6px 14px 7px 14px;

    font-size: 14px;
    font-weight: 700;
}

/* ------------------------------------------------------------
   Path / text editors
   ------------------------------------------------------------ */

QLineEdit#SettingsPathEditor,
QLineEdit#SettingsSourceNameEditor {
    background-color: #080d14;
    color: #eef6ff;
    border: 1px solid #2b4158;
    border-radius: 7px;
    padding: 8px 11px;
    selection-background-color: #176f91;
    selection-color: #ffffff;
    font-size: 14px;
}

QLineEdit#SettingsPathEditor:hover,
QLineEdit#SettingsSourceNameEditor:hover {
    border-color: #3e6684;
}

QLineEdit#SettingsPathEditor:focus,
QLineEdit#SettingsSourceNameEditor:focus {
    border: 1px solid #54d5ff;
    background-color: #0a111a;
}

QLineEdit#SettingsPathEditor:disabled,
QLineEdit#SettingsSourceNameEditor:disabled {
    color: #647486;
    background-color: #0a0e13;
    border-color: #1b2733;
}

/* ------------------------------------------------------------
   Library source browser
   ------------------------------------------------------------ */

QListWidget#SettingsSourceList {
    background-color: #080d14;
    color: #dce9f7;
    border: 1px solid #263f56;
    border-radius: 7px;
    padding: 4px 6px;
    outline: none;
    font-size: 14px;
}

QListWidget#SettingsSourceList::item {
    border-radius: 5px;
    padding: 7px 9px;
    margin: 1px 0px;
}

QListWidget#SettingsSourceList::item:hover {
    background-color: #101f2c;
    color: #ffffff;
}

QListWidget#SettingsSourceList::item:selected {
    background-color: #12394e;
    color: #ffffff;
    border: 1px solid #2aaed8;
}

/* ------------------------------------------------------------
   Buttons
   ------------------------------------------------------------ */

QPushButton#SettingsPrimaryAction {
    background-color: #147a9f;
    color: #ffffff;
    border: 1px solid #4ed6ff;
    border-radius: 7px;
    padding: 8px 15px;
    min-height: 20px;
    font-weight: 700;
}

QPushButton#SettingsPrimaryAction:hover {
    background-color: #198caf;
    border-color: #82e4ff;
}

QPushButton#SettingsPrimaryAction:pressed {
    background-color: #0e617f;
}

QPushButton#SettingsSecondaryAction,
QPushButton#SettingsBrowseAction {
    background-color: #172432;
    color: #dce9f7;
    border: 1px solid #334b61;
    border-radius: 7px;
    padding: 9px 15px;
    min-height: 20px;
}



QPushButton#SettingsBrowseAction {
    padding: 8px 13px;
}

QPushButton#SettingsSecondaryAction:hover,
QPushButton#SettingsBrowseAction:hover {
    background-color: #203448;
    color: #ffffff;
    border-color: #4e7899;
}

QPushButton#SettingsSecondaryAction:pressed,
QPushButton#SettingsBrowseAction:pressed {
    background-color: #111d28;
}

QPushButton#SettingsDangerAction {
    background-color: #2a171b;
    color: #ffb7bd;
    border: 1px solid #704049;
    border-radius: 7px;
    padding: 9px 15px;
    min-height: 20px;
}

QPushButton#SettingsDangerAction:hover {
    background-color: #432027;
    color: #ffd6da;
    border-color: #b45a67;
}

QPushButton#SettingsDangerAction:pressed {
    background-color: #251216;
}

QPushButton#SettingsPrimaryAction:disabled,
QPushButton#SettingsSecondaryAction:disabled,
QPushButton#SettingsBrowseAction:disabled,
QPushButton#SettingsDangerAction:disabled {
    background-color: #10171f;
    color: #596978;
    border-color: #263440;
}

/* ------------------------------------------------------------
   Validation controls
   ------------------------------------------------------------ */

QPushButton#SettingsValidationStatus {
    background-color: #101b25;
    color: #a9bdd0;
    border: 1px solid #30485d;
    border-radius: 7px;
    padding: 8px 11px;
    min-height: 20px;
    font-weight: 600;
}

QPushButton#SettingsValidationStatus:hover {
    background-color: #182936;
    color: #e8f6ff;
    border-color: #4b7795;
}

QPushButton#SettingsValidationStatus:pressed {
    background-color: #0d171f;
}

/* ------------------------------------------------------------
   Information / status presentation
   ------------------------------------------------------------ */

QLabel#SettingsSummaryValue {
    background-color: #080d14;
    color: #dce9f7;
    border: 1px solid #24384b;
    border-radius: 7px;
    padding: 10px 12px;
    font-size: 14px;
}

QLabel#SettingsFieldLabel {
    color: #8fa8c7;
    font-size: 12px;
    font-weight: 600;
    padding: 4px 4px 3px 4px;
}

QLabel#SettingsFieldValue {
    background-color: #080d14;
    color: #e6f1fb;
    border: 1px solid #24384b;
    border-radius: 7px;
    padding: 10px 12px;
    font-size: 14px;
}

QLabel#SettingsFieldStatus {
    color: #63d7ff;
    font-size: 12px;
    font-weight: 600;
    padding: 6px 8px;
}

QLabel#SettingsSaveStatus {
    color: #79dfff;
    font-size: 12px;
    font-weight: 600;
    padding: 7px 10px;
}

QLabel#SettingsNote {
    background-color: #08111b;
    color: #9db5cc;
    border: none;
    border-radius: 5px;
    padding: 9px 12px;
    font-size: 13px;
}
"""


__all__ = [
    "settings_stylesheet",
]
