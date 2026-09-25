from pathlib import Path

import pytest

from services.presentation.native_shader_deployment import (
    NativeShaderDeploymentService,
)
from services.presentation.visual_catalog import (
    VisualAsset,
    VisualAssetSource,
    VisualAssetType,
)


def _asset(
    reference=(
        "retro-vault://shaders/"
        "genesis/classic/"
        "RetroVault_Genesis_Classic_CRT.slangp"
    ),
):
    return VisualAsset(
        id="rvv.shader.genesis.classic.crt",
        display_name=(
            "Sega Genesis — RetroVault Classic CRT"
        ),
        asset_type=VisualAssetType.SHADER,
        source=VisualAssetSource.RVV_NATIVE,
        reference=reference,
        author="RetroVault",
    )


def _service(
    tmp_path,
):
    return NativeShaderDeploymentService(
        repository_root=Path.cwd(),
        shader_root=tmp_path / "shaders",
    )


def test_genesis_shader_plan_preserves_dependency_topology(
    tmp_path,
):
    service = _service(
        tmp_path
    )

    plan = service.plan(
        _asset()
    )

    assert plan.relative_preset == Path(
        "genesis/classic/"
        "RetroVault_Genesis_Classic_CRT.slangp"
    )

    assert set(
        plan.relative_files
    ) == {
        Path(
            "genesis/classic/"
            "RetroVault_Genesis_Classic_CRT.slangp"
        ),
        Path(
            "shaders/retrovault/genesis/classic/"
            "RetroVault_Genesis_Classic_CRT.slang"
        ),
    }

    assert all(
        path.is_file()
        for path in plan.source_files
    )

    assert not (
        tmp_path / "shaders"
    ).exists()


def test_shader_plan_rejects_overlay_asset(
    tmp_path,
):
    service = _service(
        tmp_path
    )

    asset = VisualAsset(
        id="rvv.overlay.example",
        display_name="Overlay",
        asset_type=VisualAssetType.OVERLAY,
        source=VisualAssetSource.RVV_NATIVE,
        reference=(
            "retro-vault://overlays/"
            "retrovault/genesis/classic/"
            "RetroVault_Genesis_Classic.cfg"
        ),
    )

    with pytest.raises(
        ValueError,
        match="shader assets only",
    ):
        service.plan(
            asset
        )


def test_shader_plan_rejects_non_native_asset(
    tmp_path,
):
    service = _service(
        tmp_path
    )

    asset = VisualAsset(
        id="third.party.shader",
        display_name="Third Party",
        asset_type=VisualAssetType.SHADER,
        source=VisualAssetSource.THIRD_PARTY,
        reference=(
            "retro-vault://shaders/"
            "genesis/classic/"
            "RetroVault_Genesis_Classic_CRT.slangp"
        ),
    )

    with pytest.raises(
        ValueError,
        match="Only RVV-native",
    ):
        service.plan(
            asset
        )


def test_shader_plan_rejects_unsafe_portable_path(
    tmp_path,
):
    service = _service(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="unsafe components",
    ):
        service.plan(
            _asset(
                "retro-vault://shaders/"
                "../outside.slangp"
            )
        )


def test_shader_deployment_copies_preset_and_dependency(
    tmp_path,
):
    service = _service(
        tmp_path
    )

    plan = service.deploy(
        _asset()
    )

    for (
        source,
        relative,
    ) in zip(
        plan.source_files,
        plan.relative_files,
    ):
        destination = (
            plan.shader_root
            / relative
        )

        assert destination.is_file()
        assert (
            destination.read_bytes()
            == source.read_bytes()
        )

    deployed_preset = (
        plan.shader_root
        / plan.relative_preset
    )

    text = deployed_preset.read_text(
        encoding="utf-8"
    )

    assert (
        "../../shaders/retrovault/genesis/classic/"
        "RetroVault_Genesis_Classic_CRT.slang"
        in text
    )

    dependency = (
        deployed_preset.parent
        / "../../shaders/retrovault/genesis/classic/"
        "RetroVault_Genesis_Classic_CRT.slang"
    ).resolve()

    assert dependency.is_file()


def test_shader_deployment_preserves_unrelated_existing_files(
    tmp_path,
):
    service = _service(
        tmp_path
    )

    unrelated = (
        tmp_path
        / "shaders"
        / "existing"
        / "keep.slang"
    )

    unrelated.parent.mkdir(
        parents=True
    )

    unrelated.write_text(
        "keep\n",
        encoding="utf-8",
    )

    service.deploy(
        _asset()
    )

    assert unrelated.read_text(
        encoding="utf-8"
    ) == "keep\n"


def test_shader_deployment_is_idempotent(
    tmp_path,
):
    service = _service(
        tmp_path
    )

    first = service.deploy(
        _asset()
    )

    first_bytes = {
        relative: (
            first.shader_root
            / relative
        ).read_bytes()
        for relative in first.relative_files
    }

    second = service.deploy(
        _asset()
    )

    second_bytes = {
        relative: (
            second.shader_root
            / relative
        ).read_bytes()
        for relative in second.relative_files
    }

    assert second_bytes == first_bytes
