import json

import pytest

from services.presentation import (
    PresentationProfile,
    PresentationRecommendationCatalog,
    PresentationRecommendationManifest,
)


NES = "platform.nintendo.nes"
SUPER_METROID = "game.super_metroid"


def test_catalog_preserves_system_recommendation_api():
    system = PresentationProfile(
        shader="system.slangp",
        overlay="system.cfg",
    )

    catalog = PresentationRecommendationCatalog(
        {
            NES: system,
        }
    )

    assert catalog.recommend(NES) == system


def test_catalog_returns_game_recommendation():
    game = PresentationProfile(
        overlay="game.cfg",
        artwork="game.png",
    )

    catalog = PresentationRecommendationCatalog(
        game_recommendations={
            SUPER_METROID: game,
        }
    )

    assert (
        catalog.recommend_game(
            SUPER_METROID
        )
        == game
    )


def test_missing_game_recommendation_is_empty():
    catalog = PresentationRecommendationCatalog()

    assert catalog.recommend_game(
        SUPER_METROID
    ) == PresentationProfile()


@pytest.mark.parametrize(
    "game_id",
    [
        "",
        "   ",
    ],
)
def test_game_recommendation_rejects_empty_identity(
    game_id,
):
    catalog = PresentationRecommendationCatalog()

    with pytest.raises(
        ValueError,
        match="Game ID",
    ):
        catalog.recommend_game(
            game_id
        )


@pytest.mark.parametrize(
    "game_id",
    [
        None,
        123,
        (),
    ],
)
def test_game_recommendation_rejects_untyped_identity(
    game_id,
):
    catalog = PresentationRecommendationCatalog()

    with pytest.raises(
        TypeError,
        match="Game ID",
    ):
        catalog.recommend_game(
            game_id
        )


def test_manifest_loads_optional_games_mapping(
    tmp_path,
):
    manifest = (
        tmp_path
        / "recommendations.json"
    )

    manifest.write_text(
        json.dumps(
            {
                "version": 1,
                "systems": {
                    NES: {
                        "shader": (
                            "system.slangp"
                        ),
                        "overlay": "",
                        "artwork": "",
                    },
                },
                "games": {
                    SUPER_METROID: {
                        "shader": "",
                        "overlay": (
                            "super-metroid.cfg"
                        ),
                        "artwork": (
                            "super-metroid.png"
                        ),
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    catalog = (
        PresentationRecommendationManifest(
            manifest
        ).load()
    )

    assert catalog.recommend(
        NES
    ) == PresentationProfile(
        shader="system.slangp",
    )

    assert catalog.recommend_game(
        SUPER_METROID
    ) == PresentationProfile(
        overlay="super-metroid.cfg",
        artwork="super-metroid.png",
    )


def test_manifest_games_mapping_is_optional(
    tmp_path,
):
    manifest = (
        tmp_path
        / "recommendations.json"
    )

    manifest.write_text(
        json.dumps(
            {
                "version": 1,
                "systems": {},
            }
        ),
        encoding="utf-8",
    )

    catalog = (
        PresentationRecommendationManifest(
            manifest
        ).load()
    )

    assert catalog.recommend_game(
        SUPER_METROID
    ) == PresentationProfile()


def test_manifest_rejects_non_mapping_games(
    tmp_path,
):
    manifest = (
        tmp_path
        / "recommendations.json"
    )

    manifest.write_text(
        json.dumps(
            {
                "version": 1,
                "systems": {},
                "games": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="games",
    ):
        PresentationRecommendationManifest(
            manifest
        ).load()


def test_manifest_rejects_empty_game_identity(
    tmp_path,
):
    manifest = (
        tmp_path
        / "recommendations.json"
    )

    manifest.write_text(
        json.dumps(
            {
                "version": 1,
                "systems": {},
                "games": {
                    "": {
                        "shader": "",
                        "overlay": "",
                        "artwork": "",
                    },
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="game identities",
    ):
        PresentationRecommendationManifest(
            manifest
        ).load()


def test_current_production_manifest_remains_compatible():
    catalog = (
        PresentationRecommendationManifest()
        .load()
    )

    assert catalog.recommend(
        NES
    ) != PresentationProfile()

    super_metroid = catalog.recommend_game(
        SUPER_METROID
    )

    assert super_metroid != PresentationProfile()

    assert super_metroid.shader.endswith(
        "SuperMetroid__STD.slangp"
    )

    assert catalog.recommend_game(
        "game.unknown"
    ) == PresentationProfile()
