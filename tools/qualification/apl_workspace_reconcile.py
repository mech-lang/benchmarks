"""Independent six-process APL tree reconciliation; no producer is imported.

The future exact plan/report/terminal and durable terminal hashes are explicit
inputs. Three APL observations and three controls are accepted only as one
complete cohort; the optimized alias creates no additional native sample.
"""
import argparse
import copy
from contextlib import contextmanager, ExitStack
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import stat
import statistics
import sys
import types

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'experiments/apl/binarytrees-workspace-v1'
PACKET=BASE/'full6-v1'
PRODUCER=ROOT/'tools/qualification/apl_workspace_full.py'
HELPER=ROOT/'tools/qualification/prolog_reconcile.py'
HELPER_SHA='a69b498cc0664b2951c1ef5ef2281f06f34e6415fcf6adfe8b723f06ca127cfe'
PYTHON=Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
PYTHON_SHA='ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
LOCK=Path('/tmp/mech-clbg-timing.lock')
JOBS=ROOT/'experiments/shared/owned-jobs-v1/owned-jobs'
JOB=JOBS/'apl-binarytrees-full6-v1'
OLD_LEASES={JOBS/name/'owner.lock':inode for name,inode in (
    ('apl-workspace-bounded5-v1',82370343),('apl-workspace-remaining3-v1',82374025),
    ('apl-scope-isolated2-v1',82382998),('apl-whole-subject2-v1',82384399))}
SUBJECT_ID='apl-binarytrees-workspace200-compact'
SUBJECT_KEY='binarytrees:apl-workspace200-compact'
ALIAS_KEY='binarytrees:apl-workspace200-optimized'
CONTROL_KEY='binarytrees:apl-workspace200-full-study:mech-control'
SOURCE=ROOT/'archive/comparisons/r-apl-uiua-comparison/20261011/sources/apl/binarytrees.compact.apl'
SOURCE_SHA='d1293d125d2d65940137d2d624402d4931f74d1f031bc2261165ad6663c57e74'
SETUP=BASE/'setup.apl'
SETUP_SHA='3adce52a2aea05cc00ee13e011655749f5a03bc81d37a4ee8eb13c14f227e58c'
WARNING='\nWARNING: File pipe-to_client still open - closing it\n'
TIMEOUT,OUTER_TIMEOUT=14400,15000
REFERENCE=dict(bytes=455,sha256='341de11a51feab3d8122b4b5d6a68b038a2d14434aa9bc2372f39300bf5f48e1')
BOUND_REVIEW=BASE/'whole-subject-v1/actual-bounded-work-review-v1.json'
BOUND_REVIEW_SHA='b92ef3f6b7ff7f15e21f754cf608fa583f65ac0874b189553cfc2c68bdf9d468'
OWNER_REVIEW=BASE/'scope-isolated-v1/actual-ownership-review-v1.json'
OWNER_REVIEW_SHA='1fb964c7d73c174e540b71ada594b8b435d9466dc2d9ecc55ba6a3db88059f76'
FAILED_REPORTS={BASE/'bounded-run-v1/report.json':'daff19879de9ab9e7b30574a29195224340b24a9f7b3e080baa0b5f539335388',
    BASE/'remaining-three-v1/run-v1/report.json':'98a72540c56d68d8ef45c51aa77d4b8c6054ed2513396a1504d0bd85e27b210b'}
SCHEMA='apl-workspace-independent-full6-reconciliation-v1'
AGGREGATE={'samples_seconds','sample_validation','attempts','measurement_status','median_seconds','sample_stdev_seconds',
           'time_x_mech','matched_mech_control','matched_mech_source_sha256'}
r=p=None


def require(value,message):
    if not value:raise ValueError(message)


def encoded(value):return (json.dumps(value,indent=2,allow_nan=False)+'\n').encode()
def sha(raw):return hashlib.sha256(raw).hexdigest()
def same(a,b,message):require(json.dumps(a,sort_keys=True,allow_nan=False)==json.dumps(b,sort_keys=True,allow_nan=False),message)


@contextmanager
def regular(path):
    path=Path(path);require(path.is_absolute() and path.resolve()==path,'Physical absolute file required')
    before=path.lstat();require(stat.S_ISREG(before.st_mode),'Regular file required')
    fd=os.open(path,os.O_RDONLY|os.O_NONBLOCK|os.O_NOFOLLOW)
    with os.fdopen(fd,'rb') as stream:
        held=os.fstat(fd);require((held.st_dev,held.st_ino)==(before.st_dev,before.st_ino),'Input replaced before open')
        yield stream
        named=path.lstat();require(stat.S_ISREG(named.st_mode) and (held.st_dev,held.st_ino)==(named.st_dev,named.st_ino),'Input replaced during read')


def read(path):
    with regular(path) as stream:return stream.read()


def file_sha(path):
    with regular(path) as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


class Files:
    def __init__(self):self.pins={};self.resolutions={}
    def physical(self,path):
        path=Path(path);target=Path(self.resolutions.get(str(path),str(path)))
        require(path.is_absolute() and target.is_absolute() and path.resolve()==target and target.resolve()==target,
                'Original input resolution changed: '+str(path))
        return target
    def verify(self,path,expected):
        path=Path(path);require(isinstance(expected,str) and len(expected)==64 and all(c in '0123456789abcdef' for c in expected),'Explicit SHA256 required')
        target=self.physical(path)
        require(file_sha(target)==expected and self.physical(path)==target,'Input changed: '+str(path))
        require(str(path) not in self.pins or self.pins[str(path)]==expected,'Conflicting input pin')
        self.pins[str(path)]=expected
    def document(self,ref):
        require(set(ref)>={'path','sha256'},'Exact evidence reference required')
        path=Path(ref['path']);self.verify(path,ref['sha256']);target=self.physical(path);raw=read(target)
        require(self.physical(path)==target,'Document name changed during read')
        require(sha(raw)==ref['sha256'],'Document changed during read')
        return p.strict_json(raw)


