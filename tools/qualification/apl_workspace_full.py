"""Six serial N=21 process samples for one APL implementation and Mech control.

Setup, interpreter startup, parsing, complete work/output and shutdown stay in
the unchanged full-process timer. Preparation requires independently qualified
source/count evidence; this producer never grants final timing/chart admission.
"""
import argparse
import copy
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import statistics
import sys
import traceback
import types

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'experiments/apl/binarytrees-workspace-v1'
PACKET = BASE/'full6-v1'
SUBJECT = ROOT/'tools/qualification/apl_workspace_subject.py'
SUBJECT_SHA = '620b16cb5016c08e31819f6933c44770b2d243886d08b12c16686fb0e89f295c'
HELPERS = ROOT/'tools/qualification/elixir_full.py'
HELPERS_SHA = '5fa93294c0f098b17384a43943f9c982e9447c7a309c1f64e1870389fb338703'
RECEIPTS = ROOT/'tools/qualification/prolog_reconcile.py'
RECEIPTS_SHA = 'a69b498cc0664b2951c1ef5ef2281f06f34e6415fcf6adfe8b723f06ca127cfe'
SUBJECT_PACKET = BASE/'whole-subject-v1'
SUBJECT_RUN = SUBJECT_PACKET/'run-v1'
SUBJECT_JOB = ROOT/'experiments/shared/owned-jobs-v1/owned-jobs/apl-whole-subject2-v1'
SUBJECT_FIXED = {
    SUBJECT_PACKET/'plan-v1.json': '729bf273fbecd5fbd183d745ae95a2295213efc7ce8ecf5f63068cadea8625fa',
    SUBJECT_RUN/'report.json': '277f3db35cfd64ca3fc32997cc5beafe4a63bd115ab279eefc9f74d1f64ce656',
    SUBJECT_RUN/'terminal.json': '3aedd4a31c834dd2f055c485bc2190bf9c12a309a7fd763137d8ef0a97e1ac6b',
    SUBJECT_PACKET/'actual-closure-v1.json': '1092faea796ad651f4eeaab9811ccaae25749010a5459dbb5d539b82bccfd84e',
    SUBJECT_JOB/'terminal.json': 'caa2f0d46945635833b2f23a97ebcd8f437dced1d91b4a8361ae8a9ed5e62187',
    SUBJECT_PACKET/'actual-bounded-work-review-v1.json': 'b92ef3f6b7ff7f15e21f754cf608fa583f65ac0874b189553cfc2c68bdf9d468',
}
SOURCE_SHA = 'd1293d125d2d65940137d2d624402d4931f74d1f031bc2261165ad6663c57e74'
SETUP_SHA = '3adce52a2aea05cc00ee13e011655749f5a03bc81d37a4ee8eb13c14f227e58c'
BENCHES = ['binarytrees']
SUBJECT_ID = 'apl-binarytrees-workspace200-compact'
SUBJECT_KEY = 'binarytrees:apl-workspace200-compact'
ALIAS_KEY = 'binarytrees:apl-workspace200-optimized'
CONTROL_KEY = 'binarytrees:apl-workspace200-full-study:mech-control'
TIMEOUT = 14400
OUTER_TIMEOUT = 15000
RSS_MIB = 10240
_subject_lease = None


def require(value, message):
    if not value: raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def cold(path, digest, name):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'Frozen helper changed: '+str(path))
    module = types.ModuleType(name); module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


s = cold(SUBJECT, SUBJECT_SHA, 'apl_full_private_subject')
h = cold(HELPERS, HELPERS_SHA, 'apl_full_private_helpers')
r = cold(RECEIPTS, RECEIPTS_SHA, 'apl_full_private_receipts')
p, same = r.p, r.same
b, kb = s.b, s.kb
merge, new_json = h.shared.merge, h.shared.new_json
refresh_attempt_accounting = h.refresh_attempt_accounting
preserve_wrapper_failure = h.preserve_wrapper_failure
WARNING = s.WARNING.decode('utf-8')
POWER = r.POWER
FAILURE_GATES = r.FAILURE_GATES
kernel_identity = r.kernel_identity


def verify_lock(lock):
    s.lock_identity(lock)
    require(_subject_lease is not None, 'Completed subject lease must remain held')
    held, named = os.fstat(_subject_lease.fileno()), (SUBJECT_JOB/'owner.lock').stat()
    require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) and held.st_ino == 82384399,
            'Completed subject durable lease changed')


