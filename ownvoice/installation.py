"""Versioned local installs, with one current link shared by all four skills."""
import hashlib
import json
import os
import re
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

NAMES = tuple('ownvoice-' + domain for domain in ('code','email','profile','research'))


def release_name(value):
    if not isinstance(value,str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._+-]*',value):
        raise ValueError('Invalid release identifier')
    return value


def hashes(folder):
    result = {}
    for path in sorted(folder.rglob('*')):
        if path.is_symlink(): raise ValueError('Source bundles may not contain symlinks')
        if path.is_file() and '__pycache__' not in path.parts:
            result[str(path.relative_to(folder))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def atomic_json(path, value):
    temporary = path.with_name(path.name + '.new')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    os.replace(temporary, path)


def alias_target(destination, name):
    return os.path.relpath(destination.parent / '.ownvoice/current/skills' / name, destination)


def check_aliases(destination, allow_missing=True):
    for name in NAMES:
        target = destination / name
        if target.is_symlink():
            if os.readlink(target) != alias_target(destination, name):
                raise ValueError('Unmanaged existing skill: ' + str(target))
        elif target.exists():
            raise ValueError('Existing user directory is never overwritten: ' + str(target))
        elif not allow_missing:
            raise ValueError('Managed skill link is missing: ' + str(target))


def current_release(base):
    link = base / 'current'
    if not link.is_symlink():
        if link.exists():raise ValueError('Current release must be an installer-owned link')
        return None
    target = os.readlink(link)
    if Path(target).is_absolute() or len(Path(target).parts) != 2 or Path(target).parts[0] != 'releases' or '..' in Path(target).parts:
        raise ValueError('Invalid managed current link')
    return release_name(Path(target).name)


def check_release(folder):
    if folder.is_symlink():raise ValueError('Managed release directories cannot be symlinks')
    manifest_path = folder / 'install-manifest.json'
    if not manifest_path.is_file():raise ValueError('Missing managed release manifest')
    manifest = json.loads(manifest_path.read_text())
    if manifest.get('owner') != 'ownvoice-installer/1':raise ValueError('Unmanaged release')
    if hashes(folder/'skills') != manifest['skills']:
        raise ValueError('Installed skills were modified; preserve them before upgrading or rollback')
    return manifest


def make_runtime(folder, wheel, lock, wheelhouse=None):
    subprocess.run([sys.executable, '-m', 'venv', str(folder)], check=True, capture_output=True)
    command = [str(folder/'bin/python'), '-m', 'pip', 'install', '--disable-pip-version-check', '-r', str(lock), str(wheel)]
    if wheelhouse:command += ['--no-index','--find-links',str(wheelhouse)]
    result = subprocess.run(command, text=True, capture_output=True)
    if result.returncode:raise RuntimeError('Helper installation failed: ' + result.stderr[-1600:])
    test = subprocess.run([str(folder/'bin/python'), '-I', '-c', 'import ownvoice, jsonschema; from ownvoice.cli import main'], capture_output=True, text=True)
    if test.returncode:raise RuntimeError('Installed helper could not be imported: ' + test.stderr[-1000:])


def switch(base, release):
    temporary = base / 'current.new'
    if temporary.exists() or temporary.is_symlink():temporary.unlink()
    temporary.symlink_to('releases/' + release)
    os.replace(temporary, base/'current')


def managed_install(source_root, destination, version, wheel=None, with_tools=False,
                    upgrade=False, dry_run=False, wheelhouse=None, runtime_factory=make_runtime):
    source_root = Path(source_root).resolve(); destination = Path(destination).expanduser().absolute()
    release_name(version)
    base = destination.parent / '.ownvoice'
    if destination.is_symlink() or base.is_symlink():raise ValueError('Install roots cannot be symlinks')
    check_aliases(destination)
    sources = source_root / 'skills'
    if {p.name for p in sources.iterdir() if p.is_dir()} != set(NAMES):raise ValueError('Bundle must contain exactly four skills')
    skill_hashes = hashes(sources)
    lock = source_root/'requirements-runtime.lock'
    if with_tools and (not wheel or not Path(wheel).is_file() or not lock.is_file()):
        raise ValueError('A built wheel and runtime lock are required for --with-tools')
    wheel_hash = hashlib.sha256(Path(wheel).read_bytes()).hexdigest() if with_tools else None
    lock_hash = hashlib.sha256(lock.read_bytes()).hexdigest() if with_tools else None
    identity = hashlib.sha256(json.dumps([version,skill_hashes,wheel_hash,lock_hash],sort_keys=True).encode()).hexdigest()[:16]
    release = version + '-' + identity
    old = current_release(base)
    if old:
        check_release(base/'releases'/old)
        if old != release and not upgrade:raise ValueError('Different installed version; use --upgrade')
    plan = {'destination':str(destination),'release':release,'previous':old,'with_tools':with_tools,'dry_run':dry_run}
    if dry_run:return plan
    destination.mkdir(parents=True,exist_ok=True);(base/'releases').mkdir(parents=True,exist_ok=True)
    folder = base/'releases'/release;created=[];built=False
    if folder.exists():
        manifest=check_release(folder)
        if manifest['skills'] != skill_hashes or manifest['wheel_sha256'] != wheel_hash:raise ValueError('Release collision')
    else:
        folder.mkdir();built=True
        try:
            shutil.copytree(sources,folder/'skills',ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
            if with_tools:runtime_factory(folder/'runtime',Path(wheel).resolve(),lock.resolve(),wheelhouse)
            atomic_json(folder/'install-manifest.json',{'owner':'ownvoice-installer/1','version':version,
                        'skills':skill_hashes,'wheel_sha256':wheel_hash,'lock_sha256':lock_hash,'with_tools':with_tools})
        except BaseException:
            shutil.rmtree(folder)
            raise
    try:
        for name in NAMES:
            target=destination/name
            if not target.is_symlink():
                target.symlink_to(alias_target(destination,name),target_is_directory=True);created.append(target)
        switch(base,release)
        old_state=json.loads((base/'state.json').read_text()) if (base/'state.json').exists() else {}
        atomic_json(base/'state.json',{'owner':'ownvoice-installer/1','current':release,
                    'previous':old if old != release else old_state.get('previous'),'installed':True})
    except BaseException:
        if old:switch(base,old)
        elif (base/'current').is_symlink():(base/'current').unlink()
        for target in created:
            if target.is_symlink() and os.readlink(target)==alias_target(destination,target.name):target.unlink()
        if built:shutil.rmtree(folder)
        raise
    return plan


def rollback(destination, dry_run=False):
    destination=Path(destination).expanduser().absolute();base=destination.parent/'.ownvoice'
    check_aliases(destination,False)
    state=json.loads((base/'state.json').read_text());old=current_release(base)
    previous=state.get('previous')
    if state.get('owner')!='ownvoice-installer/1' or not previous or state.get('current')!=old:
        raise ValueError('No consistent previous managed version')
    release_name(previous)
    check_release(base/'releases'/old);check_release(base/'releases'/previous)
    if not dry_run:
        switch(base,previous)
        atomic_json(base/'state.json',{'owner':'ownvoice-installer/1','current':previous,'previous':old,'installed':True})
    return {'current':previous,'previous':old,'dry_run':dry_run}


def uninstall(destination, dry_run=False):
    destination=Path(destination).expanduser().absolute();base=destination.parent/'.ownvoice'
    check_aliases(destination,False)
    current=current_release(base)
    if not current:raise ValueError('No managed installation')
    check_release(base/'releases'/current)
    if not dry_run:
        for name in NAMES:(destination/name).unlink()
        state=json.loads((base/'state.json').read_text());state['installed']=False
        atomic_json(base/'state.json',state)
    return {'removed_aliases':list(NAMES),'cached_releases_preserved':True,'dry_run':dry_run}