def load_primitives(files):
    global r,p,POWER,FAILURE_GATES,kernel_identity
    files.verify(HELPER,HELPER_SHA)
    raw=read(HELPER);require(sha(raw)==HELPER_SHA,'Independent reader changed before loading')
    r=types.ModuleType('apl_full6_independent_receipts');r.__file__=str(HELPER)
    exec(compile(raw,str(HELPER),'exec'),r.__dict__)
    p=r.p;POWER=r.POWER;FAILURE_GATES=r.FAILURE_GATES;kernel_identity=r.kernel_identity
    files.verify(r.HELPER,r.HELPER_SHA)


def alias():
    return dict(key=ALIAS_KEY,variant='optimized',source_alias_of=SUBJECT_KEY,timing_alias_of=SUBJECT_KEY,
                additional_native_processes=0,optimization_claim=False)


def schedule(plan,producer_sha):
    require(plan['schema']=='apl-workspace-qualified-full6-plan-v1' and plan['repository']==str(ROOT)
        and plan['controller']==str(PRODUCER) and plan['controller_sha256']==producer_sha
        and plan['pins'][str(PRODUCER)]==producer_sha,'Exact reviewed producer input required')
    require(plan['samples']==plan['apl_samples']==plan['matched_mech_samples']==3 and plan['full_processes']==6
        and plan['maximum_live_native_groups']==1 and plan['minimum_inherited_lock_fd']==64
        and plan['continuous_common_mutex'] is True and plan['common_mutex_inode']==79859134
        and plan['original_files_mutated'] is False and plan['no_automatic_retry'] is True
        and plan['stop_on_first_unqualified_attempt'] is True,'Six-slot timing policy changed')
    for name in ('compiler_invocations','fixture_reexecutions','bounded_reexecutions','native_count_reexecutions','new_native_probes'):
        require(type(plan[name]) is int and plan[name]==0,'Unexpected native preparation: '+name)
    require(all(plan[k] is False for k in ('full_size_work_qualified','full_timings_qualified','chart_admission')),'Plan cannot pre-admit results')
    same(plan['source_aliases'],[alias()],'Alias creates a second measured implementation')
    require(set(plan['manifests'])=={'binarytrees'},'Only binary trees belongs to this cohort')
    m=plan['manifests']['binarytrees'];rows=m['profiles'];ids=[SUBJECT_ID,'mech-aot-control']
    orders=[dict(round=i+1,profiles=ids[i%2:]+ids[:i%2]) for i in range(3)]
    require(m['benchmark']=='binarytrees' and m['size']==21 and m['samples']==3
        and m['timeout_seconds']==TIMEOUT and m['supervisor_timeout_seconds']==OUTER_TIMEOUT
        and m['maximum_rss_mib']==10240 and m['canonical_full_workload'] is True
        and m['runtime_startup_parsing_setup_output_shutdown_inside_timer'] is True
        and m['no_automatic_retry'] is True and m['chart_admission'] is False and m['shared_timing_lock']==str(LOCK),
        'Canonical work, timing boundary or limits differ')
    same(m['full_output_reference'],REFERENCE,'Complete stdout oracle changed');same(m['orders'],orders,'Rotation differs')
    same([x['id'] for x in rows],ids,'Wrong real source/control');same([x['key'] for x in rows],[SUBJECT_KEY,CONTROL_KEY],'Profile keys differ')
    same([x['language'] for x in rows],['apl','mech'],'Language roles changed')
    subject,control=rows
    require(subject['source_sha256']==SOURCE_SHA and subject['source_bundle']==[
        dict(path=str(SOURCE),sha256=SOURCE_SHA,canonical_loc=40,physical_loc=40),
        dict(path=str(SETUP),sha256=SETUP_SHA,canonical_loc=1,physical_loc=1)]
        and subject['canonical_loc']==subject['physical_loc']==subject['loc']==41
        and subject['setup_inside_timer'] is True and subject['maximum_workers']==1
        and subject['formatted_loc'] is None and subject['formatted_loc_qualified'] is False,
        'Complete source/setup bundle or serial runtime differs')
    same(subject['command'],[subject['binary'],'--cc','1','-f',str(SETUP),'-f',subject['source'],'--','{n}'],
         'Measured setup/source invocation differs')
    require(subject['support_pins'][str(SETUP)]==SETUP_SHA
        and subject['support_pins'][subject['runtime_binary']['path']]==subject['runtime_binary']['sha256']
        and subject['source_work_qualified'] is subject['canonical_source_count_qualified'] is True,
        'Source/runtime prerequisite missing')
    require(control['id']=='mech-aot-control' and control['command']==[control['binary'],'{n}']
        and control['maximum_workers']==8 and control['chart_admission'] is False,'Matched control scope differs')
    for path,expected in dict(FAILED_REPORTS,**{str(BOUND_REVIEW):BOUND_REVIEW_SHA,str(OWNER_REVIEW):OWNER_REVIEW_SHA}).items():
        require(plan['pins'].get(str(path))==expected,'Prior failed or bounded evidence missing')
    require(subject['source_count_review']==plan['qualification']['counts'] and subject['required_work_review']==plan['qualification']['work'],
            'Qualification refs differ from measured profile')
    keys={x['id']:x['key'] for x in rows}
    slots=[['binarytrees',v['round'],identity,keys[identity]] for v in orders for identity in v['profiles']]
    same(plan['schedule'],slots,'Missing, repeated or reordered slot')
    return slots,{x['key']:x for x in rows}


