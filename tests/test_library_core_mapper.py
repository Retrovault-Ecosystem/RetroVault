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


def test_unconfigured_platforms_with_known_library_cores_do_not_become_presentation_ready():
    from services.presentation.platform_policy import (
        PlatformPresentationPolicyRegistry,
        PlatformPresentationPolicyState,
    )

    cases = (
        (
            "Sega Genesis",
            "platform.sega.genesis",
            "genesis_plus_gx_libretro.so",
        ),
        (
            "Nintendo 64",
            "platform.nintendo.n64",
            "mupen64plus_next_libretro.so",
        ),
        (
            "Arcade",
            "platform.arcade",
            "mame_libretro.so",
        ),
    )

    mapper = CoreMapper()

    for (
        label,
        platform_id,
        expected_core,
    ) in cases:
        assert mapper.get_core(
            label
        ) == expected_core

        assert (
            PlatformPresentationPolicyRegistry
            .state_for(platform_id)
            is PlatformPresentationPolicyState.UNCONFIGURED
        )

        assert (
            PlatformPresentationPolicyRegistry
            .for_platform(platform_id)
            is None
        )
