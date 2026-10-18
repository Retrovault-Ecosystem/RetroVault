from dataclasses import replace
from unittest.mock import Mock

import pytest

from services.emulators.session import EmulatorSession
from services.saves.recovery import SaveRecovery, SaveTarget


@pytest.fixture
def recovery(tmp_path):
    retroarch = Mock()
    native = Mock()
    retroarch.process_running.return_value = False
    native.process_running.return_value = False
    session = EmulatorSession(retroarch, native)
    save = tmp_path / 'game.srm'
    save.write_bytes(b'progress one')
    target = SaveTarget(save, 'physical-one', 'retroarch', 'snes9x', 'sram', 'a' * 64, 'b' * 64)
    return SaveRecovery(session, tmp_path / 'backups'), target


def test_explicit_restore_preserves_previous_progress_in_safety_backup(recovery):
    service, target = recovery
    original = service.backup(target)
    target.path.write_bytes(b'progress two')
    result = service.restore(target, original)
    assert target.path.read_bytes() == b'progress one'
    service.restore(target, result['safety_backup'])
    assert target.path.read_bytes() == b'progress two'


@pytest.mark.parametrize('field,value', [('local_file_id', 'physical-two'),
    ('backend', 'snes9x'), ('core', 'other'), ('kind', 'state'),
    ('runtime_sha256', 'c' * 64), ('content_sha256', 'd' * 64)])
def test_rejects_incompatible_backup_without_touching_destination(recovery, field, value):
    service, target = recovery
    original = service.backup(target)
    target.path.write_bytes(b'new progress')
    with pytest.raises(ValueError, match='does not match'):
        service.restore(replace(target, **{field: value}), original)
    assert target.path.read_bytes() == b'new progress'
    assert len(list(service.backup_root.iterdir())) == 1


@pytest.mark.parametrize('backend', ['retroarch', 'snes9x'])
def test_owned_process_blocks_backup_and_restore(recovery, backend):
    service, target = recovery
    original = service.backup(target)
    getattr(service.session, backend).process_running.return_value = True
    with pytest.raises(ValueError, match='Quit'):
        service.backup(target)
    with pytest.raises(ValueError, match='Quit'):
        service.restore(target, original)
    assert target.path.read_bytes() == b'progress one'


def test_failed_safety_backup_never_changes_save(recovery, monkeypatch):
    service, target = recovery
    original = service.backup(target)
    target.path.write_bytes(b'new progress')
    monkeypatch.setattr(service, '_backup', Mock(side_effect=OSError('disk full')))
    with pytest.raises(OSError, match='disk full'):
        service.restore(target, original)
    assert target.path.read_bytes() == b'new progress'


@pytest.mark.parametrize('failure', ['fsync', 'replace'])
def test_failed_publication_preserves_destination_and_cleans_temp(recovery, monkeypatch, failure):
    import services.saves.recovery as module
    service, target = recovery
    original = service.backup(target)
    target.path.write_bytes(b'new progress')
    real = getattr(module.os, failure)
    calls = 0
    def fail_second(*args):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError('injected failure')
        return real(*args)
    monkeypatch.setattr(module.os, failure, fail_second)
    with pytest.raises(OSError, match='injected failure'):
        service.restore(target, original)
    assert target.path.read_bytes() == b'new progress'
    assert not list(target.path.parent.rglob('.save-*'))
    assert len(list(service.backup_root.iterdir())) == 2


def test_symlink_target_is_rejected(recovery):
    service, target = recovery
    link = target.path.with_name('link.srm')
    link.symlink_to(target.path)
    with pytest.raises(ValueError, match='symbolic'):
        service.backup(replace(target, path=link))
    assert not service.backup_root.exists()


def test_inspection_is_read_only_and_invalid_identity_is_rejected(recovery):
    service, target = recovery
    assert service.inspect(target)['size'] == len(b'progress one')
    assert not service.backup_root.exists()
    with pytest.raises(ValueError, match='unambiguous'):
        service.backup(replace(target, local_file_id=''))
    assert not service.backup_root.exists()
