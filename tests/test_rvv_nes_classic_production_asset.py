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
        "width": 1188,
        "height": 751,
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
