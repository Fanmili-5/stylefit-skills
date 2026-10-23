"""Summarize saved Luna diagnostic artifacts without making new model calls."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3
import statistics

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.local/luna-v2'
ARMS = ('plain', 'checklist', 'ownvoice')


def read(path):
    return json.loads(path.read_text()) if path.exists() else None


def validate_judgment(value, mapping):
    """A partial/duplicated judge response must not silently become a ranking."""
    if not isinstance(value, dict) or not isinstance(value.get('cases'), list):
        return ['missing_cases']
    issues = []
    ids = [row.get('task_id') for row in value['cases'] if isinstance(row, dict)]
    if len(ids) != len(value['cases']) or Counter(ids) != Counter(mapping.keys()):
        issues.append('wrong_or_duplicate_task_ids')
    for case in value['cases']:
        if not isinstance(case, dict):
            issues.append('case_not_object')
            continue
        ratings = case.get('ratings')
        if not isinstance(ratings, list):
            issues.append('missing_ratings')
            continue
        labels = [row.get('label') for row in ratings if isinstance(row, dict)]
        if len(labels) != len(ratings) or Counter(labels) != Counter(('A', 'B', 'C')):
            issues.append('wrong_or_duplicate_labels')
        for row in ratings:
            if not isinstance(row, dict):
                issues.append('rating_not_object')
                continue
            for metric in ('fidelity', 'style_fit', 'clarity'):
                score = row.get(metric)
                if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 4:
                    issues.append('invalid_' + metric)
            if not isinstance(row.get('critical_errors'), list):
                issues.append('missing_critical_errors')
        if case.get('preferred_for_use') not in {'A', 'B', 'C', 'tie'}:
            issues.append('invalid_preference')
    return sorted(set(issues))


def summarize(phase):
    tasks = read(ROOT / 'evals/luna_v2/cases.json')[phase]
    cells, judgments = [], []
    for task in tasks:
        for arm in ARMS:
            prefix = f'luna-v2-{phase}-{task["id"]}-{arm}-'
            initial = prefix + 'initial'
            final = prefix + ('revision' if task['domain'] == 'code' else 'initial')
            result = read(LOCAL / 'runs' / final / 'result.json')
            before = read(LOCAL / 'assessments' / (initial + '.json'))
            after = read(LOCAL / 'assessments' / (final + '.json'))
            value = read(LOCAL / 'runs' / final / 'output.json')
            artifact_present = isinstance((value or {}).get('artifact'), str) and bool(value['artifact'].strip()) if task['domain'] != 'code' else None
            fact_issues = [issue for issue in (after or {}).get('issues', [])
                           if issue in {'missing_facts', 'unrequested_structured_fields'}
                           or issue.startswith('incorrect_') and not issue.startswith('incorrect_source_')]
            cells.append({'task_id': task['id'], 'domain': task['domain'], 'language': task['language'],
                          'arm': arm, 'status': (result or {}).get('status', 'missing'),
                          'initial_passed': (before or {}).get('passed'),
                          'final_passed': (after or {}).get('passed'),
                          'valid_json': (result or {}).get('valid_json'),
                          'required_artifact_present': artifact_present,
                          'research_fact_fields_passed': (isinstance(value, dict) and not fact_issues)
                              if task['domain'] == 'research' else None,
                          'assessment': after, 'selected_checks': (result or {}).get('selected_checks', [])})
    for path in sorted((LOCAL / 'grading-maps').glob(f'luna-v2-{phase}-judge-*.json')):
        mapping = read(path)
        value = read(LOCAL / 'runs' / path.stem / 'output.json')
        issues = validate_judgment(value, mapping)
        judgments.append({'id': path.stem, 'valid': not issues, 'issues': issues,
                          'cases': [] if issues else [
                              {**case, 'ratings': [{**row, 'arm': mapping[case['task_id']][row['label']]}
                                                  for row in case['ratings']],
                               'preferred_arm': ('tie' if case['preferred_for_use'] == 'tie'
                                                 else mapping[case['task_id']][case['preferred_for_use']])}
                              for case in value['cases']]})
    aggregates = {}
    for arm in ARMS:
        selected = [row for row in cells if row['arm'] == arm]
        runs = [read(path) for path in (LOCAL / 'runs').glob(f'luna-v2-{phase}-*-{arm}-*/result.json')]
        rated = [rating for judge in judgments for case in judge['cases']
                 for rating in case['ratings'] if rating['arm'] == arm]
        counts = Counter(row['preferred_arm'] for judge in judgments for row in judge['cases'])
        code = [row for row in selected if row['domain'] == 'code']
        usage = Counter()
        for run in runs:
            for event in run.get('usage', []):
                usage.update({key: value for key, value in event.items() if isinstance(value, (int, float))})
        aggregates[arm] = {
            'expected_cells': len(tasks), 'completed_cells': sum(row['status'] == 'completed' for row in selected),
            'frozen_strict_passes': sum(row['final_passed'] is True for row in selected),
            'invalid_json_cells': sum(row['valid_json'] is False for row in selected),
            'missing_required_artifact_cells': sum(row['required_artifact_present'] is False for row in selected),
            'research_fact_fields_passes': sum(row['research_fact_fields_passed'] is True for row in selected),
            'initial_code_passes': sum(row['initial_passed'] is True for row in code),
            'final_code_passes': sum(row['final_passed'] is True for row in code),
            'code_cells': len(code), 'rated_cells': len(rated), 'preferred_cells': counts[arm],
            'rating_means': {metric: statistics.mean(row[metric] for row in rated) if rated else None
                             for metric in ('fidelity', 'style_fit', 'clarity')},
            'critical_error_flags': sum(len(row['critical_errors']) for row in rated),
            'generation_cli_tasks': len(runs), 'reported_usage': dict(usage),
            'prompt_characters': sum(run.get('prompt_characters', 0) for run in runs),
            'artifact_characters': sum(run.get('artifact_characters', 0) for run in runs),
            'serial_seconds_sum': sum(run.get('seconds', 0) for run in runs)}
    return {'phase': phase, 'cells': cells, 'aggregates': aggregates, 'judgments': judgments,
            'judge_ties': sum(case['preferred_arm'] == 'tie' for judge in judgments for case in judge['cases'])}


def build(phases):
    with sqlite3.connect(ROOT / '.local/ledger.sqlite') as db:
        new = db.execute('SELECT COUNT(*) FROM jobs WHERE id LIKE "luna-v2-%"').fetchone()[0]
        total = db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
    routes = [read(path) for path in (LOCAL / 'runs').glob('*/result.json')]
    usage = Counter()
    for route in routes:
        for event in route.get('usage', []):
            usage.update({key: value for key, value in event.items() if isinstance(value, (int, float))})
    return {'scope': 'Synthetic small diagnostic; hard checks and same-family Luna ratings are separate.',
            'measurement_audit': 'luna-v2-measurement-audit.md; frozen strict text pass counts are not semantic accuracy',
            'new_tasks_started': new, 'new_cap': 60, 'lifetime_tasks_started': total, 'lifetime_cap': 240,
            'requested_models': dict(Counter(row.get('requested_model', 'missing') for row in routes)),
            'response_model_unreported_tasks': sum(not row.get('reported_models') for row in routes),
            'reported_usage_all_tasks': dict(usage),
            'runtime_failures': [str(path.parent.name) for path in (LOCAL / 'runs').glob('*/result.json')
                                 if read(path).get('status') == 'failed'],
            'phases': [summarize(phase) for phase in phases]}


def public_summary(report):
    """Release aggregates and per-cell status, excluding raw outputs and blind labels."""
    result = {key: value for key, value in report.items() if key != 'phases'}
    result['phases'] = []
    for phase in report['phases']:
        cells = [{key: value for key, value in row.items() if key != 'assessment'}
                 for row in phase['cells']]
        for cell, original in zip(cells, phase['cells']):
            score = original['assessment'] or {}
            cell['strict_issues'] = score.get('issues', [])
            if cell['domain'] == 'code':
                cell['finite_cases_passed'] = sum(row['passed'] for row in score.get('cases', []))
                cell['finite_cases_total'] = len(score.get('cases', []))
        judgments = []
        for judge in phase['judgments']:
            rows = []
            for case in judge['cases']:
                ratings = [{key: value for key, value in row.items() if key not in {'label', 'evidence'}}
                           for row in case['ratings']]
                ratings.sort(key=lambda row: ARMS.index(row['arm']))
                rows.append({'task_id': case['task_id'], 'ratings': ratings,
                             'preferred_arm': case['preferred_arm']})
            judgments.append({'valid': judge['valid'], 'issues': judge['issues'], 'cases': rows})
        result['phases'].append({**phase, 'cells': cells, 'judgments': judgments})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--phase', choices=['development', 'holdout', 'all'], default='all')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--public', action='store_true', help='omit raw assessment values and blinded labels')
    args = parser.parse_args()
    report = build(['development', 'holdout'] if args.phase == 'all' else [args.phase])
    if args.public:
        report = public_summary(report)
    text = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text)
        print(args.output)
    else:
        print(text)


if __name__ == '__main__':
    main()
