"""Explicitly install a validated producer bundle; no downloading or source build."""
import argparse
import hashlib
import os
from pathlib import Path
import tempfile
from config.paths import RVDB_BUNDLE
from services.rvdb import RVDBService


def install_bundle(source, destination=RVDB_BUNDLE):
    source, destination = Path(source).expanduser(), Path(destination).expanduser()
    payload = source.read_bytes()
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.rvdb-', suffix='.json', dir=destination.parent)
    temporary = Path(temporary)
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        # Validate the exact bytes staged, not a source that could change later.
        RVDBService.from_bundle(temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return hashlib.sha256(payload).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source')
    parser.add_argument('--destination', default=str(RVDB_BUNDLE))
    args = parser.parse_args()
    print(install_bundle(args.source, args.destination))


if __name__ == '__main__':
    main()
