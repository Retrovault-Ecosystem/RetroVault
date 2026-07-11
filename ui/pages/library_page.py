from PyQt6.QtWidgets import QVBoxLayout

from ui.library.gallery import GalleryView


class LibraryPage(GalleryView):

    def __init__(self, games):

        super().__init__(
            games
        )