@contextmanager
def held_mutex():
    global _subject_lease
    require(_subject_lease is None, 'Nested full-cohort ownership')
    with s.held_mutex() as lock, (SUBJECT_JOB/'owner.lock').open('rb') as lease:
        fcntl.flock(lease, fcntl.LOCK_EX|fcntl.LOCK_NB)
        _subject_lease = lease
        try:
            verify_lock(lock)
            yield lock
        finally:
            try: verify_lock(lock)
            finally: _subject_lease = None


def read_ref(ref, pins):
    require(set(ref) == {'path', 'sha256'}, 'Exact path and digest reference required')
    path = Path(ref['path'])
    require(path.is_absolute() and '..' not in path.parts, 'Absolute physical evidence path required')
    return s.document(path, ref['sha256'], pins)


def pin_inputs(value, pins):
    for name, digest in value['inputs'].items():
        path = Path(name)
        require(not path.is_absolute() and '..' not in path.parts, 'Review inputs must be repository relative')
        s.pin(pins, ROOT/path, digest)


def retained_subject(pins):
    d = {path: s.document(path, digest, pins) for path, digest in SUBJECT_FIXED.items()}
    plan, report, terminal = (d[SUBJECT_PACKET/'plan-v1.json'], d[SUBJECT_RUN/'report.json'],
                              d[SUBJECT_RUN/'terminal.json'])
    durable = d[SUBJECT_JOB/'terminal.json']; closure = d[SUBJECT_PACKET/'actual-closure-v1.json']
    review = d[SUBJECT_PACKET/'actual-bounded-work-review-v1.json']
    require(report['status'] == terminal['status'] == s.SUCCESS and report['active'] is None
            and report['integrity_errors'] == terminal['integrity_errors'] == []
            and report['native_processes_started'] == terminal['native_processes_started'] == terminal['capture_count'] == 2
            and [x['id'] for x in plan['schedule']] == list(s.IDS), 'Small-subject producer did not close')
    require(terminal['report_sha256'] == SUBJECT_FIXED[SUBJECT_RUN/'report.json']
            and terminal['common_mutex_held'] is True and terminal['common_mutex_inode'] == 79859134,
            'Small-subject terminal identity differs')
    require(durable['status'] == 'command-exited-zero-awaiting-report-review' and durable['exit_code'] == 0
            and durable['command_pid'] == 31332 and durable['actual_command_started'] is True
            and durable['stop_signals'] == [] and durable['qualification_granted'] is durable['automatic_retry'] is False,
            'Small-subject durable closure differs')
    require(closure['status'] == 'closed-two-small-subject-captures-awaiting-independent-work-review'
            and closure['plan_sha256'] == SUBJECT_FIXED[SUBJECT_PACKET/'plan-v1.json']
            and closure['report_sha256'] == SUBJECT_FIXED[SUBJECT_RUN/'report.json']
            and closure['terminal_sha256'] == SUBJECT_FIXED[SUBJECT_RUN/'terminal.json']
            and closure['durable_terminal_sha256'] == SUBJECT_FIXED[SUBJECT_JOB/'terminal.json'],
            'Small-subject physical closure differs')
    require(review['status'] == 'two-actual-small-subject-captures-independently-reviewed'
            and all(review[k] is True for k in ('native_syntax_qualified', 'bounded_output_qualified',
                                               'bounded_whole_subject_work_qualified'))
            and all(review[k] is False for k in ('required_work_qualified', 'canonical_source_count_qualified',
                                                'full_timing_qualified', 'chart_admission')),
            'Independent bounded work disposition differs')
    pin_inputs(review, pins)
    require(report['pins'] == dict(plan['pins'], **{str(SUBJECT_PACKET/'plan-v1.json'):
                                                  SUBJECT_FIXED[SUBJECT_PACKET/'plan-v1.json']}),
            'Completed subject input closure differs')
    for path, digest in report['pins'].items(): s.pin(pins, path, digest)
    require(s.inventory(SUBJECT_RUN, ('terminal.json',)) == terminal['available_evidence'],
            'Small-subject saved artifacts differ')
    for name, entry in terminal['available_evidence'].items(): s.pin(pins, SUBJECT_RUN/name, entry['sha256'])
    job_inventory = s.inventory(SUBJECT_JOB)
    for name, entry in job_inventory.items(): s.pin(pins, SUBJECT_JOB/name, entry['sha256'])
    previous = None
    for slot, capture in zip(plan['schedule'], report['captures']):
        current, snapshot = s.checked_capture(slot, SUBJECT_RUN/slot['directory'], durable['command_pid'],
                                              report['inherited_lock_descriptor'], plan['configuration_pattern'])
        require(current == capture and snapshot == report['validated_artifacts'][slot['directory']],
                'Small-subject captured work differs')
        require(previous is None or previous <= s.stamp(current['started_at']), 'Small-subject overlap')
        previous = s.stamp(current['finished_at'])
    require(len(report['captures']) == 2 and report['attempted_commands'] == [x['directory'] for x in plan['schedule']],
            'Incomplete small-subject observations')
    return plan, dict(directory=str(SUBJECT_RUN), artifacts=s.inventory(SUBJECT_RUN)), \
        dict(directory=str(SUBJECT_JOB), artifacts=job_inventory)


