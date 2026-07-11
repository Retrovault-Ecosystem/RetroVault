import subprocess

from models.launch_profile import LaunchProfile



class RetroArchLauncher:



    def __init__(self):

        self.command = "retroarch"



    def launch(
        self,
        profile: LaunchProfile
    ):


        command = [

            self.command,

            "-L",

            profile.core,

            profile.rom

        ]



        if profile.config:


            command.extend(

                [

                    "--config",

                    profile.config

                ]

            )



        try:


            subprocess.Popen(
                command
            )


            return {

                "success": True,

                "command": command

            }



        except Exception as error:


            return {

                "success": False,

                "error": str(error)

            }
