import json
from pathlib import Path

import pytest
import yaml

from config import ConfigLoader

from services.presentation.service import (
    NativeVisualInstallStatus,
    NativeVisualService,
)


ASSET_ID = "rvv.overlay.nes.classic"


def _repository(
    tmp_path,
):
    repository = tmp_path / "repository"

    package = (
        repository
        / "retrovault"
        / "nes"
        / "classic"
    )

    package.mkdir(
        parents=True
    )

    descriptor = (
        package
        / "RetroVault_NES_Classic.cfg"
    )

    image = (
        package
        / "RetroVault_NES_Classic_1080p.png"
    )

    descriptor.write_text(
        'overlays = "1"\n'
        'overlay0_overlay = '
        '"RetroVault_NES_Classic_1080p.png"\n'
        'overlay0_full_screen = true\n'
        'overlay0_descs = 0\n',
        encoding="utf-8",
    )

    image.write_bytes(
        b"rvv-production-image"
    )

    return repository


def _manifest(
    tmp_path,
):
    manifest = (
        tmp_path
        / "visual_catalog.json"
    )

    manifest.write_text(
        json.dumps(
            {
                "version": 1,
                "assets": [
                    {
                        "id": ASSET_ID,
                        "display_name": (
                            "Nintendo NES — "
                            "RetroVault Classic"
                        ),
                        "asset_type": "overlay",
                        "source": "rvv_native",
                        "reference": (
                            "retro-vault://overlays/"
                            "retrovault/nes/classic/"
                            "RetroVault_NES_Classic.cfg"
                        ),
                        "author": "RetroVault",
                        "attribution": "",
                    }
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    return manifest


def _config_loader(
    tmp_path,
    overlay_root,
):
    default = tmp_path / "retroarch.yaml"
    runtime = tmp_path / "user.yaml"

    default.write_text(
        yaml.safe_dump(
            {
                "retroarch": {
                    "executable": "/usr/bin/retroarch",
                    "cores": {
                        "directory": "/cores",
                    },
                },
                "paths": {
                    "overlays": {
                        "directory": str(
                            overlay_root
                        ),
                    },
                    "shaders": {
                        "directory": "/shaders",
                    },
                    "artwork": {
                        "directory": "/artwork",
                    },
                },
                "library": {
                    "sources": [],
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    return ConfigLoader(
        default_file=default,
        runtime_file=runtime,
    )


def _service(
    tmp_path,
    overlay_root,
):
    from services.presentation.visual_manifest import (
        VisualAssetCatalogManifest,
    )

    return NativeVisualService(
        repository_root=_repository(
            tmp_path
        ),
        config_loader=_config_loader(
            tmp_path,
            overlay_root,
        ),
        catalog_manifest=(
            VisualAssetCatalogManifest(
                _manifest(
                    tmp_path
                )
            )
        ),
    )


def test_service_uses_effective_configured_overlay_root(
    tmp_path,
):
    overlay_root = (
        tmp_path
        / "configured-overlays"
    )

    service = _service(
        tmp_path,
        overlay_root,
    )

    assert service.overlay_root() == (
        overlay_root.resolve()
    )


def test_native_assets_are_catalog_driven(
    tmp_path,
):
    service = _service(
        tmp_path,
        tmp_path / "overlays",
    )

    assets = service.native_assets()

    assert len(assets) == 1
    assert assets[0].id == ASSET_ID


def test_missing_installation_is_not_installed(
    tmp_path,
):
    service = _service(
        tmp_path,
        tmp_path / "overlays",
    )

    result = service.status(
        ASSET_ID
    )

    assert result.status is (
        NativeVisualInstallStatus.NOT_INSTALLED
    )


def test_install_reaches_current_state(
    tmp_path,
):
    service = _service(
        tmp_path,
        tmp_path / "overlays",
    )

    result = service.install(
        ASSET_ID
    )

    assert result.status is (
        NativeVisualInstallStatus.CURRENT
    )

    assert (
        result.deployment
        .destination_descriptor
        .is_file()
    )


def test_current_state_requires_byte_identity(
    tmp_path,
):
    service = _service(
        tmp_path,
        tmp_path / "overlays",
    )

    service.install(
        ASSET_ID
    )

    result = service.status(
        ASSET_ID
    )

    assert result.status is (
        NativeVisualInstallStatus.CURRENT
    )


def test_modified_deployment_is_outdated(
    tmp_path,
):
    service = _service(
        tmp_path,
        tmp_path / "overlays",
    )

    installed = service.install(
        ASSET_ID
    )

    installed.deployment.destination_descriptor.write_text(
        "modified",
        encoding="utf-8",
    )

    result = service.status(
        ASSET_ID
    )

    assert result.status is (
        NativeVisualInstallStatus.OUTDATED
    )


def test_missing_file_in_existing_package_is_outdated(
    tmp_path,
):
    service = _service(
        tmp_path,
        tmp_path / "overlays",
    )

    installed = service.install(
        ASSET_ID
    )

    image = (
        installed.deployment
        .destination_directory
        / "RetroVault_NES_Classic_1080p.png"
    )

    image.unlink()

    result = service.status(
        ASSET_ID
    )

    assert result.status is (
        NativeVisualInstallStatus.OUTDATED
    )


def test_extra_file_in_existing_package_is_outdated(
    tmp_path,
):
    service = _service(
        tmp_path,
        tmp_path / "overlays",
    )

    installed = service.install(
        ASSET_ID
    )

    (
        installed.deployment
        .destination_directory
        / "stale.cfg"
    ).write_text(
        "stale",
        encoding="utf-8",
    )

    result = service.status(
        ASSET_ID
    )

    assert result.status is (
        NativeVisualInstallStatus.OUTDATED
    )


def test_reinstall_replaces_outdated_package(
    tmp_path,
):
    service = _service(
        tmp_path,
        tmp_path / "overlays",
    )

    installed = service.install(
        ASSET_ID
    )

    (
        installed.deployment
        .destination_directory
        / "stale.cfg"
    ).write_text(
        "stale",
        encoding="utf-8",
    )

    assert (
        service.status(
            ASSET_ID
        ).status
        is NativeVisualInstallStatus.OUTDATED
    )

    repaired = service.install(
        ASSET_ID
    )

    assert repaired.status is (
        NativeVisualInstallStatus.CURRENT
    )

    assert not (
        repaired.deployment
        .destination_directory
        / "stale.cfg"
    ).exists()


def test_unknown_asset_is_rejected(
    tmp_path,
):
    service = _service(
        tmp_path,
        tmp_path / "overlays",
    )

    with pytest.raises(
        KeyError
    ):
        service.status(
            "rvv.overlay.unknown"
        )


def test_invalid_configuration_is_rejected(
    tmp_path,
):
    class InvalidLoader:
        def load(self):
            return {
                "paths": {}
            }

    from services.presentation.visual_manifest import (
        VisualAssetCatalogManifest,
    )

    service = NativeVisualService(
        repository_root=_repository(
            tmp_path
        ),
        config_loader=InvalidLoader(),
        catalog_manifest=(
            VisualAssetCatalogManifest(
                _manifest(
                    tmp_path
                )
            )
        ),
    )

    with pytest.raises(
        ValueError,
        match="paths.overlays.directory",
    ):
        service.overlay_root()


def test_overlay_root_reloads_configuration(
    tmp_path,
):
    first = tmp_path / "first"
    second = tmp_path / "second"

    default = tmp_path / "retroarch.yaml"
    runtime = tmp_path / "user.yaml"

    default.write_text(
        yaml.safe_dump(
            {
                "retroarch": {
                    "executable": "/usr/bin/retroarch",
                    "cores": {
                        "directory": "/cores",
                    },
                },
                "paths": {
                    "overlays": {
                        "directory": str(first),
                    },
                    "shaders": {
                        "directory": "/shaders",
                    },
                    "artwork": {
                        "directory": "/artwork",
                    },
                },
                "library": {
                    "sources": [],
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    loader = ConfigLoader(
        default_file=default,
        runtime_file=runtime,
    )

    from services.presentation.visual_manifest import (
        VisualAssetCatalogManifest,
    )

    service = NativeVisualService(
        repository_root=_repository(
            tmp_path
        ),
        config_loader=loader,
        catalog_manifest=(
            VisualAssetCatalogManifest(
                _manifest(
                    tmp_path
                )
            )
        ),
    )

    assert service.overlay_root() == (
        first.resolve()
    )

    default.write_text(
        yaml.safe_dump(
            {
                "retroarch": {
                    "executable": "/usr/bin/retroarch",
                    "cores": {
                        "directory": "/cores",
                    },
                },
                "paths": {
                    "overlays": {
                        "directory": str(second),
                    },
                    "shaders": {
                        "directory": "/shaders",
                    },
                    "artwork": {
                        "directory": "/artwork",
                    },
                },
                "library": {
                    "sources": [],
                },
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )

    assert service.overlay_root() == (
        second.resolve()
    )
