"""Build synthetic, redistributable fixtures. Never build personal profiles here."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def code(identifier, language, mode, function, parameters, contract, source, tests):
    return {'id': identifier, 'domain': 'code', 'language': language, 'mode': mode,
            'packet': contract, 'source': source if mode == 'rewrite' else None,
            'function': function, 'parameters': parameters, 'tests': tests,
            'synthetic': True}


def build():
    tasks = []
    specifications = [
        ('zh', 'select_active', ['records'],
         'Return records whose active field equals True (not general truthiness), in original order. None returns []. Do not mutate records.',
         'def select_active(records):\n    # Initialize result\n    selected_records = []\n    if records is None:\n        return selected_records\n    for record in records:\n        if record.get("active") == True:\n            selected_records.append(record)\n    return selected_records\n',
         [{'args':[None],'expected':[]},{'args':[[]],'expected':[]},
          {'kwargs':{'records':[{'active':True},{'active':2},{'active':'yes'},{'active':1},{}]},'expected':[{'active':True},{'active':1}]}]),
        ('zh', 'weighted_mean', ['values','weights'],
         'Compute sum(value*weight)/sum(weights), returning float. Empty input, unequal lengths or zero total weight raise ValueError. Accept keyword arguments. Do not mutate inputs.', '',
         [{'args':[[2,8],[1,3]],'expected':6.5,'return_type':'float'}, {'args':[[],[]],'error':'ValueError'},
          {'args':[[1],[0]],'error':'ValueError'}, {'args':[[1,2],[1]],'error':'ValueError'},
          {'kwargs':{'values':[0,4],'weights':[1,1]},'expected':2.0,'return_type':'float'}]),
        ('zh', 'clamp_values', ['values','low','high'],
         'Return a new list with each value clamped to inclusive low/high. low > high raises ValueError. Preserve input and support empty lists and keyword arguments.',
         'def clamp_values(values, low, high):\n    if low > high:\n        raise ValueError("invalid bounds")\n    result_values = []\n    # Process the individual values\n    for value in values:\n        result_values.append(min(high, max(low, value)))\n    return result_values\n',
         [{'args':[[-2,0,4],0,3],'expected':[0,0,3]}, {'args':[[],0,3],'expected':[]},
          {'args':[[1],3,0],'error':'ValueError'}, {'kwargs':{'values':[1,9],'low':2,'high':2},'expected':[2,2]}]),
        ('zh', 'overlap_add', ['windows','step'],
         'Sum equally sized nonempty windows into a new list at starts i*step, adding overlaps. Empty windows list returns []. step must be positive; unequal/empty inner windows raise ValueError. No imports; do not mutate inputs.', '',
         [{'args':[[[1,2,3],[4,5,6]],2],'expected':[1,2,7,5,6]}, {'args':[[],1],'expected':[]},
          {'args':[[[1]],0],'error':'ValueError'}, {'args':[[[1,2],[3]],1],'error':'ValueError'},
          {'kwargs':{'windows':[[1,2],[3,4]],'step':1},'expected':[1,5,4]}]),
        ('en', 'filter_enabled', ['items'],
         'Return item names when enabled is exactly the boolean True (identity), preserving order. None returns []. Missing enabled is false. Do not mutate inputs.',
         'def filter_enabled(items):\n    result_names = []\n    if items is None:\n        return result_names\n    # Iterate over the supplied items\n    for item in items:\n        if item.get("enabled") is True:\n            result_names.append(item["name"])\n    return result_names\n',
         [{'args':[None],'expected':[]},{'args':[[]],'expected':[]},
          {'kwargs':{'items':[{'name':'A','enabled':True},{'name':'B','enabled':1},{'name':'C','enabled':'yes'}]},'expected':['A']}]),
        ('en', 'normalize_weights', ['weights'],
         'Return new float weights divided by their sum. Empty returns []. Any negative weight or nonempty zero total raises ValueError. Keep inputs unchanged.', '',
         [{'args':[[1,3]],'expected':[0.25,0.75]}, {'args':[[]],'expected':[]},
          {'args':[[0,0]],'error':'ValueError'}, {'args':[[-1,2]],'error':'ValueError'},
          {'kwargs':{'weights':[2]},'expected':[1.0]}]),
        ('en', 'moving_average', ['values','width'],
         'Return means for complete consecutive windows of positive integer width. Width <= 0 raises ValueError. Width larger than input returns []. Do not mutate input.',
         'def moving_average(values, width):\n    if width <= 0:\n        raise ValueError("width must be positive")\n    average_results = []\n    # Compute the average for each complete window\n    for index in range(len(values) - width + 1):\n        average_results.append(sum(values[index:index+width]) / width)\n    return average_results\n',
         [{'args':[[1,3,5],2],'expected':[2.0,4.0]}, {'args':[[],2],'expected':[]},
          {'args':[[1],2],'expected':[]}, {'args':[[1],0],'error':'ValueError'},
          {'kwargs':{'values':[3,7],'width':1},'expected':[3.0,7.0]}]),
        ('en', 'merge_counts', ['left','right'],
         'Return a new dictionary adding numeric counts for matching keys. Neither input is mutated. Empty dictionaries are valid. Keep zero totals as explicit keys.', '',
         [{'args':[{'a':2,'b':1},{'a':-2,'c':3}],'expected':{'a':0,'b':1,'c':3}},
          {'args':[{},{}],'expected':{}}, {'kwargs':{'left':{'a':0},'right':{}},'expected':{'a':0}}]),
    ]
    for index, (language, function, parameters, contract, source, tests) in enumerate(specifications):
        mode = 'rewrite' if source else 'generate'
        tasks.append(code('main-code-' + language + '-' + str(index % 4), language, mode, function, parameters, contract, source, tests))

    research = [
        ('40','3','Observed accuracy gain on this sample; independent validation remains necessary.','[S1]', ['independent','独立']),
        ('120','0.20','An observational association; no causal conclusion is justified.','[S2]', ['causal','因果']),
        ('64','12','Latency decreased by 12 ms on this benchmark; it is not a deployment guarantee.','[S3]', ['guarantee','保证']),
        ('80','0.04','The measured error changed by 0.04; the result is preliminary.','[S4]', ['preliminary','初步']),
    ]
    for language in ('zh','en'):
        for i, (n, value, limitation, citation, markers) in enumerate(research):
            packet = ('Synthetic source packet, not a real publication: sample size = ' + n + '. Measured value = ' + value + '. ' + limitation + ' Source identifier ' + citation + '. Preserve these quantities and this scope. Do not invent a publication or additional numbers.')
            source = ('本实验样本量为' + n + '，测量值为' + value + '。' + {'0':'准确率在此样本上提高3个百分点，仍需独立验证。','1':'结果为观察性关联，不能得出因果结论。','2':'此基准延迟降低12 ms，不构成部署效果保证。','3':'误差变化为0.04，结果仍属初步。'}[str(i)] + citation) if language=='zh' else ('The sample size was ' + n + ' and the measured value was ' + value + '. ' + limitation + ' ' + citation)
            tasks.append({'id':f'main-research-{language}-{i}','domain':'research','language':language,
                          'mode':'rewrite' if i%2==0 else 'generate','packet':packet,
                          'source':source if i%2==0 else None,'protected':[n,value,citation],
                          'required_any':[markers],'forbidden':['statistically significant','统计显著'], 'synthetic':True})
    for language in ('zh','en'):
        for i, (name, deadline, item) in enumerate([('Alex','2026-11-06','comments'),('Maya','2026-11-09','invoice'),('Sam','2026-11-12','meeting options'),('Lee','2026-11-16','revised draft')]):
            packet = f'Synthetic email scenario. Address {name}, a familiar colleague. Request {item} by the firm date {deadline}. Do not promise delivery, acceptance, payment or a meeting. No attachment has been supplied. Preserve the name and ISO date exactly. '
            if i==1:
                packet += 'The invoice amount to confirm is USD 250. Do not commit to paying it.'
            source = f'{name}，麻烦在{deadline}前发来{item}，谢谢。' if language=='zh' else f'{name}, please send {item} by {deadline}. Thanks.'
            if i==1: source += ' USD 250.'
            tasks.append({'id':f'main-email-{language}-{i}','domain':'email','language':language,
                          'mode':'rewrite' if i%2==0 else 'generate','packet':packet,
                          'source':source if i%2==0 else None,'protected':[name,deadline]+(['USD 250'] if i==1 else []),
                          'required_any':[], 'forbidden':['I guarantee','我保证','attached file','附件已附'], 'synthetic':True})
    pilot=[]
    for language in ('zh','en'):
        pilot.append(code('pilot-code-'+language,language,'rewrite','positive_total',['values'],
                          'Return sum of values strictly greater than zero. Empty returns 0; no mutation.',
                          'def positive_total(values):\n    # Initialize the total\n    positive_value_total = 0\n    for value in values:\n        if value > 0:\n            positive_value_total += value\n    return positive_value_total\n',
                          [{'args':[[-2,0,3,7]],'expected':10},{'args':[[]],'expected':0},{'kwargs':{'values':[0]},'expected':0}]))
        pilot.append({'id':'pilot-research-'+language,'domain':'research','language':language,'mode':'rewrite',
                      'packet':'Synthetic pilot: sample size 25, observed gain 2 percentage points [P1]. Independent validation is necessary.',
                      'source':'In 25 samples we observed a 2-point gain [P1]. Independent validation is necessary.',
                      'protected':['25','2','[P1]'],'required_any':[['independent','独立']],'forbidden':[],'synthetic':True})
        pilot.append({'id':'pilot-email-'+language,'domain':'email','language':language,'mode':'generate',
                      'packet':'Synthetic pilot. Ask Dana for the agenda by 2026-11-03. Do not promise attendance.',
                      'source':None,'protected':['Dana','2026-11-03'],'required_any':[],'forbidden':[],'synthetic':True})
    assert len(tasks)==24 and len(pilot)==6
    (ROOT/'tasks.json').write_text(json.dumps({'pilot':pilot,'main':tasks},ensure_ascii=False,indent=2)+'\n')
    print('Wrote 6 development and 24 formal synthetic fixtures.')


if __name__ == '__main__':
    build()
