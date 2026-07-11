class LibraryQuery:


    def __init__(self, games):

        self.games = games



    def all(self):

        return self.games



    def search(self, text):

        text = text.lower()


        return [
            game
            for game in self.games
            if text in game.name.lower()
        ]



    def filter_platform(self, platform):

        return [
            game
            for game in self.games
            if game.platform == platform
        ]



    def favorites(self):

        return [
            game
            for game in self.games
            if game.favorite
        ]



    def sort_name(self):

        return sorted(
            self.games,
            key=lambda game: game.name
        )



    def sort_year(self):

        return sorted(
            self.games,
            key=lambda game: game.year or 0
        )
