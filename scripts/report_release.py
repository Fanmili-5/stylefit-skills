"""Rebuild release gates from saved artifacts; no new model calls."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import sqlite3
import statistics
import hashlib

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/'.local/release-v02'
ARMS=('plain','checklist','ownvoice')
spec=importlib.util.spec_from_file_location('release_packaging',ROOT/'scripts/package_release.py')
packaging=importlib.util.module_from_spec(spec);spec.loader.exec_module(packaging)


def read(path):return json.loads(path.read_text()) if path.exists() else None


def frozen_candidate_matches():
    manifest=read(LOCAL/'holdout/frozen.json')
    if not manifest:return False
    for name,expected in manifest['dependencies'].items():
        path=ROOT/name
        if not path.is_file():return False
        content=path.read_bytes()
        if name=='ownvoice/__init__.py':
            content=content.replace(b'__version__ = "0.2.0"',b'__version__ = "0.2.0rc1"')
        if hashlib.sha256(content).hexdigest()!=expected:return False
    for name,expected in manifest['skills'].items():
        path=ROOT/'skills'/name
        if not path.is_file():return False
        content=path.read_bytes()
        if path.name=='SKILL.md':content=content.replace(b'  version: "0.2.0"',b'  version: "0.2.0rc1"')
        if hashlib.sha256(content).hexdigest()!=expected:return False
    return True


def cell_name(phase,task,style,arm,step):return f'ownvoice-v02-{phase}-{task["id"]}-s{style}-{arm}-{step}'


def judgments():
    rows=[]
    for path in sorted((LOCAL/'grading-maps').glob('*.json')):
        mapping=read(path);value=read(LOCAL/'runs'/path.stem/'output.json');issues=[]
        if not isinstance(value,dict) or not isinstance(value.get('reviews'),list) or not isinstance(value.get('style_pairs'),list):
            rows.append({'job':path.stem,'valid':False,'issues':['invalid_json_shape'],'reviews':[],'pairs':[]});continue
        reviews=value['reviews'];pairs=value['style_pairs']
        if Counter(row.get('candidate_id') for row in reviews)!=Counter(mapping['candidates'].keys()):issues.append('missing_duplicate_or_unknown_candidate')
        if Counter(row.get('pair_id') for row in pairs)!=Counter(mapping['pairs'].keys()):issues.append('missing_duplicate_or_unknown_pair')
        if any(not isinstance(row.get('material_errors'),list) or any(not isinstance(x,str) for x in row.get('material_errors',[])) for row in reviews):issues.append('invalid_error_list')
        for row in reviews:
            if any(type(row.get(key)) is not int or not 0<=row[key]<=4 for key in ('fidelity','clarity')):issues.append('invalid_rating')
        for row in pairs:
            if any(row.get(key) not in {'set_1','set_2','ambiguous'} for key in ('first_matches','second_matches')):issues.append('invalid_style_assignment')
        if issues:rows.append({'job':path.stem,'valid':False,'issues':issues,'reviews':[],'pairs':[]});continue
        decoded_reviews=[];decoded_pairs=[]
        for review in reviews:
            decoded_reviews.append({k:v for k,v in {**review,**mapping['candidates'][review['candidate_id']]}.items() if k!='candidate_id'})
        for pair in pairs:
            entry=mapping['pairs'][pair['pair_id']]
            expected=['set_'+str(mapping['candidates'][label]['style']+1) for label in entry['candidate_ids']]
            decoded_pairs.append({'arm':entry['arm'],'matched':expected==[pair['first_matches'],pair['second_matches']],
                                  'evidence':pair['evidence']})
        rows.append({'job':path.stem,'case_id':path.stem.removeprefix('ownvoice-v02-judge-'),'valid':True,'issues':[],
                     'reviews':decoded_reviews,'pairs':decoded_pairs})
    return rows


def flag_audit(graded):
    mapping=read(LOCAL/'material-flag-map.json')
    value=read(LOCAL/'runs/ownvoice-v02-material-flag-audit/output.json')
    if not mapping or not value:return {'valid':False,'flags':[],'additional_errors':[],'issues':['not_run']}
    issues=[];flags=value.get('flags');additional=value.get('additional_errors')
    if not isinstance(flags,list) or Counter(row.get('flag_id') for row in flags)!=Counter(mapping['flags'].keys()):issues.append('incomplete_or_duplicate_flags')
    if not isinstance(additional,list):issues.append('invalid_additional_errors')
    for row in flags if isinstance(flags,list) else []:
        if row.get('decision') not in {'supported','unsupported','unclear'} or not row.get('source_evidence') or not row.get('reason'):issues.append('invalid_flag_decision')
    for row in additional if isinstance(additional,list) else []:
        if row.get('candidate_id') not in mapping['candidates'] or not isinstance(row.get('material_errors'),list):issues.append('invalid_additional_candidate')
    if issues:return {'valid':False,'flags':[],'additional_errors':[],'issues':issues}
    decoded=[{k:v for k,v in {**row,**mapping['flags'][row['flag_id']]}.items() if k!='flag_id'} for row in flags]
    # Require exact agreement with the preserved initial flags before resolving any.
    calendar=next((j for j in graded if j.get('case_id')=='hold-calendar-en'),None)
    actual=Counter((r['arm'],r['style'],error) for r in (calendar or {}).get('reviews',[]) for error in r['material_errors'])
    if Counter((r['arm'],r['style'],r['claim']) for r in decoded)!=actual:
        return {'valid':False,'flags':[],'additional_errors':[],'issues':['flags_do_not_match_original_review']}
    extra=[{k:v for k,v in {**row,**mapping['candidates'][row['candidate_id']]}.items() if k!='candidate_id'} for row in additional]
    return {'valid':True,'flags':decoded,'additional_errors':extra,'issues':[],
            'scope':'One post-hoc blinded flag-validity audit; original scores/outputs unchanged. Empty additional_errors means none reported, not exhaustive independent re-review.'}


def build():
    data=read(ROOT/'evals/release_v02/cases.json');graded=judgments();audit=flag_audit(graded);phases=[]
    for phase,tasks in data.items():
        cells=[]
        for task in tasks:
            for style in ((0,) if phase=='development' else (0,1)):
                for arm in ARMS:
                    first=cell_name(phase,task,style,arm,'initial');last=cell_name(phase,task,style,arm,'revision')
                    initial=read(LOCAL/'assessments'/(first+'.json'));final=read(LOCAL/'assessments'/(last+'.json'))
                    result=read(LOCAL/'runs'/last/'result.json')
                    cells.append({'task_id':task['id'],'domain':task['domain'],'language':task['language'],'style':style,'arm':arm,
                                  'status':(result or {}).get('status','missing'),'initial_passed':(initial or {}).get('passed'),
                                  'final_passed':(final or {}).get('passed'),'blocking_issues':(final or {}).get('mechanical',{}).get('blocking_issues',[]),
                                  'behavior_passed':(final or {}).get('behavior',{}).get('passed')})
        aggregates={}
        task_ids={task['id'] for task in tasks}
        for arm in ARMS:
            selected=[c for c in cells if c['arm']==arm]
            reviews=[r for j in graded if j.get('case_id') in task_ids for r in j['reviews'] if r['arm']==arm]
            pairs=[p for j in graded if j.get('case_id') in task_ids for p in j['pairs'] if p['arm']==arm]
            runs=[read(path) for path in (LOCAL/'runs').glob(f'ownvoice-v02-{phase}-*-{arm}-*/result.json')]
            usage=Counter()
            for run in runs:
                for u in run.get('usage',[]):usage.update({k:v for k,v in u.items() if isinstance(v,(int,float))})
            aggregates[arm]={'expected':len(selected),'initial_passes':sum(c['initial_passed'] is True for c in selected),
                             'final_passes':sum(c['final_passed'] is True for c in selected),'style_pairs_matched':sum(p['matched'] for p in pairs),
                             'style_pairs_total':len(pairs),'material_error_flags':sum(len(r['material_errors']) for r in reviews),
                             'fidelity_mean':statistics.mean(r['fidelity'] for r in reviews) if reviews else None,
                             'clarity_mean':statistics.mean(r['clarity'] for r in reviews) if reviews else None,
                             'prompt_characters':sum(r.get('prompt_characters',0) for r in runs),'reported_usage':dict(usage)}
            unresolved=aggregates[arm]['material_error_flags']
            if phase=='holdout' and audit['valid']:
                unresolved-=sum(row['arm']==arm and row['decision']=='unsupported' for row in audit['flags'])
                unresolved+=sum(len(row['material_errors']) for row in audit['additional_errors'] if row['arm']==arm)
            aggregates[arm]['unresolved_material_flags']=unresolved
        phases.append({'phase':phase,'cells':cells,'aggregates':aggregates})
    native=[]
    descriptor=read(LOCAL/'native-workspace.json')
    if descriptor:
        for case in descriptor['cases']:
            name='ownvoice-v02-native-'+case['name'];assessment=read(LOCAL/'runs'/name/'native-assessment.json')
            native.append({'case_id':case['name'],'passed':bool(assessment and assessment.get('passed')),
                           'issues':(assessment or {}).get('issues',['missing_assessment']),
                           'skill_read_observed':(assessment or {}).get('skill_read_observed'),
                           'helper_execution_observed':(assessment or {}).get('helper_execution_observed'),
                           'tool_events':(assessment or {}).get('tool_events',0)})
    hold=next(p for p in phases if p['phase']=='holdout');own=hold['aggregates']['ownvoice']
    domain_matches={domain:sum(pair['matched'] for j in graded if any(t['id']==j.get('case_id') and t['domain']==domain for t in data['holdout']) for pair in j['pairs'] if pair['arm']=='ownvoice') for domain in ('code','research','email')}
    valid_hold=sum(j['valid'] for j in graded if j.get('case_id') in {t['id'] for t in data['holdout']})
    gates={'frozen_candidate_matches':frozen_candidate_matches(),'heldout_contracts':own['final_passes']==12,'heldout_reviews_complete':valid_hold==6,
           'no_unresolved_material_ownvoice_errors':valid_hold==6 and own['unresolved_material_flags']==0,
           'paired_style':own['style_pairs_total']==6 and own['style_pairs_matched']>=5 and all(v>=1 for v in domain_matches.values()),
           'native_host':len(native)==8 and all(c['passed'] for c in native)}
    with sqlite3.connect('file:'+str(ROOT/'.local/ledger.sqlite')+'?mode=ro',uri=True) as db:
        total=db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
        new=db.execute('SELECT COUNT(*) FROM jobs WHERE id LIKE "ownvoice-v02-%"').fetchone()[0]
        stages=dict(db.execute('SELECT stage,COUNT(*) FROM jobs WHERE id LIKE "ownvoice-v02-%" GROUP BY stage').fetchall())
    runtime_results=[read(p) for p in (LOCAL/'runs').glob('*/result.json')]
    return {'schema_version':1,'release_gates_passed':all(gates.values()),'gates':gates,
            'new_cli_tasks':new,'cap':120,'lifetime_cli_tasks':total,'stage_counts':stages,
            'requested_models':dict(Counter(r.get('requested_model','missing') for r in runtime_results)),
            'response_model_unreported_tasks':sum(not r.get('reported_models') for r in runtime_results),
            'runtime_failures':[{'stage':r.get('stage'),'error_type':r.get('error_type'),'case_id':r.get('case_id')} for r in runtime_results if r.get('status')=='failed'],
            'phases':phases,'judgments':graded,'flag_validity_audit':audit,'native_tests':native,'ownvoice_style_matches_by_domain':domain_matches,
            'product_hashes':packaging.product_hashes(),
            'limits':['Synthetic small sample; same-model review is not independent human preference.',
                      'CLI job accounting is not an exact count of provider requests inside native tool loops.',
                      'Finite code cases do not prove general behavioral equivalence.']}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,default=ROOT/'reports/release-v02.json')
    args=parser.parse_args();report=build();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'new_cli_tasks':report['new_cli_tasks'],'gates':report['gates'],'release_gates_passed':report['release_gates_passed']}))


if __name__=='__main__':main()