def check_stderr(attempt,row):
    require(attempt['stderr']==(WARNING if row['language']=='apl' else ''),'Exact stderr policy changed')


def check_durable(durable,plan_ref,plan):
    request,launch,worker,started,ended=[durable[k] for k in ('request','launch','worker-started','command-started','terminal')]
    command=[str(PYTHON),'-I','-S','-B',str(PRODUCER),'run','--plan',plan_ref['path'],'--plan-sha256',plan_ref['sha256']]
    for value in (request,launch,worker,started):
        same(value['command'],command,'Durable target argv changed');require(value['cwd']==str(ROOT),'Original evidence cwd required')
    require(request['schema_version']==1 and request['common_mutex_owned_by_target_command'] is True
        and worker['inherited_private_lease'] is worker['detached_session'] is worker['common_mutex_owned_by_target_command'] is True,
        'Owned durable lifecycle differs')
    for value in (request,launch,ended):require(value['automatic_retry'] is value['qualification_granted'] is False,'Durable admission/retry changed')
    require(worker['qualification_granted'] is False and ended['status']=='command-exited-zero-awaiting-report-review'
        and type(ended['exit_code']) is int and ended['exit_code']==0 and ended['actual_command_started'] is True
        and ended['command_identity_observation_missing'] is started['command_identity_observation_missing'] is False
        and ended['stop_signals']==[] and not any(ended.get(k) for k in ('error','error_type','exception_cleanup','error_log_write_failure')),
        'Durable worker did not close successfully')
    same(p.process_identity(ended['command_identity']),p.process_identity(started['command_identity']),'Controller birth changed')
    same(p.process_identity(ended['worker_identity']),p.process_identity(worker['worker_identity']),'Worker birth changed')
    same(p.process_identity(launch['worker_identity']),p.process_identity(worker['worker_identity']),'Launch worker changed')
    require(started['command_pid']==ended['command_pid']==started['command_identity']['pid']
        and p.process_identity(started['command_identity'])[2]==' '.join(command)
        and started['command_identity']['listing'].split(None,2)[1]==str(worker['worker_identity']['pid']),
        'Durable controller argv or parent differs')
    require(p.timestamp(request['created_at'])<=p.timestamp(worker['started_at'])<=p.timestamp(started['started_at'])<=p.timestamp(ended['finished_at']),
            'Durable chronology differs')


def qualification(plan,files):
    counts=files.document(plan['qualification']['counts']);work=files.document(plan['qualification']['work'])
    require(counts['schema']=='apl-binarytrees-workspace-qualified-source-counts-v1'
        and counts['canonical_LOC_admitted'] is True and counts['canonical_loc']==counts['physical_loc']==41
        and counts['formatted_loc'] is None and counts['formatted_loc_qualified'] is False
        and counts['distinct_authored_main_sources']==1 and counts['setup_assignment_included'] is True,
        'Independent complete source-count disposition required')
    same(counts['source_forms'],['compact','optimized'],'Source alias labels differ')
    require(work['schema']=='apl-binarytrees-workspace-required-work-v1'
        and work['status']=='qualified-source-work-awaiting-full-size-timing' and work['source_work_qualified'] is True
        and work['workload_n']==21 and work['source_sha256']==SOURCE_SHA and work['setup_sha256']==SETUP_SHA
        and work['workspace_scale']==200 and work['maximum_workers']==1 and work['previous_failures_preserved'] is True
        and work['source_counts']==plan['qualification']['counts'],'Qualified unchanged N21 source work required')
    same(work['bounded_subject_review'],dict(path=str(BOUND_REVIEW),sha256=BOUND_REVIEW_SHA),'Bounded work review differs')
    same(work['bounded_ownership_review'],dict(path=str(OWNER_REVIEW),sha256=OWNER_REVIEW_SHA),'Native owner review differs')
    for value in (counts,work):
        require(all(value[k] is False for k in ('full_size_work_qualified','full_timing_qualified','chart_admission')),'Prerequisite prequalified native full run')
        for name,expected in value['inputs'].items():
            path=Path(name);require(not path.is_absolute() and '..' not in path.parts,'Repository-relative qualification input required')
            require(plan['pins'].get(str(ROOT/path))==expected,'Qualifier input omitted from measured pins');files.verify(ROOT/path,expected)
    checker_ref=counts['checker'];require(checker_ref['path']==str(ROOT/'tools/qualification/apl_workspace_source_units.py'),'Wrong exact owner checker')
    for ref in (checker_ref,counts['source_owner_review']):
        require(plan['pins'].get(ref['path'])==ref['sha256'],'Source owner prerequisite was not measured')
    files.verify(Path(checker_ref['path']),checker_ref['sha256'])
    checker_raw=read(Path(checker_ref['path']))
    require(sha(checker_raw)==checker_ref['sha256'],'Owner checker changed before loading')
    module=types.ModuleType('apl_full6_exact_source_owners');module.__file__=checker_ref['path']
    exec(compile(checker_raw,checker_ref['path'],'exec'),module.__dict__)
    require(plan['pins'].get(str(module.READER))==module.READER_SHA,'Original source reader was not pinned')
    files.verify(module.READER,module.READER_SHA)
    source_bytes={identity:read(ROOT/row['path']) for identity,row in module.SOURCES.items()}
    count=module.count_bundle(source_bytes);owner=files.document(counts['source_owner_review'])
    same(owner['count'],count,'Exact authored owner replay differs')
    expected=[dict(path=str(SOURCE.relative_to(ROOT)),sha256=SOURCE_SHA,canonical_loc=40,physical_loc=40),
              dict(path=str(SETUP.relative_to(ROOT)),sha256=SETUP_SHA,canonical_loc=1,physical_loc=1)]
    same(counts['source_bundle'],expected,'Qualified two-file bundle differs')
    return dict(counts=counts,work=work,owner_projection=count)


