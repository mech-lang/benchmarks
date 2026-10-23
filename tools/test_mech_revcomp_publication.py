"""Offline preservation, source binding and transactional admission regression checks."""
import copy,json,tempfile,unittest
from pathlib import Path
from qualification import import_mech_revcomp as m
ROOT=Path(__file__).resolve().parents[1]
class AdmissionTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.cohort=m.reconcile(ROOT);cls.catalog=json.loads((ROOT/'data/benchmarks.json').read_bytes());cls.languages=json.loads((ROOT/'data/languages.json').read_bytes())
  if cls.catalog.pop('mech_revcomp_20261022_audit',None):
   for pool in ('programs','program_inventory'):
    for key in m.KEYS.values():cls.catalog[pool].pop(key)
   g=next(g for b in cls.catalog['benchmarks'] if b['key']=='revcomp' for g in b['groups'] if g['language']=='mech');g['programs']=[k for k in g['programs'] if k not in m.KEYS.values()];g['fast']=g['small']=m.PARENT
   cls.languages['languages']['mech']['displayed_program_count']=sum(r['language']=='mech' for r in cls.catalog['programs'].values())
 def test_preserves_all_historical_sources_samples_authorship_and_fixed_axes(self):
  data,meta=m.append_catalog(self.catalog,self.languages,self.cohort,ROOT)
  for pool in ('programs','program_inventory','files','archive_paths'):self.assertTrue(all(data[pool][k]==v for k,v in self.catalog[pool].items()))
  self.assertEqual([(b['baseline_loc'],b['baseline_seconds']) for b in data['benchmarks']],[(b['baseline_loc'],b['baseline_seconds']) for b in self.catalog['benchmarks']])
  self.assertEqual(len(data['files']),len(self.catalog['files']));self.assertEqual(sum(data['programs'][k]['native_observations'] for k in m.KEYS.values()),28)
  for k in m.KEYS.values():
   p=data['programs'][k];self.assertEqual(p['files'],self.catalog['programs'][m.PARENT]['files']);self.assertEqual(p['loc'],7);self.assertEqual(p['authorship'],self.catalog['programs'][m.PARENT]['authorship']);self.assertIsNone(p['formatted_loc']);self.assertEqual(len(p['algorithm']['extended_source_limitations']),11)
  self.assertEqual(data['mech_revcomp_20261022_audit']['fast'],m.KEYS['reuse4']);self.assertEqual(meta['languages']['mech']['displayed_program_count'],self.languages['languages']['mech']['displayed_program_count']+4)
 def test_rejects_tampered_cohort_duplicate_and_source_boundary(self):
  for field,value in [('median_seconds',.001),('source_sha256','0'*64),('runtime_commit','bad')]:
   c=copy.deepcopy(self.cohort);c['programs'][m.KEYS['reuse4']][field]=value
   with self.assertRaisesRegex(ValueError,'cohort drift'):m.append_catalog(self.catalog,self.languages,c,ROOT)
  once,_=m.append_catalog(self.catalog,self.languages,self.cohort,ROOT)
  with self.assertRaisesRegex(ValueError,'already admitted'):m.append_catalog(once,self.languages,self.cohort,ROOT)
  changed=copy.deepcopy(self.catalog);changed['programs'][m.PARENT]['loc']=1
  with self.assertRaisesRegex(ValueError,'source boundary/count'):m.append_catalog(changed,self.languages,self.cohort,ROOT)
 def test_source_authorship_audit_does_not_credit_runtime_edits_as_new_app_writing(self):
  from audit_authorship import audit
  data,_=m.append_catalog(self.catalog,self.languages,self.cohort,ROOT);models=json.loads((ROOT/'data/source-model-evidence.json').read_bytes())['files'];records=audit(data,models)
  for k in m.KEYS.values():self.assertEqual(records[k],data['programs'][k]['authorship'])
 def test_two_target_transaction_rollback_and_external_drift_protection(self):
  for fail_after in (1,2):
   with tempfile.TemporaryDirectory() as t:
    root=Path(t);before={n:b'before' for n in m.TARGETS};after={n:b'after' for n in m.TARGETS}
    for n in m.TARGETS:(root/n).parent.mkdir(parents=True,exist_ok=True);(root/n).write_bytes(before[n])
    with self.assertRaisesRegex(RuntimeError,'injected'):m.apply_targets(root,before,after,fail_after)
    self.assertTrue(all((root/n).read_bytes()==v for n,v in before.items()))
  with tempfile.TemporaryDirectory() as t:
   root=Path(t);before={n:b'before' for n in m.TARGETS};after={n:b'after' for n in m.TARGETS}
   for n in m.TARGETS:(root/n).parent.mkdir(parents=True,exist_ok=True);(root/n).write_bytes(before[n])
   (root/m.TARGETS[1]).write_bytes(b'other writer')
   with self.assertRaisesRegex(ValueError,'input drift'):m.apply_targets(root,before,after)
   self.assertEqual((root/m.TARGETS[0]).read_bytes(),b'before');self.assertEqual((root/m.TARGETS[1]).read_bytes(),b'other writer')
if __name__=='__main__':unittest.main()
