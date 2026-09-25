import pytest

from services.presentation.master_profile import (
    MasterPresentationClass,
    MasterPresentationProfile,
    MasterPresentationProfileRegistry,
    PresentationFitPolicy,
)


def test_registry_contains_initial_reusable_classes():
    assert {
        profile.profile_class
        for profile
        in MasterPresentationProfileRegistry.all()
    } == {
        MasterPresentationClass.CLASSIC_4_3,
        MasterPresentationClass.WIDESCREEN_16_9,
        MasterPresentationClass.ARCADE_VERTICAL,
    }


def test_classic_4_3_uses_centered_1440x1080_envelope():
    profile = (
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

    assert (
        profile.fit_policy
        is PresentationFitPolicy.CONTAIN
    )


def test_widescreen_16_9_uses_full_1080p_envelope():
    profile = (
        MasterPresentationProfileRegistry
        .require(
            MasterPresentationClass
            .WIDESCREEN_16_9
        )
    )

    assert profile.canvas == (
        1920,
        1080,
    )

    assert profile.envelope == (
        0,
        0,
        1920,
        1080,
    )


def test_vertical_arcade_is_reusable_profile_not_game_override():
    profile = (
        MasterPresentationProfileRegistry
        .require(
            MasterPresentationClass.ARCADE_VERTICAL
        )
    )

    assert profile.canvas == (
        1920,
        1080,
    )

    assert profile.envelope == (
        656,
        0,
        608,
        1080,
    )


@pytest.mark.parametrize(
    (
        "source_width",
        "source_height",
        "expected",
    ),
    (
        (
            256,
            224,
            (
                343,
                0,
                1234,
                1080,
            ),
        ),
        (
            320,
            240,
            (
                240,
                0,
                1440,
                1080,
            ),
        ),
        (
            640,
            480,
            (
                240,
                0,
                1440,
                1080,
            ),
        ),
        (
            384,
            224,
            (
                240,
                120,
                1440,
                840,
            ),
        ),
    ),
)
def test_classic_profile_contains_without_crop_or_stretch(
    source_width,
    source_height,
    expected,
):
    profile = (
        MasterPresentationProfileRegistry
        .require(
            MasterPresentationClass.CLASSIC_4_3
        )
    )

    geometry = profile.contain(
        source_width,
        source_height,
    )

    assert (
        geometry.x,
        geometry.y,
        geometry.width,
        geometry.height,
    ) == expected

    assert geometry.x >= profile.envelope_x
    assert geometry.y >= profile.envelope_y

    assert (
        geometry.x
        + geometry.width
        <= (
            profile.envelope_x
            + profile.envelope_width
        )
    )

    assert (
        geometry.y
        + geometry.height
        <= (
            profile.envelope_y
            + profile.envelope_height
        )
    )


def test_widescreen_profile_contains_native_16_9():
    profile = (
        MasterPresentationProfileRegistry
        .require(
            MasterPresentationClass
            .WIDESCREEN_16_9
        )
    )

    geometry = profile.contain(
        1920,
        1080,
    )

    assert (
        geometry.x,
        geometry.y,
        geometry.width,
        geometry.height,
    ) == (
        0,
        0,
        1920,
        1080,
    )


def test_vertical_profile_contains_portrait_content():
    profile = (
        MasterPresentationProfileRegistry
        .require(
            MasterPresentationClass.ARCADE_VERTICAL
        )
    )

    geometry = profile.contain(
        224,
        384,
    )

    assert (
        geometry.x,
        geometry.y,
        geometry.width,
        geometry.height,
    ) == (
        656,
        19,
        608,
        1042,
    )


def test_contain_rejects_invalid_source_dimensions():
    profile = (
        MasterPresentationProfileRegistry
        .require(
            MasterPresentationClass.CLASSIC_4_3
        )
    )

    with pytest.raises(
        ValueError,
        match="source_width must be positive",
    ):
        profile.contain(
            0,
            240,
        )

    with pytest.raises(
        ValueError,
        match="source_height must be positive",
    ):
        profile.contain(
            320,
            0,
        )


def test_profile_rejects_envelope_outside_canvas():
    with pytest.raises(
        ValueError,
        match="Envelope exceeds canvas width",
    ):
        MasterPresentationProfile(
            profile_class=(
                MasterPresentationClass.CLASSIC_4_3
            ),
            canvas_width=1920,
            canvas_height=1080,
            envelope_x=1000,
            envelope_y=0,
            envelope_width=1000,
            envelope_height=1080,
        )


def test_registry_accepts_stable_string_identity():
    assert (
        MasterPresentationProfileRegistry
        .require("classic_4_3")
        .profile_class
        is MasterPresentationClass.CLASSIC_4_3
    )


def test_registry_rejects_unknown_profile():
    assert (
        MasterPresentationProfileRegistry
        .get("unknown")
        is None
    )

    with pytest.raises(
        ValueError,
        match=(
            "Unknown RetroVault master "
            "presentation profile"
        ),
    ):
        (
            MasterPresentationProfileRegistry
            .require("unknown")
        )


def test_contract_contains_no_game_or_rom_identity():
    profile = (
        MasterPresentationProfileRegistry
        .require(
            MasterPresentationClass.CLASSIC_4_3
        )
    )

    fields = set(
        profile.__dataclass_fields__
    )

    forbidden = {
        "game",
        "game_id",
        "game_name",
        "rom",
        "rom_path",
        "title",
        "title_id",
    }

    assert fields.isdisjoint(
        forbidden
    )


def test_classic_profile_can_contain_resolved_4_3_display_aspect():
    profile = (
        MasterPresentationProfileRegistry
        .require(
            MasterPresentationClass.CLASSIC_4_3
        )
    )

    geometry = profile.contain_aspect(
        4,
        3,
    )

    assert (
        geometry.x,
        geometry.y,
        geometry.width,
        geometry.height,
    ) == (
        240,
        0,
        1440,
        1080,
    )


def test_display_aspect_is_distinct_from_raw_framebuffer_ratio():
    profile = (
        MasterPresentationProfileRegistry
        .require(
            MasterPresentationClass.CLASSIC_4_3
        )
    )

    raw_raster_geometry = profile.contain(
        256,
        224,
    )

    resolved_display_geometry = (
        profile.contain_aspect(
            4,
            3,
        )
    )

    assert raw_raster_geometry != resolved_display_geometry

    assert (
        resolved_display_geometry.width,
        resolved_display_geometry.height,
    ) == (
        1440,
        1080,
    )


def test_contain_aspect_supports_non_integer_display_ratio():
    profile = (
        MasterPresentationProfileRegistry
        .require(
            MasterPresentationClass.WIDESCREEN_16_9
        )
    )

    geometry = profile.contain_aspect(
        16.0,
        9.0,
    )

    assert (
        geometry.x,
        geometry.y,
        geometry.width,
        geometry.height,
    ) == (
        0,
        0,
        1920,
        1080,
    )


def test_contain_aspect_rejects_invalid_values():
    profile = (
        MasterPresentationProfileRegistry
        .require(
            MasterPresentationClass.CLASSIC_4_3
        )
    )

    for width, height in (
        (0, 3),
        (4, 0),
        (-4, 3),
        (4, -3),
        (True, 3),
        (4, False),
        ("4", 3),
        (4, "3"),
    ):
        with pytest.raises(ValueError):
            profile.contain_aspect(
                width,
                height,
            )
