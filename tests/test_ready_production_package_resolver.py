from pathlib import Path

import pytest

from services.presentation.production_package_resolver import (
    CanonicalProductionPackageResolver,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = {"paths": {kind: {"directory": str(ROOT)} for kind in ("overlays", "shaders")}}


def test_ready_nes_uses_canonical_platform_package():
    package = CanonicalProductionPackageResolver.resolve(
        config=CONFIG,
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
        config=CONFIG,
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


def test_genesis_ready_resolver_resolves_configured_package():
    """
    Resolve repository package fixtures independently of host-installed assets.

    Once the canonical assets exist, the READY platform must
    resolve the exact production package rather than retaining
    the pre-deployment missing-package expectation.
    """
    package = CanonicalProductionPackageResolver.resolve(
        config=CONFIG,
        platform_id="platform.sega.genesis",
        core_identity="genesis_plus_gx",
    )

    assert package.platform_id == "platform.sega.genesis"

    assert package.overlay == (
        str(ROOT) + "/"
        "retrovault/genesis/classic/"
        "RetroVault_Genesis_Classic.cfg"
    )

    assert package.shader == (
        str(ROOT) + "/"
        "retrovault/genesis/classic/"
        "RetroVault_Genesis_Classic_CRT.slangp"
    )

    assert package.runtime_descriptor == (
        str(ROOT) + "/"
        "retrovault/genesis/classic/"
        "RetroVault_Genesis_Classic.runtime.cfg"
    )

    assert package.production_manifest == (
        str(ROOT) + "/"
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
        312,
        80,
        1296,
        770,
    )

def test_unknown_platform_remains_outside_production_authority():
    assert (
        CanonicalProductionPackageResolver.resolve(
            config=CONFIG,
            platform_id="legacy.custom.platform",
            core_identity="fceumm",
        )
        is None
    )


def test_ready_platform_rejects_foreign_core():
    with pytest.raises(ValueError):
        CanonicalProductionPackageResolver.resolve(
            config=CONFIG,
            platform_id="platform.nintendo.nes",
            core_identity="snes9x",
        )
