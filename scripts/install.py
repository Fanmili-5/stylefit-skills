"""Copy the four skills into a host skill directory; never overwrite different files."""
import argparse
from pathlib import Path
import shutil
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from ownvoice import __version__
from ownvoice.installation import managed_install, rollback, uninstall


def install(destination):
    destination=Path(destination).expanduser()
    sources=sorted((ROOT/'skills').iterdir())
    pending=[]
    for source in sources:
        target=destination/source.name
        if target.exists():
            old={p.relative_to(target):p.read_bytes() for p in target.rglob('*') if p.is_file()}
            new={p.relative_to(source):p.read_bytes() for p in source.rglob('*') if p.is_file()}
            if old!=new:
                raise ValueError('Existing different skill; nothing overwritten: '+str(target))
        else:
            pending.append((source,target))
    # Detect every collision before making any change.
    for source,target in pending:
        shutil.copytree(source,target)
    return [str(destination/source.name) for source in sources]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host',choices=['codex','claude'])
    parser.add_argument('--dest',type=Path)
    parser.add_argument('--with-tools',action='store_true')
    parser.add_argument('--wheel',type=Path)
    parser.add_argument('--wheelhouse',type=Path)
    parser.add_argument('--upgrade',action='store_true')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--rollback',action='store_true')
    parser.add_argument('--uninstall',action='store_true')
    args=parser.parse_args()
    if not args.dest and not args.host: parser.error('--host or --dest required')
    destination=args.dest or Path.home()/('.agents' if args.host=='codex' else '.claude')/'skills'
    if args.rollback and args.uninstall:parser.error('Choose rollback or uninstall')
    if args.rollback:result=rollback(destination,args.dry_run)
    elif args.uninstall:result=uninstall(destination,args.dry_run)
    else:
        wheels=sorted((ROOT/'dist').glob('ownvoice_skills-'+__version__+'-*.whl'))
        wheel=args.wheel or (wheels[0] if len(wheels)==1 else None)
        result=managed_install(ROOT,destination,__version__,wheel,args.with_tools,args.upgrade,args.dry_run,args.wheelhouse)
    import json
    print(json.dumps(result,indent=2))


if __name__=='__main__': main()
