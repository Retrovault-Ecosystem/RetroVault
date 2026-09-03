from pathlib import Path


class ArtworkService:


    def __init__(self):

        self.cache = {}


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


    def get_artwork(self, game):

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

        if not artwork:

            return None


        path = Path(
            artwork
        )

        if not path.is_file():

            return None


        resolved = str(
            path
        )

        self.cache[
            identity
        ] = resolved

        return resolved
