from services.library.scanner import RomScanner


class LibraryBuilder:


    def __init__(
        self,
        rvdb_resolver=None,
    ):

        self.scanner = RomScanner(
            rvdb_resolver=rvdb_resolver
        )


    def build(self, sources, *, control=None):

        games = []


        for source in sources:


            if not source.enabled:

                continue


            results = self.scanner.scan(
                source, **({"control": control} if control is not None else {})
            )


            games.extend(
                results
            )


        return games
