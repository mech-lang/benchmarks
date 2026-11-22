"""Build the source compiler and execute the three-mode native test corpus."""
from argparse import ArgumentParser
from pathlib import Path
from hashlib import sha256
import json,subprocess,shutil
import reproduce
HERE=Path(__file__).resolve().parent

def main():
 parser=ArgumentParser(__doc__);parser.add_argument('--mech-root',type=Path,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--target-dir',type=Path);args=parser.parse_args();root=args.mech_root.resolve();out=args.output.resolve();out.mkdir(parents=True)
 recipe=json.loads((HERE/'recipes.json').read_text());commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip();assert commit==recipe['compiler_source_commit'];test=root/'hosts/gpu/src/native_artifact/program/codegen/narrow_pack_tests.rs';assert reproduce.digest(test)==recipe['native_probe_source_sha256'];compiler=reproduce.build_compiler(root,out,args.target_dir.resolve() if args.target_dir else out/'target');manifest=out/'compiler-driver/Cargo.toml';manifest.write_text(manifest.read_text()+'\n[[test]]\nname = "narrow_pack_extensions"\npath = '+json.dumps(str(test))+'\n');build=json.loads((out/'compiler-build.json').read_text());command=[x for x in build['command'] if x not in ['--bin','compile_profile']];command[2]='test';command+=['--no-run','--test','narrow_pack_extensions','--message-format=json'];entries=[]
 with (out/'probe-build.stdout').open('w') as stdout,(out/'probe-build.stderr').open('w') as stderr:subprocess.run(command,cwd=root,env=reproduce.clean_environment()|build['environment'],stdout=stdout,stderr=stderr,check=True)
 for line in (out/'probe-build.stdout').read_text().splitlines():
  try:row=json.loads(line)
  except ValueError:continue
  if row.get('reason')=='compiler-artifact' and row.get('executable') and row['target']['name']=='narrow_pack_extensions':entries.append({'path':row['executable'],'sha256':reproduce.digest(Path(row['executable']))})
 assert len(entries)==1;(out/'probe-build.json').write_text(json.dumps({'exit_code':0,'executables':entries,'command':command},indent=2)+'\n');source=HERE/'native-probe.py';exec(compile(source.read_text(),str(source),'exec'),{'__file__':str(out/'native-probe.py'),'__name__':'__main__'});result=json.loads((out/'native-probe-v1/result.json').read_text());assert result['native_calls']==6709248 and result['test_executions']==4 and result['all_pass'];record={'verified':True,'source_commit':commit,'compiler_sha256':reproduce.digest(compiler),'test_source_sha256':reproduce.digest(test),'native_test_executions':4,'native_calls':result['native_calls'],'binary_sha256':entries[0]['sha256'],'result_sha256':reproduce.digest(out/'native-probe-v1/result.json')};(out/'probe-verification.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
if __name__=='__main__':main()
