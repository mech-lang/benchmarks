#!/usr/bin/env python3
"""Wait for closed Prolog ownership, then prepare/run only Kotlin bounded v1.

The caller supplies durable ownership. This dispatcher owns the existing Prolog
leases and one common timing-lock descriptor across both in-process stage calls.
It never retries, resumes, recompiles a Kotlin subject, or grants qualification.
"""
import argparse
from contextlib import ExitStack, contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import stat
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
CONTROLLER = ROOT/'tools/qualification/kotlin_bounded.py'
CONTROLLER_SHA = '916a94f68e191cce8d074121859121351517c8ab2132bb5953ebc62621ba710e'
PROLOG_PLAN = ROOT/'experiments/prolog/full90-v1/plan.json'
PROLOG_PLAN_SHA = '55c09837581e1ed1ff0d317ec86155733962d68122338a353d3b0dce4fa8db6a'
PROLOG_JOB = ROOT/'experiments/prolog/full90-v1/owned-jobs/full90'
COHORT = ROOT/'experiments/prolog/prolog-full90.owner.lock'
LOCK = Path('/tmp/mech-clbg-timing.lock')
LOCK_INODE = 79859134
PLAN = ROOT/'experiments/kotlin/bounded-work-v1/plan-v1.json'
OUTPUT = ROOT/'experiments/kotlin/bounded-work-v1/run-v1'
SIGNALS = {signal.SIGINT, signal.SIGTERM, signal.SIGHUP}
COMPLETE = 'all20-bounded-output-passed-awaiting-work-JIT-and-LOC'


def require(value, message):
    if not value:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def document(path, pins):
    raw = Path(path).read_bytes()
    value = json.loads(raw)
    pins[str(Path(path).resolve())] = digest(raw)
    return value


def unchanged(pins):
    for path, expected in pins.items():
        require(digest(Path(path).read_bytes()) == expected, 'Changed dispatch input: '+path)


@contextmanager
def atomic():
    previous = signal.pthread_sigmask(signal.SIG_BLOCK, SIGNALS)
    try:
        yield
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous)


def save(path, value, first=False):
    temporary = path if first else path.with_name(path.name+'.tmp')
    with atomic():
        with temporary.open('x') as stream:
            json.dump(value, stream, indent=2)
            stream.write('\n'); stream.flush(); os.fsync(stream.fileno())
        if not first:
            os.replace(temporary, path)


def lease_identity(path, handle, expected=None):
    held, named = os.fstat(handle.fileno()), path.stat()
    require(stat.S_ISREG(path.lstat().st_mode) and
            (held.st_dev, held.st_ino) == (named.st_dev, named.st_ino), 'Lease replaced: '+str(path))
    if expected is not None:
        require((held.st_dev, held.st_ino) == expected, 'Held lease identity changed')
    if path == LOCK:
        require(held.st_ino == LOCK_INODE, 'Original timing mutex changed')
    return held.st_dev, held.st_ino


def acquire(path, stack, record, receipt, leases):
    record['waiting_for'] = str(path); save(receipt, record)
    handle = stack.enter_context(path.open('rb'))  # Never create/recreate a lease.
    identity = lease_identity(path, handle)
    fcntl.flock(handle, fcntl.LOCK_EX)  # Signal handlers raise: waiting is interruptible.
    lease_identity(path, handle, identity)
    leases.append((path, handle, identity))
    record['held_leases'].append(dict(path=str(path), device=identity[0], inode=identity[1], acquired_at=now()))
    record['waiting_for'] = None; save(receipt, record)
    return handle


def prolog_closed(pins):
    plan = document(PROLOG_PLAN, pins)
    require(pins[str(PROLOG_PLAN)] == PROLOG_PLAN_SHA and plan['repository'] == str(ROOT), 'Wrong Prolog plan')
    items = {name: document(PROLOG_JOB/(name+'.json'), pins)
             for name in ('request', 'launch', 'worker-started', 'command-started', 'terminal')}
    request, started, ended = items['request'], items['command-started'], items['terminal']
    command = [str(PYTHON), '-I', '-S', '-B', '-u', plan['controller'], 'run',
               '--plan', str(PROLOG_PLAN), '--plan-sha256', PROLOG_PLAN_SHA]
    require(request['schema_version'] == 1 and request['command'] == command and
            request['cwd'] == str(ROOT) and request['common_mutex_owned_by_target_command'] is True,
            'Wrong Prolog durable request')
    for name in ('launch', 'worker-started', 'command-started'):
        require(items[name]['command'] == command and items[name]['cwd'] == str(ROOT), 'Prolog durable argv/cwd differ')
    for item in (request, items['launch'], ended):
        require(item['automatic_retry'] is False and item['qualification_granted'] is False, 'Prolog durable policy changed')
    require(ended['status'] == 'command-exited-zero-awaiting-report-review' and
            type(ended['exit_code']) is int and ended['exit_code'] == 0 and
            ended['actual_command_started'] is True and ended['stop_signals'] == [] and
            ended['command_identity_observation_missing'] is started['command_identity_observation_missing'] is False and
            type(started['command_pid']) is int and started['command_pid'] > 0 and
            ended['command_pid'] == started['command_pid'] and
            ended['command_identity'] == started['command_identity'] and
            isinstance(ended['command_identity'], dict), 'Prolog durable command did not close cleanly')
    worker = items['worker-started']
    require(worker['inherited_private_lease'] is True and worker['detached_session'] is True and
            worker['common_mutex_owned_by_target_command'] is True and worker['qualification_granted'] is False,
            'Prolog durable worker ownership differs')
    require(not any(ended.get(k) for k in ('error', 'error_type', 'exception_cleanup', 'error_log_write_failure')),
            'Prolog durable terminal contains errors')
    output = Path(plan['output'])
    terminal = document(output/'terminal.json', pins)
    report = document(output/'report.json', pins)
    require(terminal['report'] == str(output/'report.json') and
            terminal['report_sha256'] == pins[str(output/'report.json')], 'Prolog terminal/report binding differs')
    require(report['status'] in ('complete', 'complete-with-unqualified-profiles') and
            report['status'] == terminal['status'] and report['active'] is None and
            report['plan'] == str(PROLOG_PLAN) and report['plan_sha256'] == PROLOG_PLAN_SHA and
            report['pins_unchanged_at_end'] is True and terminal['common_mutex_held'] is True and
            terminal['integrity_errors'] == [] and
            report['native_launch_unconfirmed_attempts'] == terminal['native_launch_unconfirmed_attempts'] == [] and
            not any(report.get(k) for k in ('error', 'error_type', 'terminal_integrity_errors')),
            'Prolog report is not a clean completed cohort')
    require(len(report['attempts']) + len(report['skipped_failed_profile_slots']) == 90 and
            report['completed_benchmarks'] == report['benchmark_order'] and len(report['completed_benchmarks']) == 10 and
            report['full_performance_runs'] == terminal['full_performance_runs'] == terminal['saved_attempts'] == len(report['attempts']) and
            report['supervisor']['pid'] == started['command_pid'], 'Prolog cohort completion accounting differs')
    return dict(plan_sha256=PROLOG_PLAN_SHA, report_sha256=pins[str(output/'report.json')],
                terminal_sha256=pins[str(output/'terminal.json')], status=report['status'],
                measurement_qualification_inferred=False)


def load_controller():
    raw = CONTROLLER.read_bytes()
    require(digest(raw) == CONTROLLER_SHA, 'Frozen Kotlin bounded controller changed')
    spec = importlib.util.spec_from_file_location('kotlin_dispatch_bounded', CONTROLLER)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(CONTROLLER), 'exec'), module.__dict__)
    return module


def result_files():
    pins = {}; result = {}
    for name in ('report', 'terminal'):
        path = OUTPUT/(name+'.json')
        if path.exists():
            item = document(path, pins)
            result[name] = dict(path=str(path), sha256=pins[str(path)], status=item.get('status'))
            if name == 'report':
                result['native_processes_started'] = item.get('native_processes_started')
    return result


def completed(plan_sha):
    pins = {}; plan = document(PLAN, pins)
    report = document(OUTPUT/'report.json', pins); terminal = document(OUTPUT/'terminal.json', pins)
    require(pins[str(PLAN)] == plan_sha and plan['controller_sha256'] == CONTROLLER_SHA and
            plan['output'] == str(OUTPUT), 'Bounded plan changed')
    require(report['schema'] == 'kotlin-retained-classes-bounded-results-v1' and
            report['status'] == terminal['status'] == COMPLETE and report['bounded_outputs_qualified'] is True and
            report['active'] is None and report['plan'] == str(PLAN) and report['plan_sha256'] == plan_sha and
            terminal['report_sha256'] == pins[str(OUTPUT/'report.json')] and
            terminal['common_mutex_held'] is True and terminal['common_mutex_inode'] == LOCK_INODE,
            'Bounded stage did not finish with bound report/terminal')
    for key, expected in dict(native_processes_started=157, diagnostic_compiler_processes_started=1,
            bounded_jvm_processes_started=156, qualified_bounded_cases=156,
            observed_subject_main_invocations=156, observed_subject_main_returns=156).items():
        require(type(report[key]) is int and type(terminal[key]) is int and
                report[key] == terminal[key] == expected, 'Incomplete bounded count: '+key)
    require(report['profiles'] == [p['id'] for p in plan['profiles']] and len(report['profiles']) == 20 and
            len(report['cases']) == 156 and {(c['id'],c['case']) for c in report['cases']} ==
            {(p['id'],c['case']) for p in plan['profiles'] for c in p['bounded_cases']} and
            all(c['status'] == 'bounded-output-passed' for c in report['cases']), 'Incomplete bounded cases')
    for item in (report, terminal):
        require(item['integrity_errors'] == item['process_receipt_errors'] == [] and item.get('artifact_errors', []) == [] and
                item['source_work_qualified'] is False and item['chart_admission'] is False and
                item['full_timings_qualified'] is False and item['canonical_loc'] is item['formatted_loc'] is None,
                'Bounded errors or unexpected admission')
    unchanged(pins)
    return dict(report=dict(path=str(OUTPUT/'report.json'),sha256=pins[str(OUTPUT/'report.json')],status=report['status']),
                terminal=dict(path=str(OUTPUT/'terminal.json'),sha256=pins[str(OUTPUT/'terminal.json')],status=terminal['status']),
                native_processes_started=report['native_processes_started'])


