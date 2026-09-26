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
            / "retrovault"
            / relative
        )

        assert destination.is_file()
        assert (
            destination.read_bytes()
            == source.read_bytes()
        )

    deployed_preset = (
        plan.shader_root
        / "retrovault"
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
            / "retrovault"
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
            / "retrovault"
            / relative
        ).read_bytes()
        for relative in second.relative_files
    }

    assert second_bytes == first_bytes


def _synthetic_shader_service(
    tmp_path,
    *,
    parent_text,
    child_text=None,
    shader_text=None,
):
    repository = (
        tmp_path
        / "repository"
    )

    package = (
        repository
        / "retrovault"
        / "audit"
    )

    package.mkdir(
        parents=True
    )

    (
        package
        / "parent.slangp"
    ).write_text(
        parent_text,
        encoding="utf-8",
    )

    if child_text is not None:
        (
            package
            / "child.slangp"
        ).write_text(
            child_text,
            encoding="utf-8",
        )

    if shader_text is not None:
        (
            package
            / "pass.slang"
        ).write_text(
            shader_text,
            encoding="utf-8",
        )

    asset = VisualAsset(
        id="rvv.shader.audit",
        display_name="Audit Shader",
        asset_type=VisualAssetType.SHADER,
        source=VisualAssetSource.RVV_NATIVE,
        reference=(
            "retro-vault://shaders/"
            "audit/parent.slangp"
        ),
        author="RetroVault",
    )

    service = NativeShaderDeploymentService(
        repository_root=repository,
        shader_root=(
            tmp_path
            / "installed-shaders"
        ),
    )

    return service, asset


def test_shader_plan_recursively_preserves_reference_directive(
    tmp_path,
):
    service, asset = (
        _synthetic_shader_service(
            tmp_path,
            parent_text=(
                '#reference "child.slangp"\n'
            ),
            child_text=(
                'shaders = "1"\n'
                'shader0 = "pass.slang"\n'
            ),
            shader_text=(
                "#version 450\n"
                "void main() {}\n"
            ),
        )
    )

    plan = service.plan(
        asset
    )

    assert set(
        plan.relative_files
    ) == {
        Path("audit/parent.slangp"),
        Path("audit/child.slangp"),
        Path("audit/pass.slang"),
    }


def test_shader_plan_rejects_runtime_token_dependency(
    tmp_path,
):
    service, asset = (
        _synthetic_shader_service(
            tmp_path,
            parent_text=(
                'shader0 = "$PRESET$/pass.slang"\n'
            ),
        )
    )

    with pytest.raises(
        ValueError,
        match="statically resolvable",
    ):
        service.plan(
            asset
        )


def test_shader_deployment_does_not_clone_unrelated_shader_tree(
    tmp_path,
    monkeypatch,
):
    service, asset = (
        _synthetic_shader_service(
            tmp_path,
            parent_text=(
                'shader0 = "pass.slang"\n'
            ),
            shader_text=(
                "#version 450\n"
                "void main() {}\n"
            ),
        )
    )

    unrelated = (
        service.shader_root
        / "large-existing-pack"
        / "keep.slang"
    )

    unrelated.parent.mkdir(
        parents=True
    )

    unrelated.write_text(
        "keep\n",
        encoding="utf-8",
    )

    def reject_copytree(
        *args,
        **kwargs,
    ):
        raise AssertionError(
            "Whole-tree copy is forbidden."
        )

    monkeypatch.setattr(
        "services.presentation."
        "native_shader_deployment."
        "shutil.copytree",
        reject_copytree,
    )

    service.deploy(
        asset
    )

    assert unrelated.read_text(
        encoding="utf-8"
    ) == "keep\n"


