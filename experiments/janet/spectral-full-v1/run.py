"""Three serial full-size parent/candidate observations; never chart admission."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import statistics
import sys
import process

ROOT = process.ROOT
HERE = Path(__file__).resolve().parent
EXPECTED = dict(bytes=12, sha256='f9d5b5e3eb7657cf1bbba4cc856651864df9cd9fd9a6be9b9bc5fcbb67150deb')

def main():
    plan_path = ROOT/'experiments/janet/bounded-v1/plan-v1.json'
    plan = json.loads(plan_path.read_bytes())
    for name, pin in plan['pins'].items():
        p = Path(name) if name.startswith('/') else ROOT/name
        assert process.sha(p) == pin['sha256'], name
    catalog = json.loads((ROOT/'data/benchmarks.json').read_bytes())
    mech = catalog['programs']['spectralnorm:mech-integer-simd1-u4-r4-p8-g8']
    assert mech['algorithm']['full_work']['n'] == 5500
    sources = {label: ROOT/f'experiments/janet/{version}/spectralnorm.janet'
               for label, version in [('parent','source-v2'),('candidate','source-v3')]}
    pins = {str(p):process.sha(p) for p in [*sources.values(), Path(plan['runtime']), Path(__file__), HERE/'process.py', ROOT/'data/benchmarks.json']}
    output = HERE/'run-v1'; output.mkdir(exist_ok=False)
    report = dict(status='running', n=5500, samples=[], telemetry=[], benchmark_samples=0,
                  chart_admission=False, pins=pins, expected=EXPECTED, plan_sha256=process.sha(plan_path),
                  denominator=dict(kind='retained-full-size-Mech-AOT-median-not-fresh-paired-control',
                                   program=mech['key'], seconds=mech['seconds'], n=5500),
                  timing_boundary='Parent monotonic clock immediately before fork through observed exit; startup/source parsing/VM/work/output/shutdown included. Dedicated exit observer polls at 1ms independently of telemetry; output hashing and group cleanup excluded.',
                  thermal_frequency_logging=False)
    def save(): process.save(output/'results.json', report)
    with Path(plan['common_mutex']).open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        report['mutex_inode'] = os.fstat(lock.fileno()).st_ino
        assert report['mutex_inode'] == Path(plan['common_mutex']).stat().st_ino
        def telemetry():
            index = len(report['telemetry'])
            snap = {}
            for label, command in [('battery',['/usr/bin/pmset','-g','batt']),('settings',['/usr/bin/pmset','-g','custom']),('processes',['/bin/ps','-axo','pid,ppid,pgid,pcpu,comm'])]:
                d = output/f'telemetry-{index:04d}-{label}'
                r = process.execute(command,d,plan['environment'],lock)
                assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes()
                snap[label]=(d/'stdout.bin').read_text()
            report['telemetry'].append(snap); save()
            assert "'AC Power'" in snap['battery']
            modes=[line.split()[-1] for line in snap['settings'].splitlines() if 'lowpowermode' in line]
            assert modes and set(modes)=={'0'}
            names={Path(line.split()[-1]).name for line in snap['processes'].splitlines()[1:] if line.split()}
            assert not names & {'clang','clang++','rustc','cargo','gcc','g++','cc1','cc1plus','swiftc','javac','fsc','csc'}, 'Competing compiler detected'
        try:
            telemetry()
            rng=random.Random(20261022)
            for sample in range(1,4):
                order=list(sources); rng.shuffle(order)
                for label in order:
                    assert all(process.sha(Path(p))==h for p,h in pins.items())
                    telemetry()
                    report['active']=dict(label=label,sample=sample);save()
                    d=output/f'{sample:02d}-{label}'
                    command=[plan['runtime'],'-R','-n',str(sources[label]),'5500']
                    r=process.execute(command,d,plan['environment'],lock,deadline=7200,monitor=telemetry)
                    telemetry()
                    assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes()
                    assert (d/'stdout.bin').stat().st_size==EXPECTED['bytes'] and process.sha(d/'stdout.bin')==EXPECTED['sha256']
                    observation=dict(sample=sample,label=label,seconds=r['elapsed_seconds'],x_mech_aot=r['elapsed_seconds']/mech['seconds'],output_valid=True)
                    report['samples'].append(observation);report['benchmark_samples']+=1;report['active']=None;save()
                    print(json.dumps(observation),flush=True)
            report['summary']={label:dict(median_seconds=statistics.median(r['seconds'] for r in report['samples'] if r['label']==label), stdev_seconds=statistics.stdev(r['seconds'] for r in report['samples'] if r['label']==label)) for label in sources}
            for row in report['summary'].values(): row['x_mech_aot']=row['median_seconds']/mech['seconds']
            report['status']='six-full-size-complete-process-outputs-pass';save()
        except BaseException as error:
            report['status']='failed-not-admissible';report['error']=str(error);save();raise

if __name__=='__main__': main()
