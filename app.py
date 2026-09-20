import sys

from PyQt6.QtWidgets import QApplication

from ui.main_window import MainWindow
from ui.theme import apply_theme


def main():

    app = QApplication(sys.argv)

    apply_theme(app)

    window = MainWindow()

    # RetroVault is a desktop-first application whose primary
    # Library workspace benefits from the complete available
    # screen area. Ask the native window manager for a genuine
    # maximized window instead of merely constructing a large
    # normal-state window.
    window.showMaximized()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()
