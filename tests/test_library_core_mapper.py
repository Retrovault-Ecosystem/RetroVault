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
