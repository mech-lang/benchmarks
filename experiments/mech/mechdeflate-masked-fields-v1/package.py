"""Archive actual trial data and source; omit rebuildable compiler caches."""
from pathlib import Path
from hashlib import sha256
import gzip,io,json,os,tarfile
D=Path(__file__).resolve().parent;N=Path('/private/tmp/mech-shared-cold-epilogues.2L6obP/.qualification/consolidation-995/natural4k-scorer-repair');S=N/'matcher-bit-fields-tied-study';Q=N.parent.parent;read=lambda p:json.loads(Path(p).read_text());files={};blobs={}
def add(path,name):
 path=Path(path);data=path.read_bytes();pin=sha256(data).hexdigest();row={'sha256':pin,'bytes':len(data)};assert name not in files or files[name]==row;files[name]=row;blobs.setdefault(pin,path)
def tree(root,prefix):
 for base,dirs,names in os.walk(root):
  dirs[:]=sorted(d for d in dirs if d not in {'target','test-target','compiler','.git','__pycache__'})
  for name in sorted(names):
   if name.endswith('.pyc') or name=='compile_profile':continue
   p=Path(base)/name
   if p.is_file():add(p,prefix+'/'+str(p.relative_to(root)))
for root,prefix in [(S,'study'),(N/'matcher-bit-fields-study','masked-study'),(N/'matcher-bit-fields-wide-study','copy-study')]:
 tree(root,prefix)
 for folder in ['screen-v1','full81-v1']:
  for result in (root/folder).glob('*-results.json'):
   for run in read(result)['runs']:tree(Path(run['run']),'runtime/'+Path(run['run']).name)
for role,folder in [('control',N/'fp-spill-keep-pairs-study/census/keep-pairs2'),('tied-linear4096',S/'census/tied-linear4096'),('tied-linear65536',S/'census/tied-linear65536')]:
 for name in ['receipt.json','linked-proof.json','promotion-recoveries/result.json']:add(folder/name,'actors/'+role+'/'+name)
 tree(folder/'bound','actors/'+role+'/bound')
tree(N/'fp-spill-keep-pairs-study/census/keep-pairs2/counts-word-reuse-v1-475','diagnostics/control')
for name in ['fixtures.json','pinned-peers/pins.json','pinned-peers/libdeflate-output-oracle.json','compare-library.py']:add(Q/name,name)
for i,fixture in enumerate(read(Q/'fixtures.json')):
 for kind in ['input','prefix','expected']:add(fixture[kind],f'fixtures/{i}/{kind}')
for role in ['roc','libdeflate']:add(read(Q/'pinned-peers/pins.json')['actors'][role]['command'][0],'peers/'+role+'-worker')
for actor,job in read(S/'matched-builds-v1/plan.json')['actors'].items():
 for i,path in enumerate(job['host_inputs_sha256']):add(path,f'fixed-support/{actor}/{i}')
manifest={'schema':1,'source_commit':read(S/'source-commit-binding.json')['source_commit'],'files':files,'unique_blobs':len(blobs),'logical_bytes':sum(r['bytes'] for r in files.values()),'unique_bytes':sum(p.stat().st_size for p in blobs.values()),'scope':'All three masked-field iterations, actual native tests/gates/counters, runtime observations, original source through final link clocks, public source replays and standalone outputs. Retain all partials; qualification and wins reported separately.'};(D/'raw-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with (D/'raw.tar.gz').open('wb') as raw,gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0,compresslevel=6) as zipped,tarfile.open(fileobj=zipped,mode='w') as archive:
 for pin,path in sorted(blobs.items()):
  data=path.read_bytes();assert sha256(data).hexdigest()==pin;item=tarfile.TarInfo('blobs/'+pin);item.size=len(data);item.mode=0o644;item.mtime=0;archive.addfile(item,io.BytesIO(data))
record={'archive_sha256':sha256((D/'raw.tar.gz').read_bytes()).hexdigest(),'archive_bytes':(D/'raw.tar.gz').stat().st_size,'manifest_sha256':sha256((D/'raw-manifest.json').read_bytes()).hexdigest(),'files':len(files),'unique_blobs':len(blobs)}
raw_file=D/'raw.tar.gz'
if raw_file.stat().st_size>48*1024*1024:
 payload=raw_file.read_bytes();parts=[]
 for index,offset in enumerate(range(0,len(payload),48*1024*1024)):
  data=payload[offset:offset+48*1024*1024];part=D/f'raw.tar.gz.{index:03}';part.write_bytes(data);parts.append({'file':part.name,'bytes':len(data),'sha256':sha256(data).hexdigest()})
 assert sha256(b''.join((D/r['file']).read_bytes() for r in parts)).hexdigest()==record['archive_sha256'];record['parts']=parts;raw_file.unlink()
(D/'archive.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
