"""Three shuffled sequential full-process observations per exact Janet source."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
from common import HERE,ROOT,PLAN,SOURCES,process,validate_success

N=50000000

def main():
    for name,pin in PLAN['pins'].items():
        p=Path(name) if name.startswith('/') else ROOT/name
        assert process.sha(p)==pin['sha256'],name
    catalog_path=ROOT/'data/benchmarks.json';catalog=json.loads(catalog_path.read_bytes())
    mech=catalog['programs']['nbody:pairwise-mass-tails']
    assert mech['algorithm']['full_work']['steps']==N and mech['seconds']==1.039486459
    evidence=ROOT/'archive/workloads/nbody/experiments/20261011-shared-products/replication-50m.json'
    assert process.sha(evidence)==mech['measured_backend']['evidence']['report_sha256']
    retained=json.loads(evidence.read_bytes())
    assert retained['steps']==N
    row=next(p for p in retained['programs'] if p['id']=='pairwise-seed8')
    assert len(row['sample_stdout'])==7 and len(set(row['sample_stdout']))==1
    expected=row['sample_stdout'][0].encode()
    case=dict(benchmark='nbody',case='full-50000000',expected_exit=0,validation='finite-two-energy-lines-within-1e-8',expected=dict(bytes=len(expected),sha256=hashlib.sha256(expected).hexdigest()))
    assert json.loads((HERE/'qualification-v1/results.json').read_bytes())['status']=='all-energy-work-and-complete-state-contracts-pass'
    assert json.loads((HERE/'perturbed-v1/results.json').read_bytes())['status']=='all-perturbed-state-bits-match-independent-reference'
    pins={str(p):process.sha(p) for p in [*SOURCES.values(),Path(PLAN['runtime']),Path(__file__),HERE/'common.py',HERE/'reference.py',HERE.parent/'knucleotide-bytes-v1/process.py',catalog_path,evidence,HERE/'qualify.py',HERE/'qualification-v1/results.json',HERE/'qualify_perturbed.py',HERE/'perturbed-v1/results.json']}
    output=HERE/'run-v1';output.mkdir(exist_ok=False)
    report=dict(status='running',n=N,samples=[],telemetry=[],benchmark_samples=0,chart_admission=False,pins=pins,expected_stdout=expected.decode(),output_contract=case,
                denominator=dict(kind='retained-same-input-Mech-AOT-median-not-fresh-paired-control',program=mech['key'],seconds=mech['seconds'],n=N),
                timing_boundary='Parent monotonic clock immediately before fork through observed exit; source parsing, bytecode compilation, VM startup, complete simulation, output and shutdown included. Exit observer polls independently of telemetry. Output validation, telemetry and cleanup excluded.',
                required_work=dict(steps=N,pair_interactions=10*N,position_components=15*N,bodies=5,initial_and_final_energy=True),
                thermal_frequency_logging=False)
    def save():process.save(output/'results.json',report)
    with Path(PLAN['common_mutex']).open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        report['mutex_inode']=os.fstat(lock.fileno()).st_ino
        assert report['mutex_inode']==Path(PLAN['common_mutex']).stat().st_ino
        def telemetry():
            index=len(report['telemetry']);snap={}
            for label,command in [('battery',['/usr/bin/pmset','-g','batt']),('settings',['/usr/bin/pmset','-g','custom']),('processes',['/bin/ps','-axo','pid,ppid,pgid,pcpu,comm'])]:
                d=output/f'telemetry-{index:04d}-{label}';r=process.execute(command,d,PLAN['environment'],lock)
                assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes()
                snap[label]=(d/'stdout.bin').read_text()
            report['telemetry'].append(snap);save()
            assert "'AC Power'" in snap['battery']
            modes=[line.split()[-1] for line in snap['settings'].splitlines() if 'lowpowermode' in line]
            assert modes and set(modes)=={'0'}
            names={Path(line.split()[-1]).name for line in snap['processes'].splitlines()[1:] if line.split()}
            assert not names & {'clang','clang++','rustc','cargo','gcc','g++','cc1','cc1plus','swiftc','javac','fsc','csc'},'Competing compiler detected'
        try:
            telemetry();rng=random.Random(2026102205)
            for sample in range(1,4):
                order=list(SOURCES);rng.shuffle(order)
                for label in order:
                    assert all(process.sha(Path(p))==h for p,h in pins.items())
                    telemetry();report['active']=dict(label=label,sample=sample);save()
                    d=output/f'{sample:02d}-{label}'
                    r=process.execute([PLAN['runtime'],'-R','-n',str(SOURCES[label]),str(N)],d,PLAN['environment'],lock,deadline=7200,monitor=telemetry,quantitative=True)
                    telemetry()
                    receipt=validate_success(case,(d/'stdout.bin').read_bytes(),(d/'stderr.bin').read_bytes(),r['exit_status'],expected)
                    observation=dict(sample=sample,label=label,seconds=r['elapsed_seconds'],x_mech_aot=r['elapsed_seconds']/mech['seconds'],maximum_rss_bytes=r['maximum_rss_bytes'],user_cpu_seconds=r['user_cpu_seconds'],system_cpu_seconds=r['system_cpu_seconds'],output_valid=True,output_contract=receipt)
                    report['samples'].append(observation);report['benchmark_samples']+=1;report['active']=None;save()
                    print(json.dumps(observation),flush=True)
            report['summary']={label:dict(median_seconds=statistics.median(r['seconds'] for r in report['samples'] if r['label']==label),stdev_seconds=statistics.stdev(r['seconds'] for r in report['samples'] if r['label']==label),maximum_rss_bytes=max(r['maximum_rss_bytes'] for r in report['samples'] if r['label']==label)) for label in SOURCES}
            for row in report['summary'].values():row['x_mech_aot']=row['median_seconds']/mech['seconds']
            report['status']='twelve-full-size-complete-process-outputs-pass';save()
        except BaseException as error:
            report['status']='failed-not-admissible';report['error']=str(error);save();raise

if __name__=='__main__':main()
