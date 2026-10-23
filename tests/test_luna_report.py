import copy
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('luna_report', Path(__file__).resolve().parents[1] / 'scripts/report_luna.py')
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class JudgeValidation(unittest.TestCase):
    def setUp(self):
        self.mapping = {'case-1': {'A': 'plain', 'B': 'ownvoice', 'C': 'checklist'}}
        self.value = {'cases': [{'task_id': 'case-1', 'preferred_for_use': 'tie', 'ratings': [
            {'label': label, 'fidelity': 4, 'style_fit': 3, 'clarity': 4, 'critical_errors': []}
            for label in ('A', 'B', 'C')]}]}

    def test_complete_and_duplicate_labels(self):
        self.assertEqual(report.validate_judgment(self.value, self.mapping), [])
        self.value['cases'][0]['ratings'][1]['label'] = 'A'
        self.assertIn('wrong_or_duplicate_labels', report.validate_judgment(self.value, self.mapping))

    def test_partial_case_and_invalid_score(self):
        missing = copy.deepcopy(self.value)
        missing['cases'] = []
        self.assertIn('wrong_or_duplicate_task_ids', report.validate_judgment(missing, self.mapping))
        self.value['cases'][0]['ratings'][0]['fidelity'] = True
        self.assertIn('invalid_fidelity', report.validate_judgment(self.value, self.mapping))

    def test_public_summary_omits_blind_mapping_and_raw_assessments(self):
        private = {'new_tasks_started': 1, 'phases': [{
            'phase': 'development', 'aggregates': {}, 'judge_ties': 0,
            'cells': [{'domain': 'research', 'arm': 'plain', 'assessment': {
                'issues': [], 'candidate': 'private raw value'}}],
            'judgments': [{'id': 'private-grading-id', 'valid': True, 'issues': [], 'cases': [{
                'task_id': 'case-1', 'preferred_for_use': 'A', 'preferred_arm': 'plain',
                'ratings': [{'label': 'A', 'arm': 'plain', 'evidence': 'private rationale',
                             'fidelity': 4, 'style_fit': 3, 'clarity': 4, 'critical_errors': []}]}]}]}]}
        public = report.public_summary(private)
        text = repr(public)
        for forbidden in ('private raw value', 'private-grading-id', 'private rationale', 'preferred_for_use', "'label'"):
            self.assertNotIn(forbidden, text)
        self.assertEqual(public['phases'][0]['judgments'][0]['cases'][0]['preferred_arm'], 'plain')


if __name__ == '__main__':
    unittest.main()
