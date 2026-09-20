from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import os
import re
import tempfile

from .models import (
    CheatCategory,
    CheatCode,
    CheatCodeType,
    CheatCollection,
    CheatIdentity,
)
from .retroarch import (
    RetroArchCheatParser,
)


class CheatService:
    """
    RetroVault's game-edition-aware cheat boundary.

    Discovery is intentionally extensible. RetroArch .cht files are
    the first provider; manual/imported code support uses the same
    domain model.
    """

    FLATPAK_DATABASE_ROOT = (
        "/var/lib/flatpak/app/"
        "org.libretro.RetroArch/current/active/"
        "files/share/libretro/database/cht"
    )

    DEFAULT_ROOTS = (
        "~/.config/retroarch/cheats",
        "/opt/retropie/configs/all/retroarch/cheats",
        "/usr/share/libretro-database/cht",
        "/usr/share/retroarch/cheats",
        FLATPAK_DATABASE_ROOT,
    )

    PLATFORM_DATABASE_DIRS = {
        "nes": "Nintendo - Nintendo Entertainment System",
        "snes": "Nintendo - Super Nintendo Entertainment System",
        "n64": "Nintendo - Nintendo 64",
        "gb": "Nintendo - Game Boy",
        "gbc": "Nintendo - Game Boy Color",
        "gba": "Nintendo - Game Boy Advance",
        "genesis": "Sega - Mega Drive - Genesis",
        "megadrive": "Sega - Mega Drive - Genesis",
        "mastersystem": "Sega - Master System - Mark III",
        "gamegear": "Sega - Game Gear",
        "saturn": "Sega - Saturn",
        "psx": "Sony - PlayStation",
        "ps1": "Sony - PlayStation",
    }

    def __init__(
        self,
        roots=None,
        user_root=None,
    ):
        self.roots = tuple(
            Path(
                os.path.expanduser(
                    str(root)
                )
            )
            for root in (
                roots
                if roots is not None
                else self.DEFAULT_ROOTS
            )
        )

        if user_root is None:
            user_root = (
                Path.home()
                / ".config"
                / "retrovault"
                / "cheats"
            )

        self.user_root = Path(
            os.path.expanduser(
                str(user_root)
            )
        )

    @staticmethod
    def identity_for(
        game,
        archive_member="",
    ) -> CheatIdentity:
        rom = str(
            getattr(
                game,
                "rom",
                "",
            )
            or ""
        )

        digest = ""

        path = Path(rom)

        if (
            path.is_file()
            and not archive_member
            and path.suffix.casefold()
                not in {".zip", ".7z"}
        ):
            try:
                hasher = sha256()

                with path.open(
                    "rb"
                ) as handle:
                    for chunk in iter(
                        lambda: handle.read(
                            1024 * 1024
                        ),
                        b"",
                    ):
                        hasher.update(
                            chunk
                        )

                digest = (
                    hasher.hexdigest()
                )
            except OSError:
                digest = ""

        return CheatIdentity(
            platform=str(
                getattr(
                    game,
                    "platform",
                    "",
                )
                or ""
            ),
            canonical_title=str(
                getattr(
                    game,
                    "canonical_title",
                    "",
                )
                or getattr(
                    game,
                    "name",
                    "",
                )
                or ""
            ),
            rom_path=rom,
            archive_member=str(
                archive_member
                or ""
            ),
            variant_category=str(
                getattr(
                    game,
                    "variant_category",
                    "",
                )
                or ""
            ),
            region=str(
                getattr(
                    game,
                    "variant_region",
                    "",
                )
                or ""
            ),
            language=str(
                getattr(
                    game,
                    "variant_language",
                    "",
                )
                or ""
            ),
            revision=str(
                getattr(
                    game,
                    "variant_revision",
                    "",
                )
                or ""
            ),
            rvdb_game_id=str(
                getattr(
                    game,
                    "rvdb_game_id",
                    "",
                )
                or ""
            ),
            sha256=digest,
        )

    @staticmethod
    def _normalize_title(
        value: str,
    ) -> str:
        value = Path(
            str(value)
        ).stem

        value = re.sub(
            r"\([^)]*\)|\[[^]]*\]",
            " ",
            value,
        )

        value = re.sub(
            r"[^a-zA-Z0-9]+",
            " ",
            value,
        )

        return " ".join(
            value.casefold().split()
        )

    def _candidate_names(
        self,
        identity: CheatIdentity,
    ):
        values = [
            identity.filename,
            identity.canonical_title,
        ]

        seen = set()

        for value in values:
            normalized = (
                self._normalize_title(
                    value
                )
            )

            if (
                normalized
                and normalized not in seen
            ):
                seen.add(
                    normalized
                )
                yield normalized

    @staticmethod
    def _platform_key(
        value,
    ) -> str:
        value = str(
            value
            or ""
        ).casefold()

        value = re.sub(
            r"[^a-z0-9]+",
            "",
            value,
        )

        aliases = {
            "nintendoentertainmentsystem": "nes",
            "famicom": "nes",
            "supernintendo": "snes",
            "supernintendoentertainmentsystem": "snes",
            "superfamicom": "snes",
            "nintendo64": "n64",
            "gameboy": "gb",
            "gameboycolor": "gbc",
            "gameboyadvance": "gba",
            "segagenesis": "genesis",
            "segamegadrive": "genesis",
            "megadrive": "megadrive",
            "segamastersystem": "mastersystem",
            "mastersystem": "mastersystem",
            "segagamegear": "gamegear",
            "gamegear": "gamegear",
            "segasaturn": "saturn",
            "playstation": "psx",
            "sonyplaystation": "psx",
        }

        return aliases.get(
            value,
            value,
        )

    def _all_roots(
        self,
        identity=None,
    ):
        yield self.user_root

        platform_directory = ""

        if identity is not None:
            platform_directory = (
                self.PLATFORM_DATABASE_DIRS.get(
                    self._platform_key(
                        identity.platform
                    ),
                    "",
                )
            )

        flatpak_root = Path(
            self.FLATPAK_DATABASE_ROOT
        )

        for root in self.roots:
            root = Path(root)

            try:
                same_flatpak_root = (
                    root.resolve()
                    == flatpak_root.resolve()
                )
            except OSError:
                same_flatpak_root = (
                    str(root)
                    == str(flatpak_root)
                )

            if (
                same_flatpak_root
                and platform_directory
            ):
                yield (
                    root
                    / platform_directory
                )
                continue

            yield root

    def discover_files(
        self,
        identity: CheatIdentity,
    ) -> list[Path]:
        names = set(
            self._candidate_names(
                identity
            )
        )

        if not names:
            return []

        exact = []
        fallback = []

        for root in self._all_roots(
            identity
        ):
            if not root.is_dir():
                continue

            try:
                paths = root.rglob(
                    "*.cht"
                )

                for path in paths:
                    normalized = (
                        self._normalize_title(
                            path.name
                        )
                    )

                    if normalized in names:
                        exact.append(
                            path
                        )
                    elif any(
                        name in normalized
                        or normalized in name
                        for name in names
                        if len(name) >= 4
                    ):
                        fallback.append(
                            path
                        )
            except OSError:
                continue

        result = exact or fallback

        return sorted(
            dict.fromkeys(
                result
            ),
            key=lambda path: (
                str(path).casefold()
            ),
        )

    @staticmethod
    def _raw_tags(
        value,
    ) -> list[str]:
        value = Path(
            str(value)
        ).stem

        return [
            (
                match.group(1)
                or match.group(2)
                or ""
            ).strip().casefold()
            for match in re.finditer(
                r"\\(([^()]*)\\)|\\[([^][]*)\\]",
                value,
            )
            if (
                match.group(1)
                or match.group(2)
            )
        ]

    @classmethod
    def _compatibility_for_file(
        cls,
        identity: CheatIdentity,
        path: Path,
    ) -> tuple[bool, str]:
        physical_name = (
            identity.filename
            or identity.canonical_title
        )

        physical_tags = set(
            cls._raw_tags(
                physical_name
            )
        )

        cheat_tags = set(
            cls._raw_tags(
                path.name
            )
        )

        device_tags = {
            "game genie",
            "action replay",
            "pro action replay",
            "gameshark",
            "game shark",
            "codebreaker",
            "code breaker",
            "rumbles",
        }

        cheat_edition_tags = {
            tag
            for tag in cheat_tags
            if tag not in device_tags
        }

        physical_edition_tags = {
            tag
            for tag in physical_tags
            if tag not in device_tags
        }

        sensitive_tokens = (
            "rev",
            "revision",
            "hack",
            "translation",
            "prototype",
            "proto",
            "beta",
            "sample",
            "demo",
            "unl",
            "unlicensed",
            "aftermarket",
        )

        sensitive_physical = any(
            any(
                token in tag
                for token in sensitive_tokens
            )
            for tag in physical_edition_tags
        )

        if (
            physical_edition_tags
            and cheat_edition_tags
            and cheat_edition_tags
            == physical_edition_tags
        ):
            return (
                True,
                "Exact physical-edition match.",
            )

        if (
            physical_edition_tags
            and cheat_edition_tags
            and physical_edition_tags.issubset(
                cheat_edition_tags
            )
        ):
            return (
                True,
                "Physical edition matched; "
                "cheat-device companion accepted.",
            )

        if sensitive_physical:
            return (
                False,
                "Cheat database entry is not an exact "
                "match for this revision/hack/translation/"
                "prototype edition.",
            )

        if (
            not physical_edition_tags
            and not cheat_edition_tags
        ):
            return (
                True,
                "Base-title match.",
            )

        return (
            False,
            "Region/revision compatibility is uncertain "
            "for this physical edition.",
        )

    def discover(
        self,
        game,
        archive_member="",
    ) -> CheatCollection:
        identity = self.identity_for(
            game,
            archive_member,
        )

        cheats = []
        seen = set()

        for path in self.discover_files(
            identity
        ):
            try:
                parsed = (
                    RetroArchCheatParser
                    .parse_file(
                        path
                    )
                )
            except OSError:
                continue

            compatible, compatibility_note = (
                self._compatibility_for_file(
                    identity,
                    path,
                )
            )

            for cheat in parsed:
                cheat = replace(
                    cheat,
                    compatible=compatible,
                    compatibility_note=(
                        compatibility_note
                    ),
                    source=(
                        cheat.source
                        or str(path)
                    ),
                )

                key = (
                    cheat.name.casefold(),
                    cheat.normalized_code,
                    cheat.code_type.value,
                )

                if key in seen:
                    continue

                seen.add(
                    key
                )
                cheats.append(
                    cheat
                )

        return CheatCollection(
            identity=identity,
            cheats=cheats,
        )

    @staticmethod
    def manual_cheat(
        name,
        code,
        code_type=CheatCodeType.CUSTOM,
        category=CheatCategory.CUSTOM,
    ) -> CheatCode:
        name = str(
            name
        ).strip()
        code = str(
            code
        ).strip()

        if not name:
            raise ValueError(
                "Cheat name is required."
            )

        if not code:
            raise ValueError(
                "Cheat code is required."
            )

        if not isinstance(
            code_type,
            CheatCodeType,
        ):
            code_type = CheatCodeType(
                str(code_type)
            )

        if not isinstance(
            category,
            CheatCategory,
        ):
            category = CheatCategory(
                str(category)
            )

        return CheatCode(
            name=name,
            code=code,
            code_type=code_type,
            category=category,
            source="RetroVault Custom",
        )

    @staticmethod
    def enable_all_compatible(
        cheats,
    ):
        return [
            replace(
                cheat,
                enabled=bool(
                    cheat.compatible
                ),
            )
            for cheat in cheats
        ]

    @staticmethod
    def disable_all(
        cheats,
    ):
        return [
            replace(
                cheat,
                enabled=False,
            )
            for cheat in cheats
        ]

    def import_file(
        self,
        path,
        identity: CheatIdentity,
    ) -> Path:
        source = Path(path)

        if (
            not source.is_file()
            or source.suffix.casefold()
                != ".cht"
        ):
            raise ValueError(
                "RetroVault cheat imports must be "
                "RetroArch .cht files."
            )

        # Parse before persistence so malformed/empty imports
        # cannot silently become part of the user's collection.
        parsed = (
            RetroArchCheatParser
            .parse_file(
                source
            )
        )

        if not parsed:
            raise ValueError(
                "The selected cheat file contains "
                "no usable cheat codes."
            )

        platform = (
            self._normalize_title(
                identity.platform
            )
            or "unknown-system"
        )

        title = (
            self._normalize_title(
                identity.filename
            )
            or self._normalize_title(
                identity.canonical_title
            )
            or "unknown-game"
        )

        destination_dir = (
            self.user_root
            / platform
        )

        destination_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        destination = (
            destination_dir
            / f"{title}.cht"
        )

        destination.write_text(
            source.read_text(
                errors="replace"
            )
        )

        return destination

    @staticmethod
    def runtime_file(
        cheats,
    ):
        enabled = [
            cheat
            for cheat in cheats
            if cheat.enabled
            and cheat.compatible
        ]

        if not enabled:
            return ""

        handle = tempfile.NamedTemporaryFile(
            mode="w",
            prefix="retrovault-cheats-",
            suffix=".cht",
            delete=False,
        )

        try:
            handle.write(
                RetroArchCheatParser
                .serialize(
                    enabled
                )
            )
        finally:
            handle.close()

        return handle.name
