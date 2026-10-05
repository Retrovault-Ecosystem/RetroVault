from unittest.mock import Mock

import pytest

from PyQt6.QtWidgets import QApplication

from services.library.models import Game
from ui.library.details.game_details import GameDetails


@pytest.fixture(autouse=True)
def _continue_without_cheats(
    monkeypatch,
):
    """
    Legacy launch tests validate their original launch boundary,
    not interactive Cheat Studio UX.

    The production launch path retains CheatStudio.choose().
    Headless tests deterministically select the supported
    Continue Without Cheats path.
    """

    monkeypatch.setattr(
        GameDetails,
        "_select_cheats",
        lambda self, launch_game, archive_member="": [],
    )


# RETROVAULT_LIFECYCLE_MODAL_TEST_GUARD
# Production launch warnings remain modal. Automated tests intercept
# QMessageBox.warning so headless development regression cannot block.
@pytest.fixture(autouse=True)
def _suppress_lifecycle_warning_popups(monkeypatch):
    from PyQt6.QtWidgets import QMessageBox

    monkeypatch.setattr(
        QMessageBox,
        "warning",
        lambda *args, **kwargs: QMessageBox.StandardButton.Ok,
    )


@pytest.fixture(scope="module")
def app():
    instance = QApplication.instance()

    if instance is None:
        instance = QApplication([])

    return instance


def make_game():
    return Game(
        name="Duck Tales 2",
        platform="NES",
        year=1993,
        genre="Platformer",
        core="fceumm",
        rom="/roms/Duck Tales 2 (U).nes",
        rvdb_platform_id="platform.nintendo.nes",
    )


class ReadyValidator:
    def __init__(self, *_args, **_kwargs):
        pass

    def validate(self, _rom):
        return {
            "ready": True,
            "issues": [],
        }


class NotReadyValidator:
    def __init__(self, *_args, **_kwargs):
        pass

    def validate(self, _rom):
        return {
            "ready": False,
            "issues": ["not ready"],
        }


def make_details(app):
    lifecycle = Mock()

    details = GameDetails(
        process_lifecycle=lifecycle,
    )

    details.show_game(
        make_game()
    )

    details.diagnostics.explain = (
        lambda _report: "diagnostic"
    )

    return details, lifecycle


def test_launch_request_precedes_core_resolution(
    app,
):
    details, lifecycle = make_details(app)

    order = []

    lifecycle.launch_requested.side_effect = (
        lambda *_args: order.append("launch_requested")
    )

    details.core_resolver.resolve = (
        _core_resolution_mock(lambda _core: (
            order.append("core_resolution")
            or None
        ))
    )

    details.launch_game()

    assert order == [
        "launch_requested",
        "core_resolution",
    ]

    lifecycle.launch_failed.assert_called_once_with()


def test_missing_core_normalizes_pending_launch(
    app,
):
    details, lifecycle = make_details(app)

    details.core_resolver.resolve = (
        _core_resolution_mock(lambda _core: None)
    )

    details.launch_game()

    lifecycle.launch_requested.assert_called_once_with(
        "platform.nintendo.nes"
    )
    lifecycle.launch_failed.assert_called_once_with()
    lifecycle.launch_result.assert_not_called()


def test_validation_failure_normalizes_pending_launch(
    app,
    monkeypatch,
):
    details, lifecycle = make_details(app)

    details.core_resolver.resolve = (
        _core_resolution_mock(lambda _core: "/cores/fceumm_libretro.so")
    )

    monkeypatch.setattr(
        "controllers.game_launch_controller.LaunchValidator",
        NotReadyValidator,
    )

    details.launcher.launch = Mock()

    details.launch_game()

    lifecycle.launch_requested.assert_called_once_with(
        "platform.nintendo.nes"
    )
    lifecycle.launch_failed.assert_called_once_with()
    lifecycle.launch_result.assert_not_called()

    details.launcher.launch.assert_not_called()


