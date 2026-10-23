"""Offline verification entry point; no model, network or repair operations."""
import argparse
import json
from pathlib import Path
import sys
from .verification import ContractError, parse_json, verify


def main(argv=None):
    parser = argparse.ArgumentParser(prog='ownvoice')
    commands = parser.add_subparsers(dest='command', required=True)
    check = commands.add_parser('verify')
    check.add_argument('--artifact', type=Path, required=True)
    check.add_argument('--schema', type=Path)
    check.add_argument('--constraints', type=Path)
    check.add_argument('--report', type=Path)
    args = parser.parse_args(argv)
    try:
        schema = parse_json(args.schema.read_text()) if args.schema else None
        constraints = parse_json(args.constraints.read_text()) if args.constraints else None
        result = verify(args.artifact.read_text(), schema, constraints)
        code = 0 if result['ready_for_delivery'] else 1
    except (OSError, ValueError, ImportError) as error:
        result = {'schema_version':1,'status':'not_run','ready_for_delivery':False,
                  'checks':[],'blocking_issues':['contract_or_environment_error'],
                  'verification_gaps':[str(error)],'error_type':type(error).__name__}
        code = 2
    encoded = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if args.report:
        if args.report.resolve() in {p.resolve() for p in (args.artifact, args.schema, args.constraints) if p}:
            print('Report must not overwrite input files', file=sys.stderr)
            return 2
        try:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(encoded)
        except OSError as error:
            print(str(error), file=sys.stderr)
            return 2
    print(encoded, end='')
    return code