def test_shader_deployment_rolls_back_only_touched_targets(
    tmp_path,
    monkeypatch,
):
    service, asset = (
        _synthetic_shader_service(
            tmp_path,
            parent_text=(
                'shader0 = "pass.slang"\n'
            ),
            shader_text=(
                "#version 450\n"
                "void main() {}\n"
            ),
        )
    )

    plan = service.plan(
        asset
    )

    old_bytes = {}

    for relative in plan.relative_files:
        destination = (
            service.shader_root
            / relative
        )

        destination.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        payload = (
            b"old-"
            + relative.as_posix().encode(
                "utf-8"
            )
        )

        destination.write_bytes(
            payload
        )

        old_bytes[
            relative
        ] = payload

    unrelated = (
        service.shader_root
        / "unrelated"
        / "keep.slang"
    )

    unrelated.parent.mkdir(
        parents=True
    )

    unrelated.write_bytes(
        b"unrelated"
    )

    real_replace = (
        __import__("os").replace
    )

    calls = {
        "count": 0,
    }

    def failing_replace(
        source,
        destination,
    ):
        source_path = Path(
            source
        )

        if (
            ".retrovault-shader-staging-"
            in source_path.as_posix()
        ):
            calls["count"] += 1

            if calls["count"] == 2:
                raise OSError(
                    "injected deployment failure"
                )

        return real_replace(
            source,
            destination,
        )

    monkeypatch.setattr(
        "services.presentation."
        "native_shader_deployment."
        "os.replace",
        failing_replace,
    )

    with pytest.raises(
        OSError,
        match="injected deployment failure",
    ):
        service.deploy(
            asset
        )

    for relative, payload in (
        old_bytes.items()
    ):
        assert (
            service.shader_root
            / relative
        ).read_bytes() == payload

    assert unrelated.read_bytes() == (
        b"unrelated"
    )


def test_shader_plan_accepts_external_dependency_bounded_by_shader_root(
    tmp_path,
):
    repository_root = tmp_path / "repo"
    package_root = repository_root / "retrovault"
    shader_root = tmp_path / "shaders"

    preset = (
        package_root
        / "nes"
        / "classic"
        / "preset.slangp"
    )
    preset.parent.mkdir(parents=True)

    external = (
        shader_root
        / "shaders_slang"
        / "base.slangp"
    )
    external.parent.mkdir(parents=True)
    external.write_text(
        'shaders = "0"\n',
        encoding="utf-8",
    )

    preset.write_text(
        '#reference "../../../shaders_slang/base.slangp"\n',
        encoding="utf-8",
    )

    asset = VisualAsset(
        id="rvv.shader.external.bounded",
        display_name="Bounded External",
        asset_type=VisualAssetType.SHADER,
        source=VisualAssetSource.RVV_NATIVE,
        reference=(
            "retro-vault://shaders/"
            "nes/classic/preset.slangp"
        ),
        author="RetroVault",
        attribution="RetroVault",
    )

    service = NativeShaderDeploymentService(
        repository_root=repository_root,
        shader_root=shader_root,
    )

    plan = service.plan(asset)

    assert plan.source_files == (
        preset.resolve(),
    )
    assert plan.relative_files == (
        Path("nes/classic/preset.slangp"),
    )


def test_shader_plan_rejects_external_dependency_escape_from_shader_root(
    tmp_path,
):
    repository_root = tmp_path / "repo"
    package_root = repository_root / "retrovault"
    shader_root = tmp_path / "shaders"

    preset = (
        package_root
        / "nes"
        / "classic"
        / "preset.slangp"
    )
    preset.parent.mkdir(parents=True)

    preset.write_text(
        '#reference "../../../../outside/base.slangp"\n',
        encoding="utf-8",
    )

    asset = VisualAsset(
        id="rvv.shader.external.escape",
        display_name="External Escape",
        asset_type=VisualAssetType.SHADER,
        source=VisualAssetSource.RVV_NATIVE,
        reference=(
            "retro-vault://shaders/"
            "nes/classic/preset.slangp"
        ),
        author="RetroVault",
        attribution="RetroVault",
    )

    service = NativeShaderDeploymentService(
        repository_root=repository_root,
        shader_root=shader_root,
    )

    import pytest

    with pytest.raises(
        ValueError,
        match="escaped the configured shader root",
    ):
        service.plan(asset)


