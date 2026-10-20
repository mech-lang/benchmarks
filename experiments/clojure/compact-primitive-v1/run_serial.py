"""Compact typed-aset qualification and diagnostic pilots; no catalog writes or full timing mode."""
import argparse
import datetime
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import random
import signal
import statistics
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
PLAN = HERE/'execution-plan.json'
CORPUS = ROOT/'experiments/shared/bounded-corpus-v1/cases'
REFERENCE = ROOT/'archive/languages/c3/20261012/revisions/private-v1/references.py'
REFERENCE_SHA = '6ba2d8d70f23ac04f2bd24e73356f14a1c3a046da35f25e936332b10a7cba1f3'
NAMES = ['parent', 'primitive-control', 'compact-hot-aset', 'compact-all-aset']
PILOT_NAMES = ['primitive-control', 'compact-hot-aset', 'compact-all-aset']
BOUNDED = [0, 1, 2, 3, 7, 10, 31, 1000, 1001, 10000]
SEED = 20261020
LOCK = '/tmp/mech-clbg-timing.lock'
FULL_OUTPUT = b'-0.169075164\n-0.169059907\n'
FLAGS = ['-XX:ActiveProcessorCount=8', '-Xms64m', '-Xmx8g', '-XX:+UseG1GC']
EXPECTED_NOTES = b'NOTE: Picked up JDK_JAVA_OPTIONS: \nPicked up JAVA_TOOL_OPTIONS: \nPicked up _JAVA_OPTIONS: \n'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def ref(path):
    path = Path(path).resolve()
    return dict(path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path), sha256=sha(path))


def load(path):
    return json.loads(Path(path).read_text())


def atom(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+'.tmp')
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.replace(path)


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def environment(home):
    return dict(PATH='/usr/bin:/bin', LC_ALL='C', LANG='C', TZ='UTC', JAVA_HOME=str(home),
        CLASSPATH='', JAVA_TOOL_OPTIONS='', JDK_JAVA_OPTIONS='', _JAVA_OPTIONS='',
        OMP_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1', VECLIB_MAXIMUM_THREADS='1')


def one(command, directory, timeout, env, lock_fd, stdin=Path('/dev/null')):
    """One owned process group; retains raw streams and inherited common lock."""
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=False)
    record = dict(command=list(map(str, command)), cwd=str(ROOT), environment=env,
        stdin=str(stdin), started_utc=now(), common_mutex_inode=os.fstat(lock_fd).st_ino,
        common_mutex_inherited=True, timeout_seconds=timeout)
    finished = threading.Event(); child = [None]; timed_out = [False]
    def watchdog():
        if not finished.wait(timeout):
            timed_out[0] = True
            if child[0] is not None:
                try: os.killpg(child[0], signal.SIGKILL)
                except ProcessLookupError: pass
    watcher = threading.Thread(target=watchdog, daemon=True); watcher.start()
    try:
        with Path(stdin).open('rb') as inp, (directory/'stdout.bin').open('wb') as out, (directory/'stderr.bin').open('wb') as err:
            start = time.perf_counter_ns()
            process = subprocess.Popen(record['command'], cwd=ROOT, env=env, stdin=inp, stdout=out, stderr=err,
                start_new_session=True, pass_fds=(lock_fd,))
            child[0] = process.pid
            pid, status, usage = os.wait4(process.pid, 0)
            end = time.perf_counter_ns(); process.returncode = os.waitstatus_to_exitcode(status)
        require(pid == process.pid, 'Waited for the wrong native process')
        record.update(pid=pid, pgid=pid, exit_code=process.returncode, timed_out=timed_out[0],
            elapsed_seconds=(end-start)/1e9, user_seconds=usage.ru_utime, system_seconds=usage.ru_stime,
            maximum_rss_bytes=usage.ru_maxrss)
    except BaseException as error:
        record.update(error=repr(error))
        if child[0] is not None:
            try: os.killpg(child[0], signal.SIGKILL)
            except ProcessLookupError: pass
        raise
    finally:
        finished.set(); watcher.join(); record['finished_utc'] = now()
        for stream in ['stdout', 'stderr']:
            path = directory/(stream+'.bin')
            if path.is_file(): record[stream] = dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))
        atom(directory/'process.json', record)
    listing = subprocess.check_output(['/bin/ps', '-axo', 'pid=,pgid=,comm='], text=True)
    remaining = [line.strip() for line in listing.splitlines() if len(line.split()) >= 2 and line.split()[1] == str(pid)]
    record['remaining_process_group'] = remaining
    if remaining:
        try: os.killpg(pid, signal.SIGKILL)
        except ProcessLookupError: pass
    atom(directory/'process.json', record)
    require(not remaining, 'Native process left descendants; attempt retained')
    return record


