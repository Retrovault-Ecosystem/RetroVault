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


    def refresh_artwork(
        self,
        directory,
    ):

        return self.library.refresh_artwork(
            directory
        )




    def recent(
        self,
        limit=20,
    ):

        return self.library.recent(
            limit=limit
        )


    def record_played(
        self,
        game,
    ):

        return self.library.record_played(
            game
        )


    def set_favorite(
        self,
        game,
        favorite,
    ):

        return self.library.set_favorite(
            game,
            favorite,
        )

    def collection_names(self):

        return self.library.collection_names()


    def create_collection(
        self,
        name,
    ):

        return self.library.create_collection(
            name
        )


    def rename_collection(
        self,
        current_name,
        new_name,
    ):

        return self.library.rename_collection(
            current_name,
            new_name,
        )


    def delete_collection(
        self,
        name,
    ):

        return self.library.delete_collection(
            name
        )


    def collection_games(
        self,
        name,
    ):

        return self.library.collection_games(
            name
        )


    def add_to_collection(
        self,
        name,
        game,
    ):

        return self.library.add_to_collection(
            name,
            game,
        )


    def remove_from_collection(
        self,
        name,
        game,
    ):

        return self.library.remove_from_collection(
            name,
            game,
        )
