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
EXPECTED = dict(bytes=259, sha256='f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7')

def main():
    plan_path = ROOT/'experiments/janet/bounded-v1/plan-v1.json'
    plan = json.loads(plan_path.read_bytes())
    for name, pin in plan['pins'].items():
        p = Path(name) if name.startswith('/') else ROOT/name
        assert process.sha(p) == pin['sha256'], name
    catalog = json.loads((ROOT/'data/benchmarks.json').read_bytes())
    mech = catalog['programs']['knucleotide:mech-compact-final-std1-simd0-p4']
    assert mech['algorithm']['full_work']['three_sequence_length'] == 125000000
    qualification=json.loads((HERE/'modulo-qualification-v1/results.json').read_bytes())
    assert qualification['status']=='28-complete-outputs-and-196-full-histograms-pass'
    fixture=json.loads((HERE/'input-generation-v1/input.json').read_bytes())
    stdin=Path(fixture['path'])
    assert fixture['bytes']==254166745 and fixture['sha256']=='3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'
    assert stdin.stat().st_size==fixture['bytes'] and process.sha(stdin)==fixture['sha256']
    domain=json.loads((HERE/'native-domain-v1/result.json').read_bytes())
    assert domain['status']=='72360-native-domain-checks-pass'
    assert domain['source_sha256']==process.sha(HERE/'modulo-domain.janet')
    assert domain['runtime_sha256']==process.sha(Path(plan['runtime']))
    sources = {n:HERE/'sources'/(n+'.janet') for n in ('byte-modulo','line-modulo')}
    pins = {str(p):process.sha(p) for p in [*sources.values(),Path(plan['runtime']),Path(__file__),HERE/'process.py',ROOT/'data/benchmarks.json',HERE/'qualify_modulo.py',HERE/'modulo-qualification-v1/results.json',HERE/'native-domain-v1/result.json',HERE/'modulo-domain.janet',HERE/'run-v1/results.json',stdin]}
    output = HERE/'modulo-run-v1'; output.mkdir(exist_ok=False)
    report = dict(status='running', n=25000000, samples=[], telemetry=[], benchmark_samples=0,
                  chart_admission=False, pins=pins, expected=EXPECTED, plan_sha256=process.sha(plan_path),
                  denominator=dict(kind='retained-full-size-Mech-AOT-median-not-fresh-paired-control',
                                   program=mech['key'], seconds=mech['seconds'], n=25000000),
                  timing_boundary='Parent monotonic clock immediately before fork through observed exit; startup/source parsing/VM/work/output/shutdown included. Dedicated exit observer polls at 1ms independently of telemetry; output hashing and group cleanup excluded.',
                  thermal_frequency_logging=False,input=fixture,three_sequence_length=125000000,full_histogram_updates=874999961,comparison_cohort=dict(path='run-v1/results.json',sha256=process.sha(HERE/'run-v1/results.json')))
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
                    command=[plan['runtime'],'-R','-n',str(sources[label])]
                    r=process.execute(command,d,plan['environment'],lock,stdin=stdin,deadline=7200,monitor=telemetry,quantitative=True)
                    telemetry()
                    assert r['exit_status']==0 and not (d/'stderr.bin').read_bytes()
                    assert (d/'stdout.bin').stat().st_size==EXPECTED['bytes'] and process.sha(d/'stdout.bin')==EXPECTED['sha256']
                    observation=dict(sample=sample,label=label,seconds=r['elapsed_seconds'],x_mech_aot=r['elapsed_seconds']/mech['seconds'],maximum_rss_bytes=r['maximum_rss_bytes'],user_cpu_seconds=r['user_cpu_seconds'],system_cpu_seconds=r['system_cpu_seconds'],output_valid=True)
                    report['samples'].append(observation);report['benchmark_samples']+=1;report['active']=None;save()
                    print(json.dumps(observation),flush=True)
            report['summary']={label:dict(median_seconds=statistics.median(r['seconds'] for r in report['samples'] if r['label']==label), stdev_seconds=statistics.stdev(r['seconds'] for r in report['samples'] if r['label']==label)) for label in sources}
            for row in report['summary'].values(): row['x_mech_aot']=row['median_seconds']/mech['seconds']
            for label in sources:
                report['summary'][label]['maximum_rss_bytes']=max(r['maximum_rss_bytes'] for r in report['samples'] if r['label']==label)
            report['status']='six-modulo-full-size-complete-process-outputs-pass';save()
        except BaseException as error:
            report['status']='failed-not-admissible';report['error']=str(error);save();raise

if __name__=='__main__': main()
