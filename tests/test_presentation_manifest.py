import json

import pytest

from services.presentation import (
    PresentationProfile,
    PresentationRecommendationCatalog,
    PresentationRecommendationManifest,
)


NES = "platform.nintendo.nes"


def write_manifest(
    tmp_path,
    payload,
):
    path = (
        tmp_path
        / "recommendations.json"
    )

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    return path


def test_production_manifest_loads():
    loader = PresentationRecommendationManifest()

    catalog = loader.load()

    assert isinstance(
        catalog,
        PresentationRecommendationCatalog,
    )


def test_known_platform_loads_exact_profile(
    tmp_path,
):
    path = write_manifest(
        tmp_path,
        {
            "version": 1,
            "systems": {
                NES: {
                    "shader": "shaders/nes.slangp",
                    "overlay": "overlays/nes.cfg",
                    "artwork": "artwork/nes.png",
                },
            },
        },
    )

    catalog = (
        PresentationRecommendationManifest(
            path
        ).load()
    )

    assert catalog.recommend(NES) == (
        PresentationProfile(
            shader="shaders/nes.slangp",
            overlay="overlays/nes.cfg",
            artwork="artwork/nes.png",
        )
    )


def test_missing_profile_fields_default_empty(
    tmp_path,
):
    path = write_manifest(
        tmp_path,
        {
            "version": 1,
            "systems": {
                NES: {
                    "shader": "shaders/nes.slangp",
                },
            },
        },
    )

    catalog = (
        PresentationRecommendationManifest(
            path
        ).load()
    )

    assert catalog.recommend(NES) == (
        PresentationProfile(
            shader="shaders/nes.slangp",
        )
    )


def test_missing_manifest_is_rejected(
    tmp_path,
):
    loader = PresentationRecommendationManifest(
        tmp_path / "missing.json"
    )

    with pytest.raises(
        ValueError,
        match="does not exist",
    ):
        loader.load()


def test_invalid_json_is_rejected(
    tmp_path,
):
    path = (
        tmp_path
        / "recommendations.json"
    )

    path.write_text(
        "{broken",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Invalid RetroVault",
    ):
        PresentationRecommendationManifest(
            path
        ).load()


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {
            "version": 2,
            "systems": {},
        },
        {
            "version": 1,
        },
        {
            "version": 1,
            "systems": [],
        },
        {
            "version": 1,
            "systems": {},
            "unexpected": {},
        },
        {
            "version": 1,
            "systems": {
                "": {},
            },
        },
        {
            "version": 1,
            "systems": {
                NES: [],
            },
        },
        {
            "version": 1,
            "systems": {
                NES: {
                    "shader": 123,
                },
            },
        },
        {
            "version": 1,
            "systems": {
                NES: {
                    "unknown": "value",
                },
            },
        },
    ],
)
def test_invalid_manifest_documents_are_rejected(
    tmp_path,
    payload,
):
    path = write_manifest(
        tmp_path,
        payload,
    )

    with pytest.raises(ValueError):
        PresentationRecommendationManifest(
            path
        ).load()


def test_manifest_does_not_fuzzy_match_platforms(
    tmp_path,
):
    path = write_manifest(
        tmp_path,
        {
            "version": 1,
            "systems": {
                NES: {
                    "shader": "shaders/nes.slangp",
                },
            },
        },
    )

    catalog = (
        PresentationRecommendationManifest(
            path
        ).load()
    )

    assert (
        catalog.recommend("NES")
        == PresentationProfile()
    )


def test_manifest_preserves_portable_reference_strings(
    tmp_path,
):
    reference = (
        "retro-vault://shaders/"
        "platform.nintendo.nes/default"
    )

    path = write_manifest(
        tmp_path,
        {
            "version": 1,
            "systems": {
                NES: {
                    "shader": reference,
                },
            },
        },
    )

    catalog = (
        PresentationRecommendationManifest(
            path
        ).load()
    )

    assert (
        catalog.recommend(NES).shader
        == reference
    )
