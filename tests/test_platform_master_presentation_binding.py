from dataclasses import fields

import pytest

from services.presentation.master_profile import (
    MasterPresentationClass,
    MasterPresentationProfileRegistry,
)
from services.presentation.platform_policy import (
    PlatformPresentationPolicy,
    PlatformPresentationPolicyRegistry,
    PlatformPresentationPolicyState,
)


def test_ready_nes_and_snes_bind_to_classic_4_3():
    registry = PlatformPresentationPolicyRegistry

    for platform_id in (
        "platform.nintendo.nes",
        "platform.nintendo.snes",
    ):
        assert (
            registry.state_for(platform_id)
            is PlatformPresentationPolicyState.READY
        )

        assert (
            registry.master_presentation_class_for(
                platform_id
            )
            is MasterPresentationClass.CLASSIC_4_3
        )

        profile = (
            registry.master_presentation_profile_for(
                platform_id
            )
        )

        assert profile is (
            MasterPresentationProfileRegistry
            .require(
                MasterPresentationClass.CLASSIC_4_3
            )
        )

        assert profile.canvas == (
            1920,
            1080,
        )

        assert profile.envelope == (
            240,
            0,
            1440,
            1080,
        )


def test_binding_does_not_change_production_readiness():
    registry = PlatformPresentationPolicyRegistry

    assert set(
        registry.ready_platform_ids()
    ) == {
        "platform.nintendo.nes",
        "platform.nintendo.snes",
    }

    assert len(
        registry.unconfigured_platform_ids()
    ) == 24


@pytest.mark.parametrize(
    "platform_id",
    (
        "platform.sega.genesis",
        "platform.nintendo.n64",
        "platform.arcade",
        "platform.sega.game.gear",
        "platform.atari.lynx",
        "platform.nintendo.game.boy",
        "platform.nintendo.game.boy.color",
        "platform.nintendo.game.boy.advance",
        "platform.nintendo.ds",
        "platform.nintendo.3ds",
        "platform.nintendo.gamecube",
        "platform.sega.dreamcast",
    ),
)
def test_unqualified_platform_does_not_borrow_master_profile(
    platform_id,
):
    registry = PlatformPresentationPolicyRegistry

    assert (
        registry.state_for(platform_id)
        is PlatformPresentationPolicyState.UNCONFIGURED
    )

    assert (
        registry.master_presentation_class_for(
            platform_id
        )
        is None
    )

    assert (
        registry.master_presentation_profile_for(
            platform_id
        )
        is None
    )


def test_unknown_platform_does_not_gain_implicit_profile():
    registry = PlatformPresentationPolicyRegistry

    assert (
        registry.master_presentation_class_for(
            "platform.unknown.test"
        )
        is None
    )

    assert (
        registry.master_presentation_profile_for(
            "platform.unknown.test"
        )
        is None
    )


def test_policy_accepts_stable_master_profile_string():
    policy = PlatformPresentationPolicy(
        platform_id="platform.test",
        core_identities=("example",),
        core_options={},
        master_presentation_class="classic_4_3",
    )

    assert (
        policy.master_presentation_class
        is MasterPresentationClass.CLASSIC_4_3
    )


def test_policy_rejects_unknown_master_profile():
    with pytest.raises(
        ValueError,
        match="Master presentation class",
    ):
        PlatformPresentationPolicy(
            platform_id="platform.test",
            core_identities=("example",),
            core_options={},
            master_presentation_class="not_real",
        )


def test_policy_profile_binding_contains_no_physical_geometry():
    field_names = {
        field.name
        for field in fields(
            PlatformPresentationPolicy
        )
    }

    assert (
        "master_presentation_class"
        in field_names
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
        "envelope_x",
        "envelope_y",
        "envelope_width",
        "envelope_height",
    }

    assert field_names.isdisjoint(
        forbidden
    )


def test_master_profile_binding_contains_no_game_identity():
    policy = (
        PlatformPresentationPolicyRegistry
        .for_platform(
            "platform.nintendo.nes"
        )
    )

    assert policy is not None

    payload = repr(policy).casefold()

    for forbidden in (
        "game_id",
        "rom_path",
        "rom_filename",
        "archive_filename",
        "title_id",
    ):
        assert forbidden not in payload


def test_profile_assignment_does_not_imply_runtime_migration():
    """
    Binding NES/SNES to CLASSIC_4_3 classifies their presentation family.

    It does not replace their already-approved production package
    viewport geometry. Physical deployment remains package-owned until
    an explicit migration/qualification boundary.
    """
    registry = PlatformPresentationPolicyRegistry

    nes = registry.for_platform(
        "platform.nintendo.nes"
    )

    snes = registry.for_platform(
        "platform.nintendo.snes"
    )

    assert nes is not None
    assert snes is not None

    for policy in (
        nes,
        snes,
    ):
        serialized = repr(policy)

        for forbidden in (
            "custom_viewport_x",
            "custom_viewport_y",
            "custom_viewport_width",
            "custom_viewport_height",
            "video_viewport_bias_x",
            "video_viewport_bias_y",
        ):
            assert forbidden not in serialized


def test_specialized_capability_classes_do_not_auto_assign_platforms():
    """
    Capability existence must never silently convert an UNCONFIGURED
    platform into guessed physical presentation geometry.
    """

    expected_unqualified = (
        "platform.arcade",
        "platform.atari.lynx",
        "platform.nintendo.game.boy",
        "platform.nintendo.game.boy.color",
        "platform.nintendo.game.boy.advance",
        "platform.nintendo.ds",
        "platform.nintendo.3ds",
        "platform.nintendo.gamecube",
        "platform.nintendo.wii",
        "platform.nintendo.wii.u",
        "platform.sega.dreamcast",
        "platform.sega.game.gear",
    )

    for platform_id in expected_unqualified:
        assert (
            PlatformPresentationPolicyRegistry
            .master_presentation_class_for(
                platform_id
            )
            is None
        )
