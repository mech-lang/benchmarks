"""Admit the verified Mech pi cohort from frozen evidence; no native jobs run."""
import argparse,copy,fcntl,hashlib,json,math,os,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
STUDY=Path('experiments/mech/pidigits-performance-v1')
COUNTS=Path('experiments/source-normalization/mech-v1')
PACKET=Path('experiments/mech/pidigits-publication-v1')
PARENT='pidigits:mech-pi-final-advance-signed'
LABELS={'parent':'mech-pi-advance-parent-20261022','shared-numerator':'mech-pi-shared-numerator-20261022','compact-shared':'mech-pi-compact-shared-20261022'}
KEYS={label:'pidigits:'+name for label,name in LABELS.items()}
SEALS={STUDY:'d8574a1ab7e59cab52e400dc357d91b1fd5de44b6f1c5cf973b4a249f9b9e38d',COUNTS:'7adb7576a1f7bfc5976699f1ff1e057c325b18883fd1465a9aca2ac678a2e4f9'}
TARGETS=('data/benchmarks.json','data/languages.json')
def require(ok,message):
 if not ok:raise ValueError('Mech pi admission: '+message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
def read(root,path):return json.loads((Path(root)/path).read_bytes())
def pin(root,path):return dict(path=str(path),sha256=sha((Path(root)/path).read_bytes()))
def write(path,raw):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_name(path.name+'.mech-pi.tmp')
 with tmp.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
 tmp.replace(path)
def reconcile(root=ROOT):
 root=Path(root)
 for packet,digest in SEALS.items():
  require(sha((root/packet/'seal.json').read_bytes())==digest,'frozen seal changed')
  for name,want in read(root,packet/'seal.json')['files'].items():require(sha((root/name).read_bytes())==want,'frozen artifact changed: '+name)
 run=read(root,STUDY/'run-v1/results.json');builds=read(root,STUDY/'build-v1/results.json');q=read(root,COUNTS/'qualification.json');lib=read(root,STUDY/'library-v1/results.json')
 require(run['status']=='all-complete-outputs-pass' and len(run['samples'])==35,'incomplete timing cohort')
 require(builds['status']=='all-four-subjects-built' and lib['status']=='all-five-executables-load-pinned-gmp','build/library scope differs')
 require(q['status']=='native-qualified-exact-source-subset' and q['input_programs_executed'] is False,'source counts unqualified')
 work=read(root,STUDY/'work-v2/results.json');require(work['status']=='all-real-quotient-traces-and-full-size-division-counts-pass','required work missing')
 expected='bdfa7b6c756d96492f472f97aee9cc139bee954d271eacedfd7ace5d2875f06c'
 for row in run['samples']:
  d=STUDY/'run-v1'/f"{row['round']:02d}-{row['label']}-n10000";r=read(root,d/'process.json')
  require(r['exit_status']==0 and r['quantitative_benchmark'] is True and r['reaped'] and r['group_closed'] and not r['cleanup_errors'],'open/failed timed process')
  require(row['n']==10000 and row['seconds']==r['elapsed_seconds'] and math.isfinite(row['seconds']) and row['seconds']>0,'raw timing differs')
  require(sha((root/d/'stdout.bin').read_bytes())==row['stdout_sha256']==expected and not (root/d/'stderr.bin').read_bytes(),'full output differs')
  require(r['command']==run['commands'][row['label']]+['10000'],'timed argv differs')
 for label in run['commands']:
  rows=[r for r in run['samples'] if r['label']==label];require(len(rows)==7 and {r['round'] for r in rows}==set(range(1,8)),'round coverage differs')
  require(run['summary'][label]['median_seconds']==statistics.median(r['seconds'] for r in rows),'saved median differs')
  counts=next(r['counts'] for r in work['outputs'] if r['label']==label and r['n']==10000);require(counts['tdiv']==44908 and counts['fdiv']==0,'actual division count differs')
 env=read(root,'experiments/janet/bounded-v1/plan-v1.json')['environment']
 result=dict(schema='mech-pidigits-retained-publication-cohort.v1',status='verified-retained-seven-round-cohort',full_workload_n=10000,
  compiler_source_commit=read(root,STUDY/'compiler-source.json')['compiler_commit'],compiler_sha256=builds['compiler_sha256'],
  toolchains={'mech':'0.3.6 development ('+read(root,STUDY/'compiler-source.json')['compiler_commit'][:9]+')','cranelift':'0.131.3','rustc':(root/STUDY/'library-v1/rust/stdout.bin').read_text().strip()},
  hardware={'architecture':'aarch64','scope':'Host triple of the emitted native objects; CPU model not recaptured in this cohort.'},os=(root/STUDY/'library-v1/os/stdout.bin').read_text(),
  library_pins={'gmp':{'version':'6.3.0','path':lib['gmp_path'],'sha256':lib['gmp_sha256']}},timing_boundary=run['timing_boundary'],
  manifest=str(STUDY/'compiler-source.json'),runtime_details={'compiler_build':read(root,STUDY/'compiler-source.json'),'application_build_environment':builds['environment'],'application_build_evidence':pin(root,STUDY/'build-v1/results.json')},
  source_counts=pin(root,COUNTS/'qualification.json'),timing_evidence=pin(root,STUDY/'run-v1/results.json'),work_evidence=pin(root,STUDY/'work-v2/results.json'),programs={})
 for name,pid in LABELS.items():
  label='mech-'+name;b=builds['subjects'][label];source=STUDY/'sources'/(name+'.mec');count=q['sources'][name]
  require(sha((root/source).read_bytes())==b['source_sha256']==count['source_sha256'],'source/build/count binding differs')
  require((root/STUDY/'build-v1'/label/'object/source.mec').read_bytes()==(root/source).read_bytes(),'emitted source differs')
  require(lib['subjects'][label]['executable_sha256']==b['executable_sha256'],'loader executable differs')
  observations=[]
  for row in sorted((r for r in run['samples'] if r['label']==label),key=lambda r:r['round']):
   path=STUDY/'run-v1'/f"{row['round']:02d}-{label}-n10000"/'process.json';r=read(root,path)
   observations.append(dict(seconds=row['seconds'],round=row['round'],workload_n=10000,command=r['command'],exit_status=0,raw_evidence=pin(root,path),stdout_sha256=expected,maximum_rss_bytes=r['maximum_rss_bytes'],user_cpu_seconds=r['user_cpu_seconds'],system_cpu_seconds=r['system_cpu_seconds']))
  samples=[r['seconds'] for r in observations]
  result['programs'][KEYS[name]]=dict(key=KEYS[name],id=pid,source=str(source),source_sha256=b['source_sha256'],loc=count['logical_units'],physical_loc=len((root/source).read_text().splitlines()),
   samples_seconds=samples,median_seconds=statistics.median(samples),sample_sd_seconds=statistics.stdev(samples),sample_execution_metadata=observations,
   command=run['commands'][label]+['10000'],compile_command=b['command'],binary_sha256=b['executable_sha256'],runtime_environment=env,cwd=str(root),runtime_commit=result['compiler_source_commit'],
   full_validation={'kind':'complete-output-sha256','bytes':16893,'sha256':expected,'all_seven_samples_verified':True})
 return result

def bound_authorship(data,profile,root=ROOT):
 root=Path(root);name=next((n for n,k in KEYS.items() if profile['key']==k),None);require(name is not None,'unknown authorship profile')
 parent={**data.get('program_inventory',{}),**data['programs']}[PARENT];manifest=read(root,STUDY/'source-manifest.json')
 source=STUDY/'sources'/(name+'.mec');digest=sha((root/source).read_bytes());require(profile['files']==[digest] and profile.get('original_program_key')==PARENT,'authorship source binding differs')
 detail=profile.get('source_provenance_record',{});admission=dict(path=str(PACKET/'cohort.json'),sha256=sha(encoded(reconcile(root))))
 require(detail.get('source_sha256')==digest and detail.get('original_program_key')==PARENT and detail.get('admission')==admission,'authorship admission binding differs')
 if name=='parent':require(profile['files']==parent['files'],'fresh parent source differs');return copy.deepcopy(parent['authorship'])
 context=manifest['local_candidates'][name];require(context['sha256']==digest and context['model_family']=='GPT-6','local source authorship context differs')
 old=parent['authorship'];out=copy.deepcopy(old)
 out.update(kind='ai-adapted',label='AI adapted · retained local predecessor',source_sha256=[digest],
  retained_sources=[dict(source_sha256=digest,url='https://github.com/mech-lang/benchmarks/blob/8d8d2b8dce1dcc3ee45b86f8499b1f719b07fc6b/'+str(source))],parent_programs=[PARENT],
  parent_sources=[dict(program_key=PARENT,relationship='local predecessor',**copy.deepcopy(ref)) for ref in old.get('retained_sources',[])],
  ai=dict(tool='OpenAI Codex',models=[],model_family='Codex GPT-6',exact_model=None,status='family-identified-exact-model-unverified',matched_source_files=[digest],total_source_files=1,evidence=[pin(root,STUDY/'source-manifest.json'),admission]),
  local_change_license=dict(status='suite-license',id='Apache-2.0',evidence='LICENSE',scope='New local changes only; inherited terms remain unresolved.'),evidence=[str(STUDY/'source-manifest.json'),str(COUNTS/'qualification.json')])
 return out

def append_catalog(before,languages,cohort,root=ROOT):
 root=Path(root);require(cohort==reconcile(root),'cohort drift from frozen evidence');data=copy.deepcopy(before);meta=copy.deepcopy(languages)
 require('mech_pidigits_20261022_audit' not in data,'cohort already admitted')
 bench=next(b for b in data['benchmarks'] if b['key']=='pidigits');group=next(g for g in bench['groups'] if g['language']=='mech');parent=before['programs'][PARENT]
 require(set(cohort['programs'])==set(KEYS.values()) and len(parent['files'])==1,'candidate inventory differs')
 report=str(PACKET/'cohort.json');report_hash=sha(encoded(cohort))
 for name,key in KEYS.items():
  require(key not in data['programs'] and key not in data['program_inventory'],'duplicate candidate identity')
  r=cohort['programs'][key];digest=r['source_sha256'];code=(root/r['source']).read_text()
  require(sha(code.encode())==digest and type(r['loc']) is int and r['loc']>0,'candidate source/count differs')
  require(r['median_seconds']>=bench['baseline_seconds'] and r['loc']>=bench['baseline_loc'],'new global minimum needs normalization review')
  source=dict(name=Path(r['source']).name,path=r['source'],sha256=digest,code=code,archive_path=r['source'])
  if digest in data['files']:require(data['files'][digest]['code']==code,'source collision')
  else:data['files'][digest]=source
  row=dict(key=key,id=r['id'],language='mech',benchmark='pidigits',loc=r['loc'],loc_metric='native-logical-units',physical_loc=r['physical_loc'],files=[digest],
   file_roles={digest:dict(role='application',source_path=r['source'],normalized_loc=r['loc'],physical_loc=r['physical_loc'],included_in_application_loc=True)},
   seconds=r['median_seconds'],samples=r['samples_seconds'],timing_sd=r['sample_sd_seconds'],x=r['loc']/bench['baseline_loc'],y=r['median_seconds']/bench['baseline_seconds'],
   report=report,report_sha256=report_hash,source_report=str(STUDY/'build-v1/results.json'),loc_report=str(COUNTS/'qualification.json'),command=r['command'],compile_command=r['compile_command'],
   sample_execution_metadata=r['sample_execution_metadata'],sample_details=[dict(seconds=s['seconds'],maximum_rss_bytes=s['maximum_rss_bytes']) for s in r['sample_execution_metadata']],
   retained_source_revision='c95f900435aca5ae51030eabeffae2e5dc9a2fc2' if name=='parent' else '8d8d2b8dce1dcc3ee45b86f8499b1f719b07fc6b',binary_sha256=r['binary_sha256'],runtime_environment=r['runtime_environment'],cwd=r['cwd'],execution_mode='aot',runtime_policy='Native AOT · Cranelift 0.131.3 · complete fresh process',measurement_status='measured',
   timing_boundary=cohort['timing_boundary'],timing_summary='Fresh process: startup, complete computation, output and shutdown.',native_observations=7,timing_alias_of=None,
   formatted_loc=None,formatted_x=None,formatted_loc_status='pending',formatted_loc_complete=False,formatted_loc_evidence={},eligible_for_chart=True,
   required_work_validated=True,full_output_validation=r['full_validation'],original_program_key=PARENT,local_adaptation=name!='parent',distinct_optimization_claimed=name!='parent',
   source_url='https://github.com/mech-lang/benchmarks/blob/main/'+r['source'],source_link_label='Exact retained source',source_provenance='Retained Mech pi spigot; ordinary bigint operations, both actual divisions preserved.',
   algorithm=copy.deepcopy(parent['algorithm']),source_provenance_record=dict(kind='retained-source-fresh-cohort' if name=='parent' else 'suite-authored-optimization',original_program_key=PARENT,source_sha256=digest,admission=dict(path=report,sha256=report_hash)),
   measured_backend=dict(key='native-aot',execution='aot',label='Native AOT · Cranelift',verified=True,confidence=dict(historical_platform_verified=True,historical_execution_verified=True,historical_executable_bytes_verified=True),
    evidence=dict(verified=True,report=report,report_sha256=report_hash,source_sha256=[digest],command=r['command'],actual_native_build_command=r['compile_command'],measurement_selector='/programs/'+key,
     actual_sample_array=r['samples_seconds'],runtime_receipt=dict(verified=True,report=report,report_sha256=report_hash,field='/toolchains/mech',value=cohort['toolchains']['mech'],value_encoding='literal-saved-string'))))
  row['authorship']=bound_authorship(data,row,root);row['publication_record']=copy.deepcopy(row)
  data['programs'][key]=row;data['program_inventory'][key]=copy.deepcopy(row);group['programs'].append(key)
 candidates=[data['programs'][k] for k in group['programs']]
 group['fast']=min(candidates,key=lambda r:(r['seconds'],r['loc'],r['key']))['key'];group['small']=min(candidates,key=lambda r:(r['loc'],r['seconds'],r['key']))['key']
 for summary in data['reference_summary']:
  if summary['lang']=='mech':
   for kind in ('fast','small'):
    rows=[data['programs'][g[kind]] for b in data['benchmarks'] for g in b['groups'] if g['language']=='mech']
    summary[kind]={axis:statistics.geometric_mean(r[axis] for r in rows) for axis in ('x','y')}
 meta['languages']['mech']['displayed_program_count']=sum(r['language']=='mech' for r in data['programs'].values())
 paths=[report,str(STUDY/'build-v1/results.json'),str(STUDY/'source-manifest.json'),str(COUNTS/'qualification.json'),str(STUDY/'work-v2/results.json')]+[r['source'] for r in cohort['programs'].values()]
 for path in paths:require(data['archive_paths'].get(path,path)==path,'archive mapping conflict');data['archive_paths'][path]=path
 data['mech_pidigits_20261022_audit']=dict(schema='mech-pidigits-additive-admission.v1',programs=list(KEYS.values()),report=report,report_sha256=report_hash,source_count_proof=pin(root,COUNTS/'qualification.json'),native_observations=21,native_jobs_started_by_admission=0,historical_profiles_changed=False,baselines_changed=False,fast=group['fast'],small=group['small'])
 for pool in ('programs','program_inventory','files','archive_paths'):require(all(data[pool][k]==v for k,v in before[pool].items()),'historical '+pool+' changed')
 return data,meta

def apply_targets(root,originals,prepared,fail_after=None):
 replaced=[]
 try:
  for i,name in enumerate(TARGETS,1):
   require((root/name).read_bytes()==originals[name],'canonical input drift: '+name)
   write(root/name,prepared[name]);replaced.append(name)
   if fail_after==i:raise RuntimeError('injected transaction failure')
 except BaseException:
  for name in reversed(replaced):
   require((root/name).read_bytes()==prepared[name],'externally changed output preserved during rollback: '+name)
   write(root/name,originals[name])
  raise

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('prepare','apply'));p.add_argument('--expected-preview-sha256');a=p.parse_args();out=ROOT/PACKET;out.mkdir(exist_ok=True)
 with Path('/private/tmp/mech-clbg-timing.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
  originals={n:(ROOT/n).read_bytes() for n in TARGETS};cohort=reconcile();data,languages=append_catalog(json.loads(originals[TARGETS[0]]),json.loads(originals[TARGETS[1]]),cohort)
  prepared={TARGETS[0]:encoded(data),TARGETS[1]:encoded(languages)}
  preview=dict(schema='mech-pi-publication-preview.v1',inputs={n:sha(v) for n,v in originals.items()},outputs={n:sha(v) for n,v in prepared.items()},cohort_sha256=sha(encoded(cohort)),programs=list(KEYS.values()),fast=data['mech_pidigits_20261022_audit']['fast'],native_jobs_started=0)
  if a.mode=='prepare':write(out/'cohort.json',encoded(cohort));write(out/'preview.json',encoded(preview));print(json.dumps(preview));print('preview_sha256='+sha(encoded(preview)))
  else:
   require(a.expected_preview_sha256==sha((out/'preview.json').read_bytes()),'explicit reviewed preview hash required')
   require(read(ROOT,PACKET/'preview.json')==preview and (out/'cohort.json').read_bytes()==encoded(cohort),'preview no longer reproduces')
   apply_targets(ROOT,originals,prepared);write(out/'SUCCESS.json',encoded(dict(preview=pin(ROOT,PACKET/'preview.json'),before=preview['inputs'],after=preview['outputs'],historical_profiles_changed=False,native_jobs_started=0)));print('Admitted three verified Mech cohorts; historical profiles and fixed baselines preserved.')
if __name__=='__main__':main()
