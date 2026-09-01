def apply_theme(app):
    """Apply RetroVault's shared dark desktop theme."""

    app.setStyleSheet(
        """
        QWidget {
            background-color: #121212;
            color: #eeeeee;
            font-size: 14px;
        }

        QMainWindow {
            background-color: #101010;
        }

        QLabel#PageTitle {
            font-size: 28px;
            font-weight: 700;
        }

        QLabel#PageSubtitle {
            color: #9aa0a6;
            font-size: 13px;
        }

        QLabel#SectionTitle {
            font-size: 16px;
            font-weight: 700;
        }

        QPushButton {
            background-color: #242424;
            border: 1px solid #343434;
            border-radius: 6px;
            padding: 8px 12px;
        }

        QPushButton:hover {
            background-color: #303030;
            border-color: #4a4a4a;
        }

        QPushButton:pressed {
            background-color: #383838;
        }

        QPushButton#NavButton {
            min-height: 28px;
            padding: 9px 12px;
            text-align: left;
            border: 1px solid transparent;
            background-color: transparent;
        }

        QPushButton#NavButton:hover {
            background-color: #242424;
        }

        QPushButton#NavButton:checked {
            background-color: #2c2c2c;
            border-color: #454545;
            font-weight: 700;
        }

        QLineEdit,
        QComboBox {
            background-color: #1b1b1b;
            border: 1px solid #3a3a3a;
            border-radius: 6px;
            padding: 7px 9px;
            min-height: 22px;
        }

        QLineEdit:focus,
        QComboBox:focus {
            border-color: #666666;
        }

        QComboBox::drop-down {
            border: none;
            width: 24px;
        }

        QListWidget {
            background-color: #181818;
            border: 1px solid #343434;
            border-radius: 7px;
            outline: none;
            padding: 4px;
        }

        QListWidget::item {
            border-radius: 5px;
            padding: 7px 8px;
            margin: 1px;
        }

        QListWidget::item:hover {
            background-color: #252525;
        }

        QListWidget::item:selected {
            background-color: #353535;
            color: #ffffff;
        }

        QScrollArea {
            border: none;
            background-color: transparent;
        }

        QScrollBar:vertical {
            background: #161616;
            width: 12px;
            margin: 0;
        }

        QScrollBar::handle:vertical {
            background: #444444;
            min-height: 28px;
            border-radius: 5px;
        }

        QScrollBar::handle:vertical:hover {
            background: #555555;
        }

        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical {
            height: 0;
        }

        QScrollBar:horizontal {
            background: #161616;
            height: 12px;
            margin: 0;
        }

        QScrollBar::handle:horizontal {
            background: #444444;
            min-width: 28px;
            border-radius: 5px;
        }

        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal {
            width: 0;
        }
        """
    )
