import pytest

from services.retroarch.core_identity import (
    canonical_libretro_core_identity,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    (
        (
            "fceumm",
            "fceumm",
        ),
        (
            "FCEUmm",
            "fceumm",
        ),
        (
            "fceumm_libretro",
            "fceumm",
        ),
        (
            "fceumm_libretro.so",
            "fceumm",
        ),
        (
            "/opt/retropie/libretrocores/lr-fceumm/"
            "fceumm_libretro.so",
            "fceumm",
        ),
        (
            r"C:\\cores\\snes9x_libretro.dll",
            "snes9x",
        ),
        (
            "/cores/snes9x_libretro.dylib",
            "snes9x",
        ),
        (
            "/opt/retropie/libretrocores/lr-genesis-plus-gx/"
            "genesis_plus_gx_libretro.so",
            "genesis_plus_gx",
        ),
        (
            "lr-fceumm",
            "fceumm",
        ),
    ),
)
def test_canonical_libretro_core_identity(
    value,
    expected,
):
    assert (
        canonical_libretro_core_identity(
            value
        )
        == expected
    )


@pytest.mark.parametrize(
    "value",
    (
        None,
        123,
        "",
        "   ",
    ),
)
def test_canonical_libretro_core_identity_rejects_invalid_values(
    value,
):
    with pytest.raises(
        ValueError
    ):
        canonical_libretro_core_identity(
            value
        )
