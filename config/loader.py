import os
import yaml



CONFIG_FILE = os.path.join(

    os.path.dirname(
        __file__
    ),

    "retroarch.yaml"

)



class ConfigLoader:



    def load(self):


        with open(
            CONFIG_FILE,
            "r"
        ) as file:


            return yaml.safe_load(
                file
            )
