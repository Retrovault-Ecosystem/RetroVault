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


def test_every_canonical_rvdb_platform_has_explicit_policy_state():
    from pathlib import Path
    import json

    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
        PlatformPresentationPolicyState,
    )

    bundle = json.loads(
        Path(
            "data/rvdb/rvdb.bundle.json"
        ).read_text(
            encoding="utf-8"
        )
    )

    platform_ids = set()

    def walk(value):
        if isinstance(value, dict):
            for key in (
                "platform_id",
                "id",
            ):
                candidate = value.get(key)

                if (
                    isinstance(candidate, str)
                    and candidate.startswith(
                        "platform."
                    )
                ):
                    platform_ids.add(
                        candidate
                    )

            for child in value.values():
                walk(child)

        elif isinstance(value, list):
            for child in value:
                walk(child)

    walk(bundle)

    assert (
        set(
            PlatformPresentationPolicyRegistry
            .canonical_platform_ids()
        )
        == platform_ids
    )

    for platform_id in platform_ids:
        assert (
            PlatformPresentationPolicyRegistry
            .state_for(platform_id)
            in {
                PlatformPresentationPolicyState.READY,
                PlatformPresentationPolicyState.UNCONFIGURED,
            }
        )


def test_only_validated_nes_and_snes_are_ready():
    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
    )

    assert set(
        PlatformPresentationPolicyRegistry
        .ready_platform_ids()
    ) == {
        "platform.nintendo.nes",
        "platform.nintendo.snes",
    }


def test_remaining_canonical_platforms_are_explicitly_unconfigured():
    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
    )

    unconfigured = set(
        PlatformPresentationPolicyRegistry
        .unconfigured_platform_ids()
    )

    assert len(unconfigured) == 24

    assert (
        "platform.sega.genesis"
        in unconfigured
    )

    assert (
        "platform.nintendo.n64"
        in unconfigured
    )

    assert (
        "platform.arcade"
        in unconfigured
    )


def test_unconfigured_platform_without_core_preserves_safe_none_fallback():
    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
    )

    for platform_id in (
        PlatformPresentationPolicyRegistry
        .unconfigured_platform_ids()
    ):
        assert (
            PlatformPresentationPolicyRegistry
            .resolve(
                platform_id=platform_id,
            )
            is None
        )


def test_unconfigured_platform_cannot_borrow_known_core_policy():
    import pytest

    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
    )

    for platform_id in (
        PlatformPresentationPolicyRegistry
        .unconfigured_platform_ids()
    ):
        for core_identity in (
            "fceumm",
            "snes9x",
        ):
            with pytest.raises(
                ValueError
            ):
                (
                    PlatformPresentationPolicyRegistry
                    .resolve(
                        platform_id=platform_id,
                        core_identity=core_identity,
                    )
                )


def test_unknown_platform_without_core_preserves_safe_none_fallback():
    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
    )

    assert (
        PlatformPresentationPolicyRegistry
        .resolve(
            platform_id="platform.unknown.test",
        )
        is None
    )


def test_unknown_platform_cannot_borrow_known_core_policy():
    import pytest

    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
    )

    with pytest.raises(ValueError):
        (
            PlatformPresentationPolicyRegistry
            .resolve(
                platform_id="platform.unknown.test",
                core_identity="fceumm",
            )
        )

    with pytest.raises(ValueError):
        (
            PlatformPresentationPolicyRegistry
            .resolve(
                platform_id="platform.unknown.test",
                core_identity="snes9x",
            )
        )


def test_ready_platform_rejects_foreign_core_policy():
    import pytest

    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
    )

    with pytest.raises(ValueError):
        (
            PlatformPresentationPolicyRegistry
            .resolve(
                platform_id="platform.nintendo.nes",
                core_identity="snes9x",
            )
        )

    with pytest.raises(ValueError):
        (
            PlatformPresentationPolicyRegistry
            .resolve(
                platform_id="platform.nintendo.snes",
                core_identity="fceumm",
            )
        )


def test_core_only_resolution_remains_backward_compatible():
    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
    )

    assert (
        PlatformPresentationPolicyRegistry
        .resolve(
            core_identity="fceumm",
        )
        .platform_id
        == "platform.nintendo.nes"
    )

    assert (
        PlatformPresentationPolicyRegistry
        .resolve(
            core_identity="snes9x",
        )
        .platform_id
        == "platform.nintendo.snes"
    )


