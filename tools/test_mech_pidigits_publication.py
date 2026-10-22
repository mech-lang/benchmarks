"""Offline evidence, preservation and rollback tests; no timing subjects launched."""
import copy,json,tempfile,unittest
from pathlib import Path
from qualification import import_mech_pidigits as m
ROOT=Path(__file__).resolve().parents[1]
class AdmissionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cohort=m.reconcile(ROOT);cls.catalog=json.loads((ROOT/'data/benchmarks.json').read_bytes());cls.languages=json.loads((ROOT/'data/languages.json').read_bytes())
  if cls.catalog.pop('mech_pidigits_20261022_audit',None):
   for pool in ('programs','program_inventory'):
    for key in m.KEYS.values():cls.catalog[pool].pop(key,None)
   bench=next(b for b in cls.catalog['benchmarks'] if b['key']=='pidigits');g=next(g for g in bench['groups'] if g['language']=='mech');g['programs']=[k for k in g['programs'] if k not in m.KEYS.values()]
   rows=[cls.catalog['programs'][k] for k in g['programs']];g['fast']=min(rows,key=lambda r:(r['seconds'],r['loc'],r['key']))['key']
   cls.languages['languages']['mech']['displayed_program_count']=sum(r['language']=='mech' for r in cls.catalog['programs'].values())
 def test_preserves_every_historical_source_sample_and_fixed_axis(self):
  after,meta=m.append_catalog(self.catalog,self.languages,self.cohort,ROOT)
  for pool in ('programs','program_inventory','files','archive_paths'):
   self.assertTrue(all(after[pool][k]==v for k,v in self.catalog[pool].items()))
  self.assertEqual([(b['baseline_loc'],b['baseline_seconds']) for b in after['benchmarks']],[(b['baseline_loc'],b['baseline_seconds']) for b in self.catalog['benchmarks']])
  group=next(g for b in after['benchmarks'] if b['key']=='pidigits' for g in b['groups'] if g['language']=='mech')
  self.assertEqual(group['fast'],m.KEYS['compact-shared']);self.assertEqual(group['small'],'pidigits:mech-pi-final-compact-signed')
  self.assertEqual(sum(after['programs'][k]['native_observations'] for k in m.KEYS.values()),21)
  self.assertEqual(self.catalog['programs'][m.PARENT]['samples'],after['programs'][m.PARENT]['samples'])
  self.assertEqual(meta['languages']['mech']['displayed_program_count'],self.languages['languages']['mech']['displayed_program_count']+3)
 def test_rejects_unknown_minimum_duplicate_and_source_drift(self):
  c=copy.deepcopy(self.cohort);c['programs'][m.KEYS['compact-shared']]['median_seconds']=.0001
  with self.assertRaisesRegex(ValueError,'cohort drift'):m.append_catalog(self.catalog,self.languages,c,ROOT)
  c=copy.deepcopy(self.cohort);c['programs'][m.KEYS['compact-shared']]['source_sha256']='0'*64
  with self.assertRaisesRegex(ValueError,'cohort drift'):m.append_catalog(self.catalog,self.languages,c,ROOT)
  once,_=m.append_catalog(self.catalog,self.languages,self.cohort,ROOT)
  with self.assertRaisesRegex(ValueError,'already admitted'):m.append_catalog(once,self.languages,self.cohort,ROOT)
 def test_transaction_failure_rolls_back_both_targets(self):
  for fail_after in (1,2):
   with tempfile.TemporaryDirectory() as t:
    root=Path(t);before={n:b'before' for n in m.TARGETS};after={n:b'after' for n in m.TARGETS}
    for n in m.TARGETS:(root/n).parent.mkdir(parents=True,exist_ok=True);(root/n).write_bytes(before[n])
    with self.assertRaisesRegex(RuntimeError,'injected'):m.apply_targets(root,before,after,fail_after=fail_after)
    self.assertTrue(all((root/n).read_bytes()==v for n,v in before.items()))
 def test_drift_is_preserved_and_local_authorship_does_not_relabel_parent(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);before={n:b'before' for n in m.TARGETS};after={n:b'after' for n in m.TARGETS}
   for n in m.TARGETS:(root/n).parent.mkdir(parents=True,exist_ok=True);(root/n).write_bytes(before[n])
   (root/m.TARGETS[1]).write_bytes(b'other writer')
   with self.assertRaisesRegex(ValueError,'input drift'):m.apply_targets(root,before,after)
   self.assertEqual((root/m.TARGETS[1]).read_bytes(),b'other writer');self.assertEqual((root/m.TARGETS[0]).read_bytes(),b'before')
  after,_=m.append_catalog(self.catalog,self.languages,self.cohort,ROOT)
  self.assertEqual(after['programs'][m.KEYS['parent']]['authorship'],self.catalog['programs'][m.PARENT]['authorship'])
  a=after['programs'][m.KEYS['compact-shared']]['authorship'];self.assertEqual(a['ai']['model_family'],'Codex GPT-6');self.assertIsNone(a['ai']['exact_model']);self.assertEqual(a['license'],self.catalog['programs'][m.PARENT]['authorship']['license'])
if __name__=='__main__':unittest.main()
