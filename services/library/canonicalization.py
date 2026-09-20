from dataclasses import replace
from pathlib import Path

from services.library.game_variants import (
    CATEGORY_TITLES,
    GameFamilyResolver,
    VariantClassifier,
)


class LibraryCanonicalizer:
    """
    Convert scanned/imported Game objects into one visible canonical
    Library entry per game family while preserving every discovered
    edition as launchable variant metadata.

    Canonicalization is deliberately performed after scanning so the
    scanner remains responsible for exact physical ROM discovery and
    RVDB enrichment while this service owns presentation identity.
    """

    def __init__(
        self,
        classifier=None,
        family_resolver=None,
    ):
        self.classifier = (
            classifier
            if classifier is not None
            else VariantClassifier()
        )

        self.family_resolver = (
            family_resolver
            if family_resolver is not None
            else GameFamilyResolver()
        )

    @staticmethod
    def _source_name(game):
        rom = str(
            getattr(
                game,
                "rom",
                "",
            )
            or ""
        )

        if rom:
            return Path(rom).name

        return str(
            getattr(
                game,
                "name",
                "",
            )
            or ""
        )

    def _classify(self, game):
        return self.classifier.classify(
            self._source_name(game)
        )

    @staticmethod
    def _family_key(
        game,
        variant,
    ):
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
                "rvdb_platform_id",
                "",
            )
            or getattr(
                game,
                "platform",
                "",
            )
            or ""
        ).strip().casefold()

        if rvdb_game_id:
            return (
                "rvdb",
                platform,
                rvdb_game_id.casefold(),
            )

        canonical = str(
            getattr(
                variant,
                "canonical_title",
                "",
            )
            or getattr(
                game,
                "name",
                "",
            )
            or ""
        ).strip().casefold()

        return (
            "title",
            platform,
            canonical,
        )

    @staticmethod
    def _variant_value(
        variant,
        name,
    ):
        value = getattr(
            variant,
            name,
            "",
        )

        if value is None:
            return ""

        if hasattr(value, "value"):
            return str(value.value)

        return str(value)

    def _decorate_game(
        self,
        game,
        variant,
        *,
        family_key,
        primary,
    ):
        game.canonical_title = str(
            getattr(
                variant,
                "canonical_title",
                "",
            )
            or getattr(
                game,
                "name",
                "",
            )
            or ""
        )

        game.family_key = "|".join(
            str(part)
            for part in family_key
        )

        category = getattr(
            variant,
            "category",
            "",
        )

        game.variant_category = (
            CATEGORY_TITLES.get(
                category,
                self._variant_value(
                    variant,
                    "category",
                ),
            )
        )

        game.variant_label = str(
            getattr(
                variant,
                "display_name",
                "",
            )
            or getattr(
                game,
                "name",
                "",
            )
            or ""
        )

        game.variant_region = self._variant_value(
            variant,
            "region",
        )

        game.variant_language = self._variant_value(
            variant,
            "language",
        )

        game.variant_revision = self._variant_value(
            variant,
            "revision",
        )

        game.is_primary_variant = bool(
            primary
        )

        return game

    @staticmethod
    def _preference_key(
        game,
        variant,
    ):
        """
        Prefer the normal USA/English release, then other standard
        releases, then revisions/languages/regions/special variants.

        The A.6 classifier owns category semantics. This ranking only
        chooses the visible representative within a family.
        """

        category = str(
            getattr(
                getattr(
                    variant,
                    "category",
                    "",
                ),
                "value",
                getattr(
                    variant,
                    "category",
                    "",
                ),
            )
        ).casefold()

        region = str(
            getattr(
                variant,
                "region",
                "",
            )
            or ""
        ).casefold()

        language = str(
            getattr(
                variant,
                "language",
                "",
            )
            or ""
        ).casefold()

        revision = str(
            getattr(
                variant,
                "revision",
                "",
            )
            or ""
        ).casefold()

        category_rank = {
            "standard": 0,
            "standard edition": 0,
            "revision": 1,
            "revisions": 1,
            "translation": 2,
            "translations & languages": 2,
            "regional": 3,
            "regional editions": 3,
            "hack": 4,
            "hacks & mods": 4,
            "prototype": 5,
            "prototypes & betas": 5,
            "unlicensed": 6,
            "unlicensed / aftermarket": 6,
            "other": 7,
            "other variants": 7,
        }.get(
            category,
            8,
        )

        usa_rank = 0 if (
            "usa" in region
            or region in {
                "us",
                "u",
                "north america",
            }
        ) else 1

        english_rank = 0 if (
            not language
            or "english" in language
            or language in {
                "en",
                "eng",
            }
        ) else 1

        revision_rank = (
            0
            if not revision
            else 1
        )

        return (
            category_rank,
            usa_rank,
            english_rank,
            revision_rank,
            str(
                getattr(
                    game,
                    "name",
                    "",
                )
            ).casefold(),
            str(
                getattr(
                    game,
                    "rom",
                    "",
                )
            ).casefold(),
        )

    def canonicalize(
        self,
        games,
    ):
        groups = {}

        for game in games:
            variant = self._classify(
                game
            )

            key = self._family_key(
                game,
                variant,
            )

            groups.setdefault(
                key,
                [],
            ).append(
                (
                    game,
                    variant,
                )
            )

        canonical_games = []

        for key, entries in groups.items():
            ordered = sorted(
                entries,
                key=lambda item: (
                    self._preference_key(
                        item[0],
                        item[1],
                    )
                ),
            )

            primary_game, primary_variant = (
                ordered[0]
            )

            variants = []

            for index, (
                game,
                variant,
            ) in enumerate(
                ordered
            ):
                self._decorate_game(
                    game,
                    variant,
                    family_key=key,
                    primary=(
                        index == 0
                    ),
                )

                variants.append(
                    {
                        "name": str(
                            getattr(
                                game,
                                "name",
                                "",
                            )
                            or ""
                        ),
                        "rom": str(
                            getattr(
                                game,
                                "rom",
                                "",
                            )
                            or ""
                        ),
                        "source": str(
                            getattr(
                                game,
                                "source",
                                "",
                            )
                            or ""
                        ),
                        "category": str(
                            getattr(
                                game,
                                "variant_category",
                                "",
                            )
                            or ""
                        ),
                        "label": str(
                            getattr(
                                game,
                                "variant_label",
                                "",
                            )
                            or ""
                        ),
                        "region": str(
                            getattr(
                                game,
                                "variant_region",
                                "",
                            )
                            or ""
                        ),
                        "language": str(
                            getattr(
                                game,
                                "variant_language",
                                "",
                            )
                            or ""
                        ),
                        "revision": str(
                            getattr(
                                game,
                                "variant_revision",
                                "",
                            )
                            or ""
                        ),
                        "preferred": (
                            index == 0
                        ),
                    }
                )

            canonical_title = str(
                getattr(
                    primary_variant,
                    "canonical_title",
                    "",
                )
                or getattr(
                    primary_game,
                    "name",
                    "",
                )
                or ""
            )

            singleton_source_name = ""

            if len(entries) == 1:
                singleton_source_name = str(
                    getattr(
                        primary_game,
                        "name",
                        "",
                    )
                    or ""
                )

            primary_game.name = (
                canonical_title
            )

            if singleton_source_name:
                primary_game.name = (
                    singleton_source_name
                )

            primary_game.variants = (
                variants
            )

            canonical_games.append(
                primary_game
            )

        canonical_games.sort(
            key=lambda game: (
                str(
                    getattr(
                        game,
                        "platform",
                        "",
                    )
                ).casefold(),
                str(
                    getattr(
                        game,
                        "name",
                        "",
                    )
                ).casefold(),
                str(
                    getattr(
                        game,
                        "rom",
                        "",
                    )
                ).casefold(),
            )
        )

        return canonical_games
