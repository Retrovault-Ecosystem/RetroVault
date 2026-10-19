import hashlib
import json
import pytest
from services.rvdb import RVDBError
from services.rvdb.delivery import install_bundle, rollback_bundle

REPO = 'https://github.com/Retrovault-Ecosystem/RVDB'
COMMIT = 'a' * 40

def sha(data):
    return hashlib.sha256(data).hexdigest()

def put(path, label):
    data = json.dumps({'nodes': {}, 'edges': {}}, indent=label).encode()
    path.write_bytes(data)
    return data

def install(source, target, data):
    return install_bundle(source, target, expected_sha256=sha(data), producer_commit=COMMIT)

def test_roundtrip_and_repeated_install_preserve_original_backup(tmp_path):
    target, source = tmp_path/'active.json', tmp_path/'candidate.json'
    old, new = put(target, 1), put(source, 2)
    assert install(source, target, new) == sha(new)
    install(source, target, new)
    assert rollback_bundle(target) == sha(old)
    assert target.read_bytes() == old
    assert rollback_bundle(target) == sha(old)

def test_wrong_hash_never_changes_active(tmp_path):
    target, source = tmp_path/'active.json', tmp_path/'candidate.json'
    old, new = put(target, 1), put(source, 2)
    with pytest.raises(ValueError):
        install_bundle(source,target,expected_sha256='0'*64,producer_commit=COMMIT)
    assert target.read_bytes()==old

def test_failed_activation_preserves_active_and_allows_rollback(tmp_path,monkeypatch):
    import services.rvdb.delivery as delivery
    target, source = tmp_path/'active.json', tmp_path/'candidate.json'
    old,new=put(target,1),put(source,2)
    replace=delivery.os.replace
    def fail(src,dst):
        if dst==target: raise OSError('activation failed')
        return replace(src,dst)
    monkeypatch.setattr(delivery.os,'replace',fail)
    with pytest.raises(OSError):install(source,target,new)
    assert target.read_bytes()==old
    assert not list(tmp_path.glob('.rvdb-stage-*'))

def test_corrupt_checkpoint_is_not_activated(tmp_path):
    target, source = tmp_path/'active.json', tmp_path/'candidate.json'
    put(target,1);new=put(source,2);install(source,target,new)
    checkpoint=target.with_name(target.name+'.rollback.json')
    d=json.loads(checkpoint.read_text());d['previous_sha256']='0'*64;checkpoint.write_text(json.dumps(d))
    with pytest.raises(ValueError):rollback_bundle(target)
    assert target.read_bytes()==new

@pytest.mark.parametrize('operation',['write','flush','fsync','replace'])
@pytest.mark.parametrize('phase',['checkpoint','activation'])
def test_publication_failures_preserve_active_and_remove_staging(tmp_path,monkeypatch,operation,phase):
    import services.rvdb.delivery as delivery
    target,source=tmp_path/'active.json',tmp_path/'candidate.json'
    old,new=put(target,1),put(source,2)
    publish=delivery._publish
    def injected(path,payload,**kwargs):
        if (path==target) != (phase=='activation'):
            return publish(path,payload,**kwargs)
        with monkeypatch.context() as m:
            def fail(*args,**kwargs):raise OSError('injected '+operation)
            if operation in ('fsync','replace'):
                m.setattr(delivery.os,operation,fail)
            else:
                original=delivery.tempfile.NamedTemporaryFile
                class File:
                    def __init__(self,*a,**kw):self.inner=original(*a,**kw)
                    def __enter__(self):self.inner.__enter__();return self
                    def __exit__(self,*a):return self.inner.__exit__(*a)
                    def __getattr__(self,name):return fail if name==operation else getattr(self.inner,name)
                m.setattr(delivery.tempfile,'NamedTemporaryFile',File)
            return publish(path,payload,**kwargs)
    monkeypatch.setattr(delivery,'_publish',injected)
    with pytest.raises(OSError):install(source,target,new)
    assert target.read_bytes()==old
    assert not list(tmp_path.glob('.rvdb-stage-*'))

def test_first_install_has_no_rollback_and_external_update_is_protected(tmp_path):
    target,source=tmp_path/'active.json',tmp_path/'candidate.json'
    data=put(source,1);install(source,target,data)
    with pytest.raises(ValueError,match='No previous'):rollback_bundle(target)
    newer=put(source,2);install(source,target,newer)
    external=put(target,3)
    with pytest.raises(ValueError,match='outside'):rollback_bundle(target)
    assert target.read_bytes()==external

def test_invalid_candidate_and_symlink_destination_are_rejected(tmp_path):
    target,source=tmp_path/'active.json',tmp_path/'candidate.json'
    old=put(target,1);source.write_bytes(b'invalid')
    with pytest.raises(RVDBError):install(source,target,b'invalid')
    assert target.read_bytes()==old
    link=tmp_path/'link.json';link.symlink_to(target)
    new=put(source,2)
    with pytest.raises(ValueError,match='symlink'):install(source,link,new)
    assert target.read_bytes()==old


def test_explicit_rollback_recovers_corrupt_active_bundle(tmp_path):
    target,source=tmp_path/'active.json',tmp_path/'candidate.json'
    old,new=put(target,1),put(source,2);install(source,target,new)
    target.write_bytes(b'interrupted external write')
    assert rollback_bundle(target)==sha(old)
    assert target.read_bytes()==old


def test_concurrent_delivery_is_rejected(tmp_path):
    from services.rvdb.delivery import _locked
    target,source=tmp_path/'active.json',tmp_path/'candidate.json'
    old,new=put(target,1),put(source,2)
    with _locked(target):
        with pytest.raises(BlockingIOError):install(source,target,new)
    assert target.read_bytes()==old


def test_interruption_between_checkpoint_and_activation_is_recoverable(tmp_path,monkeypatch):
    import services.rvdb.delivery as delivery
    target,source=tmp_path/'active.json',tmp_path/'candidate.json'
    old,new=put(target,1),put(source,2)
    publish=delivery._publish
    def interrupt(path,payload,**kwargs):
        if path==target:raise KeyboardInterrupt('interrupted before activation')
        return publish(path,payload,**kwargs)
    with monkeypatch.context() as m:
        m.setattr(delivery,'_publish',interrupt)
        with pytest.raises(KeyboardInterrupt):install(source,target,new)
    assert target.read_bytes()==old
    assert rollback_bundle(target)==sha(old)
    assert install(source,target,new)==sha(new)
    assert rollback_bundle(target)==sha(old)


def test_invalid_update_preserves_existing_rollback_point(tmp_path):
    target,source=tmp_path/'active.json',tmp_path/'candidate.json'
    old,new=put(target,1),put(source,2);install(source,target,new)
    checkpoint=target.with_name(target.name+'.rollback.json');before=checkpoint.read_bytes()
    source.write_bytes(b'broken')
    with pytest.raises(RVDBError):install(source,target,b'broken')
    assert checkpoint.read_bytes()==before
    assert rollback_bundle(target)==sha(old)
