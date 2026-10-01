"""Real source scan, identity, stores and subprocess restart; emulator execution is replaced."""
import itertools
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from config import ConfigWriter
from config.paths import config_home
from scripts import qualify_retroarch_runtime as qualification
from services.presentation.production_package_resolver import CanonicalProductionPackageResolver
from services.retroarch.core_resolver import core_suffix


class EmulatorDouble:
    fail = False

    def __init__(self, executable, **kwargs):
        self.command = executable
        self.active_process = None
        self.cleanup_errors = []
        self.directory = Path(os.environ['XDG_CACHE_HOME']) / 'test-runtime'
        for name in ('primary_config_runtime', 'session_config', 'core_options_runtime',
                     'overlay_runtime', 'shader_runtime', 'contain_runtime',
                     'adaptive_bezel_runtime', 'cheat_runtime', 'content_display_aspect_probe'):
            setattr(self, name, SimpleNamespace(directory=self.directory))

    def process_running(self):
        return self.active_process is not None

    def _probe_running(self):
        return False

    def launch(self, profile):
        if self.fail:
            return {'success': False, 'error': 'Injected spawn failure'}
        self.directory.mkdir(parents=True, exist_ok=True)
        config = self.directory / 'test.cfg'
        config.write_text('input_overlay_enable = "false"\n')
        self.active_process = object()
        return {'success': True, 'command': [self.command, '--config', str(config)]}

    def stop(self):
        self.active_process = None
        return True

    def clear_exited_process(self):
        self.active_process = None

    def shutdown(self):
        self.stop()
        for path in self.directory.glob('*'):
            path.unlink()
        return True


CASES = {
    'nes': ('fceumm', ['nes'], ['core.mesen']),
    'snes': ('snes9x', ['sfc', 'smc'], ['core.bsnes', 'core.snes9x']),
    'genesis': ('genesis_plus_gx', ['md', 'gen'], ['core.genesis.plus.gx']),
}


@pytest.fixture(params=[('nes', 'nes'), ('snes', 'sfc'), ('snes', 'smc'),
                        ('genesis', 'md'), ('genesis', 'gen')],
                ids=['nes', 'snes-sfc', 'snes-smc', 'genesis-md', 'genesis-gen'])
def environment(tmp_path, monkeypatch, request):
    import config.paths
    original_profile = tmp_path / 'user-profile'
    monkeypatch.setenv('XDG_CONFIG_HOME', str(original_profile))
    monkeypatch.setenv('XDG_CACHE_HOME', str(tmp_path / 'user-cache'))
    monkeypatch.setenv('XDG_DATA_HOME', str(tmp_path / 'user-data'))
    bundle = tmp_path / 'bundle.json'
    platform, extension = request.param
    core_identity, _, supported_cores = CASES[platform]
    platform_id = qualification.PLATFORMS[platform]
    nodes, edges = {}, {}
    for slug, (_, extensions, cores) in CASES.items():
        identity = qualification.PLATFORMS[slug]
        nodes[identity] = dict(id=identity, type='platform', name=slug, extensions=extensions)
        edges[identity] = {'supports_core': cores}
        for core_id in cores:
            nodes[core_id] = dict(id=core_id, type='core', name=core_id)
    bundle.write_text(json.dumps({'nodes': nodes, 'edges': edges}))
    monkeypatch.setattr(config.paths, 'RVDB_BUNDLE', bundle)
    executable = tmp_path / 'retroarch'
    executable.write_text('#!/bin/sh\nexit 0\n')
    executable.chmod(0o755)
    core = tmp_path / 'cores' / (core_identity + '_libretro' + core_suffix())
    core.parent.mkdir()
    for identity, _, _ in CASES.values():
        (core.parent / (identity + '_libretro' + core_suffix())).write_bytes(b'core fixture, never loaded')
    primary = tmp_path / 'retroarch.cfg'
    primary.write_text('config_save_on_exit = "true"\n')
    resources = tmp_path / 'assets'
    settings = {'retroarch': {'executable': str(executable), 'primary_config': str(primary),
                              'cores': {'directory': str(core.parent)}},
                'library': {'sources': []},
                'paths': {kind: {'directory': str(resources / kind)}
                          for kind in ('overlays', 'shaders', 'artwork')}}
    for identity in qualification.PLATFORMS.values():
        assets = CanonicalProductionPackageResolver._ASSETS[identity]
        fixture_overlay = resources / 'overlays' / assets.overlay
        shader = resources / 'shaders' / assets.shader
        for path in (fixture_overlay, shader):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('# fixture\n')
        fixture_overlay.with_suffix('.runtime.cfg').write_text('# fixture\n')
        fixture_overlay.with_suffix('.production.json').write_text(json.dumps({'platform_id': identity}))
    overlay = resources / 'overlays' / CanonicalProductionPackageResolver._ASSETS[platform_id].overlay
    ConfigWriter().write(settings)
    rom = tmp_path / ('Unknown Game (USA).' + extension)
    rom.write_bytes(b'synthetic scan fixture, never executed')
    ticks = itertools.count()
    monkeypatch.setattr(qualification, 'time', SimpleNamespace(monotonic=lambda: next(ticks), sleep=lambda _: None))
    monkeypatch.setattr(qualification, 'RetroArchLauncher', EmulatorDouble)
    monkeypatch.setattr(EmulatorDouble, 'fail', False)
    return SimpleNamespace(platform=platform, platform_id=platform_id, extension=extension,
                           core_identity=core_identity, supported_cores=supported_cores,
                           case=qualification.pipeline_case(platform), root=tmp_path / 'run', rom=rom, bundle=bundle, core=core,
                           overlay=overlay, primary=primary, profile=original_profile,
                           user_config=config_home() / 'retrovault/runtime.json')