# Independently retained receipt checks: explicit 14400/15000 limits and exact
# APL diagnostic; no producer import or producer admission decision is used.
def validate_attempt(attempt, raw, supervised, slot, row, manifest, pins, provenance):
    same(supervised, attempt, 'Report differs from supervisor receipt')
    same({k: v for k, v in attempt.items() if k not in p.SUPERVISOR_FIELDS}, raw,
         'Supervisor changed raw sampler evidence')
    same([attempt[k] for k in ('benchmark', 'round', 'id', 'key')], slot, 'Attempt outside rotation')
    checks = attempt['qualification_checks']
    require(set(checks) == p.CHECKS and all(type(v) is bool for v in checks.values()),
            'Missing or nonboolean qualification gate')
    require(type(attempt['qualified']) is bool and p.integer(attempt['sampler_wait_status'], 0),
            'Invalid qualification or sampler exit')
    require(attempt['full_workload'] is True and p.integer(attempt['workload_n'], manifest['size'])
            and p.integer(attempt['timeout_seconds'], TIMEOUT)
            and p.integer(attempt['maximum_rss_mib'], 10240), 'Changed measured workload')
    require(attempt['valid_environment'] is True and attempt['pins_unchanged_at_end'] is True,
            'Environment or integrity failure')
    for field in p.EMPTY_LIST_FIELDS:
        # The frozen execute exception path cleans and waits for its child but
        # does not create this normal-exit-only field. Other monitor receipts
        # remain mandatory; a present nonempty group always rejects the run.
        value = (attempt.get(field, []) if not attempt['qualified'] and field == 'remaining_group_members'
                 else attempt[field])
        same(value, [], 'Monitor or process cleanup failure: '+field)
    for field in ('power_at_start', 'power_at_end'):
        same(attempt[field], POWER, 'Changed measured power policy')
    command = [part.replace('{n}', str(manifest['size'])) for part in row['command']]
    native = attempt['supervised_native_group']
    require(native['type'] == 'native-group-started' and p.integer(native['pid']) and native['pid'] > 0
            and p.integer(native['pgid'], native['pid']) and native['inherited_common_mutex'] is True,
            'Missing authoritative native group')
    same(native['command'], command, 'Registered command differs')
    same(attempt['command'], command, 'Executed command differs')
    for field in ('cwd', 'runtime_environment', 'source_sha256', 'language'):
        same(attempt[field], row[field], 'Measured profile differs: '+field)
    provenance.extend(p.check_fingerprint(attempt, row, pins))
    begin, end = p.timestamp(attempt['started_at']), p.timestamp(attempt['finished_at'])
    require(begin <= end, 'Inverted timing interval')
    if not attempt['qualified']:
        require(all(checks[k] for k in p.CHECKS-FAILURE_GATES), 'Failure compromised measurement integrity')
        require(attempt.get('error') and attempt.get('error_type') in
                ('TimeoutError', 'OutputValidationError', 'RuntimeError'), 'Not an isolated workload failure')
        require(not all(checks.values()), 'Unqualified attempt claims every gate passed')
        require(not any(attempt.get(k) for k in p.ERROR_FIELDS
                if k not in ('error', 'error_type', 'resource_violation')), 'Failure contains wrapper/cleanup error')
        return begin, end
    require(all(checks.values()) and p.integer(attempt['exit_status'], 0), 'Failed successful-sample gate')
    require(not any(attempt.get(k) for k in p.ERROR_FIELDS),
            'Successful sample contains error evidence')
    check_stderr(attempt, row)
    seconds = attempt['seconds']
    require(p.finite(seconds, True) and seconds <= TIMEOUT
            and seconds <= (end-begin).total_seconds()+0.01, 'Impossible sample duration')
    peak = attempt['peak_process_group_rss_kib']
    require(p.integer(peak) and 0 <= peak <= 10240*1024, 'Exceeded measured RSS ceiling')
    require(p.integer(attempt['stdout_bytes']) and attempt['stdout_bytes'] > 0
            and p.digest(attempt['stdout_sha256']), 'Incomplete output binding')
    validation = attempt['validation']
    require(validation['reference_match'] is True, 'Output validation failed')
    same([validation['bytes'], validation['sha256']], [attempt['stdout_bytes'], attempt['stdout_sha256']],
         'Sampler/validator output disagreement')
    if manifest['full_output_reference'] is not None:
        same(manifest['full_output_reference'], dict(bytes=attempt['stdout_bytes'], sha256=attempt['stdout_sha256']),
             'Output differs from full reference')
    else:
        require(slot[0] == 'nbody' and validation['tolerance'] == 1e-8, 'Unexpected tolerance-only validation')
        energies = validation['energies']
        require(type(energies) is list and len(energies) == 2 and all(p.finite(x) for x in energies)
                and all(abs(a-b) <= 1e-8 for a,b in zip(energies, (-0.169075164, -0.169059907))),
                'Invalid N-body energies')
    return begin, end


