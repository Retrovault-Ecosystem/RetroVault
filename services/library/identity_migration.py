"""Resumable identity migration through the existing persistence services.

The registry commits first. Each backed-up store then commits independently;
repeating after interruption uses the same IDs and retains unresolved keys.
"""
import os
from pathlib import Path


def backup_original(path):
    path = Path(path)
    if not path.exists():
        return
    backup = path.with_name(path.name + ".pre-identity.bak")
    if backup.exists():
        return
    # Same-directory atomic publication avoids accepting a partial backup on retry.
    temporary = backup.with_name(backup.name + ".tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(path.read_bytes())
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, backup)
    finally:
        temporary.unlink(missing_ok=True)


def mapped_list(values, mapping):
    return list(dict.fromkeys(mapping.get(value, value) for value in values))


def migrate_stores(mapping, *stores):
    # Validate every input before changing any store. Later I/O failures are
    # recoverable by retry; this is intentionally not a cross-file transaction.
    for store in stores:
        store.validate_identity_migration()
    for store in stores:
        store.migrate_identities(mapping)
