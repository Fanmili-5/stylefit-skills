"""Synthetic complex fixtures; no coursework, private samples or user profile."""
import json
import math
from pathlib import Path
from text_cases import build_text

ROOT=Path(__file__).resolve().parent

SERIES_CORE='''import math

def coerce_value(value):
    if value is None:
        return None
    number = float(value)
    if math.isnan(number):
        return None
    return number

def rolling_mean(values, width, *, min_count=1):
    if isinstance(width, bool) or not isinstance(width, int) or width <= 0:
        raise ValueError("invalid width")
    if isinstance(min_count, bool) or not isinstance(min_count, int) or not 1 <= min_count <= width:
        raise ValueError("invalid min_count")
    result = []
    for position in range(len(values)):
        # Initialize data for this iteration
        window = values[max(0, position - width + 1):position + 1]
        present_values = []
        for value in window:
            number = coerce_value(value)
            if number is not None:
                present_values.append(number)
        if len(present_values) < min_count:
            result.append(None)
        else:
            result.append(sum(present_values) / len(present_values))
    return result
'''
SERIES_API='''from series_core import rolling_mean, coerce_value

def moving_average(values, width, *, min_count=1):
    return rolling_mean(values, width, min_count=min_count)

def valid_count(values):
    count = 0
    for value in values:
        if coerce_value(value) is not None:
            count += 1
    return count

movingAverage = moving_average
'''
EVENT_CORE='''def latest_by_key(events, *, include_deleted=False):
    chosen = {}
    versions = {}
    for event in events:
        key = event["key"]
        version = event.get("version", 0)
        if isinstance(version, bool) or not isinstance(version, int):
            raise TypeError("version must be int")
        if key not in chosen or version >= versions[key]:
            chosen[key] = event
            versions[key] = version
    output = []
    for key, event in chosen.items():
        if event.get("deleted") is True and not include_deleted:
            continue
        output.append({"key": key, "value": event.get("value"), "version": versions[key]})
    return output
'''
EVENT_API='''from event_core import latest_by_key

def summarize_events(events, *, include_deleted=False):
    items = latest_by_key(events, include_deleted=include_deleted)
    return {"items": items, "count": len(items)}

summarizeEvents = summarize_events
'''
BUCKET_CORE='''import math

def histogram(values, boundaries, *, right=False):
    bounds = [float(value) for value in boundaries]
    if any(not math.isfinite(value) for value in bounds):
        raise ValueError("nonfinite boundary")
    if any(bounds[index] >= bounds[index + 1] for index in range(len(bounds) - 1)):
        raise ValueError("boundaries must increase")
    counts = [0] * (len(bounds) + 1)
    missing = 0
    for value in values:
        if value is None:
            missing += 1
            continue
        number = float(value)
        if math.isnan(number):
            missing += 1
            continue
        bucket_index = len(bounds)
        for index, boundary in enumerate(bounds):
            if (number <= boundary) if right else (number < boundary):
                bucket_index = index
                break
        counts[bucket_index] += 1
    return {"counts": counts, "missing": missing, "boundaries": bounds}
'''
BUCKET_API='''from bucket_core import histogram

def bucket_report(values, boundaries, *, right=False):
    return histogram(values, boundaries, right=right)

bucketReport = bucket_report
'''
WEIGHT_CORE='''import math

def weighted_rows(rows, weights, *, empty_value=None):
    numeric_weights = [float(weight) for weight in weights]
    if any(math.isnan(weight) for weight in numeric_weights):
        raise ValueError("nan weight")
    if any(len(row) != len(numeric_weights) for row in rows):
        raise ValueError("shape mismatch")
    output = []
    for row in rows:
        numerator = 0.0
        denominator = 0.0
        for value, weight in zip(row, numeric_weights):
            if value is None:
                continue
            number = float(value)
            if math.isnan(number):
                continue
            numerator += number * weight
            denominator += weight
        if denominator == 0:
            output.append(empty_value)
        else:
            output.append(numerator / denominator)
    return output
'''
WEIGHT_API='''from weight_core import weighted_rows

def row_means(rows, weights, *, empty_value=None):
    return weighted_rows(rows, weights, empty_value=empty_value)

rowMeans = row_means
'''

