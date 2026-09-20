from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import re

from .models import (
    CheatCategory,
    CheatCode,
    CheatCodeType,
)


_INDEX_RE = re.compile(
    r"^cheat(?P<index>\d+)_(?P<field>[A-Za-z0-9_]+)$"
)


class RetroArchCheatParser:
    """
    Read/write the portable subset of RetroArch .cht files used by
    RetroVault.

    Unknown fields are ignored rather than treated as fatal so that
    upstream cheat databases can evolve independently.
    """

    @staticmethod
    def _unquote(value: str) -> str:
        value = value.strip()

        if (
            len(value) >= 2
            and value[0] == '"'
            and value[-1] == '"'
        ):
            value = value[1:-1]

        return value.replace(
            r"\"",
            '"',
        )

    @classmethod
    def parse_text(
        cls,
        text: str,
        source: str = "",
    ) -> list[CheatCode]:
        records = {}

        for raw_line in text.splitlines():
            line = raw_line.strip()

            if (
                not line
                or line.startswith("#")
                or "=" not in line
            ):
                continue

            key, value = line.split(
                "=",
                1,
            )

            key = key.strip()
            value = cls._unquote(
                value
            )

            match = _INDEX_RE.match(
                key
            )

            if match is None:
                continue

            index = int(
                match.group(
                    "index"
                )
            )
            field = match.group(
                "field"
            ).casefold()

            records.setdefault(
                index,
                {},
            )[field] = value

        cheats = []

        for index in sorted(records):
            record = records[index]

            code = str(
                record.get(
                    "code",
                    "",
                )
            ).strip()

            if not code:
                continue

            name = str(
                record.get(
                    "desc",
                    "",
                )
                or f"Cheat {index + 1}"
            ).strip()

            enabled = str(
                record.get(
                    "enable",
                    "false",
                )
            ).casefold() in {
                "true",
                "1",
                "yes",
                "on",
            }

            cheats.append(
                CheatCode(
                    name=name,
                    code=code,
                    code_type=(
                        CheatCodeType.RETROARCH
                    ),
                    category=(
                        cls.infer_category(
                            name
                        )
                    ),
                    source=source,
                    enabled=enabled,
                )
            )

        return cheats

    @classmethod
    def parse_file(
        cls,
        path,
    ) -> list[CheatCode]:
        path = Path(path)

        return cls.parse_text(
            path.read_text(
                errors="replace"
            ),
            source=str(path),
        )

    @staticmethod
    def infer_category(
        name: str,
    ) -> CheatCategory:
        text = name.casefold()

        rules = (
            (
                (
                    "invinc",
                    "invulner",
                    "god mode",
                ),
                CheatCategory.INVINCIBILITY,
            ),
            (
                (
                    "level select",
                    "stage select",
                    "level ",
                    "stage ",
                ),
                CheatCategory.LEVEL_STAGE,
            ),
            (
                (
                    "life",
                    "lives",
                    "health",
                    "energy",
                    "heart",
                    "hp",
                ),
                CheatCategory.LIVES_HEALTH,
            ),
            (
                (
                    "weapon",
                    "power-up",
                    "powerup",
                    "ammo",
                ),
                CheatCategory.WEAPONS,
            ),
            (
                (
                    "item",
                    "inventory",
                    "key",
                ),
                CheatCategory.ITEMS,
            ),
            (
                (
                    "character",
                    "player",
                ),
                CheatCategory.CHARACTER,
            ),
            (
                (
                    "timer",
                    "time",
                ),
                CheatCategory.TIME,
            ),
            (
                (
                    "score",
                    "money",
                    "coin",
                    "currency",
                ),
                CheatCategory.SCORE,
            ),
            (
                (
                    "unlock",
                    "secret",
                ),
                CheatCategory.UNLOCKABLES,
            ),
            (
                (
                    "debug",
                    "developer",
                ),
                CheatCategory.DEBUG,
            ),
        )

        for needles, category in rules:
            if any(
                needle in text
                for needle in needles
            ):
                return category

        return CheatCategory.GAMEPLAY

    @staticmethod
    def serialize(
        cheats,
    ) -> str:
        cheats = list(cheats)

        lines = [
            f"cheats = {len(cheats)}",
            "",
        ]

        for index, cheat in enumerate(
            cheats
        ):
            description = (
                cheat.name
                .replace(
                    '"',
                    r'\"',
                )
            )

            code = (
                cheat.normalized_code
                .replace(
                    '"',
                    r'\"',
                )
            )

            lines.extend(
                [
                    (
                        f'cheat{index}_desc = '
                        f'"{description}"'
                    ),
                    (
                        f'cheat{index}_code = '
                        f'"{code}"'
                    ),
                    (
                        f"cheat{index}_enable = "
                        + (
                            "true"
                            if cheat.enabled
                            else "false"
                        )
                    ),
                    "",
                ]
            )

        return "\n".join(
            lines
        ).rstrip() + "\n"

    @classmethod
    def with_enabled(
        cls,
        cheat: CheatCode,
        enabled: bool,
    ) -> CheatCode:
        return replace(
            cheat,
            enabled=enabled,
        )
