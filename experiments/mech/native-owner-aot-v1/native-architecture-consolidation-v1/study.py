"""One controller implementation, with separately pinned data for two studies."""
if not __debug__:
 raise RuntimeError('Python optimization disables required campaign evidence and process-supervision checks; do not use -O, -OO, or PYTHONOPTIMIZE')
import argparse,importlib.util,json,subprocess,sys
from pathlib import Path
CODE_DIR=Path(__file__).resolve().parent
ROOT=CODE_DIR.parents[3]
STUDY_IDS=('native-architecture-consolidation-v1','post-native-architecture-cleanup-v1')

def select_study(arguments):
 parser=argparse.ArgumentParser(add_help=False,allow_abbrev=False)
 parser.add_argument('--study',choices=STUDY_IDS,action='append')
 selected,remaining=parser.parse_known_args(arguments)
 if selected.study and len(selected.study)!=1:parser.error('--study must be supplied only once')
 return selected.study[0] if selected.study else STUDY_IDS[0],remaining

# Consume only this shared option before each entrypoint handles its own argv.
STUDY_ID,_remaining=select_study(sys.argv[1:])
sys.argv[1:]=_remaining
HERE=CODE_DIR.parent/STUDY_ID
RETAINED=Path('/private/tmp/mech-benchmark-publication')
WORKSPACE=Path('/private/tmp/mech-native-consolidation')
sys.path.insert(0,str(ROOT/'tools/qualification'))
spec=importlib.util.spec_from_file_location('owned_process',ROOT/'experiments/janet/knucleotide-bytes-v1/process.py')
process=importlib.util.module_from_spec(spec);spec.loader.exec_module(process)
def read(path):return json.loads(Path(path).read_text())

def read_plan():
 plan=read(HERE/'plan.json')
 if plan.get('study_id')!=STUDY_ID:raise ValueError('Plan does not belong to the selected study')
 return plan

def build_receipt_path(reference,shared=False):
 """Local receipts, or an explicitly pinned receipt from one of the two studies."""
 base=HERE
 digest=None
 if isinstance(reference,dict) and shared:
  if set(reference)!={'study_id','path','sha256'} or reference['study_id'] not in STUDY_IDS:
   raise ValueError('Shared receipt must identify one of the two maintained studies')
  base=CODE_DIR.parent/reference['study_id']
  name=reference['path'];digest=reference['sha256']
  if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
   raise ValueError('Shared receipt requires its exact SHA-256')
 elif isinstance(reference,str):name=reference
 else:raise ValueError('Build/environment receipt has not been explicitly adopted')
 if not isinstance(name,str) or not name or Path(name).is_absolute():
  raise ValueError('Receipt path must be relative to its named study')
 path=(base/name).resolve()
 if not path.is_relative_to(base.resolve()):raise ValueError('Receipt path escapes its named study')
 if digest is not None and process.sha(path)!=digest:raise ValueError('Shared receipt hash differs from its adopted pin')
 return path

def runtime_environment(plan):
 receipt=read(build_receipt_path(plan.get('runtime_environment_receipt'),shared=True))
 env=receipt.get('environment')
 if not isinstance(env,dict) or not env or not all(isinstance(k,str) and isinstance(v,str) for k,v in env.items()):
  raise ValueError('Runtime environment receipt must contain an explicit string map')
 return env.copy()

def source_state(workspace=None):
 if workspace is None:
  plan=read_plan()
  candidate=read(build_receipt_path(plan.get('candidate_receipt')))
  workspace=Path(candidate.get('workspace',WORKSPACE))
 def git(*args):return subprocess.check_output(['git','-C',str(workspace),*args],text=True).strip()
 return dict(commit=git('rev-parse','HEAD'),tree=git('rev-parse','HEAD^{tree}'),status=git('status','--porcelain'))
def subjects():
 plan=read_plan()
 f=read(build_receipt_path(plan.get('candidate_receipt')))
 i=read(build_receipt_path(plan.get('baseline_receipt'),shared=True))
 controls=read(HERE/'retained-controls.json')
 targets={'F':Path(f['executable']),'I':Path(i['executable']),'W':Path(controls['W']['path']),'R':Path(controls['R']['path'])}
 pins={'F':f['executable_sha256'],'I':i['executable_sha256'],'W':controls['W']['sha256'],'R':controls['R']['sha256']}
 assert source_state(Path(f.get('workspace',WORKSPACE)))==f['source'] and not f['source']['status']
 assert i['source']['commit']==plan['implementation_base']
 for s,p in targets.items():assert process.sha(p)==pins[s],s
 return targets,pins,f,i

def inputs():
 plan=read_plan()
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
