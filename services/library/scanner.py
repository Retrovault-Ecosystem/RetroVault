import os
from pathlib import Path

from services.library.core_mapper import CoreMapper
from services.library.models import Game
from services.library.rvdb_resolver import (
    RVDBLibraryResolver,
)


SUPPORTED_EXTENSIONS = {

    ".nes": "Nintendo Entertainment System",

    ".sfc": "Super Nintendo",

    ".smc": "Super Nintendo",

    ".bin": "Unknown",

    ".gen": "Sega Genesis",

    ".md": "Sega Genesis",

    ".chd": "Unknown",

    ".iso": "Unknown",

    ".cue": "Unknown",

    ".zip": "Arcade",

    ".7z": "Archive",

    ".z64": "Nintendo 64",

    ".n64": "Nintendo 64",

    ".v64": "Nintendo 64",

}


class RomScanner:

    def __init__(
        self,
        rvdb_resolver=None,
    ):

        self.core_mapper = CoreMapper()

        self.rvdb_resolver = (
            rvdb_resolver
            if rvdb_resolver is not None
            else self._default_rvdb_resolver()
        )

    @staticmethod
    def _default_rvdb_resolver():

        bundle = Path(
            "data/rvdb/rvdb.bundle.json"
        )

        if not bundle.is_file():
            return None

        return (
            RVDBLibraryResolver.from_bundle(
                bundle
            )
        )

    def _resolve_platform(
        self,
        extension,
        legacy_platform,
    ):

        if self.rvdb_resolver is None:
            return (
                legacy_platform,
                "",
            )

        rvdb_platform = (
            self.rvdb_resolver
            .platform_for_extension(
                extension
            )
        )

        if rvdb_platform is None:
            return (
                legacy_platform,
                "",
            )

        return (
            rvdb_platform.get(
                "name",
                legacy_platform,
            ),
            rvdb_platform["id"],
        )

    def scan(self, source):

        games = []

        root = os.path.expanduser(
            source.path
        )

        for directory, folders, files in os.walk(
            root
        ):

            for filename in files:

                ext = os.path.splitext(
                    filename
                )[1].lower()

                if ext not in SUPPORTED_EXTENSIONS:

                    continue

                legacy_platform = (
                    SUPPORTED_EXTENSIONS[
                        ext
                    ]
                )

                (
                    platform,
                    rvdb_platform_id,
                ) = self._resolve_platform(
                    ext,
                    legacy_platform,
                )

                games.append(

                    Game(

                        name=os.path.splitext(
                            filename
                        )[0],

                        platform=platform,

                        year=0,

                        genre="",

                        core=self.core_mapper.get_core(
                            platform
                        ),

                        rom=os.path.join(
                            directory,
                            filename
                        ),

                        source=source.name,

                        rvdb_platform_id=(
                            rvdb_platform_id
                        ),

                    )

                )

        return games
