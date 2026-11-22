"""Verify all qualified runtime observations, complete builds and raw streams."""
from pathlib import Path
from hashlib import sha256
from statistics import mean,median
import gzip,io,json,math,re,tarfile,zlib
D=Path(__file__).resolve().parent;read=lambda p:json.loads(p.read_bytes());sha=lambda b:sha256(b).hexdigest();a=read(D/'archive.json');raw=(D/'raw.tar.gz').read_bytes();assert sha(raw)==a['archive_sha256'] and len(raw)==a['archive_bytes'];mb=(D/'raw-manifest.json').read_bytes();assert sha(mb)==a['manifest_sha256'];manifest=json.loads(mb);files=manifest['files']
with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
 blobs={}
 for member in archive:
  assert member.isfile() and member.name.startswith('blobs/');pin=member.name[6:];data=archive.extractfile(member).read();assert len(pin)==64 and pin not in blobs and sha(data)==pin;blobs[pin]=data
assert len(files)==a['files'] and len(blobs)==a['unique_blobs']
for name,row in files.items():assert len(blobs[row['sha256']])==row['bytes'],name
blob=lambda name:blobs[files[name]['sha256']];j=lambda name:json.loads(blob(name));fixtures=j('fixtures.json');byname={row['name']:(index,row) for index,row in enumerate(fixtures)};policy=j('study/full81-v1/qualification-policy-as-run.json');oracle={row['case']:row for row in j('pinned-peers/libdeflate-output-oracle.json')};full=j('study/full81-v1/fp2-results.json');assert full['complete'] and len(full['runs'])==2;plan=full['plan'];assert plan['blocks_per_case']==96;assert files['actors/control/bound/mech-worker']['sha256']==plan['control_worker_sha256'];assert files['actors/fp2/bound/mech-worker']['sha256']==plan['candidate_worker_sha256'];assert files['compare-library.py']['sha256']==plan['timer_sha256'];assert files['study/full81.py']['sha256']==plan['controller_sha256'];total=0;paired_blocks=0;scores=[]
for run in full['runs']:
 base='runtime/'+Path(run['run']).name;rows=j(base+'/summary.json');assert rows==run['results'] and len(rows)==81;assert files[base+'/summary.json']['sha256']==run['summary_sha256'];assert {row['case'] for row in rows}==set(byname);complete=j(base+'/complete.json');assert complete['balanced_blocks_per_case']==96 and complete['all_outputs_independently_inflated'] and complete['all_input_and_output_aliases_preserved']
 for row in rows:
  blocks=json.loads(gzip.decompress(blob(base+'/'+row['case']+'/observations.json.gz')));assert len(blocks)==96;_,fixture=byname[row['case']];values={actor:[] for actor in blocks[0]['observations']}
  for block in blocks:
   paired_blocks+=1
   for actor,items in block['observations'].items():
    for item in items:
     total+=1;assert item['case']==row['case'] and item['input_bytes']==fixture['input_bytes'] and item['prefix_bytes']==fixture['prefix_bytes'];assert not item['warmup'] and not item['profile'];assert all(item[key] for key in ['independent_inflation','input_alias_unchanged','borrowed_output_alias_unchanged']);assert math.isfinite(item['seconds']) and item['seconds']>=0
     if actor=='libdeflate':assert all(item[key]==oracle[row['case']][key] for key in ['output_sha256','raw_bytes','capacity','matches_reference_bytes'])
     else:assert item['exact_reference'] and item['raw_bytes']==fixture['raw_bytes'] and item['capacity']==fixture['capacity']
    seconds=mean(v['seconds'] for v in items);assert seconds>0 and math.isclose(seconds,block['means'][actor],rel_tol=1e-12);values[actor].extend(v['seconds'] for v in items)
  for actor,items in values.items():
   assert math.isclose(median(items),row['median_seconds'][actor],rel_tol=1e-12)
   for peer in ['roc','libdeflate']:
    ratio=math.exp(mean(math.log(b['means'][actor]/b['means'][peer]) for b in blocks));assert math.isclose(ratio,row['paired_x_'+peer][actor],rel_tol=1e-12)
 wins={peer:{row['case'] for row in rows if row['paired_x_'+peer]['mech-experiment']<1} for peer in ['roc','libdeflate']};assert len(wins['roc'])==81 and len(wins['libdeflate'])==63
 control_wins={peer:{row['case'] for row in rows if row['paired_x_'+peer]['mech-control']<1} for peer in ['roc','libdeflate']};assert len(control_wins['roc'])==81 and len(control_wins['libdeflate'])==63
 for peer,names in policy['required_peer_wins'].items():assert set(names)<=control_wins[peer]
 for peer,names in policy['required_peer_wins'].items():assert set(names)<=wins[peer] and not run['required_named_missing'][peer]
 for actor in ['mech-control','mech-experiment']:assert blob(base+'/'+actor+'.stderr').endswith(b'CLEANUP private_payload_bytes=0 live_owner_records=0\n')
 assert blob(base+'/roc.stderr').endswith(b'CLEANUP reference_input_and_output_roots_released=1\n');assert blob(base+'/libdeflate.stderr').endswith(b'CLEANUP libdeflate_compressor_and_output_released=1\n');scores.append({peer:len(names) for peer,names in wins.items()})
