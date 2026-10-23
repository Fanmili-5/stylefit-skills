from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ownvoice.installation import NAMES, current_release, managed_install, rollback, uninstall


class ManagedInstallationTests(unittest.TestCase):
    def fixture(self,root):
        source=root/'bundle'
        for name in NAMES:
            folder=source/'skills'/name;folder.mkdir(parents=True)
            (folder/'SKILL.md').write_text(name+' original')
        return source,root/'project/.agents/skills'

    def test_dry_run_install_upgrade_rollback_uninstall(self):
        with tempfile.TemporaryDirectory() as temp:
            source,dest=self.fixture(Path(temp))
            managed_install(source,dest,'1',dry_run=True)
            self.assertFalse(dest.exists())
            first=managed_install(source,dest,'1')
            self.assertTrue(all((dest/name/'SKILL.md').is_file() for name in NAMES))
            self.assertEqual(managed_install(source,dest,'1')['release'],first['release'])
            (source/'skills'/NAMES[0]/'SKILL.md').write_text('new version')
            with self.assertRaises(ValueError):managed_install(source,dest,'2')
            second=managed_install(source,dest,'2',upgrade=True)
            self.assertEqual((dest/NAMES[0]/'SKILL.md').read_text(),'new version')
            self.assertEqual(rollback(dest)['current'],first['release'])
            self.assertTrue((dest/NAMES[0]/'SKILL.md').read_text().endswith('original'))
            self.assertTrue(uninstall(dest)['cached_releases_preserved'])
            self.assertFalse(any((dest/name).is_symlink() for name in NAMES))

    def test_unmanaged_collision_and_local_edits_preserved(self):
        with tempfile.TemporaryDirectory() as temp:
            source,dest=self.fixture(Path(temp));(dest/NAMES[0]).mkdir(parents=True)
            (dest/NAMES[0]/'SKILL.md').write_text('user data')
            with self.assertRaises(ValueError):managed_install(source,dest,'1')
            self.assertEqual((dest/NAMES[0]/'SKILL.md').read_text(),'user data')
            self.assertEqual(len(list(dest.iterdir())),1)
        with tempfile.TemporaryDirectory() as temp:
            source,dest=self.fixture(Path(temp));managed_install(source,dest,'1')
            (dest/NAMES[0]/'SKILL.md').write_text('user edit')
            with self.assertRaises(ValueError):managed_install(source,dest,'2',upgrade=True)
            with self.assertRaises(ValueError):uninstall(dest)
            self.assertEqual((dest/NAMES[0]/'SKILL.md').read_text(),'user edit')

    def test_runtime_failure_does_not_activate_partial_version(self):
        with tempfile.TemporaryDirectory() as temp:
            source,dest=self.fixture(Path(temp));first=managed_install(source,dest,'1')
            wheel=source/'dummy.whl';wheel.write_bytes(b'test');(source/'requirements-runtime.lock').write_text('test')
            def fail(*args):raise RuntimeError('intentional runtime setup failure')
            with self.assertRaises(RuntimeError):managed_install(source,dest,'2',wheel,True,True,runtime_factory=fail)
            self.assertEqual(current_release(dest.parent/'.ownvoice'),first['release'])
            self.assertTrue((dest/NAMES[0]/'SKILL.md').is_file())


if __name__=='__main__':unittest.main()
