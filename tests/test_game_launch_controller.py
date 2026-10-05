"""Application workflow ownership without Qt or emulator processes."""
from types import SimpleNamespace
from unittest.mock import Mock
import pytest

from controllers.game_launch_controller import GameLaunchController
from services.library.models import Game


def setup_controller(tmp_path):
    launcher = Mock(command='retroarch')
    launcher.process_running.return_value = False
    launcher.launch.return_value = {'success': True}
    loader = Mock()
    loader.load.return_value = {'retroarch': {'executable': 'retroarch', 'cores': {'directory': ''}}}
    controller = GameLaunchController(launcher=launcher, config_loader=loader)
    controller.core_resolver.resolve = Mock(return_value=SimpleNamespace(path='/cores/test.so'))
    controller.validator_factory = Mock(return_value=Mock(validate=Mock(return_value={'ready': True})))
    controller.diagnostics.explain = Mock(return_value=[])
    game = Game('Family', 'NES', 0, '', 'test', rom='/roms/preferred.nes', local_file_id='local-file:preferred')
    selected = {'name': 'Edition', 'rom': '/roms/edition.nes', 'local_file_id': 'local-file:edition'}
    calls = dict(choose_edition=lambda: selected, choose_archive=lambda rom: '',
                 choose_cheats=lambda game, member: [object()], status=Mock(), warning=Mock(), played=Mock())
    generated = tmp_path / 'generated.cht'
    def create(cheats):
        generated.write_text('cheats = 1')
        return str(generated)
    controller.cheat_service = Mock(runtime_file=Mock(side_effect=create))
    return controller, game, calls, generated


@pytest.mark.parametrize('failure', ['none', 'core', 'validation', 'launch', 'exception', 'presentation'])
def test_generated_cheat_input_owned_across_outcomes(tmp_path, failure):
    c, game, calls, generated = setup_controller(tmp_path)
    if failure == 'core':
        c.core_resolver.resolve.return_value = SimpleNamespace(path='', message='Missing core')
    elif failure == 'validation':
        c.validator_factory.return_value.validate.return_value = {'ready': False}
    elif failure == 'launch':
        c.launcher.launch.return_value = {'success': False, 'error': 'Cannot start'}
    elif failure == 'exception':
        c.launcher.launch.side_effect = OSError('Cannot spawn')
    elif failure == 'presentation':
        from services.presentation.launch_resolver import LaunchPresentationResolver
        resolver = Mock(spec=LaunchPresentationResolver)
        resolver.resolve.side_effect = ValueError('Package missing')
        calls['presentation_provider'] = lambda: resolver
    success = c.launch(game, **calls)
    assert success == (failure == 'none')
    assert not generated.exists()
    if success:
        played = calls['played'].call_args.args[0]
        assert played.local_file_id == 'local-file:edition'
        assert played.rom == '/roms/edition.nes'
    else:
        calls['played'].assert_not_called()
    assert game.local_file_id == 'local-file:preferred'
    assert game.rom == '/roms/preferred.nes'
    assert c.current_game is None
    assert c._select_cheats is None


def test_cheat_input_exists_until_launcher_copies_it(tmp_path):
    c, game, calls, generated = setup_controller(tmp_path)
    def launch(profile):
        assert generated.exists()
        assert profile.cheat_file == str(generated)
        return {'success': True}
    c.launcher.launch.side_effect = launch
    assert c.launch(game, **calls)
    assert not generated.exists()


@pytest.mark.parametrize('step', ['edition', 'archive', 'cheats'])
def test_cancel_does_not_write_history_or_prepare_cheats(tmp_path, step):
    c, game, calls, generated = setup_controller(tmp_path)
    if step == 'edition':
        calls['choose_edition'] = lambda: None
    elif step == 'archive':
        calls['choose_edition'] = lambda: {'rom': '/roms/game.7z'}
        calls['choose_archive'] = lambda rom: None
    else:
        calls['choose_cheats'] = lambda *args: None
    assert not c.launch(game, **calls)
    assert not generated.exists()
    c.launcher.launch.assert_not_called()
    calls['played'].assert_not_called()


def test_recent_write_failure_does_not_turn_success_into_failure(tmp_path):
    c, game, calls, generated = setup_controller(tmp_path)
    calls['played'].side_effect = OSError('Read-only history')
    assert c.launch(game, **calls)
    assert calls['warning'].call_args.args[0] == 'Recently Played Update Failed'
    assert not generated.exists()


