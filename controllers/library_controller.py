from services.library import LibraryService



class LibraryController:


    def __init__(self):

        self.library = LibraryService()

        self.library.load()



    def get_games(self):

        return self.library.get_games()
