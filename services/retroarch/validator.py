import os



class LaunchValidator:



    def __init__(
        self,
        retroarch,
        core
    ):

        self.retroarch = retroarch

        self.core = core



    def validate(
        self,
        rom
    ):


        results = {

            "retroarch":
            self.check_retroarch(),


            "core":
            self.check_core(),


            "rom":
            self.check_rom(rom)

        }


        results["ready"] = all(
            results.values()
        )


        return results



    def check_retroarch(self):


        return (

            self.retroarch
            is not None

            and

            os.path.exists(
                self.retroarch
            )

        )



    def check_core(self):


        return (

            self.core
            is not None

            and

            os.path.exists(
                self.core
            )

        )



    def check_rom(
        self,
        rom
    ):


        if rom is None:
            return False

        if not os.path.isfile(
            rom
        ):
            return False

        try:
            return (
                os.path.getsize(
                    rom
                )
                > 0
            )
        except OSError:
            return False
