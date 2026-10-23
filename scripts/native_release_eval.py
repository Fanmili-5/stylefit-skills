"""Exercise discovered skills and installed helpers in a disposable Codex workspace."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'evals/release_v02'))
import runtime
from ownvoice.installation import managed_install
from ownvoice.verification import verify
from ownvoice.checks import check_code

LOCAL=ROOT/'.local/release-v02'


def prepare():
    descriptor=LOCAL/'native-workspace.json'
    if descriptor.exists():
        data=json.loads(descriptor.read_text())
        if Path(data['root']).exists():return data
        raise RuntimeError('Prior native workspace disappeared; preserve its results')
    workspace=Path(tempfile.mkdtemp(prefix='ownvoice-v02-native-'))
    subprocess.run(['git','init','-q',str(workspace)],check=True,capture_output=True)
    wheels=list((ROOT/'dist').glob('ownvoice_skills-0.2.0rc1-*.whl'))
    if len(wheels)!=1:raise RuntimeError('Build matching wheel first')
    install=managed_install(ROOT,workspace/'.agents/skills','0.2.0rc1',wheels[0],True,wheelhouse=ROOT/'.local/wheelhouse-v02')
    (workspace/'AGENTS.md').write_text('This is a disposable synthetic skill test workspace. Use installed skills normally when relevant. Work only inside this workspace. No web, external messages, or calls to other models. Never invent verification execution.\n')
    tasks=json.loads((ROOT/'evals/release_v02/cases.json').read_text())['development']
    cases=[]
    for explicit in (True,False):
        for domain in ('code','research','email'):
            name=('explicit' if explicit else 'implicit')+'-'+domain
            folder=workspace/name;folder.mkdir()
            if domain=='code':
                before='def present_values(values):\n    output_values = []\n    for value in values:\n        if value is not None:\n            output_values.append(value)\n    return output_values\n'
                (folder/'before.py').write_text(before)
                (folder/'test_output.py').write_text("import unittest\nfrom output import present_values\nclass Contract(unittest.TestCase):\n    def test_values(self):\n        self.assertEqual(present_values([None,0,False,2]),[0,False,2])\n    def test_empty(self):\n        self.assertEqual(present_values([]),[])\n")
                request=('Simplify before.py into output.py using concise repository-style code. Preserve present_values(values), zeros, False, empty input and nonmutation. No personal profile. Run the provided tests and the skill static before/after checker, saving its JSON stdout as checks.json. Do not change tests or before.py.')
                case={'name':name,'domain':domain,'folder':str(folder),'before':before}
            else:
                task=next(t for t in tasks if t['domain']==domain)
                public={k:v for k,v in task.items() if k not in {'constraints','style_sets','synthetic'}}
                public['style_samples']=task['style_sets'][0]
                (folder/'task.json').write_text(json.dumps(public,ensure_ascii=False,indent=2))
                (folder/'schema.json').write_text(json.dumps(task['output_schema']))
                (folder/'constraints.json').write_text(json.dumps(task['constraints']))
                request=('Complete task.json using its style samples and authoritative sources/current brief, without building a personal profile. Write result.json matching schema.json. Check the explicit constraints with the installed skill verifier and save its actual report to checks.json. Read any failure, revise at most once, then rerun. Do not change task.json, schema.json or constraints.json. Review the actual body against the source separately from the ledger.')
                case={'name':name,'domain':domain,'folder':str(folder),'task':task}
            prefix=('Use $ownvoice-'+domain+'. ' if explicit else '')
            case['prompt']=prefix+request+' Your working directory is '+str(folder)+'.'
            cases.append(case)
    profile=workspace/'explicit-profile';profile.mkdir()
    schema=json.loads((ROOT/'schemas/profile.schema.json').read_text())
    # Codex schema-output restrictions do not apply here; the installed local verifier uses the published v1 schema.
    (profile/'schema.json').write_text(json.dumps(schema))
    (profile/'samples.txt').write_text('Confirmed fictional user-written English code examples:\ndef scale(values, factor):\n    scaled_values = []\n    for value in values:\n        scaled_values.append(value * factor)\n    return scaled_values\n\ndef present(values):\n    return [value for value in values if value is not None]\n')
    cases.append({'name':'explicit-profile','domain':'profile','folder':str(profile),
                  'prompt':'Use $ownvoice-profile to draft a v1 style profile from the confirmed English code samples in samples.txt. Save only the temporary review artifact result.json here, not a reusable profile or private samples elsewhere. Keep other domains/languages empty or absent. Do not ask questions already answered. Validate schema.json with the installed verifier, saving checks.json. Working directory: '+str(profile)})
    negative=workspace/'negative';negative.mkdir()
    cases.append({'name':'negative','domain':None,'folder':str(negative),'prompt':'Reply exactly OK42. This request needs no files, skills or tools.'})
    data={'root':str(workspace),'install':install,'cases':cases}
    descriptor.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    return data


def observed_skill_read(events,domain,skill_text):
    # A later command in the same shell chain can fail after cat succeeded.
    # Require the actual full skill contents, not the shell chain's final exit code.
    return any('ownvoice-'+domain in str(event.get('command','')) and 'SKILL.md' in str(event.get('command',''))
               and skill_text.strip() in str(event.get('aggregated_output','')) for event in events)


def assess(case,name):
    folder=Path(case['folder']);run=LOCAL/'runs'/name
    metadata=json.loads((run/'result.json').read_text())
    events=json.loads((run/'tool-events.json').read_text()) if (run/'tool-events.json').exists() else []
    commands=[str(event.get('command','')) for event in events]
    evidence='\n'.join(commands)
    if case['domain'] is None:
        passed=(run/'artifact.txt').read_text()=='OK42' and not any('ownvoice-' in line for line in commands)
        return {'passed':passed,'unrelated_task_did_not_invoke_ownvoice':passed,'tool_events':len(events)}
    domain=case['domain']
    expected_skill=(folder.parent/'.agents/skills'/('ownvoice-'+domain)/'SKILL.md').read_text()
    skill_read=observed_skill_read(events,domain,expected_skill)
    profile_read=(domain!='profile' and any('ownvoice-profile/SKILL.md' in line for line in commands))
    report_path=folder/'checks.json'
    try:report=json.loads(report_path.read_text())
    except (OSError,ValueError):report={}
    helper_name='check_python_pair.py' if domain=='code' else 'verify.py'
    helper_events=[event for event in events if helper_name in str(event.get('command','')) and 'python' in str(event.get('command','')) and event.get('exit_code')==0]
    issues=[]
    if not skill_read:issues.append('no_observed_skill_read')
    if not helper_events:issues.append('no_successful_helper_command')
    if profile_read:issues.append('unnecessary_profile_building_skill_read')
    if domain=='code':
        source=(folder/'output.py').read_text() if (folder/'output.py').exists() else ''
        task={'function':'present_values','parameters':['values'],'tests':[{'args':[[None,0,False,2]],'expected':[0,False,2]},{'args':[[]],'expected':[]}]}
        score=check_code(task,source)
        if not score['passed']:issues.append('code_contract_failed')
        if (folder/'before.py').read_text()!=case['before']:issues.append('source_overwritten')
        if not report.get('static_checks_passed'):issues.append('static_checker_report_missing_or_failed')
    else:
        artifact=folder/'result.json'
        text=artifact.read_text() if artifact.exists() else ''
        schema=json.loads((folder/'schema.json').read_text())
        constraints=json.loads((folder/'constraints.json').read_text()) if (folder/'constraints.json').exists() else None
        if domain!='profile':
            if schema!=case['task']['output_schema'] or constraints!=case['task']['constraints']:issues.append('verification_contract_was_modified')
            expected_task={k:v for k,v in case['task'].items() if k not in {'constraints','style_sets','synthetic'}}
            expected_task['style_samples']=case['task']['style_sets'][0]
            if json.loads((folder/'task.json').read_text())!=expected_task:issues.append('source_task_was_modified')
        elif schema!=json.loads((ROOT/'schemas/profile.schema.json').read_text()):issues.append('profile_schema_was_modified')
        score=verify(text,schema,constraints)
        if not score['ready_for_delivery']:issues.append('artifact_contract_failed')
        if not report.get('ready_for_delivery') or report.get('artifact_sha256')!=hashlib.sha256(text.encode()).hexdigest():issues.append('verification_report_does_not_match_artifact')
        if domain=='profile':
            try:
                value=json.loads(text)
                preferences=value['preferences']
                if not preferences.get('code',{}).get('en'):issues.append('english_code_preferences_missing')
                if any(entries for scope,langs in preferences.items() for lang,entries in langs.items() if (scope,lang)!=('code','en')):issues.append('profile_scope_contamination')
            except (ValueError,KeyError,TypeError):issues.append('invalid_profile')
    return {'passed':not issues,'issues':issues,'skill_read_observed':skill_read,'helper_execution_observed':bool(helper_events),
            'unnecessary_profile_read':profile_read,'tool_events':len(events),'artifact_checks':score,
            'scope':'Observed CLI file/tool events plus checked local artifacts; not desktop UI or human preference evidence.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--only');args=parser.parse_args();data=prepare()
    if args.prepare:print(json.dumps({'prepared':True,'cases':len(data['cases'])}));return
    for case in data['cases']:
        if args.only and case['name']!=args.only:continue
        name='ownvoice-v02-native-'+case['name']
        result=runtime.run(name,'native',case['prompt'],metadata={'case_id':case['name'],'domain':case['domain'],'step':'native'},
                           native=True,cwd=case['folder'],timeout=300)
        if result['status']!='completed':raise RuntimeError('Native CLI failed; preserve result')
        score=assess(case,name)
        score_path=LOCAL/'runs'/name/'native-assessment.json'
        if score_path.exists() and json.loads(score_path.read_text())!=score:
            preserved=score_path.with_name('native-assessment-initial.json')
            if not preserved.exists():preserved.write_bytes(score_path.read_bytes())
        score_path.write_text(json.dumps(score,ensure_ascii=False,indent=2)+'\n')
        print(json.dumps({'case':case['name'],'passed':score['passed'],'issues':score.get('issues',[])},ensure_ascii=False),flush=True)
        if not score['passed']:raise RuntimeError('Native acceptance failed; stop before scheduling more cases')


if __name__=='__main__':main()