def test_failed_launcher_result_reaches_lifecycle(
    app,
    monkeypatch,
):
    details, lifecycle = make_details(app)

    details.core_resolver.resolve = (
        _core_resolution_mock(lambda _core: "/cores/fceumm_libretro.so")
    )

    monkeypatch.setattr(
        "controllers.game_launch_controller.LaunchValidator",
        ReadyValidator,
    )

    launch_result = {
        "success": False,
        "error": "spawn failed",
    }

    details.launcher.launch = Mock(
        return_value=launch_result
    )

    details.launch_game()

    lifecycle.launch_requested.assert_called_once_with(
        "platform.nintendo.nes"
    )
    lifecycle.launch_failed.assert_not_called()

    lifecycle.launch_result.assert_called_once_with(
        launch_result
    )


def test_successful_launcher_result_reaches_lifecycle(
    app,
    monkeypatch,
):
    details, lifecycle = make_details(app)

    details.core_resolver.resolve = (
        _core_resolution_mock(lambda _core: "/cores/fceumm_libretro.so")
    )

    monkeypatch.setattr(
        "controllers.game_launch_controller.LaunchValidator",
        ReadyValidator,
    )

    launch_result = {
        "success": True,
        "command": ["retroarch"],
    }

    details.launcher.launch = Mock(
        return_value=launch_result
    )

    details.launch_game()

    lifecycle.launch_requested.assert_called_once_with(
        "platform.nintendo.nes"
    )
    lifecycle.launch_failed.assert_not_called()

    lifecycle.launch_result.assert_called_once_with(
        launch_result
    )


def test_no_selected_game_does_not_enter_lifecycle(
    app,
):
    lifecycle = Mock()

    details = GameDetails(
        process_lifecycle=lifecycle,
    )

    details.launch_game()

    lifecycle.launch_requested.assert_not_called()
    lifecycle.launch_failed.assert_not_called()
    lifecycle.launch_result.assert_not_called()


def test_standalone_game_details_remains_safe(
    app,
    monkeypatch,
):
    details = GameDetails()

    details.show_game(
        make_game()
    )

    details.core_resolver.resolve = (
        _core_resolution_mock(lambda _core: "/cores/fceumm_libretro.so")
    )

    details.diagnostics.explain = (
        lambda _report: "diagnostic"
    )

    monkeypatch.setattr(
        "controllers.game_launch_controller.LaunchValidator",
        ReadyValidator,
    )

    details.launcher.launch = Mock(
        return_value={
            "success": True,
            "command": ["retroarch"],
        }
    )

    details.launch_game()

    details.launcher.launch.assert_called_once()


def test_launch_hands_canonical_platform_to_lifecycle(
    app,
):
    details, lifecycle = make_details(app)

    details.core_resolver.resolve = (
        _core_resolution_mock(lambda _core: None)
    )

    details.launch_game()

    lifecycle.launch_requested.assert_called_once_with(
        "platform.nintendo.nes"
    )


def _core_resolution_mock(callback):
    """Keep UI sequencing tests independent of installed host binaries."""
    from unittest.mock import Mock
    from services.retroarch.core_resolver import CoreResolution
    def resolve(name, **kwargs):
        path = callback(name)
        return CoreResolution("resolved" if path else "missing", path=path,
                              message="Required core is missing: " + str(name))
    return Mock(side_effect=resolve)


