import pytest

from services.presentation.visual_catalog import (
    VisualAsset,
    VisualAssetCatalog,
    VisualAssetSource,
    VisualAssetType,
)


def make_native_overlay():
    return VisualAsset(
        id="rvv.overlay.nes.classic",
        display_name="Nintendo NES — RetroVault Classic",
        asset_type=VisualAssetType.OVERLAY,
        source=VisualAssetSource.RVV_NATIVE,
        reference=(
            "retro-vault://overlays/"
            "retrovault/nes/classic.cfg"
        ),
        author="RetroVault",
        attribution="Original RetroVault visual.",
    )


def test_visual_asset_preserves_curated_metadata():
    asset = make_native_overlay()

    assert asset.id == "rvv.overlay.nes.classic"
    assert (
        asset.display_name
        == "Nintendo NES — RetroVault Classic"
    )
    assert (
        asset.asset_type
        is VisualAssetType.OVERLAY
    )
    assert (
        asset.source
        is VisualAssetSource.RVV_NATIVE
    )
    assert asset.author == "RetroVault"


def test_visual_asset_requires_stable_identity():
    with pytest.raises(ValueError):
        VisualAsset(
            id="",
            display_name="Example",
            asset_type=VisualAssetType.SHADER,
            source=VisualAssetSource.USER,
            reference="retro-vault://shaders/example.slangp",
        )


def test_visual_asset_requires_display_name():
    with pytest.raises(ValueError):
        VisualAsset(
            id="rvv.shader.example",
            display_name="",
            asset_type=VisualAssetType.SHADER,
            source=VisualAssetSource.USER,
            reference="retro-vault://shaders/example.slangp",
        )


def test_visual_asset_requires_reference():
    with pytest.raises(ValueError):
        VisualAsset(
            id="rvv.shader.example",
            display_name="Example",
            asset_type=VisualAssetType.SHADER,
            source=VisualAssetSource.USER,
            reference="",
        )


def test_visual_asset_requires_typed_asset_type():
    with pytest.raises(TypeError):
        VisualAsset(
            id="rvv.shader.example",
            display_name="Example",
            asset_type="shader",
            source=VisualAssetSource.USER,
            reference="retro-vault://shaders/example.slangp",
        )


def test_visual_asset_requires_typed_source():
    with pytest.raises(TypeError):
        VisualAsset(
            id="rvv.shader.example",
            display_name="Example",
            asset_type=VisualAssetType.SHADER,
            source="user",
            reference="retro-vault://shaders/example.slangp",
        )


def test_catalog_supports_exact_id_lookup():
    asset = make_native_overlay()

    catalog = VisualAssetCatalog(
        [asset]
    )

    assert (
        catalog.get(
            "rvv.overlay.nes.classic"
        )
        is asset
    )

    assert (
        catalog.get(
            "RVV.OVERLAY.NES.CLASSIC"
        )
        is None
    )


def test_catalog_require_rejects_unknown_id():
    catalog = VisualAssetCatalog()

    with pytest.raises(KeyError):
        catalog.require(
            "rvv.overlay.missing"
        )


def test_catalog_rejects_duplicate_ids():
    asset = make_native_overlay()

    with pytest.raises(ValueError):
        VisualAssetCatalog(
            [
                asset,
                asset,
            ]
        )


def test_catalog_filters_by_asset_type():
    overlay = make_native_overlay()

    shader = VisualAsset(
        id="third-party.shader.nes.example",
        display_name="Nintendo NES — Example CRT",
        asset_type=VisualAssetType.SHADER,
        source=VisualAssetSource.THIRD_PARTY,
        reference=(
            "retro-vault://shaders/"
            "example/NES.slangp"
        ),
    )

    catalog = VisualAssetCatalog(
        [
            overlay,
            shader,
        ]
    )

    assert catalog.for_type(
        VisualAssetType.OVERLAY
    ) == (
        overlay,
    )

    assert catalog.for_type(
        VisualAssetType.SHADER
    ) == (
        shader,
    )


def test_catalog_filters_by_source():
    native = make_native_overlay()

    third_party = VisualAsset(
        id="third-party.shader.nes.example",
        display_name="Nintendo NES — Example CRT",
        asset_type=VisualAssetType.SHADER,
        source=VisualAssetSource.THIRD_PARTY,
        reference=(
            "retro-vault://shaders/"
            "example/NES.slangp"
        ),
        author="Example Author",
    )

    catalog = VisualAssetCatalog(
        [
            native,
            third_party,
        ]
    )

    assert catalog.for_source(
        VisualAssetSource.RVV_NATIVE
    ) == (
        native,
    )

    assert catalog.for_source(
        VisualAssetSource.THIRD_PARTY
    ) == (
        third_party,
    )


def test_catalog_rejects_non_asset_entries():
    with pytest.raises(TypeError):
        VisualAssetCatalog(
            [
                object(),
            ]
        )
