from dataclasses import dataclass

from services.library.game_variants import (
    CATEGORY_TITLES,
    GameFamilyResolver,
    VariantCategory,
    VariantClassifier,
)


@dataclass
class StubGame:
    name: str
    platform: str
    rom: str
    rvdb_game_id: str = ""
    archive_members: tuple[str, ...] = ()
    preferred_archive_member: str = ""


def classify(name):
    return VariantClassifier.classify(
        name
    )


def test_standard_usa_rom_is_standard():
    variant = classify(
        "Super Mario Bros. (USA).nes"
    )

    assert (
        variant.canonical_title
        == "Super Mario Bros."
    )
    assert variant.region == "USA"
    assert (
        variant.category
        == VariantCategory.STANDARD
    )


def test_non_usa_region_is_regional_edition():
    variant = classify(
        "Super Mario Bros. (Japan).nes"
    )

    assert variant.region == "Japan"
    assert (
        variant.category
        == VariantCategory.REGION
    )


def test_non_english_language_is_not_standard():
    variant = classify(
        "Example Game (Spanish).sfc"
    )

    assert variant.language == "Spanish"
    assert (
        variant.category
        == VariantCategory.TRANSLATION
    )


def test_goodtools_translation_is_grouped():
    variant = classify(
        "Example Game (J) [T+Eng].nes"
    )

    assert variant.language == "English"
    assert (
        variant.category
        == VariantCategory.TRANSLATION
    )
    assert (
        "Translation: English"
        in variant.labels
    )


def test_revision_is_grouped():
    variant = classify(
        "Example Game (USA) (Rev 1).nes"
    )

    assert variant.revision == "1"
    assert (
        variant.category
        == VariantCategory.REVISION
    )


def test_hack_is_grouped():
    variant = classify(
        "Example Game (USA) [h1].nes"
    )

    assert (
        variant.category
        == VariantCategory.HACK
    )
    assert "Hack / Mod" in variant.labels


def test_prototype_and_beta_are_grouped():
    prototype = classify(
        "Example Game (USA) (Proto).nes"
    )
    beta = classify(
        "Example Game (USA) (Beta).nes"
    )

    assert (
        prototype.category
        == VariantCategory.PROTOTYPE
    )
    assert (
        beta.category
        == VariantCategory.PROTOTYPE
    )


def test_unlicensed_is_grouped():
    variant = classify(
        "Example Game (USA) (Unl).nes"
    )

    assert (
        variant.category
        == VariantCategory.UNLICENSED
    )


def test_category_titles_match_presentation_contract():
    assert (
        CATEGORY_TITLES[
            VariantCategory.STANDARD
        ]
        == "Standard Edition"
    )
    assert (
        CATEGORY_TITLES[
            VariantCategory.REVISION
        ]
        == "Revisions"
    )
    assert (
        CATEGORY_TITLES[
            VariantCategory.TRANSLATION
        ]
        == "Translations & Languages"
    )
    assert (
        CATEGORY_TITLES[
            VariantCategory.REGION
        ]
        == "Regional Editions"
    )
    assert (
        CATEGORY_TITLES[
            VariantCategory.HACK
        ]
        == "Hacks & Mods"
    )
    assert (
        CATEGORY_TITLES[
            VariantCategory.PROTOTYPE
        ]
        == "Prototypes & Betas"
    )
    assert (
        CATEGORY_TITLES[
            VariantCategory.UNLICENSED
        ]
        == "Unlicensed / Aftermarket"
    )


def test_same_title_editions_form_one_family():
    games = [
        StubGame(
            name="Example Game (USA)",
            platform="NES",
            rom="/roms/Example Game (USA).nes",
        ),
        StubGame(
            name="Example Game (Japan)",
            platform="NES",
            rom="/roms/Example Game (Japan).nes",
        ),
        StubGame(
            name="Example Game (USA) (Rev 1)",
            platform="NES",
            rom=(
                "/roms/"
                "Example Game (USA) (Rev 1).nes"
            ),
        ),
        StubGame(
            name="Example Game (USA) [h1]",
            platform="NES",
            rom=(
                "/roms/"
                "Example Game (USA) [h1].nes"
            ),
        ),
    ]

    families = (
        GameFamilyResolver.resolve(
            games
        )
    )

    assert len(families) == 1

    family = families[0]

    assert (
        family.canonical_title
        == "Example Game"
    )
    assert family.edition_count == 4
    assert (
        family.primary_variant.region
        == "USA"
    )
    assert (
        family.primary_variant.category
        == VariantCategory.STANDARD
    )


