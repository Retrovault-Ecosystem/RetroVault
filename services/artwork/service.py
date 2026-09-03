from pathlib import Path


SUPPORTED_ARTWORK_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


class ArtworkService:


    def __init__(
        self,
        directory=None,
    ):

        self.directory = (
            Path(
                directory
            ).expanduser()
            if directory
            else None
        )

        self.cache = {}

        self._index = None


    @staticmethod
    def _identity(game):

        rom = getattr(
            game,
            "rom",
            "",
        )

        if rom:
            return str(rom)

        return (
            getattr(
                game,
                "name",
                "",
            ),
            getattr(
                game,
                "platform",
                "",
            ),
        )


    def _build_index(self):

        if self._index is not None:
            return self._index

        index = {}

        root = self.directory

        if (
            root is None
            or not root.is_dir()
        ):
            self._index = index

            return self._index

        try:

            for path in root.rglob(
                "*"
            ):

                if not path.is_file():
                    continue

                if (
                    path.suffix.lower()
                    not in SUPPORTED_ARTWORK_EXTENSIONS
                ):
                    continue

                key = (
                    path.stem
                    .casefold()
                )

                index.setdefault(
                    key,
                    [],
                ).append(
                    path
                )

        except OSError:

            self._index = {}

            return self._index

        for paths in index.values():

            paths.sort(
                key=lambda item:
                    str(item)
                    .casefold()
            )

        self._index = index

        return self._index


    def _discover_artwork(
        self,
        game,
    ):

        rom = getattr(
            game,
            "rom",
            "",
        )

        if not rom:
            return None

        stem = (
            Path(
                rom
            )
            .stem
            .casefold()
        )

        matches = (
            self._build_index()
            .get(
                stem,
                [],
            )
        )

        if len(matches) != 1:
            return None

        return str(
            matches[0]
        )


    def get_artwork(
        self,
        game,
    ):

        identity = self._identity(
            game
        )

        if identity in self.cache:

            return self.cache[
                identity
            ]

        artwork = getattr(
            game,
            "artwork",
            "",
        )

        if artwork:

            path = Path(
                artwork
            ).expanduser()

            if path.is_file():

                resolved = str(
                    path
                )

                self.cache[
                    identity
                ] = resolved

                return resolved

        discovered = (
            self._discover_artwork(
                game
            )
        )

        if discovered is None:
            return None

        self.cache[
            identity
        ] = discovered

        return discovered
