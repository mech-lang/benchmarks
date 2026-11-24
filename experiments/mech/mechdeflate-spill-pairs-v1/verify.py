"""Independently recompute saved observations, build timings and output streams."""
from pathlib import Path
from hashlib import sha256
from statistics import mean,median
from collections import Counter
import gzip,io,json,math,tarfile,zlib
D=Path(__file__).resolve().parent;sha=lambda b:sha256(b).hexdigest();read=lambda p:json.loads(Path(p).read_bytes());a=read(D/'archive.json');raw=(D/'raw.tar.gz').read_bytes();assert sha(raw)==a['archive_sha256'] and len(raw)==a['archive_bytes'];mb=(D/'raw-manifest.json').read_bytes();assert sha(mb)==a['manifest_sha256'];files=json.loads(mb)['files'];blobs={}
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
 for member in archive:
  assert member.isfile() and member.name.startswith('blobs/');pin=member.name[6:];data=archive.extractfile(member).read();assert len(pin)==64 and pin not in blobs and sha(data)==pin;blobs[pin]=data
assert len(files)==a['files'] and len(blobs)==a['unique_blobs']
for name,row in files.items():assert len(blobs[row['sha256']])==row['bytes'],name
blob=lambda p:blobs[files[p]['sha256']];j=lambda p:json.loads(blob(p));fixtures=j('fixtures.json');byname={v['name']:(i,v) for i,v in enumerate(fixtures)};oracle={v['case']:v for v in j('pinned-peers/libdeflate-output-oracle.json')};policy=j('study/full81-v1/qualification-policy-as-run.json');total=0;paired_blocks=0;all_scores=[]
def runtime(study,filename,full):
 global total,paired_blocks
 result=j(study+'/'+filename);assert result['complete'] and len(result['runs'])==2;plan=result['plan'];assert plan['blocks_per_case']==96;assert files['compare-library.py']['sha256']==plan['timer_sha256'];script='full81.py' if full else 'screen.py';assert files[study+'/'+script]['sha256']==plan['controller_sha256'];role=plan['role'];candidate='actors/'+role+'/bound/mech-worker' if full else study+'/census/'+role+'/bound/mech-worker';assert files[candidate]['sha256']==plan['candidate_worker_sha256'];assert files['actors/control/bound/mech-worker']['sha256']==plan['control_worker_sha256']
 for run in result['runs']:
  base='runtime/'+Path(run['run']).name;rows=j(base+'/summary.json');assert rows==run['results'] and len(rows)==(81 if full else 6);assert files[base+'/summary.json']['sha256']==run['summary_sha256'];assert {r['case'] for r in rows}==set(plan['cases']);complete=j(base+'/complete.json');assert complete['balanced_blocks_per_case']==96 and complete['all_outputs_independently_inflated'] and complete['all_input_and_output_aliases_preserved']
  for row in rows:
   blocks=json.loads(gzip.decompress(blob(base+'/'+row['case']+'/observations.json.gz')));assert len(blocks)==96;_,fixture=byname[row['case']];values={actor:[] for actor in blocks[0]['observations']}
   for block in blocks:
    paired_blocks+=1
    for actor,items in block['observations'].items():
     for item in items:
      total+=1;assert item['case']==row['case'] and item['input_bytes']==fixture['input_bytes'] and item['prefix_bytes']==fixture['prefix_bytes'];assert not item['warmup'] and not item['profile'];assert all(item[k] for k in ['independent_inflation','input_alias_unchanged','borrowed_output_alias_unchanged']);assert math.isfinite(item['seconds']) and item['seconds']>=0
      if actor=='libdeflate':assert item['version']=='1.26' and item['level']==12 and item['reference_capacity']==fixture['capacity'] and all(item[k]==oracle[row['case']][k] for k in ['output_sha256','raw_bytes','capacity','matches_reference_bytes'])
      else:assert item['exact_reference'] and item['raw_bytes']==fixture['raw_bytes'] and item['capacity']==fixture['capacity']
     seconds=mean(v['seconds'] for v in items);assert seconds>0 and math.isclose(seconds,block['means'][actor],rel_tol=1e-12);values[actor].extend(v['seconds'] for v in items)
   for actor,items in values.items():
    assert math.isclose(median(items),row['median_seconds'][actor],rel_tol=1e-12)
    for peer in ['roc','libdeflate']:
     ratio=math.exp(mean(math.log(b['means'][actor]/b['means'][peer]) for b in blocks));assert math.isclose(ratio,row['paired_x_'+peer][actor],rel_tol=1e-12)
  wins={peer:{r['case'] for r in rows if r['paired_x_'+peer]['mech-experiment']<1} for peer in ['roc','libdeflate']}
  for peer,names in policy['required_peer_wins'].items():assert set(names)&{r['case'] for r in rows}<=wins[peer] and not run['required_named_missing'][peer]
  if full:
   assert len(wins['roc'])==81 and len(wins['libdeflate'])==63;all_scores.append({'role':role,'order':run['order'],'roc':81,'libdeflate':63})
  for actor in ['mech-control','mech-experiment']:assert blob(base+'/'+actor+'.stderr').endswith(b'CLEANUP private_payload_bytes=0 live_owner_records=0\n')
  assert blob(base+'/roc.stderr').endswith(b'CLEANUP reference_input_and_output_roots_released=1\n');assert blob(base+'/libdeflate.stderr').endswith(b'CLEANUP libdeflate_compressor_and_output_released=1\n')
