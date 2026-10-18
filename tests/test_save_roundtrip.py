import pytest
from scripts.qualify_save_roundtrip import validate_restart


def test_reload_requires_fresh_process_and_exact_persisted_files():
    evidence = {'success': True, 'phase': 'create', 'pid': 101,
                'saves_after': {'game.srm': 'sha', 'game.state': 'state-sha'}}
    validate_restart(evidence, dict(evidence['saves_after']), 102)
    with pytest.raises(ValueError, match='fresh application'):
        validate_restart(evidence, evidence['saves_after'], 101)
    with pytest.raises(ValueError, match='changed'):
        validate_restart(evidence, {'game.srm': 'changed'}, 102)


@pytest.mark.parametrize('previous', [ {}, {'success': False},
    {'success': True, 'phase': 'reload'},
    {'success': True, 'phase': 'create', 'pid': 1, 'saves_after': {}}])
def test_reload_rejects_incomplete_or_empty_evidence(previous):
    with pytest.raises(ValueError):
        validate_restart(previous, {}, 2)


def test_state_only_does_not_require_sram_or_accept_screenshot(tmp_path):
    from types import SimpleNamespace
    from scripts.qualify_save_roundtrip import validate_saved_files
    context = SimpleNamespace(states=tmp_path / 'states', sram=tmp_path / 'sram')
    context.states.mkdir()
    screenshot = context.states / 'Game.state.png'
    screenshot.write_bytes(b'picture')
    with pytest.raises(ValueError, match='state'):
        validate_saved_files(context, {str(screenshot): 'sha'}, True)
    state = context.states / 'Game.state'
    state.write_bytes(b'state')
    files = {str(state): 'sha'}
    validate_saved_files(context, files, True)
    with pytest.raises(ValueError, match='sram'):
        validate_saved_files(context, files)


def test_native_state_extension_remains_supported(tmp_path):
    from types import SimpleNamespace
    from scripts.qualify_save_roundtrip import validate_saved_files
    state = tmp_path / 'Game.000'
    state.write_bytes(b'state')
    validate_saved_files(SimpleNamespace(states=tmp_path, sram=tmp_path / 'sram'),
                         {str(state): 'sha'}, True)