def run(env):
    return qualification._qualify_pipeline(env.rom, env.root, 1, platform=env.platform)


def test_real_scan_persistence_and_fresh_process_restart(environment):
    env = environment
    original = env.user_config.read_bytes()
    report = run(env)
    assert report['pipeline_passed'], report
    assert report['restart']['pid'] != os.getpid()
    before, after = report['before_launch'], report['restart']['snapshot']
    assert before['recent'] == []
    assert after['recent'] == [after['local_file_id']]
    assert after['local_file_id'].startswith('local-file:')
    assert after['local_file_id'] == before['local_file_id']
    assert after['favorite']
    assert after['collections'] == [environment.case['collection']]
    assert after['saved_overlay'] == env.case['preference']
    assert after['presentation_authority'] == 'production package'
    assert after['platform_id'] == env.platform_id
    assert '/' + env.platform + '/' in after['selected_overlay']
    assert after['rvdb_game_id'] == ''  # No invented canonical title.
    assert set(report['rvdb_supported_cores']) == set(env.supported_cores)
    assert Path(report['core']).name == env.core_identity + '_libretro' + core_suffix()
    assert env.user_config.read_bytes() == original
    assert os.environ['XDG_CONFIG_HOME'] == str(env.profile)
    assert not report['remaining_transients']


@pytest.mark.parametrize('failure,stage', [('bundle', 'library_discovery'),
    ('rom', 'setup'), ('core', 'core_readiness'), ('package', 'presentation'), ('spawn', 'launch')])
def test_pipeline_failure_is_stage_specific_and_preserves_profile(environment, monkeypatch, failure, stage):
    env = environment
    original = env.user_config.read_bytes()
    if failure == 'bundle':
        env.bundle.write_text('{broken')
    elif failure == 'rom':
        env.rom.unlink()
    elif failure == 'core':
        env.core.unlink()
    elif failure == 'package':
        env.overlay.unlink()
    else:
        monkeypatch.setattr(EmulatorDouble, 'fail', True)
    report = run(env)
    assert not report['pipeline_passed']
    assert report['stages'][stage]['passed'] is False
    assert env.user_config.read_bytes() == original
    assert os.environ['XDG_CONFIG_HOME'] == str(env.profile)
    assert not report['owned_group_remaining']
    state_file = env.root / 'profile/retrovault/library-state.json'
    if state_file.exists():
        assert json.loads(state_file.read_text()).get('recent', []) == []


