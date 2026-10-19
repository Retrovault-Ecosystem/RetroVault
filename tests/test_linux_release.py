"""Release artifacts must be deterministic and reject untrusted archive paths."""
import hashlib
import io
import tarfile
import pytest
from scripts.linux_release import make_archive, read_archive


def test_archive_determinism_and_pin(tmp_path):
    files={'app.py':b'print("hello")\n','requirements.txt':b''}
    first=tmp_path/'a.tar.gz';second=tmp_path/'b.tar.gz'
    make_archive(files,first,'test',{'source_commit':'a'*40})
    make_archive(files,second,'test',{'source_commit':'a'*40})
    assert first.read_bytes()==second.read_bytes()
    digest=hashlib.sha256(first.read_bytes()).hexdigest()
    manifest,payload=read_archive(first,digest)
    assert manifest['release']=='test' and payload==files
    with pytest.raises(ValueError):read_archive(first,'0'*64)

@pytest.mark.parametrize('name',['../escape','/absolute','a/../../escape'])
def test_archive_rejects_unsafe_paths(tmp_path,name):
    archive=tmp_path/'bad.tar.gz'
    with tarfile.open(archive,'w:gz') as t:
        member=tarfile.TarInfo(name);member.size=1;t.addfile(member,io.BytesIO(b'x'))
    with pytest.raises(ValueError):read_archive(archive,hashlib.sha256(archive.read_bytes()).hexdigest())


def test_install_failure_keeps_previous_state_and_user_data(tmp_path,monkeypatch):
    import scripts.linux_release as release
    root=tmp_path/'install'
    with release.owned_root(root,create=True):
        (root/'state.json').write_text('{"current":"old","previous":null}')
    user=tmp_path/'user-save';user.write_text('progress')
    archive=tmp_path/'test.tar.gz'
    files={'app.py':b'', 'requirements.txt':b'', 'data/rvdb/rvdb.bundle.json':b'{}','scripts/check_startup.py':b''}
    digest=make_archive(files,archive,'new',{})
    monkeypatch.setattr(release,'check_host',lambda:None)
    def fail(*a,**kw):raise OSError('environment preparation failed')
    monkeypatch.setattr(release.subprocess,'run',fail)
    with pytest.raises(OSError):release.install(archive,digest,root)
    assert release.read_state(root)['current']=='old'
    assert not (root/'releases/new').exists()
    assert user.read_text()=='progress'


def test_rollback_and_remove_preserve_external_data(tmp_path):
    import json
    import scripts.linux_release as release
    root=tmp_path/'install';user=tmp_path/'user';user.mkdir();(user/'save').write_text('progress')
    with release.owned_root(root,create=True):
        for version in ('one','two'):
            d=root/'releases'/version;d.mkdir(parents=True)
            (d/'app.py').write_bytes(b'code')
            (d/'release.json').write_text(json.dumps({'files':{'app.py':hashlib.sha256(b'code').hexdigest()}}))
        (root/'state.json').write_text('{"current":"two","previous":"one"}')
    assert release.rollback(root)=='one'
    with pytest.raises(ValueError):release.rollback(root)
    release.remove(root);release.remove(root)
    assert (user/'save').read_text()=='progress'
    assert not (root/'releases').exists()


def test_nonempty_unowned_root_is_never_adopted(tmp_path):
    import scripts.linux_release as release
    (tmp_path/'save').write_text('progress')
    with pytest.raises(ValueError):
        with release.owned_root(tmp_path,create=True):pass
    assert (tmp_path/'save').read_text()=='progress'