def validate_qualification(counts, work, refs, pins):
    require(counts['schema'] == 'apl-binarytrees-workspace-qualified-source-counts-v1'
            and counts['canonical_LOC_admitted'] is True
            and counts['canonical_loc'] == counts['physical_loc'] == 41
            and counts['formatted_loc'] is None and counts['formatted_loc_qualified'] is False
            and counts['distinct_authored_main_sources'] == 1
            and counts['source_forms'] == ['compact', 'optimized']
            and counts['setup_assignment_included'] is True,
            'Independent complete 41-unit source admission required')
    expected = [(str(ROOT/'archive/comparisons/r-apl-uiua-comparison/20261011/sources/apl/binarytrees.compact.apl'),
                 SOURCE_SHA, 40, 40), (str(BASE/'setup.apl'), SETUP_SHA, 1, 1)]
    require([(str(ROOT/row['path']) if not Path(row['path']).is_absolute() else row['path'], row['sha256'],
              row['canonical_loc'], row['physical_loc']) for row in counts['source_bundle']] == expected,
            'Measured setup or unchanged source omitted from count')
    require(work['schema'] == 'apl-binarytrees-workspace-required-work-v1'
            and work['status'] == 'qualified-source-work-awaiting-full-size-timing'
            and work['source_work_qualified'] is True and work['workload_n'] == 21
            and work['source_sha256'] == SOURCE_SHA and work['setup_sha256'] == SETUP_SHA
            and work['workspace_scale'] == 200 and work['maximum_workers'] == 1
            and work['source_counts'] == refs['counts'], 'Full source-work disposition required')
    require(work['bounded_subject_review'] == dict(path=str(SUBJECT_PACKET/'actual-bounded-work-review-v1.json'),
                sha256=SUBJECT_FIXED[SUBJECT_PACKET/'actual-bounded-work-review-v1.json'])
            and work['bounded_ownership_review'] == dict(path=str(s.OWNERSHIP_REVIEW), sha256=s.OWNERSHIP_REVIEW_SHA)
            and work['previous_failures_preserved'] is True, 'Work review must preserve exact bounded/failure history')
    for value in (counts, work):
        require(all(value[k] is False for k in ('full_size_work_qualified', 'full_timing_qualified', 'chart_admission')),
                'Preparation cannot inherit unobserved full-size/timing admission')
        pin_inputs(value, pins)
    owner_ref = counts['source_owner_review']; checker_ref = counts['checker']
    owner = read_ref(owner_ref, pins)
    checker = s.pin(pins, checker_ref['path'], checker_ref['sha256'])
    require(checker == ROOT/'tools/qualification/apl_workspace_source_units.py', 'Unexpected exact owner checker')
    module = cold(checker, checker_ref['sha256'], 'apl_full_private_source_units')
    sources = {identity: (ROOT/row['path']).read_bytes() for identity, row in module.SOURCES.items()}
    require(owner['count'] == module.count_bundle(sources), 'Exact source owner coverage did not replay')
    require(pins.get(str(module.READER)) == module.READER_SHA, 'Frozen APL source reader is unbound')


def control(pins):
    audit = h.read_metadata(h.AUDIT, h.AUDIT_SHA, pins)
    require(audit['status'] == 'reviewed', 'Matched control audit changed')
    row = next(row for row in audit['controls'] if row['benchmark'] == 'binarytrees')
    require(row['language'] == 'mech' and row['command'] == [row['binary'], '{n}'], 'Matched control changed')
    pins.update(merge(pins, {row[k]: row[k+'_sha256'] for k in ('source', 'binary')}, row.get('support', {})))
    result = {key: copy.deepcopy(row[key]) for key in h.shared.EXECUTION_FIELDS}
    result.update(id='mech-aot-control', key=CONTROL_KEY, maximum_workers=8, loc=None, chart_admission=False,
                  control_provenance=dict(path=str(h.AUDIT), sha256=h.AUDIT_SHA, original_id=row['id']))
    return result


