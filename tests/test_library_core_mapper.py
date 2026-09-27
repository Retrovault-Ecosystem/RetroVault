from services.library.core_mapper import CoreMapper


def test_nes_canonical_and_alias_names_share_core():
    mapper = CoreMapper()

    expected = "fceumm_libretro.so"

    assert mapper.get_core(
        "Nintendo Entertainment System"
    ) == expected

    assert mapper.get_core(
        "NES"
    ) == expected


def test_snes_canonical_and_alias_names_share_core():
    mapper = CoreMapper()

    expected = "snes9x_libretro.so"

    assert mapper.get_core(
        "Super Nintendo"
    ) == expected

    assert mapper.get_core(
        "Super Nintendo Entertainment System"
    ) == expected

    assert mapper.get_core(
        "SNES"
    ) == expected


def test_genesis_canonical_and_alias_names_share_core():
    mapper = CoreMapper()

    expected = "genesis_plus_gx_libretro.so"

    assert mapper.get_core(
        "Sega Genesis"
    ) == expected

    assert mapper.get_core(
        "Genesis"
    ) == expected


def test_unknown_platform_has_no_guessed_core():
    mapper = CoreMapper()

    assert mapper.get_core(
        "Definitely Unknown Platform"
    ) == ""


def test_core_mapper_is_derived_from_canonical_platform_core_authority():
    from services.library.core_mapper import (
        CORE_MAP,
        PLATFORM_ALIASES,
    )
    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
    )

    for label, platform_id in (
        PLATFORM_ALIASES.items()
    ):
        cores = (
            PlatformPresentationPolicyRegistry
            .compatible_core_identities(
                platform_id
            )
        )

        assert len(cores) == 1

        expected = (
            f"{cores[0]}_libretro.so"
        )

        assert CORE_MAP[label] == expected
        assert CoreMapper().get_core(
            label
        ) == expected


def test_known_library_cores_do_not_override_presentation_policy_state():
    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
        PlatformPresentationPolicyState,
    )

    cases = (
        (
            "Sega Genesis",
            "platform.sega.genesis",
            "genesis_plus_gx_libretro.so",
            PlatformPresentationPolicyState.READY,
            True,
        ),
        (
            "Nintendo 64",
            "platform.nintendo.n64",
            "mupen64plus_next_libretro.so",
            PlatformPresentationPolicyState.UNCONFIGURED,
            False,
        ),
        (
            "Arcade",
            "platform.arcade",
            "mame_libretro.so",
            PlatformPresentationPolicyState.UNCONFIGURED,
            False,
        ),
    )

    mapper = CoreMapper()

    for (
        label,
        platform_id,
        expected_core,
        expected_presentation_state,
        expects_policy,
    ) in cases:
        assert mapper.get_core(label) == expected_core

        assert (
            PlatformPresentationPolicyRegistry.state_for(platform_id)
            is expected_presentation_state
        )

        policy = PlatformPresentationPolicyRegistry.for_platform(
            platform_id
        )

        if expects_policy:
            assert policy is not None
        else:
            assert policy is None



def test_sega_shared_genesis_plus_gx_library_aliases():
    """Library aliases resolve through canonical policy, not presentation fallback."""
    from services.library.core_mapper import (
        CoreMapper,
        PLATFORM_ALIASES,
    )

    expected = {
        "Game Gear":
            "platform.sega.game.gear",
        "Sega Game Gear":
            "platform.sega.game.gear",
        "Master System":
            "platform.sega.master.system",
        "Sega Master System":
            "platform.sega.master.system",
        "SG-1000":
            "platform.sega.sg1000",
        "Sega SG-1000":
            "platform.sega.sg1000",
    }

    mapper = CoreMapper()

    for alias, platform_id in expected.items():
        assert (
            PLATFORM_ALIASES[alias]
            == platform_id
        )

        assert (
            mapper.get_core(alias)
            == "genesis_plus_gx_libretro.so"
        )
