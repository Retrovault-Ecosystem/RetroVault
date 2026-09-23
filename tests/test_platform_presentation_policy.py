import pytest

from services.presentation.platform_policy import (
    PlatformPresentationPolicy,
    PlatformPresentationPolicyRegistry,
)
from services.retroarch.core_options_runtime import (
    CoreOptionsRuntimeConfig,
)


def test_registry_contains_explicit_nes_and_snes_platforms():
    policies = {
        policy.platform_id: policy
        for policy in (
            PlatformPresentationPolicyRegistry.all()
        )
    }

    assert set(policies) == {
        "platform.nintendo.nes",
        "platform.nintendo.snes",
    }

    assert (
        policies[
            "platform.nintendo.nes"
        ].core_identities
        == ("fceumm",)
    )

    assert (
        policies[
            "platform.nintendo.snes"
        ].core_identities
        == ("snes9x",)
    )


def test_nes_policy_preserves_complete_fceumm_source():
    policy = (
        PlatformPresentationPolicyRegistry.resolve(
            platform_id="platform.nintendo.nes",
            core_identity="fceumm",
        )
    )

    assert policy is not None

    assert dict(
        policy.core_options
    ) == {
        "fceumm_overscan_h_left": "0",
        "fceumm_overscan_h_right": "0",
        "fceumm_overscan_v_top": "0",
        "fceumm_overscan_v_bottom": "0",
    }


def test_snes_policy_does_not_redefine_approved_geometry():
    policy = (
        PlatformPresentationPolicyRegistry.resolve(
            platform_id="platform.nintendo.snes",
            core_identity="snes9x",
        )
    )

    assert policy is not None
    assert dict(policy.core_options) == {}

    serialized = repr(policy)

    for forbidden in (
        "custom_viewport",
        "viewport_bias",
        "aspect_ratio_index",
        "1044",
        "783",
        "0.239057239",
    ):
        assert forbidden not in serialized


def test_platform_policy_contains_no_game_identity():
    for policy in (
        PlatformPresentationPolicyRegistry.all()
    ):
        payload = repr(
            policy
        ).lower()

        for forbidden in (
            "game_id",
            "rom",
            "title",
            "filename",
            "archive",
        ):
            assert forbidden not in payload


def test_unknown_platform_falls_back_without_foreign_policy():
    assert (
        PlatformPresentationPolicyRegistry.for_platform(
            "platform.sega.genesis"
        )
        is None
    )

    assert (
        PlatformPresentationPolicyRegistry.resolve(
            platform_id="platform.sega.genesis",
        )
        is None
    )


def test_unknown_core_falls_back_without_foreign_policy():
    assert (
        PlatformPresentationPolicyRegistry.for_core(
            "genesis_plus_gx"
        )
        is None
    )

    assert (
        PlatformPresentationPolicyRegistry.resolve(
            core_identity="genesis_plus_gx",
        )
        is None
    )


def test_platform_core_mismatch_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "Platform/core presentation "
            "policy mismatch"
        ),
    ):
        PlatformPresentationPolicyRegistry.resolve(
            platform_id="platform.nintendo.nes",
            core_identity="snes9x",
        )


def test_policy_is_immutable():
    policy = (
        PlatformPresentationPolicyRegistry.for_platform(
            "platform.nintendo.nes"
        )
    )

    assert policy is not None

    with pytest.raises(
        TypeError,
    ):
        policy.core_options[
            "fceumm_overscan_h_left"
        ] = "8"


def test_policy_rejects_invalid_platform_identity():
    with pytest.raises(
        ValueError,
        match="Platform ID",
    ):
        PlatformPresentationPolicy(
            platform_id="",
            core_identities=(
                "example",
            ),
            core_options={},
        )


def test_policy_rejects_duplicate_core_identity():
    with pytest.raises(
        ValueError,
        match="unique",
    ):
        PlatformPresentationPolicy(
            platform_id="platform.test",
            core_identities=(
                "example",
                "EXAMPLE",
            ),
            core_options={},
        )


def test_core_options_runtime_preserves_existing_fceumm_api():
    assert (
        CoreOptionsRuntimeConfig.policy_for(
            "/tmp/fceumm_libretro.so"
        )
        == {
            "fceumm_overscan_h_left": "0",
            "fceumm_overscan_h_right": "0",
            "fceumm_overscan_v_top": "0",
            "fceumm_overscan_v_bottom": "0",
        }
    )


def test_core_options_runtime_can_validate_platform_core_pair():
    assert (
        CoreOptionsRuntimeConfig.policy_for(
            "/tmp/fceumm_libretro.so",
            platform_id="platform.nintendo.nes",
        )
        == {
            "fceumm_overscan_h_left": "0",
            "fceumm_overscan_h_right": "0",
            "fceumm_overscan_v_top": "0",
            "fceumm_overscan_v_bottom": "0",
        }
    )


def test_snes_core_options_runtime_is_explicitly_geometry_neutral():
    assert (
        CoreOptionsRuntimeConfig.policy_for(
            "/tmp/snes9x_libretro.so",
            platform_id="platform.nintendo.snes",
        )
        == {}
    )


def test_core_options_runtime_rejects_cross_platform_core_pair():
    with pytest.raises(
        ValueError,
        match=(
            "Platform/core presentation "
            "policy mismatch"
        ),
    ):
        CoreOptionsRuntimeConfig.policy_for(
            "/tmp/snes9x_libretro.so",
            platform_id="platform.nintendo.nes",
        )
