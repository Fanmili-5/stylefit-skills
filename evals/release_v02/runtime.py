"""Append-only Luna-only CLI execution for the authorized 0.2 round."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import subprocess
import tempfile
import time

ROOT=Path(__file__).resolve().parents[2]
LOCAL=ROOT/'.local/release-v02'
MODEL='gpt-6-luna'
EFFORT='medium'
CAP=120
STAGE_CAPS={'preflight':2,'development':18,'smoke':6,'holdout':72,'judge':9,'native':8,'retry':5}
spec=importlib.util.spec_from_file_location('v02_legacy_cli',ROOT/'scripts/evaluate.py')
legacy=importlib.util.module_from_spec(spec);spec.loader.exec_module(legacy)


def reserve(identifier,stage):
    if not identifier.startswith('ownvoice-v02-') or stage not in STAGE_CAPS:raise ValueError('Invalid 0.2 job')
    authorization=json.loads((LOCAL/'authorization.json').read_text())
    if authorization!={'baseline':239,'additional_cap':120,'lifetime_cap':359,'model':MODEL,'effort':EFFORT}:
        raise RuntimeError('Authorization mismatch')
    with sqlite3.connect(ROOT/'.local/ledger.sqlite',timeout=20) as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT 1 FROM jobs WHERE id=?',(identifier,)).fetchone():return False
        total=db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
        used=db.execute('SELECT COUNT(*) FROM jobs WHERE id LIKE "ownvoice-v02-%"').fetchone()[0]
        staged=db.execute('SELECT COUNT(*) FROM jobs WHERE stage=?',('ownvoice-v02-'+stage,)).fetchone()[0]
        if total>=359 or used>=CAP or staged>=STAGE_CAPS[stage]:raise RuntimeError('Authorized budget exhausted')
        db.execute('INSERT INTO jobs VALUES(?,?,?,?,?,?,?)',(identifier,'ownvoice-v02-'+stage,MODEL,'started',time.time(),None,None))
    return True


def command(prompt,schema_path=None,native=False,cwd=None):
    args=['codex','exec','--model',MODEL,'-c','model_reasoning_effort='+EFFORT,'--json','--ephemeral','--skip-git-repo-check',
          '--disable','plugins','--disable','apps','--disable','hooks','--disable','computer_use','--color','never',
          '-c','tools.web_search=false','-c','developer_instructions=""','-s','workspace-write' if native else 'read-only']
    if not native:args+=['--enable','skip_host_skill_discovery','--disable','shell_tool']
    else:
        disabled=[]
        for root in (Path.home()/'.codex/skills',Path.home()/'.agents/skills'):
            if root.exists():disabled.extend(str(p) for p in root.rglob('SKILL.md'))
        entries=','.join('{path='+json.dumps(path)+',enabled=false}' for path in sorted(set(disabled)))
        if entries:args+=['-c','skills.config=['+entries+']']
    if schema_path:args+=['--output-schema',str(Path(schema_path).resolve())]
    if cwd:args+=['-C',str(Path(cwd).resolve())]
    args.append(prompt)
    return args


def run(identifier,stage,prompt,schema=None,metadata=None,native=False,cwd=None,timeout=180):
    if not reserve(identifier,stage):
        p=LOCAL/'runs'/identifier/'result.json'
        return json.loads(p.read_text()) if p.exists() else {'status':'started'}
    folder=LOCAL/'runs'/identifier;folder.mkdir(parents=True)
    (folder/'prompt.txt').write_text(prompt)
    schema_path=None
    if schema is not None:
        schema_path=folder/'schema.json';schema_path.write_text(json.dumps(schema))
    args=command(prompt,schema_path,native,cwd)
    (folder/'invocation.json').write_text(json.dumps({'argv_without_prompt':args[:-1],'requested_model':MODEL,'effort':EFFORT},indent=2)+'\n')
    result={'requested_model':MODEL,'reasoning_effort':EFFORT,'stage':stage,**(metadata or {})}
    started=time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix='ownvoice-v02-cli-') as temporary:
            process=subprocess.run(args,cwd=cwd or temporary,env=legacy.runtime_environment('codex'),text=True,capture_output=True,timeout=timeout)
        (folder/'stdout.jsonl').write_text(legacy.redact(process.stdout));(folder/'stderr.txt').write_text(legacy.redact(process.stderr))
        if process.returncode:raise RuntimeError('CLI exit '+str(process.returncode)+': '+legacy.redact(process.stderr[-800:]))
        events=[];messages=[];reported=[];tools=[];usage=[]
        for line in process.stdout.splitlines():
            try:event=json.loads(line)
            except ValueError:continue
            events.append(event)
            if event.get('type')=='error':raise RuntimeError('CLI error event: '+str(event.get('message',''))[:500])
            item=event.get('item',{})
            if event.get('type')=='item.completed' and item.get('type')=='agent_message':messages.append(item.get('text',''))
            if item.get('type') in {'command_execution','mcp_tool_call','web_search'} and event.get('type')=='item.completed':tools.append(item)
            if event.get('model'):reported.append(event['model'])
            if isinstance(event.get('usage'),dict):usage.append(event['usage'])
        if any(name!=MODEL and not name.startswith(MODEL+'-') for name in reported):raise RuntimeError('Non-Luna response metadata; no fallback')
        if not native and tools:raise RuntimeError('Tools contaminated text-only comparison')
        if not messages:raise RuntimeError('No final agent response')
        artifact=messages[-1].strip();(folder/'artifact.txt').write_text(artifact)
        result.update(status='completed',reported_models=sorted(set(reported)),usage=usage,
                      tool_events=len(tools),observable_completed_turns=sum(e.get('type')=='turn.completed' for e in events),
                      prompt_characters=len(prompt),artifact_characters=len(artifact),artifact_sha256=hashlib.sha256(artifact.encode()).hexdigest())
        try:
            output=json.loads(artifact)
            if not isinstance(output,dict):raise ValueError('Object expected')
            (folder/'output.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n');result['valid_json']=True
        except ValueError:result['valid_json']=False
        if native:(folder/'tool-events.json').write_text(json.dumps(tools,ensure_ascii=False,indent=2)+'\n')
    except Exception as error:
        result.update(status='failed',error_type=type(error).__name__,error='CLI timeout' if isinstance(error,subprocess.TimeoutExpired) else legacy.redact(str(error))[:1000])
    result['seconds']=time.monotonic()-started
    (folder/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    with sqlite3.connect(ROOT/'.local/ledger.sqlite') as db:
        db.execute('UPDATE jobs SET status=?,finished=?,result=? WHERE id=?',(result['status'],time.time(),json.dumps(result),identifier))
        used=db.execute('SELECT COUNT(*) FROM jobs WHERE id LIKE "ownvoice-v02-%"').fetchone()[0]
    print(json.dumps({'job':identifier,'used':used,'cap':CAP,**{k:result.get(k) for k in ('status','valid_json','tool_events','seconds')}},ensure_ascii=False),flush=True)
    return result


def preflight():
    ready=run('ownvoice-v02-preflight-route','preflight','Reply exactly READY; no tools.')
    if ready.get('status')!='completed' or (LOCAL/'runs/ownvoice-v02-preflight-route/artifact.txt').read_text()!='READY':
        raise RuntimeError('Route preflight failed; no fallback')
    schema={'type':'object','properties':{'artifact':{'type':'string'},'unknown':{'type':'null'}},'required':['artifact','unknown'],'additionalProperties':False}
    shaped=run('ownvoice-v02-preflight-schema','preflight','Return artifact READY and unknown null. No tools.',schema)
    value=json.loads((LOCAL/'runs/ownvoice-v02-preflight-schema/output.json').read_text()) if shaped.get('valid_json') else None
    if shaped.get('status')!='completed' or value!={'artifact':'READY','unknown':None}:raise RuntimeError('Schema preflight failed; no fallback')


if __name__=='__main__':preflight()
