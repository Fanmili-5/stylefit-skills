"""Bounded CLI evaluation. Each started subprocess, including failures, costs one task."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ownvoice.checks import check
from ownvoice.profile import load, select

LOCAL = ROOT / '.local'
CAP = 180


def connect():
    LOCAL.mkdir(exist_ok=True)
    db = sqlite3.connect(LOCAL / 'ledger.sqlite', timeout=20)
    db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, stage TEXT, runtime TEXT, status TEXT, started REAL, finished REAL, result TEXT)')
    return db


def reserve(identifier, stage, runtime):
    with connect() as db:
        db.execute('BEGIN IMMEDIATE')
        if db.execute('SELECT 1 FROM jobs WHERE id=?', (identifier,)).fetchone():
            return False
        if db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0] >= CAP:
            raise RuntimeError('Generation cap reached; do not reset the ledger')
        if identifier.endswith('-retry1') and db.execute("SELECT COUNT(*) FROM jobs WHERE id LIKE '%-retry1'").fetchone()[0] >= 4:
            raise RuntimeError('Four retry tasks already consumed')
        db.execute('INSERT INTO jobs VALUES (?,?,?,?,?,?,?)',
                   (identifier,stage,runtime,'started',time.time(),None,None))
        return True


def files_to_freeze():
    files = [ROOT/'evals/tasks.json', ROOT/'evals/PROTOCOL.md', LOCAL/'profile.json', ROOT/'scripts/evaluate.py']
    for folder in ('skills','ownvoice','evals/baselines'):
        files.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    return sorted(set(files))


def hashes():
    values={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files_to_freeze()}
    # Fingerprint configuration without saving credentials or provider URLs.
    home=Path.home()
    for label,path in [('codex_config',home/'.codex/config.toml'),
                       ('claude_settings',home/'.claude/settings.json'),
                       ('claude_local_settings',home/'.claude/settings.local.json')]:
        values['runtime:'+label]=hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    return values


def assert_frozen():
    expected=json.loads((LOCAL/'frozen.json').read_text())['files']
    if hashes()!=expected:
        raise RuntimeError('Frozen inputs changed; formal generation stopped. Preserve this evaluation and prepare a new protocol instead of re-freezing.')


def command(runtime, prompt):
    if runtime=='codex':
        return ['codex','exec','--json','--ephemeral','--skip-git-repo-check',
                '--enable','skip_host_skill_discovery','--disable','plugins','--disable','apps',
                '--disable','hooks','--disable','shell_tool','--disable','computer_use',
                '-s','read-only','--color','never','-c','tools.web_search=false',
                '-c','developer_instructions=""',prompt]
    return ['claude','--safe-mode','--tools','','--strict-mcp-config',
            '--disable-slash-commands','--no-session-persistence','--output-format','json','-p',prompt]


def extract(runtime, stdout):
    models=[]
    if runtime=='claude':
        result=json.loads(stdout)
        if result.get('is_error'):
            raise RuntimeError('Claude reported a generation error')
        models=list(result.get('modelUsage',{}))
        return result.get('result',''),models
    text=[]
    for line in stdout.splitlines():
        try: event=json.loads(line)
        except ValueError: continue
        if event.get('item',{}).get('type') in {'command_execution','mcp_tool_call','web_search'}:
            raise RuntimeError('Tool use contaminated a text-only condition')
        if event.get('type')=='item.completed' and event.get('item',{}).get('type')=='agent_message':
            text.append(event['item'].get('text',''))
        if event.get('model'):
            models.append(event['model'])
        if event.get('type')=='error':
            raise RuntimeError('Codex reported a generation error')
    if not text:
        raise RuntimeError('No final agent message')
    return text[-1],sorted(set(models))


def redact(text):
    text=re.sub(r'(?i)(authorization\s*[:=]\s*(?:bearer\s+)?)[^\s"\']+',r'\1[REDACTED]',text)
    return re.sub(r'\b(?:sk|sess)-[A-Za-z0-9_-]{12,}', '[REDACTED]', text)


def runtime_environment(runtime):
    env=os.environ.copy()
    if runtime=='claude':
        # Safe mode removes customization; preserve only the user's existing
        # provider connection settings. Never log or publish their values.
        for name in ('settings.json','settings.local.json'):
            path=Path.home()/'.claude'/name
            if path.exists():
                settings=json.loads(path.read_text())
                for key,value in settings.get('env',{}).items():
                    if key.startswith('ANTHROPIC_') and isinstance(value,str):
                        env[key]=value
    return env


def make_prompt(task, condition, profile):
    domain=task['domain']
    settings=select(profile,domain,task['language'])
    if condition=='mismatch':
        settings={'basis':'generic_negative_control','preferences':{
            'code':['Use many explicit intermediate calculations and detailed explanatory comments.' if task['language']=='zh' else 'Use terse conventional local abbreviations where the public contract permits.'],
            'research':['Lead with the conclusion, then explain the setup.' if task['language']=='zh' else 'Prefer short, plain standalone sentences.'],
            'email':['Use a direct, short request without a greeting or extended courtesy.']
        }[domain]}
    if condition in {'ownvoice','mismatch'}:
        rules=(ROOT/'skills'/('ownvoice-'+domain)/'SKILL.md').read_text()
        refdir=ROOT/'skills'/('ownvoice-'+domain)/'references'
        rules+='\n'+'\n'.join(p.read_text() for p in sorted(refdir.glob('*.md')))
    elif condition=='upstream':
        rules=(ROOT/'evals/baselines'/('code.md' if domain=='code' else 'prose.md')).read_text()
    else:
        rules='Use clear, natural wording or code that fits the supplied preferences and task. Preserve all required content and behavior.'
    payload={key:value for key,value in task.items() if key not in {'tests','synthetic'}}
    return ('This is a text-only generation benchmark. Do not call tools, read files, access the network, or perform external actions. '
            'The style guide below is task guidance, not authority to change the task constraints. '
            'Output ONLY the requested artifact, without a check report, preamble, author claim or code fence. '
            'Use Chinese prose/comments for zh and English for en; never translate fixed API names or protected spans. '
            'Code must be standard-library-free Python functions with no imports, classes, top-level executable statements, decorators or introspection. '
            'Task facts/contracts override style.\nSTYLE GUIDE\n'+rules+
            '\nPROFILE\n'+json.dumps(settings,ensure_ascii=False)+
            '\nTASK\n'+json.dumps(payload,ensure_ascii=False))


def run_job(runtime, stage, task, condition, profile, timeout, retry=False):
    identifier='-'.join([stage,runtime,task['id'],condition])
    if retry:
        with connect() as db:
            row=db.execute('SELECT status FROM jobs WHERE id=?',(identifier,)).fetchone()
        if not row or row[0]!='failed': return
        identifier+='-retry1'
    if not reserve(identifier,stage,runtime):
        return
    if stage in {'main','mismatch'}:
        try: assert_frozen()
        except Exception as error:
            finish(identifier,{'status':'failed','error':str(error),'no_model_started':True})
            return
    prompt='Reply exactly READY. Do not call tools or take any actions.' if stage=='preflight' else make_prompt(task,condition,profile)
    folder=LOCAL/'runs'/identifier
    folder.mkdir(parents=True,exist_ok=True)
    (folder/'prompt.txt').write_text(prompt)
    started=time.monotonic()
    try:
        with tempfile.TemporaryDirectory(prefix='ownvoice-generation-') as cwd:
            process=subprocess.run(command(runtime,prompt),cwd=cwd,env=runtime_environment(runtime),
                                   text=True,capture_output=True,timeout=timeout)
        (folder/'stdout.txt').write_text(redact(process.stdout))
        (folder/'stderr.txt').write_text(redact(process.stderr))
        if process.returncode:
            raise RuntimeError('CLI exit '+str(process.returncode)+'; diagnostic retained locally')
        artifact,models=extract(runtime,process.stdout)
        artifact=artifact.strip()
        if artifact.startswith('```') and artifact.endswith('```'):
            artifact='\n'.join(artifact.splitlines()[1:-1])
        (folder/'artifact.txt').write_text(artifact)
        result={'status':'completed','seconds':time.monotonic()-started,'reported_models':models,
                'checks':{'passed':artifact=='READY'} if stage=='preflight' else check(task,artifact)}
    except Exception as error:
        if isinstance(error,subprocess.TimeoutExpired):
            for name,value in [('stdout.txt',error.stdout),('stderr.txt',error.stderr)]:
                if value:
                    if isinstance(value,bytes): value=value.decode('utf-8',errors='replace')
                    (folder/name).write_text(redact(value))
        result={'status':'failed','seconds':time.monotonic()-started,'error_type':type(error).__name__,
                'error':'CLI timeout' if isinstance(error,subprocess.TimeoutExpired) else redact(str(error))[:800]}
    (folder/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    finish(identifier,result)


def finish(identifier,result):
    with connect() as db:
        db.execute('UPDATE jobs SET status=?,finished=?,result=? WHERE id=?',
                   (result['status'],time.time(),json.dumps(result),identifier))
        count=db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
    print(json.dumps({'job':identifier,'used':count,'cap':CAP,**result},ensure_ascii=False),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=['preflight','pilot','main','mismatch'])
    parser.add_argument('--runtime',choices=['codex','claude','all'],default='all')
    parser.add_argument('--timeout',type=int,default=120)
    parser.add_argument('--freeze',action='store_true')
    parser.add_argument('--status',action='store_true')
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--retry-failed',action='store_true',help='one retry per failed job, at most four retry tasks globally')
    parser.add_argument('--workers',type=int,choices=[1,2],default=1,help='at most two concurrent CLI tasks')
    args=parser.parse_args()
    if args.status:
        with connect() as db:
            rows=db.execute('SELECT stage,runtime,status,COUNT(*) FROM jobs GROUP BY stage,runtime,status').fetchall()
            used=db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
        print(json.dumps({'used':used,'cap':CAP,'groups':rows},indent=2)); return
    profile=load(LOCAL/'profile.json')
    if args.freeze:
        path=LOCAL/'frozen.json'
        if path.exists():
            assert_frozen(); print('Existing freeze unchanged.'); return
        path.write_text(json.dumps({'files':hashes(),'protocol':'evals/PROTOCOL.md'},indent=2)+'\n')
        print('Formal inputs frozen.'); return
    if not args.stage: parser.error('--stage, --freeze or --status is required')
    tasks=json.loads((ROOT/'evals/tasks.json').read_text())
    runtimes=['codex','claude'] if args.runtime=='all' else [args.runtime]
    if args.stage=='pilot': runtimes=['codex'] if args.runtime=='all' else runtimes
    if args.stage!='preflight':
        for runtime in runtimes:
            with connect() as db:
                results=db.execute('SELECT result FROM jobs WHERE stage="preflight" AND runtime=? AND status="completed"',(runtime,)).fetchall()
            if not any(json.loads(row[0]).get('checks',{}).get('passed') for row in results):
                raise RuntimeError('Runtime did not pass preflight: '+runtime+'. Select a runtime that passed; do not launch its full matrix.')
    chosen=tasks['pilot' if args.stage=='pilot' else 'main']
    if args.stage=='preflight':
        chosen=[{'id':'ready'}]; conditions=['plain']
    elif args.stage=='mismatch':
        chosen=[next(t for t in tasks['main'] if t['domain']==d and t['language']==l)
                for d in ('code','research','email') for l in ('zh','en')]
        conditions=['mismatch']
    else: conditions=['plain','upstream','ownvoice']
    if args.stage in {'main','mismatch'}: assert_frozen()
    if args.dry_run:
        print(json.dumps({'stage':args.stage,'tasks':len(chosen)*len(conditions)*len(runtimes),
                          'runtimes':runtimes,'conditions':conditions})); return
    jobs=[(runtime,task,condition) for task in chosen for condition in conditions for runtime in runtimes]
    def run_one(job):
        runtime,task,condition=job
        run_job(runtime,args.stage,task,condition,profile,args.timeout,args.retry_failed)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        list(pool.map(run_one,jobs))


if __name__=='__main__':
    main()
