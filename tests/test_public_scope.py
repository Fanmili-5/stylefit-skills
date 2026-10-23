import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from ownvoice.profile import load, select

ROOT = Path(__file__).resolve().parents[1]


class PublicScopeTests(unittest.TestCase):
    def test_empty_template_invents_no_preferences(self):
        profile = load(ROOT / 'examples/profile.empty.json')
        self.assertEqual(profile['basis'], 'generic')
        for domain in ('code', 'research', 'email'):
            for language in ('zh', 'en'):
                self.assertEqual(select(profile, domain, language)['preferences'], [])

    def test_switching_profiles_preserves_both_users_and_unknown_domains(self):
        first = {'schema_version': 1, 'basis': 'preferences',
                 'preferences': {'code': {'en': ['Use descriptive local names.']}}}
        second = {'schema_version': 1, 'basis': 'preferences',
                  'preferences': {'code': {'en': ['Use conventional short local names.']}}}
        original = json.dumps([first, second], sort_keys=True)
        for profile in (first, second, first):
            self.assertEqual(select(profile, 'code', 'en')['preferences'], profile['preferences']['code']['en'])
            self.assertEqual(select(profile, 'email', 'en')['preferences'], [])
        self.assertEqual(json.dumps([first, second], sort_keys=True), original)

    def test_installer_does_not_distribute_project_owners_private_profile(self):
        spec = importlib.util.spec_from_file_location('public_installer', ROOT / 'scripts/install.py')
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as folder:
            bundle = Path(folder) / 'bundle'
            skill = bundle / 'skills/example-skill'
            skill.mkdir(parents=True)
            (skill / 'SKILL.md').write_text('public instructions')
            private = bundle / '.local'
            private.mkdir()
            (private / 'profile.json').write_text('{"private_marker": "owner-only"}')
            installer.ROOT = bundle
            destination = Path(folder) / 'installed'
            installer.install(destination)
            installed = {str(path.relative_to(destination)): path.read_text()
                         for path in destination.rglob('*') if path.is_file()}
            self.assertEqual(installed, {'example-skill/SKILL.md': 'public instructions'})


if __name__ == '__main__':
    unittest.main()