def check_outer(record, attempt, controller_pid=None):
    require(record['status'] == 'returned' and p.integer(record['deadline_seconds'], OUTER_TIMEOUT)
            and p.integer(record['native_timeout_seconds'], TIMEOUT)
            and p.integer(record['common_mutex_fd']) and record['common_mutex_fd'] >= 64,
            'Outer supervisor did not return within the unchanged policy')
    require(record['common_mutex_held_through_cleanup'] is True and record['native_execute_unchanged'] is True
            and record['native_validation_unchanged'] is True and record['deadline_expired'] is False,
            'Outer supervisor changed measurement or lost ownership')
    same(record['cleanup_errors'], [], 'Outer supervisor cleanup error')
    require(not record.get('error') and not record.get('error_type'), 'Outer supervisor error')
    native = attempt['supervised_native_group']; pid = native['pid']
    same(record['native_registrations'], [native], 'Outer native registration differs')
    children, groups = record['owned_sampler_children'], record['owned_groups']
    require(len(children) == 1, 'Expected exactly one sampler child')
    child_key = next(iter(children)); child = children[child_key]
    require(child_key.isdecimal() and str(int(child_key)) == child_key and int(child_key) > 0
            and int(child_key) != pid and child['reaped'] is True, 'Sampler not normally owned/reaped')
    require(set(groups) == {child_key, str(pid)}, 'Extra or missing owned process group')
    same(groups[child_key], child['identity'], 'Sampler identity differs across receipts')
    gaps = []
    for key in (child_key, str(pid)):
        identity = groups[key]
        if identity is None:
            gaps.append(dict(attempt=attempt['attempt'], pid=int(key), observation='kernel identity unavailable'))
        else:
            kernel_identity(identity, int(key))
            if key == str(pid):
                require(identity['pgid'] == pid and identity['ppid'] == int(child_key), 'Native group not child-owned')
            elif controller_pid is not None:
                require(p.integer(identity['ppid'], controller_pid), 'Sampler not owned by durable controller')
    # Sampler identity can precede setsid(): its observed PGID may still be the
    # controller group. Do not replace that real observation with its later PID.
    if attempt['qualified']:
        same(record['signals'], [], 'Successful outer supervisor used cleanup signals')
    else:
        for event in record['signals']:
            require(p.integer(event['signal'], int(signal.SIGKILL)), 'Unexpected outer cleanup signal')
            require((event['kind'] == 'direct-child' and p.integer(event.get('pid'), int(child_key)))
                    or (event['kind'] == 'owned-group' and p.integer(event.get('pgid'))
                        and str(event['pgid']) in groups), 'Signal targets unowned process')
    return gaps


