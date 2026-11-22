"""Verify frozen matcher discovery evidence and recompute every primary screen."""
from pathlib import Path
from hashlib import sha256
import gzip,json,math,statistics,tarfile
HERE=Path(__file__).resolve().parent
sha=lambda b:sha256(b).hexdigest();read=lambda p:json.loads(p.read_bytes())
a=read(HERE/'archive.json');raw=(HERE/'raw.tar.gz').read_bytes();assert sha(raw)==a['archive_sha256'] and len(raw)==a['archive_bytes'];manifest_bytes=(HERE/'raw-manifest.json').read_bytes();assert sha(manifest_bytes)==a['manifest_sha256'];manifest=json.loads(manifest_bytes);files=manifest['files']
with tarfile.open(fileobj=__import__('io').BytesIO(raw),mode='r:gz') as archive:
 blobs={}
 for member in archive:
  assert member.isfile() and member.name.startswith('blobs/');pin=member.name[6:];assert len(pin)==64 and pin not in blobs;data=archive.extractfile(member).read();assert sha(data)==pin;blobs[pin]=data
assert len(blobs)==a['unique_blobs']==manifest['unique_blobs'] and len(files)==a['files']
for path,row in files.items():assert len(blobs[row['sha256']])==row['bytes'],path
blob=lambda name:blobs[files[name]['sha256']]
j=lambda name:json.loads(blob(name))
assert j('study/native-tools-validation.json')['linked_control_exact'] and j('study/native-tools-validation.json')['full_symbol_census_exact']
fixtures=j('fixtures.json');policy=j('study/screen-v1/qualification-policy-as-run.json');oracle={x['case']:x for x in j('peers/libdeflate-output-oracle.json')};tests=j('study/actual-option-tests/result.json');assert tests['complete'] and tests['all_pass'] and tests['environment']['MECH_ARM64_REUSE_I32_ARITHMETIC']=='add'
for run in tests['runs']:assert run['exit_code']==0 and files['study/actual-option-tests/'+run['name']+'.log']['sha256']==run['log_sha256']
roles=[];observations=0;blocks_checked=0;summary=read(HERE/'summary.json')
for name in sorted(files):
 if not name.startswith('study/screen-v1/') or not name.endswith('-results.json'):continue
 result=j(name);assert result['complete'] and len(result['runs'])==2 and result['plan']['blocks_per_case']==96;role=result['plan']['role'];roles.append(role);assert files['study/census/'+role+'/bound/mech-worker']['sha256']==result['plan']['candidate_worker_sha256'];assert files['study/native-tools-control-replay/mech-worker']['sha256']==result['plan']['control_worker_sha256'];assert files['tooling/compare-library.py']['sha256']==result['plan']['timer_sha256'];assert files['study/screen.py']['sha256']==result['plan']['controller_sha256'];assert files['study/screen-v1/qualification-policy-as-run.json']['sha256']==result['plan']['policy_sha256']
 gate=j('study/census/'+role+'/linked-proof.json');assert gate['candidate_peak_stack_bytes']<=5280;recovery=j('study/census/'+role+'/promotion-recoveries/result.json');assert recovery['exact_recoveries']==12 and recovery['benchmark_worker_sha256']==result['plan']['candidate_worker_sha256']
 for run in result['runs']:
  base='runtime/'+Path(run['run']).name;assert files[base+'/summary.json']['sha256']==run['summary_sha256'];rows=j(base+'/summary.json');assert rows==run['results'] and len(rows)==6;complete=j(base+'/complete.json');assert complete['all_outputs_independently_inflated'] and complete['all_input_and_output_aliases_preserved'];assert complete['balanced_blocks_per_case']==96
  for row in rows:
   samples=json.loads(gzip.decompress(blob(base+'/'+row['case']+'/observations.json.gz')));assert len(samples)==96;expected=next(f for f in fixtures if f['name']==row['case']);actor_values={actor:[] for actor in samples[0]['observations']}
   for block in samples:
    blocks_checked+=1
    for actor,values in block['observations'].items():
     assert len(values)==1
     for value in values:
      observations+=1;assert value['case']==row['case'] and value['input_bytes']==expected['input_bytes'] and value['prefix_bytes']==expected['prefix_bytes'];assert not value['warmup'] and not value['profile'];assert all(value[k] for k in ['independent_inflation','input_alias_unchanged','borrowed_output_alias_unchanged']);assert math.isfinite(value['seconds']) and value['seconds']>=0
      if actor=='libdeflate':
       assert all(value[k]==oracle[row['case']][k] for k in ['output_sha256','capacity','raw_bytes','matches_reference_bytes'])
      else:assert value['exact_reference'] and value['raw_bytes']==expected['raw_bytes'] and value['capacity']==expected['capacity']
     mean=statistics.mean(v['seconds'] for v in values);assert mean>0 and math.isclose(mean,block['means'][actor],rel_tol=1e-12);actor_values[actor].extend(v['seconds'] for v in values)
   for actor,values in actor_values.items():
    assert math.isclose(statistics.median(values),row['median_seconds'][actor],rel_tol=1e-12)
    for peer in ['roc','libdeflate']:
     ratio=math.exp(statistics.mean(math.log(b['means'][actor]/b['means'][peer]) for b in samples));assert math.isclose(ratio,row['paired_x_'+peer][actor],rel_tol=1e-12)
  for peer,names in policy['required_peer_wins'].items():
   selected={r['case'] for r in rows};wins={r['case'] for r in rows if r['paired_x_'+peer]['mech-experiment']<1};assert sorted(set(names)&selected-wins)==run['required_named_missing'][peer]
  for actor in ['mech-control','mech-experiment']:assert blob(base+'/'+actor+'.stderr').endswith(b'CLEANUP private_payload_bytes=0 live_owner_records=0\n')
  assert blob(base+'/roc.stderr').endswith(b'CLEANUP reference_input_and_output_roots_released=1\n');assert blob(base+'/libdeflate.stderr').endswith(b'CLEANUP libdeflate_compressor_and_output_released=1\n')
