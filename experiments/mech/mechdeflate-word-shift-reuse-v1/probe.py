"""Build and run the native shift-extension probe directly from a Mech checkout."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json,os,subprocess
import reproduce

def main():
 p=ArgumentParser(__doc__);p.add_argument('--mech-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--target-dir',type=Path);a=p.parse_args();root=a.mech_root.resolve();out=a.output.resolve();out.mkdir(parents=True);target=a.target_dir.resolve() if a.target_dir else out/'target';compiler=reproduce.build_compiler(root,out,target);driver=out/'compiler-driver';manifest=driver/'Cargo.toml';test=root/'hosts/gpu/src/native_artifact/program/codegen/low_word_tests.rs';manifest.write_text(manifest.read_text()+'\n[[test]]\nname = "word_shift_extensions"\npath = '+json.dumps(str(test))+'\n');build=json.loads((out/'compiler-build.json').read_text());command=[x for x in build['command'] if x not in ['--bin','compile_profile']];command[2]='test';command+=['--no-run','--test','word_shift_extensions','--message-format=json']
 with (out/'probe-build.stdout').open('w') as stdout,(out/'probe-build.stderr').open('w') as stderr:subprocess.run(command,cwd=root,env=reproduce.clean_environment()|build['environment'],stdout=stdout,stderr=stderr,check=True)
 executables=[]
 for line in (out/'probe-build.stdout').read_text().splitlines():
  try:r=json.loads(line)
  except ValueError:continue
  if r.get('reason')=='compiler-artifact' and r.get('executable') and r['target']['name']=='word_shift_extensions':executables.append(Path(r['executable']))
 binary,=executables;runs=[]
 for mode in ['0','1']:
  folder=out/('mode-'+mode);folder.mkdir();flags={'MECH_ARM64_REUSE_I32_ARITHMETIC':'all','MECH_ARM64_REUSE_I32_SHIFTS':mode,'MECH_SHIFT_EXTENSION_PROBE':str(folder)};cmd=[str(binary),'--nocapture','--test-threads=1'];log=folder/'tests.log'
  with log.open('w') as f:subprocess.run(cmd,env=reproduce.clean_environment()|flags,stdout=f,stderr=f,check=True)
  assert 'test result: ok. 2 passed; 0 failed;' in log.read_text();calls=sum(json.loads((folder/(group+'.json')).read_text())['native_observations'] for group in ['fixed','fallback']);assert calls==519400;runs.append({'mode':mode,'command':cmd,'flags':flags,'passed':2,'native_calls':calls,'log':str(log.relative_to(out)),'log_sha256':reproduce.digest(log)})
 changed=[]
 for group in ['fixed','fallback']:
  left={x['name']:x for x in json.loads((out/'mode-0'/(group+'.json')).read_text())['functions']};right={x['name']:x for x in json.loads((out/'mode-1'/(group+'.json')).read_text())['functions']};assert left.keys()==right.keys()
  for name,x in left.items():
   y=right[name]
   if (x['form'] in ['Immediate','BinaryConstant'] and x['amount']%32==0) or x['form'] in ['Parameter','Variable']:assert x['body']==y['body'],name
   if x['body']!=y['body']:changed.append({'name':name,'form':x['form'],'amount':x['amount'],'off_bytes':len(x['body']),'on_bytes':len(y['body'])})
 assert len(changed)==22
 record={'verified':True,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'compiler_sha256':reproduce.digest(compiler),'probe_binary_sha256':reproduce.digest(binary),'test_source_sha256':reproduce.digest(test),'native_calls':sum(x['native_calls'] for x in runs),'native_test_executions':4,'runs':runs,'changed_functions':changed,'scope':'Actual native mathematical-reference and memory checks. Probe construction is separate from all primary runtime and codec-build clocks.'};(out/'probe-verification.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:record[k] for k in ['verified','source_commit','native_calls','native_test_executions']},indent=2))

if __name__=='__main__':main()
