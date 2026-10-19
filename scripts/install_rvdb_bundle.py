"""Explicit pinned local-bundle installation or rollback; restart RetroVault afterward."""
import argparse
from config.paths import RVDB_BUNDLE
from services.rvdb import RVDBError
from services.rvdb.delivery import install_bundle as _install, rollback_bundle


def install_bundle(source, destination=RVDB_BUNDLE, *, expected_sha256, producer_commit):
    return _install(source, destination, expected_sha256=expected_sha256, producer_commit=producer_commit)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', nargs='?')
    parser.add_argument('--destination', default=str(RVDB_BUNDLE))
    parser.add_argument('--expected-sha256')
    parser.add_argument('--producer-commit')
    parser.add_argument('--rollback', action='store_true')
    args = parser.parse_args()
    if args.rollback:
        if args.source or args.expected_sha256 or args.producer_commit:
            parser.error('--rollback cannot be combined with installation arguments')
    elif not args.source or not args.expected_sha256 or not args.producer_commit:
        parser.error('installation requires source, --expected-sha256 and --producer-commit')
    try:
        digest = (rollback_bundle(args.destination) if args.rollback else
                  install_bundle(args.source, args.destination, expected_sha256=args.expected_sha256,
                                 producer_commit=args.producer_commit))
    except (OSError, ValueError, RVDBError) as exc:
        parser.exit(1, f'RVDB delivery failed: {exc}\n')
    print(digest)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
