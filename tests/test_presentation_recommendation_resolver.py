import pytest

from services.presentation import (
    PresentationAssetReferenceResolver,
    PresentationProfile,
    PresentationRecommendationCatalog,
    PresentationRecommendationResolver,
)


NES = "platform.nintendo.nes"
SNES = "platform.nintendo.snes"


def make_asset_resolver(tmp_path):
    shader_root = tmp_path / "shaders"
    overlay_root = tmp_path / "overlays"
    artwork_root = tmp_path / "artwork"

    shader_root.mkdir()
    overlay_root.mkdir()
    artwork_root.mkdir()

    return (
        PresentationAssetReferenceResolver(
            shader_root=shader_root,
            overlay_root=overlay_root,
            artwork_root=artwork_root,
        ),
        shader_root,
        overlay_root,
        artwork_root,
    )


def test_portable_recommendation_resolves_to_local_assets(
    tmp_path,
):
    (
        asset_resolver,
        shader_root,
        overlay_root,
        artwork_root,
    ) = make_asset_resolver(tmp_path)

    shader = (
        shader_root
        / NES
        / "default.slangp"
    )
    overlay = (
        overlay_root
        / NES
        / "default.cfg"
    )
    artwork = (
        artwork_root
        / NES
        / "default.png"
    )

    for path in (
        shader,
        overlay,
        artwork,
    ):
        path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        path.write_text(
            "asset",
            encoding="utf-8",
        )

    catalog = PresentationRecommendationCatalog(
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
        }
    )

    resolver = PresentationRecommendationResolver(
        catalog=catalog,
        asset_resolver=asset_resolver,
    )

    assert resolver.resolve(NES) == (
        PresentationProfile(
            shader=str(shader.resolve()),
            overlay=str(overlay.resolve()),
            artwork=str(artwork.resolve()),
        )
    )


def test_unknown_platform_resolves_to_empty_profile(
    tmp_path,
):
    (
        asset_resolver,
        _,
        _,
        _,
    ) = make_asset_resolver(tmp_path)

    resolver = PresentationRecommendationResolver(
        catalog=PresentationRecommendationCatalog(
            {
                NES: PresentationProfile(
                    shader=(
                        "retro-vault://shaders/"
                        f"{NES}/default.slangp"
                    ),
                ),
            }
        ),
        asset_resolver=asset_resolver,
    )

    assert resolver.resolve(SNES) == (
        PresentationProfile()
    )


def test_existing_nonportable_catalog_values_are_preserved(
    tmp_path,
):
    (
        asset_resolver,
        _,
        _,
        _,
    ) = make_asset_resolver(tmp_path)

    expected = PresentationProfile(
        shader="/catalog/manual.slangp",
        overlay="/catalog/manual.cfg",
        artwork="/catalog/manual.png",
    )

    resolver = PresentationRecommendationResolver(
        catalog=PresentationRecommendationCatalog(
            {
                NES: expected,
            }
        ),
        asset_resolver=asset_resolver,
    )

    assert resolver.resolve(NES) == expected


def test_missing_portable_asset_remains_explicit_error(
    tmp_path,
):
    (
        asset_resolver,
        _,
        _,
        _,
    ) = make_asset_resolver(tmp_path)

    resolver = PresentationRecommendationResolver(
        catalog=PresentationRecommendationCatalog(
            {
                NES: PresentationProfile(
                    shader=(
                        "retro-vault://shaders/"
                        f"{NES}/missing.slangp"
                    ),
                ),
            }
        ),
        asset_resolver=asset_resolver,
    )

    with pytest.raises(
        ValueError,
        match="does not exist",
    ):
        resolver.resolve(NES)


def test_catalog_platform_validation_is_preserved(
    tmp_path,
):
    (
        asset_resolver,
        _,
        _,
        _,
    ) = make_asset_resolver(tmp_path)

    resolver = PresentationRecommendationResolver(
        catalog=PresentationRecommendationCatalog(),
        asset_resolver=asset_resolver,
    )

    with pytest.raises(
        ValueError,
        match="must not be empty",
    ):
        resolver.resolve("")


@pytest.mark.parametrize(
    "catalog",
    [
        None,
        {},
        "",
    ],
)
def test_constructor_requires_catalog(
    tmp_path,
    catalog,
):
    (
        asset_resolver,
        _,
        _,
        _,
    ) = make_asset_resolver(tmp_path)

    with pytest.raises(
        TypeError,
        match="Recommendation catalog",
    ):
        PresentationRecommendationResolver(
            catalog=catalog,
            asset_resolver=asset_resolver,
        )


@pytest.mark.parametrize(
    "asset_resolver",
    [
        None,
        {},
        "",
    ],
)
def test_constructor_requires_asset_resolver(
    asset_resolver,
):
    with pytest.raises(
        TypeError,
        match="Asset resolver",
    ):
        PresentationRecommendationResolver(
            catalog=PresentationRecommendationCatalog(),
            asset_resolver=asset_resolver,
        )
