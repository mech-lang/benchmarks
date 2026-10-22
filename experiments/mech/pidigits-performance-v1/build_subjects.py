"""Rebuild exact Mech sources and unchanged published Rust source, serially."""
import fcntl
import json
import os
from pathlib import Path
import shutil
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'janet/pidigits-gmp-v1'))
from common import process,PLAN,ROOT
HERE=Path(__file__).resolve().parent
WORKSPACE=Path('/private/tmp/mech-pidigits-performance')

def main():
    out=HERE/'build-v1';out.mkdir(exist_ok=False);b=HERE/'.build';b.mkdir(exist_ok=True)
    env={**PLAN['environment'],'PATH':'/Users/cim310/.cargo/bin:/usr/bin:/bin','HOME':'/Users/cim310','C_INCLUDE_PATH':'/opt/homebrew/Cellar/gmp/6.3.0/include','LIBRARY_PATH':'/opt/homebrew/Cellar/gmp/6.3.0/lib','RUSTFLAGS':'-L native=/opt/homebrew/Cellar/gmp/6.3.0/lib','CARGO_TARGET_DIR':str(WORKSPACE/'target')}
    compiler=WORKSPACE/'target/release/mech';report=dict(status='running',environment=env,compiler_sha256=process.sha(compiler),subjects={})
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for name,source in [('mech-parent','parent'),('mech-shared-numerator','shared-numerator'),('mech-compact-shared','compact-shared')]:
            source=HERE/'sources'/(source+'.mec');binary=b/name
            command=[str(compiler),'build',str(source),'--backend','cranelift','--offline','--keep-project','--no-config','--name',name,'-o',str(binary)]
            r=process.execute(command,out/name,env,lock,deadline=1800)
            assert r['exit_status']==0,(name,(out/name/'stderr.bin').read_text()[-3000:])
            project=b/(name+'.project');evidence=out/name/'object';evidence.mkdir()
            for file in ('control.json','mech-control.o','source.mec','Cargo.toml','Cargo.lock','build.rs'):
                assert (project/file).is_file(),str(project/file)
                shutil.copyfile(project/file,evidence/file)
            report['subjects'][name]=dict(command=command,source_sha256=process.sha(source),executable_sha256=process.sha(binary),object_sha256=process.sha(evidence/'mech-control.o'));process.save(out/'results.json',report)
        source=ROOT/'archive/workloads/pidigits/upstream/pidigits-rust-3.rs';binary=b/'rust-3'
        command=['/Users/cim310/.cargo/bin/rustc','--edition=2015','-C','opt-level=3','-C','target-cpu=native','-C','codegen-units=1','-L','native=/opt/homebrew/Cellar/gmp/6.3.0/lib',str(source),'-o',str(binary)]
        r=process.execute(command,out/'rust-3',env,lock,deadline=120)
        assert r['exit_status']==0,(out/'rust-3/stderr.bin').read_text()
        report['subjects']['rust-3']=dict(command=command,source_sha256=process.sha(source),executable_sha256=process.sha(binary),application_bytes_unchanged=True)
    report['status']='all-four-subjects-built';process.save(out/'results.json',report);print(json.dumps(report['subjects'],indent=2))
if __name__=='__main__':main()
