"""Read-only output checks. Structured equality does not verify free-form prose."""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re


class ContractError(ValueError):
    pass


def parse_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError('Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def constant(value):
        raise ValueError('Non-finite JSON number: ' + value)
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def pointer(value, path):
    if not isinstance(path, str) or (path and not path.startswith('/')):
        raise ContractError('Paths must be JSON pointers')
    if not path:
        return value
    for token in path[1:].split('/'):
        token = token.replace('~1', '/').replace('~0', '~')
        value = value[int(token)] if isinstance(value, list) else value[token]
    return value


def equivalent(left, right, tolerance=0):
    if left is None or isinstance(left, bool) or right is None or isinstance(right, bool):
        return type(left) is type(right) and left == right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isfinite(left) and math.isfinite(right) and math.isclose(left, right, rel_tol=tolerance, abs_tol=tolerance)
    if isinstance(left, dict) and isinstance(right, dict):
        return set(left) == set(right) and all(equivalent(left[k], right[k], tolerance) for k in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(equivalent(a, b, tolerance) for a, b in zip(left, right))
    return type(left) is type(right) and left == right


def normalize_date(value, formats):
    if not isinstance(value, str):
        raise ValueError('Date must be a string')
    for layout in formats:
        try:
            parsed = datetime.strptime(value, layout)
            return parsed.astimezone(timezone.utc).isoformat() if parsed.tzinfo else parsed.isoformat()
        except ValueError:
            pass
    raise ValueError('Date does not match an explicitly permitted format')


def validate_schema(schema):
    from jsonschema import Draft202012Validator
    from referencing import Registry
    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if key in {'$ref', '$dynamicRef'} and (not isinstance(value, str) or not value.startswith('#')):
                    raise ContractError('Only document-local schema references are supported')
                if key == 'format':
                    raise ContractError('Use explicit date assertions; format annotations alone are not validation')
                walk(value)
        elif isinstance(node, list):
            for value in node: walk(value)
    walk(schema)
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as error:
        raise ContractError('Invalid JSON Schema: ' + str(error)) from error
    return Draft202012Validator(schema, registry=Registry())


ASSERTION_KEYS = {
    'equal': {'path', 'expected', 'tolerance'},
    'date': {'path', 'expected', 'formats'},
    'contains': {'path', 'value'},
    'not_contains': {'path', 'value'},
    'regex': {'path', 'pattern'},
    'source_ids': {'path', 'allowed'},
    'unit_conversion': {'path', 'source_value', 'factor', 'offset', 'tolerance'},
}


def constraints_contract(constraints):
    if not isinstance(constraints, dict) or constraints.get('schema_version') != 1 or type(constraints.get('schema_version')) is not int:
        raise ContractError('constraints.schema_version must be 1')
    if set(constraints) - {'schema_version', 'assertions', 'semantic_review'}:
        raise ContractError('Unknown constraint fields')
    assertions = constraints.get('assertions', [])
    if not isinstance(assertions, list): raise ContractError('assertions must be a list')
    for item in assertions:
        if not isinstance(item, dict) or item.get('op') not in ASSERTION_KEYS:
            raise ContractError('Unsupported assertion')
        if set(item) - (ASSERTION_KEYS[item['op']] | {'op', 'id'}):
            raise ContractError('Unknown assertion fields')
        if not isinstance(item.get('path'), str): raise ContractError('Assertion path is required')
        if item['path'] and not item['path'].startswith('/'): raise ContractError('Invalid JSON pointer')
        required = {'equal': ['expected'], 'date': ['expected', 'formats'], 'contains': ['value'],
                    'not_contains': ['value'], 'regex': ['pattern'], 'source_ids': ['allowed'],
                    'unit_conversion': ['source_value', 'factor']}[item['op']]
        if any(key not in item for key in required): raise ContractError('Incomplete assertion ' + item['op'])
        if 'tolerance' in item and (isinstance(item['tolerance'], bool) or not isinstance(item['tolerance'], (int, float)) or not math.isfinite(item['tolerance']) or item['tolerance'] < 0):
            raise ContractError('Invalid numerical tolerance')
        if item['op'] == 'regex':
            try: re.compile(item['pattern'])
            except (TypeError, re.error) as error: raise ContractError('Invalid pattern') from error
        if item['op'] == 'date' and (not isinstance(item['formats'], list) or not item['formats'] or any(not isinstance(x, str) for x in item['formats'])):
            raise ContractError('Explicit date formats are required')
        if item['op'] == 'source_ids' and (not isinstance(item['allowed'], list) or any(not isinstance(x, str) for x in item['allowed'])):
            raise ContractError('Source IDs must be strings')
        if item['op'] == 'unit_conversion' and any(isinstance(item.get(k, 0), bool) or not isinstance(item.get(k, 0), (int, float)) or not math.isfinite(item.get(k, 0)) for k in ('source_value','factor','offset')):
            raise ContractError('Conversion quantities must be finite numbers')
    review = constraints.get('semantic_review')
    if review is not None and (not isinstance(review, dict) or set(review) - {'required', 'status', 'evidence', 'source'}):
        raise ContractError('Invalid semantic_review')
    if review:
        if type(review.get('required', False)) is not bool or review.get('status', 'not_run') not in {'passed','failed','not_run'}:
            raise ContractError('Invalid semantic review status')
        if review.get('status', 'not_run') != 'not_run' and (not review.get('evidence') or review.get('source') not in {'human','model'}):
            raise ContractError('Review requires evidence and a human/model source')
    return assertions


def verify(text, schema=None, constraints=None):
    """Never rewrite input or infer the expected facts from the candidate itself."""
    checks, gaps = [], []
    validator = validate_schema(schema) if schema is not None else None
    assertions = constraints_contract(constraints) if constraints is not None else []
    needs_json = schema is not None or bool(assertions)
    if needs_json:
        try:
            value = parse_json(text)
            checks.append({'name': 'json_syntax', 'status': 'passed'})
        except (ValueError, TypeError) as error:
            return finish([{'name':'json_syntax','status':'failed','evidence':str(error)}], gaps, text)
    else:
        value = text
        checks.append({'name': 'artifact_nonempty', 'status': 'passed' if text.strip() else 'failed'})
    if validator is not None:
        try:
            errors = [{'path': '/' + '/'.join(str(x) for x in error.absolute_path), 'message': error.message}
                      for error in sorted(validator.iter_errors(value), key=lambda x: str(list(x.absolute_path)))]
        except Exception as error:
            raise ContractError('Schema could not be resolved locally: '+str(error)) from error
        checks.append({'name':'json_schema','status':'failed' if errors else 'passed','errors':errors})
    for index, item in enumerate(assertions):
        try:
            actual = pointer(value, item['path']); op = item['op']
            if op == 'equal': ok = equivalent(actual, item['expected'], item.get('tolerance', 0))
            elif op == 'date': ok = normalize_date(actual, item['formats']) == normalize_date(item['expected'], item['formats'])
            elif op == 'contains': ok = item['value'] in actual
            elif op == 'not_contains': ok = item['value'] not in actual
            elif op == 'regex': ok = isinstance(actual, str) and re.search(item['pattern'], actual) is not None
            elif op == 'source_ids': ok = isinstance(actual, list) and all(isinstance(x, str) and x in item['allowed'] for x in actual)
            elif op == 'unit_conversion': ok = equivalent(actual, item['source_value'] * item['factor'] + item.get('offset', 0), item.get('tolerance', 1e-9))
            checks.append({'name':item.get('id', 'assertion_'+str(index)), 'status':'passed' if ok else 'failed', 'path':item['path']})
        except (KeyError, IndexError, ValueError, TypeError, OverflowError) as error:
            checks.append({'name':item.get('id','assertion_'+str(index)), 'status':'failed','path':item['path'],'evidence':str(error)})
    review = (constraints or {}).get('semantic_review')
    if review:
        state = review.get('status', 'not_run')
        checks.append({'name':'semantic_review','status':state,'required':review.get('required', False),
                       'evidence':review.get('evidence'),'source':review.get('source')})
        if state == 'not_run': gaps.append('Raw prose has not been independently reviewed against the source packet.')
    else:
        gaps.append('Mechanical checks do not establish free-form semantic fidelity.')
    if not schema and not assertions: gaps.append('No structural or factual contract supplied.')
    return finish(checks, gaps, text)


def finish(checks, gaps, text):
    blocking = [check['name'] for check in checks if check['status'] == 'failed' or
                (check['status'] == 'not_run' and check.get('required', True))]
    return {'schema_version':1,'status':'failed' if blocking else 'passed',
            'ready_for_delivery':not blocking,'checks':checks,'blocking_issues':blocking,
            'verification_gaps':gaps,'artifact_sha256':hashlib.sha256(text.encode()).hexdigest(),
            'scope':'Only declared checks; review attestations are not mechanical proof of prose truth.'}
