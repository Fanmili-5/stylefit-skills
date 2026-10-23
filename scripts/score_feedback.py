"""Score the private blind review; do not publish participant notes or mapping."""
import argparse
from collections import defaultdict
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
METRICS = ('style', 'clarity', 'use')


def score(feedback, mapping, tasks):
    if feedback.get('schema_version') != 1 or not isinstance(feedback.get('answers'), list):
        raise ValueError('Expected a version 1 feedback export')
    answers = feedback['answers']
    ids = [row['id'] for row in mapping]
    answer_ids = [row.get('id') for row in answers]
    if len(ids) != len(set(ids)) or len(answer_ids) != len(set(answer_ids)):
        raise ValueError('Duplicate pair IDs')
    if not ids or set(answer_ids) != set(ids):
        raise ValueError('Feedback must contain exactly the pairs in the private mapping')
    by_id = {row['id']: row for row in answers}
    task_lookup = {task['id']: task for task in tasks}
    groups = defaultdict(lambda: {metric: {'win': 0, 'tie': 0, 'loss': 0}
                                  for metric in METRICS})
    comparisons = defaultdict(lambda: {metric: {'win': 0, 'tie': 0, 'loss': 0}
                                       for metric in METRICS})
    for pair in mapping:
        other = pair['other']
        if other not in {'plain', 'upstream', 'mismatch'}:
            raise ValueError('Unknown comparison condition')
        if {pair['left'], pair['right']} != {'ownvoice', other}:
            raise ValueError('Invalid comparison mapping')
        task = task_lookup[pair['task']]
        key = (other, pair['runtime'], task['domain'], task['language'])
        answer = by_id[pair['id']]
        for metric in METRICS:
            choice = answer.get(metric)
            if choice not in {'left', 'right', 'tie'}:
                raise ValueError('Every pair needs all three ratings, including ties')
            outcome = 'tie' if choice == 'tie' else 'win' if pair[choice] == 'ownvoice' else 'loss'
            groups[key][metric][outcome] += 1
            comparisons[other][metric][outcome] += 1
    runtimes = sorted({pair['runtime'] for pair in mapping})
    baseline_count = 3 if len(runtimes) == 1 else 6
    required = {'plain': (baseline_count, 2 if baseline_count == 3 else 4),
                'upstream': (baseline_count, 2 if baseline_count == 3 else 4),
                'mismatch': (6, 4)}
    if len(runtimes) not in {1, 2} or set(comparisons) != set(required):
        raise ValueError('Mapping does not match the frozen pilot design')
    gates = {}
    for other, (expected, minimum_wins) in required.items():
        counts = comparisons[other]['use']
        if sum(counts.values()) != expected:
            raise ValueError('Unexpected pair count for ' + other)
        gates[other] = {'pairs': expected, 'minimum_wins': minimum_wins,
                        'passed': counts['win'] >= minimum_wins}
    return {
        'scope': 'One-participant preference pilot; no population or significance claim.',
        'primary_metric': 'willingness to use', 'runtimes': runtimes,
        'comparisons': dict(comparisons),
        'groups': [{'comparison': key[0], 'runtime': key[1], 'domain': key[2],
                    'language': key[3], 'ratings': ratings}
                   for key, ratings in sorted(groups.items())],
        'pilot_gates': gates,
        'preference_gate_passed': all(gate['passed'] for gate in gates.values()),
        'release_readiness': 'Preference counts alone do not establish content fidelity or release readiness.',
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('feedback', type=Path)
    parser.add_argument('--mapping', type=Path, default=ROOT / '.local/blind-mapping.json')
    parser.add_argument('--output', type=Path, default=ROOT / '.local/preference-report.json')
    args = parser.parse_args()
    result = score(json.loads(args.feedback.read_text()), json.loads(args.mapping.read_text()),
                   json.loads((ROOT / 'evals/tasks.json').read_text())['main'])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({'pairs': len(json.loads(args.mapping.read_text())),
                      'preference_gate_passed': result['preference_gate_passed'],
                      'report': str(args.output)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
