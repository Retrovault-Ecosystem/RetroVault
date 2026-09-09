import os
from pathlib import Path

import pytest

from services.presentation.native_deployment import (
    NativeVisualDeploymentService,
)
from services.presentation.visual_catalog import (
    VisualAsset,
    VisualAssetSource,
    VisualAssetType,
)
from services.presentation.visual_manifest import (
    VisualAssetCatalogManifest,
)


def make_package(
    root,
):
    package = (
        root
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
        b"native-rvv-image"
    )

    return descriptor, image


def make_asset(
    *,
    source=VisualAssetSource.RVV_NATIVE,
    asset_type=VisualAssetType.OVERLAY,
    reference=(
        "retro-vault://overlays/"
        "retrovault/nes/classic/"
        "RetroVault_NES_Classic.cfg"
    ),
):
    return VisualAsset(
        id="rvv.overlay.nes.classic",
        display_name=(
            "Nintendo NES — RetroVault Classic"
        ),
        asset_type=asset_type,
        source=source,
        reference=reference,
        author="RetroVault",
    )


def make_service(
    tmp_path,
):
    repository = tmp_path / "repository"
    overlay_root = tmp_path / "overlays"

    descriptor, image = make_package(
        repository
    )

    service = NativeVisualDeploymentService(
        repository_root=repository,
        overlay_root=overlay_root,
    )

    return (
        service,
        repository,
        overlay_root,
        descriptor,
        image,
    )


def test_plan_maps_catalog_path_without_mutation(
    tmp_path,
):
    (
        service,
        _repository,
        overlay_root,
        descriptor,
        image,
    ) = make_service(
        tmp_path
    )

    plan = service.plan(
        make_asset()
    )

    assert plan.asset_id == (
        "rvv.overlay.nes.classic"
    )

    assert plan.relative_descriptor == Path(
        "retrovault/nes/classic/"
        "RetroVault_NES_Classic.cfg"
    )

    assert plan.source_descriptor == (
        descriptor.resolve()
    )

    assert plan.source_files == (
        descriptor.resolve(),
        image.resolve(),
    )

    assert plan.overlay_root == (
        overlay_root.resolve()
    )

    assert plan.destination_directory == (
        overlay_root.resolve()
        / "retrovault"
        / "nes"
        / "classic"
    )

    assert plan.destination_descriptor == (
        overlay_root.resolve()
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic.cfg"
    )

    assert plan.portable_reference == (
        "retro-vault://overlays/"
        "retrovault/nes/classic/"
        "RetroVault_NES_Classic.cfg"
    )

    assert not overlay_root.exists()


def test_deploy_copies_complete_native_package(
    tmp_path,
):
    (
        service,
        _repository,
        _overlay_root,
        descriptor,
        image,
    ) = make_service(
        tmp_path
    )

    plan = service.deploy(
        make_asset()
    )

    deployed_descriptor = (
        plan.destination_directory
        / descriptor.name
    )

    deployed_image = (
        plan.destination_directory
        / image.name
    )

    assert deployed_descriptor.read_bytes() == (
        descriptor.read_bytes()
    )

    assert deployed_image.read_bytes() == (
        image.read_bytes()
    )

    assert sorted(
        path.name
        for path in (
            plan.destination_directory
        ).iterdir()
    ) == sorted(
        (
            descriptor.name,
            image.name,
        )
    )


def test_redeploy_replaces_stale_package(
    tmp_path,
):
    (
        service,
        _repository,
        overlay_root,
        descriptor,
        image,
    ) = make_service(
        tmp_path
    )

    destination = (
        overlay_root
        / "retrovault"
        / "nes"
        / "classic"
    )

    destination.mkdir(
        parents=True
    )

    (
        destination
        / descriptor.name
    ).write_bytes(
        b"stale-descriptor"
    )

    (
        destination
        / image.name
    ).write_bytes(
        b"stale-image"
    )

    (
        destination
        / "obsolete-file.txt"
    ).write_text(
        "obsolete",
        encoding="utf-8",
    )

    service.deploy(
        make_asset()
    )

    assert (
        destination
        / descriptor.name
    ).read_bytes() == descriptor.read_bytes()

    assert (
        destination
        / image.name
    ).read_bytes() == image.read_bytes()

    assert not (
        destination
        / "obsolete-file.txt"
    ).exists()