def test_rvdb_identity_groups_filename_variations():
    games = [
        StubGame(
            name="Canonical Name",
            platform="SNES",
            rom=(
                "/roms/"
                "Canonical Name (USA).sfc"
            ),
            rvdb_game_id="game:test",
        ),
        StubGame(
            name="Localized Name",
            platform="SNES",
            rom=(
                "/roms/"
                "Localized Name (Japan).sfc"
            ),
            rvdb_game_id="game:test",
        ),
    ]

    families = (
        GameFamilyResolver.resolve(
            games
        )
    )

    assert len(families) == 1
    assert (
        families[0].canonical_id
        == "game:test"
    )
    assert (
        families[0].edition_count
        == 2
    )


def test_archive_members_and_loose_roms_share_variant_model():
    game = StubGame(
        name="Example Game",
        platform="NES",
        rom="/roms/example.7z",
        archive_members=(
            "Example Game (USA).nes",
            "Example Game (Japan).nes",
            "Example Game (USA) [h1].nes",
        ),
        preferred_archive_member=(
            "Example Game (USA).nes"
        ),
    )

    variants = (
        GameFamilyResolver
        .variants_for_game(
            game
        )
    )

    assert len(variants) == 3

    assert all(
        variant.rom
        == "/roms/example.7z"
        for variant in variants
    )

    assert all(
        variant.archive_member
        for variant in variants
    )

    preferred = [
        variant
        for variant in variants
        if variant.preferred
    ]

    assert len(preferred) == 1
    assert (
        preferred[0].region
        == "USA"
    )


def test_empty_variant_groups_are_omitted():
    games = [
        StubGame(
            name="Example Game (USA)",
            platform="NES",
            rom="/roms/Example Game (USA).nes",
        ),
        StubGame(
            name="Example Game (Japan)",
            platform="NES",
            rom="/roms/Example Game (Japan).nes",
        ),
    ]

    family = (
        GameFamilyResolver.resolve(
            games
        )[0]
    )

    groups = family.grouped_variants()

    assert VariantCategory.STANDARD in groups
    assert VariantCategory.REGION in groups

    assert (
        VariantCategory.HACK
        not in groups
    )
    assert (
        VariantCategory.PROTOTYPE
        not in groups
    )


def test_preference_policy_prefers_usa_standard():
    variants = [
        classify(
            "Example Game (Japan).nes"
        ),
        classify(
            "Example Game (USA) (Rev 1).nes"
        ),
        classify(
            "Example Game (USA).nes"
        ),
        classify(
            "Example Game (USA) [h1].nes"
        ),
    ]

    selected = min(
        variants,
        key=(
            VariantClassifier
            .preference_key
        ),
    )

    assert selected.region == "USA"
    assert (
        selected.category
        == VariantCategory.STANDARD
    )
    assert not selected.revision


def test_family_key_is_platform_scoped():
    variant = classify(
        "Example Game (USA).nes"
    )

    nes = (
        VariantClassifier.family_key(
            variant,
            "NES",
        )
    )

    snes = (
        VariantClassifier.family_key(
            variant,
            "SNES",
        )
    )

    assert nes != snes


def test_classifier_never_changes_authoritative_rom_path():
    rom = (
        "/games/NES/"
        "Example Game (USA) (Rev 1).nes"
    )

    variant = (
        VariantClassifier.classify(
            rom
        )
    )

    assert variant.rom == rom


def test_canonical_title_preserves_terminal_title_punctuation():
    samples = {
        "Super Mario Bros. (USA).nes":
            "Super Mario Bros.",
        "Dr. Mario (USA).nes":
            "Dr. Mario",
        "Mr. Gimmick (USA).nes":
            "Mr. Gimmick",
    }

    for filename, expected in samples.items():
        variant = classify(filename)

        assert (
            variant.canonical_title
            == expected
        )


def test_canonical_title_preserves_period_before_variant_tags():
    assert (
        VariantClassifier.canonical_title(
            "Super Mario Bros. (USA)"
        )
        == "Super Mario Bros."
    )
