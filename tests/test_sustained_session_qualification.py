"""Explicit sustained qualification must not relax ordinary smoke-run limits."""
import pytest
from scripts.qualify_retroarch_runtime import validate_observation_duration, qualify
from scripts.qualify_standalone_runtime import qualify as qualify_native


@pytest.mark.parametrize('seconds', [1, 30, 0, 601, float('nan'), float('inf'), True])
def test_sustained_requires_exact_approved_window(seconds):
    with pytest.raises(ValueError):
        validate_observation_duration(seconds, sustained=True)


def test_short_default_and_explicit_sustained_window():
    validate_observation_duration(30)
    validate_observation_duration(600, sustained=True)
    with pytest.raises(ValueError):
        validate_observation_duration(600)


def test_sustained_rejects_non_pipeline_before_output(tmp_path):
    with pytest.raises(ValueError, match='pipeline'):
        qualify('nes', 'missing.nes', tmp_path/'out', 600, sustained=True)
    assert not (tmp_path/'out').exists()


def test_native_rejects_unapproved_duration_before_output(tmp_path):
    with pytest.raises(ValueError):
        qualify_native('missing', 'missing.sfc', tmp_path/'out', 601, sustained=True)
    assert not (tmp_path/'out').exists()


def test_explicit_mode_reaches_pipeline_and_keeps_human_acceptance_pending(tmp_path, monkeypatch):
    import scripts.qualify_retroarch_runtime as runner
    monkeypatch.setattr(runner, '__file__', str(tmp_path/'scripts'/'runner.py'))
    captured = {}
    def pipeline(rom, output, seconds, **options):
        captured.update(seconds=seconds, **options)
        return {'owned_group_remaining': False, 'visual_acceptance': 'pending'}
    monkeypatch.setattr(runner, '_qualify_pipeline', pipeline)
    result = runner.qualify('nes', 'fixture.nes', tmp_path/'out', 600,
                            pipeline=True, managed_keyboard=True, sustained=True)
    assert captured['sustained'] is True
    assert captured['seconds'] == 600
    assert captured['managed_keyboard'] is True
    assert result['visual_acceptance'] == 'pending'
