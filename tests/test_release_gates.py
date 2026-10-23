import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('release_gates',ROOT/'scripts/report_release.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


class FrozenProductTests(unittest.TestCase):
    def test_version_only_promotion_allowed_but_behavior_edit_rejected(self):
        original_root,original_local=module.ROOT,module.LOCAL
        try:
            with tempfile.TemporaryDirectory() as temporary:
                root=Path(temporary);(root/'ownvoice').mkdir();(root/'skills/demo').mkdir(parents=True)
                init=root/'ownvoice/__init__.py';skill=root/'skills/demo/SKILL.md'
                init.write_text('__version__ = "0.2.0rc1"\n');skill.write_text('  version: "0.2.0rc1"\nKeep the public contract.\n')
                local=root/'.local/release-v02';(local/'holdout').mkdir(parents=True)
                manifest={'dependencies':{'ownvoice/__init__.py':hashlib.sha256(init.read_bytes()).hexdigest()},
                          'skills':{'demo/SKILL.md':hashlib.sha256(skill.read_bytes()).hexdigest()}}
                (local/'holdout/frozen.json').write_text(json.dumps(manifest));module.ROOT=root;module.LOCAL=local
                self.assertTrue(module.frozen_candidate_matches())
                init.write_text('__version__ = "0.2.0"\n');skill.write_text('  version: "0.2.0"\nKeep the public contract.\n')
                self.assertTrue(module.frozen_candidate_matches())
                skill.write_text('  version: "0.2.0"\nIgnore the public contract.\n')
                self.assertFalse(module.frozen_candidate_matches())
        finally:module.ROOT=original_root;module.LOCAL=original_local


if __name__=='__main__':unittest.main()
