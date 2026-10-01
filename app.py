import sys

from PyQt6.QtWidgets import QApplication, QMessageBox
from services.startup import check_startup

from ui.main_window import MainWindow
from ui.theme import apply_theme


def main():

    app = QApplication(sys.argv)

    report = check_startup()
    if report.errors:
        QMessageBox.critical(None, "Startup configuration error",
                             "\n".join(report.errors) + "\nThe files have not been changed. Correct them and restart.")
        return 1
    try:
        window = MainWindow()
    except (OSError, ValueError) as exc:
        QMessageBox.critical(None, "Startup error", str(exc) + "\nUser settings have not been reset.")
        return 1
    if report.warnings:
        window.statusBar().showMessage(" | ".join(report.warnings))
    app.installEventFilter(window)
    app.aboutToQuit.connect(window.shutdown_runtime)

    # Style the completed widget tree once, before its first display.
    # Styling thousands of library widgets as they are reparented during
    # construction repeatedly recalculates the same stylesheet rules.
    apply_theme(app)

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
    raise SystemExit(main())
