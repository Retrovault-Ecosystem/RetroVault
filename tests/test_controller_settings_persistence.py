"""Controller intent uses the existing durable settings transaction."""
import json

import pytest

from config import ConfigLoader, ConfigWriter
from config.controller_preferences import defaults, DEFAULT_KEYS
from services.settings.service import SettingsService


@pytest.fixture
def settings(tmp_path):
    base = tmp_path / 'default.yaml'
    base.write_text('retroarch:\n  executable: retroarch\n')
    runtime = tmp_path / 'runtime.json'
    runtime.write_text(json.dumps({'extension': {'keep': 42}}))
    loader = ConfigLoader(default_file=base, runtime_file=runtime)
    return SettingsService(loader, ConfigWriter(runtime_file=runtime)), runtime


def keyboard_preferences():
    values = defaults()
    values['retroarch'] = dict(mode='managed', players=[
        dict(kind='keyboard', device={}, bindings=dict(DEFAULT_KEYS))])
    return values


def test_save_reload_reset_preserves_unrelated_preferences(settings):
    service, runtime = settings
    values = keyboard_preferences()
    service.save_controller_preferences(values)
    assert service.config_loader.load()['controllers'] == values
    assert json.loads(runtime.read_text())['extension'] == {'keep': 42}
    service.save_controller_preferences(defaults())
    assert service.config_loader.load()['controllers'] == defaults()
    assert json.loads(runtime.read_text())['extension'] == {'keep': 42}


def test_invalid_mapping_does_not_write(settings):
    service, runtime = settings
    before = runtime.read_bytes()
    values = keyboard_preferences()
    values['retroarch']['players'][0]['bindings']['a'] = 'F1'
    with pytest.raises(ValueError):
        service.save_controller_preferences(values)
    assert runtime.read_bytes() == before


def test_failed_write_preserves_previous_mapping_and_allows_retry(settings, monkeypatch):
    service, runtime = settings
    before = runtime.read_bytes()
    original = service.config_writer.update
    def fail(_):
        raise OSError('write blocked')
    monkeypatch.setattr(service.config_writer, 'update', fail)
    with pytest.raises(OSError):
        service.save_controller_preferences(keyboard_preferences())
    assert runtime.read_bytes() == before
    monkeypatch.setattr(service.config_writer, 'update', original)
    service.save_controller_preferences(keyboard_preferences())
    assert service.config_loader.load()['controllers'] == keyboard_preferences()


def test_successful_write_with_failed_reread_is_not_a_failed_save(settings, monkeypatch):
    service, runtime = settings
    load = service.config_loader.load
    calls = 0
    def loading():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError('reread failed')
        return load()
    monkeypatch.setattr(service.config_loader, 'load', loading)
    result = service.save_controller_preferences(keyboard_preferences())
    assert result.refresh_error == 'reread failed'
    assert result.config['controllers'] == keyboard_preferences()
    assert json.loads(runtime.read_text())['controllers'] == keyboard_preferences()


def test_loader_rejects_invalid_saved_controller_data(settings):
    service, runtime = settings
    runtime.write_text(json.dumps({'controllers': {'retroarch': 'invalid'}}))
    with pytest.raises(ValueError):
        service.config_loader.load()
