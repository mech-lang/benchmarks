"""Capture additional exact source reader evidence, without changing sealed v1."""
import fcntl,gzip,hashlib,importlib.util,json,os,signal,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
PACKET=ROOT/'experiments/clojure/compact-primitive-v1/source-owner-v1'
SOURCE_PACKET=ROOT/'experiments/source-normalization/clojure-v1'
CORE=ROOT/'experiments/clojure/optimization-v1/.build'
CANDIDATES=[('compact_hot_aset.clj','e73abcb37312c1f54fd71e4fbc80042d0581b5e36bc26e06a2d46aebe575ef05'),
 ('compact_all_aset.clj','ed81b8e90730e54abebeddf029f2822b5c6074b71ef070836e3c8e32a0a5b86c')]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(x):return (json.dumps(x,sort_keys=True,ensure_ascii=False,indent=2)+'\n').encode()
def require(ok,message):
 if not ok:raise ValueError(message)
def save(path,value):path.write_bytes(encoded(value))
with Path('/tmp/mech-clbg-timing.lock').open('r+b') as lock:
 fcntl.flock(lock.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
 require(not PACKET.exists(),'fresh source owner packet required');PACKET.mkdir(parents=True)
 terminal=dict(schema='supplemental-clojure-reader-window.v1',status='started',canonical_changed=False,chart_admission=False,application_execution=False)
 try:
  tool_path=ROOT/'tools/clojure_logical_source_units.py';spec=importlib.util.spec_from_file_location('reviewed_clojure_owners',tool_path);tool=importlib.util.module_from_spec(spec);spec.loader.exec_module(tool)
  review=json.loads((SOURCE_PACKET/'independent-review.json').read_bytes())
  require(sha(tool_path.read_bytes())==review['approved_source_scope']['tool_sha256'],'owner tool drift')
  catalog_raw=(ROOT/'data/benchmarks.json').read_bytes();catalog=json.loads(catalog_raw)
  parent=catalog['programs']['nbody:clojure-nbody-compact'];jobs={}
  for source_hash in parent['files']:
   source=catalog['files'][source_hash];role=parent.get('file_roles',{}).get(source_hash,{}).get('role','application')
   require(sha(source['code'].encode())==source_hash,'parent/support drift')
   jobs['file:'+source_hash]=dict(text=source['code'],source_sha256=source_hash,role=role,path=source['path'],scope='retained-control')
  for name,digest in CANDIDATES:
   path=ROOT/'experiments/clojure/compact-primitive-v1/sources/clbg/nbody'/name;raw=path.read_bytes();require(sha(raw)==digest,'candidate drift')
   jobs['file:'+digest]=dict(text=raw.decode(),source_sha256=digest,role='application',path=path.relative_to(ROOT).as_posix(),scope='supplemental-unadmitted-source')
  manifest=dict(schema='supplemental-clojure-exact-source-inputs.v1',catalog_sha256=sha(catalog_raw),jobs=jobs,policy=tool.POLICY,analysis_tool_sha256=sha(tool_path.read_bytes()),sealed_parent_report_sha256=sha((SOURCE_PACKET/'qualification.json').read_bytes()))
  save(PACKET/'inputs.json',manifest)
  quote=lambda x:json.dumps(x,ensure_ascii=True)
  edn='[\n'+'\n'.join('['+' '.join(quote(x) for x in (key,row['text'],row['source_sha256']))+']' for key,row in sorted(jobs.items()))+'\n]\n';(PACKET/'inputs.edn').write_text(edn)
  java=CORE/'jdk/jdk-25.0.4.1+1/Contents/Home/bin/java';require(sha(java.read_bytes())==tool.JAVA_SHA,'java drift')
  jars=[CORE/'vendor'/name for name in tool.JAR_PINS if name!='tools.reader-1.6.0.jar']+[SOURCE_PACKET/'.build/vendor/tools.reader-1.6.0.jar']
  require({p.name:sha(p.read_bytes()) for p in jars}==tool.JAR_PINS,'reader jar drift')
  helper=SOURCE_PACKET/'capture.clj';require(sha(helper.read_bytes())==review['approved_source_scope']['helper_sha256'],'reader helper drift')
  command=[str(java),'-Xms32m','-Xmx256m','-cp',':'.join(map(str,jars)),'clojure.main',str(helper),str(PACKET/'inputs.edn')]
  env=dict(PATH='/usr/bin:/bin',LANG='C',LC_ALL='C',TZ='UTC');record=dict(command=command,cwd=str(ROOT),environment=env,started=time.time(),common_lock_inherited=True,timeout=45)
  process=subprocess.Popen(command,cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,pass_fds=(lock.fileno(),));record['pid']=process.pid
  try:out,err=process.communicate(timeout=45)
  except BaseException:
   os.killpg(process.pid,signal.SIGKILL);out,err=process.communicate();record['timeout_or_interrupt']=True
  record.update(finished=time.time(),exit_status=process.returncode,stdout_sha256=sha(out),stderr_sha256=sha(err));save(PACKET/'process.json',record)
  (PACKET/'stdout.json').write_bytes(out);(PACKET/'stderr.bin').write_bytes(err)
  require(process.returncode==0 and not err,'Native reader failed')
  native=json.loads(out);require(set(native['jobs'])==set(jobs),'reader job set drift')
  outcomes={}
  for key,row in jobs.items():outcomes[key]=tool.owners(row['text'],tool.source_tree(row['text']),native['jobs'][key])
  report=dict(schema='supplemental-clojure-source-owner-qualification.v1',policy=tool.POLICY,
   status='native-evidence-captured-pending-independent-review',canonical_changed=False,chart_admission=False,application_execution=False,
   input_manifest_sha256=sha((PACKET/'inputs.json').read_bytes()),native_output_sha256=sha(out),process_receipt_sha256=sha((PACKET/'process.json').read_bytes()),
   helper_sha256=sha(helper.read_bytes()),analysis_tool_sha256=sha(tool_path.read_bytes()),policy_sha256=sha((SOURCE_PACKET/'policy.json').read_bytes()),
   java_sha256=tool.JAVA_SHA,jars=tool.JAR_PINS,outcomes=outcomes)
  save(PACKET/'qualification.json',report)
  terminal.update(status='completed-pending-review',jobs=len(jobs),report_sha256=sha((PACKET/'qualification.json').read_bytes()),
   units={key:row['logical_units'] for key,row in outcomes.items()},unowned_significant_tokens=sum(row['coverage']['unowned_significant_tokens'] for row in outcomes.values()))
 except BaseException as error:
  terminal.update(status='failed-retained',error=repr(error));save(PACKET/'terminal.json',terminal);raise
 save(PACKET/'terminal.json',terminal);print(json.dumps(terminal))
