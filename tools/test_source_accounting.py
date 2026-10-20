"""Regression checks for LOC scope, source preservation and historical replay."""
import copy
import gzip
import json
import unittest

from source_accounting import ROOT, PACKET, historical_catalog, transform


class SourceAccountingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.published = json.loads((ROOT / 'data/benchmarks.json').read_text())
        cls.before = json.loads(gzip.decompress((ROOT / PACKET / 'before.json.gz').read_bytes()))
        cls.partitions = json.loads((ROOT / PACKET / 'partitions.json').read_text())
        # Check the LOC transition independently, then check the complete public
        # catalog including every later admission through historical_catalog.
        cls.current, _ = transform(cls.before,json.loads((ROOT/'data/source-size-review.json').read_text()),cls.partitions)

    def test_sources_and_every_timing_field_are_preserved(self):
        self.assertEqual(self.current['files'], self.before['files'])
        allowed = {'loc','canonical_loc','physical_loc','formatted_loc','formatted_x','file_roles','x','source_accounting'}
        for pool in ('programs','program_inventory'):
            self.assertEqual(self.current[pool].keys(), self.before[pool].keys())
            for key, old in self.before[pool].items():
                self.assertEqual({k:v for k,v in old.items() if k not in allowed},
                                 {k:v for k,v in self.current[pool][key].items() if k not in allowed}, key)

    def test_shared_host_does_not_inflate_application_size(self):
        row = self.current['programs']['mandelbrot:luau-mandelbrot-v1']
        self.assertEqual((row['loc'],row['source_accounting']['previous_loc']), (32,140))
        self.assertEqual(row['source_accounting']['support_loc'],108)
        self.assertEqual(row['file_roles'][row['files'][1]]['role'],'runtime-support')

    def test_embedded_binding_and_workload_helpers_are_distinct(self):
        p = {**self.current['programs'], **self.current['program_inventory']}
        self.assertEqual(p['pidigits:pidigits-rust-3']['loc'],82)
        record = self.partitions['sources']['efb32920c4c8c42ff5c1d6d3a521b9c2a0fc93d06a6f1e994e00c80d39f61b19']
        self.assertEqual((record['application_loc'],record['support_loc']), (21,13))
        self.assertTrue(all(row['role']=='application' for row in record['owner_partition'] if row['line']==13))

    def test_formatted_helpers_follow_the_same_policy(self):
        row = self.current['programs']['pidigits:nim-pidigits-optimized']
        self.assertEqual(row['formatted_loc'],61)
        self.assertEqual(row['source_accounting']['previous_formatted_loc'],79)

    def test_exact_legacy_reconstruction_and_tamper_rejection(self):
        self.assertEqual(historical_catalog(ROOT,self.published), self.before)
        changed = copy.deepcopy(self.published)
        changed['programs']['mandelbrot:luau-mandelbrot-v1']['loc'] += 1
        with self.assertRaisesRegex(AssertionError,'validated source-accounting'):
            historical_catalog(ROOT,changed)

    def test_every_reviewed_partition_reconciles(self):
        for row in self.partitions['sources'].values():
            self.assertEqual(row['full_normalized_loc'],row['application_loc']+row['support_loc'])
        julia = self.partitions['sources']['d9552c519b2a965e9a092c3658460bf8c6e3402dbcd169a498bcff678014da04']
        self.assertEqual((julia['previous_loc'],julia['full_normalized_loc'],julia['application_loc']),(58,52,48))


if __name__ == '__main__':
    unittest.main()
