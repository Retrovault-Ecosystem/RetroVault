import os

from services.retroarch.archive_runtime import ArchiveRuntime

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

        self.rvdb_resolver = rvdb_resolver

        self.archive_runtime = ArchiveRuntime()

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
            rvdb_platform.name,
            rvdb_platform.id,
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

                platform_extension = ext

                if ext == ".7z":
                    archive_path = os.path.join(
                        directory,
                        filename,
                    )

                    preferred_member = (
                        self.archive_runtime
                        .preferred_member(
                            archive_path
                        )
                    )

                    if preferred_member:
                        member_extension = (
                            os.path.splitext(
                                preferred_member
                            )[1]
                            .lower()
                        )

                        if (
                            member_extension
                            in SUPPORTED_EXTENSIONS
                            and member_extension
                            != ".7z"
                        ):
                            platform_extension = (
                                member_extension
                            )
                            legacy_platform = (
                                SUPPORTED_EXTENSIONS[
                                    member_extension
                                ]
                            )

                (
                    platform,
                    rvdb_platform_id,
                ) = self._resolve_platform(
                    platform_extension,
                    legacy_platform,
                )

                game_name = os.path.splitext(
                    filename
                )[0]

                rvdb_game_id = ""

                if (
                    self.rvdb_resolver is not None
                    and rvdb_platform_id
                ):
                    rvdb_game = (
                        self.rvdb_resolver.game_for_name(
                            game_name,
                            rvdb_platform_id,
                        )
                    )

                    if rvdb_game is not None:
                        rvdb_game_id = (
                            rvdb_game.id
                        )

                games.append(

                    Game(

                        name=game_name,

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

                        rvdb_game_id=(
                            rvdb_game_id
                        ),

                    )

                )

        return games
