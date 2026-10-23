"""Fresh synthetic release tasks; public schemas specify every nested field."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def obj(properties):
    return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}


def shape(value):
    if value is None:return {'type':'null'}
    if isinstance(value,bool):return {'type':'boolean'}
    if isinstance(value,int):return {'type':'integer'}
    if isinstance(value,float):return {'type':'number'}
    if isinstance(value,str):return {'type':'string'}
    if isinstance(value,dict):return obj({k:shape(v) for k,v in value.items()})
    return {'type':'array','items':shape(value[0]) if value else {'type':'string'}}


def styles(domain,lang):
    if domain=='code':
        if lang=='zh':return [
            ['def total(xs):\n    return sum(x for x in xs if x is not None)\n',
             'def scale(xs, factor):\n    return [x * factor for x in xs]\n',
             'def valid(xs):\n    return [x for x in xs if x is not None]\n'],
            ['def total(values):\n    total_value = 0\n    for value in values:\n        if value is not None:\n            total_value += value\n    return total_value\n',
             'def scale(values, factor):\n    scaled_values = []\n    for value in values:\n        scaled_values.append(value * factor)\n    return scaled_values\n',
             'def valid(values):\n    valid_values = []\n    for value in values:\n        # 零值也属于有效观测。\n        if value is not None:\n            valid_values.append(value)\n    return valid_values\n']]
        return [
            ['def scale(xs, k):\n    return [x * k for x in xs]\n','def total(xs):\n    return sum(x for x in xs if x is not None)\n','def count(xs):\n    return sum(x is not None for x in xs)\n'],
            ['def scale(values, factor):\n    scaled_values = []\n    for value in values:\n        scaled_values.append(value * factor)\n    return scaled_values\n',
             'def total(values):\n    total_value = 0\n    for value in values:\n        if value is not None:\n            total_value += value\n    return total_value\n',
             'def count(values):\n    valid_count = 0\n    for value in values:\n        # Keep measured zeros.\n        if value is not None:\n            valid_count += 1\n    return valid_count\n']]
    if domain=='research':
        if lang=='zh':return [
            ['Cedar 样本的误差有所下降，但证据尚不足以支持外部推广。比较仅覆盖一个站点，独立验证仍待开展。',
             '这次观察提示了改进方向，但不能据此推断因果。尾部耗时仍有回退。',
             '目前只能确认本次样本中的变化。样本来自同一设备，其他设备上的结果未知。'],
            ['实验设置：我们先固定 Cedar 的输入队列，再比较两种配置。\n观测结果：误差下降，尾部耗时仍有回退。\n解释边界：同一站点的观察不能代替独立验证。',
             '实验设置：这次测量只覆盖一台设备。\n观测结果：中位耗时较低。\n解释边界：结果不能推及其他设备。',
             '实验设置：我们使用固定样本进行比较。\n观测结果：两项指标呈现权衡。\n解释边界：当前设计不支持因果推断。']]
        return [
            ['Error was lower on Cedar, but the result does not establish transfer. The comparison covered one site; independent validation is pending.',
             'The observed change supports another test, not a deployment guarantee. Tail latency increased.',
             'This is a sample-specific observation. We used one device. Other devices remain untested.'],
            ['Setup: We fixed the Cedar input queue before comparing configurations.\nObservation: Error fell while tail latency increased.\nLimit: A single-site comparison cannot establish transfer.',
             'Setup: We measured one device.\nObservation: Median runtime was lower.\nLimit: Independent-device validation is pending.',
             'Setup: We used the same sample for both configurations.\nObservation: The metrics showed a tradeoff.\nLimit: The design does not establish causation.']]
    if lang=='zh':return [
        ['Robin，请在周四前回复 Cedar 的修改意见。谢谢。','Lee，请在明天下午前发来可选时间。谢谢。','Sam，请在周五前把标注版发给我。谢谢。'],
        ['Robin，你好！\n\n想请你帮忙看一下 Cedar 的说明。需要你回复的内容是：\n- 修改意见；\n- 尚未解决的问题。\n请在周四前发给我。\n\n谢谢你的帮助！',
         'Lee，你好！\n\n想和你确认下周的安排：\n- 请列出可选时间；\n- 请说明时区。\n请在明天下午前回复。\n\n谢谢！',
         'Sam，你好！\n\n麻烦你整理材料：\n- 发来标注版；\n- 列出需要讨论的地方。\n请在周五前发给我。\n\n谢谢你的帮助！']]
    return [
        ['Robin, please send comments on Cedar by Thursday. Thanks.','Lee, please send the available times by tomorrow afternoon. Thanks.','Sam, please send the annotated draft by Friday. Thanks.'],
        ['Hi Robin,\n\nI would appreciate your help reviewing Cedar. Please send:\n- Your comments;\n- Any unresolved issues.\nPlease reply by Thursday.\n\nThank you for your help.',
         'Hi Lee,\n\nCould you help confirm next week’s arrangements? Please include:\n- Available times;\n- Their timezones.\nPlease reply by tomorrow afternoon.\n\nThank you.',
         'Hi Sam,\n\nI would appreciate your help preparing the material. Please send:\n- The annotated draft;\n- The points requiring discussion.\nPlease send these by Friday.\n\nThank you for your help.']]


def bundle(kind):
    if kind=='events':
        files={
          'rules.py':"""def valid_version(value):
    # Step 1: determine if the version is valid.
    version_value = value
    if isinstance(version_value, bool) or not isinstance(version_value, int):
        raise TypeError('version must be int')
    return version_value

