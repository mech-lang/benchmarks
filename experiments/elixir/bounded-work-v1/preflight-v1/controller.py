#!/usr/bin/env python3
"""Prepare/run bounded output checks of the twenty retained Elixir BEAM forms.

prepare reads/hashes metadata only. run starts exactly the planned, serial
bounded cases under the existing mutex; it never invokes a subject compiler.
The 78 reference inputs/outputs come from the already closed Prolog preparation
corpus. Neither its old runtimes nor an oracle generator is executed. All actual
stdout/stderr, including a failed partial case, remain in a fresh output tree.
Correct bounded output does not grant required-work, LOC or full-timing admission.
"""
import argparse
import csv
import ctypes
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LOCK = Path('/tmp/mech-clbg-timing.lock')
LOCK_INODE = 79859134
COHORT = ROOT/'archive/languages/elixir/20261013'
EXPERIMENT = ROOT/'experiments/elixir/bounded-work-v1'
COMPILER = COHORT/'revisions/remaining19-compile-owners-v1/jobs/remaining19-compile-owners-v1/preparation-result.json'
COMPILER_SHA = '6a45e7514c68a300b3d3770e713a3c7a9a91744b5ef149f5ec5c626e5ec4fffe'
FIRST = COHORT/'jobs/saved-first-compile-owner-writer-v1/preparation-result.json'
FIRST_SHA = 'a5eec9dbf0c93c68ada489fa00aab486306ce5585e1fe0a2af8678c532398206'
HELPER = ROOT/'experiments/elixir/helper-semantics/results-v1/report.json'
HELPER_SHA = 'b8da9856b0aaf1c68fafde50f38abf63a08f43370d5cb512ba8ca3a5952d3538'
PROLOG = ROOT/'archive/languages/prolog/20261013'
REFERENCE_ROOT = ROOT/'archive/qualification/prolog/checks/prolog-remaining155-closed-review-v1/receipt.json'
REFERENCE_ROOT_SHA = '139d9124d3df942bb3170112b3841c33b0191580a002f974835a627651be9bc8'
REFERENCE_REPORT = PROLOG/'qualification/prepare-explicit-goal-rest-v1/report.json'
REFERENCE_REPORT_SHA = 'cab6ea7f3bd8a237f8f83833ed9b9cc293bbe1878cc8a894d74fdcf41f7ffbff'
ELIXIR = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg/elixir-comparison/20261013/.build/retained-otp-toolchain-v1/elixir')
SUPPORT_SHA = 'c9fbb60888c46fb50195245761a411716f1256145af367e03a23f70aea270e89'
RUNNER_SHA = 'bdad2389d437fd4c69122e5d25b3065412b4bca0c272631667283273392ba8ff'
NUMERIC = {'nbody': [0, 1, 2, 10000], 'mandelbrot': [1, 2, 3, 7, 8, 9, 15, 16, 17, 31, 65, 129, 200],
    'spectralnorm': [1, 2, 3, 5, 9, 100], 'binarytrees': [0, 4, 7, 9],
    'fannkuchredux': [1, 2, 3, 4, 5, 6, 7, 8], 'pidigits': [0, 1, 9, 10, 11, 20, 21, 27, 97],
    'fasta': [0, 1, 2, 29, 30, 31, 60, 61, 287, 574, 20000]}
STREAMS = {
    'regexredux': ['all-replacements', 'records', 'header-eof', 'replacement-boundaries', 'empty'],
    'revcomp': ['iupac', 'comment-crlf-eof', 'tail', 'empty', 'header-eof', 'preheader-ignored'],
    'knucleotide': ['ties-and-stop', 'one-base', 'empty', 'missing', 'crlf-comment-eof',
        'embedded-header-comment', 'arbitrary-widths', 'header-eof', 'empty-input',
        'exact-token-cr', 'exact-token-controls', 'tail']}