def orders():
    ids = [SUBJECT_ID, 'mech-aot-control']
    return [dict(round=i+1, profiles=ids[i%2:]+ids[:i%2]) for i in range(3)]


def schedule_for(manifests):
    require(set(manifests) == {'binarytrees'}, 'Only full binary trees scheduled')
    manifest = manifests['binarytrees']; rows = manifest['profiles']
    require([row['id'] for row in rows] == [SUBJECT_ID, 'mech-aot-control']
            and [row['key'] for row in rows] == [SUBJECT_KEY, CONTROL_KEY]
            and [row['language'] for row in rows] == ['apl', 'mech']
            and manifest['samples'] == 3 and manifest['size'] == 21 and manifest['orders'] == orders(),
            'Exactly one real APL source and matched control in three alternating rounds required')
    keys = {row['id']: row['key'] for row in rows}
    slots = [('binarytrees', order['round'], identity, keys[identity]) for order in orders() for identity in order['profiles']]
    require(len(slots) == len(set(slots)) == 6, 'Duplicate or omitted full-size slot')
    return slots


def subject_profile(spec, counts, refs, output):
    subject = spec['subject_runtime_path']; launcher = spec['launcher_runtime_path']; setup = str(BASE/'setup.apl')
    env = b.environment(output/'environment')
    row = dict(id=SUBJECT_ID, key=SUBJECT_KEY, benchmark='binarytrees', language='apl', variant='compact',
        source=subject, source_sha256=SOURCE_SHA, binary=launcher, binary_sha256=spec['launcher']['sha256'],
        command=[launcher, '--cc', '1', '-f', setup, '-f', subject, '--', '{n}'], cwd=str(Path(launcher).parent),
        runtime_environment=env, runtime_binary=spec['runtime_binary'], maximum_workers=1,
        source_bundle=copy.deepcopy(counts['source_bundle']), source_count_review=refs['counts'], required_work_review=refs['work'],
        support_pins={setup: SETUP_SHA, spec['runtime_binary']['path']: spec['runtime_binary']['sha256']},
        canonical_loc=41, physical_loc=41, loc=41, formatted_loc=None, formatted_loc_qualified=False,
        source_work_qualified=True, canonical_source_count_qualified=True, chart_admission=False,
        memory_policy='GNU APL workspace scale 200; unchanged allocator and garbage collection',
        setup_inside_timer=True, source_alias_of=None, timing_alias_of=None, optimization_claim=False)
    # Fingerprint support references are absolute, matching the frozen collector.
    for member in row['source_bundle']: member['path'] = str(ROOT/member['path'])
    return row


