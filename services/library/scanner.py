import os

from services.library.core_mapper import CoreMapper
from services.library.models import Game


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


    def __init__(self):

        self.core_mapper = CoreMapper()



    def scan(self, source):

        games = []


        root = os.path.expanduser(
            source.path
        )


        for directory, folders, files in os.walk(root):


            for filename in files:


                ext = os.path.splitext(
                    filename
                )[1].lower()



                if ext not in SUPPORTED_EXTENSIONS:

                    continue



                platform = SUPPORTED_EXTENSIONS[ext]


                games.append(

                    Game(

                        name=os.path.splitext(filename)[0],

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

                        source=source.name

                    )

                )


        return games