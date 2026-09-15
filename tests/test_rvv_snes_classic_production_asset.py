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
    / "rvv_snes_classic.json"
)

ASSET_ROOT = (
    ROOT
    / "retrovault"
    / "snes"
    / "classic"
)

PNG = ASSET_ROOT / "RetroVault_SNES_Classic_1080p.png"
CFG = ASSET_ROOT / "RetroVault_SNES_Classic.cfg"
RUNTIME = ASSET_ROOT / "RetroVault_SNES_Classic.runtime.cfg"
SHADER = ASSET_ROOT / "RetroVault_SNES_Classic.shader.cfg"
META = ASSET_ROOT / "RetroVault_SNES_Classic.production.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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


def decode_rgba_png(path: Path):
    raw = path.read_bytes()

    assert raw[:8] == b"\x89PNG\r\n\x1a\n"

    position = 8
    width = height = None
    bit_depth = color_type = interlace = None
    idat = bytearray()

    while position < len(raw):
        length = struct.unpack(
            ">I",
            raw[position:position + 4],
        )[0]

        kind = raw[position + 4:position + 8]
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
            ) = struct.unpack(">IIBBBBB", data)

            assert compression == 0
            assert filter_method == 0

        elif kind == b"IDAT":
            idat.extend(data)

        elif kind == b"IEND":
            break

        position = end + 4

    assert width == 1920
    assert height == 1080
    assert bit_depth == 8
    assert color_type == 6
    assert interlace == 0

    decoded = zlib.decompress(bytes(idat))

    row_bytes = width * 4
    rows = []
    offset = 0

    for y in range(height):
        filter_type = decoded[offset]
        offset += 1

        scanline = bytearray(
            decoded[offset:offset + row_bytes]
        )
        offset += row_bytes

        previous = (
            rows[y - 1]
            if y > 0
            else bytearray(row_bytes)
        )

        reconstructed = bytearray(row_bytes)

        for i, value in enumerate(scanline):
            left = (
                reconstructed[i - 4]
                if i >= 4
                else 0
            )
            up = previous[i]
            upper_left = (
                previous[i - 4]
                if i >= 4
                else 0
            )

            if filter_type == 0:
                result = value
            elif filter_type == 1:
                result = (value + left) & 0xFF
            elif filter_type == 2:
                result = (value + up) & 0xFF
            elif filter_type == 3:
                result = (
                    value + ((left + up) // 2)
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
                    f"Unsupported PNG filter: {filter_type}"
                )

            reconstructed[i] = result

        rows.append(reconstructed)

    return width, height, rows


def test_snes_production_package_exists():
    for path in (
        PNG,
        CFG,
        RUNTIME,
        SHADER,
        META,
    ):
        assert path.is_file()


def test_snes_production_png_is_rgba_1080p():
    width, height, _ = decode_rgba_png(PNG)
    assert (width, height) == (1920, 1080)


def test_snes_production_alpha_contract():
    width, height, rows = decode_rgba_png(PNG)

    transparent = 0
    partial = 0
    opaque = 0

    for y in range(height):
        for x in range(width):
            alpha = rows[y][(x * 4) + 3]

            if alpha == 0:
                transparent += 1
            elif alpha == 255:
                opaque += 1
            else:
                partial += 1

    assert transparent > 0
    assert partial > 0
    assert opaque > 0

    assert rows[540][(960 * 4) + 3] == 0
    assert rows[10][(10 * 4) + 3] == 255


def test_snes_manifest_declares_blended_screen():
    meta = load_json(META)

    assert meta["canvas"] == {
        "width": 1920,
        "height": 1080,
    }

    alpha = meta["alpha_presentation"]

    assert alpha["mode"] == "blended_screen"
    assert alpha["center"] == "fully_transparent"
    assert (
        alpha["edge_transition"]
        == "partially_transparent"
    )
    assert alpha["outer_bezel"] == "fully_opaque"


def test_snes_overlay_cfg_is_portable():
    text = CFG.read_text(encoding="utf-8")

    assert 'overlays = "1"' in text
    assert (
        'overlay0_overlay = '
        '"RetroVault_SNES_Classic_1080p.png"'
        in text
    )
    assert "overlay0_full_screen = true" in text
    assert "overlay0_descs = 0" in text
    assert "input_overlay" not in text
    assert "/home/" not in text


def test_snes_runtime_descriptor_is_owned():
    text = RUNTIME.read_text(encoding="utf-8")

    required = (
        'aspect_ratio_index = "23"',
        'video_force_aspect = "true"',
        'video_scale_integer = "false"',
        'custom_viewport_width = "1044"',
        'custom_viewport_height = "783"',
        'video_viewport_bias_x = "0.500000"',
        'video_viewport_bias_y = "0.239057239"',
    )

    for value in required:
        assert value in text

def test_snes_shader_descriptor_preserves_approved_crt_contract():
    text = SHADER.read_text(encoding="utf-8")

    required = (
        'post_br = "2.200000"',
        'bloom = "0.100000"',
        'scans = "0.500000"',
        'beam_max = "1.100000"',
        'scanline1 = "6.000000"',
        'scanline2 = "8.000000"',
        'shadowMask = "6.000000"',
        'maskstr = "0.500000"',
        'HSM_CURVATURE_MODE = "0.000000"',
        'HSM_NON_INTEGER_SCALE = "100.000000"',
    )

    for value in required:
        assert value in text

def test_snes_spec_tracks_validated_production_package():
    data = load_json(SPEC)

    assert data["production_assets"]["status"] == "production_validated"

    validation = data["production_validation"]

    assert validation["status"] == "pass"
    assert validation["geometry"]["viewport"] == {
        "x": 438,
        "y": 71,
        "width": 1044,
        "height": 783,
    }
    assert validation["geometry"]["aspect_ratio"] == "4:3"
