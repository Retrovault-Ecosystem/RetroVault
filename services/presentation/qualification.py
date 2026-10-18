"""Presentation evidence only: never selects runtime policy or promotes readiness."""
from dataclasses import asdict
import hashlib
import math
from pathlib import Path

from .master_profile import (MasterPresentationClass, MasterPresentationProfileRegistry,
                             master_presentation_qualification)
from .platform_policy import PlatformPresentationPolicyRegistry
from .production_package_resolver import CanonicalProductionPackageResolver
from services.retroarch.core_identity import canonical_libretro_core_identity
from services.retroarch.runtime_display_aspect import RuntimeDisplayAspectObserver

VISUAL_CHECKS = ('orientation', 'all_edges_visible', 'natural_proportions',
                 'bezel_alignment', 'startup', 'gameplay')


def checksum(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def family_templates():
    """Calculated examples are not physical display or live-platform qualification."""
    rows = []
    for family in MasterPresentationClass:
        profile = MasterPresentationProfileRegistry.get(family)
        row = {'family': family.value, 'existing_registry_state': master_presentation_qualification(family).value,
               'evidence_scope': 'mathematical template only', 'live_result': 'not_run',
               'profile': asdict(profile) if profile else None, 'examples': []}
        if profile:
            for width, height in ((4, 3), (16, 9), (8, 7), (9, 16)):
                geometry = profile.contain_aspect(width, height)
                row['examples'].append({'display_aspect': [width, height], 'geometry': asdict(geometry)})
        rows.append(row)
    rows.append({'family': 'mixed_or_exception', 'profile': None, 'examples': [],
                 'evidence_scope': 'requires explicit content modes and transition evidence',
                 'live_result': 'not_run'})
    return rows


def binding_snapshot(platform_id, core_path, config):
    core = canonical_libretro_core_identity(str(core_path))
    package = CanonicalProductionPackageResolver.resolve(platform_id=platform_id, core_identity=core, config=config)
    if package is None:
        raise ValueError('An existing production binding is required; qualification cannot create one.')
    family = PlatformPresentationPolicyRegistry.master_presentation_profile_for(platform_id)
    if family is None:
        raise ValueError('No explicit presentation family binding.')
    files = {Path(package.overlay), Path(package.shader), Path(package.runtime_descriptor), Path(package.production_manifest)}
    # Include all package-local shader/artwork dependencies. No assets are written.
    for directory in {Path(package.overlay).parent, Path(package.shader).parent}:
        files.update(p for p in directory.rglob('*') if p.is_file())
    return {'platform_id': platform_id, 'backend': 'retroarch', 'core': core,
            'core_path': str(core_path), 'core_sha256': checksum(core_path),
            'family': family.profile_class.value, 'family_envelope': asdict(family),
            'package_aperture': asdict(package.fixed_glass()),
            'package_hashes': {str(p): checksum(p) for p in sorted(files)}}


def geometry_evidence(binding, capture, log_text):
    """Compare captured viewport against package containment and observed aspect."""
    from .production_glass import ProductionGlass
    observer = RuntimeDisplayAspectObserver('/unused-evidence-log')
    observer.observe_text(log_text)
    aspect = observer.display_aspect
    if aspect is None:
        return {'result': 'blocked', 'reason': 'No core display-aspect evidence.'}
    aperture = ProductionGlass(**binding['package_aperture'])
    profile = aperture.as_master_profile(profile_class=MasterPresentationClass(binding['family']))
    expected = asdict(profile.contain_aspect(aspect.width, aspect.height))
    settings = capture.get('effective_settings', {})
    try:
        actual = {name: int(settings['custom_viewport_' + name]) for name in ('x', 'y', 'width', 'height')}
    except (KeyError, TypeError, ValueError):
        return {'result': 'blocked', 'reason': 'Final custom viewport evidence is incomplete.'}
    errors = []
    if actual != expected:
        errors.append('Final viewport differs from package containment of the observed aspect; inspect content mode/transition.')
    if (actual['width'] <= 0 or actual['height'] <= 0 or actual['x'] < aperture.x or actual['y'] < aperture.y
            or actual['x'] + actual['width'] > aperture.x + aperture.width
            or actual['y'] + actual['height'] > aperture.y + aperture.height):
        errors.append('Viewport is outside the package aperture.')
    # Configuration alone is not proof of rendered orientation or visible edges.
    return {'result': 'fail' if errors else 'pass', 'errors': errors,
            'aspect': asdict(aspect), 'aspect_source': 'RetroArch core geometry log',
            'expected': expected, 'actual': actual, 'integer_rounding_tolerance_pixels': 1,
            'set_geometry_events': observer.set_geometry_count,
            'transition_qualification': 'not_run', 'rendered_edges_and_orientation': 'pending human acceptance'}


def assess_case(record):
    """Missing evidence never becomes pass. No runtime policy consumes this result."""
    if record.get('automation_passed') is not True or record.get('package_unchanged') is not True:
        return {'result': 'fail', 'reason': 'Runtime, preservation or package verification failed.'}
    geometry = record.get('geometry', {})
    if geometry.get('result') != 'pass':
        return {'result': geometry.get('result', 'blocked'), 'reason': 'Geometry evidence is incomplete or conflicting.'}
    binding = record.get('binding', {})
    fixture = record.get('fixture', {})
    capture = record.get('capture', {})
    if (not all(binding.get(key) for key in ('platform_id', 'backend', 'core', 'core_sha256',
                                             'family', 'family_envelope', 'package_aperture', 'package_hashes'))
            or not all(fixture.get(key) for key in ('sha256', 'form'))
            or not record.get('local_file_id') or not capture.get('ordered_configs')
            or not capture.get('shader_sha256') or not capture.get('artwork_sha256')
            or not record.get('frontend_launcher', {}).get('sha256')):
        return {'result': 'blocked', 'reason': 'Binding, fixture, binary or package/configuration provenance is missing.'}
    display = record.get('display', {})
    for field in ('width', 'height', 'scale'):
        value = display.get(field)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
            return {'result': 'blocked', 'reason': 'Display dimensions/scaling are unverified.'}
    if not display.get('source') or not record.get('runtime_version') or not record.get('content_mode'):
        return {'result': 'blocked', 'reason': 'Display provenance, runtime version or content mode is missing.'}
    acceptance = record.get('human_acceptance', {})
    if any(acceptance.get(key) is False for key in VISUAL_CHECKS):
        return {'result': 'fail', 'reason': 'A visual acceptance check failed.'}
    if not all(acceptance.get(key) is True for key in VISUAL_CHECKS) or not acceptance.get('user_quote') or not acceptance.get('date'):
        return {'result': 'not_run', 'reason': 'Targeted human visual acceptance remains pending.'}
    return {'result': 'pass', 'reason': 'Qualified only for the recorded binding, fixture, mode and display.'}
