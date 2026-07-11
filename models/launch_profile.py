from dataclasses import dataclass



@dataclass
class LaunchProfile:


    game: str

    rom: str

    core: str


    config: str = ""

    overlay: str = ""

    shader: str = ""
