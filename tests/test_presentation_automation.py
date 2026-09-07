import pytest

from services.presentation import (
    PresentationAutomationPolicy,
    PresentationProfile,
)


def test_empty_manual_profile_accepts_automatic_profile():
    manual = PresentationProfile()

    automatic = PresentationProfile(
        shader="/automatic/nes.slangp",
        overlay="/automatic/nes.cfg",
        artwork="/automatic/nes.png",
    )

    assert (
        PresentationAutomationPolicy.compose(
            manual,
            automatic,
        )
        == automatic
    )


def test_manual_profile_is_authoritative_by_property():
    manual = PresentationProfile(
        overlay="/manual/duck-tales.cfg",
    )

    automatic = PresentationProfile(
        shader="/automatic/nes.slangp",
        overlay="/automatic/nes.cfg",
        artwork="/automatic/nes.png",
    )

    assert (
        PresentationAutomationPolicy.compose(
            manual,
            automatic,
        )
        == PresentationProfile(
            shader="/automatic/nes.slangp",
            overlay="/manual/duck-tales.cfg",
            artwork="/automatic/nes.png",
        )
    )


def test_complete_manual_profile_blocks_automatic_profile():
    manual = PresentationProfile(
        shader="/manual/game.slangp",
        overlay="/manual/game.cfg",
        artwork="/manual/game.png",
    )

    automatic = PresentationProfile(
        shader="/automatic/system.slangp",
        overlay="/automatic/system.cfg",
        artwork="/automatic/system.png",
    )

    assert (
        PresentationAutomationPolicy.compose(
            manual,
            automatic,
        )
        == manual
    )


def test_empty_automatic_profile_preserves_manual_profile():
    manual = PresentationProfile(
        shader="/manual/nes.slangp",
    )

    assert (
        PresentationAutomationPolicy.compose(
            manual,
            PresentationProfile(),
        )
        == manual
    )


@pytest.mark.parametrize(
    "manual",
    [
        None,
        {},
        "",
    ],
)
def test_compose_rejects_untyped_manual_profile(
    manual,
):
    with pytest.raises(
        TypeError,
        match="Manual presentation",
    ):
        PresentationAutomationPolicy.compose(
            manual,
            PresentationProfile(),
        )


@pytest.mark.parametrize(
    "automatic",
    [
        None,
        {},
        "",
    ],
)
def test_compose_rejects_untyped_automatic_profile(
    automatic,
):
    with pytest.raises(
        TypeError,
        match="Automatic presentation",
    ):
        PresentationAutomationPolicy.compose(
            PresentationProfile(),
            automatic,
        )
