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


def test_genesis_ready_resolver_resolves_deployed_package():
    """
    A.3-N.5-D deploys the qualified Genesis production package.

    Once the canonical assets exist, the READY platform must
    resolve the exact production package rather than retaining
    the pre-deployment missing-package expectation.
    """
    package = CanonicalProductionPackageResolver.resolve(
        platform_id="platform.sega.genesis",
        core_identity="genesis_plus_gx",
    )

    assert package.platform_id == "platform.sega.genesis"

    assert package.overlay == (
        "/opt/retropie/configs/all/retroarch/overlays/"
        "retrovault/genesis/classic/"
        "RetroVault_Genesis_Classic.cfg"
    )

    assert package.shader == (
        "/opt/retropie/configs/all/retroarch/shaders/"
        "retrovault/genesis/classic/"
        "RetroVault_Genesis_Classic_CRT.slangp"
    )

    assert package.runtime_descriptor == (
        "/opt/retropie/configs/all/retroarch/overlays/"
        "retrovault/genesis/classic/"
        "RetroVault_Genesis_Classic.runtime.cfg"
    )

    assert package.production_manifest == (
        "/opt/retropie/configs/all/retroarch/overlays/"
        "retrovault/genesis/classic/"
        "RetroVault_Genesis_Classic.production.json"
    )

    glass = package.fixed_glass()

    assert (
        glass.canvas_width,
        glass.canvas_height,
        glass.x,
        glass.y,
        glass.width,
        glass.height,
    ) == (
        1920,
        1080,
        330,
        90,
        1260,
        900,
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