CASE_NAMES = {**{b: ['n-'+str(n) for n in ns] for b, ns in NUMERIC.items()}, **STREAMS}
TIMEOUT = 60
RSS_LIMIT_KIB = 2*1024*1024
FILE_LIMIT = 8*1024*1024
CLEANUP_TIMEOUT = 5


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def save(path, value):
    path = Path(path)
    temporary = path.with_suffix(path.suffix+'.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2, allow_nan=False); stream.write('\n')
        stream.flush(); os.fsync(stream.fileno())
    temporary.replace(path)


def lock_identity(lock):
    opened, named = os.fstat(lock.fileno()), LOCK.stat()
    require((opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino)
            and opened.st_ino == LOCK_INODE, 'Common timing mutex changed')


class Evidence:
    def __init__(self):
        self.pins = {}
        with (ROOT/'migration/reorganization-paths.tsv').open() as stream:
            self.mapping = {r['original_path']: r['current_path'] for r in csv.DictReader(stream, delimiter='\t')}

    def path(self, name):
        path = Path(name)
        if path.is_relative_to(ROOT):
            return path
        if '/benchmarks/clbg/' in str(path):
            key = 'benchmarks/clbg/'+str(path).split('/benchmarks/clbg/', 1)[1]
            if key in self.mapping:
                candidate = ROOT/self.mapping[key]
                require(candidate.resolve().is_relative_to(ROOT), 'Archive path escapes repository')
                return candidate
        return path

    def bind(self, name, expected, *, original=False):
        require(re.fullmatch('[0-9a-f]{64}', expected) is not None, 'Invalid SHA-256')
        path = Path(name) if original else self.path(name)
        require(sha(path) == expected, 'Changed input: '+str(path))
        require(str(path) not in self.pins or self.pins[str(path)] == expected, 'Conflicting evidence pins')
        self.pins[str(path)] = expected
        return path

    def read(self, name, expected):
        path = self.bind(name, expected)
        raw = path.read_bytes()
        require(hashlib.sha256(raw).hexdigest() == expected, 'JSON changed while reading')
        return json.loads(raw)

    def ref(self, name, expected, *, original=False):
        return dict(path=str(self.bind(name, expected, original=original)), sha256=expected)


def reference_cases(evidence):
    root = evidence.read(REFERENCE_ROOT, REFERENCE_ROOT_SHA)
    require(root['status'] == 'closed-qualified-all20-Prolog-bounded-preparation-awaiting-work-and-LOC'
            and root['report_sha256'] == REFERENCE_REPORT_SHA and root['total_bounded_cases'] == 156
            and root['qualification_checks_per_case'] == 20, 'Closed bounded corpus missing')
    report = evidence.read(REFERENCE_REPORT, REFERENCE_REPORT_SHA)
    require(report['all20_bounded_outputs_qualified'] is True and report['total_bounded_cases'] == 156
            and report['terminal_evidence_complete'] is True and report['active'] is None,
            'Reference corpus is incomplete')
    pins = report['pins']
    result = {bench: [] for bench in CASE_NAMES}
    for row in report['case_results']:
        if not row['id'].endswith('-compact'):
            continue
        benchmark = row['id'].split('-')[1]
        raw_name, supervisor_name = row['result_path'], row['supervisor_result_path']
        raw = evidence.read(raw_name, pins[raw_name])
        supervised = evidence.read(supervisor_name, pins[supervisor_name])
        require(supervised['qualified'] is True and supervised['full_workload'] is False
                and supervised['preparation_only'] is True and supervised['never_chart_eligible'] is True
                and supervised['case'] == row['actual_case']
                and len(supervised['qualification_checks']) == 20
                and all(v is True for v in supervised['qualification_checks'].values())
                and supervised['stderr'] == '' and supervised['exit_status'] == 0
                and supervised['validation']['reference_match'] is True, 'Reference case not qualified')
        require(raw['stdout_sha256'] == supervised['stdout_sha256']
                and raw['stdout_bytes'] == supervised['stdout_bytes'], 'Raw/supervisor output differs')
        directory = Path(raw_name).parents[1]/'bounded-output'/row['id']/row['actual_case']
        expected_name, actual_name = str(directory/'expected.stdout'), str(directory/'actual.stdout')
        expected = evidence.ref(expected_name, pins[expected_name])
        actual = evidence.ref(actual_name, pins[actual_name])
        require(actual['sha256'] == supervised['stdout_sha256'], 'Retained reference output differs')
        stdin = None
        if benchmark in STREAMS:
            stdin_name = str(directory/'stdin.fasta')
            stdin = evidence.ref(stdin_name, pins[stdin_name])
        else:
            require(row['case'] == 'n-'+str(raw['workload_n']), 'Reference size differs')
        result[benchmark].append(dict(case=row['case'], n=raw['workload_n'], stdin=stdin, expected=expected,
            oracle_raw=evidence.ref(raw_name, pins[raw_name]), oracle_supervisor=evidence.ref(supervisor_name, pins[supervisor_name]),
            retained_actual=actual, validation='finite-two-energy-lines-within-1e-8' if benchmark == 'nbody' else 'exact-complete-bytes'))
    for bench, cases in result.items():
        require(len(cases) == len(CASE_NAMES[bench]) and {c['case'] for c in cases} == set(CASE_NAMES[bench]),
                'Reference case inventory differs: '+bench)
        cases.sort(key=lambda c: CASE_NAMES[bench].index(c['case']))
    require(sum(map(len, result.values())) == 78, 'Expected 78 distinct bounded cases')
    return result


def prepare(args):
    require(not args.plan.exists() and not args.output.exists(), 'Fresh plan and output required')
    require(not args.plan.resolve().is_relative_to(args.output.resolve()), 'Plan must be outside the fresh execution directory')
    evidence = Evidence()
    compiled = evidence.read(COMPILER, COMPILER_SHA)
    first = evidence.read(FIRST, FIRST_SHA)
    helper = evidence.read(HELPER, HELPER_SHA)
    terminal_path = HELPER.with_name('terminal.json')
    terminal = evidence.read(terminal_path, args.helper_terminal_sha256)
    require(helper['status'] == terminal['status'] == 'compiled-helper-semantics-passed'
            and helper['helper_formatting_and_stdio_qualified'] is True
            and terminal['report_sha256'] == HELPER_SHA
            and helper['changed_pins'] == helper['integrity_errors'] == terminal['integrity_errors'] == terminal['artifact_errors'] == [],
            'Compiled helper semantics not qualified')
    require(helper['subject_main_executions'] == helper['benchmark_samples'] == 0,
            'Helper receipt unexpectedly contains main/timing executions')
    require(compiled['total_compiled_profiles'] == len(compiled['profiles']) == 20
            and compiled['subject_main_executions'] == 0 and compiled['chart_admission'] is False,
            'Retained compile cohort differs')
    for path, digest in helper['pins'].items():
        evidence.bind(path, digest, original=True)
    for name, item in terminal['available_evidence'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'Unsafe helper artifact')
        evidence.bind(HELPER.parent/name, item['sha256'])
    require(set(helper['profile_ids']) == {r['id'] for r in compiled['profiles']}
            and len(helper['profile_ids']) == 20, 'Helper cohort differs')
    cases = reference_cases(evidence)
    review_path = EXPERIMENT/'source-review.json'
    review = evidence.read(review_path, sha(review_path))
    require(review['status'] == 'ten-exact-main-sources-read-awaiting-compiled-work-witnesses'
            and review['unique_main_sources'] == 10 and review['compiled_forms'] == 20,
            'Source semantic review missing')
    rows = []
    for row in compiled['profiles']:
        identity = row['id']
        _, benchmark, variant = identity.split('-')
        require(benchmark in CASE_NAMES and variant in ('compact', 'optimized'), 'Unknown retained form')
        sources = row['physical_inputs']
        require(len(sources) == 3 and {s['role'] for s in sources} == {'application', 'application-helper', 'application-launcher'}
                and all(s['counted'] is True for s in sources), 'Complete authored bundle required')
        by_role = {s['role']: s for s in sources}
        require(by_role['application-helper']['sha256'] == SUPPORT_SHA
                and by_role['application-launcher']['sha256'] == RUNNER_SHA
                and by_role['application']['sha256'] == review['benchmarks'][benchmark]['main_sha256'],
                'Reviewed source identity differs')
        for item in sources + row['beams']:
            evidence.bind(item['path'], item['sha256'], original=True)
        require(len(row['beams']) == 2, 'Expected two retained subject modules')
        beams = {Path(b['path']).name: b for b in row['beams']}
        require(set(beams) == {'Elixir.Clbg.Main.beam', 'Elixir.Clbg.Support.beam'}, 'Unexpected retained module')
        ebin = Path(beams['Elixir.Clbg.Main.beam']['path']).parent
        require(all(Path(b['path']).parent == ebin for b in row['beams'])
                and {p.name for p in ebin.glob('*.beam')} == set(beams), 'Unexpected module in subject directory')
        owner = first if row['reused'] else row
        for term in owner['original_owner_terms']:
            evidence.bind(term['path'], term['sha256'])
        require(len(owner['original_owner_terms']) == 2, 'Missing original Main/Support ownership terms')
        if row['reused']:
            require(identity == first['selected_profile'] == 'elixir-nbody-compact'
                    and first['compiled_source_debug_bindings'] == 2, 'Wrong first compile reuse')
        else:
            require(row['source_debug_bindings'] == 2 and row['compiler_command']['exit_status'] == 0
                    and row['compiler_command']['final_exit_status'] == 0
                    and row['owner_writer_command']['exit_status'] == 0, 'Compile/owner receipt failed')
        command = [str(ELIXIR/'bin/elixir'), '-pa', str(ebin), by_role['application-launcher']['path'], '{n}']
        if not row['reused']:
            require(row['runtime_command'] == command, 'Retained launch changed')
        environment = dict(owner['runtime_environment'])
        require(environment['ELIXIR_ERL_OPTIONS'] == '+S 8:8 +A 1 +SDcpu 1:1 +SDio 1'
                and all(not environment.get(k) for k in ('ERL_FLAGS', 'ERL_AFLAGS', 'ERL_ZFLAGS', 'ERL_LIBS', 'ERL_COMPILER_OPTIONS')),
                'Retained runtime flags differ')
        rows.append(dict(id=identity, benchmark=benchmark, variant=variant, physical_inputs=sources,
            beams=row['beams'], owners=owner['original_owner_terms'], ebin=str(ebin), command=command,
            runtime_environment=environment, bounded_cases=cases[benchmark],
            source_alias_note='The compact and optimized forms have identical main source bytes; no distinct optimization is claimed.'))
    require(len({r['id'] for r in rows}) == 20 and sum(len(r['bounded_cases']) for r in rows) == 156,
            'Incomplete planned case inventory')
    observer = EXPERIMENT/'verify-runtime.exs'
    for path in (observer, Path(__file__).resolve(), Path(sys.executable).resolve(), Path('/bin/ps')):
        evidence.bind(path, sha(path))
    plan = dict(schema='elixir-retained-beam-bounded-plan-v1', status='prepared-awaiting-reviewed-native-execution',
        controller=str(Path(__file__).resolve()), controller_sha256=sha(__file__), observer=str(observer),
        output=str(args.output.resolve()), profiles=rows, pins=evidence.pins,
        source_review=str(review_path), helper_report=str(HELPER), helper_report_sha256=HELPER_SHA,
        helper_terminal_sha256=args.helper_terminal_sha256, reference_report=str(REFERENCE_REPORT),
        reference_report_sha256=REFERENCE_REPORT_SHA, distinct_reference_cases=78, planned_subject_main_executions=156,
        timeout_seconds=TIMEOUT, maximum_process_group_rss_kib=RSS_LIMIT_KIB, per_stream_file_limit_bytes=FILE_LIMIT,
        subject_recompilations=0, benchmark_samples=0, source_work_qualified=False,
        canonical_loc=None, formatted_loc=None, chart_admission=False)
    args.plan.parent.mkdir(parents=True, exist_ok=True)
    require(not args.plan.exists(), 'Plan appeared during preparation')
    save(args.plan, plan)
    print(json.dumps(dict(status=plan['status'], plan=str(args.plan), sha256=sha(args.plan), native_executions=0)))


def output_validation(benchmark, actual, expected):
    result = dict(stdout_bytes=len(actual), stdout_sha256=hashlib.sha256(actual).hexdigest(),
                  expected_bytes=len(expected), expected_sha256=hashlib.sha256(expected).hexdigest())
    if benchmark == 'nbody':
        require(re.fullmatch(rb'-?\d+\.\d{9}\n-?\d+\.\d{9}\n', actual) is not None, 'Malformed N-body complete output')
        values, reference = [float(x) for x in actual.splitlines()], [float(x) for x in expected.splitlines()]
        require(len(reference) == 2 and all(math.isfinite(x) for x in values+reference)
                and all(abs(a-b) <= 1e-8 for a, b in zip(values, reference)), 'N-body energies differ')
        result.update(method='finite-two-energy-lines-within-1e-8', energies=values, expected_energies=reference, tolerance=1e-8)
    else:
        require(actual == expected, 'Complete bounded output differs from the retained independent reference')
        result['method'] = 'exact-complete-bytes'
    result['reference_match'] = True
    return result


def bounded_schedule(rows):
    require(len(rows) == 20 and {r['id'] for r in rows}
            == {'elixir-'+b+'-'+v for b in CASE_NAMES for v in ('compact', 'optimized')},
            'Exactly twenty retained form identities required')
    count = 0
    for row in rows:
        bench = row['benchmark']
        require(row['id'] == 'elixir-'+bench+'-'+row['variant']
                and [c['case'] for c in row['bounded_cases']] == CASE_NAMES[bench], 'Bounded case order/inventory changed')
        for case in row['bounded_cases']:
            expected_n = int(case['case'][2:]) if bench in NUMERIC else 0
            require(type(case['n']) is int and case['n'] == expected_n
                    and (case['stdin'] is not None) == (bench in STREAMS), 'Unexpected full-size/input substitution')
            count += 1
    require(count == 156, 'Expected 156 bounded cases')


class BSDInfo(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint32) for name in
                ('flags','status','xstatus','pid','ppid','uid','gid','ruid','rgid','svuid','svgid','reserved')]
    _fields_ += [('comm',ctypes.c_char*16),('name',ctypes.c_char*32)]
    _fields_ += [(name,ctypes.c_uint32) for name in ('nfiles','pgid','jobc','tdev','tpgid')]
    _fields_ += [('nice',ctypes.c_int32),('birth_seconds',ctypes.c_uint64),('birth_microseconds',ctypes.c_uint64)]


