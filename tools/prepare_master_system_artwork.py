"""User-authorized, alpha-only cutout of the approved Master System concept.

Native-resolution candidate only; no resize, recolor, or production activation.
Coordinates are exclusive right/bottom and sit inside the existing beveled frame.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageChops

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'design/master-system-model1/Master_System_Model1_concept_v1.png'
OUTPUT = ROOT / 'design/master-system-model1/Master_System_Model1_runtime_cutout.png'
APERTURE = (274, 72, 1398, 736)


def prepare():
    source_bytes = SOURCE.read_bytes()
    original = Image.open(SOURCE).convert('RGBA')
    if original.size != (1672, 941):
        raise ValueError('Approved source size changed; review aperture before processing.')
    result = original.copy()
    alpha = result.getchannel('A')
    alpha.paste(0, APERTURE)
    result.putalpha(alpha)
    result.save(OUTPUT)
    decoded = Image.open(OUTPUT).convert('RGBA')
    assert decoded.getchannel('A').crop(APERTURE).getextrema() == (0, 0)
    # Verify all channels separately: RGBA getbbox alone can hide RGB changes.
    for before, after in zip(original.split(), decoded.split()):
        difference = ImageChops.difference(before, after)
        difference.paste(0, APERTURE)
        assert difference.getbbox() is None, 'Pixels outside the aperture changed'
    assert original.convert('RGB').tobytes() == decoded.convert('RGB').tobytes()
    assert SOURCE.read_bytes() == source_bytes
    report = {
        'source': str(SOURCE.relative_to(ROOT)),
        'source_sha256': hashlib.sha256(source_bytes).hexdigest(),
        'output': str(OUTPUT.relative_to(ROOT)),
        'output_sha256': hashlib.sha256(OUTPUT.read_bytes()).hexdigest(),
        'native_canvas': list(original.size),
        'aperture_exclusive_bounds': list(APERTURE),
        'outside_aperture_pixels_identical': True,
        'all_rgb_pixels_identical': True,
        'aperture_alpha_range': [0, 0],
        'production_geometry_qualified': False,
    }
    OUTPUT.with_suffix('.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    prepare()
