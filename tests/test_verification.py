import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from ownvoice.verification import ContractError, parse_json, verify


class OutputVerificationTests(unittest.TestCase):
    schema = {'type':'object','required':['artifact','facts'],'additionalProperties':False,
              'properties':{'artifact':{'type':'string'},'facts':{'type':'object','required':['n','independent'],
              'properties':{'n':{'type':'integer'},'independent':{'type':['integer','null']}}}}}

    def test_invalid_json_duplicate_keys_and_field_renaming(self):
        valid = json.dumps({'artifact':'text','facts':{'n':5,'independent':None}})
        self.assertTrue(verify(valid,self.schema)['ready_for_delivery'])
        for text in (valid+'}', valid.replace('artifact','draft'), '{"artifact":"one","artifact":"two"}', '{"artifact":NaN}'):
            with self.subTest(text=text):self.assertFalse(verify(text,self.schema)['ready_for_delivery'])

    def test_null_boolean_unit_and_obligation_regressions(self):
        obj={'artifact':'x','facts':{'n':5,'independent':None,'ms':420},'action':{'actor':'Alex','action':'reply','deadline':'2026-12-07'}}
        assertions=[{'op':'equal','path':'/facts/independent','expected':None},
                    {'op':'equal','path':'/facts/n','expected':5},
                    {'op':'unit_conversion','path':'/facts/ms','source_value':0.42,'factor':1000},
                    {'op':'equal','path':'/action','expected':obj['action'].copy()}]
        constraints={'schema_version':1,'assertions':assertions}
        self.assertTrue(verify(json.dumps(obj),{},constraints)['ready_for_delivery'])
        for path,bad in (('independent',0),('n',True),('ms',0.42)):
            changed=json.loads(json.dumps(obj));changed['facts'][path]=bad
            self.assertFalse(verify(json.dumps(changed),{},constraints)['ready_for_delivery'])
        obj['action']['action']='complete_review'
        self.assertFalse(verify(json.dumps(obj),{},constraints)['ready_for_delivery'])

    def test_declared_date_formats_and_required_unexecuted_review(self):
        constraints={'schema_version':1,'assertions':[{'op':'date','path':'/date','expected':'2026-11-09',
                     'formats':['%Y-%m-%d','%Y 年 %m 月 %d 日','%d %B %Y']}],
                     'semantic_review':{'required':True,'status':'not_run'}}
        for date in ('2026-11-09','2026 年 11 月 09 日','9 November 2026'):
            result=verify(json.dumps({'date':date}),{},constraints)
            self.assertEqual(result['blocking_issues'],['semantic_review'])
        constraints['semantic_review']={'required':True,'status':'passed','source':'human','evidence':'source packet checked'}
        self.assertTrue(verify('{"date":"2026-11-09"}',{},constraints)['ready_for_delivery'])

    def test_bad_contract_cannot_be_reported_as_candidate_failure_or_success(self):
        for schema in ({'type':'imaginary'},{'$ref':'https://invalid.test/private'},{'type':'string','format':'date'}):
            with self.subTest(schema=schema),self.assertRaises(ContractError):verify('"x"',schema)
        with self.assertRaises(ContractError):verify('{}',{}, {'schema_version':1,'assertions':[{'op':'guess','path':''}]})

    def test_cli_preserves_artifact_and_report_status(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);artifact=root/'artifact.json';schema=root/'schema.json';report=root/'report.json'
            artifact.write_text('{"draft":"x"}');schema.write_text(json.dumps(self.schema));before=artifact.read_bytes()
            command=[sys.executable,'-B','-m','ownvoice','verify','--artifact',str(artifact),'--schema',str(schema),'--report',str(report)]
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(result.returncode,1,result.stderr)
            self.assertEqual(artifact.read_bytes(),before)
            self.assertFalse(json.loads(report.read_text())['ready_for_delivery'])
            schema.write_text('{')
            result=subprocess.run(command,capture_output=True,text=True)
            self.assertEqual(result.returncode,2,result.stderr)
            self.assertEqual(json.loads(report.read_text())['status'],'not_run')


if __name__=='__main__':unittest.main()
