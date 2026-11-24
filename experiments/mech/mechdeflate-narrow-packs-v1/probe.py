"""Rebuild and execute the narrow-pack native witnesses from a Mech checkout."""
from argparse import ArgumentParser
from hashlib import sha256
from pathlib import Path
import collections,json,os,shutil,struct,subprocess
import reproduce

def run_matrix(work):
    K=work;read=lambda p:json.loads(Path(p).read_text());sha=lambda p:sha256(Path(p).read_bytes()).hexdigest();build=read(K/'probe-build.json');assert build['exit_code']==0;entry,=build['executables'];binary=Path(entry['path']);assert sha(binary)==entry['sha256'];out=K/'native-probe-v1';out.mkdir();base={k:v for k,v in os.environ.items() if not k.startswith('MECH_')};runs=[]
    for mode in ['00','01','10','11']:
     folder=out/('mode-'+mode);folder.mkdir();flags={'MECH_ARM64_REUSE_I32_ARITHMETIC':'all','MECH_ARM64_REUSE_I32_SHIFTS':'1','MECH_ARM64_REUSE_I8_DEFINITIONS':'all','MECH_ARM64_REUSE_I8_BOOLEAN_DEFINITIONS':'1','MECH_ARM64_PACK_NARROW_HALVES':mode[0],'MECH_ARM64_FOLD_SHIFTED_EXTENSIONS':mode[1],'MECH_NARROW_PACK_PROBE':str(folder)};cmd=[str(binary),'--nocapture','--test-threads=1'];log=folder/'tests.log'
     with log.open('w') as f:r=subprocess.run(cmd,env=base|flags,stdout=f,stderr=f)
     assert r.returncode==0 and 'test result: ok. 2 passed; 0 failed;' in log.read_text(),(log,log.read_text()[-6000:]);calls=sum(read(folder/(group+'.json'))['native_observations'] for group in ['unsigned','fallback']);runs.append({'mode':mode,'command':cmd,'flags':flags,'passed':2,'native_observations':calls,'log':str(log.relative_to(K)),'log_sha256':sha(log)});print('MODE',mode,'2 tests;',calls,'native calls passed',flush=True)
    changes=[];excluded=collections.Counter();geometries=set();templates={32:read(K/'assembler-oracle/result.json')['instructions']['_bfi32']['word'],64:read(K/'assembler-oracle/result.json')['instructions']['_bfi64']['word']}
    for mode in ['01','10','11']:
     for group in ['unsigned','fallback']:
      a={x['name']:x for x in read(out/'mode-00'/(group+'.json'))['functions']};b={x['name']:x for x in read(out/('mode-'+mode)/(group+'.json'))['functions']};assert a.keys()==b.keys()
      for name,x in a.items():
       y=b[name];changed=x['body']!=y['body'];count=x['amount']%x['bits'];form=x['form']
       if form in ['Raw','Variable'] or (count==0 and form!='Variable'):
        assert not changed,('excluded producer changed',mode,name);excluded[mode]+=1
       if changed:changes.append({'mode':mode,'name':name,'form':form,'op':x['op'],'opt':x['opt'],'bits':x['bits'],'narrow_bits':x['narrow_bits'],'amount':x['amount'],'off_bytes':len(x['body']),'on_bytes':len(y['body'])})
       if mode in ['10','11']:
        for offset in range(0,len(y['body']),4):
         word=struct.unpack_from('<I',bytes(y['body']),offset)[0]
         for bits,template in templates.items():
          if word&0xfffffc00==template&0xfffffc00:geometries.add(bits)
     assert any(x['mode']==mode and x['form']=='Basic' and x['op']=='Or' and x['opt']=='none' for x in changes),'no admitted pack changed'
    assert geometries=={32,64},geometries
    record={'complete':True,'all_pass':True,'runs':runs,'native_test_executions':8,'native_calls':sum(x['native_observations'] for x in runs),'changed_functions':changes,'excluded_exact_functions':dict(excluded),'assembler_geometries_observed':sorted(geometries),'binary_sha256':sha(binary),'source_manifest_sha256':sha(K/'producer-plan.json'),'scope':'Actual native mathematical-reference outputs and all nine memory words under both optimization levels and all four option combinations. Dirty original operands, shared extensions, joined narrow values, modulo shifts and rejected null pointers checked. Raw and variable producers and identity shifts remain byte-exact; BFI opcode geometries match an independent assembler oracle.'};(out/'result.json').write_text(json.dumps(record,indent=2)+'\n');print('NATIVE COMPLETE',record['native_calls'],'calls;',len(changes),'changed bodies;',dict(excluded),'excluded exact',flush=True)

def main():
    parser=ArgumentParser(__doc__)
    parser.add_argument('--mech-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--target-dir',type=Path)
    args=parser.parse_args()
    root,out=args.mech_root.resolve(),args.output.resolve()
    out.mkdir(parents=True)
    target=args.target_dir.resolve() if args.target_dir else out/'target'
    compiler=reproduce.build_compiler(root,out,target)
    test=root/'hosts/gpu/src/native_artifact/program/codegen/narrow_pack_tests.rs'
    manifest=out/'compiler-driver/Cargo.toml'
    manifest.write_text(manifest.read_text()+'\n[[test]]\nname = "narrow_pack_extensions"\npath = '+json.dumps(str(test))+'\n')
    build=json.loads((out/'compiler-build.json').read_text())
    command=[x for x in build['command'] if x not in ['--bin','compile_profile']]
    command[2]='test'
    command+=['--no-run','--test','narrow_pack_extensions','--message-format=json']
    with (out/'probe-build.stdout').open('w') as stdout,(out/'probe-build.stderr').open('w') as stderr:
        subprocess.run(command,cwd=root,env=reproduce.clean_environment()|build['environment'],stdout=stdout,stderr=stderr,check=True)
    executables=[]
    for line in (out/'probe-build.stdout').read_text().splitlines():
        try: row=json.loads(line)
        except ValueError: continue
        if row.get('reason')=='compiler-artifact' and row.get('executable') and row['target']['name']=='narrow_pack_extensions':
            executables.append({'path':row['executable'],'sha256':reproduce.digest(Path(row['executable']))})
    assert len(executables)==1
    (out/'probe-build.json').write_text(json.dumps({'exit_code':0,'command':command,'executables':executables},indent=2)+'\n')
    (out/'producer-plan.json').write_text(json.dumps({'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'test_source_sha256':reproduce.digest(test)},indent=2)+'\n')
    (out/'assembler-oracle').mkdir()
    shutil.copy2(Path(__file__).resolve().parent/'assembler-oracle.json',out/'assembler-oracle/result.json')
    run_matrix(out)
    record=json.loads((out/'native-probe-v1/result.json').read_text())
    record.update(verified=record['complete'] and record['all_pass'],source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),compiler_sha256=reproduce.digest(compiler),test_source_sha256=reproduce.digest(test))
    assert record['native_calls']==13328640 and record['native_test_executions']==8
    (out/'probe-verification.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({key:record[key] for key in ['verified','source_commit','native_calls','native_test_executions']},indent=2))

if __name__=='__main__': main()
