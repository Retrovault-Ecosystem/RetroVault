#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw


CANVAS_WIDTH = 1920
CANVAS_HEIGHT = 1080

# Genesis Classic owns its own physical presentation geometry.
#
# These coordinates are part of this artwork composition itself.
# They are NOT copied from NES/SNES and are NOT derived from any ROM,
# title, source raster, or emulated framebuffer.
#
# The glass is intentionally centered on the 1920x1080 presentation
# canvas and provides a large 4:3-family presentation region. Runtime
# content will later be CONTAINed within this fixed physical glass using
# the core-reported display aspect.
GLASS_X = 330
GLASS_Y = 90
GLASS_WIDTH = 1260
GLASS_HEIGHT = 900

OUTPUT = Path(
    "retrovault/genesis/classic/"
    "RetroVault_Genesis_Classic.png"
)


def _rect(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    fill: tuple[int, int, int, int],
) -> None:
    draw.rectangle(box, fill=fill)


def build() -> Image.Image:
    image = Image.new(
        "RGBA",
        (CANVAS_WIDTH, CANVAS_HEIGHT),
        (0, 0, 0, 0),
    )

    draw = ImageDraw.Draw(image, "RGBA")

    x = GLASS_X
    y = GLASS_Y
    w = GLASS_WIDTH
    h = GLASS_HEIGHT

    left = x
    top = y
    right = x + w
    bottom = y + h

    # ------------------------------------------------------------------
    # GENESIS CLASSIC VISUAL LANGUAGE
    #
    # Original RetroVault composition:
    #   - charcoal/black console-era surround
    #   - restrained metallic graphite layering
    #   - thin cool highlight around the physical glass
    #   - lower control-deck treatment inspired by the horizontal,
    #     understated industrial language of the Genesis hardware
    #
    # No Sega/Genesis trademarks, logos, copyrighted console artwork,
    # or copied bezel assets are embedded.
    # ------------------------------------------------------------------

    # Outer presentation field.
    _rect(
        draw,
        (0, 0, CANVAS_WIDTH - 1, CANVAS_HEIGHT - 1),
        (12, 13, 15, 255),
    )

    # Upper graphite band.
    _rect(
        draw,
        (0, 0, CANVAS_WIDTH - 1, 54),
        (24, 26, 29, 255),
    )
    _rect(
        draw,
        (0, 55, CANVAS_WIDTH - 1, 61),
        (47, 50, 54, 255),
    )

    # Side body fields.
    _rect(
        draw,
        (0, 62, left - 1, CANVAS_HEIGHT - 1),
        (18, 19, 22, 255),
    )
    _rect(
        draw,
        (right, 62, CANVAS_WIDTH - 1, CANVAS_HEIGHT - 1),
        (18, 19, 22, 255),
    )

    # Lower deck.
    _rect(
        draw,
        (left, bottom, right - 1, CANVAS_HEIGHT - 1),
        (17, 18, 21, 255),
    )

    # Symmetric metallic rails.
    _rect(
        draw,
        (left - 20, top - 20, right + 19, top - 13),
        (70, 73, 77, 255),
    )
    _rect(
        draw,
        (left - 20, bottom + 12, right + 19, bottom + 19),
        (70, 73, 77, 255),
    )
    _rect(
        draw,
        (left - 20, top - 12, left - 13, bottom + 11),
        (58, 61, 65, 255),
    )
    _rect(
        draw,
        (right + 12, top - 12, right + 19, bottom + 11),
        (58, 61, 65, 255),
    )

    # Inner dark frame.
    _rect(
        draw,
        (left - 12, top - 12, right + 11, top - 5),
        (5, 6, 7, 255),
    )
    _rect(
        draw,
        (left - 12, bottom + 4, right + 11, bottom + 11),
        (5, 6, 7, 255),
    )
    _rect(
        draw,
        (left - 12, top - 4, left - 5, bottom + 3),
        (5, 6, 7, 255),
    )
    _rect(
        draw,
        (right + 4, top - 4, right + 11, bottom + 3),
        (5, 6, 7, 255),
    )

    # Thin cool glass highlight.
    _rect(
        draw,
        (left - 4, top - 4, right + 3, top - 1),
        (122, 128, 136, 255),
    )
    _rect(
        draw,
        (left - 4, bottom, right + 3, bottom + 3),
        (74, 78, 84, 255),
    )
    _rect(
        draw,
        (left - 4, top, left - 1, bottom - 1),
        (106, 111, 118, 255),
    )
    _rect(
        draw,
        (right, top, right + 3, bottom - 1),
        (68, 72, 78, 255),
    )

    # Lower-deck horizontal detailing.
    deck_y = bottom + 44

    _rect(
        draw,
        (left + 34, deck_y, right - 35, deck_y + 3),
        (45, 48, 52, 255),
    )
    _rect(
        draw,
        (left + 92, deck_y + 22, right - 93, deck_y + 25),
        (29, 31, 35, 255),
    )

    # Small symmetric hardware-style accents.
    accent_w = 86
    accent_h = 8
    accent_y = bottom + 64

    _rect(
        draw,
        (
            left + 68,
            accent_y,
            left + 68 + accent_w,
            accent_y + accent_h,
        ),
        (73, 76, 81, 255),
    )
    _rect(
        draw,
        (
            right - 68 - accent_w,
            accent_y,
            right - 68,
            accent_y + accent_h,
        ),
        (73, 76, 81, 255),
    )

    # THE PHYSICAL GLASS.
    #
    # This is the single authoritative transparent aperture. Nothing
    # inside this rectangle belongs to the bezel. Runtime content is
    # composited here later using dynamic CONTAIN.
    _rect(
        draw,
        (
            left,
            top,
            right - 1,
            bottom - 1,
        ),
        (0, 0, 0, 0),
    )

    return image


def main() -> None:
    image = build()

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    image.save(
        OUTPUT,
        format="PNG",
        optimize=False,
    )

    print(OUTPUT)
    print(
        f"canvas={CANVAS_WIDTH}x{CANVAS_HEIGHT}"
    )
    print(
        "glass="
        f"{GLASS_X},{GLASS_Y},"
        f"{GLASS_WIDTH},{GLASS_HEIGHT}"
    )


if __name__ == "__main__":
    main()
