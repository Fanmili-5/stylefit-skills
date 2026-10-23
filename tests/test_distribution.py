import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class DistributionTests(unittest.TestCase):
    def installer(self):
        spec=importlib.util.spec_from_file_location('installer',ROOT/'scripts/install.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def test_all_skills_copy_and_reinstall_without_changes(self):
        module=self.installer()
        with tempfile.TemporaryDirectory() as folder:
            paths=module.install(folder)
            self.assertEqual(len(paths),4)
            self.assertTrue(all((Path(p)/'SKILL.md').is_file() for p in paths))
            self.assertEqual(paths,module.install(folder))

    def test_collision_does_not_partially_install(self):
        module=self.installer()
        with tempfile.TemporaryDirectory() as folder:
            conflict=Path(folder)/'stylefit-research';conflict.mkdir()
            (conflict/'SKILL.md').write_text('user content')
            with self.assertRaises(ValueError): module.install(folder)
            self.assertEqual([p.name for p in Path(folder).iterdir()],['stylefit-research'])
            self.assertEqual((conflict/'SKILL.md').read_text(),'user content')


if __name__=='__main__': unittest.main()
