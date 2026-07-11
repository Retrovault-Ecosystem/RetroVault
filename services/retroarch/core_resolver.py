import os



class CoreResolver:


    def __init__(
        self,
        config
    ):

        self.core_directory = (

            config["retroarch"]
                  ["cores"]
                  ["directory"]

        )



    def find(
        self,
        name
    ):


        if not self.core_directory:

            return None



        self.core_directory = os.path.expanduser(

            self.core_directory

        )



        for root, dirs, files in os.walk(

            self.core_directory

        ):


            for file in files:


                if file.endswith(".so"):


                    if name.lower() in file.lower():

                        return os.path.join(

                            root,

                            file

                        )



        return None
