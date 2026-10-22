"""Observe real GMP quotient arguments/results without changing application bytes."""
import fcntl
import json
from pathlib import Path
import re
from run import HERE,ROOT,PLAN,COMMANDS,process,reference

def expected_trace(n):
    q,r,t,k,printed=1,0,1,0,0;lines=[];pairs=0
    while printed<n:
        k+=1;old_q=q;q*=k;r=(r+2*old_q)*(2*k+1);t*=2*k+1
        if r>q:
            a=(3*q+r)//t;b=(4*q+r)//t
            lines.extend([f'Q {3*q+r} {t} {a}\n',f'Q {4*q+r} {t} {b}\n']);pairs+=1
            if a==b:
                printed+=1
                if printed<n:r=(r-t*a)*10;q*=10
    return ''.join(lines).encode(),pairs

def main():
    out=HERE/'work-v1';out.mkdir(exist_ok=False);lib=HERE/'.build/gmp-work-counter.dylib'
    report=dict(status='running',diagnostic_only=True,benchmark_samples=0,application_bytes_unchanged=True,outputs=[],counter_source_sha256=process.sha(HERE/'gmp-work-counter.c'))
    def save():process.save(out/'results.json',report)
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        cmd=['/usr/bin/clang','-O2','-dynamiclib','-I/opt/homebrew/Cellar/gmp/6.3.0/include','-L/opt/homebrew/Cellar/gmp/6.3.0/lib',str(HERE/'gmp-work-counter.c'),'-lgmp','-o',str(lib)]
        r=process.execute(cmd,out/'build-counter',PLAN['environment'],lock,deadline=120);assert r['exit_status']==0,(out/'build-counter/stderr.bin').read_text()
        report['counter_library_sha256']=process.sha(lib);report['command_pins']={name:process.sha(Path(cmd[0])) for name,cmd in COMMANDS.items()}
        for n in (0,1,9,10,11,30,97,257,10000):
            want=reference(n)[0]
            if n<10000:trace,pairs=expected_trace(n);(out/f'expected-n{n}.trace').write_bytes(trace)
            else:trace=None;pairs=22454
            counts={}
            for name,cmd in COMMANDS.items():
                d=out/f'{name}-n{n}';env={**PLAN['environment'],'DYLD_INSERT_LIBRARIES':str(lib),'MECH_GMP_TRACE_QUOTIENTS':str(int(trace is not None))}
                r=process.execute(cmd+[str(n)],d,env,lock,deadline=120)
                assert r['exit_status']==0 and (d/'stdout.bin').read_bytes()==want,(name,n)
                stderr=(d/'stderr.bin').read_bytes();split=stderr.rsplit(b'WORK ',1);assert len(split)==2,(name,n,stderr[-500:])
                m=re.fullmatch(rb'tdiv=(\d+) fdiv=(\d+) mul_ui=(\d+) add=(\d+)\n',split[1]);assert m,(name,n)
                c=dict(zip(('tdiv','fdiv','mul_ui','add'),map(int,m.groups())))
                assert c['tdiv']==2*pairs and c['fdiv']==0,(name,n,c,pairs)
                assert split[0]==(trace or b''),(name,n,'quotient argument/result mismatch')
                counts[name]=c;report['outputs'].append(dict(label=name,n=n,counts=c,stdout_sha256=process.sha(d/'stdout.bin'),stderr_sha256=process.sha(d/'stderr.bin'),actual_quotients_match_independent_reference=trace is not None));save()
            assert counts['mech-parent']['mul_ui']-counts['mech-shared-numerator']['mul_ui']==pairs,(n,counts)
            assert counts['mech-compact-shared']==counts['mech-shared-numerator'],(n,counts)
        report['status']='all-real-quotient-traces-and-full-size-division-counts-pass';save();print(json.dumps(report['outputs'][-5:],indent=2))
if __name__=='__main__':main()