# Recompute every observation in both orders of all six retained screens too.
for study in ['study','umov-study']:
 for role in ['fp2','fp8','fp24']:
  screen=j(study+'/screen-v1/'+role+'-results.json');assert screen['complete'] and len(screen['runs'])==2
  for run in screen['runs']:
   base='runtime/'+Path(run['run']).name;rows=j(base+'/summary.json');assert rows==run['results'] and len(rows)==6 and not any(run['required_named_missing'].values());assert files[base+'/summary.json']['sha256']==run['summary_sha256']
   for row in rows:
    blocks=json.loads(gzip.decompress(blob(base+'/'+row['case']+'/observations.json.gz')));assert len(blocks)==96;_,fixture=byname[row['case']];values={actor:[] for actor in blocks[0]['observations']}
    for block in blocks:
     paired_blocks+=1
     for actor,items in block['observations'].items():
      for item in items:
       total+=1;assert item['case']==row['case'] and item['input_bytes']==fixture['input_bytes'] and item['prefix_bytes']==fixture['prefix_bytes'];assert not item['warmup'] and not item['profile'];assert all(item[key] for key in ['independent_inflation','input_alias_unchanged','borrowed_output_alias_unchanged']);assert math.isfinite(item['seconds']) and item['seconds']>=0
       if actor=='libdeflate':assert all(item[key]==oracle[row['case']][key] for key in ['output_sha256','raw_bytes','capacity','matches_reference_bytes'])
       else:assert item['exact_reference'] and item['raw_bytes']==fixture['raw_bytes'] and item['capacity']==fixture['capacity']
      seconds=mean(v['seconds'] for v in items);assert seconds>0 and math.isclose(seconds,block['means'][actor],rel_tol=1e-12);values[actor].extend(v['seconds'] for v in items)
    for actor,items in values.items():
     assert math.isclose(median(items),row['median_seconds'][actor],rel_tol=1e-12)
     for peer in ['roc','libdeflate']:
      ratio=math.exp(mean(math.log(b['means'][actor]/b['means'][peer]) for b in blocks));assert math.isclose(ratio,row['paired_x_'+peer][actor],rel_tol=1e-12)
recipes=read(D/'recipes.json');assert manifest['source_commit']==recipes['compiler_source_commit'];binding=j('study/source-commit-binding.json');assert binding['source_commit']==recipes['compiler_source_commit'];replays=0
for path,pin in binding['files_exact_to_commit'].items():assert files['study/source-overlay/'+path]['sha256']==pin
for mode in ['normal','checked']:
 replay=j('study/public-'+mode+'-replay-v1/reproduction.json');assert replay['source_commit']==recipes['compiler_source_commit'];assert len(replay['records'])==len(recipes['roles'])
 for row in replay['records']:
  assert row['all_three_exact'] and row['artifacts']==recipes['roles'][row['role']]['artifacts'];replays+=1
  for name,pin in row['artifacts'].items():assert files['study/public-'+mode+'-replay-v1/'+row['role']+'/frontend/'+name]['sha256']==pin
bootstrap=j('study/public-source-build-v1/reproduction.json');assert bootstrap['source_commit']==recipes['compiler_source_commit'] and len(bootstrap['records'])==2
for row in bootstrap['records']:
 assert row['all_three_exact'] and row['artifacts']==recipes['roles'][row['role']]['artifacts'];replays+=1
 for name,pin in row['artifacts'].items():assert files['study/public-source-build-v1/'+row['role']+'/frontend/'+name]['sha256']==pin