class Kernel:
    """The retained Kotlin helper's zombie-aware identity read, without reaping."""
    def __init__(self):
        self.library = ctypes.CDLL('/usr/lib/libproc.dylib', use_errno=True)
        self.library.proc_pidinfo.argtypes = [ctypes.c_int,ctypes.c_int,ctypes.c_uint64,ctypes.c_void_p,ctypes.c_int]
        self.library.proc_pidinfo.restype = ctypes.c_int
        require(ctypes.sizeof(BSDInfo) == 136, 'Unexpected kernel identity layout')

    def identity(self, pid):
        info = BSDInfo()
        # PROC_PIDTBSDINFO requires arg != 0 to include unreaped zombies.
        if self.library.proc_pidinfo(pid,3,1,ctypes.byref(info),ctypes.sizeof(info)) != ctypes.sizeof(info):
            return None
        require(info.pid == pid and info.birth_seconds > 0, 'Invalid kernel identity')
        return {name:getattr(info,name) for name in
                ('pid','ppid','pgid','status','birth_seconds','birth_microseconds')}


def owned_identity(kernel, process, initial=None):
    identity = kernel.identity(process.pid)
    require(identity and identity['ppid'] == os.getpid() and identity['pgid'] == process.pid,
            'Missing owned native identity before reap')
    if initial is not None:
        require(all(identity[key] == initial[key] for key in
                ('pid','ppid','pgid','birth_seconds','birth_microseconds')),
                'Native leader identity changed before reap')
    return identity


