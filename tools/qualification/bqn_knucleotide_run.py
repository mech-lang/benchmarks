"""Serial, source-pinned BQN k-nucleotide qualification and matched timings."""
import argparse
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import random
import shutil
import statistics
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'experiments/bqn/optimization-v1'
spec = importlib.util.spec_from_file_location('bqn_process', ROOT/'tools/qualification/lean_run.py')
process = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = process
spec.loader.exec_module(process)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def atom(path, value):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.replace(path)


def power():
    battery = subprocess.check_output(['/usr/bin/pmset','-g','batt'], text=True)
    settings = subprocess.check_output(['/usr/bin/pmset','-g','custom'], text=True)
    assert "'AC Power'" in battery and all(line.split()[-1] == '0' for line in settings.splitlines() if 'lowpowermode' in line)
    return dict(battery=battery, settings=settings)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', nargs='+', required=True)
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--expected', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--samples', type=int, default=1)
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--runtime', type=Path, default=HERE/'.build/CBQN/BQN')
    parser.add_argument('--profile', action='store_true')
    parser.add_argument('--work-witness', action='store_true', help='Untimed hash-work tracing with the separate diagnostic runtime')
    args = parser.parse_args()
    assert args.samples > 0 and not args.output.exists()
    assert not (args.profile and args.work_witness)
    if args.work_witness:
        args.runtime = HERE/'.build/CBQN-witness/BQN'
    sources = {name: HERE/'sources'/name for name in args.sources}
    runtime = args.runtime.resolve()
    pins = {str(p.relative_to(ROOT)): sha(p) for p in [*sources.values(), HERE/'stdlib/standard.bqn', HERE/'stdlib/native.c', HERE/'stdlib/khash.h', HERE/'stdlib/libarray-standard.dylib', runtime]}
    full = args.expected is None
    expected = dict(bytes=259, sha256=process.FULL['knucleotide'][2]) if full else dict(bytes=args.expected.stat().st_size, sha256=sha(args.expected))
    args.output.mkdir(parents=True)
    snapshot = args.output/'sources'; snapshot.mkdir()
    for path in sources.values(): shutil.copyfile(path, snapshot/path.name)
    report = dict(schema='bqn-knucleotide-execution.v1', status='RUNNING', controller_sha256=sha(__file__),
        started_utc=process.now(), source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
        pins=pins,input=dict(path=str(args.input),bytes=args.input.stat().st_size,sha256=sha(args.input)),expected=expected,
        full_workload=full,chart_admission=False,diagnostic_profile=args.profile,diagnostic_work_witness=args.work_witness,
        timing_boundary='Fresh process through exit, including startup, input, all language workers and output; no compilation, hashing, validation or profiling in admitted samples.',
        host=dict(cpu=subprocess.check_output(['/usr/sbin/sysctl','-n','machdep.cpu.brand_string'],text=True).strip(),os=subprocess.check_output(['/usr/bin/sw_vers'],text=True)),
        cases=[],orders=[])
    with open('/tmp/mech-clbg-timing.lock','a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        report['common_mutex_inode']=__import__('os').fstat(lock.fileno()).st_ino
        rng=random.Random(20261020)
        for sample in range(1,args.samples+1):
            order=list(sources);rng.shuffle(order);report['orders'].append(order)
            for name in order:
                assert all(sha(ROOT/p)==h for p,h in pins.items())
                before=power()
                command=[str(runtime)]+(['-Xprofile'] if args.profile else [])+[str(sources[name].resolve())]
                if args.work_witness:command=['/usr/bin/env','MECH_BQN_COUNT_WITNESS=1',*command]
                report['active']=dict(source=name,sample=sample);atom(args.output/'report.json',report)
                directory=args.output/f'{sample:02d}-{Path(name).stem}'
                record=process.one(command,args.input.resolve(),directory,args.timeout)
                after=power()
                valid=record['exit_code']==0 and record['stdout']['bytes']==expected['bytes'] and record['stdout']['sha256']==expected['sha256']
                if not (args.profile or args.work_witness):valid=valid and record['stderr']['bytes']==0
                record.update(source=name,sample=sample,output_valid=valid,power_before=before,power_after=after)
                report['cases'].append(record);report['active']=None
                atom(args.output/'report.json',report)
                print(json.dumps(dict(source=name,sample=sample,seconds=record['elapsed_seconds'],valid=valid,stderr_bytes=record['stderr']['bytes'])),flush=True)
                if not valid:
                    report['status']='FAILED';atom(args.output/'report.json',report)
                    print((directory/'stderr.bin').read_text(errors='replace')[:2000],flush=True)
                    raise SystemExit(1)
                assert all(sha(ROOT/p)==h for p,h in pins.items())
        report['status']='PASSED';report['finished_utc']=process.now()
        report['medians']={name:statistics.median(c['elapsed_seconds'] for c in report['cases'] if c['source']==name) for name in sources}
        atom(args.output/'report.json',report)


if __name__=='__main__':main()
