"""Prepare an offline blind form; keep method mapping and seed private."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import secrets
import sqlite3

ROOT=Path(__file__).resolve().parents[1]
LOCAL=ROOT/'.local'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime',choices=['codex','claude','all'],default='all')
    args=parser.parse_args()
    db=sqlite3.connect(LOCAL/'ledger.sqlite')
    available=[]
    for runtime in ('codex','claude'):
        rows=db.execute('SELECT result FROM jobs WHERE stage="preflight" AND runtime=? AND status="completed"',(runtime,)).fetchall()
        if any(json.loads(row[0]).get('checks',{}).get('passed') for row in rows): available.append(runtime)
    runtimes=available if args.runtime=='all' else [r for r in available if r==args.runtime]
    if not runtimes: raise SystemExit('No runtime passed preflight')
    seed_path=LOCAL/'blind-seed.txt'
    if not seed_path.exists(): seed_path.write_text(str(secrets.randbits(128)))
    generator=random.Random(int(seed_path.read_text()))
    tasks=json.loads((ROOT/'evals/tasks.json').read_text())['main']
    pairs=[];mapping=[]

    def artifact(stage,runtime,task,condition):
        identifier='-'.join([stage,runtime,task['id'],condition])
        row=db.execute('SELECT status FROM jobs WHERE id=?',(identifier,)).fetchone()
        if not row or row[0]!='completed': raise SystemExit('Required output is not completed: '+identifier)
        return (LOCAL/'runs'/identifier/'artifact.txt').read_text()

    def add(task,runtime,other,stage):
        choices=[('ownvoice',artifact('main',runtime,task,'ownvoice')),
                 (other,artifact(stage,runtime,task,other))]
        generator.shuffle(choices)
        identifier='P'+str(len(pairs)+1).zfill(2)
        pairs.append({'id':identifier,'domain':task['domain'],'language':task['language'],
                      'mode':task['mode'],'task':task['packet'],'left':choices[0][1],'right':choices[1][1]})
        mapping.append({'id':identifier,'task':task['id'],'runtime':runtime,'other':other,
                        'left':choices[0][0],'right':choices[1][0]})

    for ri,runtime in enumerate(runtimes):
        for di,domain in enumerate(('code','research','email')):
            for li,language in enumerate(('zh','en')):
                group=[t for t in tasks if t['domain']==domain and t['language']==language]
                task=group[(di+li+ri)%len(group)]
                add(task,runtime,'plain' if (di+li+ri)%2==0 else 'upstream','main')
    for di,domain in enumerate(('code','research','email')):
        for li,language in enumerate(('zh','en')):
            runtime=runtimes[(di+li)%len(runtimes)]
            task=next(t for t in tasks if t['domain']==domain and t['language']==language)
            add(task,runtime,'mismatch','mismatch')
    (LOCAL/'blind-mapping.json').write_text(json.dumps(mapping,indent=2)+'\n')
    payload=json.dumps(pairs,ensure_ascii=False).replace('<','\\u003c')
    html=HTML.replace('/*PAIRS*/[]',payload)
    (LOCAL/'blind_review.html').write_text(html)
    (LOCAL/'blind-packet.json').write_text(json.dumps(pairs,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'pairs':len(pairs),'form':str(LOCAL/'blind_review.html'),
                      'seed_commitment':hashlib.sha256(seed_path.read_bytes()).hexdigest(),
                      'mapping_published':False},ensure_ascii=False))


HTML='''<!doctype html><html lang="zh"><meta charset="utf-8"><title>OwnVoice 盲评</title>
<style>body{font:16px system-ui;max-width:1200px;margin:28px auto;padding:0 20px;background:#faf9f6;color:#202323}article{background:white;border:1px solid #ddd;border-radius:12px;margin:24px 0;padding:24px}.cols{display:grid;grid-template-columns:1fr 1fr;gap:20px}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f5f3;padding:18px;line-height:1.5}fieldset{border:0;padding:8px 0}label{margin-right:18px}button{padding:12px 20px;font-size:16px}small{color:#666}@media(max-width:750px){.cols{grid-template-columns:1fr}}</style>
<h1>OwnVoice 成对评审</h1><p>请按自己的偏好比较。方法和运行工具名称已隐藏，允许平局。先看任务约束；如发现事实或功能问题，请记录。页面不联网、不上传答案。</p><main id="pairs"></main><button id="export">导出我的评审 JSON</button><p id="status"></p>
<script>const pairs=/*PAIRS*/[];const target=document.getElementById('pairs');
for(const p of pairs){const a=document.createElement('article');const title=document.createElement('h2');title.textContent=p.id+' · '+p.domain+' · '+p.language+' · '+p.mode;a.append(title);const task=document.createElement('p');task.textContent=p.task;a.append(task);const cols=document.createElement('div');cols.className='cols';for(const side of ['left','right']){const col=document.createElement('section');const h=document.createElement('h3');h.textContent=side==='left'?'左':'右';const pre=document.createElement('pre');pre.textContent=p[side];col.append(h,pre);cols.append(col)}a.append(cols);for(const [key,question]of [['style','哪个更符合你的表达习惯？'],['clarity','哪个更清楚？'],['use','哪个更愿意直接采用？']]){const field=document.createElement('fieldset');const legend=document.createElement('legend');legend.textContent=question;field.append(legend);for(const [value,text]of [['left','左'],['tie','平局'],['right','右']]){const label=document.createElement('label');const input=document.createElement('input');input.type='radio';input.name=p.id+'-'+key;input.value=value;label.append(input,document.createTextNode(text));field.append(label)}a.append(field)}const note=document.createElement('textarea');note.id=p.id+'-note';note.placeholder='可选：事实、功能问题或选择理由';note.rows=2;note.style.width='100%';a.append(note);target.append(a)}
document.getElementById('export').onclick=()=>{const answers=pairs.map(p=>{const r={id:p.id,note:document.getElementById(p.id+'-note').value};for(const key of ['style','clarity','use'])r[key]=document.querySelector('input[name="'+p.id+'-'+key+'"]:checked')?.value||null;return r});if(answers.some(a=>!a.style||!a.clarity||!a.use)){document.getElementById('status').textContent='请完成每组的三项选择，允许选平局。';return}const url=URL.createObjectURL(new Blob([JSON.stringify({schema_version:1,answers},null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='ownvoice-feedback.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);document.getElementById('status').textContent='已导出；页面没有发送任何网络请求。'};</script></html>'''


if __name__=='__main__': main()