def members(pgid, *, timeout=5):
    result = subprocess.run(['/bin/ps', '-axo', 'pid=,pgid=,rss=,stat='], capture_output=True, text=True, timeout=timeout, check=True)
    rows = []
    for line in result.stdout.splitlines():
        fields = line.split()
        require(len(fields) == 4 and all(x.isdecimal() for x in fields[:3]), 'Malformed process-group observation')
        pid, group, rss = map(int, fields[:3])
        status = fields[3]
        if group == pgid and not status.startswith('Z'):
            rows.append(dict(pid=pid, pgid=group, rss_kib=rss, status=status))
    return rows


def child_limits():
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (FILE_LIMIT, FILE_LIMIT))


def cleanup_owned(process, record):
    deadline = time.monotonic()+CLEANUP_TIMEOUT

    def remaining_time():
        remaining = deadline-time.monotonic()
        require(remaining > 0, 'Process-group cleanup deadline expired')
        return remaining

    # An unreaped direct child reserves its PID even if it has already exited.
    # After poll/wait reaps it, the numeric PGID alone is no longer ownership
    # evidence and must never authorize a signal to a potentially reused group.
    if process.returncode is None:
        record['cleanup_signal_identity'] = 'unreaped-direct-child'
        try:
            os.killpg(process.pid, signal.SIGKILL)
            record['stop_signals'].append(int(signal.SIGKILL))
        except ProcessLookupError:
            pass
        except BaseException as cleanup:
            record['cleanup_errors'].append(str(cleanup) or type(cleanup).__name__)
    else:
        record['cleanup_signal_skipped_reason'] = 'direct-child-already-reaped-no-active-owned-identity'
        record['exit_status'] = process.returncode
        if record.get('remaining_process_group') == []:
            record['remaining_after_cleanup'] = []
            return
    try:
        while True:
            timeout = remaining_time()
            record['monitor_processes'] += 1
            remaining = members(process.pid, timeout=timeout)
            record['remaining_after_cleanup'] = remaining
            if not remaining:
                break
            time.sleep(min(0.05, remaining_time()))
        # Keep the leader's PID reserved until every live group member is gone.
        # Both process scans and the final reap share this cleanup deadline.
        if process.returncode is None:
            process.wait(timeout=remaining_time())
        record['exit_status'] = process.returncode
    except BaseException as cleanup:
        record['cleanup_errors'].append(str(cleanup) or type(cleanup).__name__)


