import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from PyQt6.QtGui import QImage

from services.presentation.master_profile import MasterPresentationClass
from services.presentation.production_glass import ProductionGlassResolver
from services.retroarch.adaptive_bezel_runtime import AdaptiveBezelRuntime

ROOT = Path(__file__).resolve().parents[1]
OVERLAY = ROOT / 'retrovault/nes/classic/RetroVault_NES_Classic.cfg'


def package():
    return SimpleNamespace(overlay=str(OVERLAY),
                           production_manifest=str(OVERLAY.with_suffix('.production.json')))


@pytest.mark.parametrize('aspect', [(1.219, 1), (4, 3), (16, 9), (3, 2), (10, 9), (3, 4)])
def test_frame_has_exact_transparent_game_rectangle_and_preserves_outer_art(tmp_path, aspect):
    pkg = package()
    glass = ProductionGlassResolver.from_manifest(pkg.production_manifest)
    geometry = glass.as_master_profile(profile_class=MasterPresentationClass.CLASSIC_4_3).contain_aspect(*aspect)
    runtime = AdaptiveBezelRuntime(tmp_path)
    overlay = Path(runtime.create(package=pkg, glass=glass, geometry=geometry))
    result = QImage(str(overlay.parent / 'artwork.png'))
    source = QImage(str(OVERLAY.with_name('RetroVault_NES_Classic_1080p.png')))
    # Exhaustive alpha comparison catches rim overlap and residual old opening.
    for y in range(glass.y, glass.y + glass.height):
        for x in range(glass.x, glass.x + glass.width):
            inside = (geometry.x <= x < geometry.x + geometry.width
                      and geometry.y <= y < geometry.y + geometry.height)
            assert result.pixelColor(x, y).alpha() == (0 if inside else 255)
    for rect in [(0, 0, 319, 1080), (1597, 0, 323, 1080), (0, 898, 1920, 182)]:
        assert result.copy(*rect) == source.copy(*rect).convertToFormat(result.format())
    runtime.cleanup()
    assert not overlay.parent.exists()


def test_non_adaptive_package_keeps_original_overlay(tmp_path):
    manifest = tmp_path / 'manifest.json'
    manifest.write_text('{}')
    pkg = SimpleNamespace(production_manifest=str(manifest), overlay='original.cfg')
    assert AdaptiveBezelRuntime(tmp_path).create(package=pkg, glass=None, geometry=None) == 'original.cfg'
    assert list(tmp_path.iterdir()) == [manifest]


def test_invalid_frame_fails_before_artifacts(tmp_path):
    pkg = package()
    data = json.loads(Path(pkg.production_manifest).read_text())
    data['adaptive_frame']['frame'] = [-1, 0, 1, 1]
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps(data))
    pkg.production_manifest = str(manifest)
    glass = ProductionGlassResolver.from_manifest(str(manifest))
    with pytest.raises(ValueError, match='exceeds'):
        AdaptiveBezelRuntime(tmp_path).create(package=pkg, glass=glass, geometry=glass)
    assert list(tmp_path.iterdir()) == [manifest]


@pytest.mark.parametrize('aspect', [(1.524, 1), (1.306, 1), (4, 3)])
def test_approved_genesis_frame_fits_core_aspect_and_preserves_branding(tmp_path, aspect):
    from PIL import Image, ImageChops, ImageDraw

    overlay = ROOT / 'retrovault/genesis/classic/RetroVault_Genesis_Classic.cfg'
    pkg = SimpleNamespace(overlay=str(overlay),
                          production_manifest=str(overlay.with_suffix('.production.json')))
    glass = ProductionGlassResolver.from_manifest(pkg.production_manifest)
    geometry = glass.as_master_profile(
        profile_class=MasterPresentationClass.CLASSIC_4_3).contain_aspect(*aspect)
    runtime = AdaptiveBezelRuntime(tmp_path)
    generated = Path(runtime.create(package=pkg, glass=glass, geometry=geometry))
    with Image.open(generated.parent / 'artwork.png') as result, Image.open(
        overlay.with_suffix('.png')) as source:
        expected = Image.new('L', source.size, 255)
        ImageDraw.Draw(expected).rectangle(
            (geometry.x, geometry.y, geometry.x + geometry.width - 1,
             geometry.y + geometry.height - 1), fill=0)
        assert ImageChops.difference(result.getchannel('A'), expected).getbbox() is None
        # All controls, platform marks, paired rules and wordmarks stay untouched.
        diff = ImageChops.difference(result.convert('RGB'), source.convert('RGB'))
        ImageDraw.Draw(diff).rectangle((290, 60, 1629, 869), fill=(0, 0, 0))
        assert diff.getbbox() is None
    runtime.cleanup()
    assert not generated.parent.exists()
