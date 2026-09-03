from ui.library.gallery import GalleryView


class LibraryPage(GalleryView):
    def __init__(
        self,
        games,
        rvdb_service=None,
        favorite_handler=None,
        played_handler=None,
        recent_provider=None,
    ):
        super().__init__(
            games,
            rvdb_service=rvdb_service,
            favorite_handler=favorite_handler,
            played_handler=played_handler,
            recent_provider=recent_provider,
        )
