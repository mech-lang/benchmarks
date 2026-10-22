"""Seven shuffled serial fresh-process observations for five GMP-leaf spigot forms."""
import fcntl
import json
import os
from pathlib import Path
import random
import statistics
from common import HERE,ROOT,PLAN,SOURCES,process,validate_success

N=10000
ROUNDS=7

def main():
    for name,pin in PLAN['pins'].items():
        p=Path(name) if name.startswith('/') else ROOT/name
        assert process.sha(p)==pin['sha256'],name
    catalog=ROOT/'data/benchmarks.json';mech=json.loads(catalog.read_bytes())['programs']['pidigits:mech-pi-final-advance-signed']
    assert mech['seconds']==.300272042 and mech['algorithm']['full_work']['digits']==N and mech['algorithm']['full_work']['threads']==1
    work=json.loads((HERE/'full-work-v1/results.json').read_bytes());assert work['status']=='five-full-size-outputs-and-dual-extraction-work-counts-pass'
    assert json.loads((HERE/'qualification-v2/results.json').read_bytes())['status']=='all-complete-outputs-and-unbounded-integer-state-traces-pass'
    assert json.loads((HERE/'library-v2/results.json').read_bytes())['status']=='both-applications-load-pinned-gmp; loader-and-link-metadata-retained'
    expected=(HERE/'full-work-v1/expected.stdout').read_bytes();case=dict(benchmark='pidigits',case='full-10000',expected_exit=0,validation='exact-complete-bytes',expected=work['expected'])
    gmp=Path(PLAN['environment']['MECH_GMP_LIBRARY'])
    files=[*SOURCES.values(),Path(PLAN['runtime']),gmp,Path(__file__),HERE/'common.py',HERE.parent/'knucleotide-bytes-v1/process.py',catalog,HERE/'qualify.py',HERE/'qualification-v2/results.json',HERE/'check_full_work.py',HERE/'full-work-v1/results.json',HERE/'full-work-v1/expected.stdout',HERE/'check_libraries.py',HERE/'library-v2/results.json']
    pins={str(p):process.sha(p) for p in files};out=HERE/'run-v1';out.mkdir(exist_ok=False)
    report=dict(status='running',n=N,rounds=ROUNDS,samples=[],telemetry=[],benchmark_samples=0,chart_admission=False,pins=pins,expected_stdout_sha256=work['expected']['sha256'],output_contract=case,required_work=work['reference_counts'],
                denominator=dict(kind='retained-same-input-Mech-AOT-median-not-fresh-paired-control',program=mech['key'],seconds=mech['seconds'],n=N),
                library=dict(path=str(gmp),sha256=process.sha(gmp),version='6.3.0',boundary='General unmodified GMP arithmetic leaves only; single-threaded advance, both extracts, selection and output remain in Janet.'),
                timing_boundary='Parent monotonic clock before fork through independently observed exit; VM startup, source/FFI compilation, library loading, all spigot arithmetic/output, mpz cleanup and shutdown included. Output checks and group cleanup follow exit. Live read-only telemetry is concurrent host activity inside observed wall time; post-exit callbacks do not extend the independent exit timestamp.',thermal_frequency_logging=False)
    def save():process.save(out/'results.json',report)
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);report['mutex_inode']=os.fstat(lock.fileno()).st_ino
        assert report['mutex_inode']==Path(PLAN['common_mutex']).stat().st_ino
        def telemetry():
            index=len(report['telemetry']);snap={}
            for label,command in [('battery',['/usr/bin/pmset','-g','batt']),('settings',['/usr/bin/pmset','-g','custom']),('processes',['/bin/ps','-axo','pid,ppid,pgid,pcpu,comm'])]:
                d=out/f'telemetry-{index:04d}-{label}';r=process.execute(command,d,PLAN['environment'],lock)
                assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes();snap[label]=(d/'stdout.bin').read_text()
            report['telemetry'].append(snap);save();assert "'AC Power'" in snap['battery']
            modes=[line.split()[-1] for line in snap['settings'].splitlines() if 'lowpowermode' in line];assert modes and set(modes)=={'0'}
            names={Path(line.split()[-1]).name for line in snap['processes'].splitlines()[1:] if line.split()}
            assert not names & {'clang','clang++','rustc','cargo','gcc','g++','cc1','cc1plus','swiftc','javac','fsc','csc'},'Competing compiler detected'
        try:
            telemetry();rng=random.Random(2026102207)
            for sample in range(1,ROUNDS+1):
                order=list(SOURCES);rng.shuffle(order)
                for label in order:
                    assert all(process.sha(Path(p))==h for p,h in pins.items());telemetry();report['active']=dict(label=label,sample=sample);save()
                    d=out/f'{sample:02d}-{label}';r=process.execute([PLAN['runtime'],'-R','-n',str(SOURCES[label]),str(N)],d,PLAN['environment'],lock,deadline=300,monitor=telemetry,quantitative=True)
                    telemetry();receipt=validate_success(case,(d/'stdout.bin').read_bytes(),(d/'stderr.bin').read_bytes(),r['exit_status'],expected)
                    row=dict(sample=sample,label=label,seconds=r['elapsed_seconds'],x_mech_aot=r['elapsed_seconds']/mech['seconds'],maximum_rss_bytes=r['maximum_rss_bytes'],user_cpu_seconds=r['user_cpu_seconds'],system_cpu_seconds=r['system_cpu_seconds'],output_valid=True,output_contract=receipt)
                    report['samples'].append(row);report['benchmark_samples']+=1;report['active']=None;save();print(json.dumps({k:v for k,v in row.items() if k!='output_contract'}),flush=True)
            report['summary']={label:dict(median_seconds=statistics.median(r['seconds'] for r in report['samples'] if r['label']==label),stdev_seconds=statistics.stdev(r['seconds'] for r in report['samples'] if r['label']==label),maximum_rss_bytes=max(r['maximum_rss_bytes'] for r in report['samples'] if r['label']==label)) for label in SOURCES}
            for row in report['summary'].values():row['x_mech_aot']=row['median_seconds']/mech['seconds']
            report['status']='35-full-size-complete-process-outputs-pass';save()
        except BaseException as error:report['status']='failed-not-admissible';report['error']=str(error);save();raise

if __name__=='__main__':main()
