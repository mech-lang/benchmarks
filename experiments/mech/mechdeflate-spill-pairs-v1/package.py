"""Archive actual observations, source bindings and outputs; omit build caches."""
from pathlib import Path
from hashlib import sha256
import gzip,io,json,os,tarfile
D=Path(__file__).resolve().parent;N=Path('/private/tmp/mech-shared-cold-epilogues.2L6obP/.qualification/consolidation-995/natural4k-scorer-repair');P=N/'fp-spill-keep-pairs-study';R=N/'fp-one-cell-study';T=N/'fp-spill-fmov-study';Q=N.parent.parent;read=lambda p:json.loads(Path(p).read_text());files={};blobs={}
def add(path,name):
 path=Path(path);data=path.read_bytes();pin=sha256(data).hexdigest();row={'sha256':pin,'bytes':len(data)};assert name not in files or files[name]==row;files[name]=row;blobs.setdefault(pin,path)
def tree(root,prefix):
 for base,dirs,names in os.walk(root):
  dirs[:]=sorted(d for d in dirs if d not in {'target','test-target','compiler','.git','__pycache__'})
  for name in sorted(names):
   if name.endswith('.pyc') or name=='compile_profile':continue
   p=Path(base)/name
   if p.is_file():add(p,prefix+'/'+str(p.relative_to(root)))
for role in ['keep-pairs2','keep-pairs65536']:
 full=read(P/'full81-v1'/f'{role}-results.json');assert full['complete'] and all(not any(r['required_named_missing'].values()) for r in full['runs'])
assert read(P/'matched-builds-v1/deployment-smokes.json')['checked_executions']==405
assert read(R/'matched-builds-v1/deployment-smokes.json')['checked_executions']==324
tree(P,'study');tree(R,'one-cell-study')
for root in [P,R]:
 for result in (root/'screen-v1').glob('*-results.json'):
  for run in read(result)['runs']:tree(Path(run['run']),'runtime/'+Path(run['run']).name)
for role in ['keep-pairs2','keep-pairs65536']:
 for run in read(P/'full81-v1'/f'{role}-results.json')['runs']:tree(Path(run['run']),'runtime/'+Path(run['run']).name)
for role,source in [('control',N/'late-prefetch-base-study/census/shared-linear4096'),('keep-pairs2',P/'census/keep-pairs2'),('keep-pairs65536',P/'census/keep-pairs65536')]:
 for name in ['receipt.json','linked-proof.json','promotion-recoveries/result.json']:add(source/name,'actors/'+role+'/'+name)
 tree(source/'bound','actors/'+role+'/bound')
tree(N/'late-prefetch-base-study/census/shared-linear4096/counts-word-reuse-v1-475','diagnostics/control')
for name in ['result.json','observations.json','execution.log']:add(T/'native-probe-v1'/name,'prior-native-probe/'+name)
add(T/'source-overlay/hosts/gpu/src/native_artifact/program/codegen/fp_spill_tests.rs','prior-native-probe/fp_spill_tests.rs')
for name in ['fixtures.json','pinned-peers/pins.json','pinned-peers/libdeflate-output-oracle.json','compare-library.py']:add(Q/name,name)
for index,case in enumerate(read(Q/'fixtures.json')):
 for kind in ['input','prefix','expected']:add(case[kind],f'fixtures/{index}/{kind}')
for role in ['roc','libdeflate']:add(read(Q/'pinned-peers/pins.json')['actors'][role]['command'][0],'peers/'+role+'-worker')
for actor,job in read(P/'matched-builds-v1/plan.json')['actors'].items():
 for index,path in enumerate(job['host_inputs_sha256']):add(path,f'fixed-support/{actor}/{index}')
manifest={'schema':1,'source_commit':read(P/'source-commit-binding.json')['source_commit'],'files':files,'unique_blobs':len(blobs),'logical_bytes':sum(row['bytes'] for row in files.values()),'unique_bytes':sum(path.stat().st_size for path in blobs.values()),'scope':'Two fully qualified pair-preserving spill-cache recipes, one-cell partial, all runtime observations/counters, source/native probes, both complete-build matrices and729actual standalone outputs. Original source/bytecode unchanged; no64th Cwin.'};(D/'raw-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with (D/'raw.tar.gz').open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as zipped,tarfile.open(fileobj=zipped,mode='w') as archive:
 for pin,path in sorted(blobs.items()):
  data=path.read_bytes();assert sha256(data).hexdigest()==pin;entry=tarfile.TarInfo('blobs/'+pin);entry.size=len(data);entry.mode=0o644;entry.mtime=0;archive.addfile(entry,io.BytesIO(data))
record={'archive_sha256':sha256((D/'raw.tar.gz').read_bytes()).hexdigest(),'archive_bytes':(D/'raw.tar.gz').stat().st_size,'manifest_sha256':sha256((D/'raw-manifest.json').read_bytes()).hexdigest(),'files':len(files),'unique_blobs':len(blobs)};(D/'archive.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
