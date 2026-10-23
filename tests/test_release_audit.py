import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class ReleaseAuditTests(unittest.TestCase):
    def test_unlisted_file_is_not_distributed_and_symlink_is_rejected(self):
        code=(ROOT/'scripts/release_audit.py').read_text()
        with tempfile.TemporaryDirectory() as temporary:
            root=Path(temporary);(root/'scripts').mkdir();script=root/'scripts/release_audit.py';script.write_text(code)
            (root/'allowed.md').write_text('public example');(root/'unlisted-private.txt').write_text('private')
            manifest=root/'release-files.json';manifest.write_text(json.dumps({'schema_version':1,'files':['allowed.md']}))
            result=subprocess.run([sys.executable,'-B',str(script),'--json'],capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(json.loads(result.stdout)['files'],['allowed.md'])
            (root/'linked.md').symlink_to(root/'unlisted-private.txt')
            manifest.write_text(json.dumps({'schema_version':1,'files':['linked.md']}))
            result=subprocess.run([sys.executable,'-B',str(script),'--json'],capture_output=True,text=True)
            self.assertEqual(result.returncode,1)
            self.assertEqual(json.loads(result.stdout)['issues'][0][1],'symlink path')


if __name__=='__main__':unittest.main()