def test_shader_plan_requires_external_dependency_to_be_installed(
    tmp_path,
):
    repository_root = tmp_path / "repo"
    package_root = repository_root / "retrovault"
    shader_root = tmp_path / "shaders"

    preset = (
        package_root
        / "nes"
        / "classic"
        / "preset.slangp"
    )
    preset.parent.mkdir(parents=True)

    preset.write_text(
        '#reference "../../../shaders_slang/missing.slangp"\n',
        encoding="utf-8",
    )

    asset = VisualAsset(
        id="rvv.shader.external.missing",
        display_name="Missing External",
        asset_type=VisualAssetType.SHADER,
        source=VisualAssetSource.RVV_NATIVE,
        reference=(
            "retro-vault://shaders/"
            "nes/classic/preset.slangp"
        ),
        author="RetroVault",
        attribution="RetroVault",
    )

    service = NativeShaderDeploymentService(
        repository_root=repository_root,
        shader_root=shader_root,
    )

    import pytest

    with pytest.raises(
        ValueError,
        match="external dependency does not exist",
    ):
        service.plan(asset)


def test_shader_plan_uses_retrovault_deployment_namespace(
    tmp_path,
):
    repository_root = tmp_path / "repo"
    shader_root = tmp_path / "shaders"

    preset = (
        repository_root
        / "retrovault"
        / "nes"
        / "classic"
        / "preset.slangp"
    )
    preset.parent.mkdir(parents=True)
    preset.write_text(
        'shaders = "0"\n',
        encoding="utf-8",
    )

    asset = VisualAsset(
        id="rvv.shader.namespace",
        display_name="Namespace",
        asset_type=VisualAssetType.SHADER,
        source=VisualAssetSource.RVV_NATIVE,
        reference=(
            "retro-vault://shaders/"
            "nes/classic/preset.slangp"
        ),
        author="RetroVault",
        attribution="RetroVault",
    )

    service = NativeShaderDeploymentService(
        repository_root=repository_root,
        shader_root=shader_root,
    )

    plan = service.plan(asset)

    assert plan.destination_preset == (
        shader_root
        / "retrovault"
        / "nes"
        / "classic"
        / "preset.slangp"
    ).resolve()


def test_shader_deploy_writes_only_to_retrovault_namespace(
    tmp_path,
):
    repository_root = tmp_path / "repo"
    shader_root = tmp_path / "shaders"

    preset = (
        repository_root
        / "retrovault"
        / "nes"
        / "classic"
        / "preset.slangp"
    )
    shader = (
        repository_root
        / "retrovault"
        / "shaders"
        / "retrovault"
        / "nes"
        / "classic"
        / "pass.slang"
    )

    preset.parent.mkdir(parents=True)
    shader.parent.mkdir(parents=True)

    preset.write_text(
        'shaders = "1"\n'
        'shader0 = "../../shaders/retrovault/nes/classic/pass.slang"\n',
        encoding="utf-8",
    )
    shader.write_text(
        "// pass\n",
        encoding="utf-8",
    )

    asset = VisualAsset(
        id="rvv.shader.namespace.deploy",
        display_name="Namespace Deploy",
        asset_type=VisualAssetType.SHADER,
        source=VisualAssetSource.RVV_NATIVE,
        reference=(
            "retro-vault://shaders/"
            "nes/classic/preset.slangp"
        ),
        author="RetroVault",
        attribution="RetroVault",
    )

    service = NativeShaderDeploymentService(
        repository_root=repository_root,
        shader_root=shader_root,
    )

    plan = service.deploy(asset)

    expected_preset = (
        shader_root
        / "retrovault"
        / "nes"
        / "classic"
        / "preset.slangp"
    )
    expected_shader = (
        shader_root
        / "retrovault"
        / "shaders"
        / "retrovault"
        / "nes"
        / "classic"
        / "pass.slang"
    )

    assert plan.destination_preset == expected_preset.resolve()
    assert expected_preset.read_bytes() == preset.read_bytes()
    assert expected_shader.read_bytes() == shader.read_bytes()

    assert not (
        shader_root
        / "nes"
        / "classic"
        / "preset.slangp"
    ).exists()

    assert not (
        shader_root
        / "shaders"
        / "retrovault"
        / "nes"
        / "classic"
        / "pass.slang"
    ).exists()
