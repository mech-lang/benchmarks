"""Add frozen Mech record-runtime cohorts without changing historical observations."""
import argparse,copy,fcntl,hashlib,json,math,os,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
BASE=Path('experiments/mech/revcomp-streaming-v1');STUDY=Path('experiments/mech/revcomp-buffer-reuse-v1');PACKET=Path('experiments/mech/revcomp-publication-v1')
CLI=Path('experiments/mech/pidigits-performance-v1')
PARENT='revcomp:mech-revcomp-optimized';SOURCE='archive/workloads/revcomp/revcomp.mec'
LABELS={'original4':'mech-revcomp-parent-20261022','compacted4':'mech-revcomp-compacted-20261022','reuse4':'mech-revcomp-reused-4-20261022','reuse8':'mech-revcomp-reused-8-20261022'}
KEYS={name:'revcomp:'+value for name,value in LABELS.items()}
SEALS={CLI:'d8574a1ab7e59cab52e400dc357d91b1fd5de44b6f1c5cf973b4a249f9b9e38d',BASE:'d87a7dbd44661ecc0ccd5d376b7b86fdcf010b2f4f431b510e97c385b8967293',STUDY:'1c5da776c225eb5506992ded7f90475df2c892ac7552ac1bf290cb5092a9f215'}
SOURCE_SHA='7ca0b4ff377cc51f9104c4dd5c78a2db8c0bee5ec4690ab4f0685706fc46695d'
OUTPUT_SHA='e5730d4fd55c464f276e5c6062c80f46e0a735281de15d8c957e2731a9baf70e';FULL_BYTES=254166745
TARGETS=('data/benchmarks.json','data/languages.json')
def require(ok,message):
 if not ok:raise ValueError('Mech record admission: '+message)
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(value):return (json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
def read(root,path):return json.loads((Path(root)/path).read_bytes())
def pin(root,path):return dict(path=str(path),sha256=sha((Path(root)/path).read_bytes()))
def write(path,raw):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temp=path.with_name(path.name+'.mech-record.tmp')
 with temp.open('xb') as stream:stream.write(raw);stream.flush();os.fsync(stream.fileno())
 temp.replace(path)
def reconcile(root=ROOT):
 root=Path(root)
 for folder,digest in SEALS.items():
  require(sha((root/folder/'seal.json').read_bytes())==digest,'frozen seal changed')
  for name,want in read(root,folder/'seal.json')['files'].items():require(sha((root/name).read_bytes())==want,'frozen artifact changed: '+name)
 run=read(root,STUDY/'run-v1/results.json');build=read(root,STUDY/'build-v1/results.json');refine=read(root,STUDY/'test-refinement-v2/results.json');comp=read(root,STUDY/'compiler.json');oldcomp=read(root,BASE/'compiler.json')
 compiler_recipe=read(root,CLI/'compiler-source.json');cli_build=read(root,CLI/'build-v1/results.json')
 require(cli_build['compiler_sha256']==oldcomp['compiler_cli_sha256'] and compiler_recipe['compiler_commit']==oldcomp['compiler_cli_commit'],'emitter recipe identity differs')
 generator_path=Path('experiments/janet/knucleotide-bytes-v1/input-generation-v1');generator=read(root,generator_path/'input.json');generator_process=read(root,generator_path/'process.json')
 require(generator['sha256']==run['input']['sha256'] and generator['bytes']==FULL_BYTES and generator_process['exit_status']==0,'input generator identity differs')
 require(sha((root/generator['generator']).read_bytes())==generator['generator_sha256'],'input generator source differs')
 require(run['status']=='all-35-full-size-outputs-pass' and len(run['samples'])==35 and run['official_input_all_five_pass'],'incomplete full cohort')
 require(build['status']=='tests-and-build-pass-identical-native-object' and refine['byte_identical_measured_executable'] and refine['rebuilt_binary_sha256']==build['binary_sha256'],'build/refined executable differs')
 require('10 passed; 0 failed' in (root/STUDY/'test-refinement-v1/tests/stdout.bin').read_text(),'runtime tests missing')
 require(sha((root/SOURCE).read_bytes())==SOURCE_SHA and len((root/SOURCE).read_text().splitlines())==7,'application source/count changed')
 for name,digest in read(root,BASE/'candidate-build-v1/results.json')['mech']['unchanged_emitted_inputs'].items():
  require(sha((root/STUDY/'build-v1/source-and-object'/name).read_bytes())==digest,'native object or emitted inputs changed')
 for folder in (BASE,STUDY):
  q=read(root,folder/'qualification-v1/results.json');require(q['status']=='all-61-parent-candidate-behaviors-identical' and len(q['cases'])==61 and not q['new_regressions'],'bounded qualification differs')
  require(len(q['existing_source_contract_differences'])==11,'source limitations changed')
  for row in q['cases']:
   require(row['parent']==row['candidate'],'bounded behavior regression')
   for label in ('parent','candidate'):
    d=folder/'qualification-v1'/f"{label}-{row['case']}";r=read(root,d/'process.json')
    actual=dict(exit_status=r['exit_status'],stdout_sha256=sha((root/d/'stdout.bin').read_bytes()),stderr_sha256=sha((root/d/'stderr.bin').read_bytes()))
    require(actual==row[label],'bounded raw capture changed')
  for p in (root/folder).rglob('process.json'):
   r=json.loads(p.read_bytes());require(r['reaped'] and r['group_closed'] and not r['cleanup_errors'],'owned process not closed')
 expected=(root/'archive/workloads/revcomp/inputs/revcomp-output-1000.txt').read_bytes()
 for label in run['variants']:
  d=STUDY/'run-v1'/f'official-{label}';r=read(root,d/'process.json')
  require(r['exit_status']==0 and (root/d/'stdout.bin').read_bytes()==expected and not (root/d/'stderr.bin').read_bytes(),'official output changed')
 for row in run['samples']:
  d=STUDY/'run-v1'/f"{row['round']:02d}-{row['label']}";r=read(root,d/'process.json');o=read(root,d/'stdout-omitted.json')
  require(r['exit_status']==0 and r['quantitative_benchmark'] and row['seconds']==r['elapsed_seconds'] and math.isfinite(row['seconds']) and row['seconds']>0,'raw timing changed')
  require(o['verified_complete'] and o['reaped'] and o['group_closed'] and o['bytes']==FULL_BYTES and o['sha256']==OUTPUT_SHA and not (root/d/'stderr.bin').read_bytes(),'full-output receipt changed')
  require(r['command']==run['variants'][row['label']]['command'],'timed command changed')
 for label in run['variants']:
  rows=[r for r in run['samples'] if r['label']==label]
  require(len(rows)==7 and {r['round'] for r in rows}==set(range(1,8)) and run['summary'][label]['median_seconds']==statistics.median(r['seconds'] for r in rows),'round coverage or median changed')
 parent=read(root,BASE/'baseline-build-v1/results.json');compacted=read(root,BASE/'candidate-build-v1/results.json')
 specs={
  'original4':(BASE/'baseline-build-v1/results.json',parent['command'],parent['binary_sha256'],'6de19875e2266f39c93712800c400672a44b98c9',BASE/'compiler-snapshot/runtime-parent.rs'),
  'compacted4':(BASE/'candidate-build-v1/results.json',compacted['mech']['command'],compacted['mech']['binary_sha256'],'6634f1f4d59c0a2eebee44065f236f8647703464',BASE/'compiler-snapshot/runtime-candidate.rs'),
  'reuse4':(STUDY/'build-v1/results.json',build['build_command'],build['binary_sha256'],comp['candidate_runtime_commit'],STUDY/'test-refinement-v1/runtime-candidate.rs'),
  'reuse8':(STUDY/'build-v1/results.json',build['build_command'],build['binary_sha256'],comp['candidate_runtime_commit'],STUDY/'test-refinement-v1/runtime-candidate.rs')}
 result=dict(schema='mech-record-runtime-publication-cohort.v1',status='verified-retained-seven-round-cohort',full_workload_n=25000000,
  compiler_source_commit=oldcomp['compiler_cli_commit'],compiler_sha256=oldcomp['compiler_cli_sha256'],toolchains=dict(cranelift='0.131.3',rustc=oldcomp['rustc_version']),hardware=oldcomp['hardware'],os=oldcomp['os_version'],
  input={**run['input'],'generator':{**generator,'source_evidence':pin(root,generator['generator']),'receipt':pin(root,generator_path/'input.json'),'command':generator_process['command']},'generated_bases':250000000},timing_boundary=run['timing_boundary'],power={'policy':'Default; AC power; low power mode disabled','first_swap':run['telemetry'][0]['swap'],'last_swap':run['telemetry'][-1]['swap'],'temperature_frequency_trace':False},
  library_pins={'gmp':{'version':'6.3.0','path':compiler_recipe['installed_gmp'],'sha256':read(root,CLI/'library-v1/results.json')['gmp_sha256'],'scope':'Installed build dependency pin from the frozen emitter study; no new revcomp loader trace.'}},
  runtime_details={'compiler_build':compiler_recipe,'compiler_build_evidence':pin(root,CLI/'compiler-source.json'),'application_build_environment':build['environment'],'compiler_cli':pin(root,BASE/'compiler.json'),'runtime_build':pin(root,STUDY/'compiler.json'),'test_refinement':pin(root,STUDY/'test-refinement-v2/results.json'),'reproduction':'Restore the emitter CLI at its source commit, then the per-program runtime checkout commit before its saved build command. Adapt recorded absolute paths and restore the input/toolchain caches.'},
  source_count={'policy':'Inherited unchanged-source count; not newly qualified logical units or native formatted LOC','loc':7,'source_sha256':SOURCE_SHA},
  correctness_scope='Official generated workload; eleven pre-existing broader FASTA source limitations retained explicitly.',bounded_source_limitations=read(root,STUDY/'qualification-v1/results.json')['existing_source_contract_differences'],programs={})
 for label,key in KEYS.items():
  receipt,command,binary,commit,runtime_source=specs[label];observations=[]
  require(run['pins'][run['variants'][label]['command'][0]]==binary,'executable pin differs')
  for row in sorted((r for r in run['samples'] if r['label']==label),key=lambda r:r['round']):
   path=STUDY/'run-v1'/f"{row['round']:02d}-{label}"/'process.json';r=read(root,path)
   observations.append(dict(seconds=row['seconds'],round=row['round'],workload_n=25000000,command=r['command'],exit_status=0,stdin=run['input'],raw_evidence=pin(root,path),stdout_bytes=FULL_BYTES,stdout_sha256=OUTPUT_SHA,maximum_rss_bytes=r['maximum_rss_bytes'],user_cpu_seconds=r['user_cpu_seconds'],system_cpu_seconds=r['system_cpu_seconds']))
  samples=[r['seconds'] for r in observations]
  result['programs'][key]=dict(key=key,id=LABELS[label],source=SOURCE,source_sha256=SOURCE_SHA,loc=7,samples_seconds=samples,median_seconds=statistics.median(samples),sample_sd_seconds=statistics.stdev(samples),sample_execution_metadata=observations,
   command=run['variants'][label]['command'],compile_command=command,binary_sha256=binary,runtime_environment={**run['runtime_environment'],'MECH_SEQUENCE_PARTITIONS':str(run['variants'][label]['workers'])},cwd='/private/tmp/mech-benchmark-publication',runtime_commit=commit,runtime_source=pin(root,runtime_source),build_evidence=pin(root,receipt),
   runtime_version='Mech 0.3.6 development (emitter '+oldcomp['compiler_cli_commit'][:9]+', runtime '+commit[:9]+')',
   full_validation=dict(kind='complete-output-sha256-receipt',bytes=FULL_BYTES,sha256=OUTPUT_SHA,all_seven_samples_verified=True,full_output_omitted_after_hash=True))
 return result

def bound_authorship(data,profile,root=ROOT):
 require(profile['key'] in KEYS.values() and profile['files']==[SOURCE_SHA],'authorship source identity changed')
 parent=data['programs'][PARENT];require(parent['files']==profile['files'],'parent source identity changed')
 return copy.deepcopy(parent['authorship'])

def append_catalog(before,languages,cohort,root=ROOT):
 root=Path(root);require(cohort==reconcile(root),'cohort drift from frozen evidence');require('mech_revcomp_20261022_audit' not in before,'cohort already admitted')
 data=copy.deepcopy(before);meta=copy.deepcopy(languages);parent=before['programs'][PARENT]
 require(parent['files']==[SOURCE_SHA] and parent['loc']==7,'inherited source boundary/count changed')
 bench=next(b for b in data['benchmarks'] if b['key']=='revcomp');group=next(g for g in bench['groups'] if g['language']=='mech');report=str(PACKET/'cohort.json');report_hash=sha(encoded(cohort))
 for label,key in KEYS.items():
  require(key not in data['programs'] and key not in data['program_inventory'],'duplicate candidate identity');r=cohort['programs'][key]
  require(r['median_seconds']>=bench['baseline_seconds'] and r['loc']>=bench['baseline_loc'],'new fixed minimum needs review')
  row=copy.deepcopy(parent)
  for name in ('publication_record','prior_runtime_metadata','source_alias_of','aliased_sample_source'):row.pop(name,None)
  row.update(key=key,id=r['id'],seconds=r['median_seconds'],samples=r['samples_seconds'],timing_sd=r['sample_sd_seconds'],x=7/bench['baseline_loc'],y=r['median_seconds']/bench['baseline_seconds'],
   report=report,report_sha256=report_hash,source_report=r['build_evidence']['path'],command=r['command'],compile_command=r['compile_command'],sample_execution_metadata=r['sample_execution_metadata'],sample_details=[dict(seconds=s['seconds'],maximum_rss_bytes=s['maximum_rss_bytes']) for s in r['sample_execution_metadata']],
   retained_source_revision='c95f900435aca5ae51030eabeffae2e5dc9a2fc2',binary_sha256=r['binary_sha256'],runtime_environment=r['runtime_environment'],cwd=r['cwd'],execution_mode='aot',runtime_policy='Native AOT · Cranelift 0.131.3 · runtime '+r['runtime_commit'][:9]+' · '+str(4 if label.endswith('4') else 8)+' partitions',measurement_status='measured',
   timing_boundary=cohort['timing_boundary'],timing_summary='Fresh process: startup, input, complete native work, all output and shutdown.',native_observations=7,timing_alias_of=None,eligible_for_chart=True,
   required_work_validated=True,full_output_validation=r['full_validation'],original_program_key=PARENT,local_adaptation=False,distinct_optimization_claimed=label!='original4',optimization_scope='runtime-only; application bytes unchanged',physical_loc=7,
   source_url='https://github.com/mech-lang/benchmarks/blob/c95f900435aca5ae51030eabeffae2e5dc9a2fc2/'+SOURCE,source_link_label='Exact retained source',source_provenance='Unchanged Mech application; separately measured runtime and worker policy.',
   source_provenance_record=dict(kind='retained-source-new-runtime-cohort',original_program_key=PARENT,source_sha256=SOURCE_SHA,runtime_commit=r['runtime_commit'],admission=dict(path=report,sha256=report_hash)),
   measured_backend=dict(key='native-aot',execution='aot',label='Native AOT · Cranelift',verified=True,confidence=dict(historical_platform_verified=True,historical_execution_verified=True,historical_executable_bytes_verified=True),
    evidence=dict(verified=True,report=report,report_sha256=report_hash,source_sha256=[SOURCE_SHA],command=r['command'],actual_native_build_command=r['compile_command'],measurement_selector='/programs/'+key,actual_sample_array=r['samples_seconds'],runtime_receipt=dict(verified=True,report=report,report_sha256=report_hash,field='/programs/'+key+'/runtime_version',value=r['runtime_version'],value_encoding='literal-saved-string'))))
  row['algorithm']['evidence']=[dict(path=SOURCE,sha256=SOURCE_SHA),r['runtime_source'],r['build_evidence']]
  row['algorithm']['extended_source_limitations']=cohort['bounded_source_limitations']
  row['authorship']=bound_authorship(data,row,root);row['publication_record']=copy.deepcopy(row);data['programs'][key]=row;data['program_inventory'][key]=copy.deepcopy(row);group['programs'].append(key)
 rows=[data['programs'][k] for k in group['programs']];group['fast']=min(rows,key=lambda r:(r['seconds'],r['loc'],r['key']))['key'];group['small']=min(rows,key=lambda r:(r['loc'],r['seconds'],r['key']))['key']
 for summary in data['reference_summary']:
  if summary['lang']=='mech':
   for kind in ('fast','small'):
    selected=[data['programs'][g[kind]] for b in data['benchmarks'] for g in b['groups'] if g['language']=='mech'];summary[kind]={axis:statistics.geometric_mean(r[axis] for r in selected) for axis in ('x','y')}
 meta['languages']['mech']['displayed_program_count']=sum(r['language']=='mech' for r in data['programs'].values())
 for path in [report,SOURCE,str(BASE/'compiler.json'),str(STUDY/'compiler.json'),str(STUDY/'run-v1/results.json')]:
  require(data['archive_paths'].get(path,path)==path,'archive mapping conflict');data['archive_paths'][path]=path
 data['mech_revcomp_20261022_audit']=dict(schema='mech-record-runtime-additive-admission.v1',programs=list(KEYS.values()),report=report,report_sha256=report_hash,native_observations=28,native_jobs_started_by_admission=0,historical_profiles_changed=False,baselines_changed=False,source_bytes_changed=False,source_counts_changed=False,authorship_changed=False,fast=group['fast'],small=group['small'])
 for pool in ('programs','program_inventory','files','archive_paths'):require(all(data[pool][k]==v for k,v in before[pool].items()),'historical '+pool+' changed')
 return data,meta

def apply_targets(root,originals,prepared,fail_after=None):
 replaced=[]
 try:
  for i,name in enumerate(TARGETS,1):
   require((root/name).read_bytes()==originals[name],'canonical input drift: '+name);write(root/name,prepared[name]);replaced.append(name)
   if fail_after==i:raise RuntimeError('injected transaction failure')
 except BaseException:
  for name in reversed(replaced):
   require((root/name).read_bytes()==prepared[name],'externally changed output preserved during rollback: '+name);write(root/name,originals[name])
  raise

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('prepare','apply'));p.add_argument('--expected-preview-sha256');a=p.parse_args();out=ROOT/PACKET;out.mkdir(exist_ok=True)
 with Path('/private/tmp/mech-clbg-timing.lock').open('a+') as lock:
  fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);originals={n:(ROOT/n).read_bytes() for n in TARGETS};cohort=reconcile();data,languages=append_catalog(json.loads(originals[TARGETS[0]]),json.loads(originals[TARGETS[1]]),cohort);prepared={TARGETS[0]:encoded(data),TARGETS[1]:encoded(languages)}
  preview=dict(schema='mech-record-publication-preview.v1',inputs={n:sha(v) for n,v in originals.items()},outputs={n:sha(v) for n,v in prepared.items()},cohort_sha256=sha(encoded(cohort)),programs=list(KEYS.values()),fast=data['mech_revcomp_20261022_audit']['fast'],native_jobs_started=0)
  if a.mode=='prepare':write(out/'cohort.json',encoded(cohort));write(out/'preview.json',encoded(preview));print(json.dumps(preview));print('preview_sha256='+sha(encoded(preview)))
  else:
   require(a.expected_preview_sha256==sha((out/'preview.json').read_bytes()),'explicit reviewed preview hash required');require(read(ROOT,PACKET/'preview.json')==preview and (out/'cohort.json').read_bytes()==encoded(cohort),'preview no longer reproduces');apply_targets(ROOT,originals,prepared);write(out/'SUCCESS.json',encoded(dict(preview=pin(ROOT,PACKET/'preview.json'),before=preview['inputs'],after=preview['outputs'],historical_profiles_changed=False,native_jobs_started=0)));print('Admitted four verified Mech runtime cohorts; historical sources, counts, authorship, samples and fixed baselines preserved.')
if __name__=='__main__':main()
