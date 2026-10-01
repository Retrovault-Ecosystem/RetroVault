"""Explicit backend selection and physical-file launch input."""
from dataclasses import dataclass
import os
from pathlib import Path
import shutil

SNES = 'platform.nintendo.snes'
RETROARCH = 'retroarch'
SNES9X = 'snes9x'
STANDALONE_NOTICE = ('Snes9x standalone uses its native display and controls. RetroArch overlays, '
                     'shaders, CRT adjustments and cheats are not applied; saved preferences are retained.')


def selected_backend(config, platform_id):
    if platform_id != SNES:
        return RETROARCH
    backend = config.get('emulation', {}).get('snes_backend', RETROARCH)
    if backend not in (RETROARCH, SNES9X):
        raise ValueError(f'Unsupported SNES backend: {backend}')
    return backend


def executable_path(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Configure the Snes9x GTK executable in Settings.')
    expanded = os.path.expanduser(value.strip())
    if '/' in expanded and not Path(expanded).is_absolute():
        raise ValueError('Snes9x executable must be an absolute path or a command on PATH.')
    resolved = shutil.which(expanded)
    if not resolved or not Path(resolved).is_file():
        raise ValueError('Snes9x GTK executable is unavailable or not executable.')
    return str(Path(resolved).absolute())


@dataclass(frozen=True)
class StandaloneRequest:
    game: str
    rom: str
    platform_id: str
    local_file_id: str
    executable: str
