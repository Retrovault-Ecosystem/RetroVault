from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Iterable


class VariantCategory(str, Enum):
    STANDARD = "standard"
    REVISION = "revision"
    TRANSLATION = "translation"
    REGION = "region"
    HACK = "hack"
    PROTOTYPE = "prototype"
    UNLICENSED = "unlicensed"
    OTHER = "other"


CATEGORY_TITLES = {
    VariantCategory.STANDARD: "Standard Edition",
    VariantCategory.REVISION: "Revisions",
    VariantCategory.TRANSLATION: "Translations & Languages",
    VariantCategory.REGION: "Regional Editions",
    VariantCategory.HACK: "Hacks & Mods",
    VariantCategory.PROTOTYPE: "Prototypes & Betas",
    VariantCategory.UNLICENSED: "Unlicensed / Aftermarket",
    VariantCategory.OTHER: "Other Variants",
}


@dataclass(frozen=True)
class GameVariant:
    """
    One playable ROM edition belonging to a canonical game family.

    `rom` remains the durable Library path. `archive_member` is empty
    for a loose ROM and contains the authoritative archive member path
    for ZIP/7z-style multi-edition content.
    """

    rom: str
    title: str
    canonical_title: str
    category: VariantCategory

    archive_member: str = ""
    region: str = ""
    language: str = ""
    revision: str = ""

    labels: tuple[str, ...] = ()
    preferred: bool = False

    @property
    def display_name(self) -> str:
        metadata = list(self.labels)

        if self.preferred and "Recommended" not in metadata:
            metadata.insert(0, "Recommended")

        if not metadata:
            return self.title

        return (
            f"{self.title} — "
            + " • ".join(metadata)
        )


@dataclass(frozen=True)
class GameFamily:
    """
    A single clean Library identity with one or more playable editions.
    """

    canonical_id: str
    canonical_title: str
    platform: str
    variants: tuple[GameVariant, ...]

    @property
    def primary_variant(self) -> GameVariant:
        if not self.variants:
            raise ValueError(
                "Game family has no playable variants."
            )

        return min(
            self.variants,
            key=VariantClassifier.preference_key,
        )

    @property
    def edition_count(self) -> int:
        return len(self.variants)

    def grouped_variants(
        self,
    ) -> dict[VariantCategory, tuple[GameVariant, ...]]:
        groups = {}

        for category in VariantCategory:
            variants = tuple(
                variant
                for variant in self.variants
                if variant.category == category
            )

            if variants:
                groups[category] = variants

        return groups


