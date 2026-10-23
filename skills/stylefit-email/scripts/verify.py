"""Locate the installer-managed helper; never silently skip missing validation."""
import importlib.util
import json
import os
from pathlib import Path
import sys

arguments=sys.argv[1:]
if not arguments or arguments[0]!='verify':arguments=['verify',*arguments]
here=Path(__file__).resolve()
runtime=here.parents[3]/'runtime/bin/python'
if runtime.is_file():
    os.execv(str(runtime),[str(runtime),'-I','-m','ownvoice',*arguments])
checkout=here.parents[3]
if (checkout/'pyproject.toml').is_file() and (checkout/'ownvoice/cli.py').is_file():
    sys.path.insert(0,str(checkout))
if importlib.util.find_spec('ownvoice'):
    from ownvoice.cli import main
    raise SystemExit(main(arguments))
print(json.dumps({'status':'not_run','ready_for_delivery':False,'blocking_issues':['helper_unavailable'],
                  'verification_gaps':['Install the suite with --with-tools, or install its Python wheel in this interpreter.']}))
raise SystemExit(2)