def build_plan(output, refs):
    b.physical(output)
    require(output.is_relative_to(PACKET) and output != PACKET and not output.exists(), 'Fresh full6 output required')
    pins = {}
    prior_plan, artifacts, durable = retained_subject(pins)
    counts, work = (read_ref(refs[k], pins) for k in ('counts', 'work'))
    validate_qualification(counts, work, refs, pins)
    spec = s.document(b.SPEC, b.SPEC_SHA, pins)
    row = subject_profile(spec, counts, refs, output)
    manifest = dict(benchmark='binarytrees', profiles=[row, control(pins)], samples=3, size=21,
        canonical_full_workload=True, orders=orders(), timeout_seconds=TIMEOUT, supervisor_timeout_seconds=OUTER_TIMEOUT,
        maximum_rss_mib=RSS_MIB, full_output_reference=dict(bytes=455, sha256=h.FULL['binarytrees'][2]),
        shared_timing_lock=str(h.LOCK), no_automatic_retry=True, chart_admission=False,
        runtime_startup_parsing_setup_output_shutdown_inside_timer=True)
    manifests = {'binarytrees': manifest}
    pins.update(merge(pins, h.SAMPLER_PINS, {str(HELPERS): HELPERS_SHA, str(h.SHARED): h.SHARED_SHA,
        str(h.SUPERVISOR): h.SUPERVISOR_SHA, str(RECEIPTS): RECEIPTS_SHA, str(r.HELPER): r.HELPER_SHA,
        str(SUBJECT): SUBJECT_SHA, str(h.PYTHON.resolve()): h.PYTHON_SHA}))
    for path in (Path(__file__).resolve(), Path(__file__).with_name('test_apl_workspace_full.py'), PACKET/'README.md'):
        s.pin(pins, path)
    absent = set(prior_plan['absent_inputs'])
    for path in b.preference_paths(Path(spec['runtime_binary']['path']).parent.parent, [output/'environment']):
        if path.is_file(): s.pin(pins, path)
        else:
            require(not os.path.lexists(path), 'Unexpected nonregular APL preference path'); absent.add(str(path))
    return dict(schema='apl-workspace-qualified-full6-plan-v1', status='prepared-awaiting-independent-review',
        controller=str(Path(__file__).resolve()), controller_sha256=sha(__file__), repository=str(ROOT), output=str(output),
        qualification=refs, manifests=manifests, schedule=[list(slot) for slot in schedule_for(manifests)],
        pins=pins, input_resolutions={name: str(Path(name).resolve()) for name in pins}, absent_inputs=sorted(absent),
        prerequisite_artifact_closures=[artifacts, durable],
        source_aliases=[dict(key=ALIAS_KEY, variant='optimized', source_alias_of=SUBJECT_KEY, timing_alias_of=SUBJECT_KEY,
                            additional_native_processes=0, optimization_claim=False)],
        samples=3, apl_samples=3, matched_mech_samples=3, full_processes=6, maximum_live_native_groups=1,
        common_mutex_inode=79859134, minimum_inherited_lock_fd=64, continuous_common_mutex=True,
        compiler_invocations=0, fixture_reexecutions=0, bounded_reexecutions=0,
        pure_source_owner_replays=1, native_count_reexecutions=0, new_native_probes=0,
        original_files_mutated=False, no_automatic_retry=True, stop_on_first_unqualified_attempt=True,
        full_size_work_qualified=False, full_timings_qualified=False, chart_admission=False,
        timing_policy='Fresh process including startup, parsing, workspace assignment, all N=21 work, '
                      'complete output and shutdown. Pin checks, environment waits and output validation are outside the timer.')


def check_execution_inputs(plan, harness, lock):
    verify_lock(lock)
    s.verify(plan['pins'], plan['input_resolutions'], plan['absent_inputs'], lock)
    for closure in plan['prerequisite_artifact_closures']:
        require(s.inventory(Path(closure['directory'])) == closure['artifacts'], 'Retained prerequisite inventory changed')
    h.check_execution_inputs(plan, harness)
    verify_lock(lock)


def check_stderr(attempt, row):
    expected = WARNING if row['language'] == 'apl' else ''
    require(attempt['stderr'] == expected, 'Unknown or missing exact shutdown diagnostic; raw sample preserved')


def qualified_sample(attempt, manifest, row, fingerprint):
    h.shared.qualified_sample(attempt, manifest, row, fingerprint)
    check_stderr(attempt, row)


# Receipt checks adapted from the pinned independent reader: only the recorded
# native/outer limits and exact APL stderr policy differ. Raw bytes stay intact.
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


def initial_rows(plan):
    return {row['key']: dict(copy.deepcopy(row), samples_seconds=[], sample_validation=[], attempts=[],
                            measurement_status='pending')
            for row in plan['manifests']['binarytrees']['profiles']}


def summarize(rows):
    if not all(len(row['samples_seconds']) == 3 for row in rows.values()): return
    for row in rows.values():
        row.update(median_seconds=statistics.median(row['samples_seconds']),
                   sample_stdev_seconds=statistics.stdev(row['samples_seconds']), measurement_status='measured')
    control_row = rows[CONTROL_KEY]
    for row in rows.values():
        row.update(time_x_mech=row['median_seconds']/control_row['median_seconds'],
                   matched_mech_control=CONTROL_KEY, matched_mech_source_sha256=control_row['source_sha256'])


def attempt_paths(output, attempt):
    stem = f'{attempt["attempt"]:03d}-{attempt["id"]}'
    return (output/'attempts'/(stem+'.json'), output/'attempts'/(stem+'.supervisor.json'),
            output/'outer-supervisor'/(stem+'.json'))


