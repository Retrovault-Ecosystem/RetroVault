from services.library.source_manager import SourceManager
from services.library.library_builder import LibraryBuilder
from services.library.state import LibraryState


class LibraryService:


    def __init__(
        self,
        rvdb_resolver=None,
        library_state=None,
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

        self.games = []


    def load(self):

        games = self.builder.build(
            self.sources.sources()
        )

        self.games = self.state.apply(
            games
        )

        return self.games


    def get_games(self):

        return self.games


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
