import subprocess

from models.launch_profile import LaunchProfile

from .overlay_runtime import OverlayRuntimeConfig



class RetroArchLauncher:



    def __init__(
        self,
        overlay_runtime=None,
    ):

        self.command = "retroarch"

        self.overlay_runtime = (
            overlay_runtime
            or OverlayRuntimeConfig()
        )



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


        if profile.overlay:

            try:
                append_config = (
                    self.overlay_runtime.create(
                        profile.overlay
                    )
                )
            except (
                OSError,
                ValueError,
            ) as error:
                return {
                    "success": False,
                    "error": str(error),
                }

            command.extend(
                [
                    "--appendconfig",
                    append_config,
                ]
            )


        if profile.shader:


            command.extend(

                [

                    "--set-shader",

                    profile.shader

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
