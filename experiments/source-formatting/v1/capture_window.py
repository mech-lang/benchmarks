"""One explicitly scheduled serial native window; never execute application input."""
import fcntl,gzip,hashlib,importlib.util,json,os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
NIM=ROOT/'experiments/nim/optimization-v1';DIST=NIM/'.build/nim/nim-2.2.12';RUN=HERE/'nim-run-v1'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def encoded(x):return (json.dumps(x,sort_keys=True,indent=2,ensure_ascii=False)+'\n').encode()
def save(path,x):path.write_bytes(encoded(x))
def require(x,m):
 if not x:raise ValueError(m)
def native(name,cmd,cwd,timeout=90):
 path=RUN/(name+'.json');require(not path.exists(),'receipt already exists')
 record=dict(command=cmd,cwd=str(cwd),environment=ENV,common_lock_inherited=True,started=time.time(),timeout=timeout)
 proc=subprocess.Popen(cmd,cwd=cwd,env=ENV,stdout=subprocess.PIPE,stderr=subprocess.PIPE,start_new_session=True,pass_fds=(LOCK.fileno(),))
 record['pid']=proc.pid
 try:out,err=proc.communicate(timeout=timeout)
 except BaseException:
  os.killpg(proc.pid,signal.SIGKILL);out,err=proc.communicate();record['timeout_or_interrupt']=True
 finally:
  record.update(exit_status=proc.returncode,finished=time.time(),stdout_sha256=sha(out),stderr_sha256=sha(err))
  (RUN/(name+'.stdout')).write_bytes(out);(RUN/(name+'.stderr')).write_bytes(err);save(path,record)
 require(proc.returncode==0,name+' failed: '+err.decode(errors='replace')[-1500:]);return out
with Path('/tmp/mech-clbg-timing.lock').open('r+b') as LOCK:
 fcntl.flock(LOCK.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
 ENV=dict(PATH='/usr/bin:/bin',LANG='C',LC_ALL='C',TZ='UTC',HOME=str(RUN/'home'),XDG_CONFIG_HOME=str(RUN/'home'))
 (RUN/'home').mkdir(exist_ok=True);(RUN/'.build').mkdir(exist_ok=True)
 receipt=dict(schema='nim-formatter-native-window.v1',status='started',application_execution=False,canonical_changed=False,chart_admission=False)
 try:
  restoration=json.loads((NIM/'runtime-restoration.json').read_bytes());verified={}
  for relative,digest in restoration['checked_distribution_pins'].items():
   require(sha((DIST/relative).read_bytes())==digest,'distribution drift '+relative);verified[relative]=digest
  require(sha((DIST/'bin/nimpretty').read_bytes())=='cdf07fca977cfcfbeceb0189317657280ea89b11bed7220524bfef66db862cd5','formatter drift')
  receipt['verified_distribution_files']=len(verified)
  catalog=json.loads((ROOT/'data/benchmarks.json').read_bytes());key='knucleotide:nim-knucleotide-preencoded-v1';profile=catalog['programs'][key];source_hash=profile['files'][0]
  raw=catalog['files'][source_hash]['code'].encode();require(sha(raw)==source_hash=='b8373233e975e0a09fcab239b827c6535d8b024b2c7ec4d60ac4d34820bb745b','source drift')
  source=RUN/'input.nim';source.write_bytes(raw);source.chmod(0o444)
  pretty=str(DIST/'bin/nimpretty');version=native('version',[pretty,'--version'],RUN,15);require(version==b'0.2\n','wrong formatter version')
  for label,a,b in [('format',source,RUN/'formatted.nim'),('format-again',RUN/'formatted.nim',RUN/'formatted-again.nim')]:
   native(label,[pretty,'--indent:0','--maxLineLen:80','--out:'+str(b),str(a)],RUN,30)
  formatted=(RUN/'formatted.nim').read_bytes();require(formatted==(RUN/'formatted-again.nim').read_bytes(),'formatter is not idempotent')
  helper=RUN/'parse_proof.nim';binary=RUN/'.build/parse_proof'
  native('build-verifier',[str(DIST/'bin/nim'),'c','--skipUserCfg','--skipParentCfg','--skipProjCfg','--hints:off','--verbosity:0','--path:'+str(DIST),'--nimcache:'+str(RUN/'.build/cache'),'--out:'+str(binary),str(helper)],RUN,90)
  proof=json.loads(native('native-proof',[str(binary),str(source),str(RUN/'formatted.nim'),str(RUN/'formatted-again.nim')],RUN,20))
  require(proof[0]['ast']==proof[1]['ast']==proof[2]['ast'],'Native AST differs')
  require(proof[0]['tokens']==proof[1]['tokens']==proof[2]['tokens'],'Native token payload differs')
  require(proof[0]['comments']==proof[1]['comments']==proof[2]['comments'],'Native comment payload differs')
  mask_path=ROOT/'archive/validation/loc-normalization/20261012/foreign_future_mask.py';require(sha(mask_path.read_bytes())=='3b9a5c498459e5ae3ed04695faef938bbd15080c2c47ac1010ef87fb964cabd5','physical mask drift')
  spec=importlib.util.spec_from_file_location('isolated_nim_physical_mask',mask_path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
  text=formatted.decode();masked=module.mask_future(text,'nim');require(not masked['diagnostics'] and len(masked['cleaned'])==len(text),'lexical mask failed')
  count=sum(bool(row.strip()) for row in masked['cleaned'].splitlines(keepends=True))
  require(sha(source.read_bytes())==source_hash,'source changed')
  receipt.update(status='native-evidence-captured-pending-review',profile=key,source_sha256=source_hash,
   formatted_output_sha256=sha(formatted),second_output_sha256=sha((RUN/'formatted-again.nim').read_bytes()),
   formatted_physical_loc=count,physical_definition='nonblank-noncomment-physical-lines-v1',physical_mask_sha256=sha(mask_path.read_bytes()),
   physical_mask_note='Direct exact mask_future(nim), equivalent to retained mask_nim for this non-BOM source; no owner normalization.',
   helper_sha256=sha(helper.read_bytes()),helper_binary_sha256=sha(binary.read_bytes()),
   native_ast_identical=True,native_token_payload_identical=True,native_comments_identical=True,idempotent=True,
   token_count=len(proof[0]['tokens']),verifier_scope='Raw compiler parser/lexer only; no semantic pass, imports, source filters, application evaluation or macro expansion.')
 except BaseException as error:
  receipt.update(status='failed-retained',error=repr(error));save(RUN/'terminal.json',receipt);raise
 save(RUN/'terminal.json',receipt)
 print(json.dumps(receipt))
