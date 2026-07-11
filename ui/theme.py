def apply_theme(app):

    app.setStyleSheet(
        """
        QWidget {
            background-color: #121212;
            color: #eeeeee;
            font-size: 14px;
        }

        QPushButton {
            background-color: #242424;
            border-radius: 6px;
            padding: 8px;
        }

        QPushButton:hover {
            background-color: #444444;
        }
        """
    )