def energies(raw):
    try:
        lines = raw.decode('ascii').splitlines()
        if len(lines) != 2 or not raw.endswith(b'\n'): return None
        values = [float(line) for line in lines]
        return values if all(math.isfinite(value) for value in values) else None
    except (ValueError, UnicodeError): return None


def matches(raw, expected):
    actual, reference = energies(raw), energies(expected)
    return actual is not None and reference is not None and all(abs(a-b) <= 1e-8 for a,b in zip(actual, reference))


def power():
    battery = subprocess.check_output(['/usr/bin/pmset', '-g', 'batt'], text=True)
    settings = subprocess.check_output(['/usr/bin/pmset', '-g', 'custom'], text=True)
    modes = [line.split()[-1] for line in settings.splitlines() if 'lowpowermode' in line]
    require("'AC Power'" in battery and modes and set(modes) == {'0'}, 'AC power with low-power mode disabled required')
    return dict(battery=battery, settings=settings)


def competition():
    listing = subprocess.check_output(['/bin/ps', '-axo', 'pid=,comm='], text=True)
    names = {'java', 'javac', 'javap', 'cargo', 'rustc', 'rustdoc', 'clang', 'clang++', 'cc', 'gcc', 'julia', 'BQN', 'nim', 'hyperfine', 'swipl', 'matlab'}
    rows = [line.strip() for line in listing.splitlines() if len(line.split(None,1)) == 2 and Path(line.split(None,1)[1]).name in names]
    require(not rows, 'Competing compiler or subject processes: '+repr(rows))
    return rows


def check_ref(value):
    path = ROOT/value['path']
    require(path.is_file() and sha(path) == value['sha256'], 'Changed pinned file: '+value['path'])
    return path


def make_plan():
    proposal = load(HERE/'plan.json'); runtime = load(HERE/'runtime-build.json'); builds = load(HERE/'builds.json')
    check_ref(proposal['runtime']['copy']);check_ref(proposal['runtime']['receipt'])
    require(proposal['runtime']['copy']['sha256']==proposal['runtime']['receipt']['sha256'], 'Runtime receipt copy differs')
    require(runtime['schema'] == 'clojure-runtime-build.v1' and runtime['status'] == 'PASSED', 'Qualified restored runtime required')
    require(builds['schema'] == 'clojure-nbody-builds.v1' and builds['status'] == 'PASSED' and builds['active'] is None, 'Complete exact-source builds required')
    require(builds['runtime'] == ref(HERE/'runtime-build.json'), 'Runtime/build receipt binding differs')
    require(sorted(builds['programs']) == sorted(NAMES), 'Need original parent, primitive control and both compact typed-aset candidates')
    pins = [ref(HERE/'plan.json'), ref(HERE/'runtime-build.json'), ref(HERE/'builds.json'),
        ref(HERE/'build_candidates.py'), ref(HERE/'run_state_probe.py'), ref(HERE/'source-ownership-proposed.json'), ref(__file__), ref(REFERENCE)]
    require(sha(REFERENCE) == REFERENCE_SHA, 'Independent shared reference changed')
    for path,digest in runtime['pins'].items(): pins.append(dict(path=path,sha256=digest))
    for evidence in runtime['identity']+runtime['linked_image_evidence']:
        path=check_ref(evidence);pins.append(evidence)
        receipt=load(path)
        pins.extend(receipt[stream] for stream in ['stdout','stderr'])
    for name in NAMES:
        program = builds['programs'][name]
        expected = next(row['source'] for row in proposal['programs'] if row['id'] == name)
        require(program['source'] == expected and program['support'] == proposal['parent']['support'], 'Build source/support differ: '+name)
        require(program['flags'] == FLAGS, 'JVM flags differ: '+name)
        pins.extend([expected, program['support']])
        pins.extend(dict(path=path,sha256=digest) for path,digest in program['class_pins'].items())
        pins.extend(program['input_files'])
        pins.extend(program['evidence'])
    state_path=HERE/'state-probe-report.json';state=load(state_path)
    require(state['schema']=='clojure-nbody-state-probe.v1' and state['status']=='PASSED'
        and state['runtime']==ref(HERE/'runtime-build.json') and state['builds']==ref(HERE/'builds.json')
        and state['advance_function_invocations']==464 and state['raw_bit_state_slots']==35
        and state['implementations']==4
        and state['inner_pair_store_counters']=='not-instrumented-source-proof-only', 'Exact untimed state proof required')
    pins.extend([ref(state_path),state['controller'],state['script'],state['process']['stdout'],state['process']['stderr']])
    for path,digest in state['pins'].items():pins.append(dict(path=path,sha256=digest))
    corpus = load(CORPUS/'manifest.json'); pins.append(ref(CORPUS/'manifest.json'))
    cases = sorted([row for row in corpus['cases'] if row['benchmark'] == 'nbody'], key=lambda row: row['n'])
    require([row['n'] for row in cases] == [0,1,2,10,1000,10000], 'Shared n-body case inventory differs')
    for case in cases:
        for field in ['stdin','expected']:
            source = case[field]; path = CORPUS/source['path']
            require(sha(path) == source['sha256'] and path.stat().st_size == source['bytes'], 'Shared corpus file changed')
            pins.append(ref(path))
    for value in pins: check_ref(value)
    return dict(schema='clojure-compact-typed-aset-execution-plan.v1', status='PREPARED-NO-EXECUTION', proposal=ref(HERE/'plan.json'),
        runtime=ref(HERE/'runtime-build.json'), builds=ref(HERE/'builds.json'), controller=ref(__file__),
        pins={value['path']:value['sha256'] for value in pins}, programs=builds['programs'],
        java=runtime['java'], environment=runtime['environment'], state_probe=ref(state_path),bounded=cases, extra_bounded_n=[3,7,31,1001],
        independent_reference=ref(REFERENCE), order_seed=SEED, pilot_sources=PILOT_NAMES, pilot_rounds=1, pilot_n=1000000,
        full_n_context_only=50000000, full_execution_enabled=False,
        full_expected=dict(bytes=len(FULL_OUTPUT),sha256=hashlib.sha256(FULL_OUTPUT).hexdigest()),
        output_rule='Exactly two finite energy lines, complete streams; established absolute 1e-8 reference tolerance, plus byte-equality result retained separately.',
        common_mutex=LOCK, required_work=proposal['required_work'], chart_admission=False,
        timing_boundary='Fresh JVM launch, class loading and HotSpot JIT, all steps and both energy computations, GC, complete stdout/flush and process exit; excludes hashing/reference generation/power checks.')


