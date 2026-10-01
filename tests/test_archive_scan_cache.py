from unittest.mock import Mock

from services.library.archive_scan_cache import ArchiveScanCache


def test_unchanged_archive_reuses_member_across_app_restarts(tmp_path):
    archive = tmp_path / 'game.7z'
    archive.write_bytes(b'archive')
    path = tmp_path / 'cache.json'
    runtime = Mock()
    runtime.preferred_member.return_value = 'game.nes'
    cache = ArchiveScanCache(path)
    assert cache.preferred_member(archive, runtime) == 'game.nes'
    cache.flush()
    assert ArchiveScanCache(path).preferred_member(archive, runtime) == 'game.nes'
    runtime.preferred_member.assert_called_once()


def test_modified_or_replaced_archive_is_inspected_again(tmp_path):
    archive = tmp_path / 'game.7z'
    archive.write_bytes(b'first')
    runtime = Mock()
    runtime.preferred_member.side_effect = ['first.nes', 'second.sfc', 'third.md']
    cache = ArchiveScanCache(tmp_path / 'cache.json')
    assert cache.preferred_member(archive, runtime) == 'first.nes'
    archive.write_bytes(b'second archive')
    assert cache.preferred_member(archive, runtime) == 'second.sfc'
    replacement = tmp_path / 'replacement'
    replacement.write_bytes(b'second archive')
    replacement.replace(archive)
    assert cache.preferred_member(archive, runtime) == 'third.md'
    assert runtime.preferred_member.call_count == 3


def test_failed_classification_is_not_cached(tmp_path):
    archive = tmp_path / 'game.7z'
    archive.touch()
    runtime = Mock()
    runtime.preferred_member.side_effect = [None, 'game.nes']
    cache = ArchiveScanCache(tmp_path / 'cache.json')
    assert cache.preferred_member(archive, runtime) is None
    assert cache.preferred_member(archive, runtime) == 'game.nes'


def test_corrupt_or_unwritable_cache_does_not_block_scan(tmp_path):
    path = tmp_path / 'cache.json'
    path.write_text('broken json')
    cache = ArchiveScanCache(path)
    archive = tmp_path / 'game.7z'
    archive.touch()
    runtime = Mock()
    runtime.preferred_member.return_value = 'game.nes'
    assert cache.preferred_member(archive, runtime) == 'game.nes'
    cache.path = path / 'impossible.json'
    cache.flush()
    assert cache.preferred_member(archive, runtime) == 'game.nes'
