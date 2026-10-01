#!/usr/bin/env python3
"""Normalize the approved Model 1 artwork; never regenerate its branding.

Run design/branding-review/refine_branding.py first when rebuilding from the
immutable generated source. The package owns the opening; the existing runtime
contains core-reported content inside it and adapts only the inner bezel.
"""
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'design/genesis-model1/Genesis_Model1_branded.png'
OUTPUT = ROOT / 'retrovault/genesis/classic/RetroVault_Genesis_Classic.png'
CANVAS_WIDTH, CANVAS_HEIGHT = 1920, 1080
GLASS_X, GLASS_Y, GLASS_WIDTH, GLASS_HEIGHT = 312, 80, 1296, 770


def build() -> Image.Image:
    with Image.open(SOURCE) as source:
        image = source.convert('RGBA').resize(
            (CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
    # Generation left stray alpha in the casing and gameplay field. Preserve
    # visible housing, composite stray transparent RGB onto black, and cut
    # one exact rectangular opening.
    image = Image.alpha_composite(Image.new('RGBA', image.size, (0, 0, 0, 255)), image)
    ImageDraw.Draw(image).rectangle(
        (GLASS_X, GLASS_Y, GLASS_X + GLASS_WIDTH - 1,
         GLASS_Y + GLASS_HEIGHT - 1), fill=(0, 0, 0, 0))
    return image


if __name__ == '__main__':
    build().save(OUTPUT)
    print(OUTPUT)
