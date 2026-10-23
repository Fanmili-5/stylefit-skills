"""Fixture-level checks. Passing them never establishes general equivalence."""
import ast
import json
import re
import subprocess
import sys


BLOCKED = {'eval', 'exec', 'compile', 'open', 'input', 'globals', 'locals', 'vars',
           'getattr', 'setattr', 'delattr', 'hasattr', 'type', 'object', 'help', 'breakpoint'}


def safe_fixture_source(source):
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.ClassDef, ast.AsyncFunctionDef,
                             ast.Global, ast.Nonlocal)):
            raise ValueError('Unsupported construct in isolated fixture')
        if isinstance(node, ast.Name) and (node.id in BLOCKED or node.id.startswith('__')):
            raise ValueError('Unsafe name in isolated fixture')
        if isinstance(node, ast.Attribute) and node.attr.startswith('_'):
            raise ValueError('Introspection is not allowed in isolated fixtures')
        if isinstance(node, ast.FunctionDef) and (node.decorator_list or node.name.startswith('__')):
            raise ValueError('Unsupported function definition')
    if any(not isinstance(n, ast.FunctionDef) for n in tree.body):
        raise ValueError('Fixture output must contain only function definitions')
    compile(source, '<candidate>', 'exec', dont_inherit=True)
    return tree


def check_code(task, source):
    try:
        tree = safe_fixture_source(source)
        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == task['function']]
        if len(functions) != 1:
            raise ValueError('Missing required function')
        args = functions[0].args
        actual = [a.arg for a in args.posonlyargs + args.args]
        if actual != task['parameters'] or args.vararg or args.kwarg or args.kwonlyargs or args.defaults:
            raise ValueError('Required signature changed')
    except (SyntaxError, ValueError) as error:
        return {'passed': False, 'syntax_and_interface': False, 'error': str(error),
                'scope': 'Controlled standard-library Python fixture only'}
    payload = {'source': source, 'function': task['function'], 'tests': task['tests']}
    try:
        process = subprocess.run([sys.executable, '-I', '-S', '-c', WORKER],
                                 input=json.dumps(payload), text=True, capture_output=True, timeout=6)
        result = json.loads(process.stdout)
        result['scope'] = 'Only the supplied fixture inputs; not arbitrary source equivalence'
        return result
    except (subprocess.TimeoutExpired, ValueError) as error:
        return {'passed': False, 'syntax_and_interface': True, 'error': type(error).__name__}


WORKER = '''import copy, json, math, sys
try:
    import resource
    resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
except (ImportError, ValueError):
    pass
payload = json.load(sys.stdin)
safe = {name: getattr(__import__('builtins'), name) for name in (
    'len', 'range', 'enumerate', 'zip', 'sum', 'min', 'max', 'abs', 'round',
    'int', 'float', 'str', 'bool', 'list', 'tuple', 'dict', 'set', 'sorted',
    'reversed', 'all', 'any', 'isinstance', 'ValueError', 'TypeError', 'IndexError', 'KeyError')}
scope = {'__builtins__': safe}
exec(compile(payload['source'], '<candidate>', 'exec'), scope)
def equal(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=1e-10, abs_tol=1e-10)
    if isinstance(a, (list, tuple)) and isinstance(b, list):
        return isinstance(a, list) and len(a) == len(b) and all(equal(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(equal(a[k], b[k]) for k in a)
    return type(a) is type(b) and a == b
results = []
for case in payload['tests']:
    args, kwargs = copy.deepcopy(case.get('args', [])), copy.deepcopy(case.get('kwargs', {}))
    initial = copy.deepcopy((args, kwargs))
    try:
        value = scope[payload['function']](*args, **kwargs)
        ok = 'error' not in case and equal(value, case['expected'])
        if case.get('return_type'):
            ok = ok and type(value).__name__ == case['return_type']
        outcome = {'returned': repr(value)[:500]}
    except Exception as error:
        ok = type(error).__name__ == case.get('error')
        if 'message' in case:
            ok = ok and str(error) == case['message']
        outcome = {'raised': type(error).__name__, 'message': str(error)[:500]}
    ok = ok and (case.get('allow_mutation', False) or equal(list((args, kwargs)), list(initial)))
    results.append({'passed': ok, **outcome})
print(json.dumps({'passed': all(x['passed'] for x in results), 'syntax_and_interface': True,
                  'cases': results, 'cases_count': len(results)}))
'''


def check_text(task, artifact):
    missing = [span for span in task.get('protected', []) if span not in artifact]
    failed_meanings = [alternatives for alternatives in task.get('required_any', [])
                       if not any(word.casefold() in artifact.casefold() for word in alternatives)]
    forbidden = [span for span in task.get('forbidden', []) if span.casefold() in artifact.casefold()]
    number_pattern = r'(?<![A-Za-z0-9])\d+(?:\.\d+)?(?!\d)'
    numbers = set(re.findall(number_pattern, artifact))
    allowed = set(re.findall(number_pattern, task['packet']))
    added_numbers = sorted(numbers - allowed)
    return {'passed': not (missing or failed_meanings or forbidden or added_numbers),
            'missing_protected_spans': missing, 'missing_meaning_markers': failed_meanings,
            'forbidden_spans': forbidden, 'added_numbers': added_numbers,
            'semantic_fidelity_verified': False,
            'scope': 'Protected spans and selected markers only; semantic review is still required'}


def check(task, artifact):
    return check_code(task, artifact) if task['domain'] == 'code' else check_text(task, artifact)
