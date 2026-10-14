"""Capture unchanged tree/pi Node mains once; no work or timing admission."""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/typescript/single-entry-work-v1'
BOUNDED_SHA = '31f1e5263cb332c6ca26ddf3017434cf76c49253904a2e330686ddbe02068e00'
OBSERVER_SHA = 'c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc'
PRIOR = ROOT/'experiments/typescript/bounded-v1'
PRIOR_PINS = {
    'plan-v1.json': '5156050046a006d2b1aa0068bc7b24302bd8fc3dd6d796d4b7dca7e4acf58c8a',
    'run-v1/report.json': 'd11f66e11071934d4bc7b27312c9d2b38adca7b045a9b490db6d16775c05ce29',
    'run-v1/terminal.json': '7b42777781781726488415999c7600e79afb92a0bc863cb3f0a326a9c4737662',
    'independent-results-review-v1.json': '7aa31fae40150228f1023b1cf8932feca3c8599d708f82189b8bdaf55c98609c',
}
STATIC_REVIEW = ROOT/'experiments/typescript/required-work-v1/static-review-v1.json'
STATIC_SHA = '454b93f894b4dba6edae697efa69fbe7b7e966c02a8e68e5d3a750da5d1fa71c'
INPUTS = {'binarytrees': 21, 'pidigits': 10000}
OUTPUTS = {'binarytrees': (455, '341de11a51feab3d8122b4b5d6a68b038a2d14434aa9bc2372f39300bf5f48e1'),
           'pidigits': (16893, 'bdfa7b6c756d96492f472f97aee9cc139bee954d271eacedfd7ace5d2875f06c')}
SUCCESS = 'two-single-entry-captures-retained-awaiting-native-work-review'


def require(value, message):
    if not value: raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def frozen(path, digest, name):
    import types
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'Frozen dependency changed: '+str(path))
    value = types.ModuleType(name); value.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), value.__dict__)
    return value


b = frozen(ROOT/'tools/qualification/typescript_bounded.py', BOUNDED_SHA, 'typescript_single_bounded')
# Separate namespace: original bounded receipts retain their original policy.
kb = frozen(ROOT/'tools/qualification/kotlin_bounded_v2.py', OBSERVER_SHA, 'typescript_single_observer')
require((kb.TIMEOUT, kb.CLEANUP_TIMEOUT, kb.FILE_LIMIT, kb.RSS_LIMIT) ==
        (30, 5, 8*1024**2, 2*1024**3), 'Original observer policy differs')
kb.TIMEOUT = 180
kb.FILE_LIMIT = 128*1024**2
kb.RSS_LIMIT = 10*1024**3
save, atomic = kb.save, kb.atomic


def inventory(directory, exclude=()):
    require(directory.is_dir() and not directory.is_symlink(), 'Physical artifact directory required')
    result = {}
    for path in sorted(directory.rglob('*')):
        require(not path.is_symlink() and (path.is_file() or path.is_dir()), 'Linked or nonregular artifact')
        name = str(path.relative_to(directory))
        if path.is_file() and name not in exclude:
            size = path.stat().st_size
            require(size <= kb.FILE_LIMIT+kb.PIPE_CHUNK, 'Artifact exceeds capture bound')
            result[name] = dict(bytes=size, sha256=sha(path))
    require(len(result) <= 100 and sum(x['bytes'] for x in result.values()) <= 768*1024**2,
            'Diagnostic artifact inventory exceeds bound')
    return result


