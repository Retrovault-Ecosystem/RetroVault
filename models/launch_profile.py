from dataclasses import dataclass



@dataclass
class LaunchProfile:


    game: str

    rom: str

    core: str


    config: str = ""

    overlay: str = ""

    shader: str = ""

    archive_member: str = ""

    cheat_file: str = ""

    platform_id: str = ""

    # Optional emulator/core-authoritative display shape.
    #
    # These fields describe neither the source raster nor an
    # individual title.  When present, presentation runtime code may
    # proportionally CONTAIN this display aspect inside the fixed
    # platform presentation envelope.
    display_aspect_width: float | None = None
    display_aspect_height: float | None = None