for role in ['keep-pairs2','keep-pairs65536']:
 runtime('study','full81-v1/'+role+'-results.json',True);runtime('study','screen-v1/'+role+'-results.json',False)
runtime('one-cell-study','screen-v1/fp1-results.json',False)
recipes=read(D/'recipes.json');binding=j('study/source-commit-binding.json');assert binding['source_commit']==recipes['compiler_source_commit']
for path,pin in binding['files_exact_to_commit'].items():assert files['study/source-overlay/'+path]['sha256']==pin
profiles=set()
for recipe in recipes['roles'].values():
 for key in ['MECH_COMPACT_PHASE_BLOCK_LAYOUT','MECH_COMPACT_PHASE_REGISTER_WEIGHTS']:
  for entry in recipe['flags'].get(key,'').split(';'):
   if entry:
    _,path=entry.split('@',1);p=D/path;assert sha(p.read_bytes())==p.stem;profiles.add(p.stem)
replays=0
for kind in ['public-normal-replay-v1','public-checked-replay-v1','public-source-build-v1']:
 replay=j('study/'+kind+'/reproduction.json');assert replay['source_commit']==recipes['compiler_source_commit'];assert len(replay['records'])==(2 if kind=='public-source-build-v1' else len(recipes['roles']))
 for row in replay['records']:
  assert row['all_three_exact'] and row['artifacts']==recipes['roles'][row['role']]['artifacts'];replays+=1
  for name,pin in row['artifacts'].items():assert files['study/'+kind+'/'+row['role']+'/frontend/'+name]['sha256']==pin
