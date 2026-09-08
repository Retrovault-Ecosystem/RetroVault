import pytest

from services.presentation import (
    PresentationAssetReferenceResolver,
    PresentationProfile,
    PresentationRecommendationCatalog,
    PresentationRecommendationComposer,
    PresentationRecommendationResolver,
)


NES = "platform.nintendo.nes"
SNES = "platform.nintendo.snes"


def make_composer(
    tmp_path,
    recommendations=None,
):
    shader_root = tmp_path / "shaders"
    overlay_root = tmp_path / "overlays"
    artwork_root = tmp_path / "artwork"

    shader_root.mkdir()
    overlay_root.mkdir()
    artwork_root.mkdir()

    asset_resolver = (
        PresentationAssetReferenceResolver(
            shader_root=shader_root,
            overlay_root=overlay_root,
            artwork_root=artwork_root,
        )
    )

    catalog = PresentationRecommendationCatalog(
        recommendations or {}
    )

    recommendation_resolver = (
        PresentationRecommendationResolver(
            catalog=catalog,
            asset_resolver=asset_resolver,
        )
    )

    composer = PresentationRecommendationComposer(
        recommendation_resolver=(
            recommendation_resolver
        )
    )

    return (
        composer,
        shader_root,
        overlay_root,
        artwork_root,
    )


def create_asset(
    root,
    relative_path,
):
    path = root / relative_path
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    path.write_text(
        "asset",
        encoding="utf-8",
    )
    return path.resolve()


def test_empty_manual_profile_accepts_resolved_recommendation(
    tmp_path,
):
    (
        composer,
        shader_root,
        overlay_root,
        artwork_root,
    ) = make_composer(
        tmp_path,
        {
            NES: PresentationProfile(
                shader=(
                    "retro-vault://shaders/"
                    f"{NES}/default.slangp"
                ),
                overlay=(
                    "retro-vault://overlays/"
                    f"{NES}/default.cfg"
                ),
                artwork=(
                    "retro-vault://artwork/"
                    f"{NES}/default.png"
                ),
            ),
        },
    )

    shader = create_asset(
        shader_root,
        f"{NES}/default.slangp",
    )
    overlay = create_asset(
        overlay_root,
        f"{NES}/default.cfg",
    )
    artwork = create_asset(
        artwork_root,
        f"{NES}/default.png",
    )

    assert composer.compose(
        platform_id=NES,
        manual=PresentationProfile(),
    ) == PresentationProfile(
        shader=str(shader),
        overlay=str(overlay),
        artwork=str(artwork),
    )


def test_manual_values_are_authoritative_by_property(
    tmp_path,
):
    (
        composer,
        shader_root,
        overlay_root,
        artwork_root,
    ) = make_composer(
        tmp_path,
        {
            NES: PresentationProfile(
                shader=(
                    "retro-vault://shaders/"
                    f"{NES}/default.slangp"
                ),
                overlay=(
                    "retro-vault://overlays/"
                    f"{NES}/default.cfg"
                ),
                artwork=(
                    "retro-vault://artwork/"
                    f"{NES}/default.png"
                ),
            ),
        },
    )

    shader = create_asset(
        shader_root,
        f"{NES}/default.slangp",
    )
    create_asset(
        overlay_root,
        f"{NES}/default.cfg",
    )
    artwork = create_asset(
        artwork_root,
        f"{NES}/default.png",
    )

    manual = PresentationProfile(
        overlay="/manual/game.cfg",
    )

    assert composer.compose(
        platform_id=NES,
        manual=manual,
    ) == PresentationProfile(
        shader=str(shader),
        overlay="/manual/game.cfg",
        artwork=str(artwork),
    )


def test_complete_manual_profile_remains_authoritative(
    tmp_path,
):
    (
        composer,
        shader_root,
        overlay_root,
        artwork_root,
    ) = make_composer(
        tmp_path,
        {
            NES: PresentationProfile(
                shader=(
                    "retro-vault://shaders/"
                    f"{NES}/default.slangp"
                ),
                overlay=(
                    "retro-vault://overlays/"
                    f"{NES}/default.cfg"
                ),
                artwork=(
                    "retro-vault://artwork/"
                    f"{NES}/default.png"
                ),
            ),
        },
    )

    create_asset(
        shader_root,
        f"{NES}/default.slangp",
    )
    create_asset(
        overlay_root,
        f"{NES}/default.cfg",
    )
    create_asset(
        artwork_root,
        f"{NES}/default.png",
    )

    manual = PresentationProfile(
        shader="/manual/game.slangp",
        overlay="/manual/game.cfg",
        artwork="/manual/game.png",
    )

    assert composer.compose(
        platform_id=NES,
        manual=manual,
    ) == manual


def test_unknown_platform_preserves_manual_profile(
    tmp_path,
):
    (
        composer,
        _,
        _,
        _,
    ) = make_composer(
        tmp_path,
        {
            NES: PresentationProfile(
                shader="/automatic/nes.slangp",
            ),
        },
    )

    manual = PresentationProfile(
        overlay="/manual/game.cfg",
    )

    assert composer.compose(
        platform_id=SNES,
        manual=manual,
    ) == manual


def test_missing_recommended_asset_remains_explicit_error(
    tmp_path,
):
    (
        composer,
        _,
        _,
        _,
    ) = make_composer(
        tmp_path,
        {
            NES: PresentationProfile(
                shader=(
                    "retro-vault://shaders/"
                    f"{NES}/missing.slangp"
                ),
            ),
        },
    )

    with pytest.raises(
        ValueError,
        match="does not exist",
    ):
        composer.compose(
            platform_id=NES,
            manual=PresentationProfile(),
        )


def test_platform_validation_remains_authoritative(
    tmp_path,
):
    (
        composer,
        _,
        _,
        _,
    ) = make_composer(tmp_path)

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        composer.compose(
            platform_id="",
            manual=PresentationProfile(),
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
    tmp_path,
    manual,
):
    (
        composer,
        _,
        _,
        _,
    ) = make_composer(tmp_path)

    with pytest.raises(
        TypeError,
        match="Manual presentation",
    ):
        composer.compose(
            platform_id=NES,
            manual=manual,
        )


@pytest.mark.parametrize(
    "recommendation_resolver",
    [
        None,
        {},
        "",
    ],
)
def test_constructor_requires_recommendation_resolver(
    recommendation_resolver,
):
    with pytest.raises(
        TypeError,
        match="Recommendation resolver",
    ):
        PresentationRecommendationComposer(
            recommendation_resolver=(
                recommendation_resolver
            )
        )
