"""Report aggregate technical counts without copying prompts or personal content."""
from collections import defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def aggregate(rows, tasks):
    task_lookup = {task['id']: task for group in tasks.values() for task in group}
    groups = defaultdict(lambda: {'tasks': 0, 'completed': 0, 'failed': 0,
                                 'started': 0, 'constraint_passed': 0,
                                 'constraint_failed': 0, 'reported_models': set()})
    for identifier, stage, runtime, status, result in rows:
        data = json.loads(result) if result else {}
        prefix = stage + '-' + runtime + '-'
        job = identifier[len(prefix):].removesuffix('-retry1')
        task_id, condition = job.rsplit('-', 1)
        task = task_lookup.get(task_id, {})
        key = (stage, runtime, task.get('domain', 'readiness'),
               task.get('language', 'none'), task.get('mode', 'none'), condition)
        group = groups[key]
        group['tasks'] += 1
        group[status] += 1
        if status == 'completed':
            group['constraint_passed' if data.get('checks', {}).get('passed')
                  else 'constraint_failed'] += 1
        group['reported_models'].update(data.get('reported_models', []))
    keys = ('stage', 'runtime', 'domain', 'language', 'mode', 'condition')
    return [{**dict(zip(keys, key)), **{k: sorted(v) if isinstance(v, set) else v
                                      for k, v in group.items()}}
            for key, group in sorted(groups.items())]


def main():
    with sqlite3.connect(ROOT / '.local/ledger.sqlite') as db:
        rows = db.execute('SELECT id,stage,runtime,status,result FROM jobs').fetchall()
    tasks = json.loads((ROOT / 'evals/tasks.json').read_text())
    groups = aggregate(rows, tasks)
    recheck_path = ROOT / '.local/development-recheck.json'
    recheck = json.loads(recheck_path.read_text()) if recheck_path.exists() else None
    result = {
        'generated_at_utc': datetime.now(timezone.utc).isoformat(),
        'status': 'technical preview; personal preference not measured',
        'generation_tasks_used': len(rows), 'generation_task_cap': 180,
        'groups': groups,
        'development_checker_correction': {
            'occurred_before_formal_freeze': True,
            'reason': 'Sentence-final punctuation caused false added-number flags.',
            'original_passed': recheck.get('original_passed') if recheck else None,
            'rechecked_passed': recheck.get('rechecked_passed') if recheck else None,
            'total': recheck.get('total') if recheck else None,
            'new_generation_tasks': 0,
            'original_ledger_results_preserved': True,
        } if recheck else None,
        'human_preference_evaluation': 'not_measured',
        'semantic_fidelity': 'not_established_by_automated_text_checks',
        'code_coverage': 'Finite fixtures; exception messages and arbitrary inputs are not comprehensively checked.',
        'automatic_host_skill_routing': 'not_tested_by_prompt_loaded_benchmark',
        'authorship_detection': 'not_tested',
        'model_identity': 'CLI response model IDs only; an empty list means unreported, not a verified model identity.',
        'scope': 'Synthetic fixtures; one preference participant; only runtimes that passed preflight ran the matrix.',
    }
    folder = ROOT / 'reports'
    folder.mkdir(exist_ok=True)
    (folder / 'technical-status.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'generation_tasks_used': len(rows), 'groups': len(groups),
                      'report': 'reports/technical-status.json'}))


if __name__ == '__main__':
    main()
