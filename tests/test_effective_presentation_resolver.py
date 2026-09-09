import pytest

from services.library.models import Game
from services.library.state import game_identity
from services.presentation import (
    EffectivePresentationResolver,
    PresentationAssetReferenceResolver,
    PresentationProfile,
    PresentationRecommendationCatalog,
    PresentationRecommendationComposer,
    PresentationRecommendationResolver,
    PresentationResolver,
)


NES = "platform.nintendo.nes"


def make_game(
    tmp_path,
    *,
    platform_id=NES,
):
    return Game(
        name="Duck Tales 2",
        platform="Nintendo Entertainment System",
        year=1993,
        genre="Platform",
        core="FCEUmm",
        rom=str(
            tmp_path
            / "Duck Tales 2 (U).nes"
        ),
        rvdb_platform_id=platform_id,
    )


def make_effective_resolver(
    tmp_path,
    *,
    manual_resolver=None,
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

    recommendation_resolver = (
        PresentationRecommendationResolver(
            catalog=(
                PresentationRecommendationCatalog(
                    recommendations or {}
                )
            ),
            asset_resolver=asset_resolver,
        )
    )

    composer = PresentationRecommendationComposer(
        recommendation_resolver=(
            recommendation_resolver
        )
    )

    effective = EffectivePresentationResolver(
        manual_resolver=(
            manual_resolver
            or PresentationResolver()
        ),
        recommendation_composer=composer,
        asset_resolver=asset_resolver,
    )

    return (
        effective,
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


def test_automatic_recommendation_fills_empty_manual_profile(
    tmp_path,
):
    (
        resolver,
        shader_root,
        overlay_root,
        _,
    ) = make_effective_resolver(
        tmp_path,
        recommendations={
            NES: PresentationProfile(
                shader=(
                    "retro-vault://shaders/"
                    f"{NES}/default.slangp"
                ),
                overlay=(
                    "retro-vault://overlays/"
                    f"{NES}/default.cfg"
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

    assert resolver.resolve(
        make_game(tmp_path)
    ) == PresentationProfile(
        shader=str(shader),
        overlay=str(overlay),
    )


def test_manual_system_value_wins_over_automatic_by_property(
    tmp_path,
):
    manual = PresentationResolver(
        systems={
            NES: PresentationProfile(
                overlay="/manual/nes.cfg",
            ),
        }
    )

    (
        resolver,
        shader_root,
        overlay_root,
        _,
    ) = make_effective_resolver(
        tmp_path,
        manual_resolver=manual,
        recommendations={
            NES: PresentationProfile(
                shader=(
                    "retro-vault://shaders/"
                    f"{NES}/default.slangp"
                ),
                overlay=(
                    "retro-vault://overlays/"
                    f"{NES}/default.cfg"
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

    assert resolver.resolve(
        make_game(tmp_path)
    ) == PresentationProfile(
        shader=str(shader),
        overlay="/manual/nes.cfg",
    )


def test_manual_game_precedence_survives_automatic_composition(
    tmp_path,
):
    game = make_game(tmp_path)

    manual = PresentationResolver(
        default=PresentationProfile(
            artwork="/manual/default.png",
        ),
        systems={
            NES: PresentationProfile(
                shader="/manual/nes.slangp",
            ),
        },
        games={
            game_identity(game): (
                PresentationProfile(
                    overlay="/manual/duck.cfg",
                )
            ),
        },
    )

    (
        resolver,
        shader_root,
        overlay_root,
        artwork_root,
    ) = make_effective_resolver(
        tmp_path,
        manual_resolver=manual,
        recommendations={
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

    assert resolver.resolve(
        game
    ) == PresentationProfile(
        shader="/manual/nes.slangp",
        overlay="/manual/duck.cfg",
        artwork="/manual/default.png",
    )


def test_manual_portable_system_overlay_is_localized(
    tmp_path,
):
    relative = (
        "retrovault/nes/classic/"
        "RetroVault_NES_Classic.cfg"
    )

    manual = PresentationResolver(
        systems={
            NES: PresentationProfile(
                overlay=(
                    "retro-vault://overlays/"
                    f"{relative}"
                )
            ),
        }
    )

    (
        resolver,
        _,
        overlay_root,
        _,
    ) = make_effective_resolver(
        tmp_path,
        manual_resolver=manual,
    )

    overlay = create_asset(
        overlay_root,
        relative,
    )

    assert resolver.resolve(
        make_game(tmp_path)
    ) == PresentationProfile(
        overlay=str(overlay),
    )


def test_manual_portable_default_without_platform_is_localized(
    tmp_path,
):
    relative = "defaults/nes.cfg"

    manual = PresentationResolver(
        default=PresentationProfile(
            overlay=(
                "retro-vault://overlays/"
                f"{relative}"
            )
        )
    )

    (
        resolver,
        _,
        overlay_root,
        _,
    ) = make_effective_resolver(
        tmp_path,
        manual_resolver=manual,
    )

    overlay = create_asset(
        overlay_root,
        relative,
    )

    assert resolver.resolve(
        make_game(
            tmp_path,
            platform_id="",
        )
    ) == PresentationProfile(
        overlay=str(overlay),
    )



def test_unknown_platform_preserves_manual_resolution(
    tmp_path,
):
    unknown = "platform.example.unknown"

    manual = PresentationResolver(
        systems={
            unknown: PresentationProfile(
                shader="/manual/unknown.slangp",
            ),
        }
    )

    (
        resolver,
        _,
        _,
        _,
    ) = make_effective_resolver(
        tmp_path,
        manual_resolver=manual,
    )

    assert resolver.resolve(
        make_game(
            tmp_path,
            platform_id=unknown,
        )
    ) == PresentationProfile(
        shader="/manual/unknown.slangp",
    )


def test_missing_platform_identity_preserves_manual_resolution(
    tmp_path,
):
    manual = PresentationResolver(
        default=PresentationProfile(
            overlay="/manual/default.cfg",
        )
    )

    (
        resolver,
        _,
        _,
        _,
    ) = make_effective_resolver(
        tmp_path,
        manual_resolver=manual,
    )

    assert resolver.resolve(
        make_game(
            tmp_path,
            platform_id="",
        )
    ) == PresentationProfile(
        overlay="/manual/default.cfg",
    )


def test_missing_automatic_asset_remains_explicit_error(
    tmp_path,
):
    (
        resolver,
        _,
        _,
        _,
    ) = make_effective_resolver(
        tmp_path,
        recommendations={
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
        resolver.resolve(
            make_game(tmp_path)
        )


@pytest.mark.parametrize(
    "manual_resolver",
    [
        None,
        {},
        "",
    ],
)
def test_constructor_requires_manual_resolver(
    tmp_path,
    manual_resolver,
):
    (
        _effective,
        shader_root,
        overlay_root,
        artwork_root,
    ) = make_effective_resolver(tmp_path)

    asset_resolver = (
        PresentationAssetReferenceResolver(
            shader_root=shader_root,
            overlay_root=overlay_root,
            artwork_root=artwork_root,
        )
    )

    recommendation_resolver = (
        PresentationRecommendationResolver(
            catalog=(
                PresentationRecommendationCatalog()
            ),
            asset_resolver=asset_resolver,
        )
    )

    composer = PresentationRecommendationComposer(
        recommendation_resolver=(
            recommendation_resolver
        )
    )

    with pytest.raises(
        TypeError,
        match="Manual resolver",
    ):
        EffectivePresentationResolver(
            manual_resolver=manual_resolver,
            recommendation_composer=composer,
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
    tmp_path,
    asset_resolver,
):
    (
        _effective,
        shader_root,
        overlay_root,
        artwork_root,
    ) = make_effective_resolver(tmp_path)

    recommendation_resolver = (
        PresentationRecommendationResolver(
            catalog=(
                PresentationRecommendationCatalog()
            ),
            asset_resolver=(
                PresentationAssetReferenceResolver(
                    shader_root=shader_root,
                    overlay_root=overlay_root,
                    artwork_root=artwork_root,
                )
            ),
        )
    )

    composer = PresentationRecommendationComposer(
        recommendation_resolver=(
            recommendation_resolver
        )
    )

    with pytest.raises(
        TypeError,
        match="Asset resolver",
    ):
        EffectivePresentationResolver(
            manual_resolver=PresentationResolver(),
            recommendation_composer=composer,
            asset_resolver=asset_resolver,
        )



@pytest.mark.parametrize(
    "recommendation_composer",
    [
        None,
        {},
        "",
    ],
)
def test_constructor_requires_recommendation_composer(
    recommendation_composer,
):
    with pytest.raises(
        TypeError,
        match="Recommendation composer",
    ):
        EffectivePresentationResolver(
            manual_resolver=PresentationResolver(),
            recommendation_composer=(
                recommendation_composer
            ),
            asset_resolver=(
                PresentationAssetReferenceResolver()
            ),
        )