CODE_SAMPLES={
 'zh':[
  'def frame_energy(frame):\n    energy = sum(sample * sample for sample in frame)\n    return energy\n',
  'def divide_or_zero(numerator, denominator):\n    # 分母可能因校准值抵消而为零。\n    if denominator == 0:\n        return 0.0\n    return numerator / denominator\n',
  'def active_keys(records):\n    return [record["key"] for record in records if record.get("active") is True]\n'],
 'en':[
  'def frame_energy(xs):\n    return sum(x * x for x in xs)\n',
  'def ratio_or_none(a, b):\n    # Zero denotes an unmeasured baseline.\n    return a / b if b else None\n',
  'def active_keys(rows):\n    return [r["key"] for r in rows if r.get("active") is True]\n']}


def test(identifier, group, module, function, args=None, kwargs=None):
    return {'id':identifier,'group':group,'module':module,'function':function,
            'args':args or [],'kwargs':kwargs or {}}


def code_case(identifier, language, files, public, tests, brief):
    return {'id':identifier,'domain':'code','language':language,'synthetic':True,
            'task':brief+' Rewrite both modules to fit the supplied project samples, preserving all observable public behavior, keyword calls, aliases, exception types/messages, ordering and input non-mutation. Do not fix unrelated behavior. Return exactly the two files. Only Python function definitions, same-package imports, math, literal constants and aliases are supported in this controlled fixture. No classes, file I/O or introspection.',
            'style_samples':CODE_SAMPLES[language], 'files':files,'public':public,'tests':tests,
            'available_checks':{'smoke':'ordinary examples','api_contract':'keyword signatures, aliases and exception behavior','edge_cases':'missing data, ordering and boundary cases'},
            'format':{'files':{'filename.py':'full source text'},'requested_checks':['at most two of smoke/api_contract/edge_cases'],'style_evidence':['brief sample-supported observations; no inferred author identity']}}