def check_attempt(output, attempt, slot, row, manifest, pins, parent, lock_fd):
    paths = attempt_paths(output, attempt)
    require([attempt['result_path'], attempt['supervisor_result_path']] == [str(path) for path in paths[:2]],
            'Sample receipt escaped its native output directory')
    raws = [path.read_bytes() for path in paths]
    raw, supervised, outer = [p.strict_json(value) for value in raws]
    provenance = []
    validate_attempt(attempt, raw, supervised, list(slot), row, manifest, pins, provenance)
    gaps = check_outer(outer, attempt, parent)
    require(outer['common_mutex_fd'] == lock_fd, 'Outer supervisor inherited another timing descriptor')
    snapshot = {str(path): hashlib.sha256(value).hexdigest() for path, value in zip(paths, raws)}
    require(all(sha(path) == digest for path, digest in snapshot.items()), 'Receipt changed during validation')
    return snapshot, provenance, gaps


def accept_attempt(report, row, attempt):
    """A full cohort has six actual slots, never native executions for aliases."""
    row['attempts'].append(attempt['attempt'])
    if attempt['qualified']:
        row['samples_seconds'].append(attempt['seconds'])
        row['sample_validation'].append(attempt['validation'])
        row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
    else:
        row['measurement_status'] = 'stopped-unqualified'
    summarize(report['programs'])


def record_attempt(supervisor, guard, harness, plan, report, row, slot, pins, snapshots, attempt, lock):
    with supervisor.lifecycle_atomic():
        report['attempts'].append(attempt); report['active'] = None
        refresh_attempt_accounting(report); guard.save(guard.REPORT, report)
        manifest = plan['manifests']['binarytrees']
        original = next(item for item in manifest['profiles'] if item['key'] == row['key'])
        captured, provenance, gaps = check_attempt(guard.OUT, attempt, slot, original, manifest, pins,
                                                   os.getpid(), lock.fileno())
        snapshots.update(merge(snapshots, captured))
        report['descriptive_provenance'].extend(provenance)
        report['kernel_identity_observation_gaps'].extend(gaps)
        # Retain an unqualified attempt, but do not proceed to another slot.
        if attempt['qualified']:
            qualified_sample(attempt, manifest, original, harness.execution_fingerprint(original))
        accept_attempt(report, row, attempt)
        report['validated_attempt_artifacts'] = dict(snapshots)
        refresh_attempt_accounting(report); guard.save(guard.REPORT, report)
        require(attempt['qualified'], 'Full sample failed; cohort stops without retry or automatic skip')


def check_success_ledger(plan, report):
    slots = schedule_for(plan['manifests']); rows = initial_rows(plan)
    require(len(report['attempts']) == 6 and report['active'] is None, 'Six actual completed samples required')
    for index, (slot, attempt) in enumerate(zip(slots, report['attempts']), 1):
        require(attempt['attempt'] == index and [attempt[key] for key in ('benchmark', 'round', 'id', 'key')] == list(slot)
                and attempt['qualified'] is True, 'Missing, repeated, failed or reordered native sample')
        accept_attempt(dict(programs=rows), rows[slot[3]], attempt)
    require(rows == report['programs'] and report['full_performance_runs'] == report['qualified_samples'] == 6
            and report['native_launch_unconfirmed_attempts'] == []
            and report['completed_benchmarks'] == ['binarytrees'], 'Full sample ledger does not replay')
    require(report['source_aliases'] == plan['source_aliases'], 'Aliases cannot add observations')


