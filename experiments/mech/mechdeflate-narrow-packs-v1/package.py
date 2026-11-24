"""Freeze qualification evidence; excludes compiler and test build caches."""
from pathlib import Path
from hashlib import sha256
import gzip,io,json,os,tarfile
D=Path(__file__).resolve().parent;N=Path('/private/tmp/mech-shared-cold-epilogues.2L6obP/.qualification/consolidation-995/natural4k-scorer-repair');T=N/'narrow-pack-study';M=N/'matcher-pair-combination-study';S=N/'literal-run-group-study';Q=N.parent.parent
read=lambda p:json.loads(Path(p).read_text());files={};blobs={}
def add(path,name):
 path=Path(path);data=path.read_bytes();pin=sha256(data).hexdigest();row={'sha256':pin,'bytes':len(data)};assert name not in files or files[name]==row;files[name]=row;blobs.setdefault(pin,path)
def tree(root,prefix):
 for base,dirs,names in os.walk(root):
  dirs[:]=sorted(d for d in dirs if d not in {'target','test-target','compiler','.git','__pycache__'})
  for name in sorted(names):
   if name.endswith('.pyc') or name=='compile_profile':continue
   p=Path(base)/name
   if p.is_file():add(p,prefix+'/'+str(p.relative_to(root)))
full=read(T/'full81-v1/pack-sqrt-results.json');assert full['complete'] and all(not any(run['required_named_missing'].values()) for run in full['runs']);assert read(T/'matched-builds-v1/deployment-smokes.json')['checked_executions']==324
for mode in ['normal','checked']:assert all(row['all_three_exact'] for row in read(T/('public-'+mode+'-replay-v1/reproduction.json'))['records'])
tree(T,'study')
for study in [T]:
 for result in (study/'screen-v1').glob('*-results.json'):
  for run in read(result)['runs']:
   folder=Path(run['run']);tree(folder,'runtime/'+folder.name)
for run in full['runs']:
 folder=Path(run['run']);tree(folder,'runtime/'+folder.name)
for role,source in [('control',N/'boolean-definition-reuse-study/census/boolean-sqrt'),('pack-sqrt',T/'census/pack-sqrt')]:
 for name in ['receipt.json','linked-proof.json','promotion-recoveries/result.json']:add(source/name,'actors/'+role+'/'+name)
 tree(source/'bound','actors/'+role+'/bound')
tree(N/'boolean-definition-reuse-study/census/boolean-sqrt-gates','native-gates')
tree(N/'boolean-definition-reuse-study/census/boolean-sqrt/counts-word-reuse-v1-475','diagnostics/control-address')
for name in ['fixtures.json','pinned-peers/pins.json','pinned-peers/libdeflate-output-oracle.json','compare-library.py']:add(Q/name,name)
for index,case in enumerate(read(Q/'fixtures.json')):
 for kind in ['input','prefix','expected']:add(case[kind],f'fixtures/{index}/{kind}')
for role in ['roc','libdeflate']:add(read(Q/'pinned-peers/pins.json')['actors'][role]['command'][0],'peers/'+role+'-worker')
for actor,job in read(T/'matched-builds-v1/plan.json')['actors'].items():
 for index,path in enumerate(job['host_inputs_sha256']):add(path,f'fixed-support/{actor}/{index}')
manifest={'schema':1,'source_commit':'91a7702d3c280383ac8b901748987a59474c01e2','files':files,'unique_blobs':len(blobs),'logical_bytes':sum(row['bytes'] for row in files.values()),'unique_bytes':sum(p.stat().st_size for p in blobs.values()),'scope':'Full81 qualified narrow-field packs and shifted extensions, matched complete builds and standalone streams, private and public native probes, actual counters, all new partials and public source replay outputs.'};(D/'raw-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with (D/'raw.tar.gz').open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as zipped,tarfile.open(fileobj=zipped,mode='w') as out:
 for pin,path in sorted(blobs.items()):
  data=path.read_bytes();assert sha256(data).hexdigest()==pin;entry=tarfile.TarInfo('blobs/'+pin);entry.size=len(data);entry.mode=0o644;entry.mtime=0;out.addfile(entry,io.BytesIO(data))
record={'archive_sha256':sha256((D/'raw.tar.gz').read_bytes()).hexdigest(),'archive_bytes':(D/'raw.tar.gz').stat().st_size,'manifest_sha256':sha256((D/'raw-manifest.json').read_bytes()).hexdigest(),'files':len(files),'unique_blobs':len(blobs)};(D/'archive.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
