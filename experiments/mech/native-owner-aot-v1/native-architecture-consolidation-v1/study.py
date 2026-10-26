"""Pinned controls and unchanged complete-process checks for this study only."""
if not __debug__:
 raise RuntimeError('Python optimization disables required campaign evidence and process-supervision checks; do not use -O, -OO, or PYTHONOPTIMIZE')
import importlib.util,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
RETAINED=Path('/private/tmp/mech-benchmark-publication')
WORKSPACE=Path('/private/tmp/mech-native-consolidation')
sys.path.insert(0,str(ROOT/'tools/qualification'))
spec=importlib.util.spec_from_file_location('owned_process',ROOT/'experiments/janet/knucleotide-bytes-v1/process.py')
process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
def read(path):return json.loads(Path(path).read_text())
def source_state(workspace=None):
 if workspace is None:
  plan=read(HERE/'plan.json')
  candidate=read(HERE/plan.get('candidate_receipt','candidate/public-aot.json'))
  workspace=Path(candidate.get('workspace',WORKSPACE))
 def git(*args):return subprocess.check_output(['git','-C',str(workspace),*args],text=True).strip()
 return dict(commit=git('rev-parse','HEAD'),tree=git('rev-parse','HEAD^{tree}'),status=git('status','--porcelain'))
def subjects():
 plan=read(HERE/'plan.json')
 f=read(HERE/plan.get('candidate_receipt','candidate/public-aot.json'));i=read(HERE/plan.get('baseline_receipt','baseline/public-aot.json'));controls=read(HERE/'retained-controls.json')
 targets={'F':Path(f['executable']),'I':Path(i['executable']),'W':Path(controls['W']['path']),'R':Path(controls['R']['path'])}
 pins={'F':f['executable_sha256'],'I':i['executable_sha256'],'W':controls['W']['sha256'],'R':controls['R']['sha256']}
 assert source_state(Path(f.get('workspace',WORKSPACE)))==f['source'] and not f['source']['status']
 assert i['source']['commit']==read(HERE/'plan.json')['implementation_base']
 for s,p in targets.items():assert process.sha(p)==pins[s],s
 return targets,pins,f,i

def inputs():
 plan=read(HERE/'plan.json')
 inp=RETAINED/'experiments/janet/.build/inputs/fasta-n25000000.stdin'
 policy=RETAINED/'experiments/mech/native-owner-aot-v1/full-disjoint-state-v1/launch.json'
 data=RETAINED/'data/benchmarks.json'
 for path,key in [(inp,'input_sha256'),(policy,'policy_sha256'),(data,'canonical_data_sha256')]:assert process.sha(path)==plan[key]
 assert inp.stat().st_size==plan['input_bytes']
 return inp,policy,data

def check_native(path):
 # Same complete-process invariants as the retained study; no new tolerance.
 n=read(path)
 assert n['native_aot'] and not n['jit'] and n['policy']=='secured' and n['shutdown']=='completed'
 for key in ['native_hash_table_regions','native_packed_map_regions','native_packed_ssa_regions','native_parallel_tasks','native_parallel_peak_workers','native_guarded_loop_regions','native_guarded_call_regions']:assert n[key]==7,(key,n[key])
 assert n['native_parallel_batches']==1 and n['native_parallel_regions']==2
 assert n['native_frozen_map_regions']==n['native_direct_lookup_regions']==5
 assert n['native_frozen_map_reads']==10
 assert n['native_hash_table_updates']==n['native_packed_map_updates']==874999961
 assert n['native_worker_credit_batches']==854497 and n['native_worker_credit_claims']>0
 assert n['native_fused_string_map_bytes']==125000000
 return {k:v for k,v in n.items() if k.startswith('native_')}
