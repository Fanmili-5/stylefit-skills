import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('general_report_test', ROOT / 'scripts/report_general.py')
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class GeneralReportTests(unittest.TestCase):
    def test_unfavorable_style_and_content_results_remain_in_comparisons(self):
        with tempfile.TemporaryDirectory() as folder:
            previous = report.ROOT
            report.ROOT = Path(folder)
            try:
                rows = []
                for identifier, condition, profile, content, style in (
                    ('plain', 'plain', 'compact', True, True),
                    ('own-compact', 'ownvoice', 'compact', True, False),
                    ('own-expanded', 'ownvoice', 'expanded', False, True),
                ):
                    artifact = Path(folder) / '.local/runs' / identifier / 'artifact.txt'
                    artifact.parent.mkdir(parents=True)
                    artifact.write_text(identifier)
                    rows.append({'job_id': identifier, 'case_id': 'case', 'stage': 'development',
                                 'status': 'completed', 'condition': condition, 'profile': profile,
                                 'domain': 'code', 'language': 'en',
                                 'checks': {'passed': content, 'content': {'passed': content},
                                            'style': {'passed': style, 'probes': {}}}})
                result = report.build_report(3, rows)
                self.assertEqual(len(result['failed_checks']), 2)
                self.assertFalse(result['profile_contrasts'][0]['both_content_passed'])
                self.assertFalse(result['profile_contrasts'][0]['both_style_probes_passed'])
                self.assertFalse(result['method_comparisons'][0]['ownvoice_style_passed'])
                self.assertTrue(result['method_comparisons'][0]['plain_style_passed'])
            finally:
                report.ROOT = previous

    def test_inflight_and_failed_launches_are_not_completed_results(self):
        with tempfile.TemporaryDirectory() as folder:
            previous = report.ROOT
            report.ROOT = Path(folder)
            try:
                rows = [{'job_id': 'pending', 'stage': 'development', 'status': 'started'},
                        {'job_id': 'failed', 'stage': 'development', 'status': 'failed',
                         'condition': 'ownvoice', 'profile': 'compact', 'domain': 'code', 'language': 'zh'}]
                result = report.build_report(2, rows)
                self.assertEqual(len(result['pending_reservations']), 1)
                self.assertEqual(result['groups'][0]['cli_failed'], 1)
                self.assertEqual(result['groups'][0]['completed'], 0)
                self.assertEqual(result['manual_review']['reviewed'], 0)
            finally:
                report.ROOT = previous


if __name__ == '__main__':
    unittest.main()
