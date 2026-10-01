import json
from pathlib import Path
import pytest
from scripts.install_rvdb_bundle import install_bundle
from services.rvdb import RVDBError


def test_bundle_install_validates_and_preserves_bytes(tmp_path):
    source = tmp_path / 'source.json'
    source.write_text(json.dumps({'nodes': {}, 'edges': {}}))
    target = tmp_path / 'consumer/bundle.json'
    assert len(install_bundle(source, target)) == 64
    assert target.read_bytes() == source.read_bytes()
    assert list(target.parent.iterdir()) == [target]


@pytest.mark.parametrize('failure', ['invalid', 'replace'])
def test_failed_bundle_install_preserves_previous_bundle(tmp_path, monkeypatch, failure):
    source, target = tmp_path / 'source.json', tmp_path / 'bundle.json'
    target.write_text('{"nodes": {}, "edges": {}}')
    before = target.read_bytes()
    source.write_text('broken' if failure == 'invalid' else target.read_text())
    if failure == 'replace':
        def fail(*args):
            raise OSError('interrupted replace')
        monkeypatch.setattr('scripts.install_rvdb_bundle.os.replace', fail)
    with pytest.raises((RVDBError, OSError)):
        install_bundle(source, target)
    assert target.read_bytes() == before
    assert sorted(path.name for path in tmp_path.iterdir()) == ['bundle.json', 'source.json']
