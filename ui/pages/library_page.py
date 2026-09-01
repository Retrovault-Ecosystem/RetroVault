from ui.library.gallery import GalleryView


class LibraryPage(GalleryView):
    def __init__(
        self,
        games,
        rvdb_consumer=None,
    ):
        super().__init__(
            games,
            rvdb_consumer=rvdb_consumer,
        )
