from pathlib import Path
from services.library.identity import IdentityRegistry, location_key, family_identities, project_identities
from services.library.identity_migration import migrate_stores
from services.presentation.store import PresentationStore
from copy import deepcopy
from dataclasses import fields

from services.library.models import Game
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
        identity_registry=None,
        presentation_store=None,
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
                directory=artwork_directory, rvdb_resolver=rvdb_resolver
            )
        )

        state_path = getattr(self.state, "state_file", None)
        self.identity_registry = identity_registry or (
            IdentityRegistry(Path(state_path).parent / "library-identities.json")
            if state_path is not None else None
        )
        self.presentation_store = presentation_store or (
            PresentationStore(Path(state_path).parent / "presentation-state.json")
            if state_path is not None else None
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

        game.local_file_id = str(variant.get("local_file_id", "") or "")

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

        game.artwork = str(variant.get("artwork", "") or "")
        game.artwork_origin = str(variant.get("artwork_origin", "") or "")
        game.artwork_explicit = str(variant.get("artwork_explicit", "") or "")
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

    def _register(self, games):
        registry = getattr(self, "identity_registry", None)
        if registry is None:
            return games
        games, staged = registry.stage(games)
        stores = [store for store in (
            self.state, self.collections, self.presentation_store
        ) if callable(getattr(store, "validate_identity_migration", None))]
        for store in stores:
            store.validate_identity_migration()
        registry.commit(staged)
        migrate_stores(staged["legacy_paths"], *stores)
        return games

    def _project_favorites(self, games):
        # Read ownership from the store, not representative.favorite: the latter
        # is a family projection and must never leak onto a different edition.
        reader = getattr(self.state, "favorites", None)
        if callable(reader):
            favorites = reader()
            for game in games:
                try:
                    game.favorite = bool(set(family_identities(game)) & favorites)
                except ValueError:
                    game.favorite = False
        return games

    def load(self):

        invalidate = getattr(self.artwork, "invalidate", None)
        if callable(invalidate):
            invalidate()

        physical_games = self.builder.build(
            self.sources.sources()
        )

        physical_games = self._register(physical_games)
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

        self._project_favorites(self.games)
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
        previous_physical = getattr(self, "_physical_games", None)
        previous_objects = {
            id(game): (game, deepcopy(vars(game)))
            for game in [*previous_games, *(previous_physical or [])]
            if hasattr(game, "__dict__")
        }

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

                for field in fields(Game):
                    if hasattr(game, field.name):
                        setattr(
                            previous_game,
                            field.name,
                            deepcopy(getattr(game, field.name)),
                        )

                preserved_games.append(
                    previous_game
                )

            # Physical inventory and the visible projection must reference the
            # same surviving representative after an identity-preserving reload.
            replacements = {
                game_identity(game): game
                for game in preserved_games
                if getattr(game, "rom", "")
            }
            self._physical_games = [
                replacements.get(game_identity(game), game)
                if getattr(game, "rom", "") else game
                for game in getattr(self, "_physical_games", [])
            ]
            self.games = preserved_games

            return self.games

        except Exception:
            self.sources = previous_sources
            self.games = previous_games
            if previous_physical is None:
                self.__dict__.pop("_physical_games", None)
            else:
                self._physical_games = previous_physical
            for game, state in previous_objects.values():
                game.__dict__.clear()
                game.__dict__.update(state)
            raise


    def refresh_artwork(
        self,
        directory,
    ):

        self.artwork.set_directory(
            directory
        )

        physical = self._physical_inventory()
        for game in physical:
            game.artwork = self.artwork.get_artwork(game) or ""
        self.games = self._canonicalizer().canonicalize(physical)
        self._project_favorites(self.games)

        return self.games


    def get_games(self):

        return self.games


    def _merge_registered(self, result):
        previous_games = self.games
        previous_physical = self._physical_games
        old_objects = {id(g): (g, deepcopy(vars(g))) for g in [*previous_games, *previous_physical]}
        try:
            incoming = self._register(list(result.games))
            physical = list(previous_physical)
            known = {game_identity(g): g for g in physical}
            added, skipped = [], len(result.games) - len(incoming)
            for game in incoming:
                identity = game_identity(game)
                survivor = known.get(identity)
                if survivor is not None:
                    # A moved registered file is the same edition, at a new location.
                    for field in fields(Game):
                        setattr(survivor, field.name, deepcopy(getattr(game, field.name)))
                    game = survivor
                    skipped += 1
                else:
                    added.append(game)
                physical = [g for g in physical if g is not game
                            and location_key(g.rom) != location_key(game.rom)]
                physical.append(game)
                known[identity] = game
            self.state.apply(physical)
            for game in physical:
                game.artwork = self.artwork.get_artwork(game) or ""
            canonical = self._canonicalizer().canonicalize(physical)
            self._project_favorites(canonical)
            self._physical_games = physical
            self.games = canonical
            return {"added": tuple(added), "added_count": len(added), "skipped_count": skipped}
        except Exception:
            self.games, self._physical_games = previous_games, previous_physical
            for game, state in old_objects.values():
                game.__dict__.clear()
                game.__dict__.update(state)
            raise

    def merge_bulk_import(
        self,
        result,
    ):
        if getattr(self, "identity_registry", None) is not None:
            return self._merge_registered(result)

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
                "local_file_id",
                "source",
                "artwork",
                "artwork_origin",
                "artwork_explicit",
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

        self.games = self._project_favorites(preserved_games)

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

        self._project_favorites(getattr(self, "games", []))
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

        return project_identities(self.games, identities)

    @staticmethod
    def query_platform_statistics(platform_id, *, games_provider, recent_provider=None,
                                  collection_names_provider=None, collection_games_provider=None):
        """Project existing family identities; None means unavailable, never zero."""
        result = {'games': None, 'favorites': None, 'recent': None, 'collections': None,
                  'errors': {}}
        try:
            if games_provider is None:
                return result
            matching = [game for game in games_provider()
                        if str(getattr(game, 'rvdb_platform_id', '') or '') == platform_id]
        except (OSError, ValueError, RuntimeError, TypeError) as exc:
            result['errors']['games'] = str(exc)
            return result
        result['games'] = len(matching)
        result['favorites'] = sum(bool(getattr(game, 'favorite', False)) for game in matching)
        if recent_provider is not None:
            try:
                result['recent'] = len(project_identities(matching, {str(i) for i in recent_provider()}))
            except (OSError, ValueError, RuntimeError, TypeError) as exc:
                result['errors']['recent'] = str(exc)
        if collection_names_provider is not None and collection_games_provider is not None:
            try:
                result['collections'] = sum(
                    any(str(getattr(game, 'rvdb_platform_id', '') or '') == platform_id
                        for game in collection_games_provider(name))
                    for name in collection_names_provider())
            except (OSError, ValueError, RuntimeError, TypeError) as exc:
                result['errors']['collections'] = str(exc)
        return result

    def platform_statistics(self, platform_id):
        return self.query_platform_statistics(
            platform_id, games_provider=self.get_games, recent_provider=self.recent,
            collection_names_provider=self.collection_names,
            collection_games_provider=self.collection_games)
