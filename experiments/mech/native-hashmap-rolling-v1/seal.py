"""Verify the untimed qualification and profile, then pin retained evidence."""
import hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 q=json.loads((HERE/'qualification-v1/results.json').read_bytes())
 profile=json.loads((HERE/'profile-v1/results.json').read_bytes())
 assert q['status']=='public-source-decoded-security-full-output-and-table-work-passed' and q['hash_table_work_preserved']
 assert profile['status']=='profiled-complete-output-and-table-work-pass' and profile['benchmark_samples']==0
 assert q['source_commit']==profile['source_commit']=='c79dda8cd4b075e7a056f390ba6b9579735f927b'
 assert q['variants']['source']['binary_sha256']==q['variants']['decoded']['binary_sha256']==profile['binary_sha256']
 for variant in ['source','decoded']:
  assert sha(HERE/'.build'/('knucleotide-'+variant))==profile['binary_sha256']
 for prefix,suffix in [('qualification-v1/full-source','.report.json'),('qualification-v1/full-decoded','.report.json'),('profile-v1','/security.json')]:
  p=HERE/prefix
  if prefix=='profile-v1':output=p/'subject/stdout.bin'
  else:output=p/'stdout.bin'
  assert sha(output)=='f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'
  n=json.loads(Path(str(p)+suffix).read_bytes())
  assert n['native_aot'] and not n['jit'] and not n['resident_body_evaluation'] and n['shutdown']=='completed'
  assert n['native_hash_table_regions']==7 and n['native_hash_table_updates']==874999961
 assert sha(ROOT/'data/benchmarks.json')=='849fcdc53d5ccab6ce04c395fd76bec04a675c8767ff3aa138298566387304a7'
 receipts=[p for p in HERE.rglob('process.json') if '.build' not in p.relative_to(HERE).parts]
 for p in receipts:
  r=json.loads(p.read_bytes());assert r['reaped'] and r['group_closed'] and not r['cleanup_errors'],p
  assert not r['quantitative_benchmark']
 out=HERE/'artifact-index-v1.json';files=[]
 for p in sorted(HERE.rglob('*')):
  if p.is_file() and '.build' not in p.relative_to(HERE).parts and '__pycache__' not in p.relative_to(HERE).parts and p!=out:
   files.append(dict(path=str(p.relative_to(HERE)),bytes=p.stat().st_size,sha256=sha(p)))
 result=dict(schema='mech.native-hashmap-rolling-audit.v1',status='sealed-untimed-full-qualification-and-profile',source_commit=q['source_commit'],process_receipts_closed=len(receipts),benchmark_samples=0,required_updates_per_full_mech_process=874999961,canonical_dataset_changed=False,files=files)
 if '--check' in sys.argv:assert json.loads(out.read_bytes())==result
 else:out.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:result[k] for k in ['status','process_receipts_closed','benchmark_samples']}))
if __name__=='__main__':main()