def check_pins(plan):
    check_ref(plan['controller'])
    for path,digest in plan['pins'].items(): check_ref(dict(path=path,sha256=digest))


def check_prerequisite(path, mode, plan):
    report = load(path)
    require(report['schema'] == 'clojure-compact-typed-aset-execution.v1' and report['mode'] == mode and report['status'] == 'PASSED'
        and report['active'] is None and report['plan'] == ref(PLAN) and report['pins'] == plan['pins'], 'Matching complete '+mode+' report required')
    wanted = [(name,n) for name in (NAMES if mode == 'bounded' else PILOT_NAMES)
              for n in (BOUNDED if mode == 'bounded' else [1000000])]
    require(sorted((row['source'],row['n']) for row in report['cases']) == sorted(wanted), 'Incomplete '+mode+' prerequisite')
    for row in report['cases']:
        require(row['output_valid'] and row['exit_code'] == 0 and not row['timed_out'] and not row['remaining_process_group'], 'Failed prerequisite process')
        raw = load(Path(row['stdout']['path']).with_name('process.json'))
        require(all(row.get(key) == value for key,value in raw.items()), 'Raw prerequisite process receipt differs')
        for stream in ['stdout','stderr']: check_ref(row[stream])
        require(row['command'] == plan['programs'][row['source']]['run_argv']+[str(row['n'])], 'Prerequisite command differs')
    return ref(path)


