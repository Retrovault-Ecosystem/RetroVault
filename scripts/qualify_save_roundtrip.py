"""User-paced, isolated save round trips through production launch services.

Prepare once, run create, then run reload separately. Neither successful process
exit nor save-file existence is reported as recovered gameplay acceptance.
"""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import shutil
import time

from config import ConfigLoader, ConfigWriter
from config.paths import RVDB_BUNDLE, config_home
from config.controller_preferences import defaults, DEFAULT_KEYS
from controllers.game_launch_controller import GameLaunchController
from services.emulators.session import EmulatorSession
from services.library.import_sources import ImportSourceStore
from services.retroarch.core_resolver import CoreResolver
from services.retroarch.launcher import RetroArchLauncher
from services.retroarch.primary_config_runtime import PrimaryConfigRuntime
from services.saves.context import save_context
from services.saves.policy import SavePolicy
from scripts.qualify_retroarch_runtime import (digest, isolated_config, pipeline_environment,
                                              pipeline_library, pipeline_composition)


def snapshot(context):
    return {str(path): digest(path) for root in (context.sram, context.states)
            if root is not None and root.is_dir() for path in root.iterdir() if path.is_file()}


def validate_restart(previous, saves_before, application_pid):
    if not previous.get('success') or previous.get('phase') != 'create':
        raise ValueError('The create phase did not finish successfully.')
    if previous.get('pid') == application_pid:
        raise ValueError('Reload requires a fresh application process.')
    if not previous.get('saves_after') or previous['saves_after'] != saves_before:
        raise ValueError('Saved files changed between create and reload.')


def validate_saved_files(context, files, state_only=False):
    requirements = [('state', context.states)]
    if not state_only:
        requirements.append(('sram', context.sram))
    for kind, folder in requirements:
        candidates = [Path(path) for path in files if Path(path).parent == folder]
        if kind == 'state':
            candidates = [p for p in candidates if re.search(r'(?:\.state\d*|\.\d{3})$', p.name)]
        else:
            candidates = [p for p in candidates if p.suffix == '.srm']
        if not any(p.is_file() and p.stat().st_size > 0 for p in candidates):
            raise ValueError(f'No nonempty {kind} save was captured; repeat the fixture.')


def prepare(rom, root, backend, native='', *, platform='snes', state_only=False):
    original = Path(rom).expanduser().resolve(strict=True)
    config = ConfigLoader().load()
    primary = PrimaryConfigRuntime().discover_source(config.get('retroarch', {}).get('primary_config') or None)
    if primary is None:
        raise ValueError('Primary RetroArch configuration is required for isolated qualification.')
    extensions = {'master-system': ('.sms',), 'snes': ('.sfc', '.smc'), 'genesis': ('.md', '.gen'), 'nes': ('.nes',)}
    if platform not in extensions or original.suffix.lower() not in extensions[platform]:
        raise ValueError('Use an approved loose fixture matching the selected platform.')
    if backend == 'snes9x' and platform != 'snes':
        raise ValueError('Native Snes9x qualification requires SNES.')
    protected = {str(path): digest(path) for path in
                 (original, primary, RVDB_BUNDLE, *sorted((config_home() / 'retrovault').glob('*.json')))}
    root.mkdir(parents=True, exist_ok=False)
    source = root / 'roms'
    source.mkdir()
    copied = source / original.name
    shutil.copyfile(original, copied)
    shutil.copyfile(RVDB_BUNDLE, root / 'rvdb.bundle.json')
    text = isolated_config(primary.read_text(), root)
    # All fallback core-options/profile write authorities are isolated as well.
    extra = {'rgui_config_directory': str(root / 'core-config'),
             'core_options_path': str(root / 'core-options.cfg'), 'global_core_options': 'true',
             'input_save_state': 'f2', 'input_load_state': 'f4', 'input_exit_emulator': 'escape'}
    (root / 'core-config').mkdir()
    for key, value in extra.items():
        text = re.sub(rf'^\s*{key}\s*=.*$', '', text, flags=re.MULTILINE)
        text += f'\n{key} = "{value}"\n'
    isolated = root / 'source.cfg'
    isolated.write_text(text)
    config = deepcopy(config)
    config['library'] = {'sources': []}
    config['retroarch']['primary_config'] = str(isolated)
    config['emulation'] = dict(config.get('emulation', {}), snes_backend=backend)
    if backend == 'snes9x':
        config['emulation']['snes9x_executable'] = str(Path(native).resolve(strict=True))
    config['controllers'] = defaults()
    config['controllers'][backend] = dict(mode='managed', players=[dict(
        kind='keyboard', device={}, bindings=dict(DEFAULT_KEYS))])
    with pipeline_environment(root):
        ConfigWriter().write(config)
        ImportSourceStore().persist_directory(source, source_id='save-roundtrip', source_name='Save round-trip fixture')
        _, game, _ = pipeline_library(root / 'rvdb.bundle.json', copied, platform)
        if backend == 'retroarch':
            core = CoreResolver(config).resolve(game.core, game.rvdb_platform_id)
            if not core.path:
                raise ValueError(core.message)
            SavePolicy().enable(EmulatorSession(RetroArchLauncher()), game.local_file_id, core.path, copied)
        context = save_context(game, config)
        protected[str(context.runtime)] = digest(context.runtime)
        metadata = {'backend': backend, 'rom': str(copied), 'local_file_id': game.local_file_id,
                    'platform': platform, 'state_only': state_only,
                    'protected': protected, 'gameplay_acceptance': 'pending',
                    'sram': str(context.sram), 'states': str(context.states)}
    (root / 'fixture.json').write_text(json.dumps(metadata, indent=2) + '\n')
    return metadata


