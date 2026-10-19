"""Explicit offline delivery. Producer validation stays in RVDB; activation is atomic.

The checkpoint is published before activation. It records intent, not proof that
activation finished. Rollback never swaps copies, so retries are idempotent.
"""
import base64
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from services.rvdb import RVDBService, RVDBError

PRODUCER_REPOSITORY = 'https://github.com/Retrovault-Ecosystem/RVDB'


def _sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _publish(path, payload, *, bundle=False):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.rvdb-stage-', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        if bundle:
            RVDBService.from_bundle(temporary)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _validate(payload, directory):
    with tempfile.NamedTemporaryFile(dir=directory, prefix='.rvdb-stage-') as handle:
        handle.write(payload)
        handle.flush()
        RVDBService.from_bundle(handle.name)


def _paths(destination):
    destination = Path(destination).expanduser().absolute()
    if any(p.is_symlink() for p in (destination, *destination.parents)):
        raise ValueError('Bundle delivery does not follow destination symlinks.')
    return destination, destination.with_name(destination.name + '.rollback.json')


@contextmanager
def _locked(destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    lock = destination.with_name(destination.name + '.delivery.lock')
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def install_bundle(source, destination, *, expected_sha256, producer_commit):
    """Caller obtains the pin from the trusted producer, independently of the file."""
    if not re.fullmatch(r'[0-9a-f]{64}', expected_sha256 or ''):
        raise ValueError('Expected SHA-256 must be 64 lowercase hexadecimal characters.')
    if not re.fullmatch(r'[0-9a-f]{40}', producer_commit or ''):
        raise ValueError('Producer commit must be a full 40-character hexadecimal commit ID.')
    payload = Path(source).expanduser().read_bytes()
    if _sha(payload) != expected_sha256:
        raise ValueError('Candidate does not match the independently approved SHA-256.')
    destination, checkpoint = _paths(destination)
    with _locked(destination):
        _validate(payload, destination.parent)
        previous = destination.read_bytes() if destination.exists() else None
        if previous == payload:
            return expected_sha256  # Do not replace the useful rollback point.
        if previous is not None:
            _validate(previous, destination.parent)
        if checkpoint.is_symlink():
            raise ValueError('Rollback checkpoint must not be a symlink.')
        record = {'version': 1, 'destination': str(destination),
                  'producer_repository': PRODUCER_REPOSITORY, 'producer_commit': producer_commit,
                  'candidate_sha256': expected_sha256,
                  'previous_sha256': _sha(previous) if previous is not None else None,
                  'previous_payload': base64.b64encode(previous).decode('ascii') if previous is not None else None}
        _publish(checkpoint, (json.dumps(record, sort_keys=True, indent=2)+'\n').encode())
        _publish(destination, payload, bundle=True)
    return expected_sha256


def rollback_bundle(destination):
    destination, checkpoint = _paths(destination)
    with _locked(destination):
        if checkpoint.is_symlink():
            raise ValueError('Rollback checkpoint must not be a symlink.')
        record = json.loads(checkpoint.read_text())
        if not isinstance(record, dict) or record.get('version') != 1 or record.get('destination') != str(destination):
            raise ValueError('Rollback checkpoint does not match this destination.')
        if record.get('previous_payload') is None:
            raise ValueError('No previous bundle exists for rollback.')
        try:
            payload = base64.b64decode(record['previous_payload'], validate=True)
        except (ValueError, TypeError) as exc:
            raise ValueError('Invalid rollback payload.') from exc
        if _sha(payload) != record.get('previous_sha256'):
            raise ValueError('Rollback checksum mismatch.')
        _validate(payload, destination.parent)
        current = destination.read_bytes() if destination.exists() else None
        if current == payload:
            return _sha(payload)
        if current is not None and _sha(current) != record.get('candidate_sha256'):
            try:
                _validate(current, destination.parent)
            except RVDBError:
                pass  # Explicit rollback can recover an unreadable active bundle.
            else:
                raise ValueError('Installed bundle changed outside this delivery checkpoint; refusing rollback.')
        _publish(destination, payload, bundle=True)
    return _sha(payload)
