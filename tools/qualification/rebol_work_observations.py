"""Three bounded Rebol work observations after actual primitive19 approval.

This additive consumer reuses the unchanged shared149 intake and the original
owned observer. Its diagnostics produce no benchmark samples or admission.
Map dump stderr may be accepted only by the exact map consumer while its
original normal-zero/stderr observer failure remains unchanged.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import sys
import types

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/rebol/work-observations-v1'
HELPER = ROOT/'tools/qualification/rebol_bounded.py'
KIND = 'rebol-bounded-work-observation'
SUCCESS = 'three-work-observations-retained-awaiting-independent-review'
IDS = ('binarytrees-n4', 'pidigits-n27', 'knucleotide-arbitrary-widths')
CASES = (('binarytrees', 'n-4'), ('pidigits', 'n-27'), ('knucleotide', 'arbitrary-widths'))
CAPTURE_FILES = {'start.json','active.json','process.json','stdout.bin','stderr.bin'}
GATES = ('benchmark_correctness_qualified','runtime_source_equivalence_proven',
         'source_work_qualified','canonical_source_count_qualified',
         'full_timing_qualified','chart_admission')
MAP_FILES = ('knucleotide.reb','map_contract.py','test_map_contract.py','MAP.md')
FILES = {str(path.relative_to(ROOT)) for path in (
    Path(__file__).resolve(), Path(__file__).with_name('test_rebol_work_observations.py'),
    PACKET/'README.md', PACKET/'binarytrees.reb', PACKET/'tree_contract.py',
    PACKET/'test_tree_contract.py', PACKET/'TREE.md', PACKET/'pidigits.reb',
    PACKET/'pi-source-map.json', PACKET/'pi_oracle.py', PACKET/'test_pi_oracle.py', PACKET/'PI.md',
    *(PACKET/name for name in MAP_FILES))}
MAP_STDERR_LIMIT = 16*1024**2


def require(value, message):
    if not value:
        raise AssertionError(message)


def encoded(value): return (json.dumps(value, indent=2)+'\n').encode()
def digest(raw): return hashlib.sha256(raw).hexdigest()


def read_small(path, limit=2*1024**2):
    path = Path(path)
    require(path.is_absolute() and path.resolve(strict=True) == path, 'Physical absolute metadata required')
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), 'Regular metadata required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        held = os.fstat(fd)
        require((held.st_dev, held.st_ino) == (before.st_dev, before.st_ino), 'Metadata replaced before read')
        raw = stream.read(limit+1)
        require(len(raw) <= limit, 'Metadata exceeds intake bound')
        after = path.lstat()
        require(stat.S_ISREG(after.st_mode) and (after.st_dev, after.st_ino) == (held.st_dev, held.st_ino),
                'Metadata replaced during read')
    return raw


def ref(path, sha):
    require(Path(path).is_absolute() and type(sha) is str and re.fullmatch('[0-9a-f]{64}', sha),
            'Absolute evidence path and exact SHA256 required')
    return dict(path=str(path), sha256=sha)


def load(raw, path, name):
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def source_review(value):
    require(value['schema'] == 'rebol-three-work-observations-source-review-v1'
            and value['status'] == 'independent-source-review-complete-native-observations-pending'
            and value['independent_review'] is True and set(value['files']) == FILES
            and set(value['dependencies']) == {str(HELPER.relative_to(ROOT))}
            and all(value[key] is False for key in GATES), 'Exact independent observation source review required')


@contextmanager
def held(primitive_ref, bounded_source_ref, source_ref):
    raw = read_small(source_ref['path'])
    require(digest(raw) == source_ref['sha256'], 'Observation source review changed')
    initial = json.loads(raw)
    source_review(initial)
    helper_raw = read_small(HELPER)
    require(digest(helper_raw) == initial['dependencies'][str(HELPER.relative_to(ROOT))],
            'Original shared149 helper changed')
    r = load(helper_raw, HELPER, 'rebol_work_shared149')
    require(r.ROOT == ROOT and Path(r.__file__) == HELPER, 'Original helper location changed')
    with r.held(primitive_ref, bounded_source_ref) as inherited:
        p,e,adapter,checker,inspector,common,leases,intake,extension,review,pins,resolutions = inherited
        current = e.document(source_ref, pins, resolutions)
        require(current == initial, 'Source review changed after leases were acquired')
        for name, expected in {**current['files'], **current['dependencies']}.items():
            e.pin(pins, resolutions, ROOT/name, expected)
        consumers = {}
        for name, filename in (('tree','tree_contract.py'), ('pi','pi_oracle.py'), ('map','map_contract.py')):
            path = PACKET/filename
            raw = e.read_bytes(path)
            require(digest(raw) == pins[str(path)], 'Observation consumer changed before load')
            consumers[name] = load(raw, path, 'rebol_work_'+name+'_consumer')
        try:
            yield r,p,e,adapter,consumers,inspector,common,leases,intake,extension,review,pins,resolutions
        finally:
            e.check_leases(leases)


def schedule(e, cases, image, output):
    require(MAP_STDERR_LIMIT == 16*1024**2, 'Reviewed map dump stream policy required')
    require(tuple((case['benchmark'], case['case']) for case in cases) == CASES,
            'Only the three existing bounded inputs are allowed')
    slots = []
    for index, (identity, case) in enumerate(zip(IDS, cases)):
        directory = f'{index:02d}-'+identity
        destination = output/directory
        environment = e.environment(output)
        environment['MECH_CLBG_REBOL_PRIMITIVES'] = image['path']
        if index == 0:
            sidecar = destination/'observation.reb'
            command = [str(e.RUNTIME),'-q','-s',str(PACKET/'binarytrees.reb'),'4',str(sidecar)]
            consumer = 'tree'
        elif index == 1:
            sidecar = destination/'observation.tsv'
            command = [str(e.RUNTIME),'-q','-s',str(PACKET/'pidigits.reb'),'27']
            environment['MECH_REBOL_PI_OBSERVATION'] = str(sidecar)
            consumer = 'pi'
        else:
            sidecar = destination/'observation.tsv'
            command = [str(e.RUNTIME),'-q','-s',str(PACKET/'knucleotide.reb')]
            environment['MECH_REBOL_MAP_OBSERVATION'] = str(sidecar)
            consumer = 'map'
        require(all(name not in environment for name in ('DYLD_INSERT_LIBRARIES','DYLD_LIBRARY_PATH',
                'DYLD_FRAMEWORK_PATH','MECH_REBOL_IO_FAULT_REPORT')), 'Diagnostic interposer settings are forbidden')
        stderr_limit = MAP_STDERR_LIMIT if consumer == 'map' else 1024**2
        slots.append(dict(id=identity, directory=directory, command=command, environment=environment,
            case=case, consumer=consumer, sidecar=str(sidecar), timeout_seconds=180,
            rss_limit_bytes=512*1024**2, native_file_limit_bytes=max(1024**2, stderr_limit),
            stdout_limit_bytes=1024**2, stderr_limit_bytes=stderr_limit, sidecar_limit_bytes=1024**2,
            stdin_bytes=case['stdin']['bytes'], stdin_sha256=case['stdin']['sha256'],
            expected_exit=0, expected_observer_stderr_failure=consumer == 'map'))
    return slots


def build_plan(r,p,e,adapter,consumers,inspector,output,primitive_ref,bounded_source_ref,source_ref,
               intake,extension,review,pins,resolutions):
    e.physical(output)
    require(output.is_relative_to(PACKET) and output != PACKET and not os.path.lexists(output),
            'Fresh observation output inside its packet required')
    prior,closures,jobs,image = r.primitive_inputs(p,e,adapter,inspector,review,intake,extension,pins,resolutions)
    corpus = r.corpus(e,pins,resolutions)
    by_id = {(case['benchmark'], case['case']): case for case in corpus}
    cases = [by_id[identity] for identity in CASES]
    require([case['stdin']['bytes'] for case in cases] == [0,0,10299]
            and [case['expected']['bytes'] for case in cases] == [143,45,243]
            and [case['n'] for case in cases] == [4,27,0]
            and all(case['expected_exit'] == 0 and case['validation'] == 'exact-complete-bytes' for case in cases),
            'Existing three input/output contracts differ')
    expected_tree = e.read_bytes(r.CORPUS.parent/cases[0]['expected']['path'])
    require(consumers['tree'].EXPECTED_STDOUT == expected_tree, 'Tree consumer differs from corpus oracle')
    return dict(schema='rebol-three-work-observations-plan-v1', status='prepared-awaiting-independent-review',
        repository=str(ROOT), controller=str(Path(__file__).resolve()), controller_sha256=e.sha(__file__),
        output=str(output), primitive_review=primitive_ref, bounded_source_review=bounded_source_ref,
        source_review=source_ref, schedule=schedule(e,cases,image,output), extension_image=image,
        corrected_source=extension['corrected_source'], historical_sources_preserved=True,
        pins=dict(pins), input_resolutions=dict(resolutions), unavailable_inputs=prior['unavailable_inputs'],
        prerequisite_artifact_closures=closures, prior_durable_jobs=jobs, common_mutex_inode=79859134,
        cleanup_timeout_seconds=5, native_processes=3, compilations=0, matched_controls=0,
        automatic_retry=False, benchmark_samples=0, **{key:False for key in GATES})


def native_capture(r,e,kb,slot,directory,parent):
    """Independent receipt check; only map permits its exact normal-zero error."""
    require(Path(slot['sidecar']).parent == directory, 'Sidecar escaped its capture directory')
    snapshot = e.inventory(directory)[0]
    expected_files = CAPTURE_FILES | {Path(slot['sidecar']).name}
    require(set(snapshot) == expected_files, 'Exact observer and sidecar file set required')
    start,active,final = [json.loads(e.read_bytes(directory/(name+'.json')))
                          for name in ('start','active','process')]
    for value in (start,active,final):
        require(value['command'] == slot['command'] and value['environment'] == slot['environment']
            and value['cwd'] == str(directory) and value['kind'] == KIND and value['started_at'] == start['started_at']
            and value['process_timeout_seconds'] == slot['timeout_seconds'] and value['cleanup_timeout_seconds'] == 5
            and value['maximum_process_group_rss_bytes'] == slot['rss_limit_bytes']
            and value['native_file_limit_bytes'] == slot['native_file_limit_bytes']
            and value['stdout_capture_limit_bytes'] == slot['native_file_limit_bytes']+kb.PIPE_CHUNK
            and value['stdout_transport'] == 'OS pipe, retained as received' and value['stderr_transport'] == 'exclusive artifact'
            and value['stdin_bytes'] == slot['stdin_bytes'] and value['stdin_sha256'] == slot['stdin_sha256']
            and value['inherited_common_mutex'] is True and value['common_mutex_inode'] == 79859134
            and type(value['benchmark_samples']) is int and value['benchmark_samples'] == 0
            and value['source_work_qualified'] is value['chart_admission'] is False, 'Native launch or policy differs')
    identity,leader,pid = final['identity'],final['leader_identity_before_reap'],final['pid']
    require(start['status'] == 'starting' and start['native_process_started'] is False
        and active['status'] == 'running' and active['native_process_started'] is final['native_process_started'] is True
        and active['identity'] == identity and identity['ppid'] == parent
        and all(type(identity[key]) is int and identity[key] == leader[key]
                for key in ('pid','ppid','pgid','birth_seconds','birth_microseconds'))
        and type(pid) is int and pid > 0 and active['pid'] == active['pgid'] == pid == final['pgid'] == identity['pid'] == identity['pgid']
        and leader['status'] == 5 and final['direct_child_reaped'] is True
        and final['remaining_process_group'] == final.get('remaining_after_cleanup',[]) == []
        and final['stop_signals'] == final['cleanup_errors'] == [] and not final.get('artifact_errors')
        and not final.get('cleanup_signal_fallback') and final.get('timed_out',False) is False
        and type(final['kernel_monitor_samples']) is int and final['kernel_monitor_samples'] > 0
        and type(final['exit_status']) is int and final['exit_status'] == 0
        and r.stamp(start['started_at']) <= r.stamp(final['finished_at']), 'Normal owned zero-exit closure required')
    if slot['expected_observer_stderr_failure']:
        require(slot['consumer'] == 'map' and final['status'] == 'failed'
                and final.get('error_type') == 'AssertionError'
                and final.get('error') == 'Unexpected stderr; raw bytes retained', 'Unrelated failure is not a map dump')
    else:
        require(final['status'] == 'native-passed' and not final.get('error') and not final.get('error_type'),
                'Tree/Pi observer must pass without errors')
    peak = final['observed_peak_process_group_rss_bytes']
    require(type(peak) is int and 0 <= peak <= slot['rss_limit_bytes'], 'Invalid RSS observation')
    if peak == 0:
        require(identity['status'] == 5 and not final.get('live_rss_observation_obtained',False),
                'Zero RSS lacks initial owned zombie proof')
    streams = []
    for name in ('stdout','stderr'):
        raw = e.read_bytes(directory/(name+'.bin'))
        require(snapshot[name+'.bin'] == dict(bytes=len(raw),sha256=digest(raw))
                == dict(bytes=final[name+'_bytes'],sha256=final[name+'_sha256'])
                and len(raw) <= slot[name+'_limit_bytes'], 'Native stream changed or exceeded acceptance bound')
        streams.append(raw)
    sidecar = e.read_bytes(Path(slot['sidecar']))
    require(len(sidecar) <= slot['sidecar_limit_bytes'] and snapshot[Path(slot['sidecar']).name]
            == dict(bytes=len(sidecar),sha256=digest(sidecar)), 'Sidecar changed or exceeded acceptance bound')
    require(e.inventory(directory)[0] == snapshot, 'Capture changed during validation')
    return final,streams,sidecar,snapshot


def checked_case(r,e,adapter,consumers,kb,slot,directory,parent):
    final,streams,sidecar,snapshot = native_capture(r,e,kb,slot,directory,parent)
    expected = e.read_bytes(r.CORPUS.parent/slot['case']['expected']['path'])
    require(len(expected) == slot['case']['expected']['bytes']
            and digest(expected) == slot['case']['expected']['sha256'], 'Expected output changed')
    if slot['consumer'] == 'tree':
        decoded = consumers['tree'].validate(*streams,final['exit_status'],adapter.observation(sidecar))
    elif slot['consumer'] == 'pi':
        decoded = consumers['pi'].validate(*streams,final['exit_status'],sidecar,expected)
    else:
        payload = e.read_bytes(r.CORPUS.parent/slot['case']['stdin']['path'])
        require(len(payload) == slot['stdin_bytes'] and digest(payload) == slot['stdin_sha256'], 'Map input changed')
        decoded = consumers['map'].validate(payload,*streams,final['exit_status'],sidecar,expected)
    require(streams[0] == expected, 'Unchanged bounded stdout differs')
    require(e.inventory(directory)[0] == snapshot, 'Validated observations changed before adoption')
    return dict(id=slot['id'],pid=final['pid'],started_at=final['started_at'],finished_at=final['finished_at'],
        observer_status=final['status'],observations=decoded,
        accepted_map_stderr_failure=slot['expected_observer_stderr_failure'],
        observed_peak_process_group_rss_bytes=final['observed_peak_process_group_rss_bytes'] or None,
        rss_observation_complete=False,memory_usage_qualified=False),snapshot


def finish(r,e,kb,report,plan,output,pins,resolutions,leases):
    errors = []
    lock_confirmed = False
    available,artifact_errors = e.inventory(output,('report.json','terminal.json'),tolerant=True)
    try:
        require(report['attempts'] == list(IDS[:len(report['attempts'])]) and len(report['attempts']) <= 3,
                'Attempt prefix differs')
        require([item['id'] for item in report['registered']] == report['attempts'][:len(report['registered'])]
                and len({item['pid'] for item in report['registered']}) == len(report['registered'])
                and [item['id'] for item in report['captures']] == report['attempts'][:len(report['captures'])]
                and report['active'] is None, 'Registered/validated prefix differs')
        for slot in plan['schedule'][:len(report['attempts'])]:
            raw = json.loads(e.read_bytes(output/slot['directory']/'process.json'))
            registration = next((item for item in report['registered'] if item['id'] == slot['id']),None)
            require(raw['cleanup_errors'] == [] and not raw.get('artifact_errors'), 'Native cleanup failed')
            if registration:
                require(raw['pid'] == registration['pid'] and raw['direct_child_reaped'] is True
                        and raw.get('remaining_process_group',[]) == raw.get('remaining_after_cleanup',[]) == [],
                        'Registered process group not closed')
            else:
                require(raw['native_process_started'] is False, 'Unregistered process started')
        require(all(available.get(name) == value for name,value in report['validated_files'].items()),
                'Validated artifact changed')
        if report['status'] == SUCCESS:
            expected = {str(Path(slot['directory'])/name) for slot in plan['schedule']
                        for name in CAPTURE_FILES | {Path(slot['sidecar']).name}}
            require(len(report['attempts']) == len(report['registered']) == len(report['captures']) == 3
                    and set(available) == set(report['validated_files']) == expected, 'Three complete captures required')
        r.verify_inputs(e,plan,pins,resolutions,leases)
    except BaseException as error:
        errors.append(str(error) or type(error).__name__)
    report.update(active=None,finished_at=e.now(),integrity_errors=errors,artifact_errors=artifact_errors,artifacts=available)
    if errors or artifact_errors:
        report['status'] = 'failed-integrity'
    raw = encoded(report)
    kb.save(output/'report.json',report)
    closure = {}
    report_sha = None
    try:
        require(e.read_bytes(output/'report.json') == raw, 'Serialized report changed')
        closure = e.inventory(output,('terminal.json',))[0]
        require(closure == dict(available,**{'report.json':dict(bytes=len(raw),sha256=digest(raw))}),
                'Final inventory differs')
        r.verify_inputs(e,plan,pins,resolutions,leases)
        require(e.inventory(output,('terminal.json',))[0] == closure, 'Evidence changed during final input replay')
        report_sha = e.sha(output/'report.json')
        require(report_sha == digest(raw), 'Final report changed')
        e.check_leases(leases)
        lock_confirmed = True
    except BaseException as error:
        errors.append(str(error) or type(error).__name__)
        report['status'] = 'failed-integrity'
        closure = {}
        report_sha = None
    terminal = dict(schema='rebol-three-work-observations-terminal-v1',status=report['status'],
        report_sha256=report_sha,expected_report_sha256=digest(raw),available_evidence=closure,
        integrity_errors=errors,artifact_errors=artifact_errors,common_mutex_held=lock_confirmed,
        common_mutex_inode=79859134,native_processes_started=len(report['registered']),
        validated_observations=len(report['captures']),producer_success_is_not_qualification=True,
        benchmark_samples=0,**{key:False for key in GATES})
    with (output/'terminal.json').open('xb') as stream:
        stream.write(encoded(terminal))
    require(not errors and not artifact_errors, 'Final integrity failed; evidence retained')


def run(r,e,adapter,consumers,kb,plan,plan_path,plan_sha,pins,resolutions,common,leases):
    output = Path(plan['output'])
    e.pin(pins,resolutions,plan_path,plan_sha)
    r.verify_inputs(e,plan,pins,resolutions,leases)
    output.mkdir(parents=True,exist_ok=False)
    for name in ('home','tmp'):
        (output/name).mkdir()
    report = dict(schema='rebol-three-work-observations-results-v1',status='running',plan=str(plan_path),
        plan_sha256=plan_sha,started_at=e.now(),active=None,attempts=[],registered=[],captures=[],
        validated_files={},pins=pins,input_resolutions=resolutions,primitive_review=plan['primitive_review'],
        benchmark_samples=0,**{key:False for key in GATES})
    kb.save(output/'report.json',report)
    try:
        for slot in plan['schedule']:
            r.verify_inputs(e,plan,pins,resolutions,leases)
            require(e.inventory(output,('report.json',))[0] == report['validated_files'], 'Earlier observations changed')
            payload = e.read_bytes(r.CORPUS.parent/slot['case']['stdin']['path'])
            require(len(payload) == slot['stdin_bytes'] and digest(payload) == slot['stdin_sha256'], 'Input changed')
            directory = output/slot['directory']
            directory.mkdir()
            with kb.atomic():
                report['attempts'].append(slot['id'])
                kb.save(output/'report.json',report)
            def launched(pid):
                report['registered'].append(dict(id=slot['id'],pid=pid))
                report['active'] = dict(id=slot['id'],pid=pid)
                kb.save(output/'report.json',report)
            kb.TIMEOUT = slot['timeout_seconds']
            kb.RSS_LIMIT = slot['rss_limit_bytes']
            kb.FILE_LIMIT = slot['native_file_limit_bytes']
            kb.CLEANUP_TIMEOUT = 5
            try:
                kb.observe(slot['command'],slot['environment'],directory,payload,common,launched,kind=KIND)
            except AssertionError as error:
                if not slot['expected_observer_stderr_failure'] or str(error) != 'Unexpected stderr; raw bytes retained':
                    raise
            with kb.atomic():
                report['active'] = None
                capture,snapshot = checked_case(r,e,adapter,consumers,kb,slot,directory,os.getpid())
                if report['captures']:
                    require(r.stamp(report['captures'][-1]['finished_at']) <= r.stamp(capture['started_at']),
                            'Overlapping observations')
                report['captures'].append(capture)
                report['validated_files'].update({str(Path(slot['directory'])/name):value for name,value in snapshot.items()})
                kb.save(output/'report.json',report)
        report['status'] = SUCCESS
    except BaseException as error:
        with kb.atomic():
            report.update(status='stopped-unqualified',active=None,error=str(error) or type(error).__name__,error_type=type(error).__name__)
        raise
    finally:
        with kb.atomic():
            finish(r,e,kb,report,plan,output,pins,resolutions,leases)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='mode',required=True)
    prepare = commands.add_parser('prepare')
    prepare.add_argument('--plan',type=Path,required=True)
    prepare.add_argument('--output',type=Path,required=True)
    for name in ('primitive-review','bounded-source-review','source-review'):
        prepare.add_argument('--'+name,type=Path,required=True)
        prepare.add_argument('--'+name+'-sha256',required=True)
    execute = commands.add_parser('run')
    execute.add_argument('--plan',type=Path,required=True)
    execute.add_argument('--plan-sha256',required=True)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize,
            'Use retained Python -I -S -B')
    def stop(signum, frame):
        raise KeyboardInterrupt('Rebol work observation stopped: '+str(signum))
    for signum in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):
        signal.signal(signum,stop)
    saved = None
    if args.mode == 'prepare':
        primitive_ref = ref(args.primitive_review,args.primitive_review_sha256)
        bounded_source_ref = ref(args.bounded_source_review,args.bounded_source_review_sha256)
        source_ref = ref(args.source_review,args.source_review_sha256)
        output = args.output
    else:
        raw = read_small(args.plan,64*1024**2)
        require(digest(raw) == args.plan_sha256, 'Prepared plan changed')
        saved = json.loads(raw)
        primitive_ref,bounded_source_ref,source_ref = [saved[name] for name in ('primitive_review','bounded_source_review','source_review')]
        output = Path(saved['output'])
    with held(primitive_ref,bounded_source_ref,source_ref) as context:
        r,p,e,adapter,consumers,inspector,common,leases,intake,extension,review,pins,resolutions = context
        require(Path(sys.executable).resolve() == e.PYTHON.resolve(), 'Retained Python required')
        plan = build_plan(r,p,e,adapter,consumers,inspector,output,primitive_ref,bounded_source_ref,source_ref,
                          intake,extension,review,pins,resolutions)
        r.verify_inputs(e,plan,pins,resolutions,leases)
        if args.mode == 'prepare':
            e.physical(args.plan)
            require(args.plan.is_relative_to(PACKET) and not args.plan.is_relative_to(output), 'Separate packet plan required')
            args.plan.parent.mkdir(parents=True,exist_ok=True)
            raw = encoded(plan)
            with inspector.kb.atomic():
                with args.plan.open('xb') as stream:
                    stream.write(raw)
                r.verify_inputs(e,plan,pins,resolutions,leases)
                require(e.read_bytes(args.plan) == raw, 'Prepared plan changed')
                e.check_leases(leases)
            result = dict(plan=str(args.plan),sha256=digest(raw),native_processes_started=0)
        else:
            require(saved == plan, 'Prepared observation plan does not replay exactly')
            run(r,e,adapter,consumers,inspector.kb,plan,args.plan,args.plan_sha256,pins,resolutions,common,leases)
            result = dict(status=SUCCESS,output=str(output),qualified=False)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
