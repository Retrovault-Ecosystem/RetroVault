import json
from types import SimpleNamespace
import pytest
from services.presentation.visual_tuning import controls, validate_values, validate_state, resolve_values, shader_parameters
from services.presentation.store import PresentationStore
from services.presentation.models import PresentationProfile
from services.library.presentation_studio import LibraryPresentationStudioService

NES='platform.nintendo.nes'
GEN='platform.sega.genesis'

@pytest.mark.parametrize('value', [float('nan'),float('inf'), True, '1.0', -1, 4])
def test_invalid_value_rejected(value):
    with pytest.raises(ValueError): validate_values(NES, {'brightness':value})

@pytest.mark.parametrize('key', ['HSM_SCREEN_POSITION_Y','shader','unknown','scanline_strength'])
def test_no_raw_or_unsupported_parameters(key):
    with pytest.raises(ValueError): validate_values(NES,{key:1})


def test_store_old_versions_preserved_and_tuning_round_trip(tmp_path):
    path=tmp_path/'state.json'
    original=dict(version=2,default=dict(shader='keep.slangp'),systems={},games={})
    path.write_text(json.dumps(original))
    store=PresentationStore(path)
    assert store.load()['default'].shader=='keep.slangp'
    assert json.loads(path.read_text())==original  # reads do not migrate
    store.set_visual_tuning('systems',NES,NES,{'brightness':1.3})
    store.assign_game_overlay('local-file:test','keep.cfg')
    state=store.load()
    assert state['default'].shader=='keep.slangp'
    assert state['games']['local-file:test'].overlay=='keep.cfg'
    assert resolve_values(state['visual_tuning'],NES,'local-file:test')=={'brightness':1.3}
    assert json.loads(path.read_text())['version']==3


def test_scope_inherit_and_reset_semantics(tmp_path):
    store=PresentationStore(tmp_path/'state.json')
    service=LibraryPresentationStudioService(presentation_store=store)
    game=SimpleNamespace(rvdb_platform_id=NES,local_file_id='local-file:a',rom='/a.nes')
    service.set_visual_adjustment(game,'systems','brightness','custom',1.4)
    service.set_visual_adjustment(game,'games','brightness','custom',1.6)
    assert service.visual_tuning_state(game)['effective']['brightness']==1.6
    service.set_visual_adjustment(game,'games','brightness','inherit')
    assert service.visual_tuning_state(game)['effective']['brightness']==1.4
    service.restore_approved_visuals(game,'games')
    assert shader_parameters(NES,service.visual_tuning_state(game)['effective'])=={}
    assert store.load()['visual_tuning']['systems'][NES]['brightness']==1.4
    service.restore_approved_visuals(game,'systems')
    assert store.load()['visual_tuning']['systems']=={}


def test_cross_platform_game_tuning_rejected(tmp_path):
    store=PresentationStore(tmp_path/'state.json')
    store.set_visual_tuning('games','local-file:a',NES,{'brightness':1.3})
    with pytest.raises(ValueError,match='platform'):
        resolve_values(store.load()['visual_tuning'],GEN,'local-file:a')


def test_serialization_rejects_newline_values(tmp_path):
    from services.retroarch.shader_runtime import ShaderRuntimeConfig
    preset=tmp_path/'source.slangp';preset.write_text('shaders = "0"')
    runtime=ShaderRuntimeConfig(tmp_path/'runtime')
    with pytest.raises(ValueError):runtime.resolve(str(preset),{'x':'1\nshader0="evil"'})
    assert not (tmp_path/'runtime').exists()


def test_genesis_defaults_are_neutral_and_geometry_fixed():
    from pathlib import Path
    text=Path('retrovault/shaders/retrovault/genesis/classic/RetroVault_Genesis_Classic_CRT.slang').read_text()
    assert 'gl_Position = global.MVP * Position;' in text
    assert '"Brightness" 1.0' in text
    assert '"Mask strength" 0.0' in text
    assert '"Scanline strength" 0.0' in text
    assert shader_parameters(GEN,{'brightness':1.1,'mask_strength':0.2})=={'RVV_BRIGHTNESS':'1.1','RVV_MASK_STRENGTH':'0.2'}


def test_snes_sidecar_follows_viewport():
    from pathlib import Path
    assert 'HSM_ASPECT_RATIO_MODE = "6.000000"' in Path('retrovault/snes/classic/RetroVault_SNES_Classic.shader.cfg').read_text()


def test_studio_controls_save_inherit_and_approved(tmp_path):
    from PyQt6.QtWidgets import QApplication
    from services.presentation.launch_resolver import LaunchPresentationResolver
    from services.presentation.models import LaunchPresentation
    from ui.library.widgets.presentation_studio import PresentationStudio
    app=QApplication.instance() or QApplication([])
    store=PresentationStore(tmp_path/'state.json')
    resolver=LaunchPresentationResolver()
    resolver.describe=lambda game: LaunchPresentation(PresentationProfile(),PresentationProfile(),
        authority='production package',package=SimpleNamespace())
    studio=PresentationStudio(store,lambda:resolver)
    game=SimpleNamespace(name='Game',rvdb_platform_id=GEN,local_file_id='local-file:a',rom='/a.md')
    studio.set_game(game)
    assert studio.tuning_control.count()==3
    studio.tuning_mode.setCurrentIndex(studio.tuning_mode.findData('custom'))
    studio.tuning_value.setValue(1.3)
    studio.tuning_apply.click()
    assert store.load()['visual_tuning']['games']['local-file:a']['values']['brightness']==1.3
    studio.tuning_reset.click()
    assert store.load()['visual_tuning']['games']['local-file:a']['values']['brightness'] is None
    studio.tuning_mode.setCurrentIndex(studio.tuning_mode.findData('inherit'))
    studio.tuning_apply.click()
    assert 'brightness' not in store.load()['visual_tuning']['games']['local-file:a']['values']
    studio.close()