def test_immediate_exit_does_not_record_played(tmp_path):
    c, game, calls, generated = setup_controller(tmp_path)
    c.process_lifecycle = Mock(state=SimpleNamespace(name='EXITED'))
    assert not c.launch(game, **calls)
    assert 'exited during startup' in c.last_result['error']
    calls['played'].assert_not_called()
    assert not generated.exists()


def test_reentrant_launch_cannot_replace_outer_selection(tmp_path):
    c, game, calls, generated = setup_controller(tmp_path)
    choose = calls['choose_edition']
    def nested():
        assert not c.launch(game, **calls)
        return choose()
    calls['choose_edition'] = nested
    assert c.launch(game, **calls)
    c.launcher.launch.assert_called_once()
    assert not generated.exists()


def test_failed_input_cleanup_retains_owner_for_retry(tmp_path, monkeypatch):
    from pathlib import Path
    c, game, calls, generated = setup_controller(tmp_path)
    unlink = Path.unlink
    def deny(path, *args, **kwargs):
        if path == generated:
            raise PermissionError('Busy')
        return unlink(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'unlink', deny)
    assert c.launch(game, **calls)
    assert str(generated) in c._pending_cheat_inputs
    assert calls['warning'].call_args.args[0] == 'Cheat Input Cleanup Failed'
    monkeypatch.setattr(Path, 'unlink', unlink)
    c.cleanup_inputs()
    assert not generated.exists()
    assert not c._pending_cheat_inputs

@pytest.mark.parametrize('initial', ['IDLE', 'EXITED'])
@pytest.mark.parametrize('step', ['edition', 'config', 'pending'])
def test_real_lifecycle_contains_preparation_error(tmp_path, initial, step):
    from services.presentation.hardware_runtime import HardwareRuntimeOrchestrator
    from services.presentation.hardware_state import HardwareIndicatorPolicy, HardwareRuntimeState
    from services.presentation.process_lifecycle import ProcessLifecycleAdapter
    c, game, calls, generated = setup_controller(tmp_path)
    c.launcher.active_process = None
    runtime = HardwareRuntimeOrchestrator(HardwareIndicatorPolicy())
    if initial == 'EXITED':
        runtime.launch_requested(); runtime.process_exited()
    c.process_lifecycle = ProcessLifecycleAdapter(runtime, c.launcher)
    if step == 'edition':
        calls['choose_edition'] = Mock(side_effect=ValueError('original preparation error'))
    elif step == 'config':
        game.rvdb_platform_id = 'platform.nintendo.snes'
        c.config_loader.load.side_effect = OSError('original preparation error')
    else:
        c.core_resolver.resolve.side_effect = RuntimeError('original preparation error')
    assert c.launch(game, **calls) is False
    assert c.last_result['error'] == 'original preparation error'
    assert runtime.state is (HardwareRuntimeState.IDLE if step == 'pending' else HardwareRuntimeState[initial])
    c.launcher.launch.assert_not_called()
    calls['played'].assert_not_called()
    assert not generated.exists()
    assert not c._launch_in_progress


@pytest.mark.parametrize('initial', ['IDLE', 'EXITED'])
def test_real_lifecycle_cancellation_and_retry(tmp_path, initial):
    from services.presentation.hardware_runtime import HardwareRuntimeOrchestrator
    from services.presentation.hardware_state import HardwareIndicatorPolicy, HardwareRuntimeState
    from services.presentation.process_lifecycle import ProcessLifecycleAdapter
    c, game, calls, generated = setup_controller(tmp_path)
    c.launcher.active_process = None
    runtime = HardwareRuntimeOrchestrator(HardwareIndicatorPolicy())
    if initial == 'EXITED':
        runtime.launch_requested(); runtime.process_exited()
    c.process_lifecycle = ProcessLifecycleAdapter(runtime, c.launcher)
    choose = calls['choose_edition']
    calls['choose_edition'] = lambda: None
    assert not c.launch(game, **calls)
    assert runtime.state is HardwareRuntimeState[initial]
    assert not generated.exists()
    calls['played'].assert_not_called()
    calls['choose_edition'] = choose
    def launch(profile):
        c.launcher.active_process = object()
        c.launcher.process_running.return_value = True
        return {'success': True}
    c.launcher.launch.side_effect = launch
    assert c.launch(game, **calls)
    assert runtime.state is HardwareRuntimeState.RUNNING
    calls['played'].assert_called_once()
    assert not generated.exists()