def test_failed_final_replace_restores_previous_package(
    tmp_path,
    monkeypatch,
):
    (
        service,
        _repository,
        overlay_root,
        descriptor,
        image,
    ) = make_service(
        tmp_path
    )

    destination = (
        overlay_root
        / "retrovault"
        / "nes"
        / "classic"
    )

    destination.mkdir(
        parents=True
    )

    old_descriptor = (
        destination
        / descriptor.name
    )

    old_image = (
        destination
        / image.name
    )

    old_descriptor.write_bytes(
        b"previous-descriptor"
    )

    old_image.write_bytes(
        b"previous-image"
    )

    real_replace = os.replace

    staging_name = (
        ".classic.retrovault-staging"
    )

    failed = False

    def controlled_replace(
        source,
        target,
    ):
        nonlocal failed

        source_path = Path(source)

        if (
            source_path.name == staging_name
            and not failed
        ):
            failed = True

            raise OSError(
                "simulated final package replace failure"
            )

        return real_replace(
            source,
            target,
        )

    monkeypatch.setattr(
        os,
        "replace",
        controlled_replace,
    )

    with pytest.raises(
        OSError,
        match="simulated final package",
    ):
        service.deploy(
            make_asset()
        )

    assert old_descriptor.read_bytes() == (
        b"previous-descriptor"
    )

    assert old_image.read_bytes() == (
        b"previous-image"
    )

    assert not (
        destination.parent
        / ".classic.retrovault-staging"
    ).exists()

    assert not (
        destination.parent
        / ".classic.retrovault-backup"
    ).exists()


def test_existing_staging_directory_blocks_deployment(
    tmp_path,
):
    (
        service,
        _repository,
        overlay_root,
        _descriptor,
        _image,
    ) = make_service(
        tmp_path
    )

    parent = (
        overlay_root
        / "retrovault"
        / "nes"
    )

    parent.mkdir(
        parents=True
    )

    staging = (
        parent
        / ".classic.retrovault-staging"
    )

    staging.mkdir()

    with pytest.raises(
        ValueError,
        match="staging directory",
    ):
        service.deploy(
            make_asset()
        )

    assert staging.is_dir()


def test_existing_backup_directory_blocks_deployment(
    tmp_path,
):
    (
        service,
        _repository,
        overlay_root,
        _descriptor,
        _image,
    ) = make_service(
        tmp_path
    )

    parent = (
        overlay_root
        / "retrovault"
        / "nes"
    )

    parent.mkdir(
        parents=True
    )

    backup = (
        parent
        / ".classic.retrovault-backup"
    )

    backup.mkdir()

    with pytest.raises(
        ValueError,
        match="backup directory",
    ):
        service.deploy(
            make_asset()
        )

    assert backup.is_dir()


def test_deploy_rejects_third_party_asset(
    tmp_path,
):
    service = NativeVisualDeploymentService(
        repository_root=tmp_path,
        overlay_root=tmp_path / "overlays",
    )

    with pytest.raises(
        ValueError,
        match="Only RVV-native",
    ):
        service.plan(
            make_asset(
                source=(
                    VisualAssetSource.THIRD_PARTY
                )
            )
        )


def test_deploy_rejects_non_overlay_asset(
    tmp_path,
):
    service = NativeVisualDeploymentService(
        repository_root=tmp_path,
        overlay_root=tmp_path / "overlays",
    )

    with pytest.raises(
        ValueError,
        match="overlay assets only",
    ):
        service.plan(
            make_asset(
                asset_type=(
                    VisualAssetType.SHADER
                )
            )
        )


