from pathlib import Path

from services.presentation.master_profile import (
    MasterPresentationClass,
)
from services.presentation.platform_policy import (
    PlatformPresentationPolicyRegistry,
    PlatformPresentationPolicyState,
)
from services.presentation.production_package import (
    ProductionPresentationPackageValidator,
)
from services.presentation.production_package_resolver import (
    CanonicalProductionPackageResolver,
)


ROOT = Path(__file__).resolve().parents[1]

GENESIS_DIR = (
    ROOT
    / "retrovault"
    / "genesis"
    / "classic"
)

GENESIS_OVERLAY = (
    GENESIS_DIR
    / "RetroVault_Genesis_Classic.cfg"
)

GENESIS_SHADER = (
    GENESIS_DIR
    / "RetroVault_Genesis_Classic_CRT.slangp"
)


def test_genesis_policy_is_ready_and_system_level():
    registry = PlatformPresentationPolicyRegistry

    assert (
        registry.state_for(
            "platform.sega.genesis"
        )
        is PlatformPresentationPolicyState.READY
    )

    policy = registry.resolve(
        platform_id="platform.sega.genesis",
        core_identity="genesis_plus_gx",
    )

    assert policy is not None

    assert policy.platform_id == (
        "platform.sega.genesis"
    )

    assert policy.core_identities == (
        "genesis_plus_gx",
    )

    assert dict(policy.core_options) == {}

    assert (
        policy.master_presentation_class
        is MasterPresentationClass.CLASSIC_4_3
    )

    payload = repr(policy).lower()

    for forbidden in (
        "game_id",
        "rom",
        "title",
        "filename",
        "archive",
        "custom_viewport",
        "330",
        "126",
        "1260",
        "827",
    ):
        assert forbidden not in payload


def test_genesis_core_cannot_borrow_other_platform_policy():
    registry = PlatformPresentationPolicyRegistry

    for foreign_platform in (
        "platform.nintendo.nes",
        "platform.nintendo.snes",
        "platform.sega.game.gear",
        "platform.sega.master.system",
        "platform.sega.sg1000",
    ):
        try:
            registry.resolve(
                platform_id=foreign_platform,
                core_identity="genesis_plus_gx",
            )
        except ValueError:
            pass
        else:
            if (
                registry.state_for(
                    foreign_platform
                )
                is PlatformPresentationPolicyState.READY
            ):
                raise AssertionError(
                    "READY foreign platform borrowed "
                    "Genesis presentation policy."
                )


def test_genesis_repository_package_validates_semantically():
    package = (
        ProductionPresentationPackageValidator
        .validate(
            platform_id="platform.sega.genesis",
            core_identity="genesis_plus_gx",
            overlay=str(GENESIS_OVERLAY),
            shader=str(GENESIS_SHADER),
        )
    )

    assert package is not None

    assert package.platform_id == (
        "platform.sega.genesis"
    )

    assert Path(
        package.runtime_descriptor
    ).name == (
        "RetroVault_Genesis_Classic.runtime.cfg"
    )

    assert Path(
        package.production_manifest
    ).name == (
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

    profile = glass.as_master_profile(
        profile_class=(
            MasterPresentationClass.CLASSIC_4_3
        ),
    )

    geometry = profile.contain_aspect(
        1.524,
        1.0,
    )

    assert (
        geometry.x,
        geometry.y,
        geometry.width,
        geometry.height,
    ) == (
        330,
        126,
        1260,
        827,
    )


def test_genesis_canonical_mapping_uses_own_asset_roots():
    assets = (
        CanonicalProductionPackageResolver
        ._ASSETS[
            "platform.sega.genesis"
        ]
    )

    assert (
        "/retrovault/genesis/classic/"
        in assets.overlay
    )

    assert (
        "/retrovault/genesis/classic/"
        in assets.shader
    )

    assert assets.overlay.endswith(
        "/RetroVault_Genesis_Classic.cfg"
    )

    assert assets.shader.endswith(
        "/RetroVault_Genesis_Classic_CRT.slangp"
    )


def test_genesis_static_runtime_descriptor_remains_geometry_neutral():
    runtime = (
        GENESIS_DIR
        / "RetroVault_Genesis_Classic.runtime.cfg"
    ).read_text(
        encoding="utf-8"
    )

    required = (
        'video_force_aspect = "true"',
        'video_aspect_ratio_auto = "true"',
        'video_crop_overscan = "false"',
        'video_scale_integer = "false"',
    )

    for token in required:
        assert token in runtime

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