for role in recipes['roles'].values():
 for key in ['MECH_COMPACT_PHASE_BLOCK_LAYOUT','MECH_COMPACT_PHASE_REGISTER_WEIGHTS']:
  for entry in role['flags'].get(key,'').split(';'):
   if entry:
    _,path=entry.split('@',1);p=D/path;assert sha(p.read_bytes())==p.stem
probe=j('study/native-probe-v1/result.json');assert probe['complete'] and probe['all_pass'] and probe['native_calls']==256800 and probe['test_executions']==1
assert files['study/native-probe-v1/execution.log']['sha256']==probe['log_sha256'];assert files['study/native-probe-executable']['sha256']==probe['executable_sha256'];assert 'FP spill native calls: 256800' in blob('study/native-probe-v1/execution.log').decode()
observed=j('study/native-probe-v1/observations.json');assert observed['native_observations']==256800 and observed['exact_fallbacks']==40 and observed['changed_functions']==40 and len(observed['functions'])==100
public_probe=j('study/public-native-probe-v1/probe-verification.json');assert public_probe['verified'] and public_probe['source_commit']==recipes['compiler_source_commit'] and public_probe['native_calls']==256800
assert public_probe['test_source_sha256']==files['study/source-overlay/hosts/gpu/src/native_artifact/program/codegen/fp_spill_tests.rs']['sha256'];assert files['study/public-native-probe-v1/native-probe-v1/tests.log']['sha256']==public_probe['test_log_sha256'];assert files['study/public-native-probe-v1/native-probe-v1/native-probe-executable']['sha256']==public_probe['binary_sha256'];assert j('study/public-native-probe-v1/native-probe-v1/observations.json')==observed
old_probe=j('umov-study/native-probe-v1/result.json');assert old_probe['complete'] and old_probe['all_pass'] and old_probe['native_calls']==256800 and old_probe['test_executions']==1;assert files['umov-study/native-probe-v1/execution.log']['sha256']==old_probe['log_sha256']
for root in ['study','umov-study']:
 audits=j(root+'/source-checks-v1/result.json');assert len(audits)==3 and all(r['exit_code']==0 for r in audits)
 for row in audits:assert files[root+'/source-checks-v1/'+row['name']+'.log']['sha256']==row['log_sha256']
for role in recipes['roles']:
 folder='baseline-selected' if role=='control' else role;assert files['study/census/'+folder+'/receipt.json']['sha256']==recipes['roles'][role]['source_receipt_sha256']
 for sub in ['frontend','checked/frontend','capture/frontend']:
  for name,pin in recipes['roles'][role]['artifacts'].items():assert files['study/census/'+folder+'/'+sub+'/'+name]['sha256']==pin
 if role=='control':continue
 gate=j('study/census/'+role+'/linked-proof.json');path='study/'+gate['result'].split('/fp-spill-fmov-study/',1)[1];assert files[path]['sha256']==gate['sha256'];result=j(path);assert result['matches_success_observations']==162 and len(result['checked_failure_cases'])==6 and result['peak_stack_bytes']['candidate']==gate['candidate_peak_stack_bytes']<=5280
 recovery=j('study/census/'+role+'/promotion-recoveries/result.json');assert recovery['exact_recoveries']==12 and recovery['benchmark_worker_sha256']==files['study/census/'+role+'/bound/mech-worker']['sha256']
 old=blob('umov-study/census/'+role+'/frontend/program.o');new=blob('study/census/'+role+'/frontend/program.o');assert len(old)==len(new) and len(old)%4==0;changed=0
 for at in range(0,len(old),4):
  a=int.from_bytes(old[at:at+4],'little');b=int.from_bytes(new[at:at+4],'little')
  if a==b:continue
  assert a&0xfffffc00==0x4e083c00 and b==((a&0x3ff)|0x9e660000);changed+=1
 assert changed==len(j('study/census/'+role+'/scalar-move-equivalence.json')['substitutions'])
for path in files:
 if '/counts-word-reuse-v1-' not in path or not path.endswith('/counts.json'):continue
 counts=j(path)
 for sample in counts['cases'].values():assert sample['counts']['instructions']==sum(len(b['instructions'])*b['visits'] for b in sample['blocks'])
