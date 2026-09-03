from services.library import LibraryService


class LibraryController:


    def __init__(
        self,
        rvdb_resolver=None,
    ):

        self.library = LibraryService(
            rvdb_resolver=rvdb_resolver
        )

        self.library.load()


    def get_games(self):

        return self.library.get_games()


    def set_favorite(
        self,
        game,
        favorite,
    ):

        return self.library.set_favorite(
            game,
            favorite,
        )
