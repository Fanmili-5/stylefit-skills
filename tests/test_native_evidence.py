import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('native_evidence',ROOT/'scripts/native_release_eval.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class NativeEvidenceTests(unittest.TestCase):
    def test_full_read_survives_unrelated_later_shell_failure(self):
        skill='---\nname: ownvoice-research\n---\nComplete instructions and ending.'
        event={'command':'cat .agents/skills/ownvoice-research/SKILL.md && rg absent-folder',
               'aggregated_output':skill+'\nrg: absent-folder: No such file','exit_code':2}
        self.assertTrue(module.observed_skill_read([event],'research',skill))

    def test_path_mention_failed_cat_and_partial_contents_are_not_reads(self):
        skill='Full skill instructions and ending.'
        for output in ('No such file','Full skill instructions'):
            event={'command':'cat .agents/skills/ownvoice-research/SKILL.md','aggregated_output':output,'exit_code':1}
            self.assertFalse(module.observed_skill_read([event],'research',skill))


if __name__=='__main__':unittest.main()
