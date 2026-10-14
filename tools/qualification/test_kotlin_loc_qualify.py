"""Pure regression checks for source-count admission and saved native receipts."""
import copy
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).with_name('kotlin_loc_qualify.py')
SPEC = importlib.util.spec_from_file_location('kotlin_source_count_qualification_tests', PATH)
Q = importlib.util.module_from_spec(SPEC)
exec(compile(PATH.read_bytes(), str(PATH), 'exec'), Q.__dict__)
EXPECTED = {
    'binarytrees': [45, 52], 'fannkuchredux': [62, 86], 'fasta': [61, 79],
    'knucleotide': [66, 82], 'mandelbrot': [60, 69], 'nbody': [78, 103],
    'pidigits': [56, 62], 'regexredux': [55, 61], 'revcomp': [52, 96],
    'spectralnorm': [51, 69],
}


class ReviewedCounts(unittest.TestCase):
    def setUp(self):
        self.plan = Q.read(Q.PLAN)
        self.replay = Q.read(Q.REPLAY)
        self.expected = copy.deepcopy(EXPECTED)
        self.hashes = {i['id']: i['source_sha256'] for i in Q.read(Q.RUN/'native-reader/sources/report.json')['items']}

    def check(self):
        return Q.reviewed_counts(self.plan, self.replay, self.expected, self.hashes)

    def test_actual_inventory(self):
        files, profiles = self.check()
        self.assertEqual(len(files), 40)
        self.assertEqual(len(profiles), 20)
        self.assertTrue(all(p['formatted_loc'] is None and not p['formatted_loc_qualified'] for p in profiles))

    def test_missing_helper(self):
        self.plan['profiles'][0]['inputs'].pop()
        with self.assertRaises(AssertionError): self.check()

    def test_duplicate_profile(self):
        self.plan['profiles'][-1] = self.plan['profiles'][0]
        with self.assertRaises(AssertionError): self.check()

    def test_missing_fixture(self):
        self.replay['fixture_checks'].pop()
        with self.assertRaises(AssertionError): self.check()

    def test_failed_fixture(self):
        self.replay['fixture_checks'][0]['passed'] = False
        with self.assertRaises(AssertionError): self.check()

    def test_owner_diagnostic(self):
        key = self.plan['profiles'][0]['inputs'][0]
        self.replay['files'][key]['diagnostics'] = [{'kind': 'unowned'}]
        with self.assertRaises(AssertionError): self.check()

    def test_source_identity_change(self):
        key = self.plan['profiles'][0]['inputs'][0]
        self.hashes[key] = '0'*64
        with self.assertRaises(AssertionError): self.check()

    def test_null_count(self):
        key = self.plan['profiles'][0]['inputs'][0]
        self.replay['files'][key]['normalized_loc'] = None
        with self.assertRaises(AssertionError): self.check()

    def test_different_review_total(self):
        self.expected['binarytrees'][1] += 1
        with self.assertRaises(AssertionError): self.check()

    def test_formatter_claim(self):
        self.replay['formatter_evidence_available'] = True
        with self.assertRaises(AssertionError): self.check()


class NativeReceipt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader = Q.module(Q.READER, Q.PINS[Q.READER])
        cls.supervisor = cls.reader.module()

    def setUp(self):
        self.plan = Q.read(Q.PLAN)
        self.folder = Q.RUN/'native-reader'
        self.receipt = Q.read(self.folder/'process.json')
        self.pid = Q.read(Q.DURABLE)['command_pid']

    def check(self):
        Q.validate_process(self.receipt, 'native-source-reader', self.folder, self.plan,
                           self.pid, self.supervisor, self.reader)

    def test_actual_saved_receipt(self):
        self.check()

    def test_changed_command(self):
        self.receipt['command'][-1] += '-other'
        with self.assertRaises(AssertionError): self.check()

    def test_injected_environment(self):
        self.receipt['environment']['JAVA_TOOL_OPTIONS'] = '-Xint'
        with self.assertRaises(AssertionError): self.check()

    def test_wrong_birth_identity(self):
        self.receipt['leader_identity_before_reap']['birth_microseconds'] += 1
        with self.assertRaises(AssertionError): self.check()

    def test_wrong_process_owner(self):
        self.pid += 1
        with self.assertRaises(AssertionError): self.check()

    def test_missing_resource_observations(self):
        self.receipt['kernel_monitor_samples'] = 0
        with self.assertRaises(AssertionError): self.check()

    def test_changed_resource_policy(self):
        self.receipt['process_timeout_seconds'] *= 2
        with self.assertRaises(AssertionError): self.check()

    def test_unreaped_native(self):
        self.receipt['direct_child_reaped'] = False
        with self.assertRaises(AssertionError): self.check()


if __name__ == '__main__':
    unittest.main()