class VariantClassifier:
    """
    Convert common No-Intro / GoodTools / GoodSet-style ROM names into
    stable RetroVault edition metadata.

    This classifier deliberately does not rename files or alter durable
    ROM identity. It supplies presentation/grouping metadata only.
    """

    REGION_ALIASES = {
        "u": "USA",
        "usa": "USA",
        "us": "USA",
        "e": "Europe",
        "europe": "Europe",
        "eu": "Europe",
        "j": "Japan",
        "japan": "Japan",
        "jp": "Japan",
        "w": "World",
        "world": "World",
        "australia": "Australia",
        "australian": "Australia",
        "korea": "Korea",
        "korean": "Korea",
        "china": "China",
        "ch": "China",
        "brazil": "Brazil",
        "canada": "Canada",
        "france": "France",
        "germany": "Germany",
        "spain": "Spain",
        "italy": "Italy",
    }

    LANGUAGE_ALIASES = {
        "en": "English",
        "eng": "English",
        "english": "English",
        "ja": "Japanese",
        "jap": "Japanese",
        "jpn": "Japanese",
        "japanese": "Japanese",
        "fr": "French",
        "fre": "French",
        "fra": "French",
        "french": "French",
        "de": "German",
        "ger": "German",
        "deu": "German",
        "german": "German",
        "es": "Spanish",
        "spa": "Spanish",
        "spanish": "Spanish",
        "it": "Italian",
        "ita": "Italian",
        "italian": "Italian",
        "pt": "Portuguese",
        "por": "Portuguese",
        "portuguese": "Portuguese",
        "bra": "Brazilian Portuguese",
        "ru": "Russian",
        "rus": "Russian",
        "russian": "Russian",
        "pl": "Polish",
        "pol": "Polish",
        "polish": "Polish",
        "zh": "Chinese",
        "chi": "Chinese",
        "chinese": "Chinese",
        "ko": "Korean",
        "kor": "Korean",
        "korean": "Korean",
    }

    NON_TITLE_PAREN_TAG = re.compile(
        r"\((?:"
        r"USA|U|US|Europe|E|EU|Japan|J|JP|World|W|"
        r"Australia|China|Korea|Brazil|Canada|France|"
        r"Germany|Spain|Italy|"
        r"Rev(?:ision)?[^)]*|"
        r"Beta[^)]*|Proto(?:type)?[^)]*|"
        r"Demo[^)]*|Sample[^)]*|"
        r"Unl|Unlicensed|Hack[^)]*|"
        r"En|Eng|English|Ja|Jap|Jpn|Japanese|"
        r"Fr|Fre|Fra|French|De|Ger|Deu|German|"
        r"Es|Spa|Spanish|It|Ita|Italian|"
        r"Pt|Por|Portuguese|Ru|Rus|Russian|"
        r"Pl|Pol|Polish|Zh|Chi|Chinese|Ko|Kor|Korean"
        r")\)",
        re.IGNORECASE,
    )

    GOODTOOLS_TAG = re.compile(
        r"\[[^\]]+\]"
    )

    MULTISPACE = re.compile(
        r"\s+"
    )

    @classmethod
    def classify(
        cls,
        path_or_member,
        *,
        rom=None,
        archive_member="",
        preferred=False,
    ) -> GameVariant:
        path = str(path_or_member)
        filename = Path(path).name
        stem = Path(filename).stem

        region = cls._region(stem)
        language = cls._language(stem)
        revision = cls._revision(stem)

        hack = cls._is_hack(stem)
        translation = cls._translation(stem)
        prototype = cls._is_prototype(stem)
        unlicensed = cls._is_unlicensed(stem)

        canonical_title = cls.canonical_title(stem)

        labels = []

        if region:
            labels.append(region)

        if language:
            labels.append(language)

        if revision:
            labels.append(
                f"Revision {revision}"
            )

        if translation:
            translation_label = (
                f"Translation: {translation}"
                if translation
                else "Translation"
            )

            if translation_label not in labels:
                labels.append(
                    translation_label
                )

        if hack:
            labels.append("Hack / Mod")

        if prototype:
            labels.append(
                cls._prototype_label(stem)
            )

        if unlicensed:
            labels.append(
                "Unlicensed / Aftermarket"
            )

        category = cls._category(
            region=region,
            language=language,
            revision=revision,
            hack=hack,
            translation=translation,
            prototype=prototype,
            unlicensed=unlicensed,
        )

        return GameVariant(
            rom=str(
                rom
                if rom is not None
                else path
            ),
            archive_member=str(
                archive_member
            ),
            title=stem,
            canonical_title=canonical_title,
            category=category,
            region=region,
            language=language,
            revision=revision,
            labels=tuple(
                dict.fromkeys(labels)
            ),
            preferred=bool(preferred),
        )

    @classmethod
    def canonical_title(
        cls,
        value,
    ) -> str:
        # canonical_title() may receive either a filename or an already
        # extensionless ROM title. Path.stem cannot safely distinguish
        # title punctuation from a suffix:
        #
        #   "Super Mario Bros. (USA)"
        #
        # would be interpreted as though ". (USA)" were an extension.
        #
        # Strip only a known ROM/archive extension here. Legitimate
        # punctuation in the game title therefore remains authoritative.
        stem = str(value).strip()

        known_suffixes = {
            ".nes",
            ".fds",
            ".sfc",
            ".smc",
            ".fig",
            ".gb",
            ".gbc",
            ".gba",
            ".gen",
            ".md",
            ".smd",
            ".sms",
            ".gg",
            ".32x",
            ".pce",
            ".sgx",
            ".a26",
            ".a52",
            ".a78",
            ".lnx",
            ".ngp",
            ".ngc",
            ".ws",
            ".wsc",
            ".z64",
            ".n64",
            ".v64",
            ".cue",
            ".chd",
            ".iso",
            ".bin",
            ".zip",
            ".7z",
        }

        suffix = Path(stem).suffix.casefold()

        if suffix in known_suffixes:
            stem = stem[:-len(suffix)]

        stem = cls.GOODTOOLS_TAG.sub(
            "",
            stem,
        )

        previous = None

        while previous != stem:
            previous = stem
            stem = cls.NON_TITLE_PAREN_TAG.sub(
                "",
                stem,
            )

        stem = cls.MULTISPACE.sub(
            " ",
            stem,
        ).strip(" -_")

        # Preserve legitimate title punctuation. Path.stem treats the
        # final period in titles such as "Super Mario Bros." as a file
        # suffix when canonical_title() receives an already-extensionless
        # stem. At this stage `stem` is already the caller's title text,
        # so return it directly rather than applying Path.stem again.
        return stem or str(value).strip()

    @classmethod
    def family_key(
        cls,
        variant: GameVariant,
        platform="",
    ) -> str:
        title = re.sub(
            r"[^a-z0-9]+",
            " ",
            variant.canonical_title.casefold(),
        ).strip()

        system = re.sub(
            r"[^a-z0-9]+",
            " ",
            str(platform).casefold(),
        ).strip()

        return f"{system}::{title}"

    @classmethod
    def preference_key(
        cls,
        variant: GameVariant,
    ):
        """
        Lower values are preferred.

        User-requested policy:
          1. USA + English standard retail
          2. USA standard retail
          3. Native English / World standard retail
          4. Other standard retail
          5. revisions
          6. regional alternatives
          7. translations
          8. hacks
          9. prototypes/betas
         10. unlicensed/aftermarket
         11. other variants
        """

        category_rank = {
            VariantCategory.STANDARD: 0,
            VariantCategory.REVISION: 4,
            VariantCategory.REGION: 5,
            VariantCategory.TRANSLATION: 6,
            VariantCategory.HACK: 7,
            VariantCategory.PROTOTYPE: 8,
            VariantCategory.UNLICENSED: 9,
            VariantCategory.OTHER: 10,
        }[
            variant.category
        ]

        if (
            variant.category
            == VariantCategory.STANDARD
        ):
            if (
                variant.region == "USA"
                and (
                    not variant.language
                    or variant.language == "English"
                )
            ):
                category_rank = 0
            elif variant.region == "USA":
                category_rank = 1
            elif (
                variant.language == "English"
                or variant.region == "World"
            ):
                category_rank = 2
            else:
                category_rank = 3

        return (
            0 if variant.preferred else 1,
            category_rank,
            variant.title.casefold(),
            variant.rom.casefold(),
            variant.archive_member.casefold(),
        )

    @classmethod
    def _category(
        cls,
        *,
        region,
        language,
        revision,
        hack,
        translation,
        prototype,
        unlicensed,
    ):
        if hack:
            return VariantCategory.HACK

        if translation:
            return VariantCategory.TRANSLATION

        if prototype:
            return VariantCategory.PROTOTYPE

        if unlicensed:
            return VariantCategory.UNLICENSED

        if revision:
            return VariantCategory.REVISION

        non_english = (
            language
            and language != "English"
        )

        non_preferred_region = (
            region
            and region not in {
                "USA",
                "World",
            }
        )

        if non_english:
            return VariantCategory.TRANSLATION

        if non_preferred_region:
            return VariantCategory.REGION

        return VariantCategory.STANDARD

    @classmethod
    def _region(
        cls,
        stem,
    ) -> str:
        for value in re.findall(
            r"\(([^()]*)\)",
            stem,
        ):
            for token in re.split(
                r"[,/]",
                value,
            ):
                normalized = (
                    token.strip()
                    .casefold()
                )

                region = (
                    cls.REGION_ALIASES.get(
                        normalized
                    )
                )

                if region:
                    return region

        return ""

    @classmethod
    def _language(
        cls,
        stem,
    ) -> str:
        translation = cls._translation(
            stem
        )

        if translation:
            return translation

        for value in re.findall(
            r"\(([^()]*)\)",
            stem,
        ):
            for token in re.split(
                r"[,/+]",
                value,
            ):
                normalized = re.sub(
                    r"[^a-z]",
                    "",
                    token.casefold(),
                )

                language = (
                    cls.LANGUAGE_ALIASES.get(
                        normalized
                    )
                )

                if language:
                    return language

        return ""

    @classmethod
    def _translation(
        cls,
        stem,
    ) -> str:
        match = re.search(
            r"\[t\+([^\]]+)\]",
            stem,
            re.IGNORECASE,
        )

        if not match:
            match = re.search(
                r"\((?:translation|translated)"
                r"(?:[ ,:_-]+([^)]*))?\)",
                stem,
                re.IGNORECASE,
            )

        if not match:
            return ""

        value = (
            match.group(1)
            if match.lastindex
            else ""
        )

        value = str(value or "").strip()

        normalized = re.sub(
            r"[^a-z]",
            "",
            value.casefold(),
        )

        for code, label in (
            cls.LANGUAGE_ALIASES.items()
        ):
            if normalized.startswith(code):
                return label

        return value

    @staticmethod
    def _revision(
        stem,
    ) -> str:
        match = re.search(
            r"\((?:rev(?:ision)?)"
            r"[ ._-]*([^)]+)\)",
            stem,
            re.IGNORECASE,
        )

        if not match:
            return ""

        return match.group(1).strip()

    @staticmethod
    def _is_hack(
        stem,
    ) -> bool:
        return bool(
            re.search(
                r"\[h[^\]]*\]"
                r"|\((?:hack|mod)[^)]*\)",
                stem,
                re.IGNORECASE,
            )
        )

    @staticmethod
    def _is_prototype(
        stem,
    ) -> bool:
        return bool(
            re.search(
                r"\((?:proto|prototype|beta|demo|sample)"
                r"[^)]*\)",
                stem,
                re.IGNORECASE,
            )
        )

    @staticmethod
    def _prototype_label(
        stem,
    ) -> str:
        if re.search(
            r"\((?:proto|prototype)[^)]*\)",
            stem,
            re.IGNORECASE,
        ):
            return "Prototype"

        if re.search(
            r"\(beta[^)]*\)",
            stem,
            re.IGNORECASE,
        ):
            return "Beta"

        if re.search(
            r"\(demo[^)]*\)",
            stem,
            re.IGNORECASE,
        ):
            return "Demo"

        if re.search(
            r"\(sample[^)]*\)",
            stem,
            re.IGNORECASE,
        ):
            return "Sample"

        return "Prototype / Beta"

    @staticmethod
    def _is_unlicensed(
        stem,
    ) -> bool:
        return bool(
            re.search(
                r"\[p\d*[^\]]*\]"
                r"|\((?:unl|unlicensed|aftermarket)"
                r"[^)]*\)",
                stem,
                re.IGNORECASE,
            )
        )


