from services.retroarch.archive_variant import (
    ArchiveVariantFormatter,
)


def describe(
    member,
    preferred=False,
):
    return ArchiveVariantFormatter.describe(
        member,
        preferred=preferred,
    )


def test_verified_usa_default_is_friendly():
    variant = describe(
        "Adventure Island (U) [!].nes",
        preferred=True,
    )

    assert variant.member == (
        "Adventure Island (U) [!].nes"
    )
    assert variant.labels == (
        "Recommended",
        "USA",
        "Verified",
    )


def test_europe_verified_region_is_exposed():
    variant = describe(
        "Adventure Island (E) [!].nes"
    )

    assert variant.labels == (
        "Europe",
        "Verified",
    )


def test_bad_dump_is_exposed():
    variant = describe(
        "Adventure Island (U) [b4].nes"
    )

    assert "USA" in variant.labels
    assert "Bad Dump" in variant.labels


def test_overdump_is_exposed():
    variant = describe(
        "Adventure Island (U) [o3].nes"
    )

    assert "Overdump" in variant.labels


def test_translation_is_exposed():
    variant = describe(
        "Adventure Island (U) "
        "[T+Spa1.0_PaladinKnights].nes"
    )

    assert (
        "Translation: Spanish"
        in variant.labels
    )


def test_trainer_is_exposed():
    variant = describe(
        "Adventure Island (U) [t5].nes"
    )

    assert "Trainer 5" in variant.labels


def test_hack_is_exposed():
    variant = describe(
        "Adventure Island by ssw (Hack).nes"
    )

    assert "Hack" in variant.labels


def test_pirate_variant_is_exposed():
    variant = describe(
        "PowerJoy Game [p1].nes"
    )

    assert (
        "Pirate / Unlicensed"
        in variant.labels
    )


def test_unlicensed_tag_is_exposed():
    variant = describe(
        "Example Game (Unl).nes"
    )

    assert "Unlicensed" in variant.labels


def test_alternate_is_exposed():
    variant = describe(
        "Wonder Boy (U) [a1].nes"
    )

    assert "Alternate 1" in variant.labels


def test_revision_is_exposed():
    variant = describe(
        "Example Game (USA) (Rev 1).nes"
    )

    assert "USA" in variant.labels
    assert "Revision 1" in variant.labels


def test_prototype_and_beta_are_exposed():
    prototype = describe(
        "Example Game (Prototype).nes"
    )
    beta = describe(
        "Example Game (Beta).nes"
    )

    assert "Prototype" in prototype.labels
    assert "Beta" in beta.labels


def test_display_label_does_not_replace_member_identity():
    member = (
        "Adventure Island (U) "
        "[T+Rus_Mario Soft].nes"
    )

    variant = describe(
        member,
        preferred=True,
    )

    assert variant.member == member
    assert "Recommended" in variant.display_name
    assert (
        "Translation: Russian"
        in variant.display_name
    )
