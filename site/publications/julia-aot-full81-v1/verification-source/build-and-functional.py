import hashlib,json,subprocess,time
from datetime import datetime,timezone
from pathlib import Path
B=Path('/private/tmp/mech-julia-aot-pages-preparation-20261015-v1');P=B/'source'
node='/Users/coreymontella/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
commands=[['python3','tools/build_site.py']]
for name in ['data_projection','benchmark_traits','density','labels','languages','layers','publication','rankings','relative_comparisons']:
 command=[node,'site/tests/'+name+'.mjs']
 if name=='data_projection':command+=['data/benchmarks.json','site/public/data.json']
 if name=='languages':command+=['data/benchmarks.json']
 commands.append(command)
records=[]
for i,command in enumerate(commands):
 started=time.time();p=subprocess.run(command,cwd=P,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
 (B/('functional-'+str(i)+'.stdout')).write_text(p.stdout);(B/('functional-'+str(i)+'.stderr')).write_text(p.stderr)
 records.append({'command':command,'exit_code':p.returncode,'elapsed_seconds':time.time()-started,'stdout':p.stdout,'stderr':p.stderr})
 if p.returncode:raise RuntimeError('Functional check failed: '+repr(command)+' '+p.stderr)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
public=P/'site/public';manifest=json.loads((public/'build.json').read_text())
receipt={'schema':'julia-aot-pages-remote-build-v1','status':'passed','checked_at':datetime.now(timezone.utc).isoformat(),'host':'Macmini.ht.home','source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=P,text=True).strip(),'canonical_data_sha256':sha(P/'data/benchmarks.json'),'build':manifest['version'],'manifest_sha256':sha(public/'build.json'),'dataset_sha256':sha(public/'data.json'),'dataset_bytes':(public/'data.json').stat().st_size,'gzip_sha256':sha(public/'data.json.gz'),'gzip_bytes':(public/'data.json.gz').stat().st_size,'asset_count':len(manifest['files']),'commands':records,'performance_profile':False,'benchmark_runs':0}
(B/'build-and-functional.json').write_text(json.dumps(receipt,indent=2)+'\n')
print(json.dumps({k:v for k,v in receipt.items() if k!='commands'}))
