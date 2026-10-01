"""Isolated startup contracts: no user settings, ROM corpus or emulator needed."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest
import yaml

from config import ConfigLoader, ConfigWriter
from config.paths import APP_ROOT, RVDB_BUNDLE, cache_home, config_home, data_home
from config.validation import validate_config
from services.startup import check_startup


@pytest.mark.parametrize('value', ['', 'relative/root'])
def test_empty_or_relative_xdg_uses_home_not_cwd(tmp_path, monkeypatch, value):
    monkeypatch.setenv('HOME', str(tmp_path))
    for name in ('XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_DATA_HOME'):
        monkeypatch.setenv(name, value)
    monkeypatch.chdir('/')
    assert config_home() == tmp_path / '.config'
    assert cache_home() == tmp_path / '.cache'
    assert data_home() == tmp_path / '.local/share'


def test_all_active_runtime_owners_share_isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_CACHE_HOME', str(tmp_path))
    from services.retroarch.archive_runtime import ArchiveRuntime
    from services.retroarch.cheat_runtime import CheatRuntimeConfig
    from services.retroarch.content_display_aspect_probe import ContentLoadedDisplayAspectProbe
    from services.retroarch.primary_config_runtime import PrimaryConfigRuntime
    from services.retroarch.overlay_runtime import OverlayRuntimeConfig
    from services.retroarch.shader_runtime import ShaderRuntimeConfig
    from services.retroarch.session_config import RetroArchSessionConfig
    from services.retroarch.core_options_runtime import CoreOptionsRuntimeConfig
    from services.retroarch.contain_runtime import ContainRuntimeConfig
    from services.retroarch.adaptive_bezel_runtime import AdaptiveBezelRuntime
    from services.library.archive_scan_cache import ArchiveScanCache
    paths = [ArchiveRuntime().cache_root, CheatRuntimeConfig().runtime_root,
             ContentLoadedDisplayAspectProbe().directory, PrimaryConfigRuntime().directory,
             OverlayRuntimeConfig().directory, ShaderRuntimeConfig().directory,
             RetroArchSessionConfig().directory, CoreOptionsRuntimeConfig().directory,
             ContainRuntimeConfig().directory, AdaptiveBezelRuntime().directory,
             ArchiveScanCache().path]
    assert all(path.is_relative_to(tmp_path / 'retrovault') for path in paths)
    assert list(tmp_path.iterdir()) == []


def test_persistent_store_locations_stay_separate_from_cache(tmp_path, monkeypatch):
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / 'config'))
    monkeypatch.setenv('XDG_CACHE_HOME', str(tmp_path / 'cache'))
    from services.library.state import LibraryState
    from services.library.collections import CollectionStore
    from services.presentation.store import PresentationStore
    assert LibraryState().state_file == tmp_path / 'config/retrovault/library-state.json'
    assert CollectionStore().collections_file == tmp_path / 'config/retrovault/collections.json'
    assert PresentationStore().presentation_file == tmp_path / 'config/retrovault/presentation-state.json'
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('data,field', [
    ({'retroarch': None}, 'retroarch'),
    ({'retroarch': {'cores': []}}, 'retroarch.cores'),
    ({'paths': {'overlays': {'directory': False}}}, 'paths.overlays.directory'),
    ({'paths': {'shaders': {'directory': 'relative'}}}, 'paths.shaders.directory'),
    ({'library': {'sources': 'bad'}}, 'library.sources'),
    ({'library': {'sources': [{'id': 'missing-fields'}]}}, 'library.sources'),
])
def test_invalid_nested_config_fails_before_consumers(data, field):
    with pytest.raises(ValueError, match=field):
        validate_config(data)


def test_source_booleans_and_unique_ids_are_strict():
    source = dict(id='one', name='One', enabled=True, type='local', path='/roms')
    with pytest.raises(ValueError, match='duplicates'):
        validate_config({'library': {'sources': [source, source]}})
    with pytest.raises(ValueError, match='boolean'):
        validate_config({'library': {'sources': [dict(source, enabled='false')]}})


def test_loader_preserves_unknown_extension_keys_and_list_replacement(tmp_path):
    defaults = tmp_path / 'defaults.yaml'
    defaults.write_text(yaml.safe_dump({'library': {'sources': []}, 'plugin': {'a': 1}}))
    runtime = tmp_path / 'runtime.json'
    runtime.write_text(json.dumps({'plugin': {'b': 2}}))
    assert ConfigLoader(defaults, runtime).load()['plugin'] == {'a': 1, 'b': 2}


def test_writer_failure_preserves_original_and_cleans_unique_temporary(tmp_path, monkeypatch):
    runtime = tmp_path / 'runtime.json'
    original = '{"extension": "preserve"}'
    runtime.write_text(original)
    def fail(*args):
        raise OSError('write denied')
    monkeypatch.setattr('config.writer.os.replace', fail)
    with pytest.raises(OSError, match='denied'):
        ConfigWriter(runtime).update({'retroarch': {'executable': 'retroarch'}})
    assert runtime.read_text() == original
    assert list(tmp_path.iterdir()) == [runtime]


def test_preflight_is_read_only_and_cwd_independent(tmp_path, monkeypatch):
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.setenv('XDG_CONFIG_HOME', str(tmp_path / 'config'))
    monkeypatch.setenv('XDG_CACHE_HOME', str(tmp_path / 'cache'))
    monkeypatch.setenv('PATH', '')
    reports = []
    for cwd in (APP_ROOT, tmp_path):
        monkeypatch.chdir(cwd)
        reports.append(check_startup())
    assert reports[0] == reports[1]
    assert reports[0].bundle_available
    assert reports[0].config['library']['sources'] == []
    assert reports[0].config['retroarch']['cores']['directory'] == ''
    assert list(tmp_path.iterdir()) == []


def test_invalid_configuration_diagnostic_preserves_file(tmp_path):
    runtime = tmp_path / 'runtime.json'
    runtime.write_text('{bad json')
    before = runtime.read_bytes()
    report = check_startup(ConfigLoader(runtime_file=runtime))
    assert report.errors and str(runtime) in report.errors[0]
    assert runtime.read_bytes() == before
    assert list(tmp_path.iterdir()) == [runtime]


def test_missing_bundle_disables_scan_without_fabricating_knowledge(tmp_path):
    report = check_startup(ConfigLoader(runtime_file=tmp_path / 'absent.json'),
                           bundle_path=tmp_path / 'absent-bundle.json')
    assert not report.bundle_available
    assert any('Library scanning is disabled' in value for value in report.warnings)
    assert list(tmp_path.iterdir()) == []


def test_disabled_library_controller_never_loads_or_imports(monkeypatch):
    from unittest.mock import Mock
    from controllers.library_controller import LibraryController
    library = Mock()
    monkeypatch.setattr('controllers.library_controller.LibraryService', lambda **kwargs: library)
    controller = LibraryController(library_enabled=False, bulk_importer=Mock(), import_source_store=Mock())
    library.load.assert_not_called()
    with pytest.raises(ValueError, match='RVDB unavailable'):
        controller.reload_sources()
    with pytest.raises(ValueError, match='RVDB unavailable'):
        controller.bulk_import('/roms')
    library.load.assert_not_called()


def test_explicit_primary_source_wins_over_automatic_discovery(tmp_path, monkeypatch):
    primary = tmp_path / 'chosen.cfg'
    primary.write_text('video_driver = "gl"\n')
    runtime = tmp_path / 'runtime.json'
    runtime.write_text(json.dumps({'retroarch': {'primary_config': str(primary)}}))
    report = check_startup(ConfigLoader(runtime_file=runtime))
    assert report.paths['primary_config'] == str(primary)


@pytest.mark.parametrize('bundle_available', [True, False])
def test_real_empty_startup_from_other_directory(tmp_path, bundle_available):
    # Run real MainWindow construction in a fresh process, with no user sources,
    # executable or cache. Missing-bundle setup must not trigger a scan/migration.
    code = '''
from pathlib import Path
from PyQt6.QtWidgets import QApplication
import ui.main_window as ui
from services.library.scanner import RomScanner
from config import ConfigLoader
app = QApplication([])
assert ConfigLoader().load()['library']['sources'] == []
def forbidden(*args, **kwargs):
    raise AssertionError('fresh setup must not scan')
RomScanner.scan = forbidden
BUNDLE_OVERRIDE
window = ui.MainWindow()
window.showMaximized()
app.processEvents()
assert window.isVisible()
assert window.shutdown_runtime()
window.close()
'''.replace('BUNDLE_OVERRIDE', '' if bundle_available else "ui.RVDB_BUNDLE = Path('/missing/rvdb.bundle.json')")
    env = dict(os.environ, HOME=str(tmp_path), XDG_CONFIG_HOME=str(tmp_path / 'config'),
               XDG_CACHE_HOME=str(tmp_path / 'cache'), XDG_DATA_HOME=str(tmp_path / 'data'),
               QT_QPA_PLATFORM='offscreen', PYTHONPATH=str(APP_ROOT), PATH='',
               PYTHONDONTWRITEBYTECODE='1')
    result = subprocess.run([sys.executable, '-c', code], cwd=tmp_path, env=env,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
