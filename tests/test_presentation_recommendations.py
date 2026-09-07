import pytest

from services.presentation import (
    PresentationProfile,
    PresentationRecommendationCatalog,
)


NES = "platform.nintendo.nes"
SNES = "platform.nintendo.snes"


def test_known_platform_returns_exact_recommendation():
    expected = PresentationProfile(
        shader="/catalog/nes.slangp",
        overlay="/catalog/nes.cfg",
    )

    catalog = PresentationRecommendationCatalog(
        {
            NES: expected,
        }
    )

    assert catalog.recommend(NES) == expected


def test_unknown_platform_returns_empty_profile():
    catalog = PresentationRecommendationCatalog(
        {
            NES: PresentationProfile(
                shader="/catalog/nes.slangp",
            ),
        }
    )

    assert (
        catalog.recommend(SNES)
        == PresentationProfile()
    )


def test_recommendation_properties_remain_independent():
    catalog = PresentationRecommendationCatalog(
        {
            NES: PresentationProfile(
                shader="/catalog/nes.slangp",
            ),
            SNES: PresentationProfile(
                overlay="/catalog/snes.cfg",
            ),
        }
    )

    assert catalog.recommend(NES) == (
        PresentationProfile(
            shader="/catalog/nes.slangp",
        )
    )

    assert catalog.recommend(SNES) == (
        PresentationProfile(
            overlay="/catalog/snes.cfg",
        )
    )


def test_catalog_does_not_fuzzy_match_platform_names():
    catalog = PresentationRecommendationCatalog(
        {
            NES: PresentationProfile(
                shader="/catalog/nes.slangp",
            ),
        }
    )

    assert (
        catalog.recommend("NES")
        == PresentationProfile()
    )

    assert (
        catalog.recommend(
            "Nintendo Entertainment System"
        )
        == PresentationProfile()
    )


@pytest.mark.parametrize(
    "platform_id",
    [
        "",
        "   ",
    ],
)
def test_recommend_rejects_empty_platform_id(
    platform_id,
):
    catalog = PresentationRecommendationCatalog()

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        catalog.recommend(platform_id)


@pytest.mark.parametrize(
    "platform_id",
    [
        None,
        123,
        {},
    ],
)
def test_recommend_rejects_untyped_platform_id(
    platform_id,
):
    catalog = PresentationRecommendationCatalog()

    with pytest.raises(
        TypeError,
        match="must be a string",
    ):
        catalog.recommend(platform_id)


def test_constructor_rejects_untyped_recommendation():
    with pytest.raises(
        TypeError,
        match="Recommendation",
    ):
        PresentationRecommendationCatalog(
            {
                NES: "/catalog/nes.slangp",
            }
        )


def test_constructor_rejects_invalid_platform_id():
    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        PresentationRecommendationCatalog(
            {
                "": PresentationProfile(),
            }
        )
