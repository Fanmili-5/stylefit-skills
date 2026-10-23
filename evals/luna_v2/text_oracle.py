"""Exact structured facts and selected textual checks; semantics still need review."""
import math
import re


def equal(expected,actual):
    if expected is None or isinstance(expected,bool):return type(expected) is type(actual) and expected==actual
    if isinstance(expected,(int,float)):
        return not isinstance(actual,bool) and isinstance(actual,(int,float)) and math.isclose(expected,actual,rel_tol=1e-9,abs_tol=1e-9)
    if isinstance(expected,dict):
        return isinstance(actual,dict) and set(expected)==set(actual) and all(equal(expected[key],actual[key]) for key in expected)
    if isinstance(expected,list):return isinstance(actual,list) and len(expected)==len(actual) and all(equal(left,right) for left,right in zip(expected,actual))
    return type(expected) is type(actual) and expected==actual


def assess(task,output):
    issues=[]
    if not isinstance(output,dict):return {'passed':False,'issues':['output_not_object']}
    artifact=output.get('artifact')
    if not isinstance(artifact,str) or not artifact.strip():issues.append('missing_artifact');artifact=''
    field='facts' if task['domain']=='research' else 'ledger'
    actual=output.get(field)
    if not isinstance(actual,dict):issues.append('missing_'+field);actual={}
    for key,expected in task['oracle'].items():
        if key not in actual or not equal(expected,actual[key]):issues.append('incorrect_'+key)
    if set(actual)-set(task['oracle']):issues.append('unrequested_structured_fields')
    leaked=[canary for canary in task.get('leakage_canaries',[]) if canary.casefold() in artifact.casefold()]
    if leaked:issues.append('sample_fact_leakage')
    if not isinstance(output.get('style_evidence'),list):issues.append('missing_style_evidence')
    if task['domain']=='research':
        mapping=output.get('source_map',{})
        for key,expected in task['source_map_oracle'].items():
            actual_ids=mapping.get(key)
            if not isinstance(actual_ids,list) or set(actual_ids)!=set(expected):issues.append('incorrect_source_'+key)
            for source_id in expected:
                if not re.search(r'(?<![A-Za-z0-9_])'+re.escape(source_id)+r'(?![A-Za-z0-9_])',artifact):issues.append('uncited_'+source_id)
    else:
        for reference in task['oracle']['context_refs']:
            if reference not in artifact:issues.append('missing_context_reference')
        for action in task['oracle']['recipient_actions']:
            if action['deadline'] not in artifact:issues.append('missing_current_deadline')
        for person in task['oracle']['to']:
            if person not in artifact:issues.append('missing_addressee')
    return {'passed':not issues,'issues':issues,'sample_fact_leakage':leaked,
            'scope':'Typed ledgers, numerical facts, attribution IDs and selected spans only. Raw prose can still contradict a correct ledger.'}
