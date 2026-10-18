import json
from pathlib import Path
import pytest
from PIL import Image
from services.presentation.production_package import ProductionPresentationPackageValidator
from services.presentation.production_glass import ProductionGlassResolver
from services.presentation.master_profile import MasterPresentationClass
from services.presentation.platform_policy import PlatformPresentationPolicyRegistry

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / 'retrovault/master-system/classic'
STEM = 'RetroVault_Master_System_Classic'


def test_master_system_package_contains_content_inside_transparent_opening():
    package = ProductionPresentationPackageValidator.validate(
        platform_id='platform.sega.master.system', core_identity='genesis_plus_gx',
        overlay=str(PACKAGE / (STEM+'.cfg')), shader=str(PACKAGE / (STEM+'_CRT.slangp')))
    glass = package.fixed_glass()
    image = Image.open(PACKAGE / (STEM+'.png'))
    assert image.getchannel('A').crop((274,72,1398,736)).getextrema() == (0,0)
    assert (glass.x,glass.y,glass.width,glass.height)==(315,83,1290,761)
    assert glass.x >= 274 * 1920 / image.width
    assert glass.y >= 72 * 1080 / image.height
    assert glass.x+glass.width <= 1398 * 1920 / image.width
    assert glass.y+glass.height <= 736 * 1080 / image.height
    profile=glass.as_master_profile(profile_class=MasterPresentationClass.CLASSIC_4_3)
    for aspect in (1.524,4/3,16/9):
        g=profile.contain_aspect(aspect,1)
        assert glass.x <= g.x and glass.y <= g.y
        assert g.x+g.width <= glass.x+glass.width
        assert g.y+g.height <= glass.y+glass.height
        assert abs(g.width-g.height*aspect)<=1


def test_shared_core_platform_policies_remain_separate():
    sms=PlatformPresentationPolicyRegistry.resolve(platform_id='platform.sega.master.system',core_identity='genesis_plus_gx')
    genesis=PlatformPresentationPolicyRegistry.resolve(platform_id='platform.sega.genesis',core_identity='genesis_plus_gx')
    assert sms.platform_id != genesis.platform_id
    assert dict(genesis.core_options)=={}
    assert dict(sms.core_options)=={'genesis_plus_gx_overscan':'disabled'}
    with pytest.raises(ValueError,match='does not match'):
        ProductionPresentationPackageValidator.validate(platform_id=sms.platform_id,core_identity='genesis_plus_gx',
            overlay=str(ROOT/'retrovault/genesis/classic/RetroVault_Genesis_Classic.cfg'),
            shader=str(ROOT/'retrovault/genesis/classic/RetroVault_Genesis_Classic_CRT.slangp'))
