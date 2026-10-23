import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('report', ROOT / 'scripts/report.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ReportTests(unittest.TestCase):
    def test_failures_and_retries_remain_in_denominator(self):
        result = json.dumps({'checks': {'passed': True}, 'reported_models': []})
        rows = [('main-codex-task-ownvoice', 'main', 'codex', 'failed', '{}'),
                ('main-codex-task-ownvoice-retry1', 'main', 'codex', 'completed', result),
                ('main-codex-task-upstream', 'main', 'codex', 'completed',
                 json.dumps({'checks': {'passed': False}}))]
        tasks = {'main': [{'id': 'task', 'domain': 'email', 'language': 'zh', 'mode': 'rewrite'}]}
        groups = module.aggregate(rows, tasks)
        ownvoice = next(group for group in groups if group['condition'] == 'ownvoice')
        self.assertEqual(ownvoice['tasks'], 2)
        self.assertEqual(ownvoice['failed'], 1)
        self.assertEqual(ownvoice['constraint_passed'], 1)
        self.assertEqual(ownvoice['reported_models'], [])
        self.assertEqual(next(group for group in groups if group['condition'] == 'upstream')['constraint_failed'], 1)


if __name__ == '__main__':
    unittest.main()
