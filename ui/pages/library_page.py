from ui.library.gallery import GalleryView


class LibraryPage(GalleryView):
    def __init__(
        self,
        games,
        rvdb_service=None,
    ):
        super().__init__(
            games,
            rvdb_service=rvdb_service,
        )
