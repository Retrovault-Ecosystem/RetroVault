"""Failure-path qualification for owned RetroArch sessions (no emulator needed)."""
import os
import subprocess
import sys
from unittest.mock import Mock

import pytest

from services.retroarch.launcher import RetroArchLauncher
from services.retroarch.process_group import terminate_group
from services.retroarch.content_display_aspect_probe import ContentLoadedDisplayAspectProbe
from services.retroarch.session_config import RetroArchSessionConfig


def test_exited_wrapper_retains_descendants_and_resources(monkeypatch):
    launcher = RetroArchLauncher()
    process = Mock(pid=54321)
    process.poll.return_value = 0
    launcher._active_process = process
    launcher._active_group = 54321
    monkeypatch.setattr(launcher, '_process_group_exists', lambda group: True)
    cleanup = Mock()
    monkeypatch.setattr(launcher, '_cleanup_active_transients', cleanup)
    assert launcher.process_running()
    assert launcher.clear_exited_process() is None
    cleanup.assert_not_called()
    drain = Mock(side_effect=RuntimeError('still alive'))
    monkeypatch.setattr('services.retroarch.launcher.terminate_group', drain)
    with pytest.raises(RuntimeError, match='still alive'):
        launcher.stop()
    assert launcher.active_process is process
    assert launcher._active_group == 54321
    cleanup.assert_not_called()
    drain.side_effect = None
    assert launcher.stop()
    assert launcher.active_process is None
    assert drain.call_args.args[1] == 54321
    cleanup.assert_called_once()


def test_cleanup_attempts_all_owners_and_can_retry():
    launcher = RetroArchLauncher()
    launcher.primary_config_runtime = Mock()
    launcher.primary_config_runtime.cleanup.side_effect = OSError('permission')
    owners = []
    for name in ('core_options_runtime', 'session_config', 'overlay_runtime',
                 'adaptive_bezel_runtime', 'contain_runtime', 'shader_runtime',
                 'cheat_runtime', 'content_display_aspect_probe'):
        owner = Mock()
        owner.process_running.return_value = False
        setattr(launcher, name, owner)
        owners.append(owner)
    launcher._cleanup_active_transients()
    assert 'permission' in launcher.cleanup_errors[0]
    for owner in owners:
        owner.cleanup.assert_called_once()
    launcher.primary_config_runtime.cleanup.side_effect = None
    assert launcher.shutdown()
    assert not launcher.cleanup_errors


def test_partial_session_write_remains_owned_for_cleanup(tmp_path, monkeypatch):
    runtime = RetroArchSessionConfig(directory=tmp_path)
    monkeypatch.setattr(os, 'fsync', Mock(side_effect=OSError('disk failure')))
    with pytest.raises(OSError, match='disk failure'):
        runtime.create()
    assert runtime._created
    assert any(tmp_path.iterdir())
    runtime.cleanup()
    assert not list(tmp_path.iterdir())


def test_failed_probe_drain_retains_ownership_and_blocks_reentry(tmp_path, monkeypatch):
    probe = ContentLoadedDisplayAspectProbe(directory=tmp_path)
    process = Mock(pid=54321)
    process.poll.return_value = None
    probe._active_process = process
    probe._session_directory = tmp_path / 'probe'
    probe._session_directory.mkdir()
    monkeypatch.setattr(probe, '_terminate_and_reap', Mock(side_effect=OSError('drain failed')))
    with pytest.raises(OSError, match='drain failed'):
        probe.stop()
    assert probe._active_process is process
    assert probe._session_directory.exists()
    with pytest.raises(OSError, match='still owns'):
        probe.acquire()


def test_real_owned_process_group_is_drained():
    process = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)
    try:
        terminate_group(process, process.pid, RetroArchLauncher._wait_for_process_group_exit)
        assert process.poll() is not None
        assert not RetroArchLauncher._process_group_exists(process.pid)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()


def test_termination_refuses_current_application_group():
    with pytest.raises(RuntimeError, match='unowned'):
        terminate_group(Mock(), os.getpgrp(), Mock())


def test_close_and_quit_keep_window_open_when_drain_fails():
    from PyQt6.QtCore import QEvent
    from PyQt6.QtGui import QCloseEvent
    from PyQt6.QtWidgets import QApplication, QMainWindow
    from ui.main_window import MainWindow
    app = QApplication.instance() or QApplication([])
    window = MainWindow.__new__(MainWindow)
    QMainWindow.__init__(window)
    window.retroarch_launcher = Mock()
    window.retroarch_launcher.shutdown.side_effect = RuntimeError('drain failed')
    window.process_lifecycle_timer = Mock()
    event = QCloseEvent()
    window.closeEvent(event)
    assert not event.isAccepted()
    assert window.eventFilter(app, QEvent(QEvent.Type.Quit))
    window.process_lifecycle_timer.stop.assert_not_called()
    window.retroarch_launcher.shutdown.side_effect = None
    window.closeEvent(event)
    assert event.isAccepted()
    assert not window.eventFilter(app, QEvent(QEvent.Type.Quit))
    window.deleteLater()


def test_qualification_isolates_persistence_and_rejects_includes(tmp_path):
    from scripts.qualify_retroarch_runtime import isolated_config
    text = isolated_config('savefile_directory = "/user/saves"\nconfig_save_on_exit = "true"\n', tmp_path)
    assert '/user/saves' not in text
    assert 'config_save_on_exit = "false"' in text
    assert str(tmp_path / 'saves') in text
    assert 'savestate_auto_load = "false"' in text
    with pytest.raises(ValueError, match='include'):
        isolated_config('#include "/user/config.cfg"', tmp_path)


