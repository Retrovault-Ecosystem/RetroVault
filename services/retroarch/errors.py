class LaunchError:


    def __init__(
        self,
        message
    ):

        self.message = message



    def display(self):

        return (

            "RetroVault Launch Error\n\n"

            +
            self.message

        )