def test_non_string_platform_identity_uses_legacy_core_path():
    from unittest.mock import Mock

    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
    )

    platform_id = Mock()

    policy = (
        PlatformPresentationPolicyRegistry
        .resolve(
            platform_id=platform_id,
            core_identity="fceumm",
        )
    )

    assert (
        policy.platform_id
        == "platform.nintendo.nes"
    )


def test_policy_registry_remains_tuple_backed():
    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
    )

    assert isinstance(
        PlatformPresentationPolicyRegistry.POLICIES,
        tuple,
    )


def test_policy_dataclass_remains_constructible_after_state_model():
    from dataclasses import is_dataclass

    from services.presentation.platform_policy import (
        PlatformPresentationPolicy,
    )

    assert is_dataclass(
        PlatformPresentationPolicy
    )

    policy = PlatformPresentationPolicy(
        platform_id="platform.test",
        core_identities=("test_core",),
        core_options={},
    )

    assert (
        policy.platform_id
        == "platform.test"
    )


def test_policy_state_model_contains_no_physical_geometry():
    from dataclasses import fields

    from services.presentation.platform_policy import (
        PlatformPresentationPolicy,
    )

    field_names = {
        field.name
        for field in fields(
            PlatformPresentationPolicy
        )
    }

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
        "overlay",
        "shader",
    }

    assert field_names.isdisjoint(
        forbidden
    )


def test_canonical_core_compatibility_is_independent_of_presentation_readiness():
    registry = PlatformPresentationPolicyRegistry

    assert registry.compatible_core_identities(
        "platform.nintendo.nes"
    ) == (
        "fceumm",
    )

    assert registry.compatible_core_identities(
        "platform.nintendo.snes"
    ) == (
        "snes9x",
    )

    assert registry.compatible_core_identities(
        "platform.sega.genesis"
    ) == (
        "genesis_plus_gx",
    )

    assert registry.compatible_core_identities(
        "platform.nintendo.n64"
    ) == (
        "mupen64plus_next",
    )

    assert registry.compatible_core_identities(
        "platform.arcade"
    ) == (
        "mame",
    )

    # Genesis/N64/Arcade remain presentation-UNCONFIGURED even though
    # their current Library launch core compatibility is known.
    for platform_id in (
        "platform.sega.genesis",
        "platform.nintendo.n64",
        "platform.arcade",
    ):
        assert registry.for_platform(
            platform_id
        ) is None


def test_canonical_core_compatibility_normalizes_library_core_paths():
    registry = PlatformPresentationPolicyRegistry

    assert registry.is_core_compatible(
        "platform.nintendo.nes",
        "fceumm",
    )

    assert registry.is_core_compatible(
        "platform.nintendo.nes",
        "fceumm_libretro.so",
    )

    assert registry.is_core_compatible(
        "platform.nintendo.nes",
        "/opt/retropie/libretrocores/"
        "lr-fceumm/fceumm_libretro.so",
    )

    assert registry.is_core_compatible(
        "platform.nintendo.snes",
        "snes9x_libretro.so",
    )

    assert not registry.is_core_compatible(
        "platform.nintendo.nes",
        "snes9x_libretro.so",
    )


def test_unknown_platform_or_core_never_becomes_implicit_compatibility():
    registry = PlatformPresentationPolicyRegistry

    assert registry.compatible_core_identities(
        "platform.unknown"
    ) == ()

    assert registry.compatible_core_identities(
        None
    ) == ()

    assert not registry.is_core_compatible(
        "platform.unknown",
        "fceumm",
    )

    assert not registry.is_core_compatible(
        "platform.nintendo.nes",
        "",
    )

    assert not registry.is_core_compatible(
        "platform.nintendo.nes",
        object(),
    )


def test_every_ready_policy_uses_canonical_core_compatibility():
    registry = PlatformPresentationPolicyRegistry

    for platform_id in (
        registry.ready_platform_ids()
    ):
        policy = registry.for_platform(
            platform_id
        )

        assert policy is not None

        assert tuple(
            policy.core_identities
        ) == tuple(
            registry.compatible_core_identities(
                platform_id
            )
        )


def test_sega_shared_genesis_plus_gx_core_policy_remains_unconfigured():
    """Shared core authority must not imply shared presentation geometry."""
    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
    )

    targets = (
        "platform.sega.game.gear",
        "platform.sega.master.system",
        "platform.sega.sg1000",
    )

    for platform_id in targets:
        assert (
            PlatformPresentationPolicyRegistry
            .compatible_core_identities(platform_id)
            == ("genesis_plus_gx",)
        )

        assert (
            PlatformPresentationPolicyRegistry
            .state_for(platform_id)
            .value
            == "unconfigured"
        )
