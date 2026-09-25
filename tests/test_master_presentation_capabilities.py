from dataclasses import fields

import pytest

from services.presentation.master_profile import (
    MASTER_PRESENTATION_QUALIFICATION,
    MasterPresentationClass,
    MasterPresentationProfileRegistry,
    MasterPresentationQualification,
    master_presentation_class_is_physically_qualified,
    master_presentation_qualification,
)


def test_master_presentation_classes_cover_major_display_families():
    assert set(MasterPresentationClass) == {
        MasterPresentationClass.CLASSIC_4_3,
        MasterPresentationClass.WIDESCREEN_16_9,
        MasterPresentationClass.ARCADE_HORIZONTAL,
        MasterPresentationClass.ARCADE_VERTICAL,
        MasterPresentationClass.HANDHELD_NATIVE,
        MasterPresentationClass.DUAL_SCREEN,
        MasterPresentationClass.SPECIALIZED,
    }


def test_every_master_class_has_explicit_qualification_state():
    assert (
        set(MASTER_PRESENTATION_QUALIFICATION)
        == set(MasterPresentationClass)
    )


@pytest.mark.parametrize(
    "profile_class",
    (
        MasterPresentationClass.CLASSIC_4_3,
        MasterPresentationClass.WIDESCREEN_16_9,
        MasterPresentationClass.ARCADE_VERTICAL,
    ),
)
def test_existing_physical_profiles_remain_qualified(
    profile_class,
):
    assert (
        master_presentation_qualification(profile_class)
        is MasterPresentationQualification.QUALIFIED
    )

    assert (
        master_presentation_class_is_physically_qualified(
            profile_class
        )
        is True
    )

    assert (
        MasterPresentationProfileRegistry.get(
            profile_class
        )
        is not None
    )


@pytest.mark.parametrize(
    "profile_class",
    (
        MasterPresentationClass.ARCADE_HORIZONTAL,
        MasterPresentationClass.HANDHELD_NATIVE,
        MasterPresentationClass.DUAL_SCREEN,
        MasterPresentationClass.SPECIALIZED,
    ),
)
def test_capability_only_classes_have_no_invented_geometry(
    profile_class,
):
    assert (
        master_presentation_qualification(profile_class)
        is MasterPresentationQualification.CAPABILITY_ONLY
    )

    assert (
        master_presentation_class_is_physically_qualified(
            profile_class
        )
        is False
    )

    assert (
        MasterPresentationProfileRegistry.get(
            profile_class
        )
        is None
    )


def test_qualification_lookup_accepts_stable_string_identity():
    assert (
        master_presentation_qualification(
            "handheld_native"
        )
        is MasterPresentationQualification.CAPABILITY_ONLY
    )

    assert (
        master_presentation_qualification(
            "classic_4_3"
        )
        is MasterPresentationQualification.QUALIFIED
    )


def test_unknown_qualification_identity_is_rejected():
    with pytest.raises(KeyError):
        master_presentation_qualification(
            "not_a_real_presentation_class"
        )


def test_capability_contract_contains_no_per_game_identity():
    forbidden = {
        "game_id",
        "rom_path",
        "rom_filename",
        "archive_filename",
        "title_id",
    }

    for profile_class in MasterPresentationClass:
        value = profile_class.value.casefold()

        for token in (
            "game_id",
            "rom",
            "filename",
            "title_id",
        ):
            assert token not in value

    profile = MasterPresentationProfileRegistry.require(
        MasterPresentationClass.CLASSIC_4_3
    )

    names = {
        field.name.casefold()
        for field in fields(type(profile))
    }

    assert names.isdisjoint(forbidden)