def is_deleted(event):
    deleted_value = event.get('deleted')
    result = deleted_value is True
    return result
""",
          'merge.py':"""from rules import valid_version, is_deleted

def latest_events(events):
    # Step 1: create storage for each event.
    selected_events = {}
    for event in events:
        event_key = event['key']
        event_version = valid_version(event.get('version', 0))
        previous_event = selected_events.get(event_key)
        if previous_event is None or event_version >= previous_event[0]:
            selected_events[event_key] = (event_version, event)
    result_events = []
    for event_key, version_and_event in selected_events.items():
        event = version_and_event[1]
        if not is_deleted(event):
            result_events.append((event_key, event.get('value')))
    return result_events
""",
          'summary.py':"""def summarize_pairs(pairs):
    # Step 1: initialize the result.
    result_items = []
    for event_key, event_value in pairs:
        result_items.append({'key': event_key, 'value': event_value})
    result_count = len(result_items)
    return {'items': result_items, 'count': result_count}
""",
          'api.py':"""from merge import latest_events
from summary import summarize_pairs

def summarize_events(events, *, include_count=True):
    event_pairs = latest_events(events)
    result_summary = summarize_pairs(event_pairs)
    if not include_count:
        return result_summary['items']
    return result_summary

summarizeEvents = summarize_events
"""}
        public=[('api','summarize_events'),('api','summarizeEvents'),('merge','latest_events'),('rules','valid_version'),('rules','is_deleted'),('summary','summarize_pairs')]
        tests=[('normal',[{'key':'b','value':0},{'key':'a','value':False}],{}),
               ('versions',[{'key':'b','version':2,'value':1},{'key':'a','value':2},{'key':'b','version':2,'value':3}],{}),
               ('strict_deleted',[{'key':'a','deleted':1},{'key':'b','deleted':True},{'key':'c','deleted':'yes'}],{}),
               ('old_invalid',[{'key':'a','version':5},{'key':'a','version':False}],{}),
               ('empty',[],{}),('key_missing',[{'value':3}],{}),('no_count',[{'key':'x','value':None}],{'include_count':False})]
        task='Simplify the four-module event reducer, removing narration and redundant intermediates while matching the supplied style samples. Highest integer version wins; ties replace with the last event, first-seen key order stays, deleted is True only, every version is validated even for an obsolete event. Bool versions are invalid. Preserve all public functions, defaults, exception messages, aliases and nonmutation.'
        function='summarize_events'
    elif kind=='windows':
        files={
          'numbers.py':"""import math

def present(value):
    is_present = value is not None and not (isinstance(value, float) and math.isnan(value))
    return is_present

def numeric_values(values):
    result_values = []
    for value in values:
        if present(value):
            result_values.append(float(value))
    return result_values
""",
          'windows.py':"""from numbers import numeric_values

