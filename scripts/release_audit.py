"""Audit the intended public file set without including ignored private artifacts."""
import argparse
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
FORBIDDEN={'.local','.env','.venv','__pycache__'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--json',action='store_true')
    args=parser.parse_args()
    manifest=json.loads((ROOT/'release-files.json').read_text())
    if manifest.get('schema_version')!=1 or not isinstance(manifest.get('files'),list):
        raise SystemExit('An explicit release-files.json is required')
    files=manifest['files']
    issues=[]
    if len(set(files))!=len(files):issues.append(['release-files.json','duplicate paths'])
    for relative in files:
        path=Path(relative)
        if path.is_absolute() or '..' in path.parts or not relative or not (ROOT/path).is_file():
            issues.append([relative,'invalid or missing release path']);continue
        if any((ROOT/Path(*path.parts[:index])).is_symlink() for index in range(1,len(path.parts)+1)):
            issues.append([relative,'symlink path']);continue
        if any(part in FORBIDDEN or part.startswith('.env.') for part in path.parts):
            issues.append([relative,'private/build path'])
        if path.suffix.lower() in {'.npz','.pt','.pth','.ckpt','.sqlite'}:
            issues.append([relative,'model/database artifact'])
        text=(ROOT/path).read_text(encoding='utf-8',errors='replace')
        if re.search(r'\bsk-[A-Za-z0-9_-]{20,}',text): issues.append([relative,'possible credential'])
        if re.search(r'/Users/[A-Za-z0-9_.-]+/',text): issues.append([relative,'machine-specific absolute path'])
    result={'files':sorted(files),'issues':issues,'passed':not issues,
            'scope':'Explicit reviewed file list plus regular-file and credential/path probes; not a universal secret detector.'}
    print(json.dumps(result,ensure_ascii=False,indent=2) if args.json else
          json.dumps({'files':len(files),'issues':issues,'passed':not issues}))
    raise SystemExit(0 if not issues else 1)


if __name__=='__main__': main()
