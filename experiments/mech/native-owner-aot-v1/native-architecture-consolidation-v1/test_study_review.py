"""Regressions for unqualified statistics and preserved build evidence."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from analyze import analyze_sessions, analyze
from build_subject import allocate
from campaign import observation, CONTROLLER
from qualify import qualify
from study import process


class StudyReviewTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((Path(__file__).parent / 'plan.json').read_text())
        self.reports = [dict(session=session, samples=[
            dict(order=order, position=position, subject=subject,
                 seconds=1.0 if subject == 'F' else 2.0, verified=True)
            for order, subjects in enumerate(self.plan[f'session_{session}'])
            for position, subject in enumerate(subjects)]) for session in [1, 2]]

    def test_fabricated_labels_and_timings_never_qualify_performance(self):
        result = analyze_sessions(self.reports, self.plan)
        self.assertTrue(result['statistically_accepted'])
        self.assertFalse(result['performance_qualified'])
        self.assertTrue(all('qualified' not in session for session in result['sessions']))

    def test_duplicate_positions_are_rejected(self):
        report = copy.deepcopy(self.reports[0])
        report['samples'][1]['position'] = 0
        with self.assertRaises(AssertionError):
            analyze(report, self.plan)

    def test_nonfinite_timings_are_rejected(self):
        for value in [float('nan'), float('inf')]:
            report = copy.deepcopy(self.reports[0])
            report['samples'][0]['seconds'] = value
            with self.assertRaises(AssertionError):
                analyze(report, self.plan)

    def test_evidence_qualifier_rejects_unfrozen_campaign(self):
        with self.assertRaises(AssertionError):
            qualify(self.reports, self.plan)

    def test_observations_require_matching_owned_receipts_and_cleanup(self):
        with tempfile.TemporaryDirectory() as directory, patch('campaign.HERE', Path(directory)):
            root = Path(directory)
            path = root / 'primary-session-1/00-2-R/process.json'
            path.parent.mkdir(parents=True)
            (path.parent / 'stdout.bin').write_bytes(b'output')
            (path.parent / 'stderr.bin').write_bytes(b'')
            plan = copy.deepcopy(self.plan)
            plan['output_sha256'] = process.sha(path.parent / 'stdout.bin')
            plan['controller_pins'] = {CONTROLLER: 'controller'}
            raw = dict(exit_status=0, quantitative_benchmark=True, inherited_common_mutex=True,
                       deadline_seconds=30, cleanup_errors=[], group_closed=True, reaped=True,
                       signals=[], controller_sha256='controller', elapsed_seconds=2.0,
                       maximum_rss_bytes=1234,
                       birth_identity=dict(pid=123, birth_seconds=456, birth_microseconds=789),
                       command=['/retained/R'])
            sample = dict(order=0, position=2, subject='R', process=str(path.relative_to(root)),
                          seconds=2.0, maximum_rss_bytes=1234,
                          stdout_sha256=plan['output_sha256'], native_sha256=None, native=None,
                          verified=True)

            def validate(record, row, identities):
                path.write_text(json.dumps(record))
                row['process_sha256'] = process.sha(path)
                observation(row, 1, plan, {'R': Path('/retained/R')}, identities, Path('/policy'))

            identities = set()
            validate(raw, sample, identities)
            with self.assertRaises(AssertionError):
                validate(raw, sample, identities)
            for field, value in [('group_closed', False), ('reaped', False),
                                 ('cleanup_errors', ['unreaped child']),
                                 ('quantitative_benchmark', False), ('elapsed_seconds', 1.0),
                                 ('exit_status', 1), ('command', ['/another/R'])]:
                tampered = copy.deepcopy(raw)
                tampered[field] = value
                with self.assertRaises(AssertionError, msg=field):
                    validate(tampered, copy.deepcopy(sample), set())
            wrong_path = copy.deepcopy(sample)
            wrong_path['process'] = '../escaped/process.json'
            with self.assertRaises(AssertionError):
                observation(wrong_path, 1, plan, {'R': Path('/retained/R')}, set(), Path('/policy'))

    def test_rebuilds_preserve_committed_and_previous_receipts(self):
        with tempfile.TemporaryDirectory() as directory, patch('build_subject.HERE', Path(directory)):
            old = Path(directory) / 'baseline/aot-build/process.json'
            old.parent.mkdir(parents=True)
            old.write_text('retained evidence')
            first, binary = allocate('I', 'first')
            receipt = first / 'public-aot.json'
            receipt.write_text('first build')
            second, second_binary = allocate('I', 'second')
            self.assertNotEqual(first, second)
            self.assertNotEqual(binary, second_binary)
            with self.assertRaises(FileExistsError):
                allocate('I', 'first')
            with self.assertRaises(AssertionError):
                allocate('I', '../escape')
            self.assertEqual(old.read_text(), 'retained evidence')
            self.assertEqual(receipt.read_text(), 'first build')


if __name__ == '__main__':
    unittest.main()
