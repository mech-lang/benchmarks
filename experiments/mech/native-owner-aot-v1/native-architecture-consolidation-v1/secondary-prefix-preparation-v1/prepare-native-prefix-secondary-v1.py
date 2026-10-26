"""Assemble read-only preparation notes; never invokes benchmark executables."""
from pathlib import Path
from collections import Counter
import hashlib,json
ROOT=Path('/private/tmp/mech-benchmark-publication')
REPO=Path('/private/tmp/benchmarks-native-consolidation')
BASE=ROOT/'experiments/mech/native-owner-aot-v1'
CODE=REPO/'experiments/mech/native-owner-aot-v1/native-architecture-consolidation-v1'
HIST=BASE/'paired-candidate-loads-timing-v1'

def read(p):return json.loads(p.read_text())
def pin(p):return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def require(value,message):
 if not value:raise ValueError(message)
controls=read(CODE/'retained-controls.json')
historical=read(HIST/'results.json')
for s,key in [('W','candidate_sha256'),('R','rust_sha256')]:
 require(pin(Path(controls[s]['path']))['sha256']==controls[s]['sha256']==historical[key], 'Retained executable changed')
require(historical['source_sha256']==pin(BASE/'knucleotide-source-map.mec')['sha256'],'Retained source changed')
require(historical['bytecode_sha256']==pin(Path(controls['W']['path']+'.project/program.mecb'))['sha256'],'Retained bytecode changed')
require(historical['object_sha256']==pin(Path(controls['W']['object_path']))['sha256']==controls['W']['object_sha256'],'Retained Object changed')
oracle=read(Path('/private/tmp/native-prefix-independent-oracle-v1.json'))
require(historical['input_sha256']==oracle['input']['sha256'],'Input pin differs')
old_policy=BASE/'full-timing-v1/launch.json';policy=BASE/'full-disjoint-state-v1/launch.json'
require(pin(old_policy)['sha256']==historical['launch_sha256'],'Historical policy changed')
old,new=read(old_policy),read(policy)
changes={}
def diff(a,b,prefix=''):
 for key in sorted(set(a)|set(b)):
  name=prefix+key
  if isinstance(a.get(key),dict) and isinstance(b.get(key),dict):diff(a[key],b[key],name+'.')
  elif a.get(key)!=b.get(key):changes[name]={'historical':a.get(key),'proposed':b.get(key)}
diff(old,new)
require(set(changes)=={'work','library.comparison_work'},'Unexpected policy differences')
require(all(v['proposed']>v['historical'] for v in changes.values()),'New policy is not the existing larger finite policy')
orders=[['F','I','R','W'],['I','W','F','R'],['W','R','I','F'],['R','F','W','I']]
require(all(Counter(row[i] for row in orders)==dict.fromkeys('FIWR',1) for i in range(4)),'Unbalanced positions')
require(len(Counter((a,b) for row in orders for a,b in zip(row,row[1:])))==12,'Unbalanced adjacent pairs')
prior=[]
for round_id in ['warmup','0','1','2']:
 for label in ['candidate','baseline','rust']:
  folder=HIST/f'{round_id}-{label}';receipt=read(folder/'process.json')
  require(receipt['exit_status']==0 and receipt['cleanup_errors']==[] and receipt['group_closed'] and receipt['reaped'],'Prior process incomplete')
  require(pin(folder/'stdout.bin')['sha256']==oracle['expected_output']['sha256'],'Prior output differs')
  require(receipt['inherited_common_mutex'] and receipt['deadline_seconds']==120,'Prior process contract differs')
  row={'label':label,'round':round_id,'process':pin(folder/'process.json'),'stdout':pin(folder/'stdout.bin'),'stderr':pin(folder/'stderr.bin'),
       'quantitative_benchmark':receipt['quantitative_benchmark'],'reused_as_new_observation':False}
  if label!='rust':row['native_report']=pin(HIST/f'{round_id}-{label}.report.json')
  prior.append(row)
reports=[read(p) for p in sorted(HIST.glob('*-candidate.report.json'))]
variable={key:sorted({r[key] for r in reports}) for key in ['native_work','native_comparison_work','native_worker_credit_claims','native_worker_credit_reclaims']}
exact={**dict.fromkeys(['native_hash_table_regions','native_packed_map_regions','native_packed_ssa_regions','native_guarded_loop_regions','native_guarded_call_regions','native_parallel_tasks'],7),
       'native_hash_table_updates':oracle['expected_updates'],'native_packed_map_updates':oracle['expected_updates'],
       'native_fused_string_map_bytes':1000000,'native_worker_credit_batches':oracle['expected_funded_batches'],
       'native_parallel_batches':1,'native_parallel_regions':2,'native_frozen_map_regions':5,'native_direct_lookup_regions':5,'native_frozen_map_reads':10}
require(all(all(r[key]==value for key,value in exact.items()) for r in reports),'Derived counters disagree with retained W evidence')
compile_rows={}
for subject,path,scope in [
 ('W',HIST/'build/process.json','Historical public AOT build: source emission and Rust host compilation/link; includes existing cache state'),
 ('R',ROOT/'experiments/mech/native-hashmap-work-v1/rust-comparison-v2/rust-build/process.json','Historical direct rustc build of retained R; dependency compilation excluded')]:
 r=read(path);require(r['exit_status']==0 and r['cleanup_errors']==[] and r['group_closed'] and r['reaped'],'Build receipt incomplete')
 compile_rows[subject]={'seconds':r['elapsed_seconds'],'receipt':pin(path),'scope':scope,'fresh_cold_compile_comparison':False}
