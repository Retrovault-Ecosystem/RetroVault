"""One bounded, isolated production launch. Run with python -m scripts.qualify_retroarch_runtime.

The JSON report records process evidence; it never asserts visual acceptance.
Each invocation requires a fresh report directory and an explicit user-owned ROM.
"""
import argparse
from contextlib import contextmanager
import subprocess
import sys
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import time

from config import ConfigLoader
from models.launch_profile import LaunchProfile
from services.rvdb import RVDBError
from services.retroarch.core_resolver import CoreResolver
from services.retroarch.launcher import RetroArchLauncher
from services.retroarch.primary_config_runtime import PrimaryConfigRuntime
from services.retroarch.content_display_aspect_probe import ContentLoadedDisplayAspectProbe

PLATFORMS = {
    'nes': 'platform.nintendo.nes',
    'snes': 'platform.nintendo.snes',
    'genesis': 'platform.sega.genesis',
}


def content_platform(rom, expected_platform):
    """Require the Library's RVDB identification, not an injected test-only ID."""
    from services.library.rvdb_resolver import RVDBLibraryResolver
    bundle = Path(__file__).resolve().parents[1] / 'data/rvdb/rvdb.bundle.json'
    resolver = RVDBLibraryResolver.from_bundle(bundle)
    platform = resolver.platform_for_extension(Path(rom).suffix)
    if platform is None or platform.id != expected_platform:
        raise ValueError('Library metadata cannot identify this content as ' + expected_platform)
    return platform.id


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def capture_presentation(command, output):
    """Retain the final layered overlay evidence before transient cleanup.

    This is configuration/asset evidence, not a screenshot or visual acceptance.
    Read only the primary and append configs explicitly supplied to this launch.
    """
    paths = []
    for index, argument in enumerate(command[:-1]):
        if argument == '--config':
            paths.append(Path(command[index + 1]))
        elif argument == '--appendconfig':
            paths.extend(Path(value) for value in command[index + 1].split('|'))
    effective = {}
    keys = {'input_overlay', 'input_overlay_enable', 'auto_overrides_enable',
            'input_overlay_enable_autopreferred', 'custom_viewport_x',
            'custom_viewport_y', 'custom_viewport_width', 'custom_viewport_height'}
    for path in paths:
        for line in path.read_text().splitlines():
            key, separator, value = line.partition('=')
            if separator and key.strip() in keys:
                effective[key.strip()] = value.strip().strip('"')
    record = {'effective_settings': effective,
              'evidence_type': 'launch_configuration_and_asset_not_screenshot'}
    if '--set-shader' in command:
        shader = Path(command[command.index('--set-shader') + 1])
        record['shader_preset'] = shader.read_text()
    if effective.get('input_overlay_enable') != 'true':
        return record
    overlay = Path(effective['input_overlay']).expanduser()
    match = re.search(r'^overlay0_overlay\s*=\s*"([^"\n]+)"\s*$',
                      overlay.read_text(), re.MULTILINE)
    if not match:
        raise ValueError('Selected overlay does not declare its artwork.')
    artwork = (overlay.parent / match.group(1)).resolve()
    destination = Path(output) / 'selected-overlay.png'
    shutil.copyfile(artwork, destination)
    record.update(overlay=str(overlay), overlay_sha256=digest(overlay),
                  artwork=str(artwork), artwork_sha256=digest(artwork),
                  retained_artwork=str(destination))
    return record


def isolated_config(text, root):
    if re.search(r'^\s*#include\b', text, re.MULTILINE):
        raise ValueError('Qualification source must not include other configurations.')
    settings = {
        'config_save_on_exit': 'false', 'history_list_enable': 'false',
        'savestate_auto_save': 'false', 'savestate_auto_load': 'false',
        'content_runtime_log': 'false', 'content_runtime_log_aggregate': 'false',
        'savefiles_in_content_dir': 'false', 'savestates_in_content_dir': 'false',
        'sort_savefiles_enable': 'false', 'sort_savestates_enable': 'false',
        'log_to_file': 'false',
    }
    for key, name in {
        'savefile_directory': 'saves', 'savestate_directory': 'states',
        'screenshot_directory': 'screenshots', 'runtime_log_directory': 'runtime-logs',
        'recording_output_directory': 'recordings',
    }.items():
        directory = root / name
        directory.mkdir()
        settings[key] = str(directory)
    for key, value in settings.items():
        text = re.sub(rf'^\s*{re.escape(key)}\s*=.*$', '', text, flags=re.MULTILINE)
        text += f'\n{key} = "{value}"\n'
    return text


