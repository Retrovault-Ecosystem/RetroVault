"""Run with python -m scripts.check_startup; performs no filesystem writes."""
from dataclasses import asdict
import json
from services.startup import check_startup


def main():
    report = check_startup()
    print(json.dumps(asdict(report), indent=2))
    return 1 if report.errors or not report.bundle_available else 0


if __name__ == '__main__':
    raise SystemExit(main())