def trailing_mean(values, width, *, min_count=1, fill=None):
    # Step 1: check the arguments before proceeding.
    if isinstance(width, bool) or not isinstance(width, int) or width < 1:
        raise ValueError('invalid width')
    if isinstance(min_count, bool) or not isinstance(min_count, int) or min_count < 1:
        raise ValueError('invalid min_count')
    result_values = []
    for index in range(len(values)):
        start_index = max(0, index - width + 1)
        current_values = numeric_values(values[start_index:index + 1])
        current_count = len(current_values)
        if current_count >= min_count:
            current_mean = sum(current_values) / current_count
            result_values.append(current_mean)
        else:
            result_values.append(fill)
    return result_values
""",
          'summary.py':"""from numbers import numeric_values

def describe(values):
    # Step 1: gather valid measurements.
    measured_values = numeric_values(values)
    count_value = len(measured_values)
    minimum_value = min(measured_values) if measured_values else None
    maximum_value = max(measured_values) if measured_values else None
    return {'count': count_value, 'minimum': minimum_value, 'maximum': maximum_value}
""",
          'api.py':"""from windows import trailing_mean
from summary import describe

def moving_report(values, width=3, *, min_count=1, fill=None):
    copied_values = list(values)
    mean_values = trailing_mean(copied_values, width, min_count=min_count, fill=fill)
    summary_values = describe(copied_values)
    return {'means': mean_values, 'summary': summary_values}

movingReport = moving_report
"""}
        public=[('api','moving_report'),('api','movingReport'),('windows','trailing_mean'),('numbers','present'),('numbers','numeric_values'),('summary','describe')]
        tests=[('normal',[1,2,3],{}),('partial',[0,False,None,4],{'width':2}),('missing',[None,{'$float':'nan'},0,False,'5'],{'width':3,'min_count':2}),
               ('infinite',[{'$float':'inf'},1,{'$float':'-inf'}],{'width':2}),('fill',[None,None,3],{'fill':'missing','min_count':2}),
               ('empty_bad',[],{'width':False}),('min_bad',[],{'min_count':0}),('large',[1,2],{'width':9}),('empty',[],{})]
        task='Simplify the four-module rolling report and match the provided samples. Trailing partial windows are used. Only None and float NaN are missing; 0/False and infinities remain observations, numeric strings are converted. Validate width and min_count even for empty input. Return fill unchanged for insufficient observations. Preserve every public function, keyword default, alias, dictionary key order, exceptions and input nonmutation.'
        function='moving_report'
    else:
        files={
          'weights.py':"""import math

def checked_weights(weights):
    converted_weights = [float(value) for value in weights]
    for weight in converted_weights:
        if not math.isfinite(weight):
            raise ValueError('weights must be finite')
    return converted_weights
""",
          'selection.py':"""def select_rows(events):
    selected_events = {}
    for event in events:
        event_key = event['key']
        version_value = event.get('version', 0)
        if isinstance(version_value, bool) or not isinstance(version_value, int):
            raise TypeError('version must be int')
        if event_key not in selected_events or version_value >= selected_events[event_key][0]:
            selected_events[event_key] = (version_value, event)
    result_rows = []
    for event_key, version_and_event in selected_events.items():
        selected_event = version_and_event[1]
        if selected_event.get('deleted') is not True:
            result_rows.append((event_key, selected_event['values']))
    return result_rows
""",
          'means.py':"""import math

def weighted_mean(values, weights, *, empty_value=None):
    if len(values) != len(weights):
        raise ValueError('length mismatch')
    numerator_value = 0.0
    denominator_value = 0.0
    for value, weight in zip(values, weights):
        if value is None or (isinstance(value, float) and math.isnan(value)):
            continue
        numerator_value += float(value) * weight
        denominator_value += weight
    if denominator_value == 0:
        return empty_value
    return numerator_value / denominator_value
""",
          'api.py':"""from weights import checked_weights
from selection import select_rows
from means import weighted_mean

def weighted_summary(events, weights, *, empty_value=None):
    converted_weights = checked_weights(weights)
    selected_rows = select_rows(events)
    keys_result = []
    means_result = []
    for event_key, row_values in selected_rows:
        keys_result.append(event_key)
        mean_value = weighted_mean(row_values, converted_weights, empty_value=empty_value)
        means_result.append(mean_value)
    return {'keys': keys_result, 'means': means_result, 'count': len(keys_result)}

