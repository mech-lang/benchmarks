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
        if 'ruby_zjit_audit' not in cls.current:
            raise unittest.SkipTest('The full ZJIT cohort has not been admitted yet')
        cls.original=json.loads(gzip.decompress((ROOT/PACKET/'before.json.gz').read_bytes()))
        cls.previous,_=transform(cls.original,json.loads((ROOT/'data/source-size-review.json').read_text()),
                                  json.loads((ROOT/PACKET/'partitions.json').read_text()))

    def test_previous_results_and_sources_are_exact(self):
        self.assertEqual(self.current['files'],self.previous['files'])
        for pool in ['programs','program_inventory']:
            self.assertEqual(len(self.current[pool])-len(self.previous[pool]),22)
            for key,p in self.previous[pool].items():
                self.assertEqual(self.current[pool][key],p,key)
        for old,new in zip(self.previous['benchmarks'],self.current['benchmarks']):
            original_ruby=next(g for g in old['groups'] if g['language']=='ruby')
            current_ruby=next(g for g in new['groups'] if g['language']=='ruby')
            self.assertEqual(current_ruby['programs'][:len(original_ruby['programs'])],original_ruby['programs'])
            groups=[original_ruby if g['language']=='ruby' else g for g in new['groups'] if g['language']!='ruby-zjit']
            self.assertEqual(dict(new,groups=groups),old)
        for section in ['languages','reference_summary','formatted_reference_summary']:
            old=self.previous[section];current=copy.deepcopy(self.current[section][:len(old)])
            for i,row in enumerate(current):
                if row.get('key',row.get('lang'))=='ruby':
                    allowed=['classification_note'] if section=='languages' else ['fast','small']
                    for field in allowed:
                        row[field]=old[i][field]
            self.assertEqual(current,old)

    def test_fresh_yjit_observations_are_in_the_dataset(self):
        rows=[p for k,p in self.current['programs'].items() if k not in self.previous['programs'] and p['language']=='ruby']
        self.assertEqual(len(rows),3)
        self.assertEqual(sum(len(p['samples']) for p in rows),9)
        for p in rows:
            self.assertEqual(p['native_observations'],3)
            self.assertIsNone(p['timing_alias_of'])
            self.assertTrue(all('--yjit' in r['command'] and '--zjit' not in r['command'] and r['valid']
                                for r in p['sample_execution_metadata']))

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