probe=j('study/native-probe-v1/result.json');assert probe['complete'] and probe['all_pass'] and probe['native_calls']==513600 and probe['test_executions']==1;assert files['study/native-probe-v1/execution.log']['sha256']==probe['log_sha256'];assert files['study/native-probe-executable']['sha256']==probe['executable_sha256'];assert 'FP spill native calls: 513600' in blob('study/native-probe-v1/execution.log').decode();observed=j('study/native-probe-v1/observations.json');assert observed['native_observations']==513600 and observed['exact_fallbacks']==80 and observed['changed_functions']==80 and len(observed['functions'])==200 and {r['keep_pairs'] for r in observed['functions']}=={False,True}
public=j('study/public-native-probe-v1/probe-verification.json');assert public['verified'] and public['source_commit']==recipes['compiler_source_commit'] and public['native_calls']==513600;assert public['test_source_sha256']==files['study/source-overlay/hosts/gpu/src/native_artifact/program/codegen/fp_spill_tests.rs']['sha256'];assert files['study/public-native-probe-v1/native-probe-v1/tests.log']['sha256']==public['test_log_sha256'];assert files['study/public-native-probe-v1/native-probe-v1/native-probe-executable']['sha256']==public['binary_sha256'];assert j('study/public-native-probe-v1/native-probe-v1/observations.json')==observed
reused=j('one-cell-study/native-probe-v1/result.json');assert reused['reused_prior_probe'] and reused['new_test_executions']==0;assert files['prior-native-probe/result.json']['sha256']==reused['source_result_sha256'];assert files['prior-native-probe/observations.json']['sha256']==reused['observations_sha256'];prior=j('prior-native-probe/observations.json');assert prior['native_observations']==256800;assert [{k:v for k,v in r.items() if k!='keep_pairs'} for r in observed['functions'] if not r['keep_pairs']]==prior['functions']
audits=j('study/source-checks-v1/result.json');assert len(audits)==3 and all(r['exit_code']==0 for r in audits)
for r in audits:assert files['study/source-checks-v1/'+r['name']+'.log']['sha256']==r['log_sha256']
for role in recipes['roles']:
 folder='baseline-selected' if role=='control' else role;assert files['study/census/'+folder+'/receipt.json']['sha256']==recipes['roles'][role]['source_receipt_sha256']
 for sub in ['frontend','checked/frontend','capture/frontend']:
  for name,pin in recipes['roles'][role]['artifacts'].items():assert files['study/census/'+folder+'/'+sub+'/'+name]['sha256']==pin
for study,roles,fragment in [('study',['keep-pairs-raw','keep-pairs2','keep-pairs65536-raw','keep-pairs65536'],'fp-spill-keep-pairs-study'),('one-cell-study',['fp1-raw','fp1'],'fp-one-cell-study')]:
 for role in roles:
  root=study+'/census/'+role;gate=j(root+'/linked-proof.json');path=study+'/'+gate['result'].split('/'+fragment+'/',1)[1];assert files[path]['sha256']==gate['sha256'];result=j(path);assert result['matches_success_observations']==162 and len(result['checked_failure_cases'])==6 and gate['candidate_peak_stack_bytes']==result['peak_stack_bytes']['candidate']<=5280;recovery=j(root+'/promotion-recoveries/result.json');assert recovery['exact_recoveries']==12 and recovery['benchmark_worker_sha256']==files[root+'/bound/mech-worker']['sha256']
for path in files:
 if '/counts-word-reuse-v1-' not in path or not path.endswith('/counts.json'):continue
 for sample in j(path)['cases'].values():assert sample['counts']['instructions']==sum(len(b['instructions'])*b['visits'] for b in sample['blocks'])
for role,instructions,loads in [('keep-pairs2',164668189,10151519),('keep-pairs65536',164688148,9127055)]:
 c=j('study/census/'+role+'/counts-word-reuse-v1-475/counts.json');assert c['object_sha256']==recipes['roles'][role]['artifacts']['program.o'];r=c['cases']['prefix-random-1048576']['counts'];assert r['instructions']==instructions and r['stack_loads']==loads
