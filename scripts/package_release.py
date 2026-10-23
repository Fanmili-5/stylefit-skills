"""Build a reviewable archive from audited public candidates, excluding ignored files."""
import hashlib
import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--channel',choices=['candidate','release'],default='candidate')
    args=parser.parse_args()
    audit = subprocess.run([sys.executable, str(ROOT / 'scripts/release_audit.py'), '--json'],
                           cwd=ROOT, text=True, capture_output=True, check=True)
    files = json.loads(audit.stdout)['files']
    if any((ROOT / name).is_symlink() or not (ROOT / name).is_file() for name in files):
        raise SystemExit('Release candidates must be regular files, without symlinks')
    folder = ROOT / 'dist'
    folder.mkdir(exist_ok=True)
    version = re.search(r'^version = "([0-9A-Za-z.]+)"$', (ROOT / 'pyproject.toml').read_text(), re.M).group(1)
    if args.channel=='release':
        status=json.loads((ROOT/'reports/release-v02.json').read_text())
        if not status.get('release_gates_passed') or status.get('product_hashes')!=product_hashes():
            raise SystemExit('Release gates or tested product hashes do not match; retain candidate')
    destination = folder / ('ownvoice-skills-' + version + ('-candidate' if args.channel=='candidate' else '') + '.zip')
    wheels=list(folder.glob('ownvoice_skills-'+version+'-*.whl'))
    if len(wheels)!=1:raise SystemExit('Build exactly one matching helper wheel first')
    files=sorted(set(files+[str(wheels[0].relative_to(ROOT))]))
    manifest = {}
    with zipfile.ZipFile(destination, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in files:
            content = (ROOT / name).read_bytes()
            manifest[name] = hashlib.sha256(content).hexdigest()
            item = zipfile.ZipInfo('ownvoice-skills/' + name, date_time=(2026, 1, 1, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.external_attr = 0o100644 << 16
            archive.writestr(item, content)
        archive.writestr('ownvoice-skills/RELEASE-MANIFEST.json',
                         json.dumps(manifest, indent=2) + '\n')
    digest = hashlib.sha256(destination.read_bytes()).hexdigest()
    destination.with_suffix('.zip.sha256').write_text(digest + '  ' + destination.name + '\n')
    print(json.dumps({'archive': str(destination), 'public_files': len(files), 'sha256': digest}))


def product_hashes():
    files=[]
    for name in ('skills','ownvoice'):
        files.extend(p for p in (ROOT/name).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    files.extend(ROOT/name for name in ('pyproject.toml','requirements-runtime.lock','scripts/install.py'))
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


if __name__ == '__main__':
    main()
