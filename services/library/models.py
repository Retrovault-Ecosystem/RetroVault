from dataclasses import dataclass, field
from typing import List


@dataclass
class Game:

    name: str

    platform: str

    year: int

    genre: str

    core: str

    rom: str = ""

    source: str = ""

    artwork: str = ""

    favorite: bool = False
