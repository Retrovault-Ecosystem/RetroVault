"""Same-target backups; never infer format compatibility or relocate saves."""
from dataclasses import asdict, dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import uuid
import zipfile


@dataclass(frozen=True)
class SaveTarget:
    path: Path
    local_file_id: str
    backend: str
    core: str
    kind: str
    runtime_sha256: str
    content_sha256: str

    def contract(self):
        if (not self.local_file_id or not self.backend or not self.core
                or self.kind not in ('sram', 'state')):
            raise ValueError('Save recovery requires an unambiguous edition/backend/core/kind.')
        for value in (self.runtime_sha256, self.content_sha256):
            if len(value) != 64 or any(char not in '0123456789abcdef' for char in value):
                raise ValueError('Save recovery requires verified runtime and content SHA-256.')
        result = asdict(self)
        result['path'] = str(self.path.absolute())
        return result


def _regular_path(path):
    path = Path(path).absolute()
    if any(part.is_symlink() for part in (path, *path.parents)):
        raise ValueError('Save recovery does not follow symbolic links.')
    if not path.is_file():
        raise ValueError('Select one existing regular save file.')
    return path


def _publish(path, payload):
    """Flush before replace; failed writes leave the previous destination intact."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.save-', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class SaveRecovery:
    """All operations share the process owner's lock with launch and Stop.

    Callers supply one inspected target, never a directory/wildcard or guessed
    legacy destination. Backups are same-target, same-runtime recovery points.
    """
    def __init__(self, session, backup_root):
        self.session = session
        self.backup_root = Path(backup_root).absolute()

    def inspect(self, target):
        contract = target.contract()
        path = _regular_path(target.path)
        payload = path.read_bytes()
        return {**contract, 'size': len(payload),
                'sha256': hashlib.sha256(payload).hexdigest()}

    def _backup(self, target):
        path = _regular_path(target.path)
        payload = path.read_bytes()
        manifest = {**target.contract(), 'version': 1,
                    'sha256': hashlib.sha256(payload).hexdigest()}
        if any(part.is_symlink() for part in (self.backup_root, *self.backup_root.parents)):
            raise ValueError('Backup storage must not follow symbolic links.')
        self.backup_root.mkdir(parents=True, exist_ok=True)
        destination = self.backup_root / (uuid.uuid4().hex + '.rvsave')
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, 'w') as bundle:
            bundle.writestr('manifest.json', json.dumps(manifest, sort_keys=True))
            bundle.writestr('save.bin', payload)
        _publish(destination, buffer.getvalue())
        return destination

    def backup(self, target):
        with self.session.idle_file_access():
            return self._backup(target)

    def restore(self, target, backup):
        with self.session.idle_file_access():
            path = _regular_path(target.path)
            with zipfile.ZipFile(_regular_path(backup)) as bundle:
                if sorted(bundle.namelist()) != ['manifest.json', 'save.bin']:
                    raise ValueError('Invalid save backup members.')
                manifest = json.loads(bundle.read('manifest.json'))
                payload = bundle.read('save.bin')
            expected = {**target.contract(), 'version': 1,
                        'sha256': hashlib.sha256(payload).hexdigest()}
            if manifest != expected:
                raise ValueError('Backup does not match this edition, backend, runtime and destination.')
            # Complete the safety backup before touching the selected save.
            safety_backup = self._backup(target)
            mode = path.stat().st_mode & 0o777
            _publish(path, payload)
            # A restrictive replacement permission is safe; do not claim a
            # failed restore if permission restoration fails after publication.
            permission_warning = ''
            try:
                path.chmod(mode)
            except OSError as exc:
                permission_warning = str(exc)
            return {'restored': str(path), 'safety_backup': str(safety_backup),
                    'permission_warning': permission_warning}