def reconcile(plan,report,terminal,raw,supervised,outer,durable,refs,producer_sha):
    """Pure ledger validation; all byte identities are verified by review_context."""
    slots,originals=schedule(plan,producer_sha);check_durable(durable,refs['plan'],plan)
    controller_pid=durable['command-started']['command_pid'];supervisor=report['supervisor']
    require(p.integer(supervisor['pid'],controller_pid),'Report names another controller process')
    same(p.process_identity(dict(pid=supervisor['pid'],
         listing=str(supervisor['pid'])+' 0 '+supervisor['process_listing'])),
         p.process_identity(durable['command-started']['command_identity']),'Controller birth/command identity differs')
    require(report['schema']=='apl-workspace-full6-results-v1' and terminal['schema']=='apl-workspace-full6-terminal-v1'
        and report['status']==terminal['status']=='complete' and report['active'] is None
        and not any(report.get(k) for k in ('error','error_type','terminal_integrity_errors'))
        and terminal['integrity_errors']==[] and report['pins_unchanged_at_end'] is True,
        'Only an actually complete successful six-process cohort can be admitted')
    for value in (report,terminal):
        require(value['full_performance_runs']==value['qualified_samples']==6
            and value['registered_native_attempts']==list(range(1,7)) and value['native_launch_unconfirmed_attempts']==[]
            and all(value[k] is False for k in ('full_size_work_qualified','full_timings_qualified','chart_admission')),
            'Producer accounting or admission changed')
    require(report['shared_timing_lock']==str(LOCK) and report['no_automatic_retry'] is True
        and report['stop_on_first_unqualified_attempt'] is True,'Report scheduling policy changed')
    for name in ('compiler_invocations','fixture_reexecutions','bounded_reexecutions','new_native_probes','repeated_completed_samples'):
        require(type(terminal[name]) is int and terminal[name]==0,'Unexpected terminal execution: '+name)
    require(terminal['original_files_mutated'] is False,'Original evidence was changed')
    require(terminal['saved_attempts']==6 and terminal['common_mutex_held'] is terminal['common_mutex_held_continuously'] is True
        and terminal['common_mutex_inode']==79859134 and type(terminal['common_mutex_fd']) is int and terminal['common_mutex_fd']>=64,
        'Continuous high-FD common mutex ownership required')
    same(report['plan'],refs['plan']['path'],'Report plan path differs');same(report['plan_sha256'],refs['plan']['sha256'],'Report plan pin differs')
    same(terminal['report'],refs['report']['path'],'Terminal report path differs');same(terminal['report_sha256'],refs['report']['sha256'],'Terminal report pin differs')
    same(terminal['prerequisite_pins'],dict(plan['pins'],**{refs['plan']['path']:refs['plan']['sha256']}),'Terminal prerequisite closure differs')
    same(report['source_aliases'],[alias()],'Report source alias changed');same(terminal['source_aliases'],[alias()],'Terminal source alias changed')
    require(report['sample_count']==3 and report['planned_apl_samples']==report['planned_matched_mech_samples']==3
        and report['benchmark_order']==report['completed_benchmarks']==['binarytrees']
        and report['source_work_profiles']==report['canonical_loc_profiles']==1 and report['formatted_loc_profiles']==0,
        'Wrong subject/control workload or count scope')
    require(len(report['attempts'])==6 and set(report['programs'])==set(originals),'Incomplete or extra full sample/profile')
    output=Path(plan['output']);pins=terminal['prerequisite_pins'];groups={k:[] for k in originals}
    provenance=[];gaps=[];previous=None;expected_paths=set();evidence={k:[] for k in originals}
    expected_outer=[]
    for index,(slot,attempt) in enumerate(zip(slots,report['attempts']),1):
        require(attempt['attempt']==index and attempt['qualified'] is True,'Failed/repeated/omitted sample')
        stem=f'{index:03d}-{slot[2]}';a=str(output/'attempts'/(stem+'.json'))
        b=str(output/'attempts'/(stem+'.supervisor.json'));c=str(output/'outer-supervisor'/(stem+'.json'))
        require(attempt['result_path']==a and attempt['supervisor_result_path']==b,'Attempt receipt escaped its exact slot')
        begin,end=validate_attempt(attempt,raw[a],supervised[b],slot,originals[slot[3]],plan['manifests']['binarytrees'],pins,provenance)
        gaps.extend(check_outer(outer[c],attempt,durable['command-started']['command_pid']))
        require(outer[c]['common_mutex_fd']==terminal['common_mutex_fd'],'Sampler inherited another mutex descriptor')
        require(previous is None or previous<=begin,'Actual native intervals overlap');previous=end
        paths={a,b,c};require(not expected_paths&paths,'Receipt reused by another slot');expected_paths|=paths
        for path in paths:
            require(report['validated_attempt_artifacts'][path]==terminal['available_evidence_pins'][path]
                ==terminal['validated_attempt_artifacts'][path],'Validated receipt digest differs')
        expected_outer.append(dict(path=c,sha256=terminal['available_evidence_pins'][c],status='returned'))
        groups[slot[3]].append(attempt)
        evidence[slot[3]].append(dict(attempt=index,raw=dict(path=a,sha256=terminal['available_evidence_pins'][a]),
            supervisor=dict(path=b,sha256=terminal['available_evidence_pins'][b]),
            outer=dict(path=c,sha256=terminal['available_evidence_pins'][c]),producer_report=copy.deepcopy(refs['report'])))
    require(set(raw)=={x['result_path'] for x in report['attempts']}
        and set(supervised)=={x['supervisor_result_path'] for x in report['attempts']}
        and set(outer)=={x['path'] for x in expected_outer},'Receipt set differs')
    same(report['independent_supervisors'],expected_outer,'Outer receipt ledger changed')
    require(set(report['validated_attempt_artifacts'])==set(terminal['validated_attempt_artifacts'])==expected_paths
        and set(terminal['available_evidence_pins'])==expected_paths|{refs['report']['path']},'Extra or missing terminal evidence')
    profiles={}
    for key,original in originals.items():
        row=report['programs'][key];attempts=groups[key];values=[a['seconds'] for a in attempts]
        require(len(values)==3,'Each real profile needs three observations')
        median,sd=p.three_statistics(values)
        same({k:v for k,v in row.items() if k not in AGGREGATE},original,'Measured source/runtime metadata changed')
        same(row['attempts'],[a['attempt'] for a in attempts],'Profile sample membership differs')
        same(row['samples_seconds'],values,'Sample timings differ');same(row['sample_validation'],[a['validation'] for a in attempts],'Output validation differs')
        require(row['measurement_status']=='measured' and row['median_seconds']==median
            and math.isclose(row['sample_stdev_seconds'],sd,rel_tol=1e-12,abs_tol=1e-12),'Profile statistics differ')
        profiles[key]=dict(key=key,id=original['id'],benchmark='binarytrees',language=original['language'],
            original_profile=copy.deepcopy(original),samples_seconds=values,median_seconds=median,sample_stdev_seconds=sd,
            native_observations=3,sample_evidence=evidence[key],sample_execution_metadata=copy.deepcopy(attempts),
            full_output_validation=copy.deepcopy(row['sample_validation']),full_workload_qualified=True)
    control=profiles[CONTROL_KEY]
    for key,value in profiles.items():
        ratio=value['median_seconds']/control['median_seconds'];row=report['programs'][key]
        require(row['time_x_mech']==ratio and row['matched_mech_control']==CONTROL_KEY
            and row['matched_mech_source_sha256']==originals[CONTROL_KEY]['source_sha256'],'Matched control ratio differs')
        value['time_x_mech']=ratio
    require(p.timestamp(durable['command-started']['started_at'])<=p.timestamp(report['started_at'])
        <=p.timestamp(report['attempts'][0]['started_at']) and previous<=p.timestamp(report['finished_at'])
        <=p.timestamp(durable['terminal']['finished_at']),'Cohort intervals outside owned controller lifetime')
    return dict(schema=SCHEMA,status='six-full-process-observations-ledger-reconciled-awaiting-file-review',
        language='apl',benchmark='binarytrees',profiles=profiles,source_aliases=[alias()],
        source_forms=2,distinct_authored_main_sources=1,distinct_counted_files=2,timing_aliases=1,
        subject_native_observations=3,control_native_observations=3,actual_full_native_processes=6,
        source_counts=copy.deepcopy(plan['qualification']['counts']),source_work=copy.deepcopy(plan['qualification']['work']),
        plan=copy.deepcopy(refs['plan']),report=copy.deepcopy(refs['report']),terminal=copy.deepcopy(refs['terminal']),
        durable_terminal=copy.deepcopy(refs['durable']),references=copy.deepcopy(refs),producer_sha256=producer_sha,
        preserved_failed_reports=[dict(path=str(path),sha256=value) for path,value in FAILED_REPORTS.items()],
        historical_algorithm_provenance=[p.strict_json(s) for s in sorted({p.canonical(v) for v in provenance})],
        kernel_identity_observation_gaps=gaps,source_work_qualified=False,canonical_loc_qualified=False,
        file_integrity_verified=False,runtime_publication_metadata_qualified=False,chart_admission=False,
        native_processes_started=0,complete_stdout_retained=False,
        timing_scope='Fresh process including interpreter startup, parsing, workspace assignment, complete N21 construction/traversal/output and shutdown.',
        output_scope='Frozen sampler full byte counts, SHA256 and exact output validation; complete stdout was not retained.',
        resource_scope='Sampled process-group RSS, not an unsampled maximum.',dataset_files_changed=False,historical_reports_mutated=False)


