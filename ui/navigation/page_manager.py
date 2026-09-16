from PyQt6.QtWidgets import QStackedWidget


class PageManager(QStackedWidget):

    def __init__(self):

        super().__init__()

        self.pages = {}


    def add_page(self, name, widget):

        self.pages[name] = widget

        self.addWidget(widget)


    def show_page(self, name):

        page = self.pages[name]

        refresh = getattr(
            page,
            "refresh_page",
            None,
        )

        if callable(refresh):
            refresh()

        self.setCurrentWidget(
            page
        )