def run(root, phase, seconds=900):
    if not 1 <= seconds <= 1800:
        raise ValueError('Use a bounded observation window of at most 30 minutes.')
    metadata = json.loads((root / 'fixture.json').read_text())
    output = root / (phase + '.json')
    if output.exists():
        raise ValueError('This phase already has evidence; use a new fixture for a repeat.')
    if phase == 'reload' and not (root / 'create.json').exists():
        raise ValueError('Complete the create phase before reload.')
    report = {'phase': phase, 'pid': os.getpid(), 'gameplay_acceptance': 'pending', 'success': False,
              'scope': 'save-state only' if metadata.get('state_only') else 'in-game save and save-state'}
    with pipeline_environment(root):
        library, game, _ = pipeline_library(root / 'rvdb.bundle.json', metadata['rom'], metadata.get('platform', 'snes'))
        config = ConfigLoader().load()
        context = save_context(game, config)
        if game.local_file_id != metadata['local_file_id']:
            raise ValueError('Physical edition identity changed.')
        report['saves_before'] = snapshot(context)
        if phase == 'reload':
            validate_restart(json.loads((root / 'create.json').read_text()),
                             report['saves_before'], os.getpid())
        session = EmulatorSession(RetroArchLauncher(executable=config['retroarch']['executable'],
                                                    presentation_config_provider=ConfigLoader().load))
        controller = GameLaunchController(launcher=session)
        statuses, warnings = [], []
        try:
            variant = next(v for v in game.variants if v['local_file_id'] == game.local_file_id)
            ok = controller.launch(game, choose_edition=lambda: variant,
                choose_archive=lambda *args: '', choose_cheats=lambda *args: [],
                status=statuses.append, warning=lambda *args: warnings.append(args),
                played=library.record_played, presentation_provider=pipeline_composition().build_launch)
            report['launch'] = controller.last_result
            if not ok:
                raise RuntimeError(str(controller.last_result))
            process = session.active_process
            report['emulator_pid'] = process.pid
            print('RUNNING: quit normally when the save/reload observation is finished.', flush=True)
            start = time.monotonic()
            while session.process_running() and time.monotonic() - start < seconds:
                time.sleep(0.1)
            report['observed_seconds'] = round(time.monotonic() - start, 3)
            if session.process_running():
                raise RuntimeError('Observation timed out; forced cleanup is not normal-quit acceptance.')
            report['exit_code'] = process.poll()
            if report['exit_code'] != 0:
                raise RuntimeError('Emulator did not report normal successful exit.')
            session.clear_exited_process()
            report['saves_after'] = snapshot(context)
            validate_saved_files(context, report['saves_after'], metadata.get('state_only', False))
            report['success'] = True
        except Exception as exc:
            report['error'] = str(exc)
        finally:
            try:
                session.shutdown()
                controller.cleanup_inputs()
            except (OSError, RuntimeError) as exc:
                report.update(success=False, cleanup_error=str(exc))
            report['owned_process_remaining'] = session.process_running()
            report['status'], report['warnings'] = statuses, warnings
            report['protected_unchanged'] = all(Path(path).is_file() and digest(path) == sha
                                                for path, sha in metadata['protected'].items())
            report['success'] = bool(report['success'] and report['protected_unchanged']
                                     and not report['owned_process_remaining'])
            output.write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--rom')
    parser.add_argument('--backend', choices=('retroarch', 'snes9x'), default='retroarch')
    parser.add_argument('--native', default='')
    parser.add_argument('--platform', choices=('snes', 'genesis', 'nes', 'master-system'), default='snes')
    parser.add_argument('--state-only', action='store_true', help='Explicitly exclude in-game save qualification.')
    parser.add_argument('--phase', choices=('create', 'reload'))
    parser.add_argument('--seconds', type=int, default=900)
    args = parser.parse_args()
    root = Path(args.root).resolve()
    result = prepare(args.rom, root, args.backend, args.native, platform=args.platform,
                     state_only=args.state_only) if args.prepare else run(root, args.phase, args.seconds)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result.get('success', args.prepare) else 1)
