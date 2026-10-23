import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('feedback', ROOT / 'scripts/score_feedback.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class FeedbackTests(unittest.TestCase):
    def fixture(self):
        mapping = []
        for condition, count in [('plain', 3), ('upstream', 3), ('mismatch', 6)]:
            for index in range(count):
                mapping.append({'id': str(len(mapping)), 'task': 'task', 'runtime': 'codex',
                                'other': condition, 'left': condition if index % 2 else 'ownvoice',
                                'right': 'ownvoice' if index % 2 else condition})
        answers = [{'id': pair['id'], **{key: 'right' if pair['right'] == 'ownvoice' else 'left'
                                       for key in module.METRICS}} for pair in mapping]
        tasks = [{'id': 'task', 'domain': 'code', 'language': 'en'}]
        return {'schema_version': 1, 'answers': answers}, mapping, tasks

    def test_mapping_decodes_both_sides_and_preserves_ties(self):
        feedback, mapping, tasks = self.fixture()
        feedback['answers'][0]['style'] = 'tie'
        result = module.score(feedback, mapping, tasks)
        self.assertEqual(result['comparisons']['plain']['style'], {'win': 2, 'tie': 1, 'loss': 0})
        self.assertTrue(result['preference_gate_passed'])

    def test_incomplete_duplicate_and_invalid_answers_rejected(self):
        for kind in ('missing', 'duplicate', 'invalid'):
            feedback, mapping, tasks = self.fixture()
            if kind == 'missing': feedback['answers'].pop()
            if kind == 'duplicate': feedback['answers'][1]['id'] = feedback['answers'][0]['id']
            if kind == 'invalid': feedback['answers'][0]['use'] = None
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                module.score(feedback, mapping, tasks)

    def test_ties_do_not_count_as_wins(self):
        feedback, mapping, tasks = self.fixture()
        for answer in feedback['answers']: answer['use'] = 'tie'
        result = module.score(feedback, mapping, tasks)
        self.assertFalse(result['preference_gate_passed'])
        self.assertEqual(result['comparisons']['mismatch']['use']['tie'], 6)


if __name__ == '__main__':
    unittest.main()
