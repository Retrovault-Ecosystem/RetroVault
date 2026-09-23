from __future__ import annotations

import json
import struct
import zlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SPEC = (
    ROOT
    / "data"
    / "presentation"
    / "specifications"
    / "rvv_nes_classic.json"
)

ASSET_ROOT = (
    ROOT
    / "retrovault"
    / "nes"
    / "classic"
)

PNG = (
    ASSET_ROOT
    / "RetroVault_NES_Classic_1080p.png"
)

CFG = (
    ASSET_ROOT
    / "RetroVault_NES_Classic.cfg"
)

META = (
    ASSET_ROOT
    / "RetroVault_NES_Classic.production.json"
)


def load_json(path: Path) -> dict:
    return json.loads(
        path.read_text(encoding="utf-8")
    )


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)

    if pa <= pb and pa <= pc:
        return a

    if pb <= pc:
        return b

    return c


def decode_rgba_png(
    path: Path,
) -> tuple[int, int, list[bytearray]]:
    raw = path.read_bytes()

    if raw[:8] != b"\x89PNG\r\n\x1a\n":
        raise AssertionError(
            "Invalid PNG signature."
        )

    position = 8

    width = None
    height = None
    bit_depth = None
    color_type = None
    interlace = None

    idat = bytearray()

    while position < len(raw):
        length = struct.unpack(
            ">I",
            raw[position:position + 4],
        )[0]

        kind = raw[
            position + 4:position + 8
        ]

        start = position + 8
        end = start + length

        data = raw[start:end]

        if kind == b"IHDR":
            (
                width,
                height,
                bit_depth,
                color_type,
                compression,
                filter_method,
                interlace,
            ) = struct.unpack(
                ">IIBBBBB",
                data,
            )

            assert compression == 0
            assert filter_method == 0

        elif kind == b"IDAT":
            idat.extend(data)

        elif kind == b"IEND":
            break

        position = end + 4

    assert width is not None
    assert height is not None

    assert bit_depth == 8
    assert color_type == 6
    assert interlace == 0

    decoded = zlib.decompress(
        bytes(idat)
    )

    bytes_per_pixel = 4
    row_bytes = width * bytes_per_pixel

    assert len(decoded) == (
        height * (row_bytes + 1)
    )

    rows = []
    offset = 0

    for y in range(height):
        filter_type = decoded[offset]
        offset += 1

        scanline = bytearray(
            decoded[
                offset:offset + row_bytes
            ]
        )

        offset += row_bytes

        previous = (
            rows[y - 1]
            if y > 0
            else bytearray(row_bytes)
        )

        reconstructed = bytearray(
            row_bytes
        )

        for i, value in enumerate(
            scanline
        ):
            left = (
                reconstructed[
                    i - bytes_per_pixel
                ]
                if i >= bytes_per_pixel
                else 0
            )

            up = previous[i]

            upper_left = (
                previous[
                    i - bytes_per_pixel
                ]
                if i >= bytes_per_pixel
                else 0
            )

            if filter_type == 0:
                result = value

            elif filter_type == 1:
                result = (
                    value + left
                ) & 0xFF

            elif filter_type == 2:
                result = (
                    value + up
                ) & 0xFF

            elif filter_type == 3:
                result = (
                    value
                    + ((left + up) // 2)
                ) & 0xFF

            elif filter_type == 4:
                result = (
                    value
                    + paeth(
                        left,
                        up,
                        upper_left,
                    )
                ) & 0xFF

            else:
                raise AssertionError(
                    "Unsupported PNG filter "
                    f"type: {filter_type}"
                )

            reconstructed[i] = result

        rows.append(reconstructed)

    return width, height, rows


def test_production_asset_files_exist():
    assert PNG.is_file()
    assert CFG.is_file()
    assert META.is_file()


def test_production_png_is_exact_rgba_canvas():
    width, height, _ = decode_rgba_png(
        PNG
    )

    assert (width, height) == (
        1920,
        1080,
    )


def test_production_geometry_matches_spec():
    spec = load_json(SPEC)
    meta = load_json(META)

    runtime = spec["design"]["runtime"]

    assert runtime["canvas"] == (
        meta["canvas"]
    )

    viewport = runtime["game_viewport"]
    aperture = meta["aperture"]

    for key in (
        "x",
        "y",
        "width",
        "height",
    ):
        assert (
            viewport[key]
            == aperture[key]
        )

    assert aperture == {
        "x": 355,
        "y": 100,
        "width": 1206,
        "height": 762,
    }


def test_production_aperture_is_exact_alpha_zero():
    width, height, rows = (
        decode_rgba_png(PNG)
    )

    meta = load_json(META)
    aperture = meta["aperture"]

    x0 = aperture["x"]
    y0 = aperture["y"]
    x1 = x0 + aperture["width"]
    y1 = y0 + aperture["height"]

    transparent = 0

    for y in range(height):
        for x in range(width):
            alpha = rows[y][
                (x * 4) + 3
            ]

            inside = (
                x0 <= x < x1
                and
                y0 <= y < y1
            )

            if inside:
                assert alpha == 0
                transparent += 1
            else:
                assert alpha == 255

    assert transparent == (
        aperture["width"]
        * aperture["height"]
    )


def test_retroarch_cfg_is_portable():
    text = CFG.read_text(
        encoding="utf-8"
    )

    assert (
        'overlays = "1"'
        in text
    )

    assert (
        'overlay0_overlay = '
        '"RetroVault_NES_Classic_1080p.png"'
        in text
    )

    assert (
        "overlay0_full_screen = true"
        in text
    )

    assert (
        "overlay0_descs = 0"
        in text
    )

    assert "input_overlay" not in text
    assert "/home/" not in text


def test_spec_keeps_catalog_reference_portable():
    spec = load_json(SPEC)

    assert spec["catalog"]["reference"] == (
        "retro-vault://overlays/"
        "retrovault/nes/classic/"
        "RetroVault_NES_Classic.cfg"
    )


def test_asset_is_production_after_live_proof():
    spec = load_json(SPEC)

    assert (
        spec["production_status"]
        == "production"
    )


def test_native_nes_runtime_descriptor_is_production_owned():
    from pathlib import Path

    runtime_descriptor = (
        Path(__file__).resolve().parents[1]
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic.runtime.cfg"
    )

    assert runtime_descriptor.is_file()

    assert runtime_descriptor.read_text(
        encoding="utf-8"
    ) == (
        '# RetroVault NES Classic\n'
        '#\n'
        '# Universal launch-scoped final geometry authority.\n'
        '# No per-title geometry is permitted in this descriptor.\n'
        '# FCEUmm preserves the complete source frame; this runtime owns\n'
        '# the final RetroArch viewport presented inside the fixed bezel.\n'
        '\n'
        'aspect_ratio_index = "22"\n'
        'video_force_aspect = "true"\n'
        'video_aspect_ratio = "-1.000000"\n'
        'video_aspect_ratio_auto = "false"\n'
        'video_crop_overscan = "false"\n'
        'video_scale_integer = "false"\n'
        'video_viewport_bias_x = "0.500000"\n'
        'video_viewport_bias_y = "0.500000"\n'
        'custom_viewport_x = "355"\n'
        'custom_viewport_y = "100"\n'
        'custom_viewport_width = "1206"\n'
        'custom_viewport_height = "762"\n'
    )



def test_native_nes_shader_runtime_descriptor_is_production_owned():
    from pathlib import Path

    shader_descriptor = (
        Path(__file__).resolve().parents[1]
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic.shader.cfg"
    )

    assert shader_descriptor.is_file()

    text = shader_descriptor.read_text(
        encoding="utf-8"
    )

    assert (
        'HSM_NON_INTEGER_SCALE = "100.000000"'
        in text
    )
    assert (
        'HSM_SCREEN_POSITION_Y = "0.000000"'
        in text
    )

    hsm_parameters = {
        line.split("=", 1)[0].strip()
        for line in text.splitlines()
        if line.strip().startswith("HSM_")
    }

    assert hsm_parameters == {
        "HSM_NON_INTEGER_SCALE",
        "HSM_SCREEN_POSITION_Y",
    }

    assert "minimal" in text.lower()
    assert "no unwanted thick black inset" in text.lower()


def test_native_nes_geometry_is_system_level_not_game_specific(
    tmp_path,
):
    """
    The human-approved NES geometry belongs to the native NES visual
    package, not to an individual ROM/title.

    Different NES games launched with the same production overlay must
    therefore resolve the same RetroArch geometry and shader correction.
    """
    from pathlib import Path

    from services.retroarch.overlay_runtime import (
        OverlayRuntimeConfig,
    )
    from services.retroarch.shader_runtime import (
        ShaderRuntimeConfig,
    )

    repository_root = Path(__file__).resolve().parents[1]

    overlay = (
        repository_root
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic.cfg"
    )

    assert overlay.is_file()

    expected_runtime_lines = {
        'aspect_ratio_index = "22"',
        'video_force_aspect = "true"',
        'video_aspect_ratio = "-1.000000"',
        'video_aspect_ratio_auto = "false"',
        'video_crop_overscan = "false"',
        'video_scale_integer = "false"',
        'video_viewport_bias_x = "0.500000"',
        'video_viewport_bias_y = "0.500000"',
        'custom_viewport_x = "355"',
        'custom_viewport_y = "100"',
        'custom_viewport_width = "1206"',
        'custom_viewport_height = "762"',
    }

    expected_shader_parameters = {
        "HSM_NON_INTEGER_SCALE": "100.000000",
        "HSM_SCREEN_POSITION_Y": "0.000000",
    }

    # Deliberately use unrelated ROM identities. Geometry composition
    # receives only the system-level overlay and therefore must remain
    # invariant across titles.
    games = (
        tmp_path / "Alpha Game.nes",
        tmp_path / "Beta Game.nes",
        tmp_path / "Random Validation Title.nes",
    )

    runtime_payloads = []
    shader_parameter_sets = []

    runtime = OverlayRuntimeConfig(
        tmp_path / "overlay-runtime"
    )

    for game in games:
        game.write_bytes(b"NES")

        generated = Path(
            runtime.create(
                str(overlay)
            )
        )

        payload = generated.read_text(
            encoding="utf-8"
        )

        for line in expected_runtime_lines:
            assert line in payload

        parameters = (
            ShaderRuntimeConfig
            .parameters_for_overlay(
                str(overlay)
            )
        )

        assert parameters == expected_shader_parameters

        runtime_payloads.append(payload)
        shader_parameter_sets.append(parameters)

    assert len(set(runtime_payloads)) == 1

    assert all(
        parameters == expected_shader_parameters
        for parameters in shader_parameter_sets
    )

    # Guard the architectural invariant directly: no ROM identity is
    # embedded in or consulted by the geometry descriptors.
    runtime_descriptor = overlay.with_suffix(
        ".runtime.cfg"
    ).read_text(
        encoding="utf-8"
    )

    shader_descriptor = overlay.with_suffix(
        ".shader.cfg"
    ).read_text(
        encoding="utf-8"
    )

    for game in games:
        assert game.name not in runtime_descriptor
        assert game.name not in shader_descriptor

def test_nes_classic_runtime_explicitly_owns_all_retroarch_geometry():
    runtime_path = (
        Path(__file__).resolve().parents[1]
        / "retrovault"
        / "nes"
        / "classic"
        / "RetroVault_NES_Classic.runtime.cfg"
    )

    text = runtime_path.read_text(encoding="utf-8")

    required = (
        'aspect_ratio_index = "22"',
        'video_force_aspect = "true"',
        'video_aspect_ratio = "-1.000000"',
        'video_aspect_ratio_auto = "false"',
        'video_crop_overscan = "false"',
        'video_scale_integer = "false"',
        'video_viewport_bias_x = "0.500000"',
        'video_viewport_bias_y = "0.500000"',
        'custom_viewport_x = "355"',
        'custom_viewport_y = "100"',
        'custom_viewport_width = "1206"',
        'custom_viewport_height = "762"',
    )

    for line in required:
        assert line in text
