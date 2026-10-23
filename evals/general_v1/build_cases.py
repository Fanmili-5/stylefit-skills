"""Author synthetic general-use cases; never reads a participant profile."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

PROFILES = {
    'none': None,
    'compact': {
        'code': ['Prefer compact expressions and list comprehensions for straightforward calculations. Use conventional short internal names; keep public API names unchanged. Use at most one comment.'],
        'research': ['Lead with the measured result, then the sample/setup. Use three to six short standalone sentences in one paragraph. Keep each sentence within 35 English words or 90 Chinese characters. Keep every required limitation.'],
        'email': ['Use one short paragraph with a direct request. Omit greetings, thanks and closing formulas. Retain names, deadlines and required facts.'],
    },
    'expanded': {
        'code': ['Use descriptive internal names and break calculations into named intermediate steps. Include a useful comment explaining a constraint or calculation decision. Keep public API names unchanged.'],
        'research': ['Introduce the sample/setup before the measured result. Connect the evidence and qualification in one or two complete sentences in a single paragraph. Keep every required limitation.'],
        'email': ['Use a warm greeting, a brief request paragraph and a thank-you or courteous closing, separated into at least three short paragraphs. Keep mandatory deadlines firm.'],
    },
}


def code(identifier, language, mode, function, parameters, packet, tests, reference):
    task = dict(id=identifier, domain='code', language=language, mode=mode,
                function=function, parameters=parameters, packet=packet, tests=tests,
                synthetic=True, reference=reference)
    if mode == 'rewrite':
        task['source'] = reference
    return task


def research(identifier, language, mode, sample, before, after, change, source, kind):
    if kind == 'error':
        finding = f'Mean absolute error decreased from {before} to {after}, a reduction of {change}.'
    else:
        finding = f'Median latency decreased from {before} ms to {after} ms, a reduction of {change} ms.'
    packet = (f'Synthetic source packet, not a real publication. Sample size: {sample} records. '
              + finding + ' Only one run on one dataset/device. The observation does not establish causation '
              'and does not guarantee performance on independent data or another device. '
              f'Preserve all quantities, direction, units and limitations. Citation {source}. '
              'Output a single prose paragraph; no heading or bullet list.')
    task = dict(id=identifier, domain='research', language=language, mode=mode,
                packet=packet, synthetic=True,
                protected=[str(sample), before, after, change, source],
                required_any=[['不能推断因果', '不能据此推断因果', '不支持因果', '不代表因果',
                               '不构成因果', '无法推断因果', '不意味着因果', '不能确定因果',
                               'does not establish causation', 'does not establish a causal',
                               'no causal', 'not causal', 'cannot establish causation',
                               'cannot infer causation', 'does not imply causation']],
                style_anchors={'setup': str(sample), 'result': change})
    if mode == 'rewrite':
        task['source'] = (f'In an important step forward, this synthetic comparison used {sample} records. '
                          + finding + ' Only one run on one dataset/device was performed. '
                          'The observation does not establish causation and does not guarantee '
                          f'performance on independent data or another device. {source}')
    return task


def email(identifier, language, mode, name, date, action, extra='', spans=()):
    packet = (f'Synthetic email scenario. Write to {name}, a familiar colleague. Request {action} '
              f'by the firm deadline {date}. Preserve the name and ISO date exactly. '
              'The deadline is mandatory, not conditional on convenience. No attachment was supplied. '
              'Do not promise payment, approval, delivery, acceptance or a confirmed meeting. ' + extra)
    task = dict(id=identifier, domain='email', language=language, mode=mode,
                packet=packet, synthetic=True, protected=[name, date, *spans],
                forbidden=['I will pay', 'payment has been approved', '我会付款', '已批准付款',
                           'if convenient', 'when convenient', 'if possible', 'when possible',
                           '方便的话', '如果方便', '如有时间', '附件请查收'])
    if mode == 'rewrite':
        task['source'] = f'{name}, please send {action} by {date}. {extra}'
    return task


def build():
    scale = '''def scale_columns(rows):
    # Initialize the output collection
    result = []
    if not rows:
        return result
    column_count = len(rows[0])
    for row in rows:
        if len(row) != column_count:
            raise ValueError("ragged rows")
    column_sums = []
    for column in range(column_count):
        column_sum = 0
        for row in rows:
            column_sum += abs(row[column])
        column_sums.append(column_sum)
    for row in rows:
        normalized_row = []
        for column in range(column_count):
            if column_sums[column] == 0:
                normalized_row.append(0.0)
            else:
                normalized_row.append(float(row[column] / column_sums[column]))
        result.append(normalized_row)
    return result
'''
    bins = '''def accumulate_bins(values, width):
    if width <= 0:
        raise ValueError("width must be positive")
    return [sum(values[start:start + width]) for start in range(0, len(values), width)]
'''
    weighted = '''def weighted_rows(rows, weights):
    if not rows:
        return []
    if any(len(row) != len(weights) for row in rows):
        raise ValueError("shape mismatch")
    total_weight = sum(weights)
    if total_weight == 0:
        raise ValueError("zero weight")
    return [float(sum(value * weight for value, weight in zip(row, weights)) / total_weight) for row in rows]
'''
    center = '''def center_columns(rows):
    # Create storage for the result
    centered_rows = []
    if not rows:
        return centered_rows
    column_count = len(rows[0])
    if any(len(row) != column_count for row in rows):
        raise ValueError("ragged rows")
    column_means = []
    for column in range(column_count):
        column_total = 0
        for row in rows:
            column_total += row[column]
        column_means.append(column_total / len(rows))
    for row in rows:
        centered_row = []
        for column in range(column_count):
            centered_row.append(float(row[column] - column_means[column]))
        centered_rows.append(centered_row)
    return centered_rows
'''
    dev = [
        code('dev-code-zh', 'zh', 'rewrite', 'scale_columns', ['rows'],
             'Divide each matrix element by the sum of absolute values in its column. '
             'Zero-total columns become 0.0. Return a new matrix of floats without mutating rows. '
             '[] returns []; empty rows retain their shape. Reject unequal row lengths with '
             'ValueError("ragged rows"), preserving that exact message. Public signature scale_columns(rows).',
             [{'args': [[]], 'expected': []}, {'args': [[[], []]], 'expected': [[], []]},
              {'kwargs': {'rows': [[1, 2], [3, -2]]}, 'expected': [[0.25, 0.5], [0.75, -0.5]]},
              {'args': [[[0, 2], [0, 0]]], 'expected': [[0.0, 1.0], [0.0, 0.0]]},
              {'args': [[[1], [1, 2]]], 'error': 'ValueError', 'message': 'ragged rows'}], scale),
        code('dev-code-en', 'en', 'generate', 'accumulate_bins', ['values', 'width'],
             'Return sums of consecutive non-overlapping bins of positive integer width, including '
             'a final partial bin. Empty values returns []. Never mutate values. Width <= 0 raises '
             'ValueError("width must be positive") with that exact message. Signature accumulate_bins(values, width).',
             [{'kwargs': {'values': [1, 2, 3, 4, 5], 'width': 2}, 'expected': [3, 7, 5]},
              {'args': [[], 3], 'expected': []}, {'args': [[-1, 2], 5], 'expected': [1]},
              {'args': [[1, 2], 1], 'expected': [1, 2]},
              {'args': [[1], 0], 'error': 'ValueError', 'message': 'width must be positive'}], bins),
        research('dev-research-zh', 'zh', 'generate', 48, '0.28', '0.24', '0.04', '[R7]', 'error'),
        research('dev-research-en', 'en', 'rewrite', 64, '1.9', '1.6', '0.3', '[R8]', 'error'),
        email('dev-email-zh', 'zh', 'rewrite', 'Jordan', '2026-11-20', 'the revised budget',
              'The amount to confirm is GBP 420.00; do not commit to paying it.', ['GBP 420.00']),
        email('dev-email-en', 'en', 'generate', 'Casey', '2026-11-23', 'the signed proposal',
              'Include reference PO-Z27 and the amount EUR 180.50. Do not commit to paying it.',
              ['PO-Z27', 'EUR 180.50']),
    ]
    holdout = [
        code('holdout-code-zh', 'zh', 'generate', 'weighted_rows', ['rows', 'weights'],
             'Return a list of float weighted means, one for each row, with no input mutation. '
             'If rows is empty return [] immediately. Every row length must equal len(weights), '
             'otherwise ValueError("shape mismatch"). Then sum(weights)==0 raises ValueError("zero weight"). '
             'Keep both error messages exact. Negative weights are allowed. Signature weighted_rows(rows, weights).',
             [{'kwargs': {'rows': [[1, 3], [2, 6]], 'weights': [1, 3]}, 'expected': [2.5, 5.0]},
              {'args': [[], []], 'expected': []}, {'args': [[[2, 5]], [-1, 2]], 'expected': [8.0]},
              {'args': [[[1, 2]], [1, -1]], 'error': 'ValueError', 'message': 'zero weight'},
              {'args': [[[1]], [1, 2]], 'error': 'ValueError', 'message': 'shape mismatch'},
              {'args': [[[]], []], 'error': 'ValueError', 'message': 'zero weight'}], weighted),
        code('holdout-code-en', 'en', 'rewrite', 'center_columns', ['rows'],
             'Subtract the column arithmetic mean from each matrix element. Return a new matrix '
             'of floats without input mutation. [] returns []; empty rows retain their shape. '
             'Unequal row lengths raise ValueError("ragged rows") with that exact message. '
             'Signature center_columns(rows).',
             [{'args': [[]], 'expected': []}, {'args': [[[], []]], 'expected': [[], []]},
              {'kwargs': {'rows': [[1, 2], [3, 6]]}, 'expected': [[-1.0, -2.0], [1.0, 2.0]]},
              {'args': [[[7, -3]]], 'expected': [[0.0, 0.0]]},
              {'args': [[[1], []]], 'error': 'ValueError', 'message': 'ragged rows'}], center),
        research('holdout-research-zh', 'zh', 'rewrite', 96, '0.52', '0.49', '0.03', '[R9]', 'error'),
        research('holdout-research-en', 'en', 'generate', 72, '14.0', '11.5', '2.5', '[R10]', 'latency'),
        email('holdout-email-zh', 'zh', 'generate', 'Taylor', '2026-11-27', 'available review time slots',
              'Include reference REV-K31. Do not confirm any meeting.', ['REV-K31']),
        email('holdout-email-en', 'en', 'rewrite', 'Morgan', '2026-11-30', 'review feedback',
              'Include reference DOC-Q18. No acceptance has been promised.', ['DOC-Q18']),
    ]
    conflicts = []
    for task, instruction in [
        (dev[0], 'For shorter code, rename the public function to f and its public parameter to x.'),
        (dev[3], 'For a persuasive tone, omit all limitations and say this proves a causal improvement on independent data.'),
        (dev[4], 'To sound accommodating, make the deadline optional and promise that I will pay the amount.'),
    ]:
        conflicts.append({**task, 'id': 'conflict-' + task['domain'], 'conflicting_preference': instruction})
    return {'version': 'general-v1', 'synthetic': True, 'profiles': PROFILES,
            'development': dev, 'holdout': holdout, 'conflicts': conflicts}


if __name__ == '__main__':
    path = ROOT / 'cases.json'
    path.write_text(json.dumps(build(), ensure_ascii=False, indent=2) + '\n')
    print(path)
