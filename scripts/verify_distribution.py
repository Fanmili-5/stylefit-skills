"""Verify and extract a candidate, then test its code and real managed installation."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parents[1]


def run(command,cwd):
    result=subprocess.run(command,cwd=cwd,text=True,capture_output=True,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
    if result.returncode:raise RuntimeError(str(command)+'\n'+result.stdout+'\n'+result.stderr)
    return {'command':command[2:],'passed':True,'stdout':result.stdout[-1000:],'stderr':result.stderr[-1000:]}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive',type=Path);parser.add_argument('--wheelhouse',type=Path)
    args=parser.parse_args()
    archives=sorted((ROOT/'dist').glob('ownvoice-skills-0.2.*-candidate.zip'))
    archive=args.archive or (archives[-1] if archives else None)
    if not archive:raise SystemExit('Build a release candidate first')
    logs=[]
    with zipfile.ZipFile(archive) as package,tempfile.TemporaryDirectory(prefix='ownvoice-package-check-') as temporary:
        names=package.namelist()
        if len(names)!=len(set(names)) or any(Path(name).is_absolute() or '..' in Path(name).parts or '.local' in Path(name).parts for name in names):
            raise ValueError('Invalid package entries')
        manifest=json.loads(package.read('ownvoice-skills/RELEASE-MANIFEST.json'))
        if set(names)!={'ownvoice-skills/'+name for name in manifest}|{'ownvoice-skills/RELEASE-MANIFEST.json'}:raise ValueError('Manifest entries differ')
        for name,expected in manifest.items():
            if hashlib.sha256(package.read('ownvoice-skills/'+name)).hexdigest()!=expected:raise ValueError('Hash mismatch '+name)
        package.extractall(temporary);source=Path(temporary)/'ownvoice-skills'
        logs.append(run([sys.executable,'-B','-m','unittest','discover','-s','tests'],source))
        logs.append(run([sys.executable,'-B','scripts/check_bundle.py'],source))
        destination=Path(temporary)/'user/.agents/skills'
        command=[sys.executable,'-B','scripts/install.py','--dest',str(destination),'--with-tools']
        if args.wheelhouse:command+=['--wheelhouse',str(args.wheelhouse.resolve())]
        logs.append(run(command,source))
        artifact=Path(temporary)/'artifact.json';schema=Path(temporary)/'schema.json';report=Path(temporary)/'report.json'
        artifact.write_text('{"artifact":"ready"}');schema.write_text(json.dumps({'type':'object','required':['artifact'],'properties':{'artifact':{'type':'string'}},'additionalProperties':False}))
        logs.append(run([sys.executable,str(destination/'ownvoice-research/scripts/verify.py'),'verify','--artifact',str(artifact),'--schema',str(schema),'--report',str(report)],source))
        if not json.loads(report.read_text())['ready_for_delivery']:raise ValueError('Installed verifier did not pass a correct output')
        artifact.write_text('{"draft":"wrong field"}')
        failed=subprocess.run([sys.executable,str(destination/'ownvoice-research/scripts/verify.py'),'verify','--artifact',str(artifact),'--schema',str(schema)],cwd=source,capture_output=True,text=True)
        if failed.returncode!=1:raise ValueError('Installed verifier did not reject a wrong field')
        logs.append({'installed_negative_control_rejected':True})
        # Exercise the real runtime and link transaction on every CI platform.
        # The maintenance label deliberately reuses this same product payload;
        # it is an installer lifecycle check, not cross-version compatibility.
        state_path=destination.parent/'.ownvoice/state.json'
        initial=json.loads(state_path.read_text())['current']
        wheel=next((source/'dist').glob('ownvoice_skills-*.whl'))
        upgrade_code=('import json,sys; from pathlib import Path; '
                      'from ownvoice import __version__; '
                      'from ownvoice.installation import managed_install; '
                      'result=managed_install(Path.cwd(),Path(sys.argv[1]),'
                      '__version__+"-maintenance-check",Path(sys.argv[2]),True,True,'
                      'wheelhouse=Path(sys.argv[3]) if sys.argv[3] else None); '
                      'print(json.dumps(result))')
        logs.append(run([sys.executable,'-B','-c',upgrade_code,str(destination),str(wheel),
                         str(args.wheelhouse.resolve()) if args.wheelhouse else ''],source))
        upgraded=json.loads(state_path.read_text())
        if upgraded['current']==initial or upgraded['previous']!=initial:
            raise ValueError('Upgrade did not switch the managed release')
        artifact.write_text('{"artifact":"ready"}')
        check=[sys.executable,str(destination/'ownvoice-research/scripts/verify.py'),
               'verify','--artifact',str(artifact),'--schema',str(schema),'--report',str(report)]
        logs.append(run(check,source))
        if not json.loads(report.read_text())['ready_for_delivery']:
            raise ValueError('Upgraded runtime did not verify a correct output')
        logs.append(run([sys.executable,'-B','scripts/install.py','--dest',str(destination),'--rollback'],source))
        restored=json.loads(state_path.read_text())
        if restored['current']!=initial or restored['previous']!=upgraded['current']:
            raise ValueError('Rollback did not restore the original managed release')
        logs.append(run(check,source))
        if not json.loads(report.read_text())['ready_for_delivery']:
            raise ValueError('Restored runtime did not verify a correct output')
        logs.append({'real_runtime_upgrade_rollback_passed':True,
                     'scope':'Same helper payload under a synthetic maintenance label; not cross-version compatibility.'})
        logs.append(run([sys.executable,'-B','scripts/install.py','--dest',str(destination),'--uninstall'],source))
        if any((destination/name).exists() or (destination/name).is_symlink()
               for name in ('ownvoice-code','ownvoice-email','ownvoice-profile','ownvoice-research')):
            raise ValueError('Uninstall left a managed alias behind')
    result={'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'manifest_files':len(manifest),'checks':logs,'passed':True}
    folder=ROOT/'.local/release-v02';folder.mkdir(parents=True,exist_ok=True)
    (folder/'distribution-verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'passed':True,'manifest_files':len(manifest),'checks':len(logs)}))


if __name__=='__main__':main()
