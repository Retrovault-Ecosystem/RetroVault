import os



class CoreScanner:


    def __init__(
        self,
        directory
    ):

        self.directory = directory



    def scan(self):


        if not self.directory:

            return []



        cores = []



        for root, dirs, files in os.walk(
            self.directory
        ):


            for file in files:


                if file.endswith(
                    ".so"
                ):


                    cores.append(

                        os.path.join(
                            root,
                            file
                        )

                    )



        return sorted(
            cores
        )
