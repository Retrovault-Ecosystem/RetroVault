class GameHistory:


    def __init__(self):

        self.history = []



    def played(self, game):

        if game in self.history:

            self.history.remove(
                game
            )


        self.history.insert(
            0,
            game
        )



    def recent(self, limit=10):

        return self.history[:limit]
