import copy,json,tempfile,unittest
from pathlib import Path
from mech_logical_extensions import bind,PACKET
ROOT=Path(__file__).resolve().parents[1]
class MechLogicalBindingTests(unittest.TestCase):
 def setUp(self):self.data=json.loads((ROOT/'data/benchmarks.json').read_bytes())
 def test_exact_current_sources_bind_without_native_trees_in_payload(self):
  x=bind(self.data,ROOT);self.assertTrue(x['profiles']);self.assertEqual(x['profiles']['pidigits:mech-pi-final-advance-signed']['application'],38)
  self.assertNotIn('\"owners\":',json.dumps(x));self.assertNotIn('\"syntax\":',json.dumps(x))
 def test_different_source_or_role_never_borrows_count(self):
  key='pidigits:mech-pi-final-advance-signed';d=self.data['programs'][key]['files'][0]
  for mode in ('source','role','range'):
   x=copy.deepcopy(self.data);p=x['programs'][key]
   if mode=='source':
    import hashlib
    f=copy.deepcopy(x['files'][d]);f['code']+='\n';n=hashlib.sha256(f['code'].encode()).hexdigest();f['sha256']=n;x['files'][n]=f;p['files']=[n]
   else:p['file_roles']={d:{'role':'runtime-support'} if mode=='role' else {'role':'application','support_line_ranges':[{'start':1,'end':1}]}}
   self.assertNotIn(key,bind(x,ROOT)['profiles'])
 def test_source_override_and_false_hash_rejected(self):
  key='pidigits:mech-pi-final-advance-signed';d=self.data['programs'][key]['files'][0]
  x=copy.deepcopy(self.data);x['files'][d]['code']+='drift'
  with self.assertRaisesRegex(ValueError,'source bytes'):bind(x,ROOT)
 def test_missing_or_changed_proof(self):
  with tempfile.TemporaryDirectory() as t:
   self.assertIsNone(bind(self.data,t));p=Path(t)/PACKET/'qualification.json';p.parent.mkdir(parents=True);p.write_text('{}')
   with self.assertRaisesRegex(ValueError,'frozen proof'):bind(self.data,t)
if __name__=='__main__':unittest.main()