@pytest.mark.parametrize('backend', ['retroarch', 'snes9x'])
def test_failed_startup_stop_recovers_real_owned_child(app, tmp_path, monkeypatch, backend):
    import subprocess
    import sys
    from types import SimpleNamespace
    from services.emulators.session import EmulatorSession
    from services.emulators.snes9x import Snes9xLauncher
    from services.retroarch.launcher import RetroArchLauncher
    from services.presentation.hardware_runtime import HardwareRuntimeOrchestrator
    from services.presentation.hardware_state import HardwareIndicatorPolicy, HardwareRuntimeState
    from services.presentation.process_lifecycle import ProcessLifecycleAdapter
    from controllers.game_launch_controller import GameLaunchController

    for key in ('XDG_CONFIG_HOME', 'XDG_DATA_HOME', 'XDG_CACHE_HOME', 'XDG_STATE_HOME'):
        monkeypatch.setenv(key, str(tmp_path / key))
    program = tmp_path / 'controlled-emulator'
    program.write_text(f'#!{sys.executable}\nimport time\nprint("Using rewind buffer of 16 MiB", flush=True)\ntime.sleep(60)\n')
    program.chmod(0o755)
    rom = tmp_path / 'fixture.sfc'; rom.write_bytes(b'controlled fixture')
    ra = RetroArchLauncher(executable=str(program))
    native = Snes9xLauncher(startup_timeout=1)
    session = EmulatorSession(ra, native)
    lifecycle = ProcessLifecycleAdapter(HardwareRuntimeOrchestrator(HardwareIndicatorPolicy()), session)
    config = {'retroarch': {'executable': str(program), 'cores': {'directory': ''}},
              'emulation': {'snes_backend': backend, 'snes9x_executable': str(program)}}
    controller = GameLaunchController(launcher=session, process_lifecycle=lifecycle,
                                      config_loader=SimpleNamespace(load=lambda: config))
    core = tmp_path / 'snes9x_libretro.so'; core.write_bytes(b'controlled core fixture')
    controller.core_resolver.resolve = Mock(return_value=SimpleNamespace(path=str(core)))
    controller.validator_factory = Mock(return_value=ReadyValidator())
    controller.diagnostics.explain = Mock(return_value=[])
    adapter = ra if backend == 'retroarch' else native
    real_launch = adapter.launch
    def startup_failure(request):
        result = real_launch(request)
        assert result['success'], result
        return {'success': False, 'error': 'injected post-spawn startup failure'}
    monkeypatch.setattr(adapter, 'launch', startup_failure)
    game = Game('Fixture', 'SNES', 0, '', 'snes9x', rom=str(rom),
                local_file_id='local-file:fixture',
                rvdb_platform_id='platform.nintendo.snes' if backend == 'snes9x' else '')
    played = Mock()
    calls = dict(choose_edition=lambda: {'rom': str(rom), 'local_file_id': game.local_file_id},
                 choose_archive=Mock(), choose_cheats=lambda *args: [], status=Mock(), warning=Mock(), played=played)
    unrelated = subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(60)'], start_new_session=True)
    details = None
    try:
        assert not controller.launch(game, **calls)
        owned = session.active_process
        assert owned is not None and owned.poll() is None
        assert lifecycle.state is HardwareRuntimeState.IDLE
        played.assert_not_called()
        # Neither controller nor shared backend coordinator may start another child.
        assert not controller.launch(game, **calls)
        assert not session.launch(None)['success']
        assert not session.launch_standalone(None)['success']
        assert session.active_process is owned
        details = GameDetails(launch_controller=controller)
        details.show_game(game)
        details.sync_process_session()
        assert details.stop_button.isEnabled()
        assert not details.launch_button.isEnabled()
        with monkeypatch.context() as patch:
            patch.setattr(adapter, 'stop', Mock(side_effect=RuntimeError('cleanup still blocked')))
            details.stop_game()
            assert session.active_process is owned
            assert details.stop_button.isEnabled()
        details.stop_game()
        lifecycle.poll(); details.sync_process_session()
        assert owned.poll() is not None
        assert not session.process_running()
        assert session.active_process is None
        assert not details.stop_button.isEnabled()
        assert details.launch_button.isEnabled()
        details.stop_game()  # repeated UI stop is harmless
        assert unrelated.poll() is None
        session.shutdown()
        # Generated RetroArch configs are transient; native logs/profiles are retained.
        cache = tmp_path / 'XDG_CACHE_HOME' / 'retrovault'
        for name in ('primary-runtime', 'session-runtime', 'overlay-runtime', 'shader-runtime',
                     'contain-runtime', 'core-options-runtime', 'cheat-runtime', 'aspect-probe'):
            assert not [p for p in (cache / name).rglob('*') if p.is_file()]
    finally:
        session.shutdown()
        unrelated.terminate(); unrelated.wait(timeout=5)
        if details is not None: details.close()
