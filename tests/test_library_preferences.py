"""USQE 2 application preference contract; all persistence is isolated."""
import json
import pytest
from config.loader import ConfigLoader
from config.writer import ConfigWriter
from config.library_preferences import LibraryPreferences
from services.settings.service import SettingsService


@pytest.fixture
def loader(tmp_path):
    defaults = tmp_path / 'defaults.yaml'
    defaults.write_text('retroarch:\n  executable: retroarch\n')
    return ConfigLoader(defaults, tmp_path / 'runtime.json')


def test_defaults_do_not_write(loader):
    assert LibraryPreferences.from_config(loader.load()) == LibraryPreferences()
    assert not loader.runtime_file.exists()


@pytest.mark.parametrize('field,values', [
    ('opening_view', ('gallery', 'details', 'compact')),
    ('card_size', ('small', 'default', 'large')),
    ('normal_sort', ('name', 'year')),
])
def test_valid_values(loader, field, values):
    for value in values:
        loader.runtime_file.write_text(json.dumps({'library': {'display': {field: value}}}))
        assert getattr(LibraryPreferences.from_config(loader.load()), field) == value


@pytest.mark.parametrize('bad', [None, [], 1, True, 'obsolete', {}])
@pytest.mark.parametrize('field', ['opening_view', 'card_size', 'normal_sort'])
def test_invalid_field_falls_back_but_submission_rejected(loader, field, bad):
    payload = {'library': {'display': {field: bad, 'future_key': 'keep'}}}
    original = json.dumps(payload)
    loader.runtime_file.write_text(original)
    loaded = loader.load()
    assert getattr(LibraryPreferences.from_config(loaded), field) == getattr(LibraryPreferences(), field)
    assert loaded['library']['display']['future_key'] == 'keep'
    assert loader.runtime_file.read_text() == original
    with pytest.raises(ValueError):
        LibraryPreferences.from_values({**LibraryPreferences().to_dict(), field: bad})
    with pytest.raises(ValueError):
        ConfigWriter(loader.runtime_file).update(payload)


@pytest.mark.parametrize('bad', [None, [], 'old', 1])
def test_bad_display_falls_back(loader, bad):
    loader.runtime_file.write_text(json.dumps({'library': {'display': bad}}))
    assert LibraryPreferences.from_config(loader.load()) == LibraryPreferences()


def test_unrelated_invalid_config_still_fails(loader):
    loader.runtime_file.write_text('{"library":{"sources":"bad","display":null}}')
    with pytest.raises(ValueError):
        loader.load()


def test_save_preserves_unknown_and_restarts(loader):
    loader.runtime_file.write_text('{"custom":42,"library":{"display":{"future":true},"sources":[]}}')
    service = SettingsService(loader)
    prefs = LibraryPreferences('compact', 'large', 'year')
    result = service.save_library_preferences(prefs.to_dict())
    assert not result.refresh_error
    assert LibraryPreferences.from_config(loader.load()) == prefs
    saved = json.loads(loader.runtime_file.read_text())
    assert saved['custom'] == 42 and saved['library']['display']['future'] is True
    assert saved['library']['sources'] == []


def test_failed_write_retains_bytes(loader, monkeypatch):
    loader.runtime_file.write_text('{"custom":42}')
    service = SettingsService(loader)
    before = loader.runtime_file.read_bytes()
    import config.writer as writer
    monkeypatch.setattr(writer.os, 'replace', lambda *a: (_ for _ in ()).throw(OSError('blocked')))
    with pytest.raises(OSError):
        service.save_library_preferences(LibraryPreferences('details').to_dict())
    assert loader.runtime_file.read_bytes() == before
    assert not list(loader.runtime_file.parent.glob('*.tmp'))


def test_saved_with_failed_reread(loader, monkeypatch):
    service = SettingsService(loader)
    original = loader.load
    calls = 0
    def load():
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError('reread unavailable')
        return original()
    monkeypatch.setattr(loader, 'load', load)
    prefs = LibraryPreferences('details', 'small', 'year')
    result = service.save_library_preferences(prefs.to_dict())
    assert 'reread unavailable' in result.refresh_error
    assert LibraryPreferences.from_config(result.config) == prefs
    assert LibraryPreferences.from_config(original()) == prefs


@pytest.mark.parametrize('phase', ['serialization', 'write', 'flush', 'fsync', 'replace'])
def test_atomic_failure_phases(loader, monkeypatch, phase):
    import config.writer as writer
    from pathlib import Path
    loader.runtime_file.write_text('{"unrelated":true}')
    service = SettingsService(loader)
    before = loader.runtime_file.read_bytes()
    def fail(*args, **kwargs):
        raise OSError('injected ' + phase)
    if phase == 'serialization':
        monkeypatch.setattr(writer.json, 'dumps', fail)
    elif phase in ('fsync','replace'):
        monkeypatch.setattr(writer.os, phase, fail)
    else:
        original = Path.open
        class FailingHandle:
            def __init__(self, handle): self.handle = handle
            def __enter__(self): self.handle.__enter__();return self
            def __exit__(self, *args): return self.handle.__exit__(*args)
            def write(self, data):
                if phase == 'write':
                    self.handle.write(data[:8]);fail()
                return self.handle.write(data)
            def flush(self):
                if phase == 'flush': fail()
                return self.handle.flush()
            def fileno(self): return self.handle.fileno()
        def open_file(path, *args, **kwargs):
            handle = original(path, *args, **kwargs)
            return FailingHandle(handle) if str(path).endswith('.tmp') else handle
        monkeypatch.setattr(Path, 'open', open_file)
    with pytest.raises(OSError, match='injected'):
        service.save_library_preferences(LibraryPreferences('compact').to_dict())
    assert loader.runtime_file.read_bytes() == before
    assert not list(loader.runtime_file.parent.glob('*.tmp'))
