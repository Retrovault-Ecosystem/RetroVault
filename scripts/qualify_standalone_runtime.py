"""Isolated SNES Library -> native launch -> Stop -> fresh-process relaunch evidence.

Run as a module. A process report never substitutes for user visual/audio/input acceptance.
The native executable must already be installed; this runner never downloads software.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

from config import ConfigLoader, ConfigWriter
from config.paths import RVDB_BUNDLE, config_home
from controllers.game_launch_controller import GameLaunchController
from services.emulators.models import SNES, selected_backend
from services.emulators.session import EmulatorSession
from services.library.import_sources import ImportSourceStore
from services.presentation.process_lifecycle import ProcessLifecycleAdapter
from services.presentation.hardware_runtime import HardwareRuntimeOrchestrator
from services.presentation.hardware_state import HardwareIndicatorPolicy
from services.retroarch.launcher import RetroArchLauncher
from scripts.qualify_retroarch_runtime import digest, pipeline_environment, pipeline_library


def forbidden(*args):
    raise RuntimeError('Standalone launch unexpectedly entered RetroArch preparation.')


def launch_profile(root, rom, seconds, *, restart=False):
    library, game, _ = pipeline_library(root / 'rvdb.bundle.json', rom, 'snes')
    config = ConfigLoader().load()
    if selected_backend(config, game.rvdb_platform_id) != 'snes9x':
        raise ValueError('Explicit standalone backend did not persist.')
    if restart and library.recent() != [game.local_file_id]:
        raise ValueError('Selected edition history did not survive process restart.')
    session = EmulatorSession(RetroArchLauncher(executable='/not-used/retroarch'))
    lifecycle = ProcessLifecycleAdapter(HardwareRuntimeOrchestrator(HardwareIndicatorPolicy()), session)
    controller = GameLaunchController(launcher=session, process_lifecycle=lifecycle)
    report = {'pid': os.getpid(), 'local_file_id': game.local_file_id, 'status': [], 'warnings': []}
    try:
        variants = [v for v in game.variants if v.get('local_file_id') == game.local_file_id]
        if len(variants) != 1:
            raise ValueError('Expected exactly one physical edition.')
        controller.launch(game, choose_edition=lambda: variants[0], choose_archive=forbidden,
                          choose_cheats=forbidden, presentation_provider=forbidden,
                          status=report['status'].append,
                          warning=lambda *args: report['warnings'].append(args), played=library.record_played)
        report['launch'] = dict(controller.last_result)
        if not report['launch'].get('success'):
            raise ValueError(str(report['launch']))
        start = time.monotonic()
        while time.monotonic() - start < seconds and session.process_running():
            lifecycle.poll()
            time.sleep(0.1)
        report['observed_seconds'] = round(time.monotonic() - start, 3)
        if not session.process_running():
            raise ValueError('Native session exited before the observation deadline.')
        if restart:
            session.shutdown()
        else:
            controller.stop()
        report['stopped'] = not session.process_running()
        if not report['stopped']:
            raise ValueError('Native session failed to stop.')
        report['recent'] = library.recent()
        if report['recent'] != [game.local_file_id] or report['warnings']:
            raise ValueError('History or launch warnings failed verification.')
        log = Path(report['launch']['log'])
        shutil.copyfile(log, root / ('restart-native.log' if restart else 'native.log'))
        report['save_files'] = {str(p.relative_to(report['launch']['saves'])): digest(p)
                                for folder in ('sram', 'states')
                                for p in (Path(report['launch']['saves']) / folder).rglob('*') if p.is_file()}
        return report
    finally:
        session.shutdown()
        controller.cleanup_inputs()


def qualify(executable, original, output, seconds):
    if not 1 <= seconds <= 30:
        raise ValueError('Observation duration must be 1–30 seconds.')
    root = Path(output).resolve()
    original = Path(original).expanduser().resolve()
    executable = Path(executable).expanduser().resolve()
    if original.suffix.lower() not in ('.smc', '.sfc') or not original.is_file():
        raise ValueError('Qualification requires an existing loose SNES ROM.')
    root.mkdir(parents=True, exist_ok=False)
    user_root = config_home() / 'retrovault'
    user_paths = set(user_root.glob('*.json'))
    protected = {str(p): digest(p) for p in [original, RVDB_BUNDLE, *sorted(user_paths)]}
    # Record the production RetroArch configuration if one is available, without requiring it.
    from services.retroarch.primary_config_runtime import PrimaryConfigRuntime
    ra = ConfigLoader().load().get('retroarch', {})
    primary = PrimaryConfigRuntime().discover_source(ra.get('primary_config') or None)
    if primary:
        protected[str(primary)] = digest(primary)
    report = {'backend': 'snes9x', 'platform': SNES, 'executable': str(executable),
              'executable_sha256': digest(executable), 'requested_seconds': seconds,
              'user_acceptance': 'pending', 'protected_before': protected, 'success': False}
    try:
        shutil.copyfile(RVDB_BUNDLE, root / 'rvdb.bundle.json')
        source = root / 'roms'
        source.mkdir()
        rom = source / original.name
        shutil.copyfile(original, rom)
        with pipeline_environment(root):
            ConfigWriter().write({'library': {'sources': []},
                                  'emulation': {'snes_backend': 'snes9x', 'snes9x_executable': str(executable)}})
            ImportSourceStore().persist_directory(source, source_id='standalone-snes', source_name='Standalone SNES')
            report['first_run'] = launch_profile(root, rom, seconds)
            report['profile_sha256_before_restart'] = digest(report['first_run']['launch']['config'])
            env = dict(os.environ, PYTHONPATH=str(Path(__file__).resolve().parents[1]))
            result = subprocess.run([sys.executable, '-B', '-m', 'scripts.qualify_standalone_runtime',
                                     '--restart', str(root), '--rom', str(rom)], env=env, cwd=root,
                                    capture_output=True, text=True, timeout=35)
            if result.returncode:
                raise RuntimeError('Fresh-process relaunch failed: ' + result.stderr + result.stdout)
            report['restart'] = json.loads(result.stdout)
            first, second = report['first_run'], report['restart']
            if second['pid'] == first['pid'] or second['local_file_id'] != first['local_file_id']:
                raise ValueError('Restart did not preserve physical identity in a fresh process.')
            if first['launch']['saves'] != second['launch']['saves']:
                raise ValueError('Restart changed native save ownership.')
            if any(path not in second['save_files'] for path in first['save_files']):
                raise ValueError('Restart removed an existing native save file.')
            if any(second['save_files'].get(path) != value for path, value in first['save_files'].items()
                   if path.startswith('states/')):
                raise ValueError('Restart changed an existing native save state.')
        report['success'] = True
    except Exception as exc:
        report['error'] = str(exc)
    finally:
        report['protected_after'] = {p: digest(p) if Path(p).is_file() else None for p in protected}
        report['user_state_preserved'] = (report['protected_after'] == protected and
                                          set(user_root.glob('*.json')) == user_paths)
        if not report['user_state_preserved']:
            report['success'] = False
        (root / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--executable')
    parser.add_argument('--rom', required=True)
    parser.add_argument('--output')
    parser.add_argument('--seconds', type=float, default=30)
    parser.add_argument('--restart')
    args = parser.parse_args()
    if args.restart:
        root = Path(args.restart).resolve()
        with pipeline_environment(root):
            result = launch_profile(root, args.rom, 3, restart=True)
        print(json.dumps(result))
        return 0
    if not args.executable or not args.output:
        parser.error('--executable and --output are required')
    result = qualify(args.executable, args.rom, args.output, args.seconds)
    print(json.dumps(result, indent=2))
    return 0 if result['success'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
