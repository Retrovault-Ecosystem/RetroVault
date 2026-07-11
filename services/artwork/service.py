from pathlib import Path


class ArtworkService:


    def __init__(self):

        self.cache = {}


    def get_artwork(self, game):

        if game.name in self.cache:

            return self.cache[game.name]


        if game.artwork:

            path = Path(
                game.artwork
            )

            if path.exists():

                self.cache[game.name] = str(path)

                return str(path)


        return None