def finish(plan, report, pins, snapshots, guard, harness, lock):
    """Close exact actual evidence while original common and prior leases are held."""
    errors = []; final_lock_confirmed = False
    def problem(error, path=None):
        errors.append(dict(path=path, error=str(error) or type(error).__name__, error_type=type(error).__name__))
    for path, digest in merge(pins, snapshots).items():
        try: require(sha(path) == digest, 'Pinned or validated artifact changed')
        except BaseException as error: problem(error, path)
    refresh_attempt_accounting(report)
    try:
        check_execution_inputs(plan, harness, lock)
        require(report['active'] is None, 'Native supervisor left active state')
        if report['status'] == 'complete': check_success_ledger(plan, report)
        expected = set(); previous = None
        slots = schedule_for(plan['manifests'])
        require(len(report['attempts']) <= 6, 'Extra or repeated attempt')
        for index, attempt in enumerate(report['attempts']):
            require(attempt['attempt'] == index+1, 'Nonsequential attempt identity')
            slot = slots[index]
            require([attempt[k] for k in ('benchmark', 'round', 'id', 'key')] == list(slot), 'Attempt outside prefix')
            if attempt.get('wrapper_supervisor_failure'):
                require(report['status'] == 'stopped-unqualified' and index == len(report['attempts'])-1,
                        'Wrapper failure must end the cohort')
                continue
            manifest = plan['manifests']['binarytrees']
            row = next(value for value in manifest['profiles'] if value['key'] == slot[3])
            captured, _, _ = check_attempt(guard.OUT, attempt, slot, row, manifest, pins, os.getpid(), lock.fileno())
            require(all(snapshots.get(path) == digest for path, digest in captured.items()),
                    'Missing or changed independently validated receipt')
            begin, end = p.timestamp(attempt['started_at']), p.timestamp(attempt['finished_at'])
            require(previous is None or previous <= begin, 'Native sample intervals overlapped')
            previous = end; expected.update(captured)
        require(set(snapshots) == expected, 'Unexpected validated artifact')
        if report['status'] == 'complete':
            require(r.inventory(guard.OUT) == expected|{str(guard.REPORT)}, 'Unexpected completed output')
            require(report['independent_supervisors'] == [dict(path=str(attempt_paths(guard.OUT, a)[2]),
                    sha256=snapshots[str(attempt_paths(guard.OUT, a)[2])], status='returned') for a in report['attempts']],
                    'Outer supervisor inventory differs')
    except BaseException as error: problem(error)
    report['pins_unchanged_at_end'] = not errors
    report['validated_attempt_artifacts'] = dict(snapshots)
    if errors: report.update(status='failed-terminal-integrity', terminal_integrity_errors=errors)
    expected_report = (json.dumps(report, indent=2)+'\n').encode()
    expected_report_sha = hashlib.sha256(expected_report).hexdigest()
    guard.save(guard.REPORT, report)
    try:
        available = {path: sha(path) for path in r.inventory(guard.OUT)}
        require(available.get(str(guard.REPORT)) == expected_report_sha,
                'Saved report differs from the validated ledger')
        for path, digest in merge(pins, snapshots).items():
            require(sha(path) == digest, 'Prerequisite or validated receipt changed during final inventory')
            if path in snapshots: require(available.get(path) == digest, 'Final inventory adopted changed receipt')
        check_execution_inputs(plan, harness, lock)
        require({path: sha(path) for path in r.inventory(guard.OUT)} == available,
                'Report or artifact changed during final prerequisite replay')
        final_report_sha = sha(guard.REPORT)
        require(final_report_sha == expected_report_sha, 'Final report read differs from the validated ledger')
        verify_lock(lock)
        final_lock_confirmed = True
    except BaseException as error:
        problem(error); available = {}
        report.update(status='failed-terminal-integrity', terminal_integrity_errors=errors, pins_unchanged_at_end=False)
        guard.save(guard.REPORT, report)
        final_report_sha = sha(guard.REPORT)
    new_json(guard.OUT/'terminal.json', dict(schema='apl-workspace-full6-terminal-v1', status=report['status'],
        report=str(guard.REPORT), report_sha256=final_report_sha, prerequisite_pins=pins,
        available_evidence_pins=available, validated_attempt_artifacts=dict(snapshots), integrity_errors=errors,
        common_mutex_held=final_lock_confirmed, common_mutex_inode=79859134, common_mutex_fd=lock.fileno(),
        common_mutex_held_continuously=final_lock_confirmed and not errors,
        full_performance_runs=report['full_performance_runs'],
        saved_attempts=len(report['attempts']), registered_native_attempts=report['registered_native_attempts'],
        native_launch_unconfirmed_attempts=report['native_launch_unconfirmed_attempts'], qualified_samples=report['qualified_samples'],
        source_aliases=plan['source_aliases'], compiler_invocations=0, fixture_reexecutions=0,
        bounded_reexecutions=0, new_native_probes=0, repeated_completed_samples=0, original_files_mutated=False,
        full_size_work_qualified=False, full_timings_qualified=False, chart_admission=False))
    verify_lock(lock)
    require(not errors, 'Final integrity failed; actual evidence is preserved')


def prepare(args):
    with held_mutex() as lock:
        h.checked_runtime()
        b.physical(args.plan)
        require(args.plan.is_relative_to(PACKET) and not args.plan.exists()
                and not args.plan.is_relative_to(args.output), 'Fresh external plan required')
        refs = dict(counts=dict(path=str(args.counts.resolve()), sha256=args.counts_sha256),
                    work=dict(path=str(args.work.resolve()), sha256=args.work_sha256))
        plan = build_plan(args.output, refs)
        _, harness = h.load_measurement()
        check_execution_inputs(plan, harness, lock)
        new_json(args.plan, plan)
        print(json.dumps(dict(plan=str(args.plan), sha256=sha(args.plan), native_executions=0,
                              apl_samples=3, matched_mech_samples=3, alias_additional_samples=0)), flush=True)


