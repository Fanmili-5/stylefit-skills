"""Two exploratory role-binding checks; shares the original capped ledger."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts'))
import evaluate as base
from ownvoice.checks import check_text


def main():
    folder = ROOT / '.local/email-v011'
    folder.mkdir(exist_ok=True)
    files = [Path(__file__).resolve(), ROOT / 'scripts/evaluate.py', ROOT / 'ownvoice/checks.py',
             ROOT / 'evals/email_v011/cases.json', ROOT / 'evals/email_v011/PROTOCOL.md',
             ROOT / 'skills/ownvoice-email/SKILL.md']
    config = Path.home() / '.codex/config.toml'
    hashes = {str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
    hashes['runtime_config'] = hashlib.sha256(config.read_bytes()).hexdigest() if config.exists() else None
    manifest = folder / 'frozen.json'
    if manifest.exists():
        if json.loads(manifest.read_text()) != hashes:
            raise RuntimeError('Smoke inputs changed; do not overwrite the original freeze')
    else:
        manifest.write_text(json.dumps(hashes, indent=2) + '\n')
    guide = (ROOT / 'skills/ownvoice-email/SKILL.md').read_text()
    cases = json.loads((ROOT / 'evals/email_v011/cases.json').read_text())
    for task in cases:
        identifier = 'email-v011-codex-' + task['id']
        if not base.reserve(identifier, 'email-v011-smoke', 'codex'):
            continue
        run = ROOT / '.local/runs' / identifier
        run.mkdir(parents=True, exist_ok=True)
        payload = {key: value for key, value in task.items() if key != 'synthetic'}
        prompt = ('This is a text-only draft task; no tools or external actions. '
                  'Task facts and constraints override style. Output only the email draft, '
                  'without preamble or check report.\nSTYLE GUIDE\n' + guide +
                  '\nTASK\n' + json.dumps(payload, ensure_ascii=False))
        (run / 'prompt.txt').write_text(prompt)
        started = time.monotonic()
        try:
            with tempfile.TemporaryDirectory(prefix='ownvoice-email-smoke-') as cwd:
                process = subprocess.run(base.command('codex', prompt), cwd=cwd,
                                         env=base.runtime_environment('codex'), text=True,
                                         capture_output=True, timeout=120)
            (run / 'stdout.txt').write_text(base.redact(process.stdout))
            (run / 'stderr.txt').write_text(base.redact(process.stderr))
            if process.returncode:
                raise RuntimeError('CLI exit ' + str(process.returncode))
            artifact, models = base.extract('codex', process.stdout)
            artifact = artifact.strip()
            (run / 'artifact.txt').write_text(artifact)
            result = {'status': 'completed', 'case_id': task['id'], 'candidate': 'email-0.1.1',
                      'reported_models': models, 'checks': check_text(task, artifact),
                      'scope': 'Exploratory two-case smoke; no baseline or improvement claim.'}
        except Exception as error:
            result = {'status': 'failed', 'case_id': task['id'], 'error_type': type(error).__name__}
        result['seconds'] = time.monotonic() - started
        (run / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
        base.finish(identifier, result)
        if result['status'] == 'failed':
            raise SystemExit('Smoke CLI failed; no retry budget remains')


if __name__ == '__main__':
    main()
