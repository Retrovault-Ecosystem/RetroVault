from pathlib import Path

import pytest

from services.presentation.master_profile import (
    MasterPresentationClass,
    MasterPresentationProfile,
    PresentationFitPolicy,
)
from services.retroarch.contain_runtime import (
    ContainRuntimeConfig,
)


def _glass():
    return MasterPresentationProfile(
        profile_class=(
            MasterPresentationClass.CLASSIC_4_3
        ),
        canvas_width=1920,
        canvas_height=1080,
        envelope_x=355,
        envelope_y=100,
        envelope_width=1206,
        envelope_height=762,
        fit_policy=(
            PresentationFitPolicy.CONTAIN
        ),
    )


def _values(path):
    result = {}

    for raw_line in Path(path).read_text(
        encoding="utf-8"
    ).splitlines():
        line = raw_line.strip()

        if not line:
            continue

        key, separator, value = (
            line.partition("=")
        )

        assert separator

        result[key.strip()] = (
            value.strip().strip('"')
        )

    return result


def test_contain_runtime_uses_display_aspect_not_raw_raster(
    tmp_path,
):
    runtime = ContainRuntimeConfig(
        directory=tmp_path,
    )

    geometry = runtime.geometry(
        profile=_glass(),
        display_aspect_width=1306,
        display_aspect_height=1000,
    )

    assert (
        geometry.x,
        geometry.y,
        geometry.width,
        geometry.height,
    ) == (
        460,
        100,
        995,
        762,
    )


@pytest.mark.parametrize(
    (
        "aspect_width",
        "aspect_height",
        "expected",
    ),
    (
        (
            4,
            3,
            (450, 100, 1016, 762),
        ),
        (
            8,
            7,
            (522, 100, 871, 762),
        ),
        (
            1,
            1,
            (577, 100, 762, 762),
        ),
        (
            16,
            9,
            (355, 142, 1206, 678),
        ),
    ),
)
def test_contain_runtime_is_generic_across_display_aspects(
    tmp_path,
    aspect_width,
    aspect_height,
    expected,
):
    runtime = ContainRuntimeConfig(
        directory=tmp_path,
    )

    geometry = runtime.geometry(
        profile=_glass(),
        display_aspect_width=aspect_width,
        display_aspect_height=aspect_height,
    )

    assert (
        geometry.x,
        geometry.y,
        geometry.width,
        geometry.height,
    ) == expected


def test_contain_runtime_emits_transient_custom_viewport(
    tmp_path,
):
    runtime = ContainRuntimeConfig(
        directory=tmp_path,
    )

    path = runtime.create(
        profile=_glass(),
        display_aspect_width=1306,
        display_aspect_height=1000,
    )

    values = _values(
        path
    )

    assert values == {
        "aspect_ratio_index": "23",
        "video_force_aspect": "true",
        "video_scale_integer": "false",
        "video_viewport_bias_x": "0.500000",
        "video_viewport_bias_y": "0.500000",
        "custom_viewport_x": "460",
        "custom_viewport_y": "100",
        "custom_viewport_width": "995",
        "custom_viewport_height": "762",
        "video_crop_overscan": "false",
    }


def test_contain_runtime_never_changes_fixed_envelope(
    tmp_path,
):
    profile = _glass()

    before = profile.envelope

    runtime = ContainRuntimeConfig(
        directory=tmp_path,
    )

    runtime.create(
        profile=profile,
        display_aspect_width=1306,
        display_aspect_height=1000,
    )

    assert profile.envelope == before
    assert profile.envelope == (
        355,
        100,
        1206,
        762,
    )


def test_contain_runtime_contains_every_result_inside_glass(
    tmp_path,
):
    profile = _glass()

    runtime = ContainRuntimeConfig(
        directory=tmp_path,
    )

    for width, height in (
        (1306, 1000),
        (4, 3),
        (8, 7),
        (1, 1),
        (16, 9),
        (21, 9),
        (3, 4),
        (9, 16),
    ):
        geometry = runtime.geometry(
            profile=profile,
            display_aspect_width=width,
            display_aspect_height=height,
        )

        assert geometry.x >= profile.envelope_x
        assert geometry.y >= profile.envelope_y

        assert (
            geometry.x
            + geometry.width
            <= profile.envelope_x
            + profile.envelope_width
        )

        assert (
            geometry.y
            + geometry.height
            <= profile.envelope_y
            + profile.envelope_height
        )


@pytest.mark.parametrize(
    (
        "width",
        "height",
    ),
    (
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
def test_contain_runtime_rejects_invalid_display_aspect(
    tmp_path,
    width,
    height,
):
    runtime = ContainRuntimeConfig(
        directory=tmp_path,
    )

    with pytest.raises(
        ValueError
    ):
        runtime.create(
            profile=_glass(),
            display_aspect_width=width,
            display_aspect_height=height,
        )


def test_contain_runtime_rejects_non_profile(
    tmp_path,
):
    runtime = ContainRuntimeConfig(
        directory=tmp_path,
    )

    with pytest.raises(
        TypeError
    ):
        runtime.create(
            profile=object(),
            display_aspect_width=4,
            display_aspect_height=3,
        )


def test_contain_runtime_cleanup_removes_transient_file(
    tmp_path,
):
    runtime = ContainRuntimeConfig(
        directory=tmp_path,
    )

    path = Path(
        runtime.create(
            profile=_glass(),
            display_aspect_width=1306,
            display_aspect_height=1000,
        )
    )

    assert path.is_file()

    runtime.cleanup()

    assert not path.exists()


def test_contain_runtime_contains_no_content_identity_fields():
    fields = {
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

    names = set(
        ContainRuntimeConfig.create
        .__code__
        .co_varnames
    )

    assert fields.isdisjoint(
        names
    )


def test_contain_runtime_accepts_core_display_aspect_object(
    tmp_path,
):
    from services.retroarch.display_aspect import (
        CoreDisplayAspect,
    )

    runtime = ContainRuntimeConfig(
        directory=tmp_path,
    )

    path = runtime.create_for_aspect(
        profile=_glass(),
        display_aspect=CoreDisplayAspect(
            width=1306,
            height=1000,
        ),
    )

    values = _values(
        path
    )

    assert values[
        "custom_viewport_x"
    ] == "460"

    assert values[
        "custom_viewport_y"
    ] == "100"

    assert values[
        "custom_viewport_width"
    ] == "995"

    assert values[
        "custom_viewport_height"
    ] == "762"
