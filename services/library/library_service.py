from services.library.source_manager import SourceManager
from services.library.library_builder import LibraryBuilder
from services.library.state import LibraryState
from services.artwork import ArtworkService


class LibraryService:


    def __init__(
        self,
        rvdb_resolver=None,
        library_state=None,
        artwork_service=None,
    ):

        self.sources = SourceManager()

        self.builder = LibraryBuilder(
            rvdb_resolver=rvdb_resolver
        )

        self.state = (
            library_state
            if library_state is not None
            else LibraryState()
        )

        artwork_directory = (
            self.sources.config
            .get(
                "paths",
                {},
            )
            .get(
                "artwork",
                {},
            )
            .get(
                "directory",
                "",
            )
        )

        self.artwork = (
            artwork_service
            if artwork_service is not None
            else ArtworkService(
                directory=artwork_directory
            )
        )

        self.games = []


    def load(self):

        games = self.builder.build(
            self.sources.sources()
        )

        self.games = self.state.apply(
            games
        )

        for game in self.games:

            artwork = (
                self.artwork.get_artwork(
                    game
                )
            )

            game.artwork = (
                artwork
                if artwork is not None
                else ""
            )

        return self.games


    def refresh_artwork(
        self,
        directory,
    ):

        self.artwork.set_directory(
            directory
        )

        for game in self.games:

            game.artwork = ""

            artwork = (
                self.artwork.get_artwork(
                    game
                )
            )

            game.artwork = (
                artwork
                if artwork is not None
                else ""
            )

        return self.games


    def get_games(self):

        return self.games


    def recent(
        self,
        limit=20,
    ):

        return self.state.recent(
            limit=limit
        )


    def record_played(
        self,
        game,
    ):

        return self.state.record_played(
            game
        )


    def set_favorite(
        self,
        game,
        favorite,
    ):

        favorite = bool(
            favorite
        )

        self.state.set_favorite(
            game,
            favorite,
        )

        game.favorite = favorite

        return game.favorite