def build_code():
    nan=float('nan');inf=float('inf')
    series=code_case('dev-code-zh','zh',{'series_core.py':SERIES_CORE,'series_api.py':SERIES_API},
      [{'module':'series_api','function':name} for name in ('moving_average','movingAverage','valid_count')],
      [test('s-normal','smoke','series_api','moving_average',[[1,2,3],2]),
       test('s-keyword','api_contract','series_api','moving_average',kwargs={'values':[1,None,3],'width':2,'min_count':2}),
       test('s-alias','api_contract','series_api','movingAverage',[[0,False,2],2]),
       test('s-boolwidth','api_contract','series_api','moving_average',[[],True]),
       test('s-minerror','api_contract','series_api','moving_average',[[],2],{'min_count':0}),
       test('s-missing','edge_cases','series_api','moving_average',[[None,nan,0,False,4],3],{'min_count':2}),
       test('s-infinite','edge_cases','series_api','moving_average',[[inf,2,-inf],2]),
       test('s-count','edge_cases','series_api','valid_count',[[None,nan,0,False,inf]]),
       test('s-emptyinvalid','edge_cases','series_api','moving_average',[[],0])],
      'Trailing means include partial windows. None/NaN are missing, zero and False are present numeric data, and infinity remains valid for legacy compatibility. Validate width/min_count even with empty input.')
    events=code_case('dev-code-en','en',{'event_core.py':EVENT_CORE,'event_api.py':EVENT_API},
      [{'module':'event_api','function':name} for name in ('summarize_events','summarizeEvents')],
      [test('e-normal','smoke','event_api','summarize_events',[[{'key':'b','value':2},{'key':'a','value':1}]]),
       test('e-alias','api_contract','event_api','summarizeEvents',kwargs={'events':[{'key':'x','deleted':True}],'include_deleted':True}),
       test('e-error','api_contract','event_api','summarize_events',[[{'key':'a','version':True}]]),
       test('e-key','api_contract','event_api','summarize_events',[[{'value':1}]]),
       test('e-revisions','edge_cases','event_api','summarize_events',[[{'key':'b','version':2,'value':3},{'key':'a','value':None},{'key':'b','version':1,'value':9},{'key':'b','version':2,'value':0}]]),
       test('e-deleted','edge_cases','event_api','summarize_events',[[{'key':'a','deleted':1},{'key':'b','deleted':True},{'key':'c','deleted':'yes'}]]),
       test('e-negative','edge_cases','event_api','summarize_events',[[{'key':'b','version':-2},{'key':'b','value':4}]]),
       test('e-obsoleteinvalid','edge_cases','event_api','summarize_events',[[{'key':'a','version':2},{'key':'a','version':'old'}]])],
      'Highest integer version wins; the later input wins ties. Output key order is the first-seen key order. Missing version is zero; negative versions are valid; bool is not an integer version. Only deleted is True denotes deletion, not general truthiness. Validate every event, including obsolete ones.')
    buckets=code_case('holdout-code-zh','zh',{'bucket_core.py':BUCKET_CORE,'bucket_api.py':BUCKET_API},
      [{'module':'bucket_api','function':name} for name in ('bucket_report','bucketReport')],
      [test('b-normal','smoke','bucket_api','bucket_report',[[-1,0,1,2],[0,1]]),
       test('b-keyword','api_contract','bucket_api','bucket_report',kwargs={'values':[0,1],'boundaries':[0,1],'right':True}),
       test('b-alias','api_contract','bucket_api','bucketReport',[[1],[]]),
       test('b-sorted','api_contract','bucket_api','bucket_report',[[],[1,1]]),
       test('b-missing','edge_cases','bucket_api','bucket_report',[[None,nan,0,False,-inf,inf],[0,2]]),
       test('b-nonfinite','edge_cases','bucket_api','bucket_report',[[],[inf]]),
       test('b-coercion','edge_cases','bucket_api','bucket_report',[['0','2.5'],['0','2']]),
       test('b-empty','edge_cases','bucket_api','bucket_report',[[],[]])],
      'Finite strictly increasing boundaries are validated before values. Values may be None/NaN (missing), infinity (ordinary endpoint data) or numeric strings. right=False uses number < boundary; right=True uses <=. Preserve counts, missing count, copied float boundaries and result key order.')
    weights=code_case('holdout-code-en','en',{'weight_core.py':WEIGHT_CORE,'weight_api.py':WEIGHT_API},
      [{'module':'weight_api','function':name} for name in ('row_means','rowMeans')],
      [test('w-normal','smoke','weight_api','row_means',[[[1,3],[2,6]],[1,3]]),
       test('w-keyword','api_contract','weight_api','row_means',kwargs={'rows':[[None,None]],'weights':[1,2],'empty_value':'NA'}),
       test('w-alias','api_contract','weight_api','rowMeans',[[[1,None]],[1,2]]),
       test('w-shape','api_contract','weight_api','row_means',[[[1]],[1,2]]),
       test('w-missing','edge_cases','weight_api','row_means',[[[0,None,4],[False,nan,2]],[1,8,1]]),
       test('w-negative','edge_cases','weight_api','row_means',[[[2,5]],[-1,2]]),
       test('w-zero','edge_cases','weight_api','row_means',[[[1,2]],[1,-1]],{'empty_value':0}),
       test('w-nanweight','edge_cases','weight_api','row_means',[[],[nan]]),
       test('w-empty','edge_cases','weight_api','row_means',[[],['bad']])],
      'Convert and validate weights even if rows is empty. NaN weight is an error. For each row skip only None/NaN observations and their matching weights. Zero/False observations and negative weights remain valid. A zero remaining denominator returns empty_value without coercing its type.')
    return [series,events,buckets,weights]


if __name__=='__main__':
    def encode(value):
        if isinstance(value,float) and not math.isfinite(value):
            return {'$float':'nan' if math.isnan(value) else 'inf' if value>0 else '-inf'}
        if isinstance(value,list):return [encode(item) for item in value]
        if isinstance(value,dict):return {key:encode(item) for key,item in value.items()}
        return value
    code_tasks=build_code()
    tasks=code_tasks+build_text()
    cases={'development':[task for task in tasks if task['id'].startswith('dev-')],
           'holdout':[task for task in tasks if task['id'].startswith('holdout-')]}
    (ROOT/'cases.json').write_text(json.dumps(encode(cases),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    old=ROOT/'code_cases.json'
    if old.exists():old.unlink()
    print('Authored 12 synthetic complex tasks, balanced by domain and language.')
