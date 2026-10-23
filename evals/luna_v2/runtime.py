"""Luna-only task execution and append-only accounting for the authorized extension."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / '.local/luna-v2'
MODEL = 'gpt-6-luna'
EFFORT = 'medium'
spec = importlib.util.spec_from_file_location('legacy_cli_helpers', ROOT / 'scripts/evaluate.py')
legacy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(legacy)


def command(prompt):
    args = legacy.command('codex', prompt)
    args[2:2] = ['--model', MODEL, '-c', 'model_reasoning_effort=' + EFFORT]
    if args.count('--model') != 1 or args[args.index('--model') + 1] != MODEL:
        raise RuntimeError('Luna-only model guard failed')
    return args


def reserve(identifier, stage):
    if not identifier.startswith('luna-v2-'):
        raise ValueError('Invalid new-round identifier')
    authorization = json.loads((LOCAL / 'authorization.json').read_text())
    if authorization['required_model'] != MODEL or authorization['additional_task_cap'] != 60:
        raise RuntimeError('The authorized model/budget does not match this runner')
    with sqlite3.connect(ROOT / '.local/ledger.sqlite', timeout=20) as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT 1 FROM jobs WHERE id=?', (identifier,)).fetchone():
            return False
        new = db.execute('SELECT COUNT(*) FROM jobs WHERE id LIKE "luna-v2-%"').fetchone()[0]
        total = db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
        if new >= authorization['additional_task_cap'] or total >= authorization['lifetime_task_cap']:
            raise RuntimeError('Authorized extension budget exhausted; never reset the ledger')
        db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?)',
                   (identifier, stage, 'codex-gpt-6-luna', 'started', time.time(), None, None))
    return True


def run(identifier, stage, prompt, metadata=None, timeout=180):
    if not reserve(identifier, stage):
        path = LOCAL / 'runs' / identifier / 'result.json'
        return json.loads(path.read_text()) if path.exists() else {'status': 'started'}
    folder = LOCAL / 'runs' / identifier
    folder.mkdir(parents=True, exist_ok=True)
    (folder / 'prompt.txt').write_text(prompt)
    args = command(prompt)
    # Save routing/arguments without duplicating the potentially long prompt.
    (folder / 'invocation.json').write_text(json.dumps({'argv_without_prompt': args[:-1],
                                                       'requested_model': MODEL,
                                                       'reasoning_effort': EFFORT}, indent=2) + '\n')
    started = time.monotonic()
    result = {'requested_model': MODEL, 'reasoning_effort': EFFORT, **(metadata or {})}
    try:
        with tempfile.TemporaryDirectory(prefix='ownvoice-luna-v2-') as cwd:
            process = subprocess.run(args, cwd=cwd, env=legacy.runtime_environment('codex'),
                                     text=True, capture_output=True, timeout=timeout)
        (folder / 'stdout.jsonl').write_text(legacy.redact(process.stdout))
        (folder / 'stderr.txt').write_text(legacy.redact(process.stderr))
        if process.returncode:
            raise RuntimeError('CLI exit ' + str(process.returncode))
        artifact, reported = legacy.extract('codex', process.stdout)
        if any(model != MODEL and not model.startswith(MODEL + '-') for model in reported):
            raise RuntimeError('Response reported a non-Luna model; stop without fallback')
        artifact = artifact.strip()
        if artifact.startswith('```') and artifact.endswith('```'):
            artifact = '\n'.join(artifact.splitlines()[1:-1])
        (folder / 'artifact.txt').write_text(artifact)
        usage = []
        for line in process.stdout.splitlines():
            try: event = json.loads(line)
            except ValueError: continue
            if isinstance(event.get('usage'), dict): usage.append(event['usage'])
        result.update(status='completed', reported_models=reported, usage=usage,
                      identity_evidence='explicit CLI model selection; response model unreported' if not reported else 'explicit CLI selection plus response model metadata',
                      prompt_characters=len(prompt), artifact_characters=len(artifact),
                      artifact_sha256=hashlib.sha256(artifact.encode()).hexdigest())
        if stage != 'luna-v2-preflight':
            try:
                output = json.loads(artifact)
                if not isinstance(output, dict): raise ValueError('Expected an object')
                (folder / 'output.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
                result['valid_json'] = True
            except ValueError:
                result['valid_json'] = False
        else:
            result['ready'] = artifact == 'READY'
    except Exception as error:
        result.update(status='failed', error_type=type(error).__name__,
                      error='CLI timeout' if isinstance(error, subprocess.TimeoutExpired) else legacy.redact(str(error))[:500])
    result['seconds'] = time.monotonic() - started
    (folder / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    with sqlite3.connect(ROOT / '.local/ledger.sqlite') as db:
        db.execute('UPDATE jobs SET status=?,finished=?,result=? WHERE id=?',
                   (result['status'], time.time(), json.dumps(result), identifier))
        used = db.execute('SELECT COUNT(*) FROM jobs WHERE id LIKE "luna-v2-%"').fetchone()[0]
    print(json.dumps({'job': identifier, 'new_used': used, 'new_cap': 60,
                      **{key: result.get(key) for key in ('status','requested_model','reported_models','ready','valid_json','seconds')}}, ensure_ascii=False), flush=True)
    return result


def preflight():
    result = run('luna-v2-preflight', 'luna-v2-preflight',
                 'Reply exactly READY. Do not call tools, inspect files, or take external actions.')
    if result.get('status') != 'completed' or not result.get('ready'):
        raise SystemExit('Luna preflight failed; no alternate model is permitted')


if __name__ == '__main__':
    preflight()
