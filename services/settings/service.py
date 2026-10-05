"""Application settings validation and persistence, independent of Qt."""
from dataclasses import dataclass
import os
from pathlib import Path
import shutil
import subprocess

from config import ConfigLoader, ConfigWriter
from services.library.import_sources import ImportSourceStore
from services.retroarch.core_resolver import CoreResolver


@dataclass(frozen=True)
class SettingsSaveResult:
    config: dict
    sources_changed: bool
    restart_required: bool
    refresh_error: str = ''

    @property
    def message(self):
        message = ('Settings saved. Restart RetroVault to use the new executable.'
                   if self.restart_required else
                   'Settings saved. Primary configuration, core and presentation paths apply on the next launch.')
        if self.refresh_error:
            message += f' Unable to refresh saved settings: {self.refresh_error}'
        return message


class SettingsService:
    def __init__(self, config_loader=None, config_writer=None):
        self.config_loader = config_loader or ConfigLoader()
        self.config_writer = config_writer or ConfigWriter(runtime_file=self.config_loader.runtime_file)
        self.startup_executable = self.config_loader.load().get('retroarch', {}).get('executable', '')
        self.sources = ImportSourceStore(config_loader=self.config_loader, config_writer=self.config_writer)

    @staticmethod
    def expanded_path(value):
        return Path(value).expanduser() if value else None

    @staticmethod
    def readable_directory(value):
        path = SettingsService.expanded_path(value)
        return bool(path is not None and path.is_dir() and os.access(path, os.R_OK))

    @staticmethod
    def contains_core(value):
        return CoreResolver.contains_core(value)

    @staticmethod
    def is_retroarch_executable(value):
        resolved = shutil.which(os.path.expanduser(value)) if value else None
        path = Path(resolved) if resolved else SettingsService.expanded_path(value)
        if path is None or not path.is_file() or not os.access(path, os.X_OK):
            return False
        try:
            result = subprocess.run([str(path), '--version'], capture_output=True,
                                    text=True, timeout=3, check=False)
        except (OSError, subprocess.SubprocessError):
            return False
        output = (result.stdout + '\n' + result.stderr).lower()
        return 'retroarch' in output and 'libretro' in output

    def validate(self, values):
        errors = {}
        if not self.is_retroarch_executable(values['executable']):
            errors['executable'] = 'RetroArch executable is invalid'
        if values['core_directory'] and not self.contains_core(values['core_directory']):
            errors['core_directory'] = 'RetroArch core directory is invalid'
        if values['library_path'] and not self.readable_directory(values['library_path']):
            errors['library_path'] = 'Library path is not a readable directory'
        if values['overlay_directory'] and not self.readable_directory(values['overlay_directory']):
            errors['overlay_directory'] = 'Overlay path is not a readable directory'
        primary = values['primary_config']
        if primary and not Path(primary).expanduser().is_file():
            errors['primary_config'] = 'RetroArch primary configuration does not exist'
        return errors

    def save(self, values):
        errors = self.validate(values)
        if errors:
            raise ValueError(next(iter(errors.values())))
        config = self.config_loader.load()
        sources = config.get('library', {}).get('sources', [])
        updated = [dict(source) for source in sources]
        index = next((i for i, source in enumerate(updated) if source.get('enabled', False)),
                     0 if updated else None)
        if values['library_path']:
            if index is None:
                updated.append(dict(id='local', name='Local Library', enabled=True,
                                    type='local', path=values['library_path']))
            else:
                updated[index]['path'] = values['library_path']
        overrides = {
            'retroarch': {'executable': values['executable'], 'primary_config': values['primary_config'],
                          'cores': {'directory': values['core_directory']}},
            'library': {'sources': updated},
            'paths': {'artwork': {'directory': values['artwork_directory']},
                      'overlays': {'directory': values['overlay_directory']}}}
        self.config_writer.update(overrides)
        refresh_error = ''
        try:
            effective = self.config_loader.load()
        except (OSError, ValueError) as exc:
            # A completed write must never be described as a failed save.
            from config.loader import _merge_config
            effective = _merge_config(config, overrides)
            refresh_error = str(exc)
        return SettingsSaveResult(effective, sources != updated,
                                  values['executable'] != self.startup_executable, refresh_error)

    def save_standalone(self, backend, executable):
        from config.validation import validate_config
        from services.emulators.models import executable_path
        values = {'snes_backend': backend, 'snes9x_executable': executable.strip()}
        validate_config({'emulation': values})
        if backend == 'snes9x':
            executable_path(values['snes9x_executable'])
            import sys
            if sys.platform != 'linux':
                raise ValueError('The Snes9x GTK adapter currently supports native Linux only.')
        config = self.config_loader.load()
        overrides = {'emulation': values}
        self.config_writer.update(overrides)
        refresh_error = ''
        try:
            effective = self.config_loader.load()
        except (OSError, ValueError) as exc:
            from config.loader import _merge_config
            effective = _merge_config(config, overrides)
            refresh_error = str(exc)
        return SettingsSaveResult(effective, False, False, refresh_error)
