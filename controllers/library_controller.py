from services.library import LibraryService
from services.library.bulk_import import BulkImporter
from services.library.import_sources import ImportSourceStore


class LibraryController:


    def __init__(
        self,
        rvdb_resolver=None,
        bulk_importer=None,
        import_source_store=None,
    ):

        self.library = LibraryService(
            rvdb_resolver=rvdb_resolver
        )

        self.bulk_importer = (
            bulk_importer
            if bulk_importer is not None
            else BulkImporter(
                rvdb_resolver=rvdb_resolver
            )
        )

        self.import_source_store = (
            import_source_store
            if import_source_store is not None
            else ImportSourceStore()
        )

        self.library.load()


    def get_games(self):

        return self.library.get_games()


    def bulk_import(
        self,
        directory,
        *,
        source_id="bulk-import",
        source_name="Bulk Import",
    ):

        discovered = (
            self.bulk_importer
            .import_directory(
                directory,
                source_id=source_id,
                source_name=source_name,
            )
        )

        persisted = (
            self.import_source_store
            .persist_directory(
                discovered.source.path,
                source_id=source_id,
                source_name=source_name,
            )
        )

        merged = self.library.merge_bulk_import(
            discovered
        )

        return {
            "discovered": discovered,
            "added": merged["added"],
            "added_count": merged["added_count"],
            "skipped_count": merged["skipped_count"],
            "persisted": persisted,
            "games": tuple(
                self.library.get_games()
            ),
        }


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
