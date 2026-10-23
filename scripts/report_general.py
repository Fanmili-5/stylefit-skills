"""Aggregate general-use diagnostics; keep raw artifacts and review notes private."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def collect():
    with sqlite3.connect(ROOT / '.local/ledger.sqlite') as db:
        rows = db.execute('SELECT id,stage,status,result FROM jobs WHERE stage LIKE "general-v1-%"').fetchall()
        used = db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
    records = []
    for identifier, stage, status, result in rows:
        records.append({'job_id': identifier, 'stage': stage.removeprefix('general-v1-'),
                        'status': status, **(json.loads(result) if result else {})})
    return used, records


def build_report(used, records):
    allocation = []
    for stage, expected in (('preflight', 1), ('development', 36), ('conflicts', 6), ('holdout', 36)):
        selected = [row for row in records if row['stage'] == stage]
        allocation.append({'stage': stage, 'expected': expected, 'reserved': len(selected),
                           'completed': sum(row['status'] == 'completed' for row in selected),
                           'cli_failed': sum(row['status'] == 'failed' for row in selected),
                           'inflight': sum(row['status'] == 'started' for row in selected),
                           'not_started': max(0, expected - len(selected))})
    groups = defaultdict(lambda: {'started': 0, 'completed': 0, 'cli_failed': 0,
                                  'content_passed': 0, 'content_failed': 0,
                                  'style_probe_passed': 0, 'style_probe_failed': 0,
                                  'style_not_scored': 0})
    failures = []
    pending = []
    models = set()
    by_case = defaultdict(dict)
    for row in records:
        if row['stage'] == 'preflight':
            continue
        if row['status'] == 'started':
            pending.append({'job_id': row['job_id'], 'stage': row['stage']})
            continue
        key = tuple(row.get(field) for field in ('stage', 'condition', 'profile', 'domain', 'language'))
        group = groups[key]
        group['started'] += 1
        models.update(row.get('reported_models', []))
        if row['status'] != 'completed':
            group['cli_failed'] += row['status'] == 'failed'
            continue
        group['completed'] += 1
        assessment = row['checks']
        group['content_passed' if assessment['passed'] else 'content_failed'] += 1
        style = assessment['style'].get('passed')
        group['style_not_scored' if style is None else 'style_probe_passed' if style else 'style_probe_failed'] += 1
        if not assessment['passed'] or style is False:
            failures.append({'case_id': row['case_id'], 'stage': row['stage'], 'condition': row['condition'],
                             'profile': row['profile'], 'content_passed': assessment['passed'],
                             'style_probes': assessment['style'].get('probes'),
                             'style_metrics': assessment['style'].get('metrics'),
                             'content_check': assessment.get('content') if not assessment['passed'] else None})
        artifact = ROOT / '.local/runs' / row['job_id'] / 'artifact.txt'
        row = {**row, 'artifact_sha256': hashlib.sha256(artifact.read_bytes()).hexdigest()}
        by_case[(row['stage'], row['case_id'], row['condition'])][row['profile']] = row
    contrasts = []
    method_pairs = defaultdict(dict)
    for (stage, case_id, condition), profiles in sorted(by_case.items()):
        if not {'compact', 'expanded'} <= profiles.keys():
            continue
        compact, expanded = profiles['compact'], profiles['expanded']
        contrasts.append({'stage': stage, 'case_id': case_id, 'condition': condition,
                          'both_content_passed': compact['checks']['passed'] and expanded['checks']['passed'],
                          'both_style_probes_passed': compact['checks']['style']['passed'] and expanded['checks']['style']['passed'],
                          'identical_artifacts': compact['artifact_sha256'] == expanded['artifact_sha256']})
    for (stage, case_id, condition), profiles in by_case.items():
        for profile, row in profiles.items():
            method_pairs[(stage, case_id, profile)][condition] = row
    comparisons = []
    for (stage, case_id, profile), methods in sorted(method_pairs.items()):
        if not {'plain', 'ownvoice'} <= methods.keys():
            continue
        plain, ownvoice = methods['plain'], methods['ownvoice']
        comparisons.append({'stage': stage, 'case_id': case_id, 'profile': profile,
                            'plain_content_passed': plain['checks']['passed'],
                            'ownvoice_content_passed': ownvoice['checks']['passed'],
                            'plain_style_passed': plain['checks']['style']['passed'],
                            'ownvoice_style_passed': ownvoice['checks']['style']['passed'],
                            'identical_artifacts': plain['artifact_sha256'] == ownvoice['artifact_sha256']})
    review_path = ROOT / '.local/general-v1/manual-review.json'
    reviews = json.loads(review_path.read_text()) if review_path.exists() else []
    known = {row['job_id']: row for row in records if row['status'] == 'completed' and row['stage'] != 'preflight'}
    ids = [review['job_id'] for review in reviews]
    if len(ids) != len(set(ids)) or set(ids) - known.keys():
        raise ValueError('Manual review has duplicate or unknown job IDs')
    review_counts = defaultdict(lambda: {'supported_by_packet': 0, 'regression': 0, 'unclear': 0})
    for review in reviews:
        if review['fidelity'] not in {'supported_by_packet', 'regression', 'unclear'}:
            raise ValueError('Invalid manual review status')
        row = known[review['job_id']]
        review_counts[(row['stage'], row['condition'], row['domain'])][review['fidelity']] += 1
    return {
        'evaluation': 'general-v1', 'ledger_used': used, 'ledger_cap': 180,
        'candidate_scope': 'Each v1 phase uses its saved skill snapshot. Later working-tree changes and separate smoke checks are excluded.',
        'generation_tasks_new': len(records), 'allocation': allocation,
        'pending_reservations': pending,
        'participant_profile_loaded': False, 'runtime': 'codex', 'reported_models': sorted(models),
        'model_identity': 'Empty reported_models means unreported; no model-family claim.',
        'groups': [dict(zip(('stage', 'condition', 'profile', 'domain', 'language'), key), **value)
                   for key, value in sorted(groups.items())],
        'failed_checks': failures, 'profile_contrasts': contrasts, 'method_comparisons': comparisons,
        'manual_review': {'reviewer': 'implementing assistant; not independent or blinded',
                          'reviewed': len(reviews), 'completed_artifacts': len(known),
                          'groups': [{'stage': key[0], 'condition': key[1], 'domain': key[2], **value}
                                     for key, value in sorted(review_counts.items())]},
        'limits': ['Constructed preferences and synthetic tasks are not real multi-user evidence.',
                   'Style probes measure selected instruction adherence, not preference satisfaction or quality.',
                   'Text markers and internal review do not establish complete semantic equivalence.',
                   'Fresh ephemeral tool-disabled prompts do not test automatic routing or stateful user isolation.',
                   'Held-out tasks share the authored task family; no new-domain generalization claim.'],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review-stage', choices=['development', 'conflicts', 'holdout'])
    args = parser.parse_args()
    used, records = collect()
    report = build_report(used, records)
    folder = ROOT / 'reports'
    folder.mkdir(exist_ok=True)
    (folder / 'general-v1.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    if args.review_stage:
        data = json.loads((ROOT / 'evals/general_v1/cases.json').read_text())
        task_lookup = {task['id']: task for group in ('development', 'holdout', 'conflicts') for task in data[group]}
        packet = []
        for row in records:
            if row['stage'] == args.review_stage and row['status'] == 'completed':
                task = task_lookup[row['case_id']]
                packet.append({**row, 'task': task['packet'], 'source': task.get('source'),
                               'artifact': (ROOT / '.local/runs' / row['job_id'] / 'artifact.txt').read_text()})
        destination = ROOT / '.local/general-v1' / ('review-' + args.review_stage + '.json')
        destination.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + '\n')
    totals = defaultdict(lambda: {'completed': 0, 'content_passed': 0, 'style_passed': 0})
    for row in report['groups']:
        total = totals[(row['stage'], row['condition'])]
        total['completed'] += row['completed']
        total['content_passed'] += row['content_passed']
        total['style_passed'] += row['style_probe_passed']
    print(json.dumps({'ledger_used': used, 'totals': [{'stage': key[0], 'condition': key[1], **value}
                                                    for key, value in sorted(totals.items())]}, ensure_ascii=False))


if __name__ == '__main__':
    main()
