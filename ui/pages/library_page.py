from ui.library.gallery import GalleryView


class LibraryPage(GalleryView):
    def __init__(
        self,
        games,
        rvdb_service=None,
        favorite_handler=None,
        played_handler=None,
        recent_provider=None,
        collection_names_provider=None,
        collection_add_handler=None,
        refresh_handler=None,
        refresh_completed_handler=None,
        bulk_import_handler=None,
        bulk_import_completed_handler=None,
        presentation_resolver_provider=None,
        launcher=None,
        process_lifecycle=None,
    ):
        super().__init__(
            games,
            rvdb_service=rvdb_service,
            favorite_handler=favorite_handler,
            played_handler=played_handler,
            recent_provider=recent_provider,
            collection_names_provider=(
                collection_names_provider
            ),
            collection_add_handler=(
                collection_add_handler
            ),
            refresh_handler=(
                refresh_handler
            ),
            refresh_completed_handler=(
                refresh_completed_handler
            ),
            bulk_import_handler=(
                bulk_import_handler
            ),
            bulk_import_completed_handler=(
                bulk_import_completed_handler
            ),
            presentation_resolver_provider=(
                presentation_resolver_provider
            ),
            launcher=launcher,
            process_lifecycle=process_lifecycle,
        )
