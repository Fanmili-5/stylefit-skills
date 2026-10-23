"""Compile two Python files and compare limited static contracts; never run them."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import tokenize


def dump(node):
    return ast.dump(node, include_attributes=False) if node is not None else None


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest() if text is not None else None


def public_api(tree):
    declarations = []

    def walk(nodes, prefix=''):
        for node in nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith('_') and not node.name.startswith('__'):
                    continue
                declarations.append({'name': prefix + node.name,
                                     'kind': type(node).__name__,
                                     'arguments': dump(node.args),
                                     'returns': dump(node.returns),
                                     'decorators': [dump(x) for x in node.decorator_list],
                                     'type_comment': node.type_comment,
                                     'type_parameters': [dump(x) for x in getattr(node, 'type_params', [])],
                                     'docstring_hash': digest(ast.get_docstring(node, clean=False))})
            elif isinstance(node, ast.ClassDef) and not node.name.startswith('_'):
                declarations.append({'name': prefix + node.name, 'kind': 'ClassDef',
                                     'bases': [dump(x) for x in node.bases],
                                     'keywords': [dump(x) for x in node.keywords],
                                     'decorators': [dump(x) for x in node.decorator_list],
                                     'type_parameters': [dump(x) for x in getattr(node, 'type_params', [])],
                                     'docstring_hash': digest(ast.get_docstring(node, clean=False))})
                walk(node.body, prefix + node.name + '.')
            elif isinstance(node, (ast.If, ast.Try, ast.With)):
                for field in ('body', 'orelse', 'finalbody'):
                    walk(getattr(node, field, []), prefix)
                for handler in getattr(node, 'handlers', []):
                    walk(handler.body, prefix)

    walk(tree.body)
    return declarations


def inspect_file(path):
    with tokenize.open(path) as stream:
        source = stream.read()
    compile(source, str(path), 'exec', dont_inherit=True)
    tree = ast.parse(source, filename=str(path), type_comments=True)
    imports = [dump(node) for node in ast.walk(tree)
               if isinstance(node, (ast.Import, ast.ImportFrom))]
    return {'ast': dump(tree), 'api': public_api(tree), 'imports': imports,
            'module_docstring': digest(ast.get_docstring(tree, clean=False))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--before', type=Path, required=True)
    parser.add_argument('--after', type=Path, required=True)
    args = parser.parse_args()
    try:
        before, after = inspect_file(args.before), inspect_file(args.after)
    except (OSError, SyntaxError, ValueError, UnicodeError, LookupError) as error:
        print(json.dumps({'syntax_valid': False, 'error_type': type(error).__name__,
                          'message': str(error), 'behavior_verified': False}))
        return 1
    same_api = before['api'] == after['api']
    same_imports = before['imports'] == after['imports']
    same_module_doc = before['module_docstring'] == after['module_docstring']
    passed = same_api and same_imports and same_module_doc
    print(json.dumps({'syntax_valid': True, 'same_declared_public_api': same_api,
                      'same_imports': same_imports, 'same_module_docstring': same_module_doc,
                      'same_ast': before['ast'] == after['ast'],
                      'static_checks_passed': passed, 'behavior_verified': False,
                      'scope': 'Declared public interfaces, documentation, imports, and syntax only.'}))
    return 0 if passed else 2


if __name__ == '__main__':
    raise SystemExit(main())
