import pytest
from scripts.qualify_save_paths import probe_settings


def test_probe_preserves_naming_flags_but_redirects_storage(tmp_path):
    flags, values = probe_settings('sort_savefiles_enable = "true"\n'
                                  'savefiles_in_content_dir = "false"\n'
                                  'savefile_directory = "/user/saves"\n', tmp_path)
    assert flags['sort_savefiles_enable'] == values['sort_savefiles_enable'] == 'true'
    assert values['savefile_directory'] == str(tmp_path / 'saves')
    assert values['config_save_on_exit'] == 'false'
    assert values['global_core_options'] == 'true'
    assert values['rgui_config_directory'] == str(tmp_path / 'core-config')
    assert values['network_cmd_enable'] == 'false'


@pytest.mark.parametrize('text', ['#include "another.cfg"\n',
    'sort_savefiles_enable = "true"\nsort_savefiles_enable = "false"\n'])
def test_probe_rejects_ambiguous_authority(text, tmp_path):
    with pytest.raises(ValueError):
        probe_settings(text, tmp_path)
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('code', [0, -15])
def test_controlled_stop_requires_saved_bytes_and_core_unload(tmp_path, code):
    from scripts.qualify_save_paths import stopped_save_evidence
    save = tmp_path / 'fixture.srm'
    save.write_bytes(b'fixture')
    log = f'[SRAM] Saved successfully to "{save}".\n[Core] Unloading game...'
    assert stopped_save_evidence(code, log, tmp_path, False) == [str(save)]


@pytest.mark.parametrize('code,alive,log', [(-9, False, ''), (1, False, ''),
    (-15, True, ''), (-15, False, ''), (0, False, '[Core] Unloading game...')])
def test_stop_status_alone_does_not_prove_save(tmp_path, code, alive, log):
    from scripts.qualify_save_paths import stopped_save_evidence
    with pytest.raises(RuntimeError):
        stopped_save_evidence(code, log, tmp_path, alive)


def test_save_evidence_cannot_escape_isolated_root(tmp_path):
    from scripts.qualify_save_paths import stopped_save_evidence
    save = tmp_path / 'outside.srm'
    save.write_bytes(b'fixture')
    root = tmp_path / 'isolated'
    root.mkdir()
    log = f'[SRAM] Saved successfully to "{save}".\n[Core] Unloading game...'
    with pytest.raises(RuntimeError):
        stopped_save_evidence(-15, log, root, False)