assert len(roles)==8
recipes=read(HERE/'recipes.json');records=[]
for mode in ['normal','checked']:
 replay=j('study/public-'+mode+'-replay-v1/reproduction.json');assert len(replay['records'])==10
 for row in replay['records']:
  assert row['all_three_exact'] and row['artifacts']==recipes['roles'][row['role']]['artifacts'];records.append((mode,row['role']))
  for artifact,pin in row['artifacts'].items():assert files['study/public-'+mode+'-replay-v1/'+row['role']+'/frontend/'+artifact]['sha256']==pin
for role in recipes['roles']:
 for key in ['MECH_COMPACT_PHASE_BLOCK_LAYOUT','MECH_COMPACT_PHASE_REGISTER_WEIGHTS']:
  for entry in recipes['roles'][role]['flags'].get(key,'').split(';'):
   if entry:
    _,relative=entry.split('@',1);path=HERE/relative;assert sha(path.read_bytes())==path.stem
effects=read(HERE/'qualified-cross-case-effects.json');previous=HERE.parent/'mechdeflate-literal-pairs-v1';prior_manifest=read(previous/'raw-manifest.json');pin=prior_manifest['files']['study/full81-v1/biased-pair-linear-results.json']['sha256']
with tarfile.open(previous/'raw.tar.gz','r:gz') as prior:
 data=prior.extractfile('blobs/'+pin).read();assert sha(data)==pin;original=json.loads(data)
for case,rows in effects['cases'].items():
 for row in rows:
  run=next(r for r in original['runs'] if r['order']==row['order']);before=next(r for r in run['results'] if r['case']==case)['median_seconds'];assert math.isclose(row['before_ms'],before['mech-control']*1000,rel_tol=1e-12);assert math.isclose(row['after_ms'],before['mech-experiment']*1000,rel_tol=1e-12);assert math.isclose(row['less_time_percent'],100*(1-before['mech-experiment']/before['mech-control']),rel_tol=1e-12)
assert not summary['new_promotion'] and not summary['full81_complete'] and summary['qualified_score']=={'roc':81,'libdeflate':63}
result={'verified':True,'archived_files':len(files),'unique_blobs':len(blobs),'runtime_variants':len(roles),'runtime_orders':16,'paired_blocks':blocks_checked,'observations':observations,'exact_artifact_replays':len(records),'full81_promotion':False};(HERE/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