for role,instructions,loads in [('fp2',165712539,10151519),('fp8',165712570,3860214),('fp24',165714566,210)]:
 counts=j('study/census/'+role+'/counts-word-reuse-v1-475/counts.json');assert counts['object_sha256']==recipes['roles'][role]['artifacts']['program.o'];case=counts['cases']['prefix-random-1048576']['counts'];assert case['instructions']==instructions and case['stack_loads']==loads
emission=j('study/emission.json');assert emission[0]['role']=='baseline-selected' and emission[0]['all_emissions_exact'] and emission[0]['artifacts']==recipes['roles']['control']['artifacts'];assert all(row['artifacts']['program.mecb']==recipes['roles']['control']['artifacts']['program.mecb'] for row in emission)
buildroot='study/matched-builds-v1';bp=j(buildroot+'/plan.json');comparison=j(buildroot+'/comparison.json');assert files[buildroot+'/plan.json']['sha256']==comparison['plan_sha256'];assert len(comparison['observations'])==8;assert files['study/complete-build-timer.py']['sha256']==bp['timer_sha256'];assert bp['timer_source']['historical_timer_exact'];assert len(bp['orders'])==8
for phase,trial in [('warmup',comparison['warmups']),*[(f'order-{i}',r) for i,r in enumerate(comparison['observations'],1)]]:
 for actor,result in trial.items():
  folder=buildroot+'/'+phase+'/'+actor;assert j(folder+'/result.json')==result;job=bp['actors'][actor];expected=job['artifact_sha256'];assert result['generated_artifacts']==expected and all(math.isfinite(x) and x>0 for x in result['seconds'].values());assert files[folder+'/compressor']['sha256']==result['stripped_executable']['sha256'];assert len(blob(folder+'/compressor'))==result['stripped_executable']['bytes']
  generated={kind:folder+'/frontend/'+name for kind,name in [('encoder','program.o'),('metadata','metadata.json'),('bytecode','program.mecb')]} if actor.startswith('mech-') else {'encoder':folder+'/'+Path(job['reference_object']).name}
  for kind,path in generated.items():assert files[path]['sha256']==expected[kind]
for actor,stats in comparison['medians'].items():
 for stage,value in stats.items():assert math.isclose(value,median(row[actor]['seconds'][stage] for row in comparison['observations']),rel_tol=1e-12)
for peer,value in comparison['paired_ratios'].items():assert math.isclose(value,median(row['mech-spill']['seconds']['source_through_link']/row[peer]['seconds']['source_through_link'] for row in comparison['observations']),rel_tol=1e-12)
smokes=j(buildroot+'/deployment-smokes.json');assert smokes['checked_executions']==len(smokes['records'])==324
for row in smokes['records']:
 index,fixture=byname[row['case']];data=blob(f'fixtures/{index}/input');stream=blob(buildroot+'/'+row['output_file']);assert sha(data)==row['input_sha256'] and sha(stream)==row['output_sha256'] and len(stream)==row['output_bytes'];assert zlib.decompress(stream,-15)==data;expected=blob(f'fixtures/{index}/expected')[len(blob(f'fixtures/{index}/prefix')):];assert (stream==expected)==row['matches_selected_bytes'];assert row['matches_selected_bytes'] or row['actor']=='libdeflate'
for role in ['control','fp2']:
 gate=j('actors/'+role+'/linked-proof.json');assert gate['candidate_peak_stack_bytes']<=5280;recovery=j('actors/'+role+'/promotion-recoveries/result.json');assert recovery['exact_recoveries']==12 and recovery['benchmark_worker_sha256']==files['actors/'+role+'/bound/mech-worker']['sha256']
summary=read(D/'summary.json');assert summary['score']=={'roc':81,'libdeflate':63} and summary['text_bytes']==63720 and summary['stripped_executable_bytes']==210024;result={'verified':True,'archived_files':len(files),'unique_blobs':len(blobs),'full81_orders':2,'scores':scores,'paired_blocks':paired_blocks,'observations':total,'complete_build_trials':32,'standalone_executions':324,'private_native_executions':2,'private_native_calls':513600,'public_native_calls':256800,'public_native_probe_verified':True,'exact_artifact_replays':replays};(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
