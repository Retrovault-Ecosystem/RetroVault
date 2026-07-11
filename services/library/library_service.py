from services.library.source_manager import SourceManager
from services.library.library_builder import LibraryBuilder


class LibraryService:


    def __init__(self):

        self.sources = SourceManager()

        self.builder = LibraryBuilder()

        self.games = []



    def load(self):

        self.games = self.builder.build(

            self.sources.sources()

        )

        return self.games



    def get_games(self):

        return self.games