def prerequisites(pins):
    docs = {name: b.document(PRIOR/name, digest, pins) for name, digest in PRIOR_PINS.items()}
    plan, report, terminal, review = docs.values()
    require(report['status'] == terminal['status'] == b.SUCCESS and
            report['plan_sha256'] == PRIOR_PINS['plan-v1.json'] and
            terminal['report_sha256'] == PRIOR_PINS['run-v1/report.json'] and
            report['active'] is None and report['qualified_cases'] == 149 and
            report['native_processes_started'] == terminal['native_processes_started'] == 149 and
            report['bounded_outputs_qualified'] is terminal['bounded_outputs_qualified'] is True and
            report['integrity_errors'] == terminal['integrity_errors'] == [] and
            report['process_receipt_errors'] == terminal['process_receipt_errors'] == [] and
            review['actual_native_processes'] == 149 and review['all_output_contracts_satisfied'] is True,
            'Closed independently reviewed TS149 required')
    require(plan['controller_sha256'] == BOUNDED_SHA and
            review['report']['sha256'] == PRIOR_PINS['run-v1/report.json'] and
            review['terminal']['sha256'] == PRIOR_PINS['run-v1/terminal.json'], 'Prior review linkage differs')
    actual = b.inventory(PRIOR/'run-v1', ('terminal.json',))
    require(actual == terminal['available_evidence'] and
            {k: v for k, v in actual.items() if k != 'report.json'} == report['artifacts'], 'Bounded closure changed')
    b.final_snapshot(report, actual)
    for name, record in actual.items(): b.bind(pins, PRIOR/'run-v1'/name, record['sha256'])
    for name, digest in plan['pins'].items(): b.bind(pins, name, digest)
    compiled = b.compiled_prerequisite(b.c.HERE/'run-v1/report.json', b.COMPILED_REPORT_SHA,
                                      b.COMPILED_TERMINAL_SHA, pins)
    require(compiled == plan['compiled'], 'Bounded compiled application binding differs')
    static = b.document(STATIC_REVIEW, STATIC_SHA, pins)
    require(static['static_contracts'] == 27 and len(static['profiles']) == 10 and
            all(p['static_workload_contracts_passed'] for p in static['profiles']), 'Static work review differs')
    return compiled


def expected_output(benchmark):
    if benchmark == 'pidigits':
        raw = (ROOT/'archive/workloads/pidigits/inputs/output-full.txt').read_bytes()
    else:
        require(benchmark == 'binarytrees', 'Unknown diagnostic workload')
        n = INPUTS[benchmark]
        lines = [f'stretch tree of depth {n+1}\t check: {(1 << (n+2))-1}\n']
        for depth in range(4, n+1, 2):
            count = 1 << (n-depth+4)
            lines.append(f'{count}\t trees of depth {depth}\t check: {count*((1 << (depth+1))-1)}\n')
        lines.append(f'long lived tree of depth {n}\t check: {(1 << (n+1))-1}\n')
        raw = ''.join(lines).encode('ascii')
    require((len(raw), hashlib.sha256(raw).hexdigest()) == OUTPUTS[benchmark], 'Complete output oracle differs')
    return raw


def diagnostic_options(benchmark):
    # Preserve V8's per-isolate names. CodeTracer's default name is short and
    # avoids both its 128-byte pathname buffer and isolate overwrite collisions.
    options = ['--log-code', '--log-function-events', '--log-deopt', '--logfile=v8.log',
        '--print-opt-code', '--print-opt-code-filter=*',
        '--print-maglev-code', '--trace-opt', '--trace-deopt', '--trace-osr',
        '--redirect-code-traces', '--print-bytecode',
        '--print-bytecode-filter='+('mainThread' if benchmark == 'binarytrees' else 'calculatePi'), '--trace-gc']
    if benchmark == 'pidigits':
        options += ['--print-builtin-code', '--print-builtin-code-filter=BigIntDivide*']
    return options


def command(plan, slot):
    if slot['kind'] == 'capabilities': return [plan['compiled']['node'], '--v8-options']
    row = next(p for p in plan['compiled']['profiles'] if p['benchmark'] == slot['benchmark'])
    return [plan['compiled']['node']] + diagnostic_options(slot['benchmark']) + [
        row['javascript']['path'], str(INPUTS[slot['benchmark']])]


