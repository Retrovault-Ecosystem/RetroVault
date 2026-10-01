"""Backend routing, native isolation, and real owned-process lifecycle contracts."""
import configparser
from dataclasses import replace
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from config import ConfigLoader, ConfigWriter
from config.validation import validate_config
from controllers.game_launch_controller import GameLaunchController
from services.emulators.models import SNES, StandaloneRequest, selected_backend
from services.emulators.session import EmulatorSession
from services.emulators.snes9x import Snes9xLauncher
from services.library.models import Game
from services.settings.service import SettingsService


@pytest.fixture
def native(tmp_path, monkeypatch):
    for key, name in [('XDG_CONFIG_HOME', 'config'), ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache')]:
        monkeypatch.setenv(key, str(tmp_path / name))
    program = tmp_path / 'fake-snes9x'
    program.write_text(f'#!{sys.executable}\nimport time\nprint("Using rewind buffer of 16 MiB", flush=True)\ntime.sleep(30)\n')
    program.chmod(0o755)
    rom = tmp_path / 'test ; $(touch forbidden).sfc'
    rom.write_bytes(b'ROM test fixture')
    request = StandaloneRequest('Test', str(rom), SNES, 'local-file:one', str(program))
    adapter = Snes9xLauncher(startup_timeout=0.5)
    yield adapter, request
    adapter.shutdown()


@pytest.mark.parametrize('platform,expected', [(SNES, 'snes9x'), ('platform.nintendo.nes', 'retroarch'),
                                              ('platform.sega.genesis', 'retroarch'), ('SNES', 'retroarch')])
def test_explicit_canonical_platform_route(platform, expected):
    assert selected_backend({'emulation': {'snes_backend': 'snes9x'}}, platform) == expected
    assert selected_backend({}, platform) == 'retroarch'


@pytest.mark.parametrize('section', [{'snes_backend': 'unknown'}, {'snes_backend': []},
                                    {'snes9x_executable': 123}, {'snes9x_executable': 'relative/tool'}])
def test_config_rejects_invalid_backend_settings(section):
    with pytest.raises(ValueError):
        validate_config({'emulation': section})


def test_native_arguments_profile_and_stop_preserve_saves(native, tmp_path):
    adapter, request = native
    result = adapter.launch(request)
    assert result['success']
    assert adapter.active_process.args == [request.executable, str(Path(request.rom).resolve())]
    assert adapter.process_running()
    config = configparser.ConfigParser(interpolation=None)
    config.read(result['config'])
    saves = Path(result['saves'])
    assert Path(config['Files']['SRAMDirectory']) == saves / 'sram'
    assert config['Joypad 0']['Start'] == 'Keyboard Return'
    save = saves / 'sram/test.srm'
    save.write_bytes(b'owned save')
    assert adapter.stop()
    assert not adapter.process_running()
    assert adapter.active_process is None
    assert save.read_bytes() == b'owned save'
    result2 = adapter.launch(request)
    assert result2['success'] and result2['saves'] == str(saves)
    assert not (tmp_path / 'forbidden').exists()


@pytest.mark.parametrize('change', [dict(platform_id='SNES'), dict(rom='/missing/file.sfc'),
                                    dict(rom='/missing/file.7z'), dict(executable='/missing/tool')])
def test_native_validation_fails_before_profile_writes(native, change, tmp_path):
    adapter, request = native
    with pytest.raises(ValueError):
        adapter.launch(replace(request, **change))
    assert not (tmp_path / 'config').exists()
    assert adapter.active_process is None


def test_rvdb_compatibility_is_required(native):
    adapter, request = native
    adapter.rvdb_service = SimpleNamespace(platform_view=lambda _: SimpleNamespace(emulators=[]))
    with pytest.raises(ValueError, match='RVDB'):
        adapter.launch(request)


def test_same_basename_different_identity_has_separate_saves_and_keeps_preferences(native):
    adapter, request = native
    _, log, profile, saves = adapter.prepare(request, Path(request.rom))
    cfg = configparser.ConfigParser(interpolation=None)
    cfg.optionxform = str
    cfg.read(profile)
    cfg['Joypad 0']['Start'] = 'Keyboard space'
    with profile.open('w') as handle:
        cfg.write(handle)
    _, _, same_profile, same_saves = adapter.prepare(request, Path(request.rom))
    assert (same_profile, same_saves) == (profile, saves)
    cfg.read(profile)
    assert cfg['Joypad 0']['Start'] == 'Keyboard space'
    _, _, other_profile, other_saves = adapter.prepare(replace(request, local_file_id='local-file:two'), Path(request.rom))
    assert other_saves != saves and other_profile != profile
    assert log.parent.parent.name == 'snes9x'


@pytest.mark.parametrize('body', ['import time; time.sleep(30)', 'raise SystemExit(7)'])
def test_empty_gui_or_early_exit_not_successful(native, body):
    adapter, request = native
    Path(request.executable).write_text(f'#!{sys.executable}\n{body}\n')
    result = adapter.launch(request)
    assert not result['success']
    assert 'confirm ROM loading' in result['error']
    assert not adapter.process_running()


def fake_adapter():
    adapter = Mock(command='retroarch')
    adapter.process_running.return_value = False
    adapter.launch.return_value = {'success': True}
    return adapter


def test_session_routes_exclusively_and_stops_actual_owner():
    ra, native = fake_adapter(), fake_adapter()
    session = EmulatorSession(ra, native)
    assert session.launch_standalone('native')['success']
    native.process_running.return_value = True
    assert session.active_process is native.active_process
    assert not session.launch('ra')['success']
    ra.launch.assert_not_called()
    session.stop()
    native.stop.assert_called_once()
    ra.stop.assert_not_called()
    native.process_running.return_value = False
    assert session.launch('ra')['success']
    assert session.active_process is ra.active_process
    session.shutdown()
    ra.shutdown.assert_called_once()
    native.shutdown.assert_called_once()


def test_session_retains_owner_after_launch_exception():
    ra, native = fake_adapter(), fake_adapter()
    session = EmulatorSession(ra, native)
    native.launch.side_effect = RuntimeError('cleanup incomplete')
    with pytest.raises(RuntimeError):
        session.launch_standalone('request')
    assert session.active_process is native.active_process
    session.stop()
    native.stop.assert_called_once()


def controller_setup(tmp_path, success=True):
    config = {'retroarch': {'executable': '/missing/retroarch'},
              'emulation': {'snes_backend': 'snes9x', 'snes9x_executable': '/native/snes9x-gtk'}}
    loader = SimpleNamespace(load=lambda: config)
    session = fake_adapter()
    session.launch_standalone.return_value = {'success': success, 'error': 'failed to load ROM'}
    controller = GameLaunchController(launcher=session, config_loader=loader)
    controller.core_resolver = Mock()
    controller.archive_runtime = Mock()
    controller.cheat_service = Mock()
    game = Game('Family', 'SNES', 0, '', 'missing_core', rom='/library/preferred.sfc',
                local_file_id='local-file:preferred', rvdb_platform_id=SNES)
    calls = dict(choose_edition=lambda: {'name': 'Edition', 'rom': '/library/edition.sfc',
                                         'local_file_id': 'local-file:edition'},
                 choose_archive=Mock(), choose_cheats=Mock(), status=Mock(), warning=Mock(),
                 played=Mock(), presentation_provider=Mock())
    return controller, session, game, calls


@pytest.mark.parametrize('success', [True, False])
def test_controller_branches_before_retroarch_work_and_records_selected_identity(tmp_path, success):
    controller, session, game, calls = controller_setup(tmp_path, success)
    assert controller.launch(game, **calls) == success
    request = session.launch_standalone.call_args.args[0]
    assert request.rom == '/library/edition.sfc'
    assert request.local_file_id == 'local-file:edition'
    controller.core_resolver.resolve.assert_not_called()
    controller.archive_runtime.resolve.assert_not_called()
    controller.cheat_service.runtime_file.assert_not_called()
    session.launch.assert_not_called()
    for name in ('choose_archive', 'choose_cheats', 'presentation_provider'):
        calls[name].assert_not_called()
    if success:
        assert calls['played'].call_args.args[0].local_file_id == 'local-file:edition'
    else:
        calls['played'].assert_not_called()
    assert game.local_file_id == 'local-file:preferred'


def test_native_failure_does_not_fallback_or_write_history(tmp_path):
    controller, session, game, calls = controller_setup(tmp_path)
    session.launch_standalone.side_effect = ValueError('executable unavailable')
    assert not controller.launch(game, **calls)
    calls['played'].assert_not_called()
    session.launch.assert_not_called()


def test_backend_can_change_for_next_launch(tmp_path):
    controller, session, game, calls = controller_setup(tmp_path)
    controller.config['emulation']['snes_backend'] = 'retroarch'
    controller.core_resolver.resolve.return_value = SimpleNamespace(path='', message='No RA core')
    calls['choose_cheats'].return_value = []
    assert not controller.launch(game, **calls)
    session.launch_standalone.assert_not_called()
    controller.core_resolver.resolve.assert_called_once()


def test_standalone_settings_save_without_retroarch_installation(native, tmp_path):
    _, request = native
    runtime = tmp_path / 'runtime.json'
    loader = ConfigLoader(runtime_file=runtime)
    writer = ConfigWriter(runtime_file=runtime)
    writer.write({'retroarch': {'executable': '/missing/retroarch'}, 'other_setting': 'preserved'})
    service = SettingsService(loader, writer)
    config = service.save_standalone('snes9x', request.executable)
    assert config['emulation']['snes_backend'] == 'snes9x'
    assert json.loads(runtime.read_text())['other_setting'] == 'preserved'
    assert service.save_standalone('retroarch', '/now-missing/snes9x')['emulation']['snes_backend'] == 'retroarch'
    before = runtime.read_bytes()
    with pytest.raises(ValueError):
        service.save_standalone('snes9x', '/missing/snes9x')
    assert runtime.read_bytes() == before


def test_startup_reports_selected_missing_native_backend_without_writes(tmp_path, monkeypatch):
    from services.startup import check_startup
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / 'config'))
    monkeypatch.setenv('XDG_CACHE_HOME', str(tmp_path / 'cache'))
    runtime = tmp_path / 'runtime.json'
    runtime.write_text(json.dumps({'emulation': {'snes_backend': 'snes9x', 'snes9x_executable': '/missing/snes9x'}}))
    before = set(tmp_path.rglob('*'))
    report = check_startup(ConfigLoader(runtime_file=runtime))
    assert any('Selected SNES standalone backend unavailable' in message for message in report.warnings)
    assert set(tmp_path.rglob('*')) == before