def qualify(platform, rom, output, seconds, *, via_controller=False, pipeline=False, visual_tuning=None):
    if pipeline:
        if visual_tuning is not None:
            from services.presentation.visual_tuning import validate_values
            validate_values(PLATFORMS.get(platform, ""), visual_tuning)
        pipeline_case(platform)  # Reject out-of-scope targets before creating output.
    lock_path = Path(__file__).resolve().parents[1] / "build" / "milestone5" / "qualification.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        blocked = lock_path.with_suffix('.blocked')
        if blocked.exists():
            raise RuntimeError('Previous qualification retained process ownership; inspect ' + str(blocked))
        report = (_qualify_pipeline(rom, output, seconds, platform=platform, visual_tuning=visual_tuning) if pipeline else
                  _qualify(platform, rom, output, seconds, via_controller=via_controller))
        if report['owned_group_remaining']:
            blocked.write_text(json.dumps(report, indent=2) + '\n')
        return report


def _qualify(platform, rom, output, seconds, *, via_controller=False):
    if not 1 <= seconds <= 30:
        raise ValueError('Duration must be between 1 and 30 seconds.')
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=False)
    if Path(rom).suffix.lower() in {'.zip', '.7z', '.rar'}:
        raise ValueError('Use an explicit unarchived qualification ROM.')
    platform_id = content_platform(rom, PLATFORMS[platform])
    config = ConfigLoader().load()
    selected = CoreResolver(config).resolve('', platform_id)
    if selected.status != 'resolved':
        raise ValueError(selected.message)
    source = PrimaryConfigRuntime().discover_source(config.get('retroarch', {}).get('primary_config') or None)
    if source is None:
        raise ValueError('No primary configuration available.')
    before = digest(source)
    isolated = root / 'qualification-source.cfg'
    isolated.write_text(isolated_config(source.read_text(), root))
    executable = config['retroarch']['executable']
    wrapper = root / 'logged-retroarch'
    wrapper.write_text('#!/bin/sh\nexec ' + shlex.quote(executable)
                       + ' --verbose --log-file ' + shlex.quote(str(root / 'retroarch.log')) + ' "$@" 2>>' + shlex.quote(str(root / 'wrapper.stderr')) + '\n')
    wrapper.chmod(0o700)
    old_cache = os.environ.get('XDG_CACHE_HOME')
    os.environ['XDG_CACHE_HOME'] = str(root / 'cache')
    launcher = RetroArchLauncher(executable=str(wrapper),
        content_display_aspect_probe=ContentLoadedDisplayAspectProbe(directory=root / 'probe'))
    # Explicitly route every transient owner, including older non-XDG services.
    for name in ('primary_config_runtime', 'session_config', 'core_options_runtime',
                 'overlay_runtime', 'shader_runtime', 'contain_runtime',
                 'adaptive_bezel_runtime', 'cheat_runtime'):
        runtime = getattr(launcher, name)
        if hasattr(runtime, 'directory'):
            runtime.directory = root / 'transients' / name
    launcher.cheat_runtime.runtime_root = root / 'transients' / 'cheat_runtime'
    report = {'platform': platform_id, 'platform_authority': 'library_rvdb_extension_resolution', 'rom': str(Path(rom).resolve()),
              'core': selected.path, 'core_sha256': digest(selected.path),
              'configured_executable': executable, 'source': str(source),
              'source_sha256_before': before, 'visual_acceptance': 'pending',
              'requested_seconds': seconds}
    controller = None
    try:
        if via_controller:
            from copy import deepcopy
            from controllers.game_launch_controller import GameLaunchController
            from services.library.models import Game
            from services.presentation.factory import PresentationCompositionFactory
            from services.presentation.store import PresentationStore
            from services.presentation.manifest import PresentationRecommendationManifest
            from services.presentation.process_lifecycle import ProcessLifecycleAdapter
            from services.presentation.hardware_runtime import HardwareRuntimeOrchestrator
            from services.presentation.hardware_state import HardwareIndicatorPolicy
            qualified_config = deepcopy(config)
            qualified_config['retroarch']['primary_config'] = str(isolated)
            loader = ConfigLoader()
            loader.load = lambda: deepcopy(qualified_config)
            launcher.presentation_config_provider = loader.load
            lifecycle = ProcessLifecycleAdapter(
                HardwareRuntimeOrchestrator(HardwareIndicatorPolicy()), launcher)
            controller = GameLaunchController(launcher=launcher, config_loader=loader,
                                              process_lifecycle=lifecycle)
            composition = PresentationCompositionFactory(
                config_loader=loader, presentation_store=PresentationStore(),
                recommendation_manifest=PresentationRecommendationManifest())
            game = Game(Path(rom).stem, platform, 0, '', selected.path,
                        rom=report['rom'], rvdb_platform_id=platform_id)
            report['workflow'] = 'GameLaunchController'
            report['status_messages'] = []
            report['warnings'] = []
            report['played'] = []
            controller.launch(game,
                choose_edition=lambda: {'rom': game.rom, 'name': game.name},
                choose_archive=lambda rom: '', choose_cheats=lambda *args: [],
                status=report['status_messages'].append,
                warning=lambda title, message: report['warnings'].append([title, message]),
                played=lambda selected_game: report['played'].append(selected_game.rom),
                presentation_provider=composition.build_launch)
            result = controller.last_result
        else:
            result = launcher.launch(LaunchProfile(Path(rom).stem, report['rom'], selected.path,
                                    config=str(isolated), platform_id=platform_id))
        report['launch'] = result
        if result['success']:
            report['presentation'] = capture_presentation(result['command'], root)
            report['owned_group'] = launcher._active_group
            start = time.monotonic()
            while time.monotonic() - start < seconds and launcher.process_running():
                time.sleep(0.1)
            report['observed_seconds'] = round(time.monotonic() - start, 3)
            report['alive_at_deadline'] = launcher.process_running()
            if controller is not None:
                controller.stop()
                report['stop_succeeded'] = not launcher.process_running()
            else:
                report['stop_succeeded'] = launcher.stop()
    except (OSError, RuntimeError, ValueError) as exc:
        report['error'] = str(exc)
    finally:
        try:
            launcher.shutdown()
            if controller is not None:
                controller.cleanup_inputs()
            report['shutdown_succeeded'] = True
        except (OSError, RuntimeError) as exc:
            report['shutdown_succeeded'] = False
            report['shutdown_error'] = str(exc)
        report['owned_group_remaining'] = launcher.process_running() or launcher._probe_running()
        report['cleanup_errors'] = launcher.cleanup_errors
        report['source_sha256_after'] = digest(source)
        report['source_unchanged'] = before == report['source_sha256_after']
        report['remaining_transients'] = [str(p.relative_to(root)) for directory in ('transients', 'probe')
                                        for p in (root / directory).rglob('*') if p.is_file()]
        (root / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        if old_cache is None:
            os.environ.pop('XDG_CACHE_HOME', None)
        else:
            os.environ['XDG_CACHE_HOME'] = old_cache
    return report


# These are qualification cases, not core/readiness/format policies. Those remain
# owned by RVDB and the production services. Asset references come from the catalog.
PIPELINE_CASES = {
    'nes': ('NES', 'rvv.overlay.nes.classic'),
    'snes': ('SNES', 'rvv.overlay.snes.classic'),
    'genesis': ('Genesis', 'rvv.overlay.genesis.classic'),
}


def pipeline_case(platform):
    from services.presentation.platform_policy import PlatformPresentationPolicyRegistry, PlatformPresentationPolicyState
    from services.presentation.visual_manifest import VisualAssetCatalogManifest
    if platform not in PIPELINE_CASES:
        raise ValueError('No complete-pipeline qualification case for ' + str(platform))
    platform_id = PLATFORMS[platform]
    if PlatformPresentationPolicyRegistry.state_for(platform_id) is not PlatformPresentationPolicyState.READY:
        raise ValueError('Production presentation is not READY for ' + platform_id)
    label, asset_id = PIPELINE_CASES[platform]
    asset = VisualAssetCatalogManifest().load().require(asset_id)
    return {'platform_id': platform_id, 'label': label, 'preference': asset.reference,
            'collection': label + ' pipeline qualification'}


@contextmanager
def pipeline_environment(root):
    """Establish isolation before constructing any application services."""
    root = Path(root).resolve()
    values = {'XDG_CONFIG_HOME': str(root / 'profile'),
              'XDG_CACHE_HOME': str(root / 'cache'),
              'XDG_DATA_HOME': str(root / 'data')}
    previous = {key: os.environ.get(key) for key in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def pipeline_library(bundle, rom, platform="nes"):
    from controllers.library_controller import LibraryController
    from services.library.rvdb_resolver import RVDBLibraryResolver
    resolver = RVDBLibraryResolver.from_bundle(bundle)
    expected = pipeline_case(platform)['platform_id']
    identified = resolver.platform_for_extension(Path(rom).suffix)
    if identified is None or identified.id != expected:
        raise ValueError('Library metadata cannot uniquely identify this content as ' + expected)
    library = LibraryController(rvdb_resolver=resolver)
    matches = [game for game in library.get_games()
               if Path(game.rom).resolve() == Path(rom).resolve()]
    if len(matches) != 1:
        raise ValueError('Expected exactly one discovered Library entry for the staged ROM.')
    game = matches[0]
    if game.rvdb_platform_id != expected or not game.local_file_id.startswith('local-file:'):
        raise ValueError('Scanned entry lacks expected canonical platform or registered local identity.')
    return library, game, resolver


def pipeline_composition():
    from services.presentation.factory import PresentationCompositionFactory
    from services.presentation.store import PresentationStore
    from services.presentation.manifest import PresentationRecommendationManifest
    return PresentationCompositionFactory(
        config_loader=ConfigLoader(), presentation_store=PresentationStore(),
        recommendation_manifest=PresentationRecommendationManifest())


def pipeline_snapshot(library, game):
    from services.library.identity import game_identity
    from services.presentation.store import PresentationStore
    decision = pipeline_composition().build_launch().describe(game)
    if not decision.available:
        raise ValueError(decision.error)
    identity = game_identity(game)
    saved = PresentationStore().load()['games'].get(identity)
    return {
        'local_file_id': identity, 'platform_id': game.rvdb_platform_id,
        'rvdb_game_id': game.rvdb_game_id, 'rom': str(Path(game.rom).resolve()),
        'visible_games': len(library.get_games()), 'favorite': game.favorite,
        'collections': [name for name in library.collection_names()
                        if any(game_identity(item) == identity for item in library.collection_games(name))],
        'recent': library.recent(), 'saved_overlay': saved.overlay if saved else '',
        'requested_overlay': decision.requested.overlay,
        'selected_overlay': decision.selected.overlay, 'selected_shader': decision.selected.shader,
        'presentation_authority': decision.authority,
        'visual_tuning': dict(decision.visual_tuning),
        'sources': library.import_source_store.sources(),
    }


def pipeline_restart(root, bundle, rom, platform="nes"):
    """Run service reconstruction in a new interpreter, never a reused object graph."""
    command = [sys.executable, '-B', '-m', 'scripts.qualify_retroarch_runtime',
               '--restart-profile', str(root), '--bundle', str(bundle), '--rom', str(rom),
               '--platform', platform]
    environment = dict(os.environ)
    environment['PYTHONPATH'] = str(Path(__file__).resolve().parents[1])
    cwd = Path(root) / 'restart-cwd'
    cwd.mkdir(exist_ok=True)
    result = subprocess.run(command, cwd=cwd, env=environment, capture_output=True,
                            text=True, timeout=45, check=False)
    if result.returncode:
        raise RuntimeError('Fresh-process restart failed: ' + result.stderr.strip())
    return json.loads(result.stdout)


def _qualify_pipeline(rom, output, seconds, *, platform="nes", visual_tuning=None):
    from copy import deepcopy
    from config import ConfigWriter
    from config.paths import RVDB_BUNDLE, config_home
    from services.library.import_sources import ImportSourceStore
    from services.library.presentation_studio import LibraryPresentationStudioService
    from services.presentation.store import PresentationStore
    from controllers.game_launch_controller import GameLaunchController
    from services.presentation.process_lifecycle import ProcessLifecycleAdapter
    from services.presentation.hardware_runtime import HardwareRuntimeOrchestrator
    from services.presentation.hardware_state import HardwareIndicatorPolicy

    case = pipeline_case(platform)
    if not 1 <= seconds <= 30:
        raise ValueError('Duration must be between 1 and 30 seconds.')
    root = Path(output).resolve()
    root.mkdir(parents=True, exist_ok=False)
    original = Path(rom).expanduser().resolve()
    report = {'workflow': case['label'] + ' complete platform pipeline', 'platform': case['platform_id'],
              'original_rom': str(original), 'requested_seconds': seconds,
              'visual_acceptance': 'pending', 'stages': {}, 'warnings': [],
              'owned_group_remaining': False, 'remaining_transients': [], 'cleanup_errors': []}
    protected = {}
    user_directory = None
    user_files_before = set()
    launcher = controller = None
    stage = 'setup'
    try:
        if original.suffix.lower() in {'.zip', '.7z', '.rar'} or not original.is_file():
            raise ValueError('Pipeline requires an existing unarchived ROM.')
        config = ConfigLoader().load()
        source = PrimaryConfigRuntime().discover_source(config.get('retroarch', {}).get('primary_config') or None)
        if source is None:
            raise ValueError('No primary configuration available.')
        user_directory = config_home() / "retrovault"
        user_files_before = {str(path) for path in user_directory.glob("*.json")}
        protected = {str(path): digest(path) for path in
                     [original, source, RVDB_BUNDLE, *sorted((config_home() / 'retrovault').glob('*.json'))]}
        report['protected_files_before'] = protected
        report['source'] = str(source)
        report['bundle_sha256'] = digest(RVDB_BUNDLE)
        snapshot_bundle = root / 'rvdb.bundle.json'
        shutil.copyfile(RVDB_BUNDLE, snapshot_bundle)
        staged_source = root / 'roms'
        staged_source.mkdir()
        staged_rom = staged_source / original.name
        shutil.copyfile(original, staged_rom)
        if digest(staged_rom) != protected[str(original)]:
            raise ValueError('Staged ROM differs from the original.')
        report['rom'] = str(staged_rom)
        isolated = root / 'qualification-source.cfg'
        isolated.write_text(isolated_config(source.read_text(), root))
        executable = config['retroarch']['executable']
        wrapper = root / 'logged-retroarch'
        wrapper.write_text('#!/bin/sh\nexec ' + shlex.quote(executable)
                           + ' --verbose --log-file ' + shlex.quote(str(root / 'retroarch.log'))
                           + ' "$@" 2>>' + shlex.quote(str(root / 'wrapper.stderr')) + '\n')
        wrapper.chmod(0o700)
        qualified = deepcopy(config)
        qualified['library'] = {'sources': []}
        qualified['retroarch']['primary_config'] = str(isolated)
        # Keep configured installed resources; all writable application state is isolated.
        report['stages'][stage] = {'passed': True}
        with pipeline_environment(root):
            try:
                ConfigWriter().write(qualified)
                stage = 'source_registration'
                ImportSourceStore().persist_directory(staged_source, source_id=platform + '-pipeline',
                                                       source_name=case['collection'])
                report['stages'][stage] = {'passed': True}
                stage = 'library_discovery'
                library, game, resolver = pipeline_library(snapshot_bundle, staged_rom, platform)
                report['local_file_id'] = game.local_file_id
                report['rvdb_game_id'] = game.rvdb_game_id
                report['rvdb_supported_cores'] = [ref.id for ref in resolver.supported_cores(game.rvdb_platform_id)]
                report['stages'][stage] = {'passed': True, 'constructed_by': 'LibraryService.load'}
                stage = 'core_readiness'
                selected = CoreResolver(ConfigLoader().load()).resolve(game.core, game.rvdb_platform_id)
                if selected.status != 'resolved':
                    raise ValueError(selected.message)
                report['core'] = selected.path
                report['core_sha256'] = digest(selected.path)
                report['stages'][stage] = {'passed': True}
                stage = 'user_persistence'
                library.set_favorite(game, True)
                library.create_collection(case['collection'])
                library.add_to_collection(case['collection'], game)
                LibraryPresentationStudioService(PresentationStore()).assign(
                    'overlay', 'game', case['preference'], game)
                if (game.local_file_id not in library.library.state.favorites()
                        or not any(item.local_file_id == game.local_file_id
                                   for item in library.collection_games(case['collection']))
                        or PresentationStore().load()['games'][game.local_file_id].overlay != case['preference']):
                    raise ValueError('User preferences did not persist under the scanned local identity.')
                report['stages'][stage] = {'passed': True}
                if visual_tuning is not None:
                    PresentationStore().set_visual_tuning('systems', game.rvdb_platform_id, game.rvdb_platform_id, visual_tuning)
                stage = 'presentation'
                report['before_launch'] = pipeline_snapshot(library, game)
                if report['before_launch']['recent']:
                    raise ValueError('Isolated profile unexpectedly has launch history.')
                report['stages'][stage] = {'passed': True}
                stage = 'launch'
                launcher = RetroArchLauncher(executable=str(wrapper), presentation_config_provider=ConfigLoader().load)
                lifecycle = ProcessLifecycleAdapter(HardwareRuntimeOrchestrator(HardwareIndicatorPolicy()), launcher)
                controller = GameLaunchController(launcher=launcher, process_lifecycle=lifecycle)
                report['status_messages'] = []
                variants = [variant for variant in game.variants
                            if variant.get('local_file_id') == game.local_file_id]
                if len(variants) != 1:
                    raise ValueError('Expected one scanned edition record for the selected identity.')
                controller.launch(game, choose_edition=lambda: variants[0],
                    choose_archive=lambda rom: '', choose_cheats=lambda *args: [],
                    status=report['status_messages'].append,
                    warning=lambda title, message: report['warnings'].append([title, message]),
                    played=library.record_played, presentation_provider=pipeline_composition().build_launch)
                report['launch'] = controller.last_result
                if not report['launch'].get('success'):
                    raise ValueError(report['launch'].get('error', 'Launch failed'))
                report['presentation'] = capture_presentation(report['launch']['command'], root)
                start = time.monotonic()
                while time.monotonic() - start < seconds and launcher.process_running():
                    time.sleep(0.1)
                report['observed_seconds'] = round(time.monotonic() - start, 3)
                report['alive_at_deadline'] = launcher.process_running()
                if not report['alive_at_deadline']:
                    raise ValueError(case['label'] + ' exited before the observation deadline.')
                report['stages'][stage] = {'passed': True}
                stage = 'stop'
                controller.stop()
                report['stop_succeeded'] = not launcher.process_running()
                if not report['stop_succeeded']:
                    raise ValueError('Owned emulator session did not stop.')
                report['stages'][stage] = {'passed': True}
                stage = 'history'
                report['after_launch'] = pipeline_snapshot(library, game)
                if report['after_launch']['recent'] != [game.local_file_id]:
                    raise ValueError('Recently Played did not persist the selected local-file identity.')
                if report['warnings']:
                    raise ValueError('Launch workflow reported warnings: ' + str(report['warnings']))
                report['stages'][stage] = {'passed': True}
                stage = 'restart'
                restarted = pipeline_restart(root, snapshot_bundle, staged_rom, platform)
                report['restart'] = restarted
                if restarted['snapshot'] != report['after_launch'] or restarted['pid'] == os.getpid():
                    raise ValueError('Fresh-process reconstruction changed Library state.')
                report['stages'][stage] = {'passed': True, 'fresh_process': True}
            finally:
                if launcher is not None:
                    try:
                        launcher.shutdown()
                        if controller is not None:
                            controller.cleanup_inputs()
                        report['shutdown_succeeded'] = True
                    except (OSError, RuntimeError) as exc:
                        report['shutdown_succeeded'] = False
                        report['cleanup_errors'].append(str(exc))
                    report['owned_group_remaining'] = launcher.process_running() or launcher._probe_running()
                    report['cleanup_errors'].extend(launcher.cleanup_errors)
                    for name in ('primary_config_runtime', 'session_config', 'core_options_runtime',
                                 'overlay_runtime', 'shader_runtime', 'contain_runtime',
                                 'adaptive_bezel_runtime', 'cheat_runtime', 'content_display_aspect_probe'):
                        owner = getattr(launcher, name)
                        directory = getattr(owner, 'directory', getattr(owner, 'runtime_root', None))
                        if directory is not None:
                            report['remaining_transients'].extend(str(path.relative_to(root))
                                for path in Path(directory).rglob('*') if path.is_file())
    except (OSError, ValueError, RuntimeError, RVDBError, subprocess.SubprocessError) as exc:
        report['error'] = str(exc)
        report['stages'][stage] = {'passed': False, 'error': str(exc)}
    finally:
        changed = []
        for path, checksum in protected.items():
            try:
                if digest(path) != checksum:
                    changed.append(path)
            except OSError:
                changed.append(path)
        unexpected = (sorted({str(path) for path in user_directory.glob('*.json')} - user_files_before)
                      if user_directory is not None else [])
        report['changed_protected_files'] = changed
        report['unexpected_user_files'] = unexpected
        report['source_unchanged'] = not changed and not unexpected
        report['stages']['preservation'] = {'passed': report['source_unchanged']}
        report['stages']['cleanup'] = {'passed': bool(report.get('shutdown_succeeded'))
            and not report['owned_group_remaining'] and not report['remaining_transients'] and not report['cleanup_errors']}
        report['pipeline_passed'] = (not report.get('error') and 'restart' in report['stages']
                                     and all(item['passed'] for item in report['stages'].values()))
        (root / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--platform', choices=PLATFORMS)
    parser.add_argument('--rom', required=True)
    parser.add_argument('--output')
    parser.add_argument('--seconds', type=float, default=10)
    parser.add_argument('--via-controller', action='store_true', help='Exercise the shared UI launch workflow.')
    parser.add_argument('--pipeline', action='store_true', help='Qualify a complete NES, SNES or Genesis Library/persistence/restart path.')
    parser.add_argument('--visual-tuning-json', type=json.loads, help='Isolated pipeline CRT adjustments as JSON.')
    parser.add_argument('--restart-profile', help=argparse.SUPPRESS)
    parser.add_argument('--bundle', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.restart_profile:
        if not args.bundle:
            parser.error('--restart-profile requires --bundle')
        with pipeline_environment(args.restart_profile):
            library, game, _ = pipeline_library(args.bundle, args.rom, args.platform or "nes")
            print(json.dumps({'pid': os.getpid(), 'snapshot': pipeline_snapshot(library, game)}))
        return 0
    if not args.platform or not args.output:
        parser.error('--platform and --output are required')
    report = qualify(args.platform, args.rom, args.output, args.seconds, via_controller=args.via_controller, pipeline=args.pipeline, visual_tuning=args.visual_tuning_json)
    print(json.dumps(report, indent=2))
    if args.pipeline:
        return 0 if report.get('pipeline_passed') else 1
    return 0 if (report.get('alive_at_deadline') and report.get('stop_succeeded')
                 and report.get('shutdown_succeeded') and report['source_unchanged']
                 and not report['owned_group_remaining'] and not report['remaining_transients']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
