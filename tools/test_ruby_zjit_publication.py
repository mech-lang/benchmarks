"""Verify separately measured engines preserve sources and prior observations."""
import copy
import gzip
import json
import statistics
import unittest

from source_accounting import ROOT, PACKET, transform, historical_catalog


class RubyPublication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.current=json.loads((ROOT/'data/benchmarks.json').read_text())
        cls.original=json.loads(gzip.decompress((ROOT/PACKET/'before.json.gz').read_bytes()))
        cls.previous,_=transform(cls.original,json.loads((ROOT/'data/source-size-review.json').read_text()),
                                  json.loads((ROOT/PACKET/'partitions.json').read_text()))

    def test_previous_results_and_sources_are_exact(self):
        self.assertEqual(self.current['files'],self.previous['files'])
        for pool in ['programs','program_inventory']:
            self.assertEqual(len(self.current[pool])-len(self.previous[pool]),19)
            for key,p in self.previous[pool].items():
                self.assertEqual(self.current[pool][key],p,key)

    def test_zjit_has_independent_process_samples_and_unchanged_loc(self):
        rows=[p for p in self.current['programs'].values() if p['language']=='ruby-zjit']
        self.assertEqual(len(rows),19)
        self.assertEqual(len({p['benchmark'] for p in rows}),10)
        for row in rows:
            parent=self.previous['programs'][row['source_alias_of']]
            self.assertEqual(row['files'],parent['files'])
            self.assertEqual(row['loc'],parent['loc'])
            self.assertIsNone(row['timing_alias_of'])
            self.assertEqual(row['native_observations'],3)
            self.assertEqual(row['seconds'],statistics.median(row['samples']))
            self.assertEqual(row['samples'],[r['elapsed_seconds'] for r in row['sample_execution_metadata']])
            self.assertTrue(all('--zjit' in r['command'] and '--yjit' not in r['command'] and r['valid']
                                for r in row['sample_execution_metadata']))
            self.assertEqual(row['authorship']['kind'],'upstream')
            self.assertTrue(any(s['relationship']=='implementation' for s in row['authorship']['sources']))

    def test_extensions_preserve_the_complete_historical_chain(self):
        self.assertEqual(historical_catalog(ROOT,self.current),self.original)
        changed=copy.deepcopy(self.current)
        key=next(k for k,p in changed['programs'].items() if p['language']=='ruby-zjit')
        changed['programs'][key]['samples'][0]+=1
        with self.assertRaises(AssertionError):
            historical_catalog(ROOT,changed)


if __name__=='__main__':unittest.main()
