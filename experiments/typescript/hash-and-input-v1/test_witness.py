#!/usr/bin/env python3
"""Corruption checks against captured wide-key native Map diagnostics."""
import copy
import gzip
import importlib.util
import json
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('map_qualification_tests', HERE / 'qualify.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


class CompleteWorkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.expected = native.expected_maps(native.bases(native.cases()['wide-key-collisions']))
        path = HERE / 'native-v1/buffer-cells-wide-key-collisions-work.maps.json.gz'
        cls.record = json.loads(gzip.decompress(path.read_bytes()))

    def test_retained_native_trace(self):
        native.check_witness(self.record, self.expected, True)
        self.assertTrue(any(key >= 2**32 for key, _ in self.record['maps'][-1]['entries']))

    def test_missing_histogram(self):
        record = copy.deepcopy(self.record)
        record['maps'].pop()
        with self.assertRaises(AssertionError):
            native.check_witness(record, self.expected, True)

    def test_query_only_counting(self):
        record = copy.deepcopy(self.record)
        record['maps'][-1]['entries'] = record['maps'][-1]['entries'][:1]
        with self.assertRaises(AssertionError):
            native.check_witness(record, self.expected, True)

    def test_missing_occurrence(self):
        record = copy.deepcopy(self.record)
        record['maps'][0]['events'].pop()
        with self.assertRaises(AssertionError):
            native.check_witness(record, self.expected, True)

    def test_narrowed_36bit_key(self):
        record = copy.deepcopy(self.record)
        for entry in record['maps'][-1]['entries']:
            entry[0] %= 2**32
        with self.assertRaises(AssertionError):
            native.check_witness(record, self.expected, True)

    def test_hidden_map_set_for_each_cell_increment(self):
        record = copy.deepcopy(self.record)
        record['maps'][0]['sets'] += 1
        with self.assertRaises(AssertionError):
            native.check_witness(record, self.expected, True)

    def test_missing_cell_update(self):
        record = copy.deepcopy(self.record)
        record['maps'][0]['cell_updates'] -= 1
        with self.assertRaises(AssertionError):
            native.check_witness(record, self.expected, True)


if __name__ == '__main__':
    unittest.main()
