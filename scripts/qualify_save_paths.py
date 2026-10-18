"""Measure RetroArch save naming with disposable copies, never production saves.

This is destination/collision evidence, not proof of recovered gameplay progress.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess

from config import ConfigLoader
from services.retroarch.core_resolver import CoreResolver
from services.retroarch.primary_config_runtime import PrimaryConfigRuntime
from services.retroarch.launcher import RetroArchLauncher
from services.retroarch.process_group import terminate_group, group_exists


SAVE_FLAGS = ('savefiles_in_content_dir', 'savestates_in_content_dir',
              'sort_savefiles_enable', 'sort_savestates_enable',
              'sort_savefiles_by_content_enable', 'sort_savestates_by_content_enable',
              'autosave_interval', 'savestate_auto_save', 'savestate_auto_load',
              'savestate_auto_index', 'savestate_file_compression', 'block_sram_overwrite')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def stopped_save_evidence(code, text, root, owned_group_alive):
    """Require actual flush evidence; a signalled wrapper alone is not success."""
    if owned_group_alive or code not in (0, -signal.SIGTERM):
        raise RuntimeError(f'Controlled Stop did not finish cleanly (status {code}).')
    paths = re.findall(r'\[SRAM\] Saved successfully to "([^"\n]+)"', text)
    if not paths or '[Core] Unloading game...' not in text:
        raise RuntimeError('Missing SRAM flush/core-unload evidence after Stop.')
    for value in paths:
        path = Path(value).resolve(strict=True)
        if not path.is_relative_to(root.resolve()) or not path.is_file() or not path.stat().st_size:
            raise RuntimeError('Save evidence is outside the isolated root or empty.')
    return list(dict.fromkeys(paths))


def probe_settings(text, root):
    if re.search(r'^\s*#include\b', text, re.MULTILINE):
        raise ValueError('Included primary configurations require separate save-policy inspection.')
    flags = {}
    for key in SAVE_FLAGS:
        matches = re.findall(rf'^\s*{key}\s*=\s*"([^"\n]*)"', text, re.MULTILINE)
        if len(matches) > 1:
            raise ValueError(f'Ambiguous save directive: {key}')
        if matches:
            flags[key] = matches[0]
    # Retain naming/flush settings. Redirect roots, not the naming policy.
    settings = {**flags, 'savefile_directory': str(root / 'saves'),
                'savestate_directory': str(root / 'states'),
                'core_options_path': str(root / 'core-options.cfg'),
                'global_core_options': 'true',
                'rgui_config_directory': str(root / 'core-config'),
                'system_directory': str(root / 'system'),
                'config_save_on_exit': 'false', 'history_list_enable': 'false',
                'content_runtime_log': 'false', 'content_runtime_log_aggregate': 'false',
                'auto_overrides_enable': 'false', 'auto_remaps_enable': 'false',
                'auto_shaders_enable': 'false', 'input_overlay_enable': 'false',
                'video_driver': 'null', 'audio_driver': 'null', 'input_driver': 'null',
                'input_joypad_driver': 'null', 'audio_enable': 'false',
                'pause_nonactive': 'false', 'video_threaded': 'false',
                'ui_companion_enable': 'false', 'ui_companion_start_on_boot': 'false',
                'video_shader_enable': 'false', 'video_fullscreen': 'false',
                'network_cmd_enable': 'false', 'stdin_cmd_enable': 'false'}
    return flags, settings


def qualify(rom, output, *, isolated_editions=False):
    original = Path(rom).expanduser().resolve(strict=True)
    if original.suffix.lower() not in ('.sfc', '.smc'):
        raise ValueError('Use a loose SNES fixture.')
    config = ConfigLoader().load()
    core = CoreResolver(config).resolve('snes9x', 'platform.nintendo.snes')
    if not core.path:
        raise ValueError(core.message)
    primary = PrimaryConfigRuntime().discover_source(config.get('retroarch', {}).get('primary_config'))
    if primary is None:
        raise ValueError('No production primary configuration found.')
    root = Path(output).resolve()
    source_text = primary.read_text()
    flags, settings = probe_settings(source_text, root)
    protected = {str(path): digest(path) for path in (original, primary, Path(core.path))}
    match = re.search(r'^rgui_config_directory\s*=\s*"([^"\n]+)"', source_text, re.MULTILINE)
    production_options = Path(match.group(1)).expanduser() if match else primary.parent / 'config'
    def options_snapshot():
        return {str(p): digest(p) for p in production_options.rglob('*.opt') if p.is_file()}
    options_before = options_snapshot()
    root.mkdir(parents=True, exist_ok=False)
    for directory in ('saves', 'states', 'system', 'core-config'):
        (root / directory).mkdir()
    transient = root / 'probe.cfg'
    lines = []
    for key, value in settings.items():
        escaped = value.replace('\\', '\\\\').replace('"', '\\"')
        lines.append(f'{key} = "{escaped}"\n')
    transient.write_text(''.join(lines))
    report = {'source_flags': flags, 'protected_before': protected,
              'isolated_editions': isolated_editions,
              'core': core.path, 'runs': [], 'gameplay_recovery': 'not tested',
              'termination_method': 'owned process-group Stop; normal user Quit not tested',
              'production_options_before': options_before}
    try:
        for edition in ('copy-a', 'copy-b'):
            destination = root / edition / original.name
            destination.parent.mkdir()
            shutil.copyfile(original, destination)
            if isolated_editions:
                from services.saves.policy import SavePolicy
                from services.emulators.session import EmulatorSession
                owner = EmulatorSession(RetroArchLauncher())
                values = SavePolicy(root / 'edition-saves').enable(
                    owner, edition, core.path, destination)
                # Reuse the production transient composer for save directives.
                from services.retroarch.session_config import RetroArchSessionConfig
                composer = RetroArchSessionConfig(root / 'session-config')
                routing = composer.create(save_values=values)
            else:
                composer = None
                routing = ''
            log = root / (edition + '.log')
            command = [config['retroarch']['executable'], '--config', str(transient),
                       '-L', core.path, str(destination),
                       '--verbose', '--log-file', str(log)]
            if routing:
                command += ['--appendconfig', routing]
            with (root / (edition + '.stderr')).open('wb') as stderr:
                process = subprocess.Popen(command, cwd=root, env=dict(os.environ, LC_ALL='C'),
                                           stdout=stderr, stderr=stderr, stdin=subprocess.DEVNULL,
                                           start_new_session=True)
                try:
                    try:
                        process.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        pass
                    if process.poll() is not None:
                        raise RuntimeError('Save probe exited before controlled Stop.')
                    # This probe establishes destinations, not normal-quit
                    # gameplay recovery. Use the existing bounded Stop owner.
                    terminate_group(process, process.pid, RetroArchLauncher._wait_for_process_group_exit)
                    code = process.returncode
                except subprocess.TimeoutExpired:
                    terminate_group(process, process.pid, RetroArchLauncher._wait_for_process_group_exit)
                    raise RuntimeError('Bounded save probe timed out; owned process terminated.')
                finally:
                    if group_exists(process.pid):
                        terminate_group(process, process.pid, RetroArchLauncher._wait_for_process_group_exit)
                    if composer is not None:
                        composer.cleanup()
            text = log.read_text(errors='replace')
            paths = stopped_save_evidence(code, text, root, group_exists(process.pid))
            files = {str(p.relative_to(root)): digest(p) for p in root.rglob('*')
                     if p.is_file() and p.suffix in ('.srm', '.state')}
            report['runs'].append({'copy': edition, 'exit_code': code,
                                   'reported_paths': paths, 'save_files': files})
        report['success'] = True
        first, second = report['runs']
        report['same_save_destination'] = first['reported_paths'] == second['reported_paths']
        report['first_copy_save_preserved'] = all(second['save_files'].get(path) == sha
                                                for path, sha in first['save_files'].items())
        if isolated_editions and (report['same_save_destination'] or not report['first_copy_save_preserved']):
            raise RuntimeError('Isolated copies collided or the second run changed the first save.')
    except Exception as exc:
        report.update(success=False, error=str(exc))
    finally:
        report['protected_unchanged'] = all(Path(path).is_file() and digest(path) == sha
                                            for path, sha in protected.items())
        report['production_options_unchanged'] = options_snapshot() == options_before
        report['success'] = bool(report.get('success') and report['protected_unchanged']
                                 and report['production_options_unchanged'])
        (root / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--isolated-editions', action='store_true')
    args = parser.parse_args()
    result = qualify(args.rom, args.output, isolated_editions=args.isolated_editions)
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result['success'] else 1)
