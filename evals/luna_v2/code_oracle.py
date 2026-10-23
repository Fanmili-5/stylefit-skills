"""Bounded synthetic multi-module comparison, not a general execution sandbox."""
import ast
import json
import subprocess
import sys

BLOCKED = {'eval','exec','compile','open','input','globals','locals','vars','getattr',
           'setattr','delattr','hasattr','help','breakpoint','__import__'}


def validate_files(files, allowed):
    if not isinstance(files, dict) or set(files) != set(allowed):
        raise ValueError('Return exactly the two requested source files')
    modules = {name[:-3] for name in allowed}
    for filename, source in files.items():
        if not isinstance(source, str): raise ValueError('Source must be text')
        tree = ast.parse(source, filename=filename)
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.AsyncFunctionDef, ast.Global, ast.Nonlocal, ast.With, ast.AsyncWith)):
                raise ValueError('Unsupported controlled-fixture construct')
            if isinstance(node, ast.Name) and (node.id in BLOCKED or node.id.startswith('__')):
                raise ValueError('Unsafe controlled-fixture name')
            if isinstance(node, ast.Attribute) and node.attr.startswith('_'):
                raise ValueError('Introspection is not allowed')
            if isinstance(node, ast.Import) and any(alias.name not in modules | {'math'} for alias in node.names):
                raise ValueError('Unsupported import')
            if isinstance(node, ast.ImportFrom) and (node.level or node.module not in modules | {'math'} or any(alias.name=='*' for alias in node.names)):
                raise ValueError('Unsupported import')
            if isinstance(node, ast.ImportFrom) and any(alias.name.startswith('_') for alias in node.names):
                raise ValueError('Private imported members are not allowed')
            if isinstance(node, ast.FunctionDef) and (node.decorator_list or node.name.startswith('__')):
                raise ValueError('Unsupported function')
        for node in tree.body:
            if not isinstance(node, (ast.FunctionDef, ast.Import, ast.ImportFrom, ast.Assign)):
                raise ValueError('Module-level executable code is not allowed')
            if isinstance(node, ast.Assign) and any(isinstance(part, (ast.Call, ast.ListComp, ast.DictComp, ast.GeneratorExp)) for part in ast.walk(node.value)):
                raise ValueError('Only literal constants and aliases are allowed at module level')
        compile(source, filename, 'exec', dont_inherit=True)


def compare(task, files, group=None):
    try:
        validate_files(files, task['files'])
    except (ValueError, SyntaxError) as error:
        return {'passed':False, 'syntax_and_files':False, 'error':str(error)}
    tests = [case for case in task['tests'] if group is None or case['group']==group]
    payload = {'reference':task['files'], 'candidate':files, 'public':task['public'], 'tests':tests}
    try:
        result = subprocess.run([sys.executable,'-I','-S','-c',WORKER],input=json.dumps(payload),
                                capture_output=True,text=True,timeout=8)
        parsed = json.loads(result.stdout)
        parsed['scope'] = 'Restricted synthetic modules and finite fixtures; not arbitrary-code safety or equivalence proof.'
        return parsed
    except (ValueError, subprocess.TimeoutExpired) as error:
        return {'passed':False,'syntax_and_files':True,'error':type(error).__name__}


WORKER = r'''import builtins,copy,inspect,json,math,sys,types
try:
 import resource
 resource.setrlimit(resource.RLIMIT_CPU,(3,3))
except (ImportError,ValueError): pass
payload=json.load(sys.stdin)
def decode(value):
 if isinstance(value,dict) and set(value)=={'$float'}:return float(value['$float'])
 if isinstance(value,list):return [decode(item) for item in value]
 if isinstance(value,dict):return {key:decode(item) for key,item in value.items()}
 return value
payload['tests']=decode(payload['tests'])
def load_bundle(files):
 cache={}
 def load(name):
  if name=='math':return math
  if name in cache:return cache[name]
  if name+'.py' not in files:raise ImportError(name)
  module=types.ModuleType(name);cache[name]=module
  def limited_import(name,globals=None,locals=None,fromlist=(),level=0):
   if level:raise ImportError('relative import')
   return load(name)
  names=('len','range','enumerate','zip','sum','min','max','abs','round','int','float','str','bool',
         'list','tuple','dict','set','sorted','reversed','all','any','isinstance','iter','next',
         'ValueError','TypeError','KeyError','IndexError','StopIteration')
  safe={key:getattr(builtins,key) for key in names};safe['__import__']=limited_import
  module.__dict__['__builtins__']=safe
  exec(compile(files[name+'.py'],name+'.py','exec'),module.__dict__)
  return module
 return load
def equal(left,right):
 if type(left) is not type(right):return False
 if isinstance(left,float):
  if math.isnan(left):return math.isnan(right)
  if left==0 and right==0:return math.copysign(1,left)==math.copysign(1,right)
  return left==right or math.isclose(left,right,rel_tol=1e-12,abs_tol=1e-12)
 if isinstance(left,(list,tuple)):return len(left)==len(right) and all(equal(a,b) for a,b in zip(left,right))
 if isinstance(left,dict):return list(left)==list(right) and all(equal(left[k],right[k]) for k in left)
 return left==right
def signature(function):
 return [(p.name,p.kind.name,repr(p.default)) for p in inspect.signature(function).parameters.values()]
def invoke(loader,case):
 args=copy.deepcopy(case.get('args',[]));kwargs=copy.deepcopy(case.get('kwargs',{}));initial=copy.deepcopy((args,kwargs))
 try:
  value=getattr(loader(case['module']),case['function'])(*args,**kwargs)
  outcome={'kind':'return','value':value}
 except Exception as error:outcome={'kind':'error','type':type(error).__name__,'message':str(error)}
 return outcome,equal(initial,(args,kwargs))
try:
 ref=load_bundle(payload['reference']);candidate=load_bundle(payload['candidate'])
 api=[]
 for public in payload['public']:
  try:
   ok=signature(getattr(ref(public['module']),public['function']))==signature(getattr(candidate(public['module']),public['function']))
  except Exception:ok=False
  api.append({'public':public,'passed':ok})
 results=[]
 for case in payload['tests']:
  expected,ref_clean=invoke(ref,case);actual,clean=invoke(candidate,case)
  results.append({'id':case['id'],'passed':equal(expected,actual) and ref_clean and clean,'reference':repr(expected)[:350],'candidate':repr(actual)[:350],'input_unmutated':clean})
 print(json.dumps({'passed':all(row['passed'] for row in api+results),'syntax_and_files':True,'interfaces':api,'cases':results,'cases_count':len(results)}))
except Exception as error:print(json.dumps({'passed':False,'syntax_and_files':True,'load_error':type(error).__name__+': '+str(error)}))
'''
