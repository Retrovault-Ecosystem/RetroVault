"""Evidence must not promote policy or substitute generic family geometry."""
from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from services.presentation.qualification import (family_templates, geometry_evidence, assess_case,
                                                binding_snapshot, VISUAL_CHECKS)
from services.presentation.master_profile import MasterPresentationProfileRegistry, MasterPresentationClass
from services.presentation.platform_policy import PlatformPresentationPolicyRegistry


def binding():
    return {'family': 'classic_4_3', 'package_aperture': {'canvas_width': 1920, 'canvas_height': 1080,
            'x': 438, 'y': 71, 'width': 1044, 'height': 783}}


def capture():
    return {'effective_settings': dict(custom_viewport_x='438', custom_viewport_y='71',
                                      custom_viewport_width='1044', custom_viewport_height='783')}


def complete_record():
    return {'automation_passed': True, 'package_unchanged': True, 'geometry': {'result': 'pass'},
            'binding': {**binding(), 'family_envelope': {'canvas_width': 1920},
                        'platform_id': 'platform.nintendo.snes', 'backend': 'retroarch', 'core': 'snes9x',
                        'core_sha256': 'a' * 64, 'package_hashes': {'package': 'b' * 64}},
            'fixture': {'sha256': 'c' * 64, 'form': 'loose'}, 'local_file_id': 'local-file:test',
            'frontend_launcher': {'sha256': 'd' * 64},
            'capture': {'ordered_configs': [{'sha256': 'e' * 64}], 'shader_sha256': 'f' * 64,
                        'artwork_sha256': '0' * 64},
            'display': {'width': 1920, 'height': 1080, 'scale': 1, 'source': 'recorded display'},
            'runtime_version': 'recorded version', 'content_mode': 'normal gameplay',
            'human_acceptance': {**dict.fromkeys(VISUAL_CHECKS, True), 'user_quote': 'all checks pass', 'date': '2026-10-17'}}


def test_templates_are_math_only_and_do_not_change_readiness():
    before = dict(PlatformPresentationPolicyRegistry.PLATFORM_STATES)
    rows = family_templates()
    assert json.loads(json.dumps(rows))
    assert all(row['live_result'] == 'not_run' for row in rows)
    assert next(row for row in rows if row['family'] == 'handheld_native')['profile'] is None
    assert next(row for row in rows if row['family'] == 'mixed_or_exception')['profile'] is None
    assert PlatformPresentationPolicyRegistry.PLATFORM_STATES == before
    for row in rows:
        profile = row['profile']
        if profile is None:
            continue
        for example in row['examples']:
            g = example['geometry']
            w, h = example['display_aspect']
            assert g['x'] >= profile['envelope_x'] and g['y'] >= profile['envelope_y']
            assert g['x'] + g['width'] <= profile['envelope_x'] + profile['envelope_width']
            assert g['y'] + g['height'] <= profile['envelope_y'] + profile['envelope_height']
            assert abs(g['width'] * h - g['height'] * w) <= max(w, h)


def test_binding_geometry_uses_package_aperture_not_family_envelope():
    result = geometry_evidence(binding(), capture(), '[Core] Geometry: 256x224, Aspect: 1.3333333333333333')
    assert result['result'] == 'pass'
    assert result['actual'] == {'x': 438, 'y': 71, 'width': 1044, 'height': 783}
    assert result['rendered_edges_and_orientation'] == 'pending human acceptance'
    generic = MasterPresentationProfileRegistry.require(MasterPresentationClass.CLASSIC_4_3).contain_aspect(4,3)
    assert asdict(generic) != result['actual']


def test_geometry_cannot_pass_without_runtime_evidence():
    assert geometry_evidence(binding(), capture(), '')['result'] == 'blocked'
    assert geometry_evidence(binding(), {}, '[Core] Geometry: 256x224, Aspect: 1.333')['result'] == 'blocked'


def test_wrong_viewport_and_later_geometry_are_not_silently_qualified():
    c = capture()
    c['effective_settings']['custom_viewport_x'] = '0'
    assert geometry_evidence(binding(), c, '[Core] Geometry: 256x224, Aspect: 1.333')['result'] == 'fail'
    log = '[Core] Geometry: 256x224, Aspect: 1.333\n[Environ] SET_GEOMETRY: 320x240, Aspect: 1.777'
    assert geometry_evidence(binding(), capture(), log)['result'] == 'fail'


def test_complete_evidence_can_pass_only_its_recorded_scope():
    assert assess_case(complete_record())['result'] == 'pass'


@pytest.mark.parametrize('missing', [*VISUAL_CHECKS, 'user_quote', 'date'])
def test_missing_human_evidence_never_passes(missing):
    record = complete_record()
    del record['human_acceptance'][missing]
    assert assess_case(record)['result'] == 'not_run'


@pytest.mark.parametrize('bad', [None, 0, True, float('nan'), float('inf')])
def test_missing_or_invalid_display_scale_blocks_pass(bad):
    record = complete_record()
    record['display']['scale'] = bad
    assert assess_case(record)['result'] == 'blocked'


@pytest.mark.parametrize('field', ['runtime_version','content_mode'])
def test_missing_runtime_or_content_mode_blocks_pass(field):
    record = complete_record()
    del record[field]
    assert assess_case(record)['result'] == 'blocked'


def test_failed_checks_override_complete_visual_acceptance():
    record = complete_record()
    record['package_unchanged'] = False
    assert assess_case(record)['result'] == 'fail'
    record = complete_record()
    record['human_acceptance']['orientation'] = False
    assert assess_case(record)['result'] == 'fail'


def test_unknown_binding_does_not_create_policy(tmp_path):
    with pytest.raises(ValueError, match='existing production binding'):
        binding_snapshot('platform.unknown', tmp_path / 'unused.so', {})
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('field', ['binding', 'fixture', 'local_file_id', 'capture', 'frontend_launcher'])
def test_missing_provenance_blocks_even_when_visuals_are_accepted(field):
    record = complete_record()
    del record[field]
    assert assess_case(record)['result'] == 'blocked'
