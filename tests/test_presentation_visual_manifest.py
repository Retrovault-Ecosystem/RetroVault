import json

import pytest

from services.presentation.visual_catalog import (
    VisualAssetCatalog,
    VisualAssetSource,
    VisualAssetType,
)
from services.presentation.visual_manifest import (
    VisualAssetCatalogManifest,
)


def write_manifest(
    tmp_path,
    payload,
):
    path = (
        tmp_path
        / "visual_catalog.json"
    )

    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )

    return path


def native_overlay_data():
    return {
        "id": "rvv.overlay.nes.classic",
        "display_name": (
            "Nintendo NES — RetroVault Classic"
        ),
        "asset_type": "overlay",
        "source": "rvv_native",
        "reference": (
            "retro-vault://overlays/"
            "retrovault/nes/classic.cfg"
        ),
        "author": "RetroVault",
        "attribution": (
            "Original RetroVault visual."
        ),
    }


def test_production_visual_catalog_manifest_loads():
    catalog = (
        VisualAssetCatalogManifest().load()
    )

    assert isinstance(
        catalog,
        VisualAssetCatalog,
    )

    assets = catalog.all()

    assert len(assets) == 1

    asset = catalog.require(
        "rvv.overlay.nes.classic"
    )

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

    assert asset.reference == (
        "retro-vault://overlays/"
        "retrovault/nes/classic/"
        "RetroVault_NES_Classic.cfg"
    )

    assert asset.author == "RetroVault"

    assert (
        asset.attribution
        == (
            "Original RetroVault bezel composition. "
            "Platform names and trademarks are the "
            "property of their respective owners."
        )
    )


def test_manifest_loads_typed_visual_asset(
    tmp_path,
):
    path = write_manifest(
        tmp_path,
        {
            "version": 1,
            "assets": [
                native_overlay_data(),
            ],
        },
    )

    catalog = (
        VisualAssetCatalogManifest(
            path
        ).load()
    )

    asset = catalog.require(
        "rvv.overlay.nes.classic"
    )

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
    assert (
        asset.attribution
        == "Original RetroVault visual."
    )


def test_manifest_preserves_portable_reference(
    tmp_path,
):
    data = native_overlay_data()

    reference = data["reference"]

    path = write_manifest(
        tmp_path,
        {
            "version": 1,
            "assets": [
                data,
            ],
        },
    )

    catalog = (
        VisualAssetCatalogManifest(
            path
        ).load()
    )

    assert (
        catalog.require(
            data["id"]
        ).reference
        == reference
    )


def test_optional_metadata_defaults_empty(
    tmp_path,
):
    data = native_overlay_data()
    del data["author"]
    del data["attribution"]

    path = write_manifest(
        tmp_path,
        {
            "version": 1,
            "assets": [
                data,
            ],
        },
    )

    asset = (
        VisualAssetCatalogManifest(
            path
        ).load().require(
            data["id"]
        )
    )

    assert asset.author == ""
    assert asset.attribution == ""


def test_missing_manifest_is_rejected(
    tmp_path,
):
    loader = VisualAssetCatalogManifest(
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
        / "visual_catalog.json"
    )

    path.write_text(
        "{broken",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Invalid RetroVault",
    ):
        VisualAssetCatalogManifest(
            path
        ).load()


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {
            "version": 2,
            "assets": [],
        },
        {
            "version": 1,
        },
        {
            "version": 1,
            "assets": {},
        },
        {
            "version": 1,
            "assets": [],
            "unexpected": {},
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
        VisualAssetCatalogManifest(
            path
        ).load()


@pytest.mark.parametrize(
    "mutator",
    [
        lambda data: data.update(
            unexpected="value"
        ),
        lambda data: data.pop("id"),
        lambda data: data.pop(
            "display_name"
        ),
        lambda data: data.pop(
            "asset_type"
        ),
        lambda data: data.pop(
            "source"
        ),
        lambda data: data.pop(
            "reference"
        ),
        lambda data: data.update(
            id=123
        ),
        lambda data: data.update(
            display_name=123
        ),
        lambda data: data.update(
            asset_type=123
        ),
        lambda data: data.update(
            source=123
        ),
        lambda data: data.update(
            reference=123
        ),
        lambda data: data.update(
            author=123
        ),
        lambda data: data.update(
            attribution=123
        ),
        lambda data: data.update(
            asset_type="video"
        ),
        lambda data: data.update(
            source="unknown"
        ),
        lambda data: data.update(
            id=""
        ),
        lambda data: data.update(
            display_name=""
        ),
        lambda data: data.update(
            reference=""
        ),
    ],
)
def test_invalid_asset_documents_are_rejected(
    tmp_path,
    mutator,
):
    data = native_overlay_data()

    mutator(data)

    path = write_manifest(
        tmp_path,
        {
            "version": 1,
            "assets": [
                data,
            ],
        },
    )

    with pytest.raises(ValueError):
        VisualAssetCatalogManifest(
            path
        ).load()


def test_duplicate_asset_ids_are_rejected(
    tmp_path,
):
    data = native_overlay_data()

    path = write_manifest(
        tmp_path,
        {
            "version": 1,
            "assets": [
                data,
                dict(data),
            ],
        },
    )

    with pytest.raises(
        ValueError,
        match="invalid catalog data",
    ):
        VisualAssetCatalogManifest(
            path
        ).load()


def test_manifest_preserves_exact_identity(
    tmp_path,
):
    data = native_overlay_data()

    path = write_manifest(
        tmp_path,
        {
            "version": 1,
            "assets": [
                data,
            ],
        },
    )

    catalog = (
        VisualAssetCatalogManifest(
            path
        ).load()
    )

    assert (
        catalog.get(
            "rvv.overlay.nes.classic"
        )
        is not None
    )

    assert (
        catalog.get(
            "RVV.OVERLAY.NES.CLASSIC"
        )
        is None
    )