def test_cancelled_launch_does_not_persist_recent(environment, monkeypatch):
    from controllers.game_launch_controller import GameLaunchController
    launch = GameLaunchController.launch
    def cancel(self, game, **kwargs):
        kwargs['choose_edition'] = lambda: None
        return launch(self, game, **kwargs)
    monkeypatch.setattr(GameLaunchController, 'launch', cancel)
    report = run(environment)
    assert not report['pipeline_passed']
    assert report['stages']['launch']['passed'] is False
    state = json.loads((environment.root / 'profile/retrovault/library-state.json').read_text())
    assert state['recent'] == []


def test_history_write_failure_does_not_reset_favorite(environment, monkeypatch):
    from services.library.state import LibraryState
    def denied(*args):
        raise PermissionError('History is read-only')
    monkeypatch.setattr(LibraryState, 'record_played', denied)
    report = run(environment)
    assert not report['pipeline_passed']
    assert report['stages']['history']['passed'] is False
    assert report['after_launch']['favorite']
    assert report['after_launch']['recent'] == []
    assert report['warnings']
    assert report['shutdown_succeeded']


def test_disappearing_source_cannot_pass_restart(environment, monkeypatch):
    restart = qualification.pipeline_restart
    def remove(root, bundle, rom, platform="nes"):
        Path(rom).unlink()
        return restart(root, bundle, rom, platform)
    monkeypatch.setattr(qualification, 'pipeline_restart', remove)
    report = run(environment)
    assert not report['pipeline_passed']
    assert report['stages']['restart']['passed'] is False
    assert environment.rom.exists()
    assert report['shutdown_succeeded']


def test_refresh_and_second_reconstruction_keep_one_identity(environment):
    from services.library.identity import game_identity
    env = environment
    report = run(env)
    assert report['pipeline_passed'], report
    with qualification.pipeline_environment(env.root):
        library, game, _ = qualification.pipeline_library(env.root / 'rvdb.bundle.json', report['rom'], env.platform)
        identity = game_identity(game)
        library.reload_sources()
        assert len(library.get_games()) == 1
        assert game_identity(library.get_games()[0]) == identity
        assert qualification.pipeline_snapshot(library, library.get_games()[0]) == report['after_launch']


def test_library_and_playlists_share_persisted_platform_presentation(environment, monkeypatch):
    from PyQt6.QtWidgets import QApplication, QMessageBox
    from ui.library.details.game_details import GameDetails
    import ui.main_window as main
    app = QApplication.instance() or QApplication([])
    env = environment
    report = run(env)
    assert report['pipeline_passed'], report
    monkeypatch.setattr(main, 'RVDB_BUNDLE', env.root / 'rvdb.bundle.json')
    monkeypatch.setattr(main, 'RetroArchLauncher', EmulatorDouble)
    monkeypatch.setattr(GameDetails, '_select_cheats', lambda *args: [])
    monkeypatch.setattr(QMessageBox, 'warning', lambda *args: QMessageBox.StandardButton.Ok)
    with qualification.pipeline_environment(env.root):
        window = main.MainWindow()
        try:
            library_page = window.pages.pages['Library']
            playlists_page = window.pages.pages['Playlists']
            assert playlists_page.details.presentation_store is library_page.details.presentation_store
            assert playlists_page.details.presentation_resolver_provider == library_page.details.presentation_resolver_provider
            game = playlists_page.controller.get_games()[0]
            for details in (library_page.details, playlists_page.details):
                details.show_game(game)
                details.launch_game()
                assert window.game_launch_controller.last_result['success']
                details.stop_game()
                window._poll_process_lifecycle()
                assert window.process_lifecycle.state.name == 'IDLE'
            assert playlists_page.controller.recent() == [game.local_file_id]
            assert game.favorite
            assert len(playlists_page.controller.collection_games(environment.case['collection'])) == 1
        finally:
            window.close()
            app.processEvents()


def test_unexpected_user_profile_write_fails_preservation(environment, monkeypatch):
    launch = EmulatorDouble.launch
    def stray_write(self, profile):
        (environment.user_config.parent / 'unexpected.json').write_text('{}')
        return launch(self, profile)
    monkeypatch.setattr(EmulatorDouble, 'launch', stray_write)
    report = run(environment)
    assert not report['pipeline_passed']
    assert not report['stages']['preservation']['passed']
    assert report['unexpected_user_files'] == [str(environment.user_config.parent / 'unexpected.json')]


