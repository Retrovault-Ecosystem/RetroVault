import json
from pathlib import Path

from services.presentation.native_deployment import (
    NativeVisualDeploymentService,
)
from services.presentation.visual_catalog import (
    VisualAsset,
    VisualAssetSource,
    VisualAssetType,
)
from services.retroarch.overlay_runtime import (
    OverlayRuntimeConfig,
)
from services.retroarch.session_config import (
    RetroArchSessionConfig,
)


ROOT = Path(__file__).resolve().parents[1]

NES_OVERLAY = (
    ROOT
    / "retrovault"
    / "nes"
    / "classic"
    / "RetroVault_NES_Classic.cfg"
)

SNES_OVERLAY = (
    ROOT
    / "retrovault"
    / "snes"
    / "classic"
    / "RetroVault_SNES_Classic.cfg"
)

GENESIS_OVERLAY = (
    ROOT
    / "retrovault"
    / "genesis"
    / "classic"
    / "RetroVault_Genesis_Classic.cfg"
)


def _parse_cfg(payload):
    values = {}

    for raw_line in payload.splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#"):
            continue

        key, separator, value = line.partition("=")

        if not separator:
            continue

        values[key.strip()] = value.strip().strip('"')

    return values


def _effective_geometry(overlay):
    baseline = _parse_cfg(
        RetroArchSessionConfig.BASELINE
    )

    runtime = _parse_cfg(
        OverlayRuntimeConfig._runtime_descriptor_payload(
            overlay
        )
    )

    baseline.update(runtime)

    return baseline


def test_session_baseline_neutralizes_inherited_fixed_geometry():
    values = _parse_cfg(
        RetroArchSessionConfig.BASELINE
    )

    assert values["aspect_ratio_index"] == "0"
    assert values["video_force_aspect"] == "true"
    assert values["video_aspect_ratio"] == "-1.000000"
    assert values["video_aspect_ratio_auto"] == "true"
    assert values["video_scale_integer"] == "false"

    assert values["video_viewport_bias_x"] == "0.500000"
    assert values["video_viewport_bias_y"] == "0.500000"

    assert values["custom_viewport_x"] == "0"
    assert values["custom_viewport_y"] == "0"
    assert values["custom_viewport_width"] == "0"
    assert values["custom_viewport_height"] == "0"

    assert values["video_crop_overscan"] == "false"


def test_nes_package_overrides_neutral_session_geometry():
    values = _effective_geometry(
        NES_OVERLAY
    )

    assert values["aspect_ratio_index"] == "22"
    assert values["video_aspect_ratio_auto"] == "false"
    assert values["custom_viewport_x"] == "355"
    assert values["custom_viewport_y"] == "100"
    assert values["custom_viewport_width"] == "1206"
    assert values["custom_viewport_height"] == "762"


def test_snes_package_preserves_established_fixed_geometry():
    # SNES predates the stricter OverlayRuntimeConfig allow-list and its
    # protected runtime descriptor contains additional established
    # settings such as video_fullscreen. Verify the package directly
    # rather than changing that production authority for this A.7 test.
    runtime = (
        SNES_OVERLAY
        .with_suffix(".runtime.cfg")
        .read_text(encoding="utf-8")
    )
    values = _parse_cfg(runtime)

    assert values["aspect_ratio_index"] == "23"
    assert values["video_scale_integer"] == "false"
    assert values["video_viewport_bias_x"] == "0.500000"
    assert values["video_viewport_bias_y"] == "0.239057239"
    assert values["custom_viewport_width"] == "1044"
    assert values["custom_viewport_height"] == "783"

    baseline = _parse_cfg(
        RetroArchSessionConfig.BASELINE
    )
    baseline.update(values)

    assert baseline["aspect_ratio_index"] == "23"
    assert baseline["custom_viewport_width"] == "1044"
    assert baseline["custom_viewport_height"] == "783"


def test_genesis_retains_core_driven_dynamic_geometry():
    values = _effective_geometry(
        GENESIS_OVERLAY
    )

    runtime = (
        GENESIS_OVERLAY
        .with_suffix(".runtime.cfg")
        .read_text(encoding="utf-8")
    )

    assert values["video_force_aspect"] == "true"
    assert values["video_aspect_ratio_auto"] == "true"
    assert values["video_scale_integer"] == "false"
    assert values["video_crop_overscan"] == "false"

    # The baseline neutralizes any inherited custom viewport. Genesis
    # itself must not replace that neutral state with fixed coordinates.
    assert values["custom_viewport_x"] == "0"
    assert values["custom_viewport_y"] == "0"
    assert values["custom_viewport_width"] == "0"
    assert values["custom_viewport_height"] == "0"

    forbidden = (
        "aspect_ratio_index",
        "video_aspect_ratio =",
        "custom_viewport_x",
        "custom_viewport_y",
        "custom_viewport_width",
        "custom_viewport_height",
        "video_viewport_bias_x",
        "video_viewport_bias_y",
    )

    for token in forbidden:
        assert token not in runtime


def test_native_deployment_carries_production_manifest(tmp_path):
    repository_root = tmp_path / "repository"
    overlay_root = tmp_path / "installed"

    package = (
        repository_root
        / "retrovault"
        / "test-system"
        / "classic"
    )
    package.mkdir(parents=True)

    descriptor = package / "Example.cfg"
    image = package / "Example.png"
    runtime = package / "Example.runtime.cfg"
    shader = package / "Example.shader.cfg"
    manifest = package / "Example.production.json"

    descriptor.write_text(
        'overlays = "1"\n'
        'overlay0_overlay = "Example.png"\n'
        'overlay0_full_screen = "true"\n'
        'overlay0_descs = "0"\n',
        encoding="utf-8",
    )
    image.write_bytes(b"test-image")
    runtime.write_text(
        'video_force_aspect = "true"\n',
        encoding="utf-8",
    )
    shader.write_text(
        'video_shader_enable = "true"\n',
        encoding="utf-8",
    )
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "platform_id": "platform.test.system",
            }
        ),
        encoding="utf-8",
    )

    asset = VisualAsset(
        id="test.native.production.manifest",
        display_name="Test Native Production Manifest",
        asset_type=VisualAssetType.OVERLAY,
        source=VisualAssetSource.RVV_NATIVE,
        reference=(
            "retro-vault://overlays/"
            "retrovault/test-system/classic/Example.cfg"
        ),
        author="RetroVault",
    )

    service = NativeVisualDeploymentService(
        repository_root=repository_root,
        overlay_root=overlay_root,
    )

    plan = service.plan(asset)

    assert manifest in plan.source_files

    deployment = service.deploy(asset)

    deployed_manifest = (
        deployment.destination_directory
        / manifest.name
    )

    assert deployed_manifest.is_file()
    assert deployed_manifest.read_bytes() == manifest.read_bytes()
