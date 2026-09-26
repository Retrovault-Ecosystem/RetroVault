import pytest

from models.launch_profile import LaunchProfile
from services.retroarch.display_aspect import (
    CoreDisplayAspect,
)


def _profile(**overrides):
    values = {
        "game": "Example",
        "rom": "/roms/example.bin",
        "core": "/cores/example_libretro.so",
    }

    values.update(overrides)

    return LaunchProfile(
        **values
    )


def test_launch_profile_defaults_to_no_display_aspect():
    profile = _profile()

    assert profile.display_aspect_width is None
    assert profile.display_aspect_height is None

    assert (
        CoreDisplayAspect.from_launch_profile(
            profile
        )
        is None
    )


def test_launch_profile_can_carry_core_display_aspect():
    profile = _profile(
        display_aspect_width=1306,
        display_aspect_height=1000,
    )

    aspect = (
        CoreDisplayAspect.from_launch_profile(
            profile
        )
    )

    assert aspect == CoreDisplayAspect(
        width=1306,
        height=1000,
    )

    assert aspect.ratio == pytest.approx(
        1.306
    )


@pytest.mark.parametrize(
    (
        "width",
        "height",
    ),
    (
        (None, 1),
        (1, None),
        (0, 1),
        (1, 0),
        (-1, 1),
        (1, -1),
        (True, 1),
        (1, False),
        ("4", 3),
        (4, "3"),
    ),
)
def test_invalid_display_aspect_fails_closed(
    width,
    height,
):
    profile = _profile(
        display_aspect_width=width,
        display_aspect_height=height,
    )

    with pytest.raises(
        ValueError
    ):
        CoreDisplayAspect.from_launch_profile(
            profile
        )


def test_display_aspect_contract_contains_no_content_identity():
    names = set(
        CoreDisplayAspect.__dataclass_fields__
    )

    forbidden = {
        "game",
        "game_id",
        "rom",
        "rom_path",
        "archive_member",
        "title",
        "raster",
        "source_width",
        "source_height",
    }

    assert forbidden.isdisjoint(
        names
    )
