"""Capture only the two unstarted objdump outputs after the closed Julia stage.

The original nine LLVM outputs and failed stage remain immutable prerequisites.
No Julia execution, compilation, link, benchmark, or semantic admission occurs.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
CONTROLLER = Path(__file__).resolve()
ADAPTER = ROOT/'tools/qualification/julia_native_inspection_metadata.py'
ADAPTER_SHA = 'e04a33233e6faddae3ce7a1f05d93da13044214ef5764f2679f1c6bc15c023bb'
PACKET = ROOT/'experiments/julia-aot/trimmed-native-inspection-v1'
PRIOR_OUTPUT = PACKET/'run-v1'
PRIOR_PLAN = PACKET/'plan-v1.json'
PRIOR_PLAN_SHA = 'a182fb691175b4e9c13747d952b052fb1657286694816bb5ff0f044a6536d9b5'
PRIOR_REPORT_SHA = '9a06ba1f951aa9a6fccd9e84e11e6083c7315d3fe250b892913071e4d6912864'
PRIOR_TERMINAL_SHA = '33a26e625200c6f7fff108e082bca26b7969c9500944356229b76d9d8e50fab9'
PRIOR_DURABLE = ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/julia-offline-inspection11-v1/terminal.json'
PRIOR_DURABLE_SHA = 'd6874f4356877f5fea821210d8d2a0e4d62721f4296254b8ec3f94767e18944e'
PRIOR_REVIEW = PACKET/'nine-capture-closure-review-v1.json'
PRIOR_REVIEW_SHA = 'b42756efcb779e11e1e6350ac8ec44ef9812b190cf7754fb3e3cc68e9a0043c4'
SUCCESS = 'two-remaining-offline-captures-retained-awaiting-native-owner-and-fallback-review'


def require(value, message):
    if not value:
        raise AssertionError(message)


def load_inspector():
    raw = ADAPTER.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == ADAPTER_SHA, 'Frozen metadata adapter changed')
    module = types.ModuleType('julia_remaining_metadata'); module.__file__ = str(ADAPTER)
    exec(compile(raw, str(ADAPTER), 'exec'), module.__dict__)
    return module.install(module.load_original())


j = load_inspector()
kb = j.kb


def memory_observation(final):
    """Report sample availability without changing the observer or its limits.

    A zero is accepted only when registration already observed this same child
    as a zombie. There is then no live process RSS sample in this receipt. A live
    registration followed by zero remains ambiguous and is rejected. Raw JSON
    is never rewritten, and sampled maxima never establish complete memory use.
    """
    peak = final['observed_peak_process_group_rss_bytes']
    require(type(peak) is int and 0 <= peak <= kb.RSS_LIMIT, 'Invalid or oversized observed RSS')
    if peak == 0:
        require(final['identity']['status'] == final['leader_identity_before_reap']['status'] == 5,
                'Zero RSS lacks an already-exited owned identity')
        require(final.get('live_rss_observation_obtained', False) is False,
                'Zero RSS conflicts with a recorded live observation')
    return dict(raw_observed_peak_process_group_rss_bytes=peak,
                observed_peak_process_group_rss_bytes=peak if peak else None,
                live_rss_observation_obtained=peak > 0,
                rss_observation_status='sampled-peak' if peak else 'unavailable-before-live-sample',
                rss_observation_complete=False, memory_usage_qualified=False)


def checked_capture(slot, directory, parent):
    # The frozen inspector's launch, identity, exit, stream and cleanup checks
    # are retained here; only the positive-RSS postcondition is replaced by the
    # explicit unavailable-observation disposition above.
    snapshot = j.inventory(directory)
    require(set(snapshot) == {'start.json','active.json','process.json','stdout.bin','stderr.bin'},
            'Unexpected native files')
    start, active, final = [json.loads((directory/(n+'.json')).read_bytes()) for n in ('start','active','process')]
    for record in (start, active, final):
        require(record['command'] == slot['command'] and record['environment'] == j.environment(directory)
            and record['cwd'] == str(directory) and record['kind'] == j.KIND
            and record['started_at'] == start['started_at'] and record['stdin_bytes'] == 0
            and record['stdin_sha256'] == j.EMPTY_SHA and record['inherited_common_mutex'] is True
            and record['common_mutex_inode'] == 79859134 and record['process_timeout_seconds'] == kb.TIMEOUT
            and record['cleanup_timeout_seconds'] == kb.CLEANUP_TIMEOUT
            and record['maximum_process_group_rss_bytes'] == kb.RSS_LIMIT
            and record['native_file_limit_bytes'] == j.FILE_LIMIT
            and record['stdout_capture_limit_bytes'] == j.FILE_LIMIT+kb.PIPE_CHUNK
            and record['stdout_transport'] == 'OS pipe, retained as received'
            and record['stderr_transport'] == 'exclusive artifact'
            and record['benchmark_samples'] == 0
            and record['source_work_qualified'] is record['chart_admission'] is False,
            'Native launch contract differs')
    identity, leader, pid = final['identity'], final['leader_identity_before_reap'], final['pid']
    require(start['status'] == 'starting' and start['native_process_started'] is False
        and active['status'] == 'running' and active['native_process_started'] is True
        and final['native_process_started'] is True and active['identity'] == identity
        and type(parent) is int and parent > 0 and identity['ppid'] == parent
        and all(type(identity[k]) is int and identity[k] == leader[k]
                for k in ('pid','ppid','pgid','birth_seconds','birth_microseconds'))
        and type(pid) is int and pid > 0
        and active['pid'] == active['pgid'] == pid == final['pgid'] == identity['pid'] == identity['pgid']
        and leader['status'] == 5 and final['direct_child_reaped'] is True
        and final['remaining_process_group'] == final.get('remaining_after_cleanup',[]) == []
        and final['stop_signals'] == final['cleanup_errors'] == [] and not final.get('artifact_errors')
        and not final.get('cleanup_signal_fallback') and final.get('timed_out',False) is False
        and final['status'] == 'native-passed' and type(final['exit_status']) is int and final['exit_status'] == 0
        and not final.get('error') and not final.get('error_type')
        and type(final['kernel_monitor_samples']) is int and final['kernel_monitor_samples'] > 0
        and j.stamp(start['started_at']) <= j.stamp(final['finished_at']),
        'Native ownership or normal exit differs')
    memory = memory_observation(final)
    for name in ('stdout','stderr'):
        require(snapshot[name+'.bin'] == {'bytes':final[name+'_bytes'],'sha256':final[name+'_sha256']},
                'Captured stream changed')
    require(final['stdout_bytes'] > 0 and final['stderr_bytes'] == 0, 'Empty offline capture or unexpected stderr')
    require(j.inventory(directory) == snapshot, 'Capture changed during validation')
    return dict(id=slot['id'],directory=slot['directory'],pid=pid,started_at=final['started_at'],finished_at=final['finished_at'],
        stdout_bytes=final['stdout_bytes'],stdout_sha256=final['stdout_sha256'],process_sha256=snapshot['process.json']['sha256'],
        captured_native_output=True,**memory,**{k:False for k in j.FALSE_GATES}), snapshot


def prior_evidence(pins):
    """Replay the exact closed failure, preserving all nine raw captures."""
    plan = j.document(PRIOR_PLAN, PRIOR_PLAN_SHA, pins)
    report = j.document(PRIOR_OUTPUT/'report.json', PRIOR_REPORT_SHA, pins)
    terminal = j.document(PRIOR_OUTPUT/'terminal.json', PRIOR_TERMINAL_SHA, pins)
    durable = j.document(PRIOR_DURABLE, PRIOR_DURABLE_SHA, pins)
    review = j.document(PRIOR_REVIEW, PRIOR_REVIEW_SHA, pins)
    require(plan['controller'] == str(ADAPTER) and plan['controller_sha256'] == ADAPTER_SHA
        and plan['output'] == str(PRIOR_OUTPUT) and plan['native_commands'] == 11,
        'Original prepared stage identity differs')
    prefix = [s['directory'] for s in plan['schedule'][:9]]
    require(prefix == [f'{n:02}-decode-{n:02}' for n in range(9)]
        and [s['id'] for s in plan['schedule'][9:]] == ['native-archive','final-executable'],
        'Original schedule differs')
    require(report['status'] == terminal['status'] == 'failed'
        and report['plan_sha256'] == PRIOR_PLAN_SHA
        and report['error'] == 'Native ownership or normal exit differs' and report['error_type'] == 'AssertionError'
        and report['attempted_commands'] == prefix and report['active'] is None
        and report['native_processes_started'] == terminal['native_processes_started'] == 9
        and terminal['capture_count'] == len(report['captures']) == 8
        and terminal['integrity_errors'] == report['integrity_errors'] == []
        and terminal['common_mutex_held'] is True and terminal['common_mutex_inode'] == 79859134
        and terminal['report_sha256'] == PRIOR_REPORT_SHA
        and all(report[k] is terminal[k] is False for k in j.FALSE_GATES),
        'Original failure disposition differs')
    require(durable['status'] == 'command-failed' and durable['exit_code'] == 1
        and durable['actual_command_started'] is True and durable['stop_signals'] == []
        and durable['qualification_granted'] is durable['automatic_retry'] is False
        and durable['command_identity_observation_missing'] is False
        and durable['command_identity']['pid'] == durable['command_pid']
        and j.stamp(durable['started_at']) <= j.stamp(report['started_at'])
        and j.stamp(report['finished_at']) <= j.stamp(durable['finished_at']),
        'Original durable closure differs')
    available = j.inventory(PRIOR_OUTPUT, ('terminal.json',))
    require(available == terminal['available_evidence'] and len(available) == 46
        and {n:v for n,v in available.items() if n != 'report.json'} == report['artifacts'],
        'Original artifact closure differs')
    captures = []
    for index, slot in enumerate(plan['schedule'][:9]):
        capture, snapshot = checked_capture(slot, PRIOR_OUTPUT/slot['directory'], durable['command_pid'])
        if index < 8:
            old_capture, old_snapshot = j.checked_capture(slot, PRIOR_OUTPUT/slot['directory'], durable['command_pid'])
            require(old_capture == report['captures'][index]
                and snapshot == old_snapshot == report['validated_artifacts'][slot['directory']],
                'Previously accepted decode changed')
        else:
            require(capture['raw_observed_peak_process_group_rss_bytes'] == 0
                and capture['observed_peak_process_group_rss_bytes'] is None,
                'Ninth capture availability differs')
        captures.append(capture)
    require(report['registered_commands'] == [dict(directory=c['directory'],pid=c['pid']) for c in captures]
        and len({c['pid'] for c in captures}) == 9, 'Original registration differs')
    for first, second in zip(captures, captures[1:]):
        require(j.stamp(first['finished_at']) <= j.stamp(second['started_at']), 'Original commands overlapped')
    require(review['status'] == 'failed-stage-closed-nine-raw-captures-preserved'
        and review['not_started'] == ['09-native-archive','10-final-executable']
        and review['native_processes_started'] == 9 and review['original_controller_accepted_captures'] == 8,
        'Independent closure review differs')
    require(all(not os.path.lexists(PRIOR_OUTPUT/s['directory']) for s in plan['schedule'][9:]),
            'A remaining command already has prior artifacts')
    for name, ref in available.items():
        j.pin(pins, PRIOR_OUTPUT/name, ref['sha256'])
    return plan, dict(original_status='failed', original_accepted_captures=8,
        retained_raw_captures=captures, ninth_capture_disposition='native-output-retained-RSS-unavailable',
        artifacts=available, review=dict(path=str(PRIOR_REVIEW),sha256=PRIOR_REVIEW_SHA),
        prior_plan=dict(path=str(PRIOR_PLAN),sha256=PRIOR_PLAN_SHA),
        prior_report=dict(path=str(PRIOR_OUTPUT/'report.json'),sha256=PRIOR_REPORT_SHA),
        prior_terminal=dict(path=str(PRIOR_OUTPUT/'terminal.json'),sha256=PRIOR_TERMINAL_SHA),
        prior_durable_terminal=dict(path=str(PRIOR_DURABLE),sha256=PRIOR_DURABLE_SHA))


def build_plan(output):
    # Rebuild the frozen eleven-command intake first. Only its last two commands
    # are scheduled; all native artifacts and declared runtime/tool pins stay.
    base = j.build_plan(output)
    old, prior = prior_evidence(base['pins'])
    expected = dict(base, output=old['output'], commands=old['commands'], pins=old['pins'],
                    input_resolutions=old['input_resolutions'])
    require(expected == old, 'Original input/tool/schedule reconstruction differs')
    require(all(base['pins'].get(n) == digest for n,digest in old['pins'].items()), 'Original pins changed')
    for path in (CONTROLLER, CONTROLLER.with_name('test_julia_native_inspection_remaining.py'), PACKET/'REMAINING-TWO.md'):
        j.pin(base['pins'], path)
    base.update(schema='julia-two-remaining-offline-inspection-plan-v1', controller=str(CONTROLLER),
        controller_sha256=j.sha(CONTROLLER), native_commands=2, preserved_prior_stage=prior,
        remaining_original_slots=[9,10], schedule=base['schedule'][9:], commands=base['commands'][9:],
        rss_observation_policy='raw zero requires an already-zombie owned identity; derived peak null; no memory qualification',
        rss_observation_complete=False, memory_usage_qualified=False)
    base['input_resolutions'] = {n:str(Path(n).resolve()) for n in base['pins']}
    return base


def verify(pins, resolutions, plan):
    j.verify(pins, resolutions, plan['tool_closure']['unavailable_candidates'])
    require(j.inventory(PRIOR_OUTPUT, ('terminal.json',)) == plan['preserved_prior_stage']['artifacts'],
            'Preserved nine-capture inventory changed')
    require(all(not os.path.lexists(PRIOR_OUTPUT/d) for d in ('09-native-archive','10-final-executable')),
            'Original stage acquired new command artifacts')


def finish(report, plan, output, pins, resolutions, lock):
    errors=[]; available={}; held=False
    try:
        verify(pins,resolutions,plan); kb.kh.verify_lock(lock); held=True
        entries=report['registered_commands']; attempts=report['attempted_commands']
        require(attempts == [s['directory'] for s in plan['schedule'][:len(attempts)]] and len(attempts) <= 2,
                'Remaining command sequence differs')
        require(len(entries) == report['native_processes_started'] <= len(attempts)
            and [e['directory'] for e in entries] == attempts[:len(entries)]
            and len({e['pid'] for e in entries}) == len(entries), 'Native registration differs')
        require({str(p.relative_to(output)) for p in output.glob('*/process.json')}
            == {d+'/process.json' for d in attempts}, 'Native receipt inventory differs')
        for directory in attempts:
            rec=json.loads((output/directory/'process.json').read_bytes())
            expected=next((e for e in entries if e['directory'] == directory),None)
            require(rec['cleanup_errors'] == [] and not rec.get('artifact_errors'), 'Failed cleanup/artifact retention')
            if expected:
                require(rec['native_process_started'] is True and rec['pid'] == expected['pid']
                    and rec['direct_child_reaped'] is True
                    and rec.get('remaining_process_group',[]) == rec.get('remaining_after_cleanup',[]) == [],
                    'Owned process not closed')
            else:
                require(rec['native_process_started'] is False and not rec.get('pid'), 'Unregistered native process')
        for slot,capture in zip(plan['schedule'],report['captures']):
            current,snapshot=checked_capture(slot,output/slot['directory'],os.getpid())
            require(current == capture and snapshot == report['validated_artifacts'][slot['directory']],
                    'Validated capture changed')
        require(len(report['captures']) == len(report['validated_artifacts']), 'Capture snapshot inventory differs')
        for previous,current in zip(report['captures'],report['captures'][1:]):
            require(j.stamp(previous['finished_at']) <= j.stamp(current['started_at']), 'Native commands overlapped')
        if report['status'] == SUCCESS:
            require(len(report['captures']) == len(entries) == len(attempts) == 2, 'Incomplete remaining stage')
        available=j.inventory(output,('report.json','terminal.json'))
        for directory,snapshot in report['validated_artifacts'].items():
            require({n[len(directory)+1:]:v for n,v in available.items() if n.startswith(directory+'/')} == snapshot,
                    'Final inventory adopted changed validated bytes')
    except BaseException as error:
        errors.append(str(error) or type(error).__name__)
    report.update(active=None,finished_at=datetime.now(timezone.utc).isoformat(),integrity_errors=errors,artifacts=available)
    if errors: report['status']='failed-integrity'
    expected_report=(json.dumps(report,indent=2)+'\n').encode()
    kb.save(output/'report.json',report)
    try:
        closure=j.inventory(output,('terminal.json',))
        require({n:v for n,v in closure.items() if n != 'report.json'} == available, 'Final artifact closure changed')
        require(closure['report.json'] == dict(bytes=len(expected_report),sha256=hashlib.sha256(expected_report).hexdigest()),
                'Final report changed')
        held=False
        verify(pins,resolutions,plan)
        require(j.inventory(output,('terminal.json',)) == closure, 'Captured bytes changed during final input verification')
        held=False; kb.kh.verify_lock(lock); held=True
    except BaseException as error:
        errors.append(str(error) or type(error).__name__); report['status']='failed-integrity'; closure={}
        kb.save(output/'report.json',report)
    terminal=dict(schema='julia-two-remaining-offline-inspection-terminal-v1',status=report['status'],
        report_sha256=j.sha(output/'report.json'),available_evidence=closure,integrity_errors=errors,
        native_processes_started=report['native_processes_started'],capture_count=len(report['captures']),
        common_mutex_held=held,common_mutex_inode=79859134,benchmark_samples=0,candidate_executions=0,
        rss_observation_complete=False,memory_usage_qualified=False,**{k:False for k in j.FALSE_GATES})
    with (output/'terminal.json').open('x') as stream:
        stream.write(json.dumps(terminal,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__); sub=parser.add_subparsers(dest='mode',required=True)
    prep=sub.add_parser('prepare'); prep.add_argument('--plan',type=Path,required=True); prep.add_argument('--output',type=Path,required=True)
    run=sub.add_parser('run'); run.add_argument('--plan',type=Path,required=True); run.add_argument('--plan-sha256',required=True)
    args=parser.parse_args(); j.physical(args.plan)
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
            and Path(sys.executable).resolve() == kb.kh.PYTHON.resolve(), 'Use exact retained Python -I -S -B without -O')
    def interrupted(signum,frame):
        raise KeyboardInterrupt('Julia remaining inspection interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS: signal.signal(sig,interrupted)
    with kb.LOCK.open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); kb.kh.verify_lock(lock)
        require(j.sha(kb.kh.PYTHON) == kb.kh.PYTHON_SHA, 'Retained Python changed')
        if args.mode == 'prepare':
            require(not os.path.lexists(args.plan) and not args.plan.is_relative_to(args.output), 'Fresh external plan required')
            plan=build_plan(args.output); verify(plan['pins'],plan['input_resolutions'],plan); kb.kh.verify_lock(lock)
            args.plan.parent.mkdir(parents=True,exist_ok=True)
            with args.plan.open('x') as stream: stream.write(json.dumps(plan,indent=2)+'\n')
            print(json.dumps(dict(plan=str(args.plan),sha256=j.sha(args.plan),native_processes_started=0))); return 0
        pins={}; plan=j.document(args.plan,args.plan_sha256,pins); output=Path(plan['output'])
        require(plan == build_plan(output), 'Concrete remaining plan differs')
        pins.update(plan['pins']); resolutions=dict(plan['input_resolutions'],**{str(args.plan):str(args.plan.resolve())})
        verify(pins,resolutions,plan); output.mkdir(parents=True,exist_ok=False)
        report=dict(schema='julia-two-remaining-offline-inspection-results-v1',status='running',plan=str(args.plan),
            plan_sha256=args.plan_sha256,controller_sha256=j.sha(CONTROLLER),pins=pins,input_resolutions=resolutions,
            preserved_prior_stage=plan['preserved_prior_stage'],started_at=datetime.now(timezone.utc).isoformat(),
            active=None,attempted_commands=[],registered_commands=[],native_processes_started=0,captures=[],
            validated_artifacts={},benchmark_samples=0,candidate_executions=0,rss_observation_complete=False,
            memory_usage_qualified=False,**{k:False for k in j.FALSE_GATES})
        kb.save(output/'report.json',report)
        try:
            for slot in plan['schedule']:
                names=set(plan['tool_closure']['images']) | set(plan['tool_closure']['named_path_resolutions'])
                names.add(slot['input']['path'])
                verify({n:pins[n] for n in names},{n:resolutions[n] for n in names},plan); kb.kh.verify_lock(lock)
                directory=output/slot['directory']; directory.mkdir()
                for name in ('home','tmp'): (directory/name).mkdir()
                report['attempted_commands'].append(slot['directory']); kb.save(output/'report.json',report)
                def launched(pid):
                    report['native_processes_started']+=1
                    report['registered_commands'].append(dict(directory=slot['directory'],pid=pid))
                    report['active']=dict(directory=slot['directory'],pid=pid); kb.save(output/'report.json',report)
                kb.observe(slot['command'],j.environment(directory),directory,b'',lock,launched,kind=j.KIND)
                capture,snapshot=checked_capture(slot,directory,os.getpid())
                with kb.atomic():
                    report['captures'].append(capture); report['validated_artifacts'][slot['directory']]=snapshot
                    report['active']=None; kb.save(output/'report.json',report)
            report['status']=SUCCESS
        except BaseException as error:
            report.update(status='failed',error=str(error) or type(error).__name__,error_type=type(error).__name__)
        finally:
            with kb.atomic(): finish(report,plan,output,pins,resolutions,lock)
        print(json.dumps(dict(status=report['status'],captures=len(report['captures']),report_sha256=j.sha(output/'report.json'))))
        return 0 if report['status'] == SUCCESS else 1


if __name__ == '__main__':
    raise SystemExit(main())
