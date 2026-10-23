import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from ownvoice.checks import check_code, check_text
from ownvoice.profile import select, validate

ROOT=Path(__file__).resolve().parents[1]


class ProfileTests(unittest.TestCase):
    def test_unknown_is_not_invented(self):
        profile={'schema_version':1,'basis':'preferences','preferences':{'code':{'zh':['compact']}}}
        self.assertEqual(select(profile,'email','en')['preferences'],[])
        self.assertEqual(select(profile,'code','zh')['preferences'],['compact'])

    def test_invalid_contracts(self):
        cases=[{}, {'schema_version':True,'basis':'generic','preferences':{}},
               {'schema_version':1,'basis':'guessed','preferences':{}},
               {'schema_version':1,'basis':'generic','preferences':{'email':{'xx':[]}}}]
        for case in cases:
            with self.subTest(case=case),self.assertRaises(ValueError): validate(case)


class CheckTests(unittest.TestCase):
    def test_rewrite_sources_pass_their_contracts(self):
        data=json.loads((ROOT/'evals/tasks.json').read_text())
        for task in data['pilot']+data['main']:
            if task['domain']=='code' and task.get('source'):
                with self.subTest(task=task['id']):
                    result=check_code(task,task['source'])
                    self.assertTrue(result['passed'],result)

    def test_truthiness_regression_is_detected(self):
        task=json.loads((ROOT/'evals/tasks.json').read_text())['main'][0]
        result=check_code(task,task['source'].replace('== True', ''))
        self.assertFalse(result['passed'])

    def test_mutation_and_keyword_contracts(self):
        task={'function':'f','parameters':['values'],'tests':[{'kwargs':{'values':[1]},'expected':[1,2]}]}
        self.assertFalse(check_code(task,'def f(values):\n    values.append(2)\n    return values\n')['passed'])
        self.assertFalse(check_code(task,'def f(x):\n    return x\n')['passed'])

    def test_forbidden_execution_is_not_run(self):
        task={'function':'f','parameters':[],'tests':[]}
        for source in ['import os\ndef f(): return 0\n','def f(): return open("/tmp/marker","w")\n',
                       'def f(): return (1).__class__\n','raise RuntimeError("executed")\n']:
            with self.subTest(source=source): self.assertFalse(check_code(task,source)['passed'])

    def test_chinese_added_number_is_detected(self):
        task={'packet':'样本40个。[S1]','protected':['40','[S1]']}
        self.assertFalse(check_text(task,'40个样本，另有50个。[S1]')['passed'])
        result=check_text(task,'样本共40个。[S1]')
        self.assertTrue(result['passed'])
        self.assertFalse(result['semantic_fidelity_verified'])

    def test_changed_deadline_and_negation_are_detected(self):
        task={'packet':'Alex by 2026-11-06. Not causal.','protected':['Alex','2026-11-06'],
              'required_any':[['not causal','不能推断因果']]}
        self.assertFalse(check_text(task,'Alex by 2026-11-07. Causal.')['passed'])

    def test_sentence_punctuation_does_not_create_numbers(self):
        task={'packet':'Deadline 2026-11-03. Value 0.20.','protected':['2026-11-03','0.20']}
        self.assertTrue(check_text(task,'2026-11-03, value 0.20')['passed'])


class BudgetTests(unittest.TestCase):
    def test_failed_reservations_still_consume_budget(self):
        spec=importlib.util.spec_from_file_location('runner',ROOT/'scripts/evaluate.py')
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        with tempfile.TemporaryDirectory() as folder:
            runner.LOCAL=Path(folder);runner.CAP=2
            self.assertTrue(runner.reserve('one','test','fake'))
            self.assertFalse(runner.reserve('one','test','fake'))
            self.assertTrue(runner.reserve('two','test','fake'))
            with self.assertRaises(RuntimeError): runner.reserve('three','test','fake')

    def test_dry_command_disables_claude_tools_and_custom_skills(self):
        spec=importlib.util.spec_from_file_location('runner',ROOT/'scripts/evaluate.py')
        runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
        command=runner.command('claude','hello')
        self.assertIn('--safe-mode',command)
        self.assertEqual(command[command.index('--tools')+1],'')


if __name__=='__main__': unittest.main()