def observe(row, case, directory, plan, lock, launched, *, kernel=None):
    directory.mkdir(parents=True)
    for name in ('home', 'config', 'tmp'):
        (directory/name).mkdir()
    payload = Path(case['stdin']['path']).read_bytes() if case['stdin'] else b''
    expected = Path(case['expected']['path']).read_bytes()
    (directory/'stdin.bin').write_bytes(payload)
    (directory/'expected.stdout').write_bytes(expected)
    by_role = {s['role']: s for s in row['physical_inputs']}
    beams = {Path(b['path']).name: b for b in row['beams']}
    main_sha, support_sha = beams['Elixir.Clbg.Main.beam']['sha256'], beams['Elixir.Clbg.Support.beam']['sha256']
    spec = [str(directory/'runtime.txt'), row['ebin'], by_role['application']['path'], by_role['application-helper']['path'],
            main_sha, support_sha, str(lock.fileno()), str(LOCK_INODE)]
    require(all('\n' not in part for part in spec), 'Observer spec contains newline')
    (directory/'runtime-spec.txt').write_text('\n'.join(spec)+'\n')
    command = row['command'][:3]+['-r', plan['observer']]+[x.replace('{n}', str(case['n'])) for x in row['command'][3:]]
    environment = dict(row['runtime_environment'], HOME=str(directory/'home'), XDG_CONFIG_HOME=str(directory/'config'),
        TMPDIR=str(directory/'tmp')+os.sep, ERL_CRASH_DUMP=str(directory/'erl-crash.dump'),
        CLBG_ELIXIR_BOUNDED_SPEC=str(directory/'runtime-spec.txt'))
    record = dict(id=row['id'], benchmark=row['benchmark'], case=case['case'], n=case['n'], command=command,
        retained_runtime_command=row['command'], environment=environment, cwd=str(directory),
        started_at=datetime.now(timezone.utc).isoformat(), timeout_seconds=TIMEOUT,
        process_monitor_call_timeout_seconds=5, cleanup_total_timeout_seconds=CLEANUP_TIMEOUT,
        maximum_process_group_rss_kib=RSS_LIMIT_KIB, per_stream_file_limit_bytes=FILE_LIMIT,
        stdin_bytes=len(payload), stdin_sha256=hashlib.sha256(payload).hexdigest(),
        status='starting', pid=None, pgid=None, common_mutex_held=True, subject_main_launch_requested=True,
        native_process_started=False, main_entry_directly_observed=False, stop_signals=[], cleanup_errors=[], monitor_errors=[],
        monitor_processes=0, observed_peak_process_group_rss_kib=0, benchmark_samples=0,
        source_work_qualified=False, chart_admission=False, reference_evidence=case)
    save(directory/'process.json', record)
    process = None
    try:
        kernel = kernel if kernel is not None else Kernel()
        with (directory/'stdin.bin').open('rb') as stdin, (directory/'stdout.bin').open('xb') as stdout, (directory/'stderr.txt').open('xb') as stderr:
            deadline = time.monotonic()+TIMEOUT

            def execution_remaining():
                remaining = deadline-time.monotonic()
                require(remaining > 0, 'Bounded native process timeout')
                return remaining

            process = subprocess.Popen(command, cwd=directory, env=environment, stdin=stdin, stdout=stdout, stderr=stderr,
                start_new_session=True, pass_fds=(lock.fileno(),), preexec_fn=child_limits)
            record.update(pid=process.pid, pgid=process.pid, native_process_started=True, status='running')
            launched(row['id'], case['case'], process.pid)
            record['identity'] = owned_identity(kernel, process)
            save(directory/'process.json', record)
            while True:
                execution_remaining()
                identity = owned_identity(kernel, process, record['identity'])
                record['monitor_processes'] += 1
                try:
                    group = members(process.pid, timeout=min(5, execution_remaining()))
                except BaseException as error:
                    record['monitor_errors'].append(str(error) or type(error).__name__)
                    raise
                rss = sum(p['rss_kib'] for p in group)
                record['observed_peak_process_group_rss_kib'] = max(record['observed_peak_process_group_rss_kib'], rss)
                require(rss <= RSS_LIMIT_KIB, 'Bounded process group exceeded RSS limit')
                if identity['status'] == 5:
                    record['leader_identity_before_reap'] = identity
                    record['remaining_process_group'] = group
                    require(group == [], 'Native leader exited with live descendants')
                    break
                time.sleep(min(0.05, execution_remaining()))
            record['exit_status'] = process.wait(timeout=execution_remaining())
            require(record['exit_status'] == 0, 'Abnormal native exit')
        actual, stderr = (directory/'stdout.bin').read_bytes(), (directory/'stderr.txt').read_bytes()
        require(not stderr, 'Native stderr is not empty')
        runtime_expected = ('elixir=1.20.4\notp=29\nerts=17.1\nexecution=beam-jit\nschedulers_online=8\nwordsize=8\n'
            'architecture=aarch64-apple\ncommon_mutex_inherited=true\nsource_debug_bindings=2\nsubject_modules_recompiled=0\n'
            'main_beam_sha256='+main_sha+'\nsupport_beam_sha256='+support_sha+'\n')
        require((directory/'runtime.txt').read_text() == runtime_expected, 'Incomplete runtime/BEAM observation')
        record.update(status='bounded-output-passed', validation=output_validation(row['benchmark'], actual, expected),
                      subject_execution_mode_observed='beam-jit', exact_retained_modules_loaded=True,
                      native_common_mutex_inherited=True)
    except BaseException as error:
        record.update(status='failed', error=str(error) or type(error).__name__, error_type=type(error).__name__)
        if process is not None:
            cleanup_owned(process, record)
        raise
    finally:
        record['direct_child_reaped'] = process is not None and process.returncode is not None
        record['artifacts'] = {}
        for name in ('stdin.bin', 'expected.stdout', 'stdout.bin', 'stderr.txt', 'runtime-spec.txt', 'runtime.txt', 'erl-crash.dump'):
            path = directory/name
            if path.is_file():
                record['artifacts'][name] = dict(bytes=path.stat().st_size, sha256=sha(path))
        record['finished_at'] = datetime.now(timezone.utc).isoformat()
        save(directory/'process.json', record)
    return record


