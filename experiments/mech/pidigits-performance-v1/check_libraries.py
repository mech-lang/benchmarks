"""Owned read-only loader captures for every exact executable at the same input."""
import fcntl
import json
from pathlib import Path
from run import HERE,ROOT,PLAN,COMMANDS,process,reference

def main():
    out=HERE/'library-v1';out.mkdir(exist_ok=False);lib=Path(PLAN['environment']['MECH_GMP_LIBRARY']);report=dict(status='running',gmp_path=str(lib),gmp_sha256=process.sha(lib),subjects={})
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        for name,command in COMMANDS.items():
            d=out/name;env={**PLAN['environment'],'DYLD_PRINT_LIBRARIES':'1'}
            r=process.execute(command+['30'],d,env,lock,deadline=30)
            assert r['exit_status']==0 and (d/'stdout.bin').read_bytes()==reference(30)[0]
            stderr=(d/'stderr.bin').read_text();assert stderr and all(line.startswith('dyld[') for line in stderr.splitlines())
            assert str(lib) in stderr,(name,stderr)
            report['subjects'][name]=dict(command=command+['30'],executable_sha256=process.sha(Path(command[0])),loader_sha256=process.sha(d/'stderr.bin'),stdout_sha256=process.sha(d/'stdout.bin'));process.save(out/'results.json',report)
        for name,args in [('os',['/usr/bin/sw_vers']),('rust',['/Users/cim310/.cargo/bin/rustc','--version']),('gmp-link',['/usr/bin/otool','-L',str(lib)])]:
            env={**PLAN['environment'],'HOME':'/Users/cim310','PATH':'/Users/cim310/.cargo/bin:/usr/bin:/bin'}
            r=process.execute(args,out/name,env,lock,deadline=30);assert r['exit_status']==0
    report['status']='all-five-executables-load-pinned-gmp';process.save(out/'results.json',report);print(json.dumps(report,indent=2))
if __name__=='__main__':main()
