from pathlib import Path

import pytest

from services.presentation.production_package import (
    ProductionPresentationPackage,
    ProductionPresentationPackageValidator,
)


ROOT = Path(__file__).resolve().parents[1]

NES_OVERLAY = (
    ROOT
    / "retrovault"
    / "nes"
    / "classic"
    / "RetroVault_NES_Classic.cfg"
)

NES_SHADER = (
    ROOT
    / "retrovault"
    / "nes"
    / "classic"
    / "RetroVault_NES_Classic_CRT.slangp"
)

SNES_OVERLAY = (
    ROOT
    / "retrovault"
    / "snes"
    / "classic"
    / "RetroVault_SNES_Classic.cfg"
)

SNES_SHADER = (
    ROOT
    / "retrovault"
    / "snes"
    / "classic"
    / "RetroVault_SNES_Classic_CRT.slangp"
)


def validate(
    platform_id,
    core_identity,
    overlay,
    shader,
):
    return (
        ProductionPresentationPackageValidator
        .validate(
            platform_id=platform_id,
            core_identity=core_identity,
            overlay=str(overlay),
            shader=str(shader),
        )
    )


def test_nes_ready_package_is_complete():
    package = validate(
        "platform.nintendo.nes",
        "fceumm",
        NES_OVERLAY,
        NES_SHADER,
    )

    assert isinstance(
        package,
        ProductionPresentationPackage,
    )

    assert (
        package.platform_id
        == "platform.nintendo.nes"
    )

    assert Path(
        package.runtime_descriptor
    ).name == (
        "RetroVault_NES_Classic.runtime.cfg"
    )

    assert Path(
        package.production_manifest
    ).name == (
        "RetroVault_NES_Classic.production.json"
    )


def test_snes_ready_package_is_complete():
    package = validate(
        "platform.nintendo.snes",
        "snes9x",
        SNES_OVERLAY,
        SNES_SHADER,
    )

    assert isinstance(
        package,
        ProductionPresentationPackage,
    )

    assert (
        package.platform_id
        == "platform.nintendo.snes"
    )

    assert Path(
        package.runtime_descriptor
    ).name == (
        "RetroVault_SNES_Classic.runtime.cfg"
    )

    assert Path(
        package.production_manifest
    ).name == (
        "RetroVault_SNES_Classic.production.json"
    )


@pytest.mark.parametrize(
    "platform_id",
    (
        "platform.sega.genesis",
        "platform.nintendo.n64",
        "platform.arcade",
    ),
)
def test_unconfigured_platform_fails_before_package_borrow(
    platform_id,
):
    with pytest.raises(
        ValueError,
        match="not configured",
    ):
        validate(
            platform_id,
            "fceumm",
            NES_OVERLAY,
            NES_SHADER,
        )


def test_nes_cannot_use_snes_core():
    with pytest.raises(ValueError):
        validate(
            "platform.nintendo.nes",
            "snes9x",
            NES_OVERLAY,
            NES_SHADER,
        )


def test_snes_cannot_use_nes_core():
    with pytest.raises(ValueError):
        validate(
            "platform.nintendo.snes",
            "fceumm",
            SNES_OVERLAY,
            SNES_SHADER,
        )


def test_nes_cannot_use_snes_package():
    with pytest.raises(ValueError):
        validate(
            "platform.nintendo.nes",
            "fceumm",
            SNES_OVERLAY,
            SNES_SHADER,
        )


def test_snes_cannot_use_nes_package():
    with pytest.raises(ValueError):
        validate(
            "platform.nintendo.snes",
            "snes9x",
            NES_OVERLAY,
            NES_SHADER,
        )


def test_cross_package_overlay_shader_mix_is_rejected():
    with pytest.raises(
        ValueError,
        match="same package",
    ):
        validate(
            "platform.nintendo.nes",
            "fceumm",
            NES_OVERLAY,
            SNES_SHADER,
        )


def test_ready_platform_requires_overlay():
    with pytest.raises(
        ValueError,
        match="missing its production overlay",
    ):
        (
            ProductionPresentationPackageValidator
            .validate(
                platform_id="platform.nintendo.nes",
                core_identity="fceumm",
                overlay="",
                shader=str(NES_SHADER),
            )
        )


def test_ready_platform_requires_shader():
    with pytest.raises(
        ValueError,
        match="missing its production shader",
    ):
        (
            ProductionPresentationPackageValidator
            .validate(
                platform_id="platform.nintendo.nes",
                core_identity="fceumm",
                overlay=str(NES_OVERLAY),
                shader="",
            )
        )


def test_unknown_platform_preserves_safe_fallback():
    result = (
        ProductionPresentationPackageValidator
        .validate(
            platform_id="platform.unknown.test",
            core_identity="fceumm",
            overlay=str(NES_OVERLAY),
            shader=str(NES_SHADER),
        )
    )

    assert result is None


def test_omitted_platform_preserves_legacy_path():
    result = (
        ProductionPresentationPackageValidator
        .validate(
            platform_id=None,
            core_identity="fceumm",
            overlay=str(NES_OVERLAY),
            shader=str(NES_SHADER),
        )
    )

    assert result is None


def test_non_string_platform_preserves_legacy_path():
    result = (
        ProductionPresentationPackageValidator
        .validate(
            platform_id=object(),
            core_identity="fceumm",
            overlay=str(NES_OVERLAY),
            shader=str(NES_SHADER),
        )
    )

    assert result is None


def test_package_validator_does_not_own_physical_geometry():
    fields = set(
        ProductionPresentationPackage.__dataclass_fields__
    )

    forbidden = {
        "aspect_ratio_index",
        "video_force_aspect",
        "video_scale_integer",
        "video_viewport_bias_x",
        "video_viewport_bias_y",
        "custom_viewport_x",
        "custom_viewport_y",
        "custom_viewport_width",
        "custom_viewport_height",
        "video_aspect_ratio",
        "video_aspect_ratio_auto",
        "video_crop_overscan",
    }

    assert fields.isdisjoint(
        forbidden
    )
