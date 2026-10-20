"""Compare retained Ruby submissions with isolated YJIT/ZJIT processes.

No source rewriting or warm-up exclusion. Historical YJIT samples are reusable
only when their recorded executable digest matches the executable used here.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import threading
import time

from lean_run import FULL, atom, energy_output, now, sha

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'experiments/ruby-jit'
RUBY = Path('/opt/homebrew/bin/ruby').resolve()
STDIN = {'knucleotide', 'regexredux', 'revcomp'}
SMALL = dict(nbody=10000, mandelbrot=64, spectralnorm=100,
             fannkuchredux=7, fasta=1000, binarytrees=9, pidigits=1000)
ENV = dict(PATH='/usr/bin:/bin', LC_ALL='C', LANG='C', TZ='UTC')


def prepare(path):
    data = json.loads((ROOT / 'data/benchmarks.json').read_text())
    reproduction = json.loads((ROOT / 'data/reproducibility.json').read_text())
    catalog = {**data.get('program_inventory', {}), **data['programs']}
    original_plan = HERE / 'plan-v1.json'
    original_keys = {p['key'] for p in json.loads(original_plan.read_text())['profiles']} if original_plan.exists() else None
    profiles = []
    for key, p in catalog.items():
        if p['language'] != 'ruby' or (original_keys is not None and key not in original_keys):
            continue
        r = reproduction['programs'][key]
        assert len(p['files']) == 1 and '--yjit' in r['command']
        source = data['files'][p['files'][0]]
        relative = source['archive_path']
        assert sha(ROOT / relative) == p['files'][0]
        report = ROOT / data['archive_paths'][p['report']]
        old = json.loads(report.read_text())
        toolchain = old.get('toolchains', {}).get('ruby')
        argv = []
        for argument in r['command'][1:]:
            if argument == '--yjit':
                argv.append('{jit}')
            elif argument.endswith('.rb'):
                argv.append(str(ROOT / relative) if argument.endswith(source['name'])
                            else str(ROOT / 'archive/comparisons/fast-scripting/linux_cpuinfo.rb'))
            else:
                argv.append(argument)
        environment = dict(ENV)
        environment.update(r['environment'])
        if 'CLBG_CPUINFO_FILE' in environment:
            environment['CLBG_CPUINFO_FILE'] = str(ROOT / 'archive/comparisons/fast-scripting' /
                                                  Path(environment['CLBG_CPUINFO_FILE']).name)
        support = [a for a in argv if a.endswith('.rb') and a != str(ROOT / relative)]
        if 'CLBG_CPUINFO_FILE' in environment:
            support.append(environment['CLBG_CPUINFO_FILE'])
        profiles.append(dict(key=key, id=p['id'], benchmark=p['benchmark'],
            source_path=relative, source_sha256=p['files'][0], loc=p['loc'], argv=argv,
            environment=environment, support={str(Path(s).relative_to(ROOT)): sha(s) for s in support},
            historical_yjit=dict(samples=p['samples'], seconds=p['seconds'],
                report=str(report.relative_to(ROOT)), report_sha256=sha(report),
                recorded_toolchain=toolchain, recorded_command=r['command'],
                reusable=isinstance(toolchain, dict) and toolchain.get('sha256') == sha(RUBY))))
    assert len(profiles) == 19 and {p['benchmark'] for p in profiles} == set(FULL)
    profiles.sort(key=lambda p: p['historical_yjit']['seconds'])
    probes = {}
    for mode in ('yjit', 'zjit'):
        command = [str(RUBY), '--' + mode, '-rjson', '-e',
            'puts({description:RUBY_DESCRIPTION,yjit:RubyVM::YJIT.enabled?,zjit:RubyVM::ZJIT.enabled?}.to_json)']
        probes[mode] = json.loads(subprocess.check_output(command, env=ENV, text=True))
        assert probes[mode][mode] and not probes[mode]['zjit' if mode == 'yjit' else 'yjit']
    metadata = subprocess.check_output([str(RUBY), '-rrbconfig', '-rjson', '-e',
        'puts RbConfig::CONFIG.slice("configure_args","CC","CFLAGS","host","arch","RUBY_SO_NAME").to_json'], env=ENV, text=True)
    plan = dict(schema='ruby-jit-plan.v1', created_utc=now(),
        source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        catalog_sha256=sha(ROOT / 'data/benchmarks.json'), profiles=profiles,
        runtime=dict(path=str(RUBY), sha256=sha(RUBY), probes=probes, build=json.loads(metadata)),
        controller_sha256=sha(__file__), full_workloads=FULL,
        host=dict(os=subprocess.check_output(['/usr/bin/sw_vers'], text=True),
                  hardware=subprocess.check_output(['/usr/sbin/sysctl', '-n', 'machdep.cpu.brand_string'], text=True).strip(),
                  machine=os.uname().machine),
        timing_boundary='Fresh process through exit: Ruby startup, JIT warm-up/compilation, source loading, worker creation, input, all required work, complete stdout, flushing and shutdown. Hashing and comparisons are outside timing.',
        comparison_note='Historical YJIT observations keep their original dates. Reuse requires an exact recorded runtime digest. Where that digest was not recorded, fresh YJIT samples are collected. ZJIT uses the same source, parameters, input and worker policy. No other language is remeasured.')
    atom(path, plan)
    print(json.dumps(dict(profiles=len(profiles), reused_yjit=sum(p['historical_yjit']['reusable'] for p in profiles), runtime=plan['runtime'])))


def execute(command, environment, stdin, directory, timeout=21600):
    directory.mkdir(parents=True, exist_ok=False)
    record = dict(command=command, environment=environment, stdin=str(stdin), started_utc=now())
    finished = threading.Event()
    child = [None]
    expired = [False]
    def watchdog():
        if not finished.wait(timeout):
            expired[0] = True
            if child[0] is not None:
                try:
                    os.killpg(child[0], signal.SIGKILL)
                except ProcessLookupError:
                    pass
    watcher = threading.Thread(target=watchdog, daemon=True)
    watcher.start()
    try:
        with open(stdin, 'rb') as inp, (directory / 'stdout.bin').open('wb') as out, (directory / 'stderr.bin').open('wb') as err:
            start = time.perf_counter_ns()
            proc = subprocess.Popen(command, cwd=ROOT, env=environment, stdin=inp,
                                    stdout=out, stderr=err, start_new_session=True)
            child[0] = proc.pid
            pid, status, usage = os.wait4(proc.pid, 0)
            end = time.perf_counter_ns()
            proc.returncode = os.waitstatus_to_exitcode(status)
        assert pid == proc.pid
        record.update(pid=pid, exit_code=proc.returncode, elapsed_seconds=(end-start)/1e9,
                      user_seconds=usage.ru_utime, system_seconds=usage.ru_stime,
                      maximum_rss_bytes=usage.ru_maxrss, timed_out=expired[0])
    finally:
        finished.set()
        watcher.join()
    record['finished_utc'] = now()
    for stream in ('stdout', 'stderr'):
        path = directory / (stream + '.bin')
        record[stream] = dict(path=str(path.relative_to(ROOT)), bytes=path.stat().st_size, sha256=sha(path))
    atom(directory / 'process.json', record)
    return record


def command(profile, mode, n):
    return [str(RUBY)] + ['--' + mode if a == '{jit}' else str(n) if a == '{n}' else a for a in profile['argv']]


def check_pins(plan):
    assert sha(RUBY) == plan['runtime']['sha256']
    assert sha(__file__) == plan['controller_sha256']
    for p in plan['profiles']:
        assert sha(ROOT / p['source_path']) == p['source_sha256']
        assert all(sha(ROOT / name) == wanted for name, wanted in p['support'].items())


def run(args):
    plan = json.loads(args.plan.read_text())
    check_pins(plan)
    path = args.output / 'report.json'
    if args.resume:
        report = json.loads(path.read_text())
        assert report['plan_sha256'] == sha(args.plan) and report['mode'] == args.mode
    else:
        args.output.mkdir(parents=True, exist_ok=False)
        report = dict(schema='ruby-jit-execution.v1', mode=args.mode, status='RUNNING',
                      started_utc=now(), plan_sha256=sha(args.plan), cases=[], active=None,
                      timing_processes_serial=True, chart_admission=False)
    with open('/tmp/mech-clbg-timing.lock', 'a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        report['common_mutex_inode'] = os.fstat(lock.fileno()).st_ino
        if args.mode == 'bounded':
            seed = next(p for p in plan['profiles'] if p['id'] == 'fasta-ruby-2')
            seed_dir = args.output / 'input-preparation'
            if not seed_dir.exists():
                record = execute(command(seed, 'yjit', 1000), seed['environment'], '/dev/null', seed_dir, 120)
                assert record['exit_code'] == 0 and record['stderr']['bytes'] == 0
            stdin_large = stdin_regex = seed_dir / 'stdout.bin'
        else:
            prerequisite = json.loads(args.bounded_report.read_text())
            assert prerequisite['status'] == 'PASSED' and prerequisite['plan_sha256'] == sha(args.plan)
            assert len(prerequisite['cases']) == 38
            report['bounded_report'] = dict(path=str(args.bounded_report.relative_to(ROOT)), sha256=sha(args.bounded_report))
            stdin_large = ROOT / 'experiments/lean4/.build/inputs/n25000000.fasta'
            stdin_regex = ROOT / 'experiments/lean4/.build/inputs/n5000000.fasta'
        inputs = {str(p.relative_to(ROOT)): dict(sha256=sha(p), bytes=p.stat().st_size)
                  for p in (stdin_large, stdin_regex)}
        if 'inputs' in report:
            assert report['inputs'] == inputs
        report['inputs'] = inputs
        completed = {(c['key'], c['jit'], c['sample']) for c in report['cases']}
        for p in plan['profiles']:
            b = p['benchmark']
            modes = ['yjit', 'zjit'] if args.mode == 'bounded' or not p['historical_yjit']['reusable'] else ['zjit']
            for sample in range(1, 2 if args.mode == 'bounded' else 4):
                for mode in modes:
                    if (p['key'], mode, sample) in completed:
                        continue
                    check_pins(plan)
                    power = dict(before=subprocess.check_output(['/usr/bin/pmset', '-g', 'batt'], text=True),
                                 settings=subprocess.check_output(['/usr/bin/pmset', '-g', 'custom'], text=True))
                    assert 'AC Power' in power['before'] and 'lowpowermode         0' in power['settings']
                    rows = subprocess.check_output(['/bin/ps', '-axo', 'pid,comm'], text=True).splitlines()[1:]
                    forbidden = {'ruby','cargo','rustc','clang','clang++','cc','lean','leanc','lake','julia','hyperfine','luau-host','luau-regex','luau-bigint'}
                    competitors = [r for r in rows if len(r.split(maxsplit=1)) == 2 and Path(r.split(maxsplit=1)[1]).name in forbidden]
                    assert not competitors, competitors
                    power['competing_processes_before'] = competitors
                    report['active'] = dict(key=p['key'], jit=mode, sample=sample, started_utc=now())
                    atom(path, report)
                    directory = args.output / f'{len(report["cases"])+1:03d}-{p["id"]}-{mode}-{sample}'
                    stdin = (stdin_regex if b == 'regexredux' else stdin_large) if b in STDIN else Path('/dev/null')
                    n = SMALL.get(b, 0) if args.mode == 'bounded' else FULL[b][0]
                    record = execute(command(p, mode, n), p['environment'], stdin, directory, 120 if args.mode == 'bounded' else 21600)
                    valid = record['exit_code'] == 0 and record['stderr']['bytes'] == 0 and not record['timed_out']
                    if args.mode == 'bounded':
                        if mode == 'zjit':
                            reference = next(c for c in report['cases'] if c['key'] == p['key'] and c['jit'] == 'yjit')
                            valid = valid and record['stdout']['sha256'] == reference['stdout']['sha256'] and record['stdout']['bytes'] == reference['stdout']['bytes']
                    elif b == 'nbody':
                        valid = valid and energy_output((directory/'stdout.bin').read_bytes(), b'-0.169075164\n-0.169059907\n')
                    else:
                        valid = valid and record['stdout']['bytes'] == FULL[b][1] and record['stdout']['sha256'] == FULL[b][2]
                    power['after'] = subprocess.check_output(['/usr/bin/pmset', '-g', 'batt'], text=True)
                    valid = valid and 'AC Power' in power['after']
                    record.update(key=p['key'], benchmark=b, jit=mode, sample=sample, n=n, valid=valid,
                                  source_sha256=p['source_sha256'], runtime_sha256=plan['runtime']['sha256'], power=power)
                    atom(directory/'process.json', record)
                    report['cases'].append(record)
                    report['active'] = None
                    atom(path, report)
                    print(f'{len(report["cases"])} {p["id"]} {mode} {sample}: {"PASS" if valid else "FAIL"} {record["elapsed_seconds"]:.3f}s', flush=True)
                    if not valid:
                        report['status'] = 'FAILED'
                        atom(path, report)
                        raise SystemExit(1)
        report.update(status='PASSED', finished_utc=now())
        atom(path, report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--mode', choices=['prepare', 'bounded', 'full'], required=True)
    parser.add_argument('--plan', type=Path, default=HERE/'plan-v1.json')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--bounded-report', type=Path)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    args.plan = args.plan.resolve()
    if args.output is not None:
        args.output = args.output.resolve()
    if args.bounded_report is not None:
        args.bounded_report = args.bounded_report.resolve()
    if args.mode == 'prepare':
        args.plan.parent.mkdir(parents=True, exist_ok=True)
        assert not args.plan.exists()
        prepare(args.plan)
    else:
        assert args.output is not None
        run(args)


if __name__ == '__main__':
    main()
