"""Three shuffled serial full-process samples for five ordinary Janet tree variants."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
from common import HERE,ROOT,PLAN,SOURCES,process,validate_success,expected,work

SOURCES={**SOURCES,**{name:HERE/'sources'/(name+'.janet') for name in ('unrolled','threaded-unrolled')}}
N=21

def main():
    for name,pin in PLAN['pins'].items():
        p=Path(name) if name.startswith('/') else ROOT/name
        assert process.sha(p)==pin['sha256'],name
    catalog_path=ROOT/'data/benchmarks.json';catalog=json.loads(catalog_path.read_bytes());mech=catalog['programs']['binarytrees:mech-binarytrees-parallel']
    main_nodes,short=work(N);assert main_nodes+short==613766494
    assert mech['seconds']==.394411208 and mech['algorithm']['full_work']['maximum_depth']==N and mech['algorithm']['full_work']['nodes_constructed_and_walked']==main_nodes+short
    requirements=[('qualification-v1','all-bounded-outputs-and-distinct-node-partitions-pass'),('unrolled-qualification-v1','all-bounded-outputs-and-distinct-node-partitions-pass'),('failure-v1','owned-worker-error-propagates-without-depth-summaries'),('partition-domain-v1','all-native-bounds-match-exact-integer-partitions')]
    for directory,status in requirements:assert json.loads((HERE/directory/'results.json').read_bytes())['status']==status
    want=expected(N);case=dict(benchmark='binarytrees',case='full-depth21',expected_exit=0,validation='exact-complete-bytes',expected=dict(bytes=len(want),sha256=hashlib.sha256(want).hexdigest()))
    files=[*SOURCES.values(),Path(PLAN['runtime']),Path(__file__),HERE/'common.py',HERE.parent/'knucleotide-bytes-v1/process.py',catalog_path,HERE/'qualify.py',HERE/'qualify_unrolled.py',HERE/'check_failure.py',HERE/'check_partitions.py',*[HERE/d/'results.json' for d,_ in requirements]]
    pins={str(p):process.sha(p) for p in files}
    output=HERE/'run-v1';output.mkdir(exist_ok=False)
    report=dict(status='running',n=N,samples=[],telemetry=[],benchmark_samples=0,chart_admission=False,pins=pins,expected_stdout=want.decode(),output_contract=case,
                denominator=dict(kind='retained-same-input-Mech-AOT-median-not-fresh-paired-control',program=mech['key'],seconds=mech['seconds'],n=N,allocation_policy=mech['algorithm']['allocation_policy']),
                subject_allocation_policy='Default Janet GC; fresh mutable two-reference arrays for every leaf and interior node; no pool, GC tuning or shared nodes.',
                timing_boundary='Parent monotonic clock immediately before fork through independently observed process exit; source parsing, bytecode compilation, VM/worker startup, all allocation/traversal/output and shutdown included. Output checking and process cleanup follow exit. Periodic read-only telemetry during a live subject can contribute contention inside observed wall time; later callbacks do not extend the independent exit timestamp.',
                required_work=dict(maximum_depth=N,main_stretch_and_retained_nodes=main_nodes,short_lived_nodes=short,nodes_constructed=main_nodes+short,nodes_walked=main_nodes+short),
                thermal_frequency_logging=False,maximum_application_threads=8)
    def save():process.save(output/'results.json',report)
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);report['mutex_inode']=os.fstat(lock.fileno()).st_ino
        assert report['mutex_inode']==Path(PLAN['common_mutex']).stat().st_ino
        def telemetry():
            index=len(report['telemetry']);snap={}
            commands=[('battery',['/usr/bin/pmset','-g','batt']),('settings',['/usr/bin/pmset','-g','custom']),('processes',['/bin/ps','-axo','pid,ppid,pgid,pcpu,comm']),('memory',['/usr/bin/vm_stat']),('swap',['/usr/sbin/sysctl','vm.swapusage'])]
            for label,cmd in commands:
                d=output/f'telemetry-{index:04d}-{label}';r=process.execute(cmd,d,PLAN['environment'],lock)
                assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes();snap[label]=(d/'stdout.bin').read_text()
            report['telemetry'].append(snap);save()
            assert "'AC Power'" in snap['battery']
            modes=[line.split()[-1] for line in snap['settings'].splitlines() if 'lowpowermode' in line]
            assert modes and set(modes)=={'0'}
            names={Path(line.split()[-1]).name for line in snap['processes'].splitlines()[1:] if line.split()}
            assert not names & {'clang','clang++','rustc','cargo','gcc','g++','cc1','cc1plus','swiftc','javac','fsc','csc'},'Competing compiler detected'
        try:
            telemetry();rng=random.Random(2026102206)
            for sample in range(1,4):
                order=list(SOURCES);rng.shuffle(order)
                for label in order:
                    assert all(process.sha(Path(p))==h for p,h in pins.items())
                    telemetry();report['active']=dict(label=label,sample=sample);save();d=output/f'{sample:02d}-{label}'
                    r=process.execute([PLAN['runtime'],'-R','-n',str(SOURCES[label]),str(N)],d,PLAN['environment'],lock,deadline=7200,monitor=telemetry,quantitative=True)
                    telemetry();receipt=validate_success(case,(d/'stdout.bin').read_bytes(),(d/'stderr.bin').read_bytes(),r['exit_status'],want)
                    observation=dict(sample=sample,label=label,seconds=r['elapsed_seconds'],x_mech_aot=r['elapsed_seconds']/mech['seconds'],maximum_rss_bytes=r['maximum_rss_bytes'],user_cpu_seconds=r['user_cpu_seconds'],system_cpu_seconds=r['system_cpu_seconds'],output_valid=True,output_contract=receipt)
                    report['samples'].append(observation);report['benchmark_samples']+=1;report['active']=None;save();print(json.dumps(observation),flush=True)
            report['summary']={label:dict(median_seconds=statistics.median(r['seconds'] for r in report['samples'] if r['label']==label),stdev_seconds=statistics.stdev(r['seconds'] for r in report['samples'] if r['label']==label),maximum_rss_bytes=max(r['maximum_rss_bytes'] for r in report['samples'] if r['label']==label)) for label in SOURCES}
            for row in report['summary'].values():row['x_mech_aot']=row['median_seconds']/mech['seconds']
            report['status']='fifteen-full-size-complete-process-outputs-pass';save()
        except BaseException as error:report['status']='failed-not-admissible';report['error']=str(error);save();raise

if __name__=='__main__':main()
