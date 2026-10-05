import json
from unittest.mock import Mock
import pytest
from config import ConfigLoader, ConfigWriter
from services.settings.service import SettingsService


def service(tmp_path, monkeypatch):
    defaults = tmp_path / 'defaults.yaml'
    defaults.write_text('retroarch:\n  executable: retroarch\nlibrary:\n  sources: []\n')
    runtime = tmp_path / 'runtime.json'
    loader = ConfigLoader(default_file=defaults, runtime_file=runtime)
    svc = SettingsService(loader, ConfigWriter(runtime_file=runtime))
    monkeypatch.setattr(svc, 'is_retroarch_executable', lambda value: True)
    values = dict(executable='retroarch', primary_config='', core_directory='',
                  library_path='', artwork_directory='', overlay_directory='')
    return svc, values, runtime


def test_saved_but_refresh_failed_is_explicit(tmp_path, monkeypatch):
    svc, values, runtime = service(tmp_path, monkeypatch)
    load = svc.config_loader.load
    calls = 0
    def loading():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError('Read failed after write')
        return load()
    monkeypatch.setattr(svc.config_loader, 'load', loading)
    values['executable'] = '/new/retroarch'
    result = svc.save(values)
    assert runtime.exists()
    assert result.restart_required
    assert result.config['retroarch']['executable'] == '/new/retroarch'
    assert 'Settings saved.' in result.message
    assert 'Unable to refresh' in result.message


def test_save_keeps_other_sources_and_settings(tmp_path, monkeypatch):
    svc, values, runtime = service(tmp_path, monkeypatch)
    sources = [dict(id='a',name='A',type='local',enabled=False,path='/a'),
               dict(id='b',name='B',type='local',enabled=True,path='/b')]
    runtime.write_text(json.dumps({'library': {'sources': sources}, 'extension': {'keep': True}}))
    values['library_path'] = str(tmp_path)
    result = svc.save(values)
    saved = json.loads(runtime.read_text())
    assert saved['library']['sources'][0] == sources[0]
    assert saved['library']['sources'][1]['path'] == str(tmp_path)
    assert saved['extension'] == {'keep': True}
    assert result.sources_changed


def test_invalid_input_does_not_write(tmp_path, monkeypatch):
    svc, values, runtime = service(tmp_path, monkeypatch)
    values['primary_config'] = str(tmp_path / 'missing.cfg')
    with pytest.raises(ValueError, match='does not exist'):
        svc.save(values)
    assert not runtime.exists()


def test_standalone_saved_but_refresh_failed(tmp_path, monkeypatch):
    svc, _, runtime = service(tmp_path, monkeypatch)
    runtime.write_text(json.dumps({'extension': {'keep': True}}))
    load = svc.config_loader.load
    reads = 0
    def loading():
        nonlocal reads
        reads += 1
        if reads == 2: raise OSError('reread failed')
        return load()
    monkeypatch.setattr(svc.config_loader, 'load', loading)
    result = svc.save_standalone('retroarch', '')
    assert result.refresh_error == 'reread failed'
    assert result.config['emulation']['snes_backend'] == 'retroarch'
    assert result.config['extension'] == {'keep': True}
    assert json.loads(runtime.read_text())['emulation']['snes_backend'] == 'retroarch'


def test_standalone_write_failure_is_not_saved(tmp_path, monkeypatch):
    svc, _, runtime = service(tmp_path, monkeypatch)
    monkeypatch.setattr(svc.config_writer, 'update', Mock(side_effect=OSError('write failed')))
    with pytest.raises(OSError, match='write failed'):
        svc.save_standalone('retroarch', '')
    assert not runtime.exists()