rust_deps=ROOT/'experiments/mech/native-hashmap-work-v1/rust-comparison-v2/rust-dependencies/process.json'
compile_rows['R_dependency_preparation']={'seconds':read(rust_deps)['elapsed_seconds'],'receipt':pin(rust_deps),'scope':'Historical Cargo dependency stage; cache-dependent, separate from direct rustc'}
notes={
 'schema':'mech.secondary-prefix-preparation.v1','status':'prepared-only; no subject execution; final F/I and primary-session completion pending',
 'scope':'Prospective complete-process one-million-base prefix diagnostic, separate from primary192 and from compile/size observations',
 'performance_qualified':False,'primary_timing_samples':0,'secondary_observations_collected':0,
 'oracle':oracle,'oracle_derivation_script':pin(Path('/private/tmp/native-prefix-independent-oracle-v1.py')),
 'source_compatibility':{'full_public_source':pin(BASE/'knucleotide-source-map.mec'),'bytecode':pin(Path(controls['W']['path']+'.project/program.mecb')),
  'guest_object':pin(Path(controls['W']['object_path'])),'historical_results':pin(HIST/'results.json'),
  'conclusion':'The original public source computes N from the selected THREE record; no hard-coded full/prefix length. Original W and R already produced the exact retained prefix output. F/I eligibility requires their adopted public receipts, same source/bytecode/Object checks and completed primary sessions; no replacements or rebuilding.'},
 'historical_prefix_policy':pin(old_policy),'proposed_policy':pin(policy),'policy_changes_from_historical_prefix':changes,
 'policy_choice':'Use the currently adopted primary secured policy unchanged for every new Mech prefix observation; only input changes. Historical prefix times are not pooled or compared as new samples.',
 'retained_controls':{s:{'executable':pin(Path(controls[s]['path'])),'rebuild':False} for s in ('W','R')},
 'shared_runtime_environment':pin(CODE/'runtime-environment-v1.json'),
 'shared_execution_owners':{name:pin(path) for name,path in {'study':CODE/'study.py','campaign':CODE/'campaign.py','process':REPO/'experiments/janet/knucleotide-bytes-v1/process.py','supervisor':REPO/'tools/qualification/prolog_supervisor.py'}.items()},
 'protocol':{'per_study_observations':16,'orders':orders,'warmups':0,'excluded_outliers':0,'retries_or_replacement_samples':0,
  'run_when':'Only after both primary sessions are complete and validate_reports passes; preferably after primary campaigns in both studies so these diagnostics cannot warm another pending primary campaign.',
  'subject_resolution':'Existing study.subjects() from explicitly adopted receipts; same F/I/W/R executable hashes as primary sessions',
  'runtime_environment':'Existing study.runtime_environment(plan), identical for all four subjects, without overrides',
  'policy':'Existing study.inputs() policy, pinned to proposed_policy above',
  'process':'Existing process.execute with stdin=retained prefix, deadline=30, quantitative=True; same r+ shared mutex, no replacement inode',
  'mutex':{'path':'/private/tmp/mech-clbg-timing.lock','inode':83858837},
  'commands':{'F/I/W':['<adopted executable>','<unchanged primary policy>','<unique secondary native report>','--'],'R':['<retained R executable>']},
  'verification':'Validate before/after source and executable/input/policy/controller pins; raw receipt exit0, no error/signals/unfinished observer, cleanup_errors empty, group_closed/reaped; output exact249 bytes; unique birth identities; retain every raw stdout/stderr/report including failures',
  'summary':'Show all16 elapsed observations and four-sample medians per subject; descriptive within-row ratios allowed; no bootstrap acceptance, no speedup/no-regression claim, no pooling with primary or old prefix timings',
  'archives':'New per-study secondary-prefix-v1 directory plus immutable prospective protocol; leave all old attempts unchanged'},
 'native_checks':{'exact_counters':exact,'required_flags':{'native_aot':True,'jit':False,'source_parser':False,'resident_body_evaluation':False,'policy':'secured','shutdown':'completed'},
  'schedule_dependent_checks':{'native_parallel_peak_workers':'integer in1..7, not exact7 for short input','native_worker_credit_claims':'positive integer','native_worker_credit_reclaims':'equals claims after complete shutdown','native_work':'positive and within unchanged finite policy work cap','native_comparison_work':'positive and within unchanged finite comparison cap'},
  'independent_derivation':'Seven histogram widths from unchanged source; updates sum(N-k+1)=7*N-39. Full funded batches sum(ceil((N-k+1)/1024)); unchanged runtime BATCH1024 and ample finite caps. Source has2+5 histogram tasks in two comprehensions, five query maps and two lookups per query.',
  'do_not_hardcode':variable},
 'visible_separate_metrics':{'prefix_time':'New16-observation diagnostic only, seconds to complete process exit',
  'executable_size':'File stat bytes of actual primary-pinned public executable, verified SHA before/after; F/I resolved when adopted; W5517792/R755872 now',
  'compile_time':{'F/I':'Read their adopted compiler-build/process.json and aot-build/process.json separately; no new build or runtime sum',
   'retained_observations':compile_rows,'caveat':'Build elapsed receipts are historical/cache-dependent observations with different scopes, not a controlled comparative compilation benchmark.'}},
 'historical_prefix_process_evidence':prior,
 'pending':['Final F/I receipt pins','All required primary sessions and evidence validation','Prospective secondary protocol adoption before first diagnostic sample'],
}
path=Path('/private/tmp/native-prefix-secondary-preparation-v1.json');path.write_text(json.dumps(notes,indent=2)+'\n')
print(json.dumps({'preparation':pin(path),'expected_output':oracle['expected_output'],'updates':oracle['expected_updates'],'worker_credit_batches':oracle['expected_funded_batches'],'historical_receipts_checked':len(prior),'new_subject_executions':0},indent=2))