def checked_leases(leases):
    for path,handle,identity in leases:
        held,named=os.fstat(handle.fileno()),path.lstat()
        require(stat.S_ISREG(named.st_mode) and (held.st_dev,held.st_ino)==(named.st_dev,named.st_ino)==identity,
                'Named lease changed: '+str(path))


@contextmanager
def yielded_review(result,files,recheck,on_exit_failure=None,final_consumer_check=None,final_lock_check=None):
    """Consumer restoration runs before the enclosing evidence leases release."""
    body_error=None
    try:yield result,files
    except BaseException as error:body_error=error;raise
    finally:
        closure_error=None;cleanup_error=None
        try:
            recheck()
            if final_consumer_check is not None:final_consumer_check()
            if final_lock_check is not None:final_lock_check()
        except BaseException as error:closure_error=error
        if (body_error is not None or closure_error is not None) and on_exit_failure is not None:
            try:on_exit_failure()
            except BaseException as error:cleanup_error=error
        failures=[error for error in (body_error,closure_error,cleanup_error) if error is not None]
        if len(failures)>1:raise BaseExceptionGroup('APL evidence/consumer closure failed',failures)
        if closure_error is not None:raise closure_error
        if cleanup_error is not None:raise cleanup_error


@contextmanager
def review_context(plan_ref,report_ref,terminal_ref,producer_sha,durable_ref,consumer_sha,
                   *,on_exit_failure=None,final_consumer_check=None):
    """Keep original evidence leases through consumer checks and guarded rollback."""
    require(Path(plan_ref['path']).is_relative_to(PACKET) and Path(durable_ref['path'])==JOB/'terminal.json',
            'Exact original packet and new durable job required')
    files=Files();own=Path(__file__).resolve();files.verify(own,consumer_sha);load_primitives(files)
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
        and Path(sys.executable).resolve()==PYTHON.resolve(),'Use retained Python -I -S -B')
    with ExitStack() as stack:
        leases=[]
        for path,inode in [(LOCK,79859134),*OLD_LEASES.items(),(JOB/'owner.lock',None)]:
            # The common name is /tmp on macOS; its retained leaf is physical
            # under /private/tmp. The named leaf identity is checked throughout.
            handle=stack.enter_context(regular(path.resolve()));fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            held=os.fstat(handle.fileno());require(inode is None or held.st_ino==inode,'Historical lease inode differs')
            leases.append((path,handle,(held.st_dev,held.st_ino)))
        checked_leases(leases);files.verify(PYTHON.resolve(),PYTHON_SHA)
        plan=files.document(plan_ref);schedule(plan,producer_sha)
        output=Path(plan['output']);require(output.is_relative_to(PACKET) and output.resolve()==output,'Physical full6 output required')
        require(report_ref['path']==str(output/'report.json') and terminal_ref['path']==str(output/'terminal.json'),'Exact result paths required')
        report=files.document(report_ref);terminal=files.document(terminal_ref)
        expected_pins=dict(plan['pins'],**{plan_ref['path']:plan_ref['sha256']})
        same(terminal['prerequisite_pins'],expected_pins,'Measured prerequisite pins differ')
        require(set(plan['pins'])==set(plan['input_resolutions']),'Incomplete original named resolutions')
        files.resolutions=dict(plan['input_resolutions'])
        for name,expected in expected_pins.items():files.verify(Path(name),expected)
        durable={}
        for name in ('request','launch','worker-started','command-started','terminal'):
            path=JOB/(name+'.json');expected=durable_ref['sha256'] if name=='terminal' else file_sha(path)
            durable[name]=files.document(dict(path=str(path),sha256=expected))
        require(read(JOB/'command.stderr')==b'','Durable command emitted unexpected errors')
        job_inventory=r.inventory(JOB);output_inventory=r.inventory(output)
        require(output_inventory==set(terminal['available_evidence_pins'])|{terminal_ref['path']},'Closed output inventory differs')
        for path in job_inventory:files.verify(Path(path),file_sha(Path(path)))
        for name,expected in terminal['available_evidence_pins'].items():
            require(Path(name).is_relative_to(output),'Output evidence escaped cohort');files.verify(Path(name),expected)
        raws={};wrapped={};outers={}
        for attempt in report['attempts']:
            for target,key in ((raws,'result_path'),(wrapped,'supervisor_result_path')):
                name=attempt[key];target[name]=files.document(dict(path=name,sha256=terminal['available_evidence_pins'][name]))
        for ref in report['independent_supervisors']:outers[ref['path']]=files.document(ref)
        refs=dict(plan=plan_ref,report=report_ref,terminal=terminal_ref,durable=durable_ref)
        result=reconcile(plan,report,terminal,raws,wrapped,outers,durable,refs,producer_sha)
        qualified=qualification(plan,files)
        closures=[]
        for item in plan['prerequisite_artifact_closures']:
            directory=Path(item['directory']);actual=r.inventory(directory)
            require(actual=={str(directory/name) for name in item['artifacts']},'Prior evidence inventory differs')
            for name,entry in item['artifacts'].items():files.verify(directory/name,entry['sha256'])
            closures.append((directory,actual))
        verified=tuple(files.pins.items());resolutions=tuple(files.resolutions.items())
        def recheck():
            same(files.resolutions,dict(resolutions),'Original named-resolution policy changed')
            for name,expected in (*verified,*tuple(files.pins.items())):files.verify(Path(name),expected)
            for name,target in plan['input_resolutions'].items():require(str(Path(name).resolve())==target,'Named original input changed')
            for name in plan['absent_inputs']:require(not os.path.lexists(name),'Absent runtime input appeared')
            require(r.inventory(JOB)==job_inventory and r.inventory(output)==output_inventory,'Evidence inventory changed')
            for directory,expected in closures:require(r.inventory(directory)==expected,'Prior artifact membership changed')
            checked_leases(leases)
        recheck()
        result.update(status='six-full-process-observations-file-verified-awaiting-publication',file_integrity_verified=True,
            common_mutex_held=True,common_mutex_inode=79859134,source_work_qualified=True,canonical_loc_qualified=True,
            owner_projection=qualified['owner_projection'],qualified_source_counts=qualified['counts'],qualified_source_work=qualified['work'],
            verified_file_pins=dict(sorted(files.pins.items())),held_evidence_leases=[str(v[0]) for v in leases])
        with yielded_review(result,files,recheck,on_exit_failure,final_consumer_check,
                            lambda:checked_leases(leases)) as reviewed:yield reviewed


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    for name in ('plan','report','terminal','durable-terminal'):
        parser.add_argument('--'+name,type=Path,required=True);parser.add_argument('--'+name+'-sha256',required=True)
    parser.add_argument('--producer-sha256',required=True);parser.add_argument('--tool-sha256',required=True)
    parser.add_argument('--output',type=Path,required=True);args=parser.parse_args()
    def interrupted(signum,frame):raise KeyboardInterrupt('APL reconciliation interrupted: '+str(signum))
    for sig in (signal.SIGINT,signal.SIGTERM,signal.SIGHUP):signal.signal(sig,interrupted)
    refs=[dict(path=str(getattr(args,name).resolve()),sha256=getattr(args,name+'_sha256'))
          for name in ('plan','report','terminal','durable_terminal')]
    output=args.output.resolve();require(output.is_relative_to(PACKET/'reconciliation') and not os.path.lexists(output),'Fresh reconciliation output required')
    owned={}
    def remove():
        if not owned or not os.path.lexists(output):return
        current=output.lstat();require((current.st_dev,current.st_ino)==owned['identity'],'Preserving replaced review output')
        actual=read(output);require(owned['raw'].startswith(actual),'Preserving edited review output');output.unlink()
    def check():
        current=output.lstat();require((current.st_dev,current.st_ino)==owned['identity'] and read(output)==owned['raw'],'Saved review changed')
        again=output.lstat();require((again.st_dev,again.st_ino)==owned['identity'],'Review output replaced')
    try:
        with review_context(refs[0],refs[1],refs[2],args.producer_sha256,refs[3],args.tool_sha256,
                            on_exit_failure=remove,final_consumer_check=check) as (result,files):
            raw=encoded(result);output.parent.mkdir(parents=True,exist_ok=True)
            previous_mask=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGINT,signal.SIGTERM,signal.SIGHUP})
            try:
                with output.open('xb') as stream:
                    held=os.fstat(stream.fileno());owned.update(identity=(held.st_dev,held.st_ino),raw=raw)
                    stream.write(raw);stream.flush();os.fsync(stream.fileno())
            finally:signal.pthread_sigmask(signal.SIG_SETMASK,previous_mask)
        print(json.dumps(dict(output=str(output),sha256=sha(raw),chart_admission=False)))
    except BaseException as error:
        try:remove()
        except BaseException as cleanup:raise BaseExceptionGroup('APL review and cleanup failed',[error,cleanup])
        raise


if __name__=='__main__':main()
