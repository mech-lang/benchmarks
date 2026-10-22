"""Serial complete-process comparison; no source edits to the published Rust entry."""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import random
import statistics
import sys

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path.insert(0,str(ROOT/'experiments/janet/pidigits-gmp-v1'))
from common import process,PLAN,reference
BIN=HERE/'.build'
COMMANDS={
 'mech-parent':[str(BIN/'mech-parent')],
 'mech-shared-numerator':[str(BIN/'mech-shared-numerator')],
 'mech-compact-shared':[str(BIN/'mech-compact-shared')],
 'rust-3':[str(BIN/'rust-3')],
 'janet-positive':[PLAN['runtime'],'-R','-n',str(ROOT/'experiments/janet/pidigits-gmp-v1/sources/positive-division.janet')]}

def main():
    mode=sys.argv[1];assert mode in ('qualify','time')
    out=HERE/('qualification-v1' if mode=='qualify' else 'run-v1');out.mkdir(exist_ok=False)
    files=[Path(__file__),HERE/'sources/parent.mec',HERE/'sources/shared-numerator.mec',HERE/'sources/compact-shared.mec',ROOT/'archive/workloads/pidigits/upstream/pidigits-rust-3.rs',ROOT/'experiments/janet/pidigits-gmp-v1/sources/positive-division.janet',ROOT/'experiments/janet/pidigits-gmp-v1/common.py',ROOT/'experiments/janet/knucleotide-bytes-v1/process.py',Path(PLAN['environment']['MECH_GMP_LIBRARY']),*[Path(c[0]) for c in COMMANDS.values()]]
    pins={str(p):process.sha(p) for p in files}
    report=dict(status='running',mode=mode,commands=COMMANDS,pins=pins,samples=[],telemetry=[],canonical_changes=False,chart_admission=False,historical_mech_denominator_seconds=.300272042,timing_boundary='Fresh process from parent monotonic clock before fork through independently observed exit; includes startup, parsing/JIT for Janet, complete arithmetic, output, flush, native cleanup and shutdown. No preparation or phase subtraction.',library_scope='All rebuilt subjects select installed GMP 6.3.0; loader evidence must confirm actual linkage separately.')
    def save():process.save(out/'results.json',report)
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);report['mutex_inode']=os.fstat(lock.fileno()).st_ino
        def telemetry():
            i=len(report['telemetry']);snap={}
            for label,cmd in [('power',['/usr/bin/pmset','-g','batt']),('settings',['/usr/bin/pmset','-g','custom']),('processes',['/bin/ps','-axo','pid,ppid,pgid,pcpu,comm'])]:
                d=out/f'telemetry-{i:03d}-{label}';r=process.execute(cmd,d,PLAN['environment'],lock)
                assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes()
                snap[label]=(d/'stdout.bin').read_text()
            assert "'AC Power'" in snap['power']
            assert {line.split()[-1] for line in snap['settings'].splitlines() if 'lowpowermode' in line}=={'0'}
            names={Path(line.split()[-1]).name for line in snap['processes'].splitlines()[1:] if line.split()}
            assert not names & {'rustc','cargo','clang','clang++','gcc','cc1','cc1plus','swiftc','javac'},'Competing compiler'
            report['telemetry'].append(snap);save()
        if mode=='time':
            q=json.loads((HERE/'qualification-v1/results.json').read_bytes());assert q['status']=='all-complete-outputs-pass'
            telemetry();rng=random.Random(20261022010);schedule=[]
            for trial in range(1,8):
                labels=list(COMMANDS);rng.shuffle(labels);schedule.extend((trial,label,10000) for label in labels)
        else:schedule=[(0,label,n) for n in (0,1,2,3,9,10,11,19,20,21,27,30,31,97,100,257,1000) for label in COMMANDS]
        try:
            for trial,label,n in schedule:
                assert all(process.sha(Path(p))==h for p,h in pins.items())
                if mode=='time':telemetry()
                want=reference(n)[0];d=out/f'{trial:02d}-{label}-n{n}'
                r=process.execute(COMMANDS[label]+[str(n)],d,PLAN['environment'],lock,deadline=120,quantitative=mode=='time')
                assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes() and (d/'stdout.bin').read_bytes()==want,(label,n)
                row=dict(round=trial,label=label,n=n,seconds=r['elapsed_seconds'],x_retained_mech_aot=r['elapsed_seconds']/.300272042,maximum_rss_bytes=r['maximum_rss_bytes'],stdout_sha256=process.sha(d/'stdout.bin'))
                report['samples'].append(row);save();print(json.dumps(row),flush=True)
            if mode=='time':
                report['summary']={}
                for label in COMMANDS:
                    times=[r['seconds'] for r in report['samples'] if r['label']==label]
                    report['summary'][label]=dict(median_seconds=statistics.median(times),stdev_seconds=statistics.stdev(times),x_retained_mech_aot=statistics.median(times)/.300272042)
                parent=report['summary']['mech-parent']['median_seconds']
                report['fresh_mech_aot_denominator_seconds']=parent
                for row in report['summary'].values():row['x_fresh_mech_aot']=row['median_seconds']/parent
                for row in report['samples']:row['x_fresh_mech_aot']=row['seconds']/parent
                telemetry()
            report['status']='all-complete-outputs-pass';save()
        except BaseException as e:report['status']='failed-not-admissible';report['error']=str(e);save();raise
if __name__=='__main__':main()
