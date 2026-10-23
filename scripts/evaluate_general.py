"""General-use diagnostics using the existing shared 180-task ledger."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from threading import Event
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
import evaluate as base

CASE_DIR = ROOT / 'evals/general_v1'
LOCAL = ROOT / '.local/general-v1'
spec = importlib.util.spec_from_file_location('general_checks', CASE_DIR / 'checks.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dependencies():
    paths = [Path(__file__).resolve(), ROOT / 'scripts/evaluate.py', ROOT / 'ownvoice/checks.py']
    paths += sorted(CASE_DIR.glob('*.py')) + [CASE_DIR / 'cases.json', CASE_DIR / 'PROTOCOL.md']
    return {str(path.relative_to(ROOT)): digest(path) for path in paths}


def config_hashes():
    path = Path.home() / '.codex/config.toml'
    return {'codex_config': digest(path) if path.exists() else None}


def skill_hashes(folder):
    return {str(path.relative_to(folder)): digest(path) for path in sorted(folder.rglob('*'))
            if path.is_file() and '__pycache__' not in path.parts}


def freeze(phase):
    folder = LOCAL / phase
    manifest_path = folder / 'frozen.json'
    if manifest_path.exists():
        assert_frozen(phase)
        print('Existing general-use freeze unchanged: ' + phase)
        return
    folder.mkdir(parents=True, exist_ok=True)
    snapshot = folder / 'skills'
    shutil.copytree(ROOT / 'skills', snapshot)
    manifest = {'phase': phase, 'dependencies': dependencies(), 'runtime': config_hashes(),
                'skills': skill_hashes(snapshot), 'created_utc_seconds': time.time(),
                'participant_profile_loaded': False}
    manifest_path.write_text(json.dumps(manifest, indent=2) + '\n')
    print(json.dumps({'frozen_phase': phase, 'participant_profile_loaded': False}))


def assert_frozen(phase):
    folder = LOCAL / phase
    manifest = json.loads((folder / 'frozen.json').read_text())
    if (manifest['dependencies'] != dependencies() or manifest['runtime'] != config_hashes()
            or manifest['skills'] != skill_hashes(folder / 'skills')):
        raise RuntimeError('General-use frozen inputs changed; stop rather than silently re-freeze')


def make_prompt(task, profile, condition, phase, cases):
    if condition == 'plain':
        guide = 'Produce clear, natural code or prose. Follow supplied preferences where consistent with task constraints.'
    else:
        folder = LOCAL / phase / 'skills' / ('ownvoice-' + task['domain'])
        guide = (folder / 'SKILL.md').read_text()
        guide += '\n' + '\n'.join(path.read_text() for path in sorted((folder / 'references').glob('*.md')))
    prompt = ('This is a text-only artifact task. Do not call tools, access files, or take external actions. '
              'Task facts, mandatory format and public API contracts override style preferences. '
              'Output only the requested artifact, without a code fence, preamble or check report. '
              'Use Chinese prose/comments for zh and English for en; preserve fixed identifiers. ')
    if task['domain'] == 'code':
        prompt += ('Output only synchronous Python function definitions, without imports, classes, decorators '
                   'or introspection. Do not mutate inputs. ')
    prompt += '\nSTYLE GUIDE\n' + guide
    if profile != 'none':
        preferences = ([task['conflicting_preference']] if profile == 'conflict'
                       else cases['profiles'][profile][task['domain']])
        prompt += '\nPROFILE\n' + json.dumps({'basis': 'synthetic_preferences', 'preferences': preferences})
    payload = {key: value for key, value in task.items()
               if key not in {'tests', 'reference', 'synthetic', 'style_anchors', 'conflicting_preference'}}
    return prompt + '\nTASK\n' + json.dumps(payload, ensure_ascii=False)


def run_job(stage, task, profile, condition, phase, cases, stop, timeout):
    if stop.is_set():
        return
    assert_frozen(phase)
    identifier = '-'.join(['general-v1', stage, 'codex', task['id'], profile, condition])
    if not base.reserve(identifier, 'general-v1-' + stage, 'codex'):
        return
    folder = ROOT / '.local/runs' / identifier
    folder.mkdir(parents=True, exist_ok=True)
    prompt = ('Reply exactly READY. Do not call tools or take any actions.' if stage == 'preflight'
              else make_prompt(task, profile, condition, phase, cases))
    (folder / 'prompt.txt').write_text(prompt)
    started = time.monotonic()
    result = {'case_id': task['id'], 'profile': profile, 'condition': condition,
              'phase': phase, 'domain': task.get('domain'), 'language': task.get('language'),
              'participant_profile_loaded': False}
    try:
        with tempfile.TemporaryDirectory(prefix='ownvoice-general-') as cwd:
            process = subprocess.run(base.command('codex', prompt), cwd=cwd,
                                     env=base.runtime_environment('codex'), text=True,
                                     capture_output=True, timeout=timeout)
        (folder / 'stdout.txt').write_text(base.redact(process.stdout))
        (folder / 'stderr.txt').write_text(base.redact(process.stderr))
        if process.returncode:
            raise RuntimeError('CLI exit ' + str(process.returncode))
        artifact, models = base.extract('codex', process.stdout)
        artifact = artifact.strip()
        if artifact.startswith('```') and artifact.endswith('```'):
            artifact = '\n'.join(artifact.splitlines()[1:-1])
        (folder / 'artifact.txt').write_text(artifact)
        assessment = {'passed': artifact == 'READY'} if stage == 'preflight' else checks.assess(task, artifact, profile)
        result.update(status='completed', seconds=time.monotonic() - started,
                      reported_models=models, checks=assessment)
        if stage == 'preflight' and not assessment['passed']:
            stop.set()
    except Exception as error:
        stop.set()
        result.update(status='failed', seconds=time.monotonic() - started,
                      error_type=type(error).__name__,
                      error='CLI timeout' if isinstance(error, subprocess.TimeoutExpired)
                      else base.redact(str(error))[:500])
        if isinstance(error, subprocess.TimeoutExpired):
            for name, value in [('stdout.txt', error.stdout), ('stderr.txt', error.stderr)]:
                if value:
                    if isinstance(value, bytes): value = value.decode(errors='replace')
                    (folder / name).write_text(base.redact(value))
    (folder / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    base.finish(identifier, result)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--freeze', choices=['development', 'holdout'])
    parser.add_argument('--stage', choices=['preflight', 'development', 'conflicts', 'holdout'])
    parser.add_argument('--workers', type=int, choices=[1, 2], default=2)
    parser.add_argument('--timeout', type=int, default=120)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if args.freeze:
        freeze(args.freeze)
        return
    if not args.stage:
        parser.error('--stage or --freeze is required')
    phase = 'holdout' if args.stage == 'holdout' else 'development'
    assert_frozen(phase)
    cases = json.loads((CASE_DIR / 'cases.json').read_text())
    if args.stage == 'preflight':
        jobs = [({'id': 'ready'}, 'none', 'plain')]
    else:
        with base.connect() as db:
            rows = db.execute('SELECT result FROM jobs WHERE stage=? AND status="completed"',
                              ('general-v1-preflight',)).fetchall()
        if not any(json.loads(row[0]).get('checks', {}).get('passed') for row in rows):
            raise RuntimeError('New general-use preflight has not passed')
        if args.stage == 'conflicts':
            jobs = [(task, 'conflict', condition) for task in cases['conflicts']
                    for condition in ('plain', 'ownvoice')]
        else:
            jobs = [(task, profile, condition) for task in cases[args.stage]
                    for profile in ('none', 'compact', 'expanded') for condition in ('plain', 'ownvoice')]
    if args.dry_run:
        print(json.dumps({'stage': args.stage, 'tasks': len(jobs), 'participant_profile_loaded': False}))
        return
    stop = Event()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(lambda job: run_job(args.stage, *job, phase, cases, stop, args.timeout), jobs))
    if stop.is_set():
        raise SystemExit('Runtime failure stopped scheduling; unfinished cells remain missing')


if __name__ == '__main__':
    main()
