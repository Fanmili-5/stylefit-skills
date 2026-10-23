import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ownvoice import installation as installer


class NamingMigrationTests(unittest.TestCase):
    def fixture(self, root):
        source = root/'bundle'
        destination = root/'user/.agents/skills'
        destination.mkdir(parents=True)
        base = destination.parent/'.ownvoice'
        old = base/'releases/0.2.0-legacy'
        for name in installer.LEGACY_NAMES:
            folder = old/'skills'/name
            folder.mkdir(parents=True)
            (folder/'SKILL.md').write_text('old '+name)
            (destination/name).symlink_to(installer.alias_target(destination, name))
        installer.atomic_json(old/'install-manifest.json', {
            'owner':'ownvoice-installer/1', 'version':'0.2.0',
            'skills':installer.hashes(old/'skills'), 'wheel_sha256':None,
            'lock_sha256':None, 'with_tools':False})
        installer.switch(base, old.name)
        installer.atomic_json(base/'state.json', {
            'owner':'ownvoice-installer/1', 'current':old.name,
            'previous':None, 'installed':True})
        for name in installer.NAMES:
            folder = source/'skills'/name
            folder.mkdir(parents=True)
            (folder/'SKILL.md').write_text('new '+name)
        return source, destination, base, old.name

    def assert_names(self, destination, names):
        self.assertEqual({p.name for p in destination.iterdir()}, set(names))
        self.assertTrue(all((destination/name/'SKILL.md').is_file() for name in names))

    def test_upgrade_reinstall_rollback_and_forward_restore_matching_names(self):
        with tempfile.TemporaryDirectory() as temp:
            source, destination, base, old = self.fixture(Path(temp))
            plan = installer.managed_install(source, destination, '0.2.1', upgrade=True, dry_run=True)
            self.assertEqual(plan['previous'], old)
            self.assert_names(destination, installer.LEGACY_NAMES)
            new = installer.managed_install(source, destination, '0.2.1', upgrade=True)['release']
            self.assert_names(destination, installer.NAMES)
            installer.managed_install(source, destination, '0.2.1')
            self.assertEqual(json.loads((base/'state.json').read_text())['previous'], old)
            self.assertEqual(installer.rollback(destination)['current'], old)
            self.assert_names(destination, installer.LEGACY_NAMES)
            self.assertEqual(installer.rollback(destination)['current'], new)
            self.assert_names(destination, installer.NAMES)
            installer.uninstall(destination)
            self.assertEqual(list(destination.iterdir()), [])
            self.assertTrue((base/'releases'/old/'skills').is_dir())

    def test_new_name_collision_preserves_legacy_install_and_user_content(self):
        with tempfile.TemporaryDirectory() as temp:
            source, destination, base, old = self.fixture(Path(temp))
            user = destination/'stylefit-email'
            user.mkdir(); (user/'SKILL.md').write_text('user content')
            with self.assertRaises(ValueError):
                installer.managed_install(source, destination, '0.2.1', upgrade=True)
            self.assertEqual(installer.current_release(base), old)
            self.assertEqual((user/'SKILL.md').read_text(), 'user content')
            self.assertTrue(all((destination/name/'SKILL.md').is_file() for name in installer.LEGACY_NAMES))

    def test_failed_state_write_restores_version_and_aliases_in_both_directions(self):
        with tempfile.TemporaryDirectory() as temp:
            source, destination, base, old = self.fixture(Path(temp))
            original_state = (base/'state.json').read_bytes()
            real_write = installer.atomic_json
            def fail_state(path, value):
                if path.name == 'state.json':
                    raise OSError('simulated state write failure')
                return real_write(path, value)
            with patch.object(installer, 'atomic_json', side_effect=fail_state):
                with self.assertRaises(OSError):
                    installer.managed_install(source, destination, '0.2.1', upgrade=True)
            self.assertEqual(installer.current_release(base), old)
            self.assert_names(destination, installer.LEGACY_NAMES)
            self.assertEqual((base/'state.json').read_bytes(), original_state)
            new = installer.managed_install(source, destination, '0.2.1', upgrade=True)['release']
            new_state = (base/'state.json').read_bytes()
            with patch.object(installer, 'atomic_json', side_effect=fail_state):
                with self.assertRaises(OSError):
                    installer.rollback(destination)
            self.assertEqual(installer.current_release(base), new)
            self.assert_names(destination, installer.NAMES)
            self.assertEqual((base/'state.json').read_bytes(), new_state)

    def test_edited_legacy_skill_is_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            source, destination, base, old = self.fixture(Path(temp))
            edited = destination/installer.LEGACY_NAMES[0]/'SKILL.md'
            edited.write_text('user edit')
            with self.assertRaises(ValueError):
                installer.managed_install(source, destination, '0.2.1', upgrade=True)
            self.assertEqual(edited.read_text(), 'user edit')
            self.assertEqual(installer.current_release(base), old)


if __name__ == '__main__':
    unittest.main()
