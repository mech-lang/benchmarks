"""Regressions for unqualified statistics and preserved build evidence."""
import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from analyze import analyze_sessions, analyze
from build_subject import allocate


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
