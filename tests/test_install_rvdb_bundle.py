"""Exercise actual CLI process statuses without modifying the installed bundle."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]

def cli(*args):
    return subprocess.run([sys.executable,'-m','scripts.install_rvdb_bundle',*map(str,args)],cwd=ROOT,capture_output=True,text=True)

def test_cli_pinned_install_and_offline_rollback(tmp_path):
    source,target=tmp_path/'candidate.json',tmp_path/'active.json'
    old=b'{"nodes": {}, "edges": {}}'
    target.write_bytes(old)
    new=json.dumps({'nodes':{},'edges':{}},indent=2).encode();source.write_bytes(new)
    digest=hashlib.sha256(new).hexdigest()
    result=cli(source,'--destination',target,'--expected-sha256',digest,'--producer-commit','a'*40)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()==digest
    source.unlink()
    result=cli('--rollback','--destination',target)
    assert result.returncode==0,result.stderr
    assert target.read_bytes()==old

@pytest.mark.parametrize('case',['missing-pin','wrong-hash','invalid','missing-backup'])
def test_cli_failures_are_nonzero_and_preserve_active(tmp_path,case):
    source,target=tmp_path/'candidate.json',tmp_path/'active.json'
    old=b'{"nodes": {}, "edges": {}}';target.write_bytes(old)
    payload=b'broken' if case=='invalid' else old;source.write_bytes(payload)
    args=[str(source),'--destination',str(target)]
    if case=='missing-backup':args=['--rollback','--destination',str(target)]
    elif case!='missing-pin':args+=['--expected-sha256','0'*64 if case=='wrong-hash' else hashlib.sha256(payload).hexdigest(),'--producer-commit','a'*40]
    assert cli(*args).returncode!=0
    assert target.read_bytes()==old