def test_standalone_presentation_retains_preferences_without_resolving_assets(native):
    from services.library.presentation_studio import LibraryPresentationStudioService
    from services.presentation.models import PresentationProfile
    ConfigWriter().write({'emulation': {'snes_backend': 'snes9x'}})
    saved = PresentationProfile(shader='saved-shader', overlay='saved-overlay')
    store = Mock(load=Mock(return_value={'default': saved, 'systems': {}, 'games': {}}))
    provider = Mock(side_effect=AssertionError('Native UI must not resolve RetroArch production assets'))
    service = LibraryPresentationStudioService(store, provider)
    game = SimpleNamespace(platform='SNES', rvdb_platform_id=SNES, local_file_id='local-file:one')
    state = service.state_for(game)
    assert state.backend == 'snes9x'
    assert state.default_profile == saved
    assert state.shader == state.overlay == ''
    assert state.source_label == 'Snes9x standalone'
    provider.assert_not_called()


_QT_APP = None


def qt_app():
    global _QT_APP
    from PyQt6.QtWidgets import QApplication
    _QT_APP = QApplication.instance() or QApplication([])
    return _QT_APP


def test_settings_ui_persists_native_choice_for_next_launch(native):
    from ui.pages.settings_page import SettingsPage
    qt_app()
    _, request = native
    page = SettingsPage()
    page.snes_backend.setCurrentIndex(page.snes_backend.findData('snes9x'))
    page.snes9x_executable.setText(request.executable)
    page.save_standalone_settings()
    assert ConfigLoader().load()['emulation']['snes_backend'] == 'snes9x'
    assert 'next launch' in page.standalone_status.text()
    second = SettingsPage()
    assert second.snes_backend.currentData() == 'snes9x'
    assert second.snes9x_executable.text() == request.executable
    page.close()
    second.close()


