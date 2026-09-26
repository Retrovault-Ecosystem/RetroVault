import ctypes

import pytest

from services.retroarch.core_display_aspect import (
    LibretroDisplayAspectProbe,
    _RetroGameGeometry,
)


def _geometry(
    *,
    base_width=256,
    base_height=224,
    aspect_ratio=1.306,
):
    value = _RetroGameGeometry()

    value.base_width = base_width
    value.base_height = base_height
    value.max_width = base_width
    value.max_height = base_height
    value.aspect_ratio = aspect_ratio

    return value


def test_positive_core_aspect_is_authoritative_over_raster():
    aspect = (
        LibretroDisplayAspectProbe
        ._aspect_from_geometry(
            _geometry(
                base_width=256,
                base_height=224,
                aspect_ratio=1.306,
            )
        )
    )

    assert aspect.ratio == pytest.approx(
        1.306,
        rel=1e-6,
    )

    assert aspect.ratio != pytest.approx(
        256 / 224
    )


def test_zero_core_aspect_falls_back_to_base_geometry_ratio():
    aspect = (
        LibretroDisplayAspectProbe
        ._aspect_from_geometry(
            _geometry(
                base_width=320,
                base_height=240,
                aspect_ratio=0.0,
            )
        )
    )

    assert aspect.width == 320
    assert aspect.height == 240
    assert aspect.ratio == pytest.approx(
        4 / 3
    )


@pytest.mark.parametrize(
    (
        "width",
        "height",
    ),
    (
        (0, 224),
        (256, 0),
        (0, 0),
    ),
)
def test_invalid_fallback_geometry_fails_closed(
    width,
    height,
):
    with pytest.raises(
        ValueError
    ):
        (
            LibretroDisplayAspectProbe
            ._aspect_from_geometry(
                _geometry(
                    base_width=width,
                    base_height=height,
                    aspect_ratio=0.0,
                )
            )
        )


def test_abi_geometry_field_order_matches_libretro_contract():
    names = [
        name
        for name, _ctype
        in _RetroGameGeometry._fields_
    ]

    assert names == [
        "base_width",
        "base_height",
        "max_width",
        "max_height",
        "aspect_ratio",
    ]

    assert (
        _RetroGameGeometry
        .aspect_ratio
        .offset
        >
        _RetroGameGeometry
        .max_height
        .offset
    )


def test_acquisition_contract_contains_no_content_identity():
    names = {
        name
        for name in dir(
            LibretroDisplayAspectProbe
        )
        if not name.startswith("__")
    }

    forbidden = {
        "game",
        "game_id",
        "rom",
        "rom_path",
        "archive_member",
        "title",
        "title_screen",
        "gameplay_state",
    }

    assert forbidden.isdisjoint(
        names
    )


def test_core_path_validation_rejects_non_string():
    probe = LibretroDisplayAspectProbe()

    with pytest.raises(
        ValueError
    ):
        probe.acquire(
            None
        )


def test_core_path_validation_rejects_empty_string():
    probe = LibretroDisplayAspectProbe()

    with pytest.raises(
        ValueError
    ):
        probe.acquire(
            ""
        )


def test_core_path_validation_rejects_missing_file(
    tmp_path,
):
    probe = LibretroDisplayAspectProbe()

    with pytest.raises(
        ValueError
    ):
        probe.acquire(
            str(
                tmp_path
                / "missing_libretro.so"
            )
        )


def test_loader_receives_exact_core_path(
    tmp_path,
):
    core = (
        tmp_path
        / "example_libretro.so"
    )

    core.write_bytes(
        b"not-a-real-library"
    )

    seen = []

    class FakeFunction:
        argtypes = None
        restype = object()

        def __call__(
            self,
            pointer,
        ):
            av_info = (
                pointer
                ._obj
            )

            av_info.geometry.base_width = 256
            av_info.geometry.base_height = 224
            av_info.geometry.max_width = 256
            av_info.geometry.max_height = 224
            av_info.geometry.aspect_ratio = 1.306

    class FakeLibrary:
        retro_get_system_av_info = (
            FakeFunction()
        )

    def loader(path):
        seen.append(
            path
        )

        return FakeLibrary()

    probe = LibretroDisplayAspectProbe(
        loader=loader
    )

    aspect = probe.acquire(
        str(core)
    )

    assert seen == [
        str(core)
    ]

    assert aspect.ratio == pytest.approx(
        1.306,
        rel=1e-6,
    )


def test_missing_av_info_symbol_fails_closed(
    tmp_path,
):
    core = (
        tmp_path
        / "example_libretro.so"
    )

    core.write_bytes(
        b"placeholder"
    )

    class FakeLibrary:
        pass

    probe = LibretroDisplayAspectProbe(
        loader=lambda _path: FakeLibrary()
    )

    with pytest.raises(
        ValueError,
        match="retro_get_system_av_info",
    ):
        probe.acquire(
            str(core)
        )


@pytest.mark.parametrize(
    "aspect_ratio",
    (
        float("nan"),
        float("inf"),
        float("-inf"),
    ),
)
def test_non_finite_core_aspect_fails_closed(
    aspect_ratio,
):
    with pytest.raises(
        ValueError,
        match="non-finite",
    ):
        (
            LibretroDisplayAspectProbe
            ._aspect_from_geometry(
                _geometry(
                    aspect_ratio=aspect_ratio,
                )
            )
        )


def test_probe_contract_does_not_enter_core_lifecycle():
    source = (
        __import__(
            "inspect"
        )
        .getsource(
            LibretroDisplayAspectProbe
        )
    )

    forbidden_calls = (
        ".retro_init(",
        ".retro_deinit(",
        ".retro_load_game(",
        ".retro_unload_game(",
        ".retro_set_environment(",
    )

    for token in forbidden_calls:
        assert token not in source


def test_probe_contract_uses_only_core_path_as_acquisition_input():
    import inspect

    signature = inspect.signature(
        LibretroDisplayAspectProbe.acquire
    )

    assert tuple(
        signature.parameters
    ) == (
        "self",
        "core",
    )


def test_probe_contract_contains_no_content_specific_parameters():
    import inspect

    parameters = {
        name.casefold()
        for name in inspect.signature(
            LibretroDisplayAspectProbe.acquire
        ).parameters
    }

    forbidden = {
        "game",
        "game_id",
        "rom",
        "rom_path",
        "archive_member",
        "title",
        "title_id",
        "raster",
        "raster_width",
        "raster_height",
    }

    assert forbidden.isdisjoint(
        parameters
    )


def test_prelaunch_probe_preserves_positive_display_aspect():
    aspect = (
        LibretroDisplayAspectProbe
        ._aspect_from_geometry(
            _geometry(
                base_width=256,
                base_height=224,
                aspect_ratio=1.306,
            )
        )
    )

    assert aspect.width == pytest.approx(
        1.306,
        rel=1e-6,
    )
    assert aspect.height == pytest.approx(
        1.0,
        rel=1e-6,
    )
    assert aspect.ratio == pytest.approx(
        1.306,
        rel=1e-6,
    )


def test_positive_display_aspect_never_uses_base_raster_ratio():
    aspect = (
        LibretroDisplayAspectProbe
        ._aspect_from_geometry(
            _geometry(
                base_width=320,
                base_height=224,
                aspect_ratio=1.306,
            )
        )
    )

    assert aspect.ratio == pytest.approx(
        1.306,
        rel=1e-6,
    )

    assert aspect.ratio != pytest.approx(
        320 / 224
    )
