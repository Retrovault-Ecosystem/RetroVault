import random



class GameRandomizer:


    def __init__(self, games):

        self.games = games



    def random_game(self):

        if not self.games:

            return None


        return random.choice(
            self.games
        )
