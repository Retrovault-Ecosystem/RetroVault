"""Ubuntu 26.04 x86-64 / Python 3.14 user-local release management.

Explicit local artifacts only. Never modifies XDG user data or emulator installs.
"""
import argparse
from contextlib import contextmanager
import fcntl
import gzip
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile

TARGET = {'distribution': 'ubuntu', 'version': '26.04', 'architecture': 'x86_64', 'python': '3.14'}
ROOTS = {'config','controllers','models','services','ui','retrovault','data','scripts'}
TOP = {'app.py','__init__.py','__main__.py','requirements.txt','README.md'}
MARKER = 'RetroVault user-local release root v1\n'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def safe_name(name):
    p=PurePosixPath(name)
    return bool(name) and not p.is_absolute() and '..' not in p.parts and str(p)==name and '\\' not in name


def release_id(value):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,79}',value) or value in ('.','..'):
        raise ValueError('Invalid release identifier')
    return value


def atomic(path,payload):
    temporary=None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.release-',delete=False) as f:
            temporary=Path(f.name);f.write(payload);f.flush();os.fsync(f.fileno())
        os.replace(temporary,path)
    finally:
        if temporary is not None:temporary.unlink(missing_ok=True)


def make_archive(files,output,release,provenance):
    release_id(release)
    if any(not safe_name(n) or n=='release.json' for n in files):raise ValueError('Invalid payload path')
    manifest={'format':1,'release':release,'target':TARGET,'provenance':provenance,
              'files':{n:sha(v) for n,v in sorted(files.items())}}
    content=dict(files,**{'release.json':(json.dumps(manifest,sort_keys=True,indent=2)+'\n').encode()})
    buffer=io.BytesIO()
    with gzip.GzipFile(fileobj=buffer,mode='wb',mtime=0,filename='') as gz:
        with tarfile.open(fileobj=gz,mode='w') as archive:
            for name,payload in sorted(content.items()):
                info=tarfile.TarInfo(name);info.size=len(payload);info.mode=0o644;info.mtime=0
                archive.addfile(info,io.BytesIO(payload))
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    atomic(output,buffer.getvalue())
    return sha(buffer.getvalue())


def read_archive(path,expected):
    data=Path(path).read_bytes()
    if not re.fullmatch('[0-9a-f]{64}',expected or '') or sha(data)!=expected:raise ValueError('Release checksum mismatch')
    files={}
    with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as archive:
        total=0
        for member in archive:
            total+=member.size
            if (not member.isfile() or not safe_name(member.name) or member.name in files
                    or total>1024**3):raise ValueError('Unsafe or oversized release archive')
            files[member.name]=archive.extractfile(member).read()
    manifest=json.loads(files.pop('release.json'))
    if manifest.get('format')!=1 or manifest.get('target')!=TARGET:raise ValueError('Unsupported release target/format')
    release_id(manifest['release'])
    if manifest.get('files')!={n:sha(v) for n,v in files.items()}:raise ValueError('Release inventory mismatch')
    return manifest,files


def build(repo,bundle,wheels,output,release,bundle_sha,producer_commit):
    repo=Path(repo).resolve()
    if not re.fullmatch('[0-9a-f]{40}',producer_commit):raise ValueError('Full producer commit required')
    payload=Path(bundle).read_bytes()
    if sha(payload)!=bundle_sha:raise ValueError('RVDB pin mismatch')
    from services.rvdb import RVDBService
    RVDBService.from_bundle(bundle)
    names=subprocess.check_output(['git','ls-files','-z'],cwd=repo).decode().split('\0')
    files={}
    for name in filter(None,names):
        if name in TOP or PurePosixPath(name).parts[0] in ROOTS:
            path=repo/name
            if path.is_symlink():raise ValueError('Source symlink not supported')
            files[name]=path.read_bytes()
    # Include this manager before its first publication; hash every packaged byte.
    files['scripts/linux_release.py']=Path(__file__).read_bytes()
    files['data/rvdb/rvdb.bundle.json']=payload
    for p in sorted(Path(wheels).glob('*.whl')):files['wheels/'+p.name]=p.read_bytes()
    if not any(n.startswith('wheels/') for n in files):raise ValueError('Offline wheels required')
    provenance={'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),
                'source_dirty':bool(subprocess.check_output(['git','status','--porcelain'],cwd=repo)),
                'rvdb_commit':producer_commit,'rvdb_sha256':bundle_sha}
    return make_archive(files,output,release,provenance)


def check_host():
    info=platform.freedesktop_os_release()
    if (info.get('ID')!='ubuntu' or info.get('VERSION_ID')!='26.04'
            or platform.machine()!='x86_64' or sys.version_info[:2]!=(3,14)):
        raise ValueError('Requires Ubuntu 26.04 x86-64 with Python 3.14')


def root_path(root):
    root=Path(root).expanduser().absolute()
    if root==Path.home() or root==Path('/') or any(p.is_symlink() for p in (root,*root.parents)):
        raise ValueError('Use a dedicated non-symlink installation directory')
    return root