class GameFamilyResolver:
    """
    Group local ROM editions beneath one clean Library identity.

    RVDB stable game IDs take precedence when available. Filename
    canonicalization is the safe fallback for local/unidentified ROMs.
    """

    @classmethod
    def resolve(
        cls,
        games: Iterable,
    ) -> tuple[GameFamily, ...]:
        buckets = {}

        for game in games:
            variants = cls.variants_for_game(
                game
            )

            for variant in variants:
                rvdb_game_id = str(
                    getattr(
                        game,
                        "rvdb_game_id",
                        "",
                    )
                    or ""
                ).strip()

                platform = str(
                    getattr(
                        game,
                        "platform",
                        "",
                    )
                    or ""
                )

                if rvdb_game_id:
                    key = (
                        "rvdb::"
                        + rvdb_game_id
                    )
                else:
                    key = (
                        VariantClassifier
                        .family_key(
                            variant,
                            platform,
                        )
                    )

                bucket = buckets.setdefault(
                    key,
                    {
                        "canonical_id": (
                            rvdb_game_id
                            or key
                        ),
                        "canonical_title": (
                            variant
                            .canonical_title
                        ),
                        "platform": platform,
                        "variants": [],
                    },
                )

                bucket[
                    "variants"
                ].append(
                    variant
                )

        families = []

        for bucket in buckets.values():
            variants = tuple(
                sorted(
                    bucket["variants"],
                    key=(
                        VariantClassifier
                        .preference_key
                    ),
                )
            )

            canonical_title = (
                variants[0].canonical_title
                if variants
                else bucket[
                    "canonical_title"
                ]
            )

            families.append(
                GameFamily(
                    canonical_id=bucket[
                        "canonical_id"
                    ],
                    canonical_title=(
                        canonical_title
                    ),
                    platform=bucket[
                        "platform"
                    ],
                    variants=variants,
                )
            )

        return tuple(
            sorted(
                families,
                key=lambda family: (
                    family.platform.casefold(),
                    family.canonical_title.casefold(),
                    family.canonical_id,
                ),
            )
        )

    @classmethod
    def variants_for_game(
        cls,
        game,
    ) -> tuple[GameVariant, ...]:
        """
        Foundation behavior for loose ROMs.

        Archive expansion is intentionally delegated through a supplied
        `archive_members` attribute when present so the model remains
        independent of ArchiveRuntime and can later be populated by the
        scanner/service boundary.
        """

        rom = str(
            getattr(
                game,
                "rom",
                "",
            )
            or ""
        )

        members = tuple(
            getattr(
                game,
                "archive_members",
                (),
            )
            or ()
        )

        preferred_member = str(
            getattr(
                game,
                "preferred_archive_member",
                "",
            )
            or ""
        )

        if members:
            return tuple(
                VariantClassifier.classify(
                    member,
                    rom=rom,
                    archive_member=member,
                    preferred=(
                        member
                        == preferred_member
                    ),
                )
                for member in members
            )

        source_name = (
            Path(rom).name
            if rom
            else str(
                getattr(
                    game,
                    "name",
                    "",
                )
            )
        )

        return (
            VariantClassifier.classify(
                source_name,
                rom=rom,
            ),
        )
