"""Build the compiler and check native spill-storage witnesses from source."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import json,os,subprocess,shutil
import reproduce

def main():
    parser=ArgumentParser(__doc__)
    parser.add_argument('--mech-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--target-dir',type=Path)
    args=parser.parse_args();root=args.mech_root.resolve();out=args.output.resolve();out.mkdir(parents=True)
    recipes=json.loads((Path(__file__).resolve().parent/'recipes.json').read_text())
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip()
    assert commit==recipes['compiler_source_commit']
    compiler=reproduce.build_compiler(root,out,args.target_dir.resolve() if args.target_dir else out/'target')
    test=root/'hosts/gpu/src/native_artifact/program/codegen/fp_spill_tests.rs'
    manifest=out/'compiler-driver/Cargo.toml';manifest.write_text(manifest.read_text()+'\n[[test]]\nname = "fp_spill_storage"\npath = '+json.dumps(str(test))+'\n')
    build=json.loads((out/'compiler-build.json').read_text());command=[x for x in build['command'] if x not in ['--bin','compile_profile']];command[2]='test';command+=['--no-run','--test','fp_spill_storage','--message-format=json']
    with (out/'probe-build.stdout').open('w') as stdout,(out/'probe-build.stderr').open('w') as stderr:
        subprocess.run(command,cwd=root,env=reproduce.clean_environment()|build['environment'],stdout=stdout,stderr=stderr,check=True)
    entries=[]
    for line in (out/'probe-build.stdout').read_text().splitlines():
        try:row=json.loads(line)
        except ValueError:continue
        if row.get('reason')=='compiler-artifact' and row.get('executable') and row['target']['name']=='fp_spill_storage':entries.append(Path(row['executable']))
    binary,=entries;folder=out/'native-probe-v1';folder.mkdir();cmd=[str(binary),'--nocapture','--test-threads=1'];log=folder/'tests.log'
    with log.open('w') as output:subprocess.run(cmd,env=reproduce.clean_environment()|{"MECH_FP_SPILL_PROBE":str(folder/"observations.json")},stdout=output,stderr=output,check=True)
    assert 'test result: ok. 1 passed; 0 failed;' in log.read_text() and 'FP spill native calls: 256800' in log.read_text()
    record={'verified':True,'complete':True,'all_pass':True,'source_commit':commit,'compiler_sha256':reproduce.digest(compiler),'test_source_sha256':reproduce.digest(test),'binary_sha256':reproduce.digest(binary),'test_log_sha256':reproduce.digest(log),'native_test_executions':1,'native_calls':256800,'build_command':command,'command':cmd,'scope':'Two optimization levels, original/forwarded spills, five pressure/call shapes and five cache limits;256 seeds, five loop counts, aliases and invalid guards. Exact bit preservation, live vector registers and destructive callback clobbers.256800 actual native calls.'}
    data=json.loads((folder/'observations.json').read_text());assert data['native_observations']==256800 and data['exact_fallbacks']==40 and data['changed_functions']==40
    shutil.copy2(binary,folder/'native-probe-executable')
    (folder/'result.json').write_text(json.dumps(record,indent=2)+'\n');(out/'probe-verification.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:record[k] for k in ['verified','source_commit','native_calls','native_test_executions']},indent=2))
if __name__=='__main__':main()
