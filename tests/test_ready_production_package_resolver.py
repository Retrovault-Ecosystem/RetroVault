import pytest

from services.presentation.production_package_resolver import (
    CanonicalProductionPackageResolver,
)


def test_ready_nes_uses_canonical_platform_package():
    package = CanonicalProductionPackageResolver.resolve(
        platform_id="platform.nintendo.nes",
        core_identity="fceumm",
    )

    assert package is not None
    assert package.platform_id == "platform.nintendo.nes"
    assert package.overlay.endswith(
        "/retrovault/nes/classic/"
        "RetroVault_NES_Classic.cfg"
    )
    assert package.shader.endswith(
        "/retrovault/nes/classic/"
        "RetroVault_NES_Classic_CRT.slangp"
    )


def test_ready_snes_uses_canonical_platform_package():
    package = CanonicalProductionPackageResolver.resolve(
        platform_id="platform.nintendo.snes",
        core_identity="snes9x",
    )

    assert package is not None
    assert package.platform_id == "platform.nintendo.snes"
    assert package.overlay.endswith(
        "/retrovault/snes/classic/"
        "RetroVault_SNES_Classic.cfg"
    )
    assert package.shader.endswith(
        "/retrovault/snes/classic/"
        "RetroVault_SNES_Classic_CRT.slangp"
    )


def test_genesis_remains_fail_closed():
    with pytest.raises(
        ValueError,
        match="not configured",
    ):
        CanonicalProductionPackageResolver.resolve(
            platform_id="platform.sega.genesis",
            core_identity="genesis_plus_gx",
        )


def test_unknown_platform_remains_outside_production_authority():
    assert (
        CanonicalProductionPackageResolver.resolve(
            platform_id="legacy.custom.platform",
            core_identity="fceumm",
        )
        is None
    )


def test_ready_platform_rejects_foreign_core():
    with pytest.raises(ValueError):
        CanonicalProductionPackageResolver.resolve(
            platform_id="platform.nintendo.nes",
            core_identity="snes9x",
        )
