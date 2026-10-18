from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
import pytest
from PyQt6.QtWidgets import QApplication, QMessageBox
from services.emulators.session import EmulatorSession
from services.saves.context import save_context
from services.saves.policy import SavePolicy
from ui.library.widgets.save_manager import SaveManager


@pytest.fixture
def setup(tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'data'))
    rom = tmp_path / 'Game.sfc'
    rom.write_bytes(b'content')
    core = tmp_path / 'snes9x_libretro.so'
    core.write_bytes(b'core')
    config = {'retroarch': {'cores': {'directory': str(tmp_path)}}}
    game = SimpleNamespace(local_file_id='edition', rom=str(rom), core=str(core),
                           rvdb_platform_id='platform.nintendo.snes')
    resolver = Mock()
    resolver.resolve.return_value = SimpleNamespace(path=str(core))
    monkeypatch.setattr('services.saves.context.CoreResolver', lambda config: resolver)
    adapters = [Mock(), Mock()]
    for adapter in adapters:
        adapter.process_running.return_value = False
    return game, Mock(load=Mock(return_value=config)), EmulatorSession(*adapters)


def test_context_is_read_only_and_legacy_paths_not_guessed(setup):
    game, config, _ = setup
    context = save_context(game, config.load())
    assert context.sram is None and context.states is None
    with pytest.raises(ValueError, match='displayed destination'):
        context.target(Path(game.rom).with_suffix('.srm'), 'sram')


def test_ui_cancel_does_not_enable_storage_then_explicit_choice_does(setup, monkeypatch):
    app = QApplication.instance() or QApplication([])
    game, config, session = setup
    dialog = SaveManager(game, config, session)
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.StandardButton.No)
    dialog.enable_isolation()
    assert save_context(game, config.load()).sram is None
    monkeypatch.setattr(QMessageBox, 'question', lambda *args: QMessageBox.StandardButton.Yes)
    dialog.enable_isolation()
    assert save_context(game, config.load()).sram.is_dir()
    dialog.disable_isolation()
    assert save_context(game, config.load()).sram is None
    dialog.close()


def test_ui_lists_save_kinds_separately_and_excludes_configs(setup):
    app = QApplication.instance() or QApplication([])
    game, config, session = setup
    SavePolicy().enable(session, game.local_file_id, game.core, game.rom)
    context = save_context(game, config.load())
    (context.sram / 'Game.srm').write_bytes(b'sram')
    (context.states / 'Game.state').write_bytes(b'state')
    (context.states / 'config.ini').write_text('not a save')
    (context.states / 'Game.state.png').write_bytes(b'not a save')
    dialog = SaveManager(game, config, session)
    assert dialog.files.count() == 2
    assert [kind for _, kind in dialog.targets] == ['sram', 'state']
    dialog.files.setCurrentRow(0)
    assert dialog.selected_target().local_file_id == 'edition'
    dialog.close()