@contextmanager
def owned_root(root,create=False):
    root=root_path(root)
    if create:
        root.mkdir(parents=True,exist_ok=True)
        if not (root/'.retrovault-release-root').exists():
            if list(root.iterdir()):raise ValueError('Installation directory must be empty or owned')
            atomic(root/'.retrovault-release-root',MARKER.encode())
    if (root/'.retrovault-release-root').is_symlink() or (root/'.retrovault-release-root').read_text()!=MARKER:
        raise ValueError('Not a managed installation')
    fd=os.open(root/'.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW,0o600)
    with os.fdopen(fd,'a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        yield root


def read_state(root):
    p=root/'state.json'
    if p.is_symlink():raise ValueError('Invalid state path')
    state=json.loads(p.read_text()) if p.exists() else {'current':None,'previous':None}
    for value in state.values():
        if value is not None:release_id(value)
    return state


def verify_version(directory):
    if directory.is_symlink():raise ValueError('Release directory must not be a symlink')
    manifest=json.loads((directory/'release.json').read_text())
    for name,digest in manifest['files'].items():
        if not safe_name(name):raise ValueError('Invalid installed path')
        p=directory/name
        if any(q.is_symlink() for q in (p,*p.parents)) or sha(p.read_bytes())!=digest:
            raise ValueError('Installed release differs from manifest: '+name)
    return manifest


def install(archive,expected,root):
    check_host();manifest,files=read_archive(archive,expected)
    required={'app.py','requirements.txt','data/rvdb/rvdb.bundle.json','scripts/check_startup.py'}
    if not required.issubset(files):raise ValueError('Incomplete application release')
    with owned_root(root,create=True) as root:
        state=read_state(root);versions=root/'releases'
        if versions.is_symlink():raise ValueError('Invalid releases directory')
        versions.mkdir(exist_ok=True);directory=versions/manifest['release']
        if directory.exists():raise ValueError('Release already installed; choose a new release ID')
        directory.mkdir()
        try:
            for name,payload in files.items():
                p=directory/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(payload)
            (directory/'release.json').write_text(json.dumps(manifest,sort_keys=True,indent=2)+'\n')
            subprocess.run([sys.executable,'-m','venv',str(directory/'.venv')],check=True)
            python=directory/'.venv/bin/python'
            subprocess.run([str(python),'-m','pip','install','--no-index','--no-cache-dir','--find-links',str(directory/'wheels'),'-r',str(directory/'requirements.txt')],check=True)
            with tempfile.TemporaryDirectory() as scratch:
                env=dict(os.environ,QT_QPA_PLATFORM='offscreen',PYTHONDONTWRITEBYTECODE='1')
                for k in ('CONFIG','CACHE','DATA','STATE'):env['XDG_'+k+'_HOME']=str(Path(scratch)/k.lower())
                subprocess.run([str(python),'-B','-m','scripts.check_startup'],cwd=directory,env=env,check=True)
                subprocess.run([str(python),'-c','from PyQt6.QtWidgets import QApplication; a=QApplication([]); from ui.main_window import MainWindow; w=MainWindow(); w.shutdown_runtime(); w.close()'],cwd=directory,env=env,check=True)
            verify_version(directory)
            launcher=('#!'+sys.executable+'\nimport json,os,pathlib\nr=pathlib.Path(__file__).resolve().parent\ns=json.loads((r/"state.json").read_text())\np=r/"releases"/s["current"]\nos.execv(str(p/".venv/bin/python"),[str(p/".venv/bin/python"),str(p/"app.py")])\n')
            atomic(root/'retrovault',launcher.encode());(root/'retrovault').chmod(0o755)
            atomic(root/'state.json',(json.dumps({'current':manifest['release'],'previous':state['current']})+'\n').encode())
        except BaseException:
            shutil.rmtree(directory)
            raise
    return manifest['release']


def rollback(root):
    with owned_root(root) as root:
        state=read_state(root)
        if not state['previous']:raise ValueError('No previous release')
        verify_version(root/'releases'/state['previous'])
        atomic(root/'state.json',(json.dumps({'current':state['previous'],'previous':None})+'\n').encode())
        return state['previous']


def remove(root):
    with owned_root(root) as root:
        versions=root/'releases'
        if versions.is_symlink():raise ValueError('Invalid releases directory')
        if versions.exists():
            for directory in versions.iterdir():verify_version(directory)
            for directory in versions.iterdir():shutil.rmtree(directory)
            versions.rmdir()
        for name in ('state.json','retrovault'): (root/name).unlink(missing_ok=True)
    # Keep marker/lock so removal retries are safe. User XDG data is never visited.


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('build');b.add_argument('--repo',default='.');b.add_argument('--bundle',required=True);b.add_argument('--wheels',required=True);b.add_argument('--output',required=True);b.add_argument('--release',required=True);b.add_argument('--bundle-sha',required=True);b.add_argument('--producer-commit',required=True)
    i=sub.add_parser('install');i.add_argument('archive');i.add_argument('--sha256',required=True);i.add_argument('--root',required=True)
    for name in ('rollback','remove'):
        sub.add_parser(name).add_argument('--root',required=True)
    args=vars(p.parse_args());command=args.pop('command')
    try:
        if command=='build':result=build(**args)
        elif command=='install':result=install(args['archive'],args['sha256'],args['root'])
        elif command=='rollback':result=rollback(args['root'])
        else:result=remove(args['root'])
    except (OSError,ValueError,KeyError,subprocess.SubprocessError,tarfile.TarError) as exc:p.exit(1,str(exc)+'\n')
    if result is not None:print(result)


if __name__=='__main__':main()