def build_plan(output):
    b.physical(output)
    require(output.is_relative_to(PACKET) and output != PACKET and not output.exists(), 'Fresh diagnostic output required')
    pins = {}; compiled = prerequisites(pins)
    for path in (Path(__file__).resolve(), Path(__file__).with_name('test_typescript_single_entry.py'),
                 PACKET/'README.md', PACKET/'native-api-review.json'):
        b.bind(pins, path, sha(path))
    b.bind(pins, ROOT/'tools/qualification/typescript_bounded.py', BOUNDED_SHA)
    b.bind(pins, ROOT/'tools/qualification/kotlin_bounded_v2.py', OBSERVER_SHA)
    b.bind(pins, ROOT/'archive/workloads/pidigits/inputs/output-full.txt', OUTPUTS['pidigits'][1])
    return dict(schema='typescript-two-single-entry-plan-v1', status='prepared-awaiting-independent-review',
        controller=str(Path(__file__).resolve()), controller_sha256=sha(__file__), output=str(output),
        pins=pins, compiled=compiled, schedule=[dict(kind='capabilities', directory='00-capabilities'),
        dict(kind='subject', benchmark='binarytrees', directory='01-binarytrees'),
        dict(kind='subject', benchmark='pidigits', directory='02-pidigits')],
        diagnostic_options={n: diagnostic_options(n) for n in INPUTS}, inputs=INPUTS,
        native_processes=3, subject_main_invocations=2, compiler_invocations=0, automatic_retries=0,
        timeout_seconds=kb.TIMEOUT, cleanup_seconds=kb.CLEANUP_TIMEOUT,
        maximum_process_group_rss_bytes=kb.RSS_LIMIT, native_file_limit_bytes=kb.FILE_LIMIT,
        common_mutex_inode=79859134, required_work_qualified=False,
        runtime_dependency_closure_qualified=False, full_timings_qualified=False, benchmark_samples=0, chart_admission=False)


def capabilities(raw):
    text = raw.decode('utf-8')
    needed = {x.split('=')[0].removeprefix('--no-').removeprefix('--')
              for bench in INPUTS for x in diagnostic_options(bench)}
    for flag in needed:
        require(re.search(r'^  --'+re.escape(flag)+r' \(', text, re.M), 'Missing retained V8 option: '+flag)
    return dict(required_options=sorted(needed), retained_option_listing=True)


def split_stdout(raw, benchmark, pid):
    # Retain all original stdout. Only exact V8 GC envelopes are removed from
    # the derived application stream; no arbitrary warning filter is used.
    gc = []; other = []
    pattern = re.compile(rb'\['+str(pid).encode()+rb':0x[0-9a-fA-F]+\]\s+\d+ ms: '
        rb'(?:Scavenge|Mark-Compact|Minor Mark-Sweep)(?: \([^\r\n]*\))* '
        rb'\d+\.\d+ \(\d+\.\d+\) -> \d+\.\d+ \(\d+\.\d+\) MB, '
        rb'pooled: \d+ MB, \d+\.\d+ / \d+\.\d+ ms [^\r\n]*'
        rb'\(average mu = \d+\.\d+, current mu = \d+\.\d+\) [^\r\n]*; [^\r\n]*\n')
    for line in raw.splitlines(keepends=True):
        (gc if pattern.fullmatch(line) else other).append(line)
    remaining = b''.join(other); expected = expected_output(benchmark)
    require(remaining.endswith(expected), 'Complete prescribed stdout absent after native diagnostics')
    prefix = remaining[:-len(expected)]
    name = b'mainThread' if benchmark == 'binarytrees' else b'calculatePi'
    require(prefix.startswith(b'[generated bytecode for function: '+name+b' (') and
            prefix.count(b'[generated bytecode for function:') == 1 and
            re.search(rb'\nBytecode length: [1-9][0-9]*\n', prefix) and
            b'Source Position Table' in prefix and b'Handler Table' in prefix,
            'Missing or ambiguous outer-function Ignition bytecode')
    require(not re.search(rb'\[[0-9]+:0x[0-9a-fA-F]+\].* ms:', prefix), 'Unknown GC/output diagnostic envelope')
    return dict(bytecode=prefix, gc=b''.join(gc), subject=expected)


def checked_capture(plan, slot, directory, parent):
    native, stdout, stderr = native_receipt(directory, command(plan, slot), b.environment(directory), parent)
    require(stderr == b'', 'Unexpected diagnostics on stderr')
    result = dict(directory=slot['directory'], pid=native['pid'], started_at=native['started_at'],
                  finished_at=native['finished_at'], native_process_receipt_sha256=sha(directory/'process.json'))
    if slot['kind'] == 'capabilities': return dict(result, **capabilities(stdout)), {}
    parts = split_stdout(stdout, slot['benchmark'], native['pid'])
    code_files = sorted(directory.glob('code-*.asm')); log_files = sorted(directory.glob('isolate-*-v8.log'))
    require(code_files and log_files, 'Missing per-isolate native logs')
    for path in code_files:
        require(re.fullmatch(r'code-'+str(native['pid'])+r'(?:-[0-9]+)?\.asm', path.name), 'Unowned code trace')
    for path in log_files:
        require(re.fullmatch(r'isolate-0x[0-9a-fA-F]+-'+str(native['pid'])+r'-v8\.log', path.name), 'Unowned code-event log')
    code = b''.join(path.read_bytes() for path in code_files)
    log = b''.join(path.read_bytes() for path in log_files)
    require(code and log and b'Instructions (size = ' in code and b'code-creation,' in log,
            'Native generated-code capture absent')
    script = next(p['javascript']['path'] for p in plan['compiled']['profiles'] if p['benchmark'] == slot['benchmark'])
    require(script.encode() in log, 'Code event log does not name the exact emitted source')
    if slot['benchmark'] == 'pidigits':
        require(b'name = BigIntDivide' in code, 'Targeted BigInt division builtin capture absent')
    result.update(benchmark=slot['benchmark'], argument=INPUTS[slot['benchmark']],
        stdout_contract_satisfied=True, gc_trace_lines=len(parts['gc'].splitlines()),
        generated_code_bytes=len(code), code_event_bytes=len(log),
        code_trace_files=[path.name for path in code_files], code_event_files=[path.name for path in log_files],
        runtime_work_semantics_qualified=False, benchmark_samples=0)
    return result, parts


def finish(report, plan, output, pins, lock):
    errors = []; held = False
    try:
        b.verify(pins); kb.kh.verify_lock(lock); held = True
        registered = report['registered_commands']
        require(len({x['pid'] for x in registered}) == len(registered) == report['native_processes_started'],
                'Native registration count differs')
        require({str(p.relative_to(output)) for p in output.glob('*/process.json')} ==
                {x['directory']+'/process.json' for x in registered}, 'Native receipt inventory differs')
        for entry in registered:
            raw = json.loads((output/entry['directory']/'process.json').read_bytes())
            require(raw['pid'] == entry['pid'] and raw['direct_child_reaped'] is True and
                    raw.get('remaining_process_group', []) == raw.get('remaining_after_cleanup', []) == [] and
                    raw['cleanup_errors'] == [] and not raw.get('artifact_errors'), 'Unclosed owned process')
        for slot, result in zip(plan['schedule'], report['captures']):
            current, parts = checked_capture(plan, slot, output/slot['directory'], os.getpid())
            require(current == result, 'Validated capture changed')
            for name, data in parts.items():
                require((output/slot['directory']/(name+'.bin')).read_bytes() == data, 'Derived capture differs')
        if report['status'] == SUCCESS:
            require(len(report['captures']) == report['native_processes_started'] == 3, 'Incomplete three-process cohort')
        available = inventory(output, ('report.json', 'terminal.json'))
        for directory, snapshot in report['validated_artifacts'].items():
            require({n[len(directory)+1:]:v for n,v in available.items() if n.startswith(directory+'/')} == snapshot,
                    'Validated artifact changed before final inventory')
    except BaseException as error:
        errors.append(str(error) or type(error).__name__); available = {}
    report.update(active=None, finished_at=datetime.now(timezone.utc).isoformat(), integrity_errors=errors, artifacts=available)
    if errors: report['status'] = 'failed-integrity'
    save(output/'report.json', report)
    try:
        closure = inventory(output, ('terminal.json',))
        require({n:v for n,v in closure.items() if n != 'report.json'} == available, 'Final artifact closure changed')
        require(closure['report.json']['sha256'] == sha(output/'report.json'), 'Final report changed')
        b.verify(pins); held = False; kb.kh.verify_lock(lock); held = True
    except BaseException as error:
        errors.append(str(error) or type(error).__name__); report['status'] = 'failed-integrity'
        save(output/'report.json', report); closure = {}
    terminal = dict(schema='typescript-two-single-entry-terminal-v1', status=report['status'],
        report_sha256=sha(output/'report.json'), available_evidence=closure, integrity_errors=errors,
        native_processes_started=report['native_processes_started'], capture_count=len(report['captures']),
        common_mutex_held=held, common_mutex_inode=79859134, required_work_qualified=False,
        runtime_dependency_closure_qualified=False, full_timings_qualified=False, benchmark_samples=0, chart_admission=False)
    with (output/'terminal.json').open('x') as stream: json.dump(terminal, stream, indent=2); stream.write('\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='mode', required=True)
    prep = sub.add_parser('prepare'); prep.add_argument('--plan', type=Path, required=True); prep.add_argument('--output', type=Path, required=True)
    run = sub.add_parser('run'); run.add_argument('--plan', type=Path, required=True); run.add_argument('--plan-sha256', required=True)
    args = parser.parse_args(); b.physical(args.plan)
    def interrupted(signum, frame): raise KeyboardInterrupt('TypeScript capture interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS: signal.signal(sig, interrupted)
    with kb.LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB); kb.kh.verify_lock(lock); b.checked_python()
        if args.mode == 'prepare':
            require(not args.plan.exists() and not args.plan.is_relative_to(args.output), 'Fresh external plan required')
            plan = build_plan(args.output); b.verify(plan['pins']); b.c.package_inventory(plan['compiled']['packages'])
            kb.kh.verify_lock(lock); args.plan.parent.mkdir(parents=True, exist_ok=True)
            with args.plan.open('x') as stream: json.dump(plan, stream, indent=2); stream.write('\n')
            print(json.dumps(dict(plan=str(args.plan), sha256=sha(args.plan), native_processes=0))); return 0
        pins = {}; plan = b.document(args.plan, args.plan_sha256, pins); output = Path(plan['output'])
        require(plan == build_plan(output), 'Prepared capture plan differs')
        for name, digest in plan['pins'].items(): b.bind(pins, name, digest)
        b.verify(pins); output.mkdir(parents=True, exist_ok=False)
        report = dict(schema='typescript-two-single-entry-results-v1', status='running', plan=str(args.plan),
            plan_sha256=args.plan_sha256, pins=pins, started_at=datetime.now(timezone.utc).isoformat(),
            active=None, native_processes_started=0, registered_commands=[], captures=[], validated_artifacts={},
            required_work_qualified=False, runtime_dependency_closure_qualified=False,
            full_timings_qualified=False, benchmark_samples=0, chart_admission=False)
        save(output/'report.json', report)
        try:
            for slot in plan['schedule']:
                b.verify(pins); kb.kh.verify_lock(lock)
                directory = output/slot['directory']; directory.mkdir()
                for name in ('home','tmp'): (directory/name).mkdir()
                def launched(pid):
                    report['native_processes_started'] += 1
                    report['registered_commands'].append(dict(directory=slot['directory'], pid=pid))
                    report['active'] = dict(directory=slot['directory'], pid=pid); save(output/'report.json', report)
                kb.observe(command(plan, slot), b.environment(directory), directory, b'', lock, launched, kind='typescript-single-entry')
                result, parts = checked_capture(plan, slot, directory, os.getpid())
                for name, data in parts.items():
                    with (directory/(name+'.bin')).open('xb') as stream: stream.write(data)
                snapshot = inventory(directory)
                with atomic():
                    report['captures'].append(result); report['validated_artifacts'][slot['directory']] = snapshot
                    report['active'] = None; save(output/'report.json', report)
            report['status'] = SUCCESS
        except BaseException as error:
            report.update(status='failed', error=str(error) or type(error).__name__, error_type=type(error).__name__)
        finally:
            with atomic(): finish(report, plan, output, pins, lock)
        print(json.dumps(dict(status=report['status'], captures=len(report['captures']), report_sha256=sha(output/'report.json'))))
        return 0 if report['status'] == SUCCESS else 1


# The full normal-exit validator below uses the immutable observer's actual
# start/active/process schema with this packet's explicitly recorded bounds.

def native_receipt(directory, command, environment, parent):
    """Require the immutable observer's exact normal owned-exit envelope."""
    payload, kind, expected_exit = b"", "typescript-single-entry", 0
    start,active,final = [json.loads((directory/(n+'.json')).read_bytes()) for n in ('start','active','process')]
    for record in (start,active,final):
        require(record['command']==command and record['environment']==environment and record['cwd']==str(directory)
                and record['kind']==kind and record['started_at']==start['started_at']
                and type(record['stdin_bytes']) is int and record['stdin_bytes']==len(payload)
                and record['stdin_sha256']==hashlib.sha256(payload).hexdigest()
                and record['inherited_common_mutex'] is True and record['common_mutex_inode']==79859134
                and record['process_timeout_seconds']==kb.TIMEOUT and record['cleanup_timeout_seconds']==5
                and record['maximum_process_group_rss_bytes']==kb.RSS_LIMIT
                and record['native_file_limit_bytes']==kb.FILE_LIMIT
                and record['stdout_capture_limit_bytes']==kb.FILE_LIMIT+kb.PIPE_CHUNK
                and record['stdout_transport']=='OS pipe, retained as received'
                and record['stderr_transport']=='exclusive artifact'
                and record['benchmark_samples']==0 and record['source_work_qualified'] is record['chart_admission'] is False,
                'Native launch/input/resource policy differs')
    identity = final['identity']; leader = final['leader_identity_before_reap']
    require(start['status']=='starting' and start['native_process_started'] is False
            and active['status']=='running' and active['native_process_started'] is True
            and active['identity']==identity and final['native_process_started'] is True
            and type(parent) is int and parent>0 and identity['ppid']==parent,
            'Missing or unowned native start/active identity')
    for field in ('pid','pgid','ppid','birth_seconds','birth_microseconds'):
        require(type(identity[field]) is int and identity[field]==leader[field], 'Native birth identity changed')
    pid = final['pid']
    require(type(pid) is int and pid>0 and active['pid']==active['pgid']==pid==final['pgid']==identity['pid']==identity['pgid']
            and leader['status']==5 and final['direct_child_reaped'] is True
            and final['remaining_process_group']==[] and final.get('remaining_after_cleanup',[])==[]
            and final['stop_signals']==final['cleanup_errors']==[] and not final.get('artifact_errors')
            and not final.get('cleanup_signal_fallback') and final.get('timed_out',False) is False
            and type(final['kernel_monitor_samples']) is int and final['kernel_monitor_samples']>0
            and 0<final['observed_peak_process_group_rss_bytes']<=kb.RSS_LIMIT
            and b.stamp(start['started_at'])<=b.stamp(final['finished_at'])
            and type(final['exit_status']) is int and final['exit_status']==expected_exit,
            'Native process failed normal owned closure')
    if expected_exit==1:
        require(final['status']=='failed' and final.get('error_type')=='AssertionError'
                and final.get('error')=='Native command exited unsuccessfully', 'Unrelated failure cannot be an expected rejection')
    else:
        require(expected_exit==0 and final['status']=='native-passed'
                and not final.get('error') and not final.get('error_type'), 'Successful native receipt required')
    streams = []
    for name in ('stdout','stderr'):
        raw = (directory/(name+'.bin')).read_bytes()
        require(len(raw)==final[name+'_bytes'] and hashlib.sha256(raw).hexdigest()==final[name+'_sha256'], 'Native raw stream differs')
        streams.append(raw)
    return final,streams[0],streams[1]


if __name__ == "__main__": raise SystemExit(main())
