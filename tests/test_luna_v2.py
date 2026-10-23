import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


def load_module(name):
    spec=importlib.util.spec_from_file_location('v2_'+name,ROOT/'evals/luna_v2'/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class LunaComplexOracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=json.loads((ROOT/'evals/luna_v2/cases.json').read_text(),parse_constant=lambda text:(_ for _ in ()).throw(ValueError(text)))
        cls.tasks={task['id']:task for group in cls.data.values() for task in group}
        cls.code=load_module('code_oracle');cls.text=load_module('text_oracle')

    def test_all_original_modules_pass(self):
        for task in self.tasks.values():
            if task['domain']=='code':
                with self.subTest(task=task['id']):self.assertTrue(self.code.compare(task,task['files'])['passed'])

    def test_known_compatibility_faults_are_detected(self):
        faults=[('dev-code-zh','series_core.py','if number is not None:','if number:'),
                ('dev-code-zh','series_api.py','movingAverage =','renamedAverage ='),
                ('dev-code-en','event_core.py','version >= versions[key]','version > versions[key]'),
                ('dev-code-en','event_core.py','event.get("deleted") is True','event.get("deleted")'),
                ('dev-code-en','event_core.py','chosen.items():','sorted(chosen.items()):'),
                ('holdout-code-zh','bucket_core.py','(number < boundary)','(number <= boundary)'),
                ('holdout-code-en','weight_core.py','if value is None:','if not value:')]
        for identifier,filename,before,after in faults:
            task=self.tasks[identifier];files=dict(task['files']);self.assertIn(before,files[filename]);files[filename]=files[filename].replace(before,after)
            with self.subTest(task=identifier,fault=after):self.assertFalse(self.code.compare(task,files)['passed'])

    def test_disallowed_import_and_public_signature_are_rejected(self):
        task=self.tasks['dev-code-en'];files=dict(task['files'])
        files['event_core.py']='import os\n'+files['event_core.py']
        self.assertFalse(self.code.compare(task,files)['passed'])
        files=dict(task['files']);files['event_api.py']=files['event_api.py'].replace('*, include_deleted=False','include_deleted=False')
        self.assertFalse(self.code.compare(task,files)['passed'])

    def gold_output(self,task):
        artifact=' '.join([*task.get('source_map_oracle',{}).values()][0]) if task['domain']=='research' else ''
        if task['domain']=='research':
            artifact=' '.join(source for ids in task['source_map_oracle'].values() for source in ids)+' Results have appropriate limitations.'
            return {'artifact':artifact,'facts':copy.deepcopy(task['oracle']),'source_map':copy.deepcopy(task['source_map_oracle']),'style_evidence':[]}
        artifact=' '.join(task['oracle']['to']+task['oracle']['context_refs']+[action['deadline'] for action in task['oracle']['recipient_actions']])
        return {'artifact':artifact,'ledger':copy.deepcopy(task['oracle']),'style_evidence':[]}

    def test_gold_structured_facts_and_ledgers_pass(self):
        for task in self.tasks.values():
            if task['domain']!='code':
                with self.subTest(task=task['id']):self.assertTrue(self.text.assess(task,self.gold_output(task))['passed'])

    def test_wrong_source_units_unknown_and_actor_fail(self):
        task=self.tasks['dev-research-en'];gold=self.gold_output(task)
        for key,value in [('n',144),('reduction_ms',0.03),('independent_n',0),('significant_95',True)]:
            changed=copy.deepcopy(gold);changed['facts'][key]=value
            with self.subTest(key=key):self.assertFalse(self.text.assess(task,changed)['passed'])
        changed=copy.deepcopy(gold);changed['source_map']['primary']=['S1'];self.assertFalse(self.text.assess(task,changed)['passed'])
        task=self.tasks['dev-email-zh'];changed=self.gold_output(task);changed['ledger']['recipient_actions'][0]['actor']='Mina'
        self.assertFalse(self.text.assess(task,changed)['passed'])

    def test_sample_fact_leakage_is_not_style_transfer(self):
        task=self.tasks['holdout-email-en'];gold=self.gold_output(task);gold['artifact']+=' Cedar'
        self.assertFalse(self.text.assess(task,gold)['passed'])

    def test_luna_model_is_explicit(self):
        runtime=load_module('runtime');command=runtime.command('probe')
        self.assertEqual(command[command.index('--model')+1],'gpt-6-luna')
        self.assertIn('model_reasoning_effort=medium',command)
        self.assertEqual(command.count('--model'),1)


if __name__=='__main__':unittest.main()