def execute(args, plan):
    output = args.output.resolve()
    require(output.is_relative_to(HERE) and not output.exists(), 'Use an exclusive new output directory inside the experiment')
    require(args.mode in ['bounded','pilot'], 'Full timings require a separate reviewed selection packet')
    names = NAMES if args.mode == 'bounded' else PILOT_NAMES
    prerequisite = {}
    if args.mode != 'bounded':
        require(args.bounded_report is not None, '--bounded-report required')
        prerequisite['bounded'] = check_prerequisite(args.bounded_report,'bounded',plan)
    with open(LOCK,'a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); check_pins(plan); competition(); output.mkdir(parents=True)
        for name in ['run_serial.py','build_candidates.py','run_state_probe.py','state_probe.clj',
                     'execution-plan.json','plan.json','runtime-build.json','builds.json','source-ownership-proposed.json']:
            (output/name).write_bytes((HERE/name).read_bytes())
        report = dict(schema='clojure-compact-typed-aset-execution.v1',mode=args.mode,status='RUNNING',started_utc=now(),
            plan=ref(PLAN),pins=plan['pins'],prerequisites=prerequisite,common_mutex_inode=os.fstat(lock.fileno()).st_ino,
            full_workload=False,diagnostic_profile=args.mode == 'pilot',chart_admission=False,
            timing_boundary=plan['timing_boundary'],required_work=plan['required_work'],sources=names,cases=[],orders=[],active=None)
        atom(output/'report.json',report)
        try:
            expected = {}
            if args.mode == 'bounded':
                for case in plan['bounded']: expected[case['n']] = (CORPUS/case['expected']['path']).read_bytes()
                import importlib.util
                spec=importlib.util.spec_from_file_location('clojure_shared_reference',REFERENCE); oracle=importlib.util.module_from_spec(spec);spec.loader.exec_module(oracle)
                for n in plan['extra_bounded_n']: expected[n] = oracle.nbody(n)
                references=output/'references';references.mkdir()
                for n,raw in expected.items(): (references/('n-'+str(n)+'.stdout')).write_bytes(raw)
                report['references']={str(n):ref(references/('n-'+str(n)+'.stdout')) for n in expected}
                schedule=[(n,1) for n in BOUNDED]
            else: schedule=[(1000000,1)]
            rng=random.Random(SEED)
            for n,sample in schedule:
                order=list(names);rng.shuffle(order);report['orders'].append(dict(n=n,sample=sample,sources=order))
                for name in order:
                    check_pins(plan);competition();before=power()
                    report['active']=dict(source=name,n=n,sample=sample);atom(output/'report.json',report)
                    directory=output/('n-'+str(n)+'-round-'+str(sample)+'-'+name)
                    row=one(plan['programs'][name]['run_argv']+[str(n)],directory,args.timeout,plan['environment'],lock.fileno())
                    after=power();raw=(directory/'stdout.bin').read_bytes();err=(directory/'stderr.bin').read_bytes()
                    reference=expected[n] if args.mode=='bounded' else None
                    valid=(row['exit_code']==0 and not row['timed_out'] and not row['remaining_process_group'] and err in [b'',EXPECTED_NOTES]
                        and row['maximum_rss_bytes'] <= 10*1024**3 and math.isfinite(row['elapsed_seconds']) and row['elapsed_seconds']>0
                        and (matches(raw,reference) if reference is not None else energies(raw) is not None))
                    row.update(source=name,n=n,sample=sample,output_valid=valid,source_sha256=plan['programs'][name]['source']['sha256'],
                        exact_reference_bytes=(raw==reference) if reference is not None else None,power_before=before,power_after=after)
                    report['cases'].append(row);report['active']=None;atom(output/'report.json',report)
                    print(json.dumps(dict(source=name,n=n,sample=sample,seconds=row['elapsed_seconds'],valid=valid)),flush=True)
                    require(valid,'Output/process validation failed; attempt retained, no automatic retry');check_pins(plan)
            if args.mode=='pilot':
                control=next(row for row in report['cases'] if row['source']=='primitive-control');expected_raw=Path(control['stdout']['path']).read_bytes()
                for row in report['cases']:
                    raw=Path(row['stdout']['path']).read_bytes();row['output_valid']=matches(raw,expected_raw);row['exact_parent_bytes']=raw==expected_raw
                require(all(row['output_valid'] for row in report['cases']),'Pilot differs from matched parent')
                report['pilot_output_scope']='Two finite lines and1e-8 agreement to the matched qualified primitive control; exact bytes also recorded. Diagnostic screen, not independent output qualification or chart data.'
            report.update(status='PASSED',finished_utc=now(),pins_unchanged=True)
            report['samples']={name:[row['elapsed_seconds'] for row in report['cases'] if row['source']==name] for name in names}
            report['medians']={name:statistics.median(values) for name,values in report['samples'].items()}
        except BaseException as error:
            report.update(status='FAILED',error=repr(error),finished_utc=now());raise
        finally: atom(output/'report.json',report)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--mode',choices=['bounded','pilot'])
    parser.add_argument('--output',type=Path)
    parser.add_argument('--bounded-report',type=Path)
    parser.add_argument('--timeout',type=int,default=600)
    args=parser.parse_args();require(args.prepare != bool(args.mode),'Choose --prepare or --mode');require(args.timeout>0,'Positive timeout required')
    with open(LOCK,'a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB);plan=make_plan()
        if args.prepare:
            require(not PLAN.exists(),'Execution plan already exists; preserve it');atom(PLAN,plan);print(json.dumps(ref(PLAN)));return
        require(load(PLAN)==plan,'Execution plan stale; do not silently regenerate')
    require(args.output is not None,'--output required');execute(args,plan)


if __name__=='__main__':main()