def dispatch(args):
    receipt = args.receipt.resolve()
    require(not receipt.exists() and not receipt.with_name(receipt.name+'.tmp').exists() and
            not PLAN.exists() and not OUTPUT.exists() and not receipt.is_relative_to(OUTPUT) and
            receipt.is_relative_to(ROOT/'experiments/kotlin/dispatch-v1'), 'Fresh dispatch/plan/output required')
    pins = {str(Path(__file__).resolve()):args.dispatcher_sha256, str(CONTROLLER):CONTROLLER_SHA}
    unchanged(pins)
    receipt.parent.mkdir(parents=True, exist_ok=True)
    record = dict(schema='kotlin-bounded-dispatch-v1', status='waiting-for-Prolog-closure', started_at=now(),
                  dispatcher_pid=os.getpid(), dispatcher_sha256=args.dispatcher_sha256,
                  controller=str(CONTROLLER), controller_sha256=CONTROLLER_SHA,
                  plan=str(PLAN), output=str(OUTPUT), held_leases=[], waiting_for=None,
                  prepare_called=False, run_called=False, bounded_stage_completed=False,
                  automatic_retry=False, qualification_granted=False, pins=pins)
    save(receipt, record, first=True)
    with ExitStack() as stack:
        leases = []
        try:
            acquire(PROLOG_JOB/'owner.lock', stack, record, receipt, leases)
            acquire(COHORT, stack, record, receipt, leases)
            record['prolog_closure'] = prolog_closed(pins)
            lock = acquire(LOCK, stack, record, receipt, leases)
            pins[str(PYTHON)] = PYTHON_SHA
            unchanged(pins)
            module = load_controller(); module.kh.verify_lock(lock)
            require(not PLAN.exists() and not OUTPUT.exists(), 'Bounded output appeared while waiting')
            record.update(status='preparing', prepare_called=True, preparation_started_at=now()); save(receipt,record)
            module.prepare(SimpleNamespace(plan=PLAN, output=OUTPUT))
            plan_sha = digest(PLAN.read_bytes()); pins[str(PLAN)] = plan_sha
            record.update(plan_sha256=plan_sha, preparation_finished_at=now()); unchanged(pins)
            record.update(status='running', run_called=True, run_started_at=now()); save(receipt,record)
            module.run(SimpleNamespace(plan=PLAN, plan_sha256=plan_sha), lock)
            record['validated_stage_result'] = completed(plan_sha)
            unchanged(pins)
            record.update(status='bounded-stage-completed-awaiting-review', bounded_stage_completed=True)
        except BaseException as error:
            record.update(status='failed', bounded_stage_completed=False, error=str(error) or type(error).__name__, error_type=type(error).__name__)
            raise
        finally:
            with atomic():
                errors = []
                try:
                    record['stage_result'] = result_files()
                    if record['bounded_stage_completed'] and record['stage_result'] != record['validated_stage_result']:
                        errors.append('Completed report/terminal changed after validation')
                except BaseException as error: errors.append('Result receipt: '+str(error))
                for path, handle, identity in leases:
                    try: lease_identity(path, handle, identity)
                    except BaseException as error: errors.append(str(error))
                try: unchanged(pins)
                except BaseException as error: errors.append(str(error))
                if errors: record.update(status='failed-dispatch-integrity', bounded_stage_completed=False)
                record.update(integrity_errors=errors, finished_at=now(), held_leases_verified_at_finalization=not errors)
                save(receipt,record)
                require(not errors, 'Dispatch finalization integrity failed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--dispatcher-sha256', required=True)
    args = parser.parse_args()
    require(Path(sys.executable).resolve() == PYTHON.resolve() and sys.flags.isolated and sys.flags.no_site and
            sys.flags.dont_write_bytecode and not sys.flags.optimize, 'Use pinned Python -I -S -B without -O')
    def interrupted(signum, frame): raise KeyboardInterrupt('Kotlin dispatcher interrupted: '+str(signum))
    for sig in SIGNALS: signal.signal(sig, interrupted)
    dispatch(args)


if __name__ == '__main__': main()
