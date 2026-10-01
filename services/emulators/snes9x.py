"""Native Linux Snes9x GTK adapter, independent of RetroArch launch artifacts."""
import configparser
import hashlib
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

from config.paths import RVDB_BUNDLE, config_home, data_home, runtime_directory
from services.rvdb import RVDBService, RVDBError
from services.retroarch.process_group import group_exists
from .models import SNES, executable_path


class Snes9xLauncher:
    # Snes9x GTK 1.63 emits this via GLib only after LoadROM succeeds.
    ROM_LOADED = 'Using rewind buffer of '

    def __init__(self, *, rvdb_service=None, startup_timeout=8.0):
        self.rvdb_service = rvdb_service
        self.startup_timeout = startup_timeout
        self._process = None
        self._group = None
        self.last_result = {}

    @property
    def active_process(self):
        return self._process

    def process_running(self):
        return bool(self._process is not None and
                    (self._process.poll() is None or group_exists(self._group)))

    def clear_exited_process(self):
        if not self.process_running():
            self._process = None
            self._group = None

    def validate(self, request):
        if sys.platform != 'linux':
            raise ValueError('The Snes9x GTK adapter currently supports native Linux only.')
        if request.platform_id != SNES:
            raise ValueError('Snes9x standalone is registered for canonical SNES games only.')
        try:
            service = self.rvdb_service or RVDBService.from_bundle(RVDB_BUNDLE)
            view = service.platform_view(request.platform_id)
        except RVDBError as exc:
            raise ValueError(f'RVDB compatibility is unavailable: {exc}') from exc
        if view is None or not any(e.id == 'emulator.snes9x' for e in view.emulators):
            raise ValueError('RVDB does not identify Snes9x as compatible with this platform.')
        rom = Path(request.rom).expanduser().resolve()
        if rom.suffix.lower() not in ('.sfc', '.smc'):
            raise ValueError('Snes9x standalone requires a loose .sfc or .smc file; archives are unsupported.')
        if not rom.is_file() or not os.access(rom, os.R_OK) or rom.stat().st_size == 0:
            raise ValueError('The selected SNES ROM is missing, empty or unreadable.')
        return executable_path(request.executable), rom

    def prepare(self, request, rom):
        # Physical editions with identical basenames must not share native saves.
        identity = request.local_file_id or str(rom)
        key = hashlib.sha256(identity.encode('utf-8')).hexdigest()
        profile = config_home() / 'retrovault/emulators/snes9x' / key
        saves = data_home() / 'retrovault/emulators/snes9x' / key
        cache = runtime_directory('snes9x') / key
        for root in (profile / 'snes9x', saves, cache):
            root.mkdir(parents=True, exist_ok=True)
        config_path = profile / 'snes9x/snes9x.conf'
        config = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=('#',), strict=False)
        config.optionxform = str
        if config_path.exists():
            try:
                with config_path.open(encoding='utf-8') as handle:
                    config.read_file(handle)
            except configparser.Error as exc:
                raise ValueError(f'Invalid native Snes9x configuration: {config_path}') from exc
        if not config.has_section('Joypad 0'):
            config['Joypad 0'] = {button: 'Keyboard ' + key for button, key in {
                'Up': 'Up', 'Down': 'Down', 'Left': 'Left', 'Right': 'Right',
                'Start': 'Return', 'Select': 'Tab', 'A': 'x', 'B': 'z',
                'X': 's', 'Y': 'a', 'L': 'q', 'R': 'w'}.items()}
        if not config.has_section('Shortcuts'):
            config['Shortcuts'] = {'QuickSave000': 'Keyboard Shift+F1',
                                   'QuickLoad000': 'Keyboard F1',
                                   'GTK_fullscreen': 'Keyboard Alt+Return'}
        managed = {
            'Files': {key: str(saves / folder) for key, folder in (
                ('SRAMDirectory', 'sram'), ('SaveStateDirectory', 'states'),
                ('CheatDirectory', 'cheats'), ('PatchDirectory', 'patches'), ('ExportDirectory', 'exports'))},
            'Display': {'FullscreenOnOpen': 'true', 'ChangeDisplayResolution': 'false',
                        'MaintainAspectRatio': 'true', 'AspectRatio': '2'},
            'OpenGL': {'EnableCustomShaders': 'false', 'ShaderFile': ''},
            'Behavior': {'RewindBufferSize': '16'},
        }
        for folder in managed['Files'].values():
            if any(char in folder for char in '\n\r#'):
                raise ValueError('Snes9x native directory paths cannot contain newlines or #.')
            Path(folder).mkdir(parents=True, exist_ok=True)
        for section, entries in managed.items():
            if not config.has_section(section):
                config.add_section(section)
            for key, value in entries.items():
                config.set(section, key, value)
        temporary = config_path.with_suffix('.tmp')
        try:
            with temporary.open('w', encoding='utf-8') as handle:
                config.write(handle)
            os.replace(temporary, config_path)
        finally:
            temporary.unlink(missing_ok=True)
        env = dict(os.environ, XDG_CONFIG_HOME=str(profile), XDG_DATA_HOME=str(saves),
                   XDG_CACHE_HOME=str(cache), LC_ALL='C', LANGUAGE='C')
        return env, cache / 'session.log', config_path, saves

    def launch(self, request):
        if self.process_running():
            return {'success': False, 'error': 'Another Snes9x session is running.'}
        self.clear_exited_process()
        executable, rom = self.validate(request)
        env, log_path, config_path, saves = self.prepare(request, rom)
        result = {'success': False, 'backend': 'snes9x', 'rom': str(rom),
                  'config': str(config_path), 'saves': str(saves), 'log': str(log_path)}
        self.last_result = result
        try:
            with log_path.open('wb') as log:
                self._process = subprocess.Popen([executable, str(rom)], env=env, cwd=saves,
                                                 stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                                 start_new_session=True)
            self._group = self._process.pid
            deadline = time.monotonic() + self.startup_timeout
            while time.monotonic() < deadline:
                if self._process.poll() is not None:
                    break
                # A live empty GUI is not a successfully loaded game.
                if self.ROM_LOADED in log_path.read_text(encoding='utf-8', errors='replace'):
                    result['success'] = True
                    result['pid'] = self._process.pid
                    return result
                time.sleep(0.05)
            result['error'] = f'Snes9x did not confirm ROM loading. See {log_path}'
            self.stop()
            return result
        except (OSError, RuntimeError):
            if self._process is not None:
                self.stop()
            raise

    def stop(self):
        if self._process is None:
            return False
        process, group = self._process, self._group
        if type(group) is not int or group <= 1 or group == os.getpgrp():
            raise RuntimeError('Refusing to signal an unowned Snes9x process group.')
        for sig, timeout in ((signal.SIGTERM, 5.0), (signal.SIGKILL, 3.0)):
            try:
                os.killpg(group, sig)
            except ProcessLookupError:
                pass
            deadline = time.monotonic() + timeout
            while time.monotonic() < deadline:
                process.poll()
                if not group_exists(group):
                    process.wait()
                    self.clear_exited_process()
                    return True
                time.sleep(0.05)
        raise RuntimeError('Snes9x process group did not terminate; ownership retained.')

    def shutdown(self):
        self.stop()
