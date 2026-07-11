CORE_MAP = {

    "Nintendo Entertainment System":
        "fceumm_libretro.so",

    "Super Nintendo":
        "snes9x_libretro.so",

    "Sega Genesis":
        "genesis_plus_gx_libretro.so",

    "Nintendo 64":
        "mupen64plus_next_libretro.so",

    "Arcade":
        "mame_libretro.so",

}



class CoreMapper:


    def get_core(self, platform):

        return CORE_MAP.get(
            platform,
            ""
        )
