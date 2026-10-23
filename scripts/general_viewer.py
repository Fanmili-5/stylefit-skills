"""Build an offline comparison viewer; raw outputs stay under .local/."""
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[1]


def main():
    cases = json.loads((ROOT / 'evals/general_v1/cases.json').read_text())
    tasks = {task['id']: task for stage in ('development', 'holdout') for task in cases[stage]}
    with sqlite3.connect(ROOT / '.local/ledger.sqlite') as db:
        rows = db.execute('SELECT id,result FROM jobs WHERE stage IN (?,?) AND status="completed"',
                          ('general-v1-development', 'general-v1-holdout')).fetchall()
    groups = {}
    review_path = ROOT / '.local/general-v1/manual-review.json'
    reviews = {row['job_id']: row['fidelity'] for row in json.loads(review_path.read_text())} if review_path.exists() else {}
    for identifier, result in rows:
        row = json.loads(result)
        task = tasks[row['case_id']]
        skill = ROOT / '.local/general-v1' / row['phase'] / 'skills' / ('ownvoice-' + task['domain']) / 'SKILL.md'
        version = re.search(r'version: "([^"]+)"', skill.read_text()).group(1)
        group = groups.setdefault(task['id'], {
            'id': task['id'], 'domain': task['domain'], 'language': task['language'],
            'mode': task['mode'], 'task': task['packet'], 'source': task.get('source'),
            'candidate_version': version, 'methods': {}})
        group['methods'].setdefault(row['condition'], {})[row['profile']] = {
            'artifact': (ROOT / '.local/runs' / identifier / 'artifact.txt').read_text(),
            'content_passed': row['checks']['passed'],
            'style_probe_passed': row['checks']['style']['passed'],
            'internal_fidelity_review': reviews.get(identifier, 'not_reviewed')}
    payload = json.dumps({'tasks': list(groups.values()), 'profiles': cases['profiles']}, ensure_ascii=False)
    payload = payload.replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    path = ROOT / '.local/general-v1/compare.html'
    path.write_text(HTML.replace('/*DATA*/{}', payload))
    print(json.dumps({'viewer': str(path), 'tasks': len(groups), 'network_requests': False}, ensure_ascii=False))


HTML = '''<!doctype html><html lang="zh"><meta charset="utf-8"><title>通用适配对照</title>
<style>body{font:16px system-ui;margin:32px auto;max-width:1600px;padding:0 24px;color:#202724;background:#f6f7f4}h1{margin-bottom:8px}p{line-height:1.6}.controls{display:flex;gap:12px;flex-wrap:wrap;margin:24px 0}select{font:inherit;padding:10px;max-width:100%}.cols{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:18px}section{background:white;padding:20px;border:1px solid #d8ddd7;border-radius:12px}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.6 ui-monospace,monospace}small{color:#516357}.guide{font-size:14px;min-height:90px;color:#516357}.checks{border-top:1px solid #ddd;padding-top:12px;font-size:13px}details{margin:16px 0}summary{cursor:pointer}#packet{background:white;padding:16px;border-radius:8px}@media(max-width:1000px){.cols{grid-template-columns:1fr}.guide{min-height:0}}</style>
<h1>通用适配对照 · 冻结的 v1 样例</h1><p>同一任务，比较不提供档案及两组相反的合成偏好。这里展示生成时的冻结快照，当前工作目录可能已有补丁；不代表真实多人效果，也不是作者或检测器评分。自动通过不等于语义保真，请同时查看内部复核状态。页面离线运行，不收集问卷。</p>
<div class="controls"><select id="task" aria-label="选择任务"></select><select id="method" aria-label="选择方法"><option value="ownvoice">OwnVoice（冻结快照）</option><option value="plain">普通提示</option></select></div>
<details><summary>任务约束与改写前原文</summary><pre id="packet"></pre></details><main class="cols" id="columns"></main>
<script>const data=/*DATA*/{};const taskSelect=document.getElementById('task');const methodSelect=document.getElementById('method');
for(const task of data.tasks){const option=document.createElement('option');option.value=task.id;option.textContent=task.id+' · '+task.domain+' · '+task.language+' · '+task.mode;taskSelect.append(option)}
function render(){const task=data.tasks.find(t=>t.id===taskSelect.value);if(!task)return;document.getElementById('packet').textContent=task.task+(task.source?'\\n\\n改写前原文：\\n'+task.source:'');const columns=document.getElementById('columns');columns.replaceChildren();for(const [profile,title]of [['none','不提供档案'],['compact','紧凑偏好'],['expanded','展开偏好']]){const section=document.createElement('section');const heading=document.createElement('h2');heading.textContent=title;const guide=document.createElement('p');guide.className='guide';guide.textContent=profile==='none'?'未传入档案或偏好。':data.profiles[profile][task.domain].join(' ');const artifact=document.createElement('pre');const result=task.methods[methodSelect.value]?.[profile];artifact.textContent=result?.artifact||'尚无完成结果';const checks=document.createElement('p');checks.className='checks';const review=result?.internal_fidelity_review;const reviewText=review==='unclear'?'待澄清（编号的发件人/收件人职责有歧义）':review==='supported_by_packet'?'在该材料范围内未发现问题，非独立复核':'未完成';checks.textContent=result?'自动内容检查：'+(result.content_passed?'通过':'未通过')+'；响应指标：'+(result.style_probe_passed?'通过':'未通过')+'；内部复核：'+reviewText+'。':'';if(review==='unclear')checks.style.color='#8c4d0a';section.append(heading,guide,artifact,checks);columns.append(section)}}
taskSelect.onchange=render;methodSelect.onchange=render;render();</script></html>'''


if __name__ == '__main__':
    main()