def test_standalone_presentation_widget_reports_capabilities_and_disables_ra_controls(native):
    from ui.library.widgets.presentation_studio import PresentationStudio
    qt_app()
    ConfigWriter().write({'emulation': {'snes_backend': 'snes9x'}})
    studio = PresentationStudio()
    game = SimpleNamespace(name='SNES game', platform='SNES', rvdb_platform_id=SNES,
                           local_file_id='local-file:one')
    studio.set_game(game)
    assert studio.source_value.text() == 'Snes9x standalone'
    assert 'not applied' in studio.status.text()
    assert studio.tuning_panel.isHidden()
    assert not studio.use_overlay_button.isEnabled()
    assert not studio.use_shader_button.isEnabled()
    assert not studio.clear_overlay_button.isEnabled()
    assert not studio.clear_shader_button.isEnabled()
    studio.close()


def test_shared_session_mainwindow_wiring_and_shutdown(native, monkeypatch):
    from ui.main_window import MainWindow
    qt_app()
    window = MainWindow()
    session = window.emulator_session
    assert window.game_launch_controller.launcher is session
    assert window.process_lifecycle._session is session
    assert session.retroarch is window.retroarch_launcher
    native_shutdown = Mock()
    monkeypatch.setattr(session.snes9x, 'shutdown', native_shutdown)
    assert window.shutdown_runtime()
    native_shutdown.assert_called_once()
    window.close()


def test_missing_rvdb_bundle_is_actionable_native_failure(native, monkeypatch):
    from services.rvdb import RVDBError
    adapter, request = native
    monkeypatch.setattr('services.emulators.snes9x.RVDBService.from_bundle',
                        Mock(side_effect=RVDBError('missing bundle')))
    with pytest.raises(ValueError, match='RVDB compatibility is unavailable'):
        adapter.launch(request)
    assert adapter.active_process is None


def test_corrupt_native_profile_fails_without_overwriting_preferences(native):
    adapter, request = native
    _, _, profile, _ = adapter.prepare(request, Path(request.rom))
    original = b'not an ini configuration\n'
    profile.write_bytes(original)
    with pytest.raises(ValueError, match='Invalid native Snes9x configuration'):
        adapter.launch(request)
    assert profile.read_bytes() == original
    assert adapter.active_process is None


def test_controller_can_stop_without_optional_hardware_lifecycle(tmp_path):
    controller, session, _, _ = controller_setup(tmp_path)
    controller.stop()
    session.stop.assert_called_once()
