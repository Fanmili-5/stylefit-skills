import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('release_tests',ROOT/'scripts/release_eval.py')
runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)


class ReleaseOracleTests(unittest.TestCase):
    def setUp(self):self.data=json.loads((ROOT/'evals/release_v02/cases.json').read_text())

    def test_all_reference_bundles_pass_and_seeded_faults_fail(self):
        code=[t for group in self.data.values() for t in group if t['domain']=='code']
        for task in code:
            with self.subTest(task=task['id']):
                value={'files':task['files'],'style_evidence':[]}
                self.assertTrue(runner.assess(task,value)['passed'],runner.assess(task,value))
        task=code[0];faults=[('rules.py','deleted_value is True','bool(deleted_value)'),
                            ('merge.py','event_version >= previous_event[0]','event_version > previous_event[0]'),
                            ('api.py','summarizeEvents = summarize_events','renamed = summarize_events')]
        for filename,before,after in faults:
            files=dict(task['files']);files[filename]=files[filename].replace(before,after)
            self.assertFalse(runner.assess(task,{'files':files,'style_evidence':[]})['passed'])

    def test_explicit_text_contracts_and_seeded_errors(self):
        for group in self.data.values():
            for task in group:
                if task['domain']=='code':continue
                value={'artifact':'Evidence '+ ' '.join(str(x.get('value','')) for x in task['constraints']['assertions'] if x['op']=='contains'), 'style_evidence':[]}
                for assertion in task['constraints']['assertions']:
                    if assertion['op']!='equal':continue
                    container,key=assertion['path'][1:].split('/')
                    value.setdefault(container,{})[key]=assertion['expected']
                with self.subTest(task=task['id']):
                    self.assertTrue(runner.assess(task,value)['passed'])
                    wrong=json.loads(json.dumps(value))
                    if task['domain']=='research':wrong['facts']['independent_n']=0
                    else:wrong['ledger']['recipient_actions'][0]['actor']='WrongActor'
                    self.assertFalse(runner.assess(task,wrong)['passed'])

    def test_luna_routing_schema_and_no_unconditional_profile_guide(self):
        command=runner.runtime.command('test',Path('schema.json'))
        self.assertEqual(command[command.index('--model')+1],'gpt-6-luna')
        self.assertIn('model_reasoning_effort=medium',command)
        self.assertIn('--output-schema',command)
        native=runner.runtime.command('test',native=True)
        self.assertNotIn('skip_host_skill_discovery',native)
        self.assertNotIn('shell_tool',native)


if __name__=='__main__':unittest.main()