def test_mixed_platform_library_keeps_identity_state_and_packages_separate(environment):
    from services.library.import_sources import ImportSourceStore
    from services.library.presentation_studio import LibraryPresentationStudioService
    from services.presentation.store import PresentationStore
    env = environment
    settings = json.loads(env.user_config.read_text())
    env.root.mkdir()
    source = env.root / 'mixed-roms'
    source.mkdir()
    roms = {}
    # Same title and bytes must not collapse distinct physical/platform identities.
    for slug, extension in [('nes', 'nes'), ('snes', 'sfc'), ('genesis', 'md')]:
        roms[slug] = source / ('Shared Game (USA).' + extension)
        roms[slug].write_bytes(b'identical synthetic content')
    with qualification.pipeline_environment(env.root):
        ConfigWriter().write(settings)
        ImportSourceStore().persist_directory(source)
        library, chosen, _ = qualification.pipeline_library(env.bundle, roms[env.platform], env.platform)
        assert len(library.get_games()) == 3
        assert len({game.local_file_id for game in library.get_games()}) == 3
        library.set_favorite(chosen, True)
        library.create_collection('Selected platform')
        library.add_to_collection('Selected platform', chosen)
        library.record_played(chosen)
        LibraryPresentationStudioService(PresentationStore()).assign(
            'overlay', 'game', env.case['preference'], chosen)
        for slug, rom in roms.items():
            restored, game, _ = qualification.pipeline_library(env.bundle, rom, slug)
            selected = slug == env.platform
            snapshot = qualification.pipeline_snapshot(restored, game)
            assert snapshot['favorite'] is selected
            assert snapshot['collections'] == (['Selected platform'] if selected else [])
            assert snapshot['saved_overlay'] == (env.case['preference'] if selected else '')
            assert '/' + slug + '/' in snapshot['selected_overlay']
            assert '/' + slug + '/' in snapshot['selected_shader']
            assert restored.platform_statistics(game.rvdb_platform_id)['recent'] == int(selected)
            restarted = qualification.pipeline_restart(env.root, env.bundle, rom, slug)
            assert restarted['snapshot'] == snapshot


@pytest.mark.parametrize('extension', ['bin', 'zip', 'foreign'])
def test_wrong_or_ambiguous_content_cannot_pass_as_requested_platform(environment, extension):
    env = environment
    if extension == 'foreign':
        extension = 'md' if env.platform != 'genesis' else 'nes'
    renamed = env.rom.with_suffix('.' + extension)
    env.rom.rename(renamed)
    env.rom = renamed
    report = run(env)
    assert not report['pipeline_passed']
    assert 'launch' not in report['stages']
    assert not report['owned_group_remaining']


def test_incompatible_installed_core_cannot_pass_readiness(environment, monkeypatch):
    original = qualification.pipeline_library
    def incompatible(bundle, rom, platform='nes'):
        library, game, resolver = original(bundle, rom, platform)
        game.core = 'snes9x' if platform != 'snes' else 'genesis_plus_gx'
        return library, game, resolver
    monkeypatch.setattr(qualification, 'pipeline_library', incompatible)
    report = run(environment)
    assert not report['pipeline_passed']
    assert report['stages']['core_readiness']['passed'] is False
    assert 'not eligible' in report['error']
    assert 'launch' not in report['stages']


def test_foreign_platform_package_cannot_pass_presentation(environment):
    env = environment
    other = 'platform.nintendo.snes' if env.platform != 'snes' else 'platform.sega.genesis'
    env.overlay.with_suffix('.production.json').write_text(json.dumps({'platform_id': other}))
    report = run(env)
    assert not report['pipeline_passed']
    assert report['stages']['presentation']['passed'] is False
    assert 'launch' not in report['stages']


def test_crt_tuning_reaches_launch_and_fresh_restart(environment, monkeypatch):
    captured=[]
    original=EmulatorDouble.launch
    def launch(self,profile):
        captured.append(dict(profile.visual_tuning))
        return original(self,profile)
    monkeypatch.setattr(EmulatorDouble,'launch',launch)
    report=qualification._qualify_pipeline(environment.rom,environment.root,1,
        platform=environment.platform,visual_tuning={'brightness':1.25})
    assert report['pipeline_passed'],report
    assert captured==[{'brightness':1.25}]
    assert report['restart']['snapshot']['visual_tuning']=={'brightness':1.25}
