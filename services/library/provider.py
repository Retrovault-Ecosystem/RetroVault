from services.library.models import Game


class LibraryProvider:


    def load_games(self):

        """
        Temporary data provider.

        Later this will load from:
        - RVDB
        - ROM scanner
        - metadata files
        """

        return [

            Game(
                name="Super Metroid",
                platform="SNES",
                year=1994,
                genre="Action Adventure",
                core="bsnes"
            ),


            Game(
                name="The Legend of Zelda",
                platform="NES",
                year=1986,
                genre="Adventure",
                core="Mesen"
            ),


            Game(
                name="Sonic the Hedgehog",
                platform="Genesis",
                year=1991,
                genre="Platformer",
                core="Genesis Plus GX"
            ),

        ]
