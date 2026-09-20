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
from services.library.canonicalization import LibraryCanonicalizer


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

        self.canonicalizer = LibraryCanonicalizer()
        self._physical_games = []

        self.games = []


    def _canonicalizer(self):
        """
        Return the Library canonicalizer.

        LibraryService normally creates this dependency in __init__.
        A small number of established service tests intentionally
        construct LibraryService through __new__ so they can isolate
        source/reload behavior without running the production
        constructor. Keep that supported contract while ensuring
        production and test-created instances use the same
        canonicalization boundary.
        """

        canonicalizer = getattr(
            self,
            "canonicalizer",
            None,
        )

        if canonicalizer is None:
            canonicalizer = LibraryCanonicalizer()
            self.canonicalizer = canonicalizer

        return canonicalizer

    def _physical_inventory(self):
        """
        Return the complete physical-ROM inventory.

        Production instances maintain _physical_games directly.
        Constructor-bypassed compatibility instances may begin with
        only the canonical projection in self.games; in that case,
        reconstruct the physical editions from the canonical variant
        metadata before any incremental merge.
        """

        physical_games = getattr(
            self,
            "_physical_games",
            None,
        )

        visible_games = list(
            getattr(
                self,
                "games",
                [],
            )
            or []
        )

        needs_bootstrap = (
            physical_games is None
            or (
                not physical_games
                and bool(
                    visible_games
                )
            )
        )

        if needs_bootstrap:
            physical_games = (
                self._expand_canonical_games(
                    visible_games
                )
            )

            self._physical_games = (
                physical_games
            )

        return physical_games

    @staticmethod
    def _variant_game_from_record(
        representative,
        variant,
    ):
        """
        Reconstruct one physical Game from canonical variant metadata.

        The representative supplies shared Library/RVDB metadata while
        the variant record supplies the physical ROM identity and its
        edition-specific presentation metadata.
        """

        from dataclasses import replace

        game = replace(
            representative
        )

        game.name = str(
            variant.get(
                "name",
                "",
            )
            or representative.name
        )

        game.rom = str(
            variant.get(
                "rom",
                "",
            )
            or ""
        )

        game.source = str(
            variant.get(
                "source",
                "",
            )
            or representative.source
        )

        game.variant_category = str(
            variant.get(
                "category",
                "",
            )
            or ""
        )

        game.variant_label = str(
            variant.get(
                "label",
                "",
            )
            or ""
        )

        game.variant_region = str(
            variant.get(
                "region",
                "",
            )
            or ""
        )

        game.variant_language = str(
            variant.get(
                "language",
                "",
            )
            or ""
        )

        game.variant_revision = str(
            variant.get(
                "revision",
                "",
            )
            or ""
        )

        game.is_primary_variant = bool(
            variant.get(
                "preferred",
                False,
            )
        )

        game.variants = []

        return game

    def _expand_canonical_games(
        self,
        games,
    ):
        """
        Expand canonical Library representatives into physical editions.

        This is primarily a compatibility bridge for service instances
        created before _physical_games existed and for isolated tests
        that intentionally construct LibraryService through __new__.
        """

        physical_games = []
        seen = set()

        for representative in games:
            variants = list(
                getattr(
                    representative,
                    "variants",
                    [],
                )
                or []
            )

            if not variants:
                try:
                    identity = game_identity(
                        representative
                    )
                except ValueError:
                    continue

                if identity not in seen:
                    seen.add(identity)
                    physical_games.append(
                        representative
                    )

                continue

            for variant in variants:
                if not isinstance(
                    variant,
                    dict,
                ):
                    continue

                rom = str(
                    variant.get(
                        "rom",
                        "",
                    )
                    or ""
                )

                if not rom:
                    continue

                representative_rom = str(
                    getattr(
                        representative,
                        "rom",
                        "",
                    )
                    or ""
                )

                if rom == representative_rom:
                    game = representative
                else:
                    game = (
                        self._variant_game_from_record(
                            representative,
                            variant,
                        )
                    )

                try:
                    identity = game_identity(
                        game
                    )
                except ValueError:
                    continue

                if identity in seen:
                    continue

                seen.add(identity)
                physical_games.append(
                    game
                )

        return physical_games

    def load(self):

        physical_games = self.builder.build(
            self.sources.sources()
        )

        physical_games = self.state.apply(
            physical_games
        )

        for game in physical_games:

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

        self._physical_games = list(
            physical_games
        )

        canonical_games = (
            self._canonicalizer().canonicalize(
                self._physical_games
            )
        )

        identity_equivalent = (
            len(canonical_games)
            == len(physical_games)
            and all(
                canonical is physical
                for canonical, physical
                in zip(
                    canonical_games,
                    physical_games,
                )
            )
        )

        if identity_equivalent:
            self.games = physical_games
        else:
            self.games = canonical_games

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

        previous_by_identity = {}

        for game in previous_games:
            try:
                identity = game_identity(
                    game
                )
            except ValueError:
                continue

            previous_by_identity[
                identity
            ] = game

        self.sources = refreshed_sources

        try:
            reloaded_games = self.load()

            preserved_games = []

            for game in reloaded_games:
                try:
                    identity = game_identity(
                        game
                    )
                except ValueError:
                    preserved_games.append(
                        game
                    )
                    continue

                previous_game = (
                    previous_by_identity.get(
                        identity
                    )
                )

                if previous_game is None:
                    preserved_games.append(
                        game
                    )
                    continue

                previous_game.name = game.name
                previous_game.platform = game.platform
                previous_game.year = game.year
                previous_game.genre = game.genre
                previous_game.core = game.core
                previous_game.rom = game.rom
                previous_game.source = game.source
                previous_game.artwork = game.artwork
                previous_game.favorite = game.favorite
                previous_game.rvdb_platform_id = (
                    game.rvdb_platform_id
                )
                previous_game.rvdb_game_id = (
                    game.rvdb_game_id
                )
                previous_game.description = (
                    game.description
                )
                previous_game.developer = (
                    game.developer
                )
                previous_game.publisher = (
                    game.publisher
                )

                preserved_games.append(
                    previous_game
                )

            self.games = preserved_games

            return self.games

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
        physical_games = list(
            self._physical_inventory()
        )

        existing_identities = set()

        for game in physical_games:
            try:
                existing_identities.add(
                    game_identity(
                        game
                    )
                )
            except ValueError:
                continue

        added_physical = []
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

            applied = self.state.apply(
                [game]
            )

            if not applied:
                skipped += 1
                continue

            imported_game = applied[0]

            artwork = (
                self.artwork.get_artwork(
                    imported_game
                )
            )

            imported_game.artwork = (
                artwork
                if artwork is not None
                else ""
            )

            existing_identities.add(
                identity
            )

            physical_games.append(
                imported_game
            )

            added_physical.append(
                imported_game
            )

        self._physical_games = (
            physical_games
        )

        previous_by_identity = {}

        for game in getattr(
            self,
            "games",
            [],
        ):
            try:
                previous_by_identity[
                    game_identity(game)
                ] = game
            except ValueError:
                continue

        canonical_games = (
            self._canonicalizer().canonicalize(
                self._physical_games
            )
        )

        preserved_games = []

        for game in canonical_games:
            try:
                identity = game_identity(
                    game
                )
            except ValueError:
                preserved_games.append(
                    game
                )
                continue

            existing_game = (
                previous_by_identity.get(
                    identity
                )
            )

            if (
                existing_game is None
                or existing_game is game
            ):
                preserved_games.append(
                    game
                )
                continue

            for attribute in (
                "name",
                "platform",
                "year",
                "genre",
                "core",
                "rom",
                "source",
                "artwork",
                "favorite",
                "rvdb_platform_id",
                "rvdb_game_id",
                "description",
                "developer",
                "publisher",
                "canonical_title",
                "family_key",
                "variant_category",
                "variant_label",
                "variant_region",
                "variant_language",
                "variant_revision",
                "is_primary_variant",
            ):
                setattr(
                    existing_game,
                    attribute,
                    getattr(
                        game,
                        attribute,
                    ),
                )

            existing_game.variants = list(
                game.variants
            )

            preserved_games.append(
                existing_game
            )

        preserved_games.sort(
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

        self.games = preserved_games

        return {
            "added": tuple(
                added_physical
            ),
            "added_count": len(
                added_physical
            ),
            "skipped_count": skipped,
        }

    def _legacy_merge_bulk_import(
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
