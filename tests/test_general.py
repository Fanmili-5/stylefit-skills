import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from ownvoice.checks import check_code

ROOT = Path(__file__).resolve().parents[1]


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


class GeneralDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = json.loads((ROOT / 'evals/general_v1/cases.json').read_text())
        cls.checker = module('general_checker_test', ROOT / 'evals/general_v1/checks.py')
        cls.runner = module('general_runner_test', ROOT / 'scripts/evaluate_general.py')

    def test_reference_functions_satisfy_new_contracts(self):
        for task in self.cases['development'] + self.cases['holdout']:
            if task['domain'] == 'code':
                with self.subTest(task=task['id']):
                    result = check_code(task, task['reference'])
                    self.assertTrue(result['passed'], result)

    def test_exact_error_message_regression_is_detected(self):
        task = self.cases['development'][0]
        changed = task['reference'].replace('ragged rows', 'bad shape')
        self.assertFalse(check_code(task, changed)['passed'])

    def test_no_profile_prompt_really_omits_profile(self):
        task = self.cases['development'][0]
        prompt = self.runner.make_prompt(task, 'none', 'plain', 'development', self.cases)
        self.assertNotIn('\nPROFILE\n', prompt)
        self.assertNotIn('reference', json.loads(prompt.split('\nTASK\n')[1]))
        self.assertNotIn('tests', json.loads(prompt.split('\nTASK\n')[1]))
        self.assertIsNone(self.cases['profiles']['none'])

    def test_both_methods_receive_same_profile_and_task(self):
        task = self.cases['development'][2]
        original = copy.deepcopy(task)
        previous = self.runner.LOCAL
        with tempfile.TemporaryDirectory() as folder:
            self.runner.LOCAL = Path(folder)
            skill = Path(folder) / 'development/skills/ownvoice-research'
            skill.mkdir(parents=True)
            (skill / 'SKILL.md').write_text('An isolated test guide.')
            try:
                prompts = [self.runner.make_prompt(task, 'expanded', condition, 'development', self.cases)
                           for condition in ('plain', 'ownvoice')]
            finally:
                self.runner.LOCAL = previous
        settings = [json.loads(prompt.split('\nPROFILE\n')[1].split('\nTASK\n')[0]) for prompt in prompts]
        self.assertEqual(settings[0], settings[1])
        self.assertEqual(settings[0]['preferences'], self.cases['profiles']['expanded']['research'])
        self.assertEqual(prompts[0].split('\nTASK\n')[1], prompts[1].split('\nTASK\n')[1])
        self.assertEqual(task, original)

    def test_decimal_values_and_citations_do_not_inflate_sentence_count(self):
        text = 'Error fell from 0.28 to 0.24. There were 48 cases. Limits remain. [R7]'
        self.assertEqual(len(self.checker.sentences(text)), 3)

    def test_empty_profile_probe_catches_calibration_requests(self):
        task = self.cases['development'][2]
        for text in ('请先提供你的偏好档案。', 'Could you share your profile first?'):
            with self.subTest(text=text):
                self.assertFalse(self.checker.style(task, text, 'none')['passed'])

    def test_research_order_and_email_contrasts(self):
        task = self.cases['development'][2]
        self.assertTrue(self.checker.style(task, '误差降低0.04。样本为48条。还需验证。', 'compact')['passed'])
        self.assertFalse(self.checker.style(task, '样本为48条，误差降低0.04。', 'compact')['passed'])
        task = self.cases['development'][5]
        compact = 'Casey, send the signed proposal by 2026-11-23.'
        expanded = 'Hi Casey,\n\nSend the signed proposal by 2026-11-23.\n\nThank you.'
        self.assertTrue(self.checker.style(task, compact, 'compact')['passed'])
        self.assertTrue(self.checker.style(task, expanded, 'expanded')['passed'])
        self.assertFalse(self.checker.style(task, expanded, 'compact')['passed'])


if __name__ == '__main__':
    unittest.main()
