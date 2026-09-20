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

    rvdb_platform_id: str = ""

    rvdb_game_id: str = ""

    description: str = ""

    developer: str = ""

    publisher: str = ""

    # RetroVault canonical game-family metadata.
    #
    # These fields are additive and default-safe so existing Game
    # construction, persistence, tests, and callers remain compatible.
    canonical_title: str = ""
    family_key: str = ""
    variant_category: str = ""
    variant_label: str = ""
    variant_region: str = ""
    variant_language: str = ""
    variant_revision: str = ""
    is_primary_variant: bool = True
    variants: List[object] = field(default_factory=list)