def test_synchronous_stop_advances_lifecycle_to_exited(monkeypatch):
    from services.presentation.hardware_runtime import HardwareRuntimeOrchestrator
    from services.presentation.hardware_state import NESHardwareIndicatorPolicy, HardwareRuntimeState
    from services.presentation.process_lifecycle import ProcessLifecycleAdapter
    launcher = RetroArchLauncher()
    process = Mock(pid=54321)
    process.poll.return_value = None
    launcher._active_process = process
    launcher._active_group = 54321
    monkeypatch.setattr('services.retroarch.launcher.terminate_group', Mock())
    monkeypatch.setattr(launcher, '_cleanup_active_transients', Mock())
    adapter = ProcessLifecycleAdapter(HardwareRuntimeOrchestrator(NESHardwareIndicatorPolicy()), launcher)
    adapter.launch_requested('platform.nintendo.nes')
    adapter.launch_result({'success': True})
    adapter.stop_requested()
    assert launcher.active_process is None
    adapter.poll()
    assert adapter.state is HardwareRuntimeState.EXITED


def test_qualification_retains_final_overlay_not_superseded_primary(tmp_path):
    from scripts.qualify_retroarch_runtime import capture_presentation, digest
    primary = tmp_path / 'primary.cfg'
    primary.write_text('input_overlay = "/obsolete/overlay.cfg"\ninput_overlay_enable = "true"\n')
    baseline = tmp_path / 'session.cfg'
    baseline.write_text('input_overlay = ""\ninput_overlay_enable = "false"\n')
    overlay = tmp_path / 'overlay.cfg'
    overlay.write_text('overlay0_overlay = "approved.png"\n')
    artwork = tmp_path / 'approved.png'
    artwork.write_bytes(b'approved asset bytes')
    final = tmp_path / 'final.cfg'
    final.write_text(f'input_overlay = "{overlay}"\ninput_overlay_enable = "true"\ncustom_viewport_x = "373"\n')
    record = capture_presentation(['retroarch', '--config', str(primary), '--appendconfig',
                                   f'{baseline}|{final}'], tmp_path)
    assert record['overlay'] == str(overlay)
    assert record['artwork_sha256'] == digest(artwork)
    assert record['effective_settings']['custom_viewport_x'] == '373'
    assert (tmp_path / 'selected-overlay.png').read_bytes() == artwork.read_bytes()
    artwork.unlink()
    assert (tmp_path / 'selected-overlay.png').is_file()


def test_qualification_records_disabled_overlay_without_loading_stale_path(tmp_path):
    from scripts.qualify_retroarch_runtime import capture_presentation
    config = tmp_path / 'session.cfg'
    config.write_text('input_overlay = "/obsolete/overlay.cfg"\ninput_overlay_enable = "false"\n')
    record = capture_presentation(['retroarch', '--appendconfig', str(config)], tmp_path)
    assert 'artwork' not in record
    assert not (tmp_path / 'selected-overlay.png').exists()


def test_qualification_requires_library_platform_identification():
    from scripts.qualify_retroarch_runtime import content_platform
    assert content_platform('Sonic.md', 'platform.sega.genesis') == 'platform.sega.genesis'
    with pytest.raises(ValueError, match='Library metadata'):
        content_platform('Unknown.bin', 'platform.sega.genesis')
    with pytest.raises(ValueError, match='Library metadata'):
        content_platform('Mario.nes', 'platform.sega.genesis')


def test_pipeline_environment_restores_values_after_failure(tmp_path, monkeypatch):
    from scripts.qualify_retroarch_runtime import pipeline_environment
    monkeypatch.setenv('XDG_CONFIG_HOME', '/original/config')
    monkeypatch.delenv('XDG_DATA_HOME', raising=False)
    with pytest.raises(RuntimeError):
        with pipeline_environment(tmp_path):
            assert os.environ['XDG_CONFIG_HOME'] == str(tmp_path / 'profile')
            raise RuntimeError('setup failed')
    assert os.environ['XDG_CONFIG_HOME'] == '/original/config'
    assert 'XDG_DATA_HOME' not in os.environ


def test_complete_pipeline_rejects_unqualified_platform_without_writes(tmp_path):
    from scripts.qualify_retroarch_runtime import qualify
    output = tmp_path / 'report'
    with pytest.raises(ValueError, match='No complete-pipeline'):
        qualify('n64', '/roms/game.z64', output, 1, pipeline=True)
    assert not output.exists()


def test_pipeline_refuses_existing_output_directory(tmp_path):
    from scripts.qualify_retroarch_runtime import _qualify_pipeline
    sentinel = tmp_path / 'keep'
    sentinel.write_text('preserve')
    with pytest.raises(FileExistsError):
        _qualify_pipeline('/roms/game.nes', tmp_path, 1)
    assert sentinel.read_text() == 'preserve'


def test_pipeline_cli_returns_failure_even_if_emulator_ran(monkeypatch, capsys):
    from scripts import qualify_retroarch_runtime as runner
    monkeypatch.setattr(sys, 'argv', ['qualify', '--platform', 'nes', '--rom', '/game.nes',
                                     '--output', '/unused', '--pipeline'])
    monkeypatch.setattr(runner, 'qualify', lambda *args, **kwargs: {
        'pipeline_passed': False, 'alive_at_deadline': True, 'error': 'Restart failed'})
    assert runner.main() == 1
    assert 'Restart failed' in capsys.readouterr().out