weightedSummary = weighted_summary
"""}
        public=[('api','weighted_summary'),('api','weightedSummary'),('weights','checked_weights'),('selection','select_rows'),('means','weighted_mean')]
        tests=[('normal',[{'key':'b','values':[0,False,4]},{'key':'a','values':[1,2,3]}],[1,1,2],{}),
               ('missing',[{'key':'a','values':[None,{'$float':'nan'},0]}],[5,4,2],{}),
               ('zero_weight',[{'key':'a','values':[3,3]}],[1,-1],{'empty_value':'empty'}),
               ('version',[{'key':'b','values':[2]},{'key':'a','values':[1]},{'key':'b','version':1,'values':[9]}],[1],{}),
               ('strict_delete',[{'key':'x','deleted':1,'values':[0]},{'key':'y','deleted':True,'values':[9]}],[1],{}),
               ('shape',[{'key':'a','values':[1]}],[1,2],{}),('bad_empty',[],[{'$float':'nan'}],{}),('empty',[],[1],{}),
               ('version_bool',[{'key':'a','version':True,'values':[0]}],[1],{})]
        task='Simplify the four-module versioned weighted report and match the supplied samples. Convert and validate all weights before reading any events, including empty inputs. Highest integer version wins, equal versions replace last, first-seen key order stays, and only deleted is True removes a row. Bool versions are invalid. Skip only None/float NaN observations and their matching weights; retain zeros, False and negative weights. Return empty_value uncast for a zero denominator. Preserve public functions/defaults/aliases, validation order, exceptions, key order and nonmutation.'
        function='weighted_summary'
    fixtures=[]
    for index,case in enumerate(tests):
        if kind=='weights':name,events,weights,kwargs=case;args=[events,weights]
        else:name,values,kwargs=case;args=[values]
        fixtures.append({'id':name,'module':'api','function':function,'args':args,'kwargs':kwargs,'group':'visible' if index<2 else 'independent'})
    fixtures.append({'id':'public-alias','module':'api','function':{'events':'summarizeEvents','windows':'movingReport','weights':'weightedSummary'}[kind],
                     'args':fixtures[0]['args'],'kwargs':fixtures[0]['kwargs'],'group':'independent'})
    return files,public,fixtures,task


def code(identifier,lang,kind):
    files,public,tests,task=bundle(kind)
    schema=obj({'files':obj({name:{'type':'string'} for name in files}), 'style_evidence':{'type':'array','items':{'type':'string'}}})
    return {'id':identifier,'domain':'code','language':lang,'synthetic':True,'task':task+
            ' Return exactly all four full files. This controlled fixture permits only functions, allowed imports, literal module constants and aliases; no classes, module docstrings or introspection. Imports may name these modules or math only. Existing public names must not change. Chinese comments for zh, English for en.',
            'files':files,'public':[{'module':m,'function':f} for m,f in public], 'tests':tests,
            'output_schema':schema,'constraints':{'schema_version':1,'assertions':[]},'style_sets':styles('code',lang)}


def research(identifier,lang,kind):
    if kind=='latency':
        sources=[{'id':'D1','status':'superseded','cohort':'dev','n':110,'before_seconds':.58,'after_seconds':.47},
                 {'id':'D2','status':'correction_of_D1','cohort':'dev','n':92,'before_seconds':.58,'after_seconds':.55,'ci95_reduction_ms':[-8,68],'design':'single-device observational comparison'},
                 {'id':'D3','energy_before_J_per_run':27,'energy_after_J_per_run':30,'scope':'same engineering run, not an independent sample'},
                 {'id':'D4','independent_n':None,'deployment_effect':None,'status':'not tested'},
                 {'id':'D5','status':'unrelated simulation','n':800,'note':'not observations from this cohort'}]
        facts={'n':92,'before_ms':580.,'after_ms':550.,'reduction_ms':30.,'ci95_reduction_ms':[-8,68],
               'energy_delta_J':3.,'energy_increase_percent':11.1111,'independent_n':None,'deployment_effect':None,'significant_95':False,'causal_supported':False}
        mapping={'primary':['D2'],'tradeoff':['D3'],'unknowns':['D4']}
        task='Discuss latency in milliseconds and energy per run. Round the energy percentage increase to four decimal places. One second is 1000 ms.'
    elif kind=='accuracy':
        sources=[{'id':'N1','status':'superseded','cohort':'north','n':158,'accuracy_before':.83,'accuracy_after':.90},
                 {'id':'N2','status':'correction_of_N1','cohort':'north','n':132,'accuracy_before':.83,'accuracy_after':.86,'ci95_gain_pp':[-.5,6.5],'design':'one observational comparison; no causal identification'},
                 {'id':'N3','false_positive_before':.07,'false_positive_after':.09,'metric_direction':'higher is worse','scope':'same cohort'},
                 {'id':'N4','independent_n':None,'peak_memory_MB':None,'status':'not measured'},
                 {'id':'N5','status':'different population','n':640,'note':'not this study or independent validation'}]
        facts={'n':132,'accuracy_before':.83,'accuracy_after':.86,'gain_pp':3.,'ci95_gain_pp':[-.5,6.5],
               'false_positive_delta_pp':2.,'independent_n':None,'peak_memory_MB':None,'significant_95':False,'causal_supported':False}
        mapping={'primary':['N2'],'tradeoff':['N3'],'unknowns':['N4']}
        task='Discuss the accuracy and false-positive tradeoff in Chinese. Rate differences multiplied by 100 are percentage points, not relative percentage increases.'
    else:
        sources=[{'id':'W1','status':'superseded','cohort':'west','n':90,'mean_energy_before_kWh':.48,'mean_energy_after_kWh':.39},
                 {'id':'W2','status':'correction_of_W1','cohort':'west','n':74,'mean_energy_before_kWh':.48,'mean_energy_after_kWh':.45,'ci95_reduction_kWh':[-.01,.07],'design':'one observational run; no causal identification'},
                 {'id':'W3','peak_before_kW':1.8,'peak_after_kW':2.1,'scope':'same run, not an independent energy sample'},
                 {'id':'W4','independent_n':None,'cost_savings':None,'note':'independent test not run; price information absent'},
                 {'id':'W5','status':'unrelated engineering projection','n':2000,'note':'not measured data from this cohort'}]
        facts={'n':74,'reduction_kWh':.03,'reduction_kJ':108.,'relative_reduction_percent':6.25,'ci95_reduction_kWh':[-.01,.07],
               'peak_delta_kW':.3,'independent_n':None,'cost_savings':None,'significant_95':False,'causal_supported':False}
        mapping={'primary':['W2'],'tradeoff':['W3'],'unknowns':['W4']}
        task='Discuss mean energy versus peak power in English. Include the absolute and relative energy reduction. 1 kWh = 3600 kJ. Do not infer price or cost savings.'
    schema=obj({'artifact':{'type':'string'},'facts':shape(facts),'source_map':shape(mapping),'style_evidence':{'type':'array','items':{'type':'string'}}})
    assertions=[{'op':'equal','path':'/facts/'+key,'expected':value,'tolerance':1e-8} for key,value in facts.items()]
    for key,value in mapping.items():assertions.append({'op':'equal','path':'/source_map/'+key,'expected':value})
    for source_id in {x for values in mapping.values() for x in values}:assertions.append({'op':'contains','path':'/artifact','value':source_id})
    for canary in ('Cedar','Robin'):assertions.append({'op':'not_contains','path':'/artifact','value':canary})
    return {'id':identifier,'domain':'research','language':lang,'synthetic':True,'task':task+
            ' Use only supplied sources. Corrections replace old versions of the same cohort; never pool them. Keep null unknown, distinguish a confidence interval crossing zero from a measured null effect, and preserve observational scope. Put supporting source IDs next to claims in the prose. source_map.primary names the corrected measurement, tradeoff the resource/risk record, unknowns the unmeasured-status record. Match style samples without copying their facts.',
            'sources':sources,'output_schema':schema,'constraints':{'schema_version':1,'assertions':assertions},'style_sets':styles('research',lang)}


def email(identifier,lang,kind):
    if kind=='availability':
        sender,to,cc,doc,amount,currency,deadline='Terry',['Milan'],[],'NOTE-J82',460,'EUR','2026-12-03'
        actions=[{'actor':'Milan','action':'confirm_availability','recipient':sender,'deadline':deadline}]
        history=['The old message requested a completed review by 2026-12-03. That has been superseded.','Current request: reply whether available by the date; it is not a deadline to do the review. Payment has not been approved.']
    elif kind=='availability_zh':
        sender,to,cc,doc,amount,currency,deadline='Ning',['Kai'],['Morgan'],'DRAFT-V47',1120,'CNY','2027-01-14'
        actions=[{'actor':'Kai','action':'confirm_availability','recipient':sender,'deadline':deadline}]
        history=['An older message asked Morgan to finish the review on 2027-01-14.','Correction: Kai only needs to reply whether available by 2027-01-14. Morgan is CC only. No review completion date is set; no payment is approved.']
    else:
        sender,to,cc,doc,amount,currency,deadline='Taylor',['Quinn','Eden'],['Sage'],'CAL-R95',680,'USD','2027-01-20'
        actions=[{'actor':'Quinn','action':'select_slot','recipient':sender,'deadline':deadline},
                 {'actor':'Eden','action':'send_annotation_template','recipient':sender,'deadline':'2027-01-21'}]
        history=['An old thread confirmed the first meeting and said Finance had approved payment.','Correction: neither meeting nor payment is approved. Ask Quinn to choose; Eden only sends the annotation template. Sage is CC, with no action.']
    brief={'sender':sender,'to':to,'cc':cc,'recipient_actions':actions,
           'context':{'document_id':doc,'amount':amount,'currency':currency,'role':'context'},
           'meeting_status':'unconfirmed','approval_status':'not_approved','payment_date':None}
    ledger={'to':to,'cc':cc,'recipient_actions':actions,'context_refs':[doc],
            'amounts':[{'amount':amount,'currency':currency,'role':'context'}], 'commitments':[],
            'meeting_status':'unconfirmed','approval_status':'not_approved','payment_date':None}
    if kind=='slots':
        brief['slots_UTC']=['2027-01-24 19:00','2027-01-25 02:00']
        brief['timezone_conversion']='Add eight hours; retain the resulting calendar dates. Display Hong Kong time UTC+08:00.'
        ledger['slots_local']=['2027-01-25 03:00 +08:00','2027-01-25 10:00 +08:00']
    schema=obj({'artifact':{'type':'string'},'ledger':shape(ledger),'style_evidence':{'type':'array','items':{'type':'string'}}})
    assertions=[{'op':'equal','path':'/ledger/'+key,'expected':value} for key,value in ledger.items()]
    for token in (doc,currency):assertions.append({'op':'contains','path':'/artifact','value':token})
    for canary in ('Cedar','Robin'):assertions.append({'op':'not_contains','path':'/artifact','value':canary})
    return {'id':identifier,'domain':'email','language':lang,'synthetic':True,'task':
            'Draft the email from the authoritative current brief. Mention the document ID and amount/currency as background, not a payment or confirmation request. Current recipient_actions replace quoted history; preserve their exact machine action codes in the ledger. Replying about availability is not performing a review by that date. All deadlines are firm. Only the listed actors have actions; CC creates no action. Preserve unconfirmed/not-approved status and unknown payment_date. In the structured ledger, dates must be ISO and slots_local must use YYYY-MM-DD HH:MM +08:00; free prose may use natural dates. Keep document and currency ISO tokens exact in prose. Never send. Match expression only from the samples.',
            'current_brief':brief,'quoted_history':history,'output_schema':schema,'constraints':{'schema_version':1,'assertions':assertions},'style_sets':styles('email',lang)}


def build():
    return {'development':[code('dev-event-zh','zh','events'),research('dev-latency-en','en','latency'),email('dev-availability-en','en','availability')],
            'holdout':[code('hold-window-zh','zh','windows'),code('hold-weight-en','en','weights'),
                       research('hold-accuracy-zh','zh','accuracy'),research('hold-energy-en','en','energy'),
                       email('hold-availability-zh','zh','availability_zh'),email('hold-calendar-en','en','slots')]}


if __name__=='__main__':
    (HERE/'cases.json').write_text(json.dumps(build(),ensure_ascii=False,indent=2,allow_nan=False)+'\n')
