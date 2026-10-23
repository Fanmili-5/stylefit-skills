"""Check skill packaging without network or model calls."""
import ast
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from ownvoice.profile import load


def main():
    names = ['ownvoice-profile', 'ownvoice-code', 'ownvoice-research', 'ownvoice-email']
    for name in names:
        folder = ROOT / 'skills' / name
        text = (folder / 'SKILL.md').read_text()
        assert text.startswith('---\nname: ' + name + '\n')
        assert re.search(r'^description: .+', text, re.M)
        assert len(text.splitlines()) < 500
        for relative in re.findall(r'(?<![\w/])(references/[a-zA-Z0-9_./-]+\.md)', text):
            assert (folder / relative).is_file(), relative
        ui = (folder / 'agents/openai.yaml').read_text()
        assert '$' + name in ui
    for path in list((ROOT / 'ownvoice').glob('*.py')) + list((ROOT / 'scripts').glob('*.py')):
        ast.parse(path.read_text(), filename=str(path))
    json.loads((ROOT / 'schemas/profile.schema.json').read_text())
    for path in (ROOT / 'evals/profiles').glob('*.json'):
        load(path)
    print(json.dumps({'skills': len(names), 'static_bundle_checks': 'passed',
                      'host_discovery_verified': False, 'generation_quality_verified': False}))


if __name__ == '__main__':
    main()