def run(args, lock):
    require(sha(args.plan) == args.plan_sha256, 'Plan differs from explicit reviewed hash')
    plan = json.loads(args.plan.read_bytes())
    require(plan['schema'] == 'elixir-retained-beam-bounded-plan-v1' and plan['controller_sha256'] == sha(__file__),
            'Wrong plan/controller')
    require(plan['planned_subject_main_executions'] == 156 and plan['distinct_reference_cases'] == 78,
            'Wrong planned execution scope')
    bounded_schedule(plan['profiles'])
    output = Path(plan['output']); require(not output.exists(), 'Fresh output required; no automatic retry')
    pins = dict(plan['pins']); pins[str(args.plan.resolve())] = args.plan_sha256
    for path, digest in pins.items():
        require(sha(path) == digest, 'Preflight input changed: '+path)
    output.mkdir(parents=True)
    report = dict(schema='elixir-retained-beam-bounded-results-v1', status='running', plan=str(args.plan.resolve()),
        plan_sha256=args.plan_sha256, pins=pins, profiles=[], cases=[], active=None,
        runtime_processes_started=0, qualified_bounded_cases=0, native_process_ids=[],
        subject_recompilations=0, oracle_generator_executions=0, benchmark_samples=0,
        source_work_qualified=False, canonical_loc=None, formatted_loc=None, chart_admission=False)
    save(output/'report.json', report)

    def launched(identity, label, pid):
        report['runtime_processes_started'] += 1
        report['native_process_ids'].append(dict(id=identity, case=label, pid=pid, pgid=pid))
        report['active'] = dict(id=identity, case=label, pid=pid)
        save(output/'report.json', report)

    try:
        for row in plan['profiles']:
            for case in row['bounded_cases']:
                lock_identity(lock)
                hot = row['physical_inputs']+row['beams']+[case['expected']]
                if case['stdin']:
                    hot.append(case['stdin'])
                for item in hot:
                    require(sha(item['path']) == item['sha256'], 'Active source/reference changed')
                directory = output/row['id']/case['case']
                report['active'] = dict(id=row['id'], case=case['case'], receipt=str(directory/'process.json'), pid=None)
                save(output/'report.json', report)
                result = observe(row, case, directory, plan, lock, launched)
                report['cases'].append(dict(id=row['id'], case=case['case'], process=str(directory/'process.json'),
                    process_sha256=sha(directory/'process.json'), status=result['status']))
                report['qualified_bounded_cases'] += 1; report['active'] = None
                save(output/'report.json', report)
            report['profiles'].append(row['id'])
            print('Validated retained Elixir bounded outputs: '+row['id'], flush=True)
        require(report['runtime_processes_started'] == report['qualified_bounded_cases'] == 156
                and len(report['profiles']) == 20, 'Incomplete bounded execution ledger')
        report.update(status='all20-bounded-output-passed-awaiting-compiled-work-and-LOC',
            bounded_outputs_qualified=True, subject_execution_mode_observed='beam-jit')
    except BaseException as error:
        report.update(status='failed', bounded_outputs_qualified=False,
                      error=str(error) or type(error).__name__, error_type=type(error).__name__)
        raise
    finally:
        integrity_errors = []
        for path, digest in pins.items():
            try:
                require(sha(path) == digest, 'Pinned input changed')
            except BaseException as error:
                integrity_errors.append(dict(path=path, error=str(error) or type(error).__name__))
        report['integrity_errors'] = integrity_errors
        if integrity_errors:
            report.update(status='failed-input-integrity', bounded_outputs_qualified=False)
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        save(output/'report.json', report)
        artifacts, artifact_errors = {}, []
        for path in output.rglob('*'):
            if path.is_file():
                try:
                    artifacts[str(path.relative_to(output))] = dict(sha256=sha(path), bytes=path.stat().st_size)
                except BaseException as error:
                    artifact_errors.append(dict(path=str(path), error=str(error) or type(error).__name__))
        if artifact_errors:
            report.update(status='failed-artifact-integrity', bounded_outputs_qualified=False, artifact_errors=artifact_errors)
            save(output/'report.json', report)
            artifacts['report.json'] = dict(sha256=sha(output/'report.json'), bytes=(output/'report.json').stat().st_size)
        lock_identity(lock)
        save(output/'terminal.json', dict(status=report['status'], report_sha256=sha(output/'report.json'),
            available_evidence=artifacts, integrity_errors=integrity_errors, artifact_errors=artifact_errors,
            runtime_processes_started=report['runtime_processes_started'], qualified_bounded_cases=report['qualified_bounded_cases'],
            common_mutex_held=True, subject_recompilations=0, benchmark_samples=0, source_work_qualified=False,
            canonical_loc=None, formatted_loc=None, chart_admission=False))
        require(not integrity_errors and not artifact_errors, 'Input or output integrity failed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--plan', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    prep.add_argument('--helper-terminal-sha256', required=True)
    native = sub.add_parser('run')
    native.add_argument('--plan', type=Path, required=True)
    native.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    require(sys.flags.isolated == 1 and sys.flags.no_site == 1 and sys.dont_write_bytecode,
            'Use the retained Python interpreter with -I -S -B')
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Elixir bounded qualification interrupted: '+str(signum))
    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, interrupted)
    with LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB); lock_identity(lock)
        if args.action == 'prepare':
            prepare(args)
        else:
            run(args, lock)


if __name__ == '__main__':
    main()
