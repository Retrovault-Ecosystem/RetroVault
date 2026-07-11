from services.library.scanner import RomScanner


class LibraryBuilder:


    def __init__(self):

        self.scanner = RomScanner()



    def build(self, sources):

        games = []


        for source in sources:


            if not source.enabled:

                continue


            results = self.scanner.scan(
                source
            )


            games.extend(
                results
            )


        return games
