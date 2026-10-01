"""Read-only startup preflight. Never scans ROMs, creates stores or launches tools."""
from dataclasses import dataclass, field
import hashlib
import os
from pathlib import Path
import shutil

from config import ConfigLoader
from config.paths import RVDB_BUNDLE, config_home, cache_home
from services.rvdb import RVDBService, RVDBError
from services.retroarch.primary_config_runtime import PrimaryConfigRuntime


@dataclass
class StartupReport:
    config: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    paths: dict = field(default_factory=dict)
    bundle_sha256: str = ''
    bundle_available: bool = False


def check_startup(loader=None, bundle_path=None):
    loader = loader or ConfigLoader()
    bundle = Path(bundle_path or RVDB_BUNDLE)
    report = StartupReport(paths={'defaults': str(loader.default_file),
                                  'overrides': str(loader.runtime_file),
                                  'bundle': str(bundle), 'config_home': str(config_home()),
                                  'cache_home': str(cache_home())})
    for key in ('XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_DATA_HOME'):
        value = os.environ.get(key, '').strip()
        if value and not Path(value).expanduser().is_absolute():
            report.warnings.append(f'{key} is relative; using the home-directory fallback.')
    try:
        report.config = loader.load()
    except (OSError, ValueError) as exc:
        report.errors.append(str(exc))
        return report
    try:
        RVDBService.from_bundle(bundle)
        report.bundle_available = True
        report.bundle_sha256 = hashlib.sha256(bundle.read_bytes()).hexdigest()
    except (RVDBError, OSError) as exc:
        report.warnings.append(f'{exc}. Install a validated RVDB bundle and restart; Library scanning is disabled.')
    from services.emulators.models import selected_backend, executable_path, SNES, SNES9X
    if selected_backend(report.config, SNES) == SNES9X:
        try:
            report.paths['snes9x_executable'] = executable_path(
                report.config.get('emulation', {}).get('snes9x_executable', ''))
        except ValueError as exc:
            report.warnings.append(f'Selected SNES standalone backend unavailable: {exc}')
    retroarch = report.config.get('retroarch', {})
    executable = os.path.expanduser(retroarch.get('executable', ''))
    resolved = shutil.which(executable) if executable else None
    report.paths['executable'] = resolved or executable
    if not resolved:
        report.warnings.append('RetroArch executable is unavailable; configure it in Settings before launching.')
    cores = retroarch.get('cores', {}).get('directory', '')
    if not cores or not Path(cores).expanduser().is_dir():
        report.warnings.append('Core directory is unavailable; configure it in Settings before launching.')
    try:
        primary = PrimaryConfigRuntime().discover_source(retroarch.get('primary_config') or None)
        report.paths['primary_config'] = str(primary) if primary else ''
        if primary is None:
            report.warnings.append('No RetroArch primary configuration found; select one in Settings before production launch.')
    except (OSError, ValueError) as exc:
        report.warnings.append(str(exc))
    return report