def run(args):
    with held_mutex() as lock:
        h.checked_runtime()
        plan = read_ref(dict(path=str(args.plan.resolve()), sha256=args.plan_sha256), {})
        output = Path(plan['output'])
        require(plan == build_plan(output, plan['qualification']), 'Exact reviewed plan differs')
        pins = merge(plan['pins'], {str(args.plan.resolve()): args.plan_sha256})
        live_plan = dict(plan, pins=pins, input_resolutions=dict(plan['input_resolutions'],
                         **{str(args.plan.resolve()): str(args.plan.resolve())}))
        guard, harness = h.load_measurement()
        check_execution_inputs(live_plan, harness, lock)
        supervisor = cold(h.SUPERVISOR, h.SUPERVISOR_SHA, 'apl_full_private_supervisor')
        output.mkdir(parents=True, exist_ok=False)
        for name in ('home', 'tmp'): (output/'environment'/name).mkdir(parents=True)
        guard.OUT, guard.REPORT = output, output/'report.json'
        harness.install_interrupt_handlers()
        rows = initial_rows(plan); snapshots = {}
        report = dict(schema='apl-workspace-full6-results-v1', status='running', started_at=guard.now(),
            supervisor=guard.identity(os.getpid()), plan=str(args.plan.resolve()), plan_sha256=args.plan_sha256,
            programs=rows, attempts=[], active=None, benchmark_order=BENCHES, completed_benchmarks=[],
            sample_count=3, full_performance_runs=0, source_aliases=plan['source_aliases'],
            source_work_profiles=1, canonical_loc_profiles=1, formatted_loc_profiles=0,
            planned_apl_samples=3, planned_matched_mech_samples=3, shared_timing_lock=str(h.LOCK),
            no_automatic_retry=True, stop_on_first_unqualified_attempt=True, full_size_work_qualified=False,
            full_timings_qualified=False, chart_admission=False, descriptive_provenance=[],
            kernel_identity_observation_gaps=[], validated_attempt_artifacts={})
        refresh_attempt_accounting(report); guard.save(guard.REPORT, report)
        try:
            for slot in schedule_for(plan['manifests']):
                bench, round_index, identity, key = slot
                row = rows[key]; manifest = dict(plan['manifests'][bench], pins=pins)
                check_execution_inputs(live_plan, harness, lock)
                harness.compact.wait_for_environment(harness.REQUIRED)
                verify_lock(lock)
                print('APL FULL', bench, round_index, identity, 21, flush=True)
                before = len(report['attempts'])
                try:
                    attempt = supervisor.one_attempt(guard, harness, row, manifest, report, round_index, lock.fileno())
                    record_attempt(supervisor, guard, harness, plan, report, row, slot, pins, snapshots, attempt, lock)
                except BaseException as error:
                    with supervisor.lifecycle_atomic():
                        if len(report['attempts']) == before:
                            preserve_wrapper_failure(guard, report, row, round_index, error)
                    raise
                verify_lock(lock)
            report['completed_benchmarks'] = ['binarytrees']
            check_success_ledger(plan, report)
            with supervisor.lifecycle_atomic(): report.update(status='complete', finished_at=guard.now())
        except BaseException as error:
            with supervisor.lifecycle_atomic():
                report.update(status='stopped-unqualified', finished_at=guard.now(),
                              error=str(error) or type(error).__name__, error_type=type(error).__name__)
                (output/'error.log').write_text(traceback.format_exc())
                guard.save(guard.REPORT, report)
            raise
        finally:
            with supervisor.lifecycle_atomic(): finish(live_plan, report, pins, snapshots, guard, harness, lock)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--plan', type=Path, required=True); prep.add_argument('--output', type=Path, required=True)
    prep.add_argument('--counts', type=Path, required=True); prep.add_argument('--counts-sha256', required=True)
    prep.add_argument('--work', type=Path, required=True); prep.add_argument('--work-sha256', required=True)
    run_parser = sub.add_parser('run')
    run_parser.add_argument('--plan', type=Path, required=True); run_parser.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
            and Path(sys.executable).resolve() == h.PYTHON.resolve(), 'Use retained Python -I -S -B without -O')
    def interrupted(signum, frame): raise KeyboardInterrupt('APL full cohort interrupted: '+str(signum))
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP): signal.signal(sig, interrupted)
    if args.mode == 'prepare': prepare(args)
    else: run(args)


if __name__ == '__main__': main()
