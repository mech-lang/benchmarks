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
blob=lambda name:blobs[files[name]['sha256']];j=lambda name:json.loads(blob(name));fixtures=j('fixtures.json');byname={row['name']:(index,row) for index,row in enumerate(fixtures)};policy=j('study/full81-v1/qualification-policy-as-run.json');oracle={row['case']:row for row in j('pinned-peers/libdeflate-output-oracle.json')};full=j('study/full81-v1/reuse-byte-all-sqrt-results.json');assert full['complete'] and len(full['runs'])==2;plan=full['plan'];assert plan['blocks_per_case']==96;assert files['actors/control/bound/mech-worker']['sha256']==plan['control_worker_sha256'];assert files['actors/reuse-byte-all-sqrt/bound/mech-worker']['sha256']==plan['candidate_worker_sha256'];assert files['compare-library.py']['sha256']==plan['timer_sha256'];assert files['study/full81.py']['sha256']==plan['controller_sha256'];total=0;paired_blocks=0;scores=[]
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
probe=j('study/native-probe-v1/result.json');assert probe['complete'] and probe['all_pass'] and probe['native_calls']==1038800 and probe['native_test_executions']==4
for row in probe['runs']:
 name='study/'+row['log'];assert files[name]['sha256']==row['log_sha256'];assert '2 passed; 0 failed' in blob(name).decode()
for group in ['fixed','fallback']:
 left=j('study/native-probe-v1/mode-0/'+group+'.json');right=j('study/native-probe-v1/mode-1/'+group+'.json');a={r['name']:r for r in left['functions']};b={r['name']:r for r in right['functions']};assert a.keys()==b.keys()
 for key,x in a.items():
  if (x['form'] in ['Immediate','BinaryConstant'] and x['amount']%32==0) or x['form'] in ['Parameter','Variable']:assert x['body']==b[key]['body']
public_probe=j('study/public-native-probe-v1/probe-verification.json');assert public_probe['verified'] and public_probe['source_commit']==recipes['compiler_source_commit'] and public_probe['native_calls']==1038800 and public_probe['native_test_executions']==4
assert public_probe['test_source_sha256']==files['study/source-overlay/hosts/gpu/src/native_artifact/program/codegen/low_word_tests.rs']['sha256']
for row in public_probe['runs']:
 name='study/public-native-probe-v1/'+row['log'];assert files[name]['sha256']==row['log_sha256'] and '2 passed; 0 failed' in blob(name).decode()
emission=j('study/emission.json');assert emission[0]['hook_disabled_exact'] and emission[0]['artifacts']==recipes['roles']['control']['artifacts'];assert all(row['artifacts']['program.mecb']==recipes['roles']['control']['artifacts']['program.mecb'] for row in emission)
buildroot='study/matched-builds-v1';bp=j(buildroot+'/plan.json');comparison=j(buildroot+'/comparison.json');assert files[buildroot+'/plan.json']['sha256']==comparison['plan_sha256'];assert len(comparison['observations'])==8;assert files['study/complete-build-timer.py']['sha256']==bp['timer_sha256'];assert bp['timer_source']['historical_timer_exact'];assert len(bp['orders'])==8
for phase,trial in [('warmup',comparison['warmups']),*[(f'order-{i}',r) for i,r in enumerate(comparison['observations'],1)]]:
 for actor,result in trial.items():
  folder=buildroot+'/'+phase+'/'+actor;assert j(folder+'/result.json')==result;job=bp['actors'][actor];expected=job['artifact_sha256'];assert result['generated_artifacts']==expected and all(math.isfinite(x) and x>0 for x in result['seconds'].values());assert files[folder+'/compressor']['sha256']==result['stripped_executable']['sha256'];assert len(blob(folder+'/compressor'))==result['stripped_executable']['bytes']
  generated={kind:folder+'/frontend/'+name for kind,name in [('encoder','program.o'),('metadata','metadata.json'),('bytecode','program.mecb')]} if actor.startswith('mech-') else {'encoder':folder+'/'+Path(job['reference_object']).name}
  for kind,path in generated.items():assert files[path]['sha256']==expected[kind]
for actor,stats in comparison['medians'].items():
 for stage,value in stats.items():assert math.isclose(value,median(row[actor]['seconds'][stage] for row in comparison['observations']),rel_tol=1e-12)
for peer,value in comparison['paired_ratios'].items():assert math.isclose(value,median(row['mech-reuse']['seconds']['source_through_link']/row[peer]['seconds']['source_through_link'] for row in comparison['observations']),rel_tol=1e-12)
smokes=j(buildroot+'/deployment-smokes.json');assert smokes['checked_executions']==len(smokes['records'])==324
for row in smokes['records']:
 index,fixture=byname[row['case']];data=blob(f'fixtures/{index}/input');stream=blob(buildroot+'/'+row['output_file']);assert sha(data)==row['input_sha256'] and sha(stream)==row['output_sha256'] and len(stream)==row['output_bytes'];assert zlib.decompress(stream,-15)==data;expected=blob(f'fixtures/{index}/expected')[len(blob(f'fixtures/{index}/prefix')):];assert (stream==expected)==row['matches_selected_bytes'];assert row['matches_selected_bytes'] or row['actor']=='libdeflate'
for role in ['control','reuse-byte-all-sqrt']:
 gate=j('actors/'+role+'/linked-proof.json');assert gate['candidate_peak_stack_bytes']<=5280;recovery=j('actors/'+role+'/promotion-recoveries/result.json');assert recovery['exact_recoveries']==12 and recovery['benchmark_worker_sha256']==files['actors/'+role+'/bound/mech-worker']['sha256']
summary=read(D/'summary.json');assert summary['score']=={'roc':81,'libdeflate':63} and summary['text_bytes']==63992 and summary['stripped_executable_bytes']==210024;result={'verified':True,'archived_files':len(files),'unique_blobs':len(blobs),'full81_orders':2,'scores':scores,'paired_blocks':paired_blocks,'observations':total,'complete_build_trials':32,'standalone_executions':324,'shift_jit_test_executions':4,'shift_native_calls':1038800,'public_native_probe_verified':True,'exact_artifact_replays':replays};(D/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
