"""Independently replay hashes, owned-process closure and cohort arithmetic."""
import json,hashlib,statistics,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
EXPECTED='f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def closed(path):
 r=json.loads(path.read_bytes());assert r['reaped'] and r['group_closed'] and not r['cleanup_errors'],path;return r

def main():
 out=HERE/'artifact-index-v1.json'
 q=json.loads((HERE/'qualification-v4/results.json').read_bytes());assert q['status']=='public-source-decoded-security-full-output-and-table-work-passed' and q['hash_table_work_preserved']
 r=json.loads((HERE/'rust-comparison-v2/results.json').read_bytes());assert r['status']=='seven-matched-serial-rounds-all-full-outputs-pass'
 assert q['source_commit']==r['mech_source_commit']=='a83c2b5ff606d863d55ecbed9f1b5687f18ac813'
 assert q['variants']['source']['binary_sha256']==q['variants']['decoded']['binary_sha256']==r['mech_binary_sha256']
 assert sha(HERE/'qualification-v4/launch.json')==q['policy_sha256']==r['policy_sha256']
 assert sha(ROOT/'archive/workloads/knucleotide/upstream/knucleotide-rust-7.rs')==r['rust_source_sha256']=='47548a02d18bbc68734b0ef2145e3bd89523f15fa779682031ddbd462dbf7851'
 assert sha(ROOT/'experiments/janet/.build/inputs/fasta-n25000000.stdin')==q['input_sha256']==r['input_sha256']
 assert sha(HERE/'.build/knucleotide-source')==r['mech_binary_sha256']
 assert sha(HERE/'.build/knucleotide-decoded')==r['mech_binary_sha256']
 assert sha(HERE/'.build/knucleotide-rust-7')==r['rust_binary_sha256']
 for variant in ['source','decoded']:
  subject=HERE/'qualification-v4'/('full-'+variant);assert closed(subject/'process.json')['exit_status']==0
  assert sha(subject/'stdout.bin')==EXPECTED
  native=json.loads((HERE/'qualification-v4'/('full-'+variant+'.report.json')).read_bytes())
  assert native['native_hash_table_regions']==7 and native['native_hash_table_updates']==874999961
  assert native['native_aot'] and not native['jit'] and not native['resident_body_evaluation'] and native['shutdown']=='completed'
 samples=r['samples'];assert len(samples)==14
 recomputed={}
 for subject in ['mech','rust']:
  rows=[s for s in samples if s['subject']==subject];assert len(rows)==7 and {s['round'] for s in rows}==set(range(7))
  for sample in rows:
   receipt=ROOT/sample['process'];p=closed(receipt);assert p['exit_status']==0 and p['quantitative_benchmark']
   assert p['elapsed_seconds']==sample['seconds']
   assert sha(receipt.parent/'stdout.bin')==EXPECTED and not (receipt.parent/'stderr.bin').read_bytes()
   if subject=='mech':
    native=json.loads((receipt.parent.parent/(receipt.parent.name+'.security.json')).read_bytes())
    assert native['native_hash_table_regions']==7 and native['native_hash_table_updates']==874999961
  values=[s['seconds'] for s in rows]
  recomputed[subject]=dict(median_seconds=statistics.median(values),sample_sd_seconds=statistics.stdev(values))
 denominator=recomputed['mech']['median_seconds']
 for subject in recomputed:
  recomputed[subject]['x_mech_aot']=recomputed[subject]['median_seconds']/denominator
 assert recomputed==r['statistics']
 receipts=list(HERE.rglob('process.json'))
 receipts=[p for p in receipts if '.build' not in p.relative_to(HERE).parts]
 for p in receipts:closed(p)
 legacy=Path('/private/tmp/mech-pidigits-performance/target/release/mech')
 assert sha(legacy)=='5445d4b291972badef19ac655728675ee972618fbe47c899ecfd5c514a2582fa'
 files=[]
 for p in sorted(HERE.rglob('*')):
  parts=p.relative_to(HERE).parts
  if p.is_file() and '.build' not in parts and '__pycache__' not in parts and p!=out:
   files.append(dict(path=str(p.relative_to(HERE)),bytes=p.stat().st_size,sha256=sha(p)))
 result=dict(schema='mech.native-hash-table-work-audit.v1',status='sealed-full-output-work-and-matched-cohort',source_commit=q['source_commit'],process_receipts_closed=len(receipts),mech_required_updates_per_full_process=874999961,qualified_source_decoded_full_outputs=2,matched_samples=14,statistics=recomputed,denominator=r['denominator'],protected_rust_source_unchanged=True,legacy_emitter_unchanged=True,canonical_dataset_changed=False,files=files)
 if '--check' in sys.argv:
  assert json.loads(out.read_bytes())==result
 else:
  out.write_text(json.dumps(result,indent=2)+'\n');assert json.loads(out.read_bytes())==result
 print(json.dumps({k:result[k] for k in ['status','process_receipts_closed','matched_samples','statistics','canonical_dataset_changed']}))
if __name__=='__main__':main()
