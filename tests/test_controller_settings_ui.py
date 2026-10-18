from types import SimpleNamespace

import pytest
from PyQt6.QtWidgets import QApplication

from config import ConfigLoader, ConfigWriter
from config.controller_preferences import defaults
from services.settings.service import SettingsService
from ui.widgets.controller_settings import ControllerSettings


@pytest.fixture
def widget(tmp_path):
    app = QApplication.instance() or QApplication([])
    base = tmp_path / 'default.yaml'
    base.write_text('retroarch:\n  executable: retroarch\n')
    runtime = tmp_path / 'runtime.json'
    loader = ConfigLoader(default_file=base, runtime_file=runtime)
    service = SettingsService(loader, ConfigWriter(runtime_file=runtime))
    widget = ControllerSettings(service, device_inventory=SimpleNamespace(snapshot=lambda: []))
    yield widget, runtime
    widget.close()
    app.processEvents()


def test_preview_cancel_reset_and_apply_are_reversible(widget):
    editor, runtime = widget
    profile = editor.editors['retroarch']
    profile.mode.setCurrentIndex(1)
    profile.players[0].fields['a'].setText('c')
    editor.preview()
    assert 'Nothing was saved' in editor.status.text()
    assert not runtime.exists()
    editor.cancel()
    assert editor.value() == defaults()
    profile.mode.setCurrentIndex(1)
    profile.players[0].fields['a'].setText('c')
    editor.apply()
    saved = runtime.read_bytes()
    editor.reset()
    assert editor.value() == defaults()
    assert runtime.read_bytes() == saved
    editor.cancel()
    assert profile.players[0].fields['a'].text() == 'c'
    editor.reset()
    editor.apply()
    assert editor.service.config_loader.load()['controllers'] == defaults()


def test_failed_save_keeps_draft_for_retry(widget, monkeypatch):
    editor, runtime = widget
    editor.editors['snes9x'].mode.setCurrentIndex(1)
    def fail(_):
        raise OSError('disk unavailable')
    monkeypatch.setattr(editor.service, 'save_controller_preferences', fail)
    editor.apply()
    assert 'Could not save' in editor.status.text()
    assert editor.value()['snes9x']['mode'] == 'managed'
    assert not runtime.exists()


def test_keyboard_preview_does_not_require_sdl(widget):
    editor, runtime = widget
    def fail():
        raise ValueError('SDL unavailable')
    editor.inventory = SimpleNamespace(snapshot=fail)
    editor.editors['retroarch'].mode.setCurrentIndex(1)
    editor.preview()
    assert 'pass validation' in editor.status.text()
    assert not runtime.exists()


def test_refresh_preserves_mapping_edits(widget):
    editor, runtime = widget
    profile = editor.editors['retroarch']
    profile.mode.setCurrentIndex(1)
    profile.players[0].fields['a'].setText('c')
    editor.refresh()
    assert profile.players[0].fields['a'].text() == 'c'
    assert not runtime.exists()
