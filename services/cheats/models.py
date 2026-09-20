from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterable


class CheatCodeType(str, Enum):
    RETROARCH = "retroarch"
    GAME_GENIE = "game_genie"
    GAMESHARK = "gameshark"
    ACTION_REPLAY = "action_replay"
    PRO_ACTION_REPLAY = "pro_action_replay"
    CODEBREAKER = "codebreaker"
    RAW = "raw"
    CUSTOM = "custom"


class CheatCategory(str, Enum):
    GAMEPLAY = "Gameplay"
    LIVES_HEALTH = "Lives / Health"
    INVINCIBILITY = "Invincibility"
    LEVEL_STAGE = "Level / Stage Select"
    ITEMS = "Items / Inventory"
    WEAPONS = "Weapons / Power-Ups"
    CHARACTER = "Character / Player"
    TIME = "Time / Timer"
    SCORE = "Score / Currency"
    UNLOCKABLES = "Unlockables"
    DEBUG = "Debug / Developer"
    MISC = "Miscellaneous"
    CUSTOM = "Custom Codes"


@dataclass(frozen=True)
class CheatIdentity:
    """
    Physical game identity used for cheat matching.

    Cheats intentionally bind to the physical edition/member being
    launched rather than only to RetroVault's canonical family card.
    """

    platform: str
    canonical_title: str
    rom_path: str
    archive_member: str = ""
    variant_category: str = ""
    region: str = ""
    language: str = ""
    revision: str = ""
    rvdb_game_id: str = ""
    sha256: str = ""

    @property
    def filename(self) -> str:
        if self.archive_member:
            return Path(
                self.archive_member
            ).name

        return Path(
            self.rom_path
        ).name


@dataclass(frozen=True)
class CheatCode:
    name: str
    code: str
    code_type: CheatCodeType = (
        CheatCodeType.RETROARCH
    )
    category: CheatCategory = (
        CheatCategory.MISC
    )
    description: str = ""
    source: str = ""
    enabled: bool = False
    compatible: bool = True
    compatibility_note: str = ""

    @property
    def normalized_code(self) -> str:
        return self.code.strip()


@dataclass
class CheatCollection:
    identity: CheatIdentity
    cheats: list[CheatCode] = field(
        default_factory=list
    )

    def compatible(self) -> list[CheatCode]:
        return [
            cheat
            for cheat in self.cheats
            if cheat.compatible
        ]

    def enabled(self) -> list[CheatCode]:
        return [
            cheat
            for cheat in self.cheats
            if cheat.enabled
        ]

    def grouped(
        self,
    ) -> dict[CheatCategory, list[CheatCode]]:
        grouped = {}

        for cheat in self.cheats:
            grouped.setdefault(
                cheat.category,
                [],
            ).append(
                cheat
            )

        return grouped

    @classmethod
    def from_iterable(
        cls,
        identity: CheatIdentity,
        cheats: Iterable[CheatCode],
    ) -> "CheatCollection":
        return cls(
            identity=identity,
            cheats=list(cheats),
        )
