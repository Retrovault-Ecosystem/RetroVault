"""Explicit RetroArch edition isolation; absence preserves existing save routing."""
import hashlib
import json
from pathlib import Path

from config.paths import data_home
from services.retroarch.core_identity import canonical_libretro_core_identity
from .recovery import _publish


class SavePolicy:
    def __init__(self, root=None):
        self.root = Path(root) if root is not None else data_home() / 'retrovault/saves/retroarch'

    def directory(self, local_file_id, core):
        if not isinstance(local_file_id, str) or not local_file_id.strip():
            raise ValueError('Isolated saves require a registered physical edition.')
        identity = canonical_libretro_core_identity(core)
        key = hashlib.sha256((identity + '\0' + local_file_id).encode()).hexdigest()
        return self.root / key

    def _manifest(self, local_file_id, core, rom):
        rom = Path(rom)
        if rom.suffix.lower() not in ('.nes', '.sfc', '.smc', '.md', '.gen', '.bin'):
            raise ValueError('This save-isolation slice requires a loose cartridge file.')
        if any(char in str(rom) for char in '\n\r"'):
            raise ValueError('Unsupported character in save content path.')
        return {'version': 1, 'local_file_id': local_file_id,
                'core': canonical_libretro_core_identity(core), 'filename': rom.name}

    def settings(self, local_file_id, core, rom):
        if not local_file_id:
            return {}
        root = self.directory(local_file_id, core)
        manifest_path = root / 'policy.json'
        if not manifest_path.exists():
            return {}
        if any(p.is_symlink() for p in (manifest_path, *manifest_path.parents)):
            raise ValueError('Save policy cannot follow symbolic links.')
        expected = self._manifest(local_file_id, core, rom)
        manifest = json.loads(manifest_path.read_text())
        if not isinstance(manifest, dict):
            raise ValueError('Save policy must contain an object.')
        enabled = manifest.pop('enabled', True)
        if not isinstance(enabled, bool) or manifest != expected:
            raise ValueError('The isolated save filename or identity changed; inspect recovery before launching.')
        if not enabled:
            return {}
        for folder in ('sram', 'states'):
            if (root / folder).is_symlink() or not (root / folder).is_dir():
                raise ValueError('Isolated save directory is missing or is a symbolic link.')
        return {'savefile_directory': str(root / 'sram'),
                'savestate_directory': str(root / 'states'),
                'savefiles_in_content_dir': 'false', 'savestates_in_content_dir': 'false',
                'sort_savefiles_enable': 'false', 'sort_savestates_enable': 'false',
                'sort_savefiles_by_content_enable': 'false', 'sort_savestates_by_content_enable': 'false'}

    def enable(self, session, local_file_id, core, rom):
        """Caller confirms starting separate storage; no legacy save is copied."""
        with session.idle_file_access():
            root = self.directory(local_file_id, core)
            manifest = self._manifest(local_file_id, core, rom)
            if any(p.is_symlink() for p in (root, *root.parents)):
                raise ValueError('Save storage cannot follow symbolic links.')
            if (root / 'policy.json').exists():
                self.settings(local_file_id, core, rom)
                _publish(root / 'policy.json', json.dumps({**manifest, 'enabled': True}, sort_keys=True).encode())
                return self.settings(local_file_id, core, rom)
            for folder in ('sram', 'states'):
                destination = root / folder
                if destination.is_symlink():
                    raise ValueError('Save storage cannot follow symbolic links.')
                destination.mkdir(parents=True, exist_ok=True)
                if any(destination.iterdir()):
                    raise ValueError('Unregistered save storage is not empty; inspect before enabling.')
            _publish(root / 'policy.json', json.dumps(manifest, sort_keys=True).encode())
            return self.settings(local_file_id, core, rom)

    def disable(self, session, local_file_id, core, rom):
        """Return routing to RetroArch without deleting or moving either save set."""
        with session.idle_file_access():
            self.settings(local_file_id, core, rom)
            root = self.directory(local_file_id, core)
            if (root / 'policy.json').exists():
                manifest = {**self._manifest(local_file_id, core, rom), 'enabled': False}
                _publish(root / 'policy.json', json.dumps(manifest, sort_keys=True).encode())