build_trials=0;standalone=0
def builds(study,rounds,actors_count,output_count):
 global build_trials,standalone
 root=study+'/matched-builds-v1';plan=j(root+'/plan.json');comparison=j(root+'/comparison.json');assert files[root+'/plan.json']['sha256']==comparison['plan_sha256'];assert len(comparison['observations'])==len(plan['orders'])==rounds and len(plan['actors'])==actors_count;assert files[study+'/complete-build-timer.py']['sha256']==plan['timer_sha256'] and plan['timer_source']['historical_timer_exact'];assert all(Counter(order)==Counter(plan['actors'].keys()) for order in plan['orders'])
 for actor in plan['actors']:assert all(sum(order[i]==actor for order in plan['orders'])==rounds//actors_count for i in range(actors_count))
 for phase,trial in [('warmup',comparison['warmups']),*[(f'order-{i}',r) for i,r in enumerate(comparison['observations'],1)]]:
  for actor,result in trial.items():
   folder=root+'/'+phase+'/'+actor;assert j(folder+'/result.json')==result;job=plan['actors'][actor];expected=job['artifact_sha256'];assert result['generated_artifacts']==expected and all(math.isfinite(v) and v>0 for v in result['seconds'].values());assert files[folder+'/compressor']['sha256']==result['stripped_executable']['sha256'] and len(blob(folder+'/compressor'))==result['stripped_executable']['bytes'];generated={k:folder+'/frontend/'+n for k,n in [('encoder','program.o'),('metadata','metadata.json'),('bytecode','program.mecb')]} if actor.startswith('mech-') else {'encoder':folder+'/'+Path(job['reference_object']).name}
   for kind,path in generated.items():assert files[path]['sha256']==expected[kind]
   for pin in job['profile_inputs_sha256'].values():assert pin in blobs or pin in profiles
 for actor,stats in comparison['medians'].items():
  for stage,v in stats.items():assert math.isclose(v,median(r[actor]['seconds'][stage] for r in comparison['observations']),rel_tol=1e-12)
 for peer,v in comparison['paired_ratios'].items():assert math.isclose(v,median(r['mech-spill']['seconds']['source_through_link']/r[peer]['seconds']['source_through_link'] for r in comparison['observations']),rel_tol=1e-12)
 for actor,peers in comparison.get('paired_actor_ratios',{}).items():
  for peer,v in peers.items():assert math.isclose(v,median(r[actor]['seconds']['source_through_link']/r[peer]['seconds']['source_through_link'] for r in comparison['observations']),rel_tol=1e-12)
 smokes=j(root+'/deployment-smokes.json');assert smokes['checked_executions']==len(smokes['records'])==output_count
 for r in smokes['records']:
  i,fixture=byname[r['case']];data=blob(f'fixtures/{i}/input');stream=blob(root+'/'+r['output_file']);assert sha(data)==r['input_sha256'] and sha(stream)==r['output_sha256'] and len(stream)==r['output_bytes'] and zlib.decompress(stream,-15)==data;expected=blob(f'fixtures/{i}/expected')[len(blob(f'fixtures/{i}/prefix')):];assert (stream==expected)==r['matches_selected_bytes'];assert r['matches_selected_bytes'] or r['actor']=='libdeflate'
 build_trials+=rounds*actors_count;standalone+=output_count
builds('study',10,5,405);builds('one-cell-study',8,4,324)
census=read(D/'hot-block-census.json');assert files[census['source_file']]['sha256']==census['source_sha256'];raw_counts=j(census['source_file'])
for case,entry in census['cases'].items():
 sample=raw_counts['cases'][case];assert entry['instructions']==sample['counts']['instructions'];assert entry['top_blocks']==sorted(sample['blocks'],key=lambda b:len(b['instructions'])*b['visits'],reverse=True)[:3]
s=read(D/'summary.json');assert s['score']=={'roc':81,'libdeflate':63} and s['text_bytes']==63720 and s['compact_text_bytes']==63688 and s['stripped_executable_bytes']==210024;result={'verified':True,'archived_files':len(files),'unique_blobs':len(blobs),'full81_orders':4,'scores':all_scores,'paired_blocks':paired_blocks,'observations':total,'complete_build_trials':build_trials,'standalone_executions':standalone,'private_native_calls':513600,'public_native_calls':513600,'exact_artifact_replays':replays};(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