def test_deploy_rejects_nonportable_reference(
    tmp_path,
):
    service = NativeVisualDeploymentService(
        repository_root=tmp_path,
        overlay_root=tmp_path / "overlays",
    )

    with pytest.raises(
        ValueError,
        match="portable overlay reference",
    ):
        service.plan(
            make_asset(
                reference="/tmp/example.cfg"
            )
        )


def test_deploy_rejects_parent_traversal(
    tmp_path,
):
    service = NativeVisualDeploymentService(
        repository_root=tmp_path,
        overlay_root=tmp_path / "overlays",
    )

    with pytest.raises(
        ValueError,
        match="unsafe components",
    ):
        service.plan(
            make_asset(
                reference=(
                    "retro-vault://overlays/"
                    "../outside.cfg"
                )
            )
        )


def test_source_must_remain_under_native_package_root(
    tmp_path,
):
    repository = tmp_path / "repository"
    overlay_root = tmp_path / "overlays"

    repository.mkdir()

    outside = repository / "outside.cfg"

    outside.write_text(
        'overlay0_overlay = "outside.png"\n',
        encoding="utf-8",
    )

    (repository / "outside.png").write_bytes(
        b"outside"
    )

    service = NativeVisualDeploymentService(
        repository_root=repository,
        overlay_root=overlay_root,
    )

    with pytest.raises(
        ValueError,
        match="repository package root",
    ):
        service.plan(
            make_asset(
                reference=(
                    "retro-vault://overlays/"
                    "outside.cfg"
                )
            )
        )


def test_overlay_image_must_remain_inside_package(
    tmp_path,
):
    repository = tmp_path / "repository"
    overlay_root = tmp_path / "overlays"

    package = (
        repository
        / "retrovault"
        / "nes"
        / "classic"
    )

    package.mkdir(
        parents=True
    )

    descriptor = package / "bad.cfg"

    descriptor.write_text(
        'overlay0_overlay = "../outside.png"\n',
        encoding="utf-8",
    )

    service = NativeVisualDeploymentService(
        repository_root=repository,
        overlay_root=overlay_root,
    )

    with pytest.raises(
        ValueError,
        match="unsafe components",
    ):
        service.plan(
            make_asset(
                reference=(
                    "retro-vault://overlays/"
                    "retrovault/nes/classic/bad.cfg"
                )
            )
        )


def test_production_catalog_asset_has_deployable_plan():
    root = Path(__file__).resolve().parents[1]

    asset = (
        VisualAssetCatalogManifest()
        .load()
        .require(
            "rvv.overlay.nes.classic"
        )
    )

    service = NativeVisualDeploymentService(
        repository_root=root,
        overlay_root=(
            root
            / ".test-runtime-overlays"
        ),
    )

    plan = service.plan(
        asset
    )

    assert plan.source_descriptor == (
        root
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic.cfg"
    )

    assert plan.relative_descriptor == Path(
        "retrovault/nes/classic/"
        "RetroVault_NES_Classic.cfg"
    )

    assert len(
        plan.source_files
    ) == 2

    assert all(
        path.is_file()
        for path in plan.source_files
    )

    assert plan.destination_descriptor == (
        root
        / ".test-runtime-overlays"
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic.cfg"
    )

    assert plan.portable_reference == (
        "retro-vault://overlays/"
        "retrovault/nes/classic/"
        "RetroVault_NES_Classic.cfg"
    )

    assert not (
        root
        / ".test-runtime-overlays"
    ).exists()


def test_deployment_has_no_assignment_methods():
    assert not hasattr(
        NativeVisualDeploymentService,
        "assign_system_overlay",
    )

    assert not hasattr(
        NativeVisualDeploymentService,
        "assign_game_overlay",
    )

    assert not hasattr(
        NativeVisualDeploymentService,
        "assign_default_overlay",
    )
