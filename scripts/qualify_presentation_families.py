"""Bounded USQE #8 evidence using the existing isolated production runner.

Default operation emits mathematical templates without launching anything.
--live requires an explicit platform, fixture, content mode and fresh output.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform as host_platform
import re
import shutil

from config import ConfigLoader
from services.presentation.platform_policy import PlatformPresentationPolicyRegistry
from services.presentation.qualification import (family_templates, binding_snapshot, checksum,
                                                geometry_evidence, assess_case, VISUAL_CHECKS)
from services.retroarch.core_resolver import CoreResolver
from scripts.qualify_retroarch_runtime import qualify, PLATFORMS


def display_snapshot():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance() or QApplication([])
    if app.platformName() in ('offscreen', 'minimal'):
        return {'source': 'headless Qt; physical display unverified'}
    screens = app.screens()
    if len(screens) != 1:
        return {'source': 'multiple/no Qt screens; actual emulator output requires confirmation',
                'screen_count': len(screens)}
    screen = screens[0]
    size = screen.size()
    scale = screen.devicePixelRatio()
    return {'width': round(size.width() * scale), 'height': round(size.height() * scale),
            'scale': scale, 'source': 'Qt screen inventory; single-screen session',
            'name': screen.name(), 'logical_size': [size.width(), size.height()],
            'qt_platform': app.platformName(), 'session_type': os.environ.get('XDG_SESSION_TYPE', '')}


def run_case(platform, rom, output, *, content_mode, seconds=30):
    if platform not in PLATFORMS or not content_mode.strip():
        raise ValueError('Select a bounded platform and explicit content mode.')
    root = Path(output).resolve()
    if root.exists():
        raise ValueError('Use a fresh output directory; prior evidence is never overwritten.')
    config = ConfigLoader().load()
    platform_id = PLATFORMS[platform]
    policy = PlatformPresentationPolicyRegistry.for_platform(platform_id)
    resolution = CoreResolver(config).resolve(policy.core_identities[0], platform_id)
    if not resolution.path:
        raise ValueError(resolution.message)
    binding = binding_snapshot(platform_id, resolution.path, config)
    frontend = shutil.which(config['retroarch']['executable'])
    if not frontend:
        raise ValueError('Configured RetroArch executable is unavailable.')
    frontend_hash = checksum(frontend)
    display = display_snapshot()
    record = {'case_id': platform + '-classic-4-3', 'date': datetime.now(timezone.utc).isoformat(),
              'binding': binding, 'fixture': {'path': str(Path(rom).resolve()), 'sha256': checksum(rom), 'form': 'loose'},
              'content_mode': content_mode, 'display': display, 'host': host_platform.platform(),
              'frontend_launcher': {'path': frontend, 'sha256': frontend_hash,
                                    'note': 'May be a wrapper; loaded frontend version is recorded from its runtime log.'},
              'human_acceptance': {**{key: None for key in VISUAL_CHECKS}, 'user_quote': '', 'date': ''},
              'templates': family_templates(), 'limitations': ['Startup selection only; live geometry switching is unqualified.',
                'Configuration and mathematical evidence do not establish rendered edge visibility.',
                'Fresh-process Library reconstruction is not a second visual emulator run.']}
    report = qualify(platform, rom, root, seconds, pipeline=True, managed_keyboard=True)
    log_path = root / 'retroarch.log'
    log = log_path.read_text(errors='replace') if log_path.exists() else ''
    version = re.search(r'RetroArch\s+([^\r\n]+)', log)
    record['runtime_version'] = version.group(1).strip() if version else None
    record['runtime_driver_evidence'] = [line for line in log.splitlines()
                                       if any(token in line for token in ('[Video]', '[GL]', '[Vulkan]', '[GLCore]'))]
    record['local_file_id'] = report.get('local_file_id')
    record['capture'] = report.get('presentation', {})
    record['geometry'] = geometry_evidence(binding, record['capture'], log)
    record['automation_passed'] = bool(report.get('pipeline_passed') and report.get('core_sha256') == binding['core_sha256'])
    record['automation_passed'] = bool(record['automation_passed']
        and checksum(resolution.path) == binding['core_sha256'] and checksum(frontend) == frontend_hash)
    record['package_unchanged'] = all(Path(p).is_file() and checksum(p) == h for p, h in binding['package_hashes'].items())
    record['runtime_report'] = str(root / 'report.json')
    record['assessment'] = assess_case(record)
    (root / 'presentation-qualification.json').write_text(json.dumps(record, indent=2) + '\n')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--platform', choices=PLATFORMS)
    parser.add_argument('--rom')
    parser.add_argument('--output', required=True)
    parser.add_argument('--content-mode', default='')
    parser.add_argument('--seconds', type=float, default=30)
    args = parser.parse_args()
    if args.live:
        if not args.platform or not args.rom or not args.content_mode:
            parser.error('--live requires platform, ROM and content mode')
        result = run_case(args.platform, args.rom, args.output, content_mode=args.content_mode, seconds=args.seconds)
        print(json.dumps({'assessment': result['assessment'], 'report': str(Path(args.output) / 'presentation-qualification.json')}, indent=2))
        raise SystemExit(0 if result['automation_passed'] and result['geometry']['result'] == 'pass' else 1)
    with Path(args.output).open('x') as handle:
        json.dump({'scope': 'mathematical templates only; no live qualification', 'families': family_templates()}, handle, indent=2)
        handle.write('\n')
