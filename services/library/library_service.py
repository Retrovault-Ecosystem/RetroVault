from services.library.source_manager import SourceManager
from services.library.library_builder import LibraryBuilder
from services.library.state import (
    LibraryState,
    game_identity,
)
from services.library.collections import (
    CollectionStore,
)
from services.artwork import ArtworkService


class LibraryService:


    def __init__(
        self,
        rvdb_resolver=None,
        library_state=None,
        artwork_service=None,
        collection_store=None,
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

        self.collections = (
            collection_store
            if collection_store is not None
            else CollectionStore()
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


    def reload_sources(self):

        source_manager_type = type(
            self.sources
        )

        try:
            refreshed_sources = (
                source_manager_type()
            )
        except TypeError:
            refreshed_sources = (
                SourceManager()
            )

        previous_sources = self.sources
        previous_games = self.games

        self.sources = refreshed_sources

        try:
            return self.load()
        except Exception:
            self.sources = previous_sources
            self.games = previous_games
            raise


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


    def merge_bulk_import(
        self,
        result,
    ):

        existing_identities = set()

        for game in self.games:

            try:
                identity = game_identity(
                    game
                )
            except ValueError:
                continue

            existing_identities.add(
                identity
            )

        added = []
        skipped = 0

        for game in result.games:

            try:
                identity = game_identity(
                    game
                )
            except ValueError:
                skipped += 1
                continue

            if identity in existing_identities:
                skipped += 1
                continue

            existing_identities.add(
                identity
            )

            applied = self.state.apply(
                [game]
            )

            if not applied:
                skipped += 1
                continue

            imported_game = applied[0]

            artwork = self.artwork.get_artwork(
                imported_game
            )

            imported_game.artwork = (
                artwork
                if artwork is not None
                else ""
            )

            self.games.append(
                imported_game
            )

            added.append(
                imported_game
            )

        self.games.sort(
            key=lambda game: (
                str(
                    getattr(
                        game,
                        "platform",
                        "",
                    )
                ).casefold(),
                str(
                    getattr(
                        game,
                        "name",
                        "",
                    )
                ).casefold(),
                str(
                    getattr(
                        game,
                        "rom",
                        "",
                    )
                ).casefold(),
            )
        )

        return {
            "added": tuple(added),
            "added_count": len(added),
            "skipped_count": skipped,
        }


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

    def collection_names(self):

        return self.collections.names()


    def create_collection(
        self,
        name,
    ):

        return self.collections.create(
            name
        )


    def rename_collection(
        self,
        current_name,
        new_name,
    ):

        return self.collections.rename(
            current_name,
            new_name,
        )


    def delete_collection(
        self,
        name,
    ):

        return self.collections.delete(
            name
        )


    def add_to_collection(
        self,
        name,
        game,
    ):

        return self.collections.add_game(
            name,
            game,
        )


    def remove_from_collection(
        self,
        name,
        game,
    ):

        return self.collections.remove_game(
            name,
            game,
        )


    def collection_games(
        self,
        name,
    ):

        identities = (
            self.collections.identities(
                name
            )
        )

        games_by_identity = {}

        for game in self.games:

            try:
                identity = game_identity(
                    game
                )
            except ValueError:
                continue

            games_by_identity[
                identity
            ] = game

        return [
            games_by_identity[identity]
            for identity in identities
            if identity in games_by_identity
        ]
