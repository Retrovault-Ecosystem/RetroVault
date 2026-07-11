class RetroArchReport:



    def __init__(
        self,
        discovery,
        cores
    ):

        self.discovery = discovery

        self.cores = cores



    def generate(self):


        return {

            "retroarch":
            self.discovery.retroarch,


            "core_directory":
            self.discovery.core_directory,


            "cores":
            self.cores

        }
