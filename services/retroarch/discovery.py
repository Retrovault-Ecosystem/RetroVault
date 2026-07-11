import os
import shutil



class RetroArchDiscovery:



    def __init__(self):

        self.retroarch = None

        self.core_directory = None



    def find_retroarch(self):


        path = shutil.which(
            "retroarch"
        )


        self.retroarch = path


        return path



    def find_core_directory(self):


        possible = [

    # User RetroArch cores
    os.path.expanduser(
        "~/.config/retroarch/cores"
    ),


    # Standard Linux locations
    "/usr/lib/libretro",

    "/usr/lib/retroarch/cores",

    "/usr/lib/x86_64-linux-gnu/libretro",


    # RetroPie
    "/opt/retropie/libretrocores",


    # Snap
    os.path.expanduser(
        "~/snap/retroarch/common/.config/retroarch/cores"
    ),


    # Flatpak
    os.path.expanduser(
        "~/.var/app/org.libretro.RetroArch/config/retroarch/cores"
    )

]


        for directory in possible:


            if os.path.exists(directory):

                self.core_directory = directory

                return directory



        return None



    def installed(self):


        return self.retroarch is not None
