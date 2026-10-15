"""Prepare and own ninety fresh full-workload Rebol/control timing slots.

Two disclosed equivalent subject forms receive separate actual samples. The
frozen sampler and independent supervisor are reused without timing changes.
An actual independent Rebol qualification context is mandatory; no approval,
runtime discovery, compilation or native diagnostic is manufactured here.
"""
import argparse
import copy
from contextlib import contextmanager
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import stat
import statistics
import sys
import traceback
import types


ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/rebol/full90-v1'
QUALIFIER = ROOT/'tools/qualification/rebol_qualification.py'
HELPERS = ROOT/'tools/qualification/elixir_full.py'
HELPERS_SHA = '5fa93294c0f098b17384a43943f9c982e9447c7a309c1f64e1870389fb338703'
RECEIPTS = ROOT/'tools/qualification/prolog_reconcile.py'
RECEIPTS_SHA = 'a69b498cc0664b2951c1ef5ef2281f06f34e6415fcf6adfe8b723f06ca127cfe'
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
BENCHES = ('regexredux','revcomp','pidigits','spectralnorm','mandelbrot',
           'fasta','knucleotide','binarytrees','nbody','fannkuchredux')
FORMS = ('compact','optimized')
STDIN_BENCHES = ('regexredux','revcomp','knucleotide')
SOURCE_FILES = (Path(__file__).resolve(), Path(__file__).with_name('test_rebol_full.py'), PACKET/'README.md')
SUITE_LEASE = PACKET/'rebol-full90.owner.lock'
PROFILES = ROOT/'archive/languages/rebol/20261013/drafts/private-v1/profiles.json'
POLICY = ('Fresh direct Rebol process including runtime startup, authored source/facade evaluation, '
          'extension loading, full input, all work, complete output and shutdown; extension compilation, '
          'harness file setup, pin hashing, environment waits and output validation excluded')
ALIAS_POLICY = ('Physically preserve one equivalent baseline in both forms later; separate fresh actual '
                'records per form, no distinct optimization or copied timing')
FORBIDDEN_ENV = ('LD_PRELOAD','DYLD_INSERT_LIBRARIES','DYLD_LIBRARY_PATH','DYLD_FRAMEWORK_PATH',
                 'MECH_REBOL_IO_FAULT_REPORT','MECH_REBOL_PI_OBSERVATION','MECH_REBOL_MAP_OBSERVATION')


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def encoded(value):
    return (json.dumps(value, indent=2)+'\n').encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


@contextmanager
def regular(path):
    path = Path(path)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path, 'Physical regular input required')
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, 'rb') as stream:
        held = os.fstat(fd)
        require((held.st_dev,held.st_ino) == (before.st_dev,before.st_ino), 'Input replaced before read')
        yield stream
        after = path.lstat()
        require(stat.S_ISREG(after.st_mode) and (held.st_dev,held.st_ino) == (after.st_dev,after.st_ino),
                'Input replaced during read')


def read_bytes(path):
    with regular(path) as stream:
        raw = stream.read(32*1024**2+1)
        require(len(raw) <= 32*1024**2, 'Metadata exceeds intake bound')
        return raw


def sha(path):
    with regular(path) as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def merge(*groups):
    result = {}
    for group in groups:
        for path, expected in group.items():
            require(path not in result or result[path] == expected, 'Conflicting input identity')
            result[path] = expected
    return result


def reference(path, expected):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and type(expected) is str
            and re.fullmatch('[0-9a-f]{64}', expected), 'Exact absolute evidence reference required')
    return dict(path=str(path),sha256=expected)


def load(path, expected, name):
    raw = read_bytes(path)
    require(digest(raw) == expected, 'Reviewed Python source changed')
    require(name not in sys.modules, 'Unexpected cached module')
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


def orders_for(benchmark):
    ids = [f'rebol-{benchmark}-{form}' for form in FORMS] + ['mech-aot-control']
    return [dict(round=index+1,profiles=ids[index:]+ids[:index]) for index in range(3)]


def schedule_for(manifests):
    require(set(manifests) == set(BENCHES), 'Exactly ten full workloads required')
    slots = []
    for benchmark in BENCHES:
        manifest = manifests[benchmark]
        rows = manifest['profiles']
        ids = [f'rebol-{benchmark}-{form}' for form in FORMS] + ['mech-aot-control']
        require([row['id'] for row in rows] == ids and [row['language'] for row in rows] == ['rebol3','rebol3','mech']
                and all(row['benchmark'] == benchmark for row in rows), 'Both subject forms and control required')
        require(type(manifest['samples']) is int and manifest['samples'] == 3
                and manifest['orders'] == orders_for(benchmark), 'Exactly three rotated rounds required')
        require(all('timing_alias_of' not in row for row in rows), 'Copied timing aliases are forbidden')
        keys = {row['id']:row['key'] for row in rows}
        require(keys == {ids[0]:ids[0],ids[1]:ids[1],ids[2]:benchmark+':rebol-full-study:mech-control'},
                'Timing row identities differ')
        slots.extend((benchmark,order['round'],identity,keys[identity])
                     for order in manifest['orders'] for identity in order['profiles'])
    require(len(slots) == len(set(slots)) == 90 and len({slot[3] for slot in slots}) == 30,
            'Full90 schedule differs')
    return slots


def initial_rows(plan):
    return {row['key']:dict(copy.deepcopy(row),samples_seconds=[],sample_validation=[],attempts=[],measurement_status='pending')
            for manifest in plan['manifests'].values() for row in manifest['profiles']}


def summarize(rows, manifest):
    group = [rows[row['key']] for row in manifest['profiles']]
    if not all(len(row['samples_seconds']) == 3 or row.get('full_failure') for row in group):
        return False
    control = next(row for row in group if row['language'] == 'mech')
    for row in group:
        if not row.get('full_failure'):
            row.update(median_seconds=statistics.median(row['samples_seconds']),
                       sample_stdev_seconds=statistics.stdev(row['samples_seconds']))
    for row in group:
        row['time_x_mech'] = (row['median_seconds']/control['median_seconds']
                             if not row.get('full_failure') and not control.get('full_failure') else None)
        row['matched_mech_control'] = control['key']
        row['matched_mech_source_sha256'] = control['source_sha256']
    return True


def check_success_ledger(plan, report):
    rows = initial_rows(plan)
    index, failed, skips = 0, [], []
    for benchmark, round_index, identity, key in schedule_for(plan['manifests']):
        row = rows[key]
        if row.get('full_failure'):
            skips.append(dict(benchmark=benchmark,round=round_index,id=identity,key=key))
            continue
        require(index < len(report['attempts']), 'Missing native timing slot')
        attempt = report['attempts'][index]
        index += 1
        require(type(attempt['attempt']) is int and attempt['attempt'] == index
                and [attempt[k] for k in ('benchmark','round','id','key')] == [benchmark,round_index,identity,key],
                'Missing, repeated or reordered native timing slot')
        row['attempts'].append(index)
        if attempt['qualified']:
            row['samples_seconds'].append(attempt['seconds'])
            row['sample_validation'].append(attempt['validation'])
            row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
        else:
            row.update(full_failure=attempt,measurement_status='failed-full-workload')
            failed.append(key)
    require(index == len(report['attempts']) and index+len(skips) == 90
            and skips == report['skipped_failed_profile_slots'], 'Unaccounted timing attempt or skip')
    require(all(summarize(rows,manifest) for manifest in plan['manifests'].values()), 'Incomplete workload group')
    require(rows == report['programs'] and failed == report['isolated_failed_profiles'], 'Sample summaries differ from ledger')
    require(report['active'] is None and report['completed_benchmarks'] == list(BENCHES)
            and report['native_launch_unconfirmed_attempts'] == [] and report['full_performance_runs'] == index
            and report['qualified_samples'] == sum(len(row['samples_seconds']) for row in rows.values()),
            'Native timing accounting differs')


def attempt_paths(output, attempt):
    stem = f'{attempt["attempt"]:03d}-{attempt["id"]}'
    return (output/'attempts'/(stem+'.json'), output/'attempts'/(stem+'.supervisor.json'),
            output/'outer-supervisor'/(stem+'.json'))


def check_attempt(receipts, output, attempt, slot, row, manifest, pins, parent):
    paths = attempt_paths(output,attempt)
    require([attempt['result_path'],attempt['supervisor_result_path']] == [str(path) for path in paths[:2]],
            'Attempt receipt escaped output')
    raw = [read_bytes(path) for path in paths]
    original, supervised, outer = [receipts.p.strict_json(value) for value in raw]
    provenance = []
    receipts.check_attempt(attempt,original,supervised,list(slot),row,manifest,pins,provenance)
    gaps = receipts.check_outer(outer,attempt,parent)
    snapshots = {str(path):digest(value) for path,value in zip(paths,raw)}
    require(all(sha(path) == expected for path,expected in snapshots.items()), 'Receipt changed during validation')
    return snapshots, provenance, gaps


def record_attempt(helpers, receipts, supervisor, guard, harness, report, row, manifest, slot, pins, snapshots, attempt):
    with supervisor.lifecycle_atomic():
        report['attempts'].append(attempt)
        report['active'] = None
        row['attempts'].append(attempt['attempt'])
        helpers.refresh_attempt_accounting(report)
        guard.save(guard.REPORT,report)
        original = next(value for value in manifest['profiles'] if value['key'] == row['key'])
        captured,provenance,gaps = check_attempt(receipts,guard.OUT,attempt,slot,original,manifest,pins,os.getpid())
        snapshots.update(merge(snapshots,captured))
        report['descriptive_provenance'].extend(provenance)
        report['kernel_identity_observation_gaps'].extend(gaps)
        if attempt['qualified']:
            helpers.qualified_sample(attempt,manifest,row,harness.execution_fingerprint(row))
            require(attempt.get('stderr') == '', 'Successful full sample has stderr')
            row['samples_seconds'].append(attempt['seconds'])
            row['sample_validation'].append(attempt['validation'])
            row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
        elif helpers.isolated_failure(guard,attempt):
            row['measurement_status'] = 'failed-full-workload'
            row['full_failure'] = dict(attempt)
            report['isolated_failed_profiles'].append(row['key'])
        else:
            row['measurement_status'] = 'stopped-unqualified'
        if summarize(report['programs'],manifest) and row['benchmark'] not in report['completed_benchmarks']:
            report['completed_benchmarks'].append(row['benchmark'])
        report['validated_attempt_artifacts'] = dict(snapshots)
        helpers.refresh_attempt_accounting(report)
        guard.save(guard.REPORT,report)
        require(attempt['qualified'] or row.get('full_failure'), 'Integrity/environment/ownership failure; no retry')


def source_intake(source_ref):
    raw = read_bytes(source_ref['path'])
    require(digest(raw) == source_ref['sha256'], 'Independent source review changed')
    review = json.loads(raw)
    expected_files = {str(path.relative_to(ROOT)) for path in SOURCE_FILES}
    dependencies = {str(path.relative_to(ROOT)) for path in (QUALIFIER,HELPERS,RECEIPTS)}
    require(review['schema'] == 'rebol-full90-source-review-v1'
            and review['status'] == 'independent-source-review-complete-native-timing-pending'
            and review['independent_review'] is True and set(review['files']) == expected_files
            and set(review['dependencies']) == dependencies
            and review['full_timing_qualified'] is False and review['chart_admission'] is False,
            'Actual full90 source review required')
    pins = {str(ROOT/name):value for name,value in {**review['files'],**review['dependencies']}.items()}
    require(pins[str(HELPERS)] == HELPERS_SHA and pins[str(RECEIPTS)] == RECEIPTS_SHA,
            'Frozen timing helpers changed')
    for name,expected in pins.items():
        reference(name,expected)
        require(sha(name) == expected, 'Reviewed source changed')
    pins = merge(pins,{source_ref['path']:source_ref['sha256']})
    qualifier = load(QUALIFIER,pins[str(QUALIFIER)],'rebol_full90_qualification')
    require(qualifier.ROOT == ROOT, 'Qualification proof root changed')
    return qualifier,pins


def source_policy(base, runtime, image, environment, pins):
    benchmark = base['benchmark']
    require(base['language'] == 'rebol3' and base['original_profile_id'] == f'rebol-{benchmark}-baseline-v1'
            and base['maximum_workers'] == 1 and type(base['maximum_workers']) is int
            and base['cwd'] == str(ROOT) and base['formatted_loc'] is None,
            'Qualified base identity or count scope differs')
    require(base['command_prefix'] == [runtime['path'],'-q','-s',base['main']['path']]
            and base['input_kind'] == ('stdin' if benchmark in STDIN_BENCHES else 'integer-argument'),
            'Direct unchanged Rebol invocation required')
    require(base['alias_policy'] == dict(authored_source_forms=1,publication_forms=list(FORMS),
            distinct_optimization_claim=False,copied_timing_allowed=False), 'Equivalent-source policy changed')
    expected_environment = dict(fixed={name:environment[name] for name in
        ('PATH','LC_ALL','LANG','OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','VECLIB_MAXIMUM_THREADS')},
        fresh_directories=dict(HOME='home',REBOL_HOME='home',TMPDIR='tmp'),
        extension_variable='MECH_CLBG_REBOL_PRIMITIVES',ambient_loader_overrides=False,diagnostic_flags=[])
    require(base['runtime_environment_policy'] == expected_environment, 'Runtime environment policy differs')
    inputs = base['physical_inputs']
    require(len(inputs) == (5 if benchmark in ('pidigits','regexredux') else 4)
            and len({item['path'] for item in inputs}) == len(inputs), 'Incomplete counted source bundle')
    by_role = {}
    for item in inputs:
        reference(item['path'],item['sha256'])
        require(pins.get(item['path']) == item['sha256'] and item['counted'] is True
                and all(type(item[key]) is int and item[key] > 0 for key in ('canonical_loc','physical_loc')),
                'Unpinned or uncounted authored input')
        by_role.setdefault(item['role'],[]).append(item)
    require(set(by_role) == {'application','application-helper','application-launcher','general-library-helper'}
            and len(by_role['application']) == len(by_role['application-launcher']) == len(by_role['general-library-helper']) == 1,
            'Authored owner roles differ')
    require({key:by_role['application'][0][key] for key in ('path','sha256')} == base['main']
            and Path(by_role['application-launcher'][0]['path']).name == 'clbg_primitives.reb'
            and Path(by_role['general-library-helper'][0]['path']).name == 'clbg_primitives.c'
            and {Path(item['path']).name for item in by_role['application-helper']} ==
                ({'clbg_io.reb','clbg_big.reb'} if benchmark == 'pidigits' else
                 {'clbg_io.reb','clbg_regex.reb'} if benchmark == 'regexredux' else {'clbg_io.reb'}),
            'Counted application/helper bundle differs')
    require(all(type(base[key]) is int and base[key] == sum(item[key] for item in inputs)
                for key in ('canonical_loc','physical_loc')), 'Bundle totals differ')
    for item in (runtime,image):
        reference(item['path'],item['sha256'])
        require(pins.get(item['path']) == item['sha256'], 'Runtime/image not in actual closure')


def subject(base, form, admission, environment, pins):
    runtime,image = admission['runtime']['binary'],admission['extension_image']
    source_policy(base,runtime,image,environment,pins)
    benchmark = base['benchmark']; identity = f'rebol-{benchmark}-{form}'
    return dict(id=identity,key=identity,benchmark=benchmark,variant=form,language='rebol3',
        source=base['main']['path'],source_sha256=base['main']['sha256'],binary=runtime['path'],
        binary_sha256=runtime['sha256'],command=base['command_prefix']+([] if benchmark in STDIN_BENCHES else ['{n}']),
        cwd=base['cwd'],runtime_environment=copy.deepcopy(environment),maximum_workers=1,
        physical_inputs=copy.deepcopy(base['physical_inputs']),support=dict(extension_image=copy.deepcopy(image),
            counted_authored_inputs=copy.deepcopy(base['physical_inputs'])),
        original_profile_id=base['original_profile_id'],corrections=copy.deepcopy(base['corrections']),
        alias_policy=copy.deepcopy(base['alias_policy']),source_alias_group=base['original_profile_id'],
        separate_fresh_samples_required=True,optimization_claim=False,source_work_qualified=True,
        canonical_loc_qualified=True,formatted_loc_qualified=False,loc=base['canonical_loc'],
        canonical_loc=base['canonical_loc'],physical_loc=base['physical_loc'],formatted_loc=None,
        runtime_policy_changes=[],diagnostic_flags=[],runtime_source_equivalence_proven=False,
        chart_admission=False)


def build_plan(admission, held, helpers, receipts, output, qualification_ref, source_ref, source_pins):
    require(admission['schema'] == 'rebol-pre-timing-admission-v1' and admission['manifest'] == qualification_ref,
            'Actual qualification manifest differs')
    scope = admission['scope']
    require(all(scope[key] is True for key in ('required_work_qualified','canonical_source_count_qualified',
        'bounded_output_qualified','extension_abi_qualified','full_primitive_fixtures_qualified'))
        and all(scope[key] is False for key in ('runtime_source_equivalence_proven','full_timing_qualified','chart_admission')),
        'Actual pre-timing qualification gates required')
    bases = admission['bases']
    require(len(bases) == 10 and {base['benchmark'] for base in bases} == set(BENCHES), 'Ten actual base bundles required')
    e,pins,resolutions = held.evidence,held.pins,held.resolutions
    for name,expected in source_pins.items():e.pin(pins,resolutions,name,expected)
    require(str(PROFILES) in pins, 'Original profile policy must be in qualification closure')
    original = e.document(reference(PROFILES,pins[str(PROFILES)]),pins,resolutions)
    require(original['language'] == 'rebol3' and original['publication_forms_proposed'] == list(FORMS)
            and original['publication_alias_policy'] == ALIAS_POLICY
            and {item['id'] for item in original['profiles']} == {base['original_profile_id'] for base in bases},
            'Original forms policy changed')
    environment = e.environment(output)
    environment['MECH_CLBG_REBOL_PRIMITIVES'] = admission['extension_image']['path']
    require(not set(FORBIDDEN_ENV)&set(environment), 'Diagnostic/ambient loader overrides forbidden')
    controls = helpers.controls(pins)
    extra = merge(helpers.SAMPLER_PINS,{str(helpers.SHARED):helpers.SHARED_SHA,
        str(helpers.SUPERVISOR):helpers.SUPERVISOR_SHA,str(helpers.PYTHON.resolve()):helpers.PYTHON_SHA,
        str(receipts.HELPER):receipts.HELPER_SHA})
    for name,expected in merge(pins,extra).items():e.pin(pins,resolutions,name,expected)
    manifests = {}
    for benchmark in BENCHES:
        base = next(value for value in bases if value['benchmark'] == benchmark)
        rows = [subject(base,form,admission,environment,pins) for form in FORMS]
        controls[benchmark]['key'] = benchmark+':rebol-full-study:mech-control'
        rows.append(controls[benchmark]);size,count,output_sha = helpers.FULL[benchmark]
        manifests[benchmark] = dict(benchmark=benchmark,profiles=rows,samples=3,size=size,
            orders=orders_for(benchmark),canonical_full_workload=True,timeout_seconds=21600,
            supervisor_timeout_seconds=22200,maximum_rss_mib=10240,
            full_output_reference=None if benchmark == 'nbody' else dict(bytes=count,sha256=output_sha),
            shared_timing_lock=str(helpers.LOCK),no_automatic_retry=True,chart_admission=False,
            compilation_outside_timer=True,runtime_source_helpers_extension_loading_inside_timer=True)
    require(len({item['path'] for base in bases for item in base['physical_inputs']}) == 15,
            'Exactly fifteen counted physical sources required')
    return dict(schema='rebol-qualified-full90-v1',status='prepared-awaiting-independent-review',
        pins_verified=True,controller=str(Path(__file__).resolve()),controller_sha256=source_pins[str(Path(__file__).resolve())],
        repository=str(ROOT),output=str(output),qualification_manifest=qualification_ref,source_review=source_ref,
        qualification=copy.deepcopy(admission),original_profiles=dict(path=str(PROFILES),sha256=pins[str(PROFILES)]),
        source_work_profiles=20,canonical_loc_profiles=20,formatted_loc_profiles=0,distinct_subject_bundles=10,
        counted_physical_sources=15,retained_bounded_cases=149,retained_primitive_cases=18,
        compiler_invocations=0,fixture_reexecutions=0,bounded_reexecutions=0,new_native_probes=0,
        original_files_mutated=False,samples=3,rebol_samples=60,matched_mech_samples=30,full_processes=90,
        schedule=[list(slot) for slot in schedule_for(manifests)],manifests=manifests,
        pins=dict(pins),resolutions=dict(resolutions),shared_timing_lock=str(helpers.LOCK),common_mutex_inode=79859134,
        continuous_common_mutex=True,no_automatic_retry=True,full_timings_qualified=False,chart_admission=False,
        runtime_source_equivalence_proven=False,timing_policy=POLICY)


def write_new(path, value, ownership=None):
    raw = encoded(value)
    with Path(path).open('xb') as stream:
        identity = (os.fstat(stream.fileno()).st_dev,os.fstat(stream.fileno()).st_ino)
        if ownership is not None:ownership.update(path=str(path),raw=raw,identity=identity)
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    return raw,identity


def verify_written(path, raw, identity):
    before = Path(path).lstat()
    require(stat.S_ISREG(before.st_mode) and (before.st_dev,before.st_ino) == identity
            and read_bytes(path) == raw, 'Owned metadata changed')


@contextmanager
def suite_lease():
    require(PACKET.resolve(strict=True) == PACKET, 'Physical existing packet required')
    fd = os.open(SUITE_LEASE,os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_NONBLOCK,0o600)
    with os.fdopen(fd,'r+b') as stream:
        require(stat.S_ISREG(os.fstat(fd).st_mode), 'Regular suite lease required')
        fcntl.flock(stream,fcntl.LOCK_EX|fcntl.LOCK_NB)
        identity = (os.fstat(fd).st_dev,os.fstat(fd).st_ino)
        def check():
            held,named = os.fstat(fd),SUITE_LEASE.lstat()
            require(stat.S_ISREG(named.st_mode) and SUITE_LEASE.resolve() == SUITE_LEASE
                    and (held.st_dev,held.st_ino) == (named.st_dev,named.st_ino) == identity,
                    'Suite lease identity changed')
        check()
        try:yield check
        finally:check()


def check_output_paths(plan_path, output):
    for path in (plan_path,output):
        require(path.is_absolute() and path.parent.resolve(strict=True) == path.parent
                and path.is_relative_to(PACKET) and path != PACKET and not os.path.lexists(path),
                'Fresh physical path under full90 packet required')
    require(plan_path != output and not plan_path.is_relative_to(output), 'Plan cannot be a run artifact')


def check_inputs(plan, held, helpers, harness, check_lease):
    held.recheck()
    helpers.check_execution_inputs(plan,harness)
    helpers.verify_lock(held.common)
    check_lease()


def artifact_inventory(output):
    result = {}
    for path in sorted(output.rglob('*')):
        mode = path.lstat().st_mode
        require(stat.S_ISREG(mode) or stat.S_ISDIR(mode), 'Nonregular run artifact')
        require(path.resolve(strict=True) == path, 'Artifact directory alias changed')
        if stat.S_ISREG(mode):result[str(path)] = sha(path)
    return result


def finish(state, forced_error=None):
    """Masked final callback, after qualification replay and before all leases close."""
    plan,report = state['plan'],state['report']
    held,helpers,receipts = state['held'],state['helpers'],state['receipts']
    guard,harness,snapshots = state['guard'],state['harness'],state['snapshots']
    errors = []
    def problem(error, path=None):
        errors.append(dict(path=path,error=str(error) or type(error).__name__,error_type=type(error).__name__))
    if forced_error is not None:problem(forced_error)
    helpers.refresh_attempt_accounting(report)
    try:
        check_inputs(plan,held,helpers,harness,state['check_lease'])
        require(report['status'] != 'running', 'Run body did not reach closed status')
        require(report['active'] is None, 'Supervisor cleanup left active state')
        complete = report['status'] in ('complete','complete-with-unqualified-profiles')
        if complete:check_success_ledger(plan,report)
        expected,previous = set(),None
        for attempt in report['attempts']:
            if attempt.get('wrapper_supervisor_failure'):
                require(not complete, 'Wrapper failure cannot complete cohort')
                continue
            slot = tuple(attempt[key] for key in ('benchmark','round','id','key'))
            require(slot in schedule_for(plan['manifests']), 'Attempt outside full90')
            manifest = plan['manifests'][attempt['benchmark']]
            row = next(value for value in manifest['profiles'] if value['key'] == attempt['key'])
            current,_,_ = check_attempt(receipts,guard.OUT,attempt,slot,row,manifest,held.pins,os.getpid())
            require(all(snapshots.get(path) == value for path,value in current.items()), 'Validated receipt changed')
            begin,end = receipts.p.timestamp(attempt['started_at']),receipts.p.timestamp(attempt['finished_at'])
            require(begin <= end and (previous is None or previous <= begin), 'Overlapping native intervals')
            previous = end;expected.update(current)
        require(set(snapshots) == expected, 'Unowned validated receipt')
        if complete:
            require(set(artifact_inventory(guard.OUT)) == expected|{str(guard.REPORT)}, 'Completed artifact membership differs')
            require(report['independent_supervisors'] == [dict(path=str(attempt_paths(guard.OUT,a)[2]),
                sha256=snapshots[str(attempt_paths(guard.OUT,a)[2])],status='returned') for a in report['attempts']],
                'Independent supervisor ledger differs')
    except BaseException as error:problem(error)
    report['pins_unchanged_at_end'] = not errors
    report['validated_attempt_artifacts'] = dict(snapshots)
    if errors:report.update(status_before_terminal_integrity_failure=report['status'],status='failed-terminal-integrity',terminal_integrity_errors=errors)
    report_raw = encoded(report)
    guard.save(guard.REPORT,report)
    available,held_now,report_sha = {},False,digest(report_raw)
    try:
        available = artifact_inventory(guard.OUT)
        require(available.get(str(guard.REPORT)) == digest(report_raw), 'Serialized report changed before inventory')
        require(all(available.get(path) == expected for path,expected in snapshots.items()), 'Inventory adopted changed validated bytes')
        check_inputs(plan,held,helpers,harness,state['check_lease'])
        require(artifact_inventory(guard.OUT) == available, 'Artifact changed during final prerequisite replay')
        report_sha = digest(read_bytes(guard.REPORT))
        require(report_sha == digest(report_raw) == available.get(str(guard.REPORT)),
                'Report changed during final prerequisite replay')
        helpers.verify_lock(held.common);state['check_lease']();held_now = True
    except BaseException as error:problem(error)
    if errors:
        held_now = False
        report.update(status='failed-terminal-integrity',pins_unchanged_at_end=False,terminal_integrity_errors=errors)
        # Preserve any independently changed report; only rewrite our exact bytes.
        try:
            require(read_bytes(guard.REPORT) == report_raw, 'Changed report preserved')
            guard.save(guard.REPORT,report);report_sha = digest(encoded(report))
            available[str(guard.REPORT)] = report_sha
        except BaseException as error:problem(error,str(guard.REPORT))
    terminal = dict(schema='rebol-full90-terminal-v1',status=report['status'],report=str(guard.REPORT),
        report_sha256=report_sha,prerequisite_pins=dict(held.pins),prerequisite_resolutions=dict(held.resolutions),
        available_evidence_pins=available,validated_attempt_artifacts=dict(snapshots),integrity_errors=errors,
        common_mutex_held=held_now,common_mutex_inode=79859134,common_mutex_held_continuously=held_now,
        full_performance_runs=report['full_performance_runs'],saved_attempts=len(report['attempts']),
        registered_native_attempts=report['registered_native_attempts'],
        native_launch_unconfirmed_attempts=report['native_launch_unconfirmed_attempts'],
        qualified_samples=report['qualified_samples'],skipped_failed_profile_slots=report['skipped_failed_profile_slots'],
        compiler_invocations=0,fixture_reexecutions=0,bounded_reexecutions=0,repeated_completed_samples=0,
        original_files_mutated=False,full_timings_qualified=False,runtime_source_equivalence_proven=False,chart_admission=False)
    state['terminal_owned'] = {}
    raw,identity = write_new(guard.OUT/'terminal.json',terminal,state['terminal_owned'])
    verify_written(guard.OUT/'terminal.json',raw,identity)
    helpers.verify_lock(held.common);state['check_lease']()
    require(not errors, 'Terminal integrity failed; actual artifacts preserved')


def downgrade_terminal(state, error, *, leases_may_be_released=False):
    owned = state.get('terminal_owned')
    if not owned:return
    path = Path(owned['path'])
    verify_written(path,owned['raw'],owned['identity'])
    value = json.loads(owned['raw'])
    if value['status'] not in ('complete','complete-with-unqualified-profiles'):return
    value.update(status='failed-terminal-integrity',full_timings_qualified=False,chart_admission=False,
                 common_mutex_held=False,common_mutex_held_continuously=False)
    value['integrity_errors'].append(dict(path=None,error=str(error) or type(error).__name__,error_type=type(error).__name__))
    # Change only the newly created terminal inode and its exact owned bytes.
    fd = os.open(path,os.O_RDWR|os.O_NOFOLLOW|os.O_NONBLOCK)
    with os.fdopen(fd,'r+b') as stream:
        st = os.fstat(fd)
        require(stat.S_ISREG(st.st_mode) and (st.st_dev,st.st_ino) == owned['identity']
                and stream.read() == owned['raw'], 'Changed terminal preserved')
        raw = encoded(value);stream.seek(0);stream.write(raw);stream.truncate();stream.flush();os.fsync(fd)
        owned['raw'] = raw
    verify_written(path,raw,owned['identity'])


def finalize_once(state, forced_error=None):
    if not state.get('started'):return
    if state.get('finalization_started'):
        if forced_error is not None:downgrade_terminal(state,forced_error)
        return
    with state['supervisor'].lifecycle_atomic():
        state['finalization_started'] = True
        try:finish(state,forced_error)
        except BaseException as error:
            downgrade_terminal(state,error)
            raise


@contextmanager
def final_failure_guard(state):
    """A late enclosing lease check must not leave a successful owned terminal."""
    try:yield
    except BaseException as original:
        try:
            if state.get('terminal_owned'):
                with state['supervisor'].lifecycle_atomic():
                    downgrade_terminal(state,original,leases_may_be_released=True)
        except BaseException as closure:
            raise BaseExceptionGroup('Run failed; terminal preservation also failed',[original,closure])
        raise


def run_loop(state):
    plan,held,helpers = state['plan'],state['held'],state['helpers']
    guard,harness,supervisor,receipts = (state[key] for key in ('guard','harness','supervisor','receipts'))
    output = Path(plan['output'])
    require(not os.path.lexists(output), 'No overwrite, resume, or repeated sample')
    guard.OUT,guard.REPORT = output,output/'report.json'
    report = dict(schema='rebol-full90-results-v1',status='running',started_at=guard.now(),
        supervisor=guard.identity(os.getpid()),plan=state['plan_ref']['path'],plan_sha256=state['plan_ref']['sha256'],
        qualification_manifest=plan['qualification_manifest'],programs=initial_rows(plan),attempts=[],active=None,
        benchmark_order=list(BENCHES),completed_benchmarks=[],sample_count=3,full_performance_runs=0,
        skipped_failed_profile_slots=[],isolated_failed_profiles=[],shared_timing_lock=plan['shared_timing_lock'],
        source_work_profiles=20,canonical_loc_profiles=20,formatted_loc_profiles=0,planned_rebol_samples=60,
        planned_matched_mech_samples=30,full_timings_qualified=False,runtime_source_equivalence_proven=False,
        chart_admission=False,no_automatic_retry=True,validated_attempt_artifacts={},descriptive_provenance=[],
        kernel_identity_observation_gaps=[])
    state.update(report=report,snapshots={})
    harness.install_interrupt_handlers()
    try:
        with supervisor.lifecycle_atomic():
            output.mkdir();state['started'] = True
        for name in ('home','tmp'):(output/name).mkdir()
        helpers.refresh_attempt_accounting(report);guard.save(guard.REPORT,report)
        for bench,round_index,identifier,key in schedule_for(plan['manifests']):
            row = report['programs'][key]
            manifest = dict(plan['manifests'][bench],pins=dict(held.pins))
            if row.get('full_failure'):
                with supervisor.lifecycle_atomic():
                    report['skipped_failed_profile_slots'].append(dict(benchmark=bench,round=round_index,id=identifier,key=key))
                    guard.save(guard.REPORT,report)
                continue
            check_inputs(plan,held,helpers,harness,state['check_lease'])
            harness.compact.wait_for_environment(harness.REQUIRED)
            check_inputs(plan,held,helpers,harness,state['check_lease'])
            print('REBOL FULL',bench,round_index,identifier,manifest['size'],flush=True)
            before = len(report['attempts'])
            try:
                attempt = supervisor.one_attempt(guard,harness,row,manifest,report,round_index,held.common.fileno())
                record_attempt(helpers,receipts,supervisor,guard,harness,report,row,manifest,
                    (bench,round_index,identifier,key),held.pins,state['snapshots'],attempt)
            except BaseException as error:
                with supervisor.lifecycle_atomic():
                    if len(report['attempts']) == before:helpers.preserve_wrapper_failure(guard,report,row,round_index,error)
                raise
            helpers.verify_lock(held.common);state['check_lease']()
        check_success_ledger(plan,report)
        with supervisor.lifecycle_atomic():
            report.update(status='complete-with-unqualified-profiles' if report['isolated_failed_profiles'] else 'complete',
                          finished_at=guard.now())
    except BaseException as error:
        if not state.get('started'):raise
        with supervisor.lifecycle_atomic():
            report.update(status='stopped-unqualified',finished_at=guard.now(),error=str(error) or type(error).__name__,
                          error_type=type(error).__name__)
            with (output/'error.log').open('x') as stream:stream.write(traceback.format_exc())
            guard.save(guard.REPORT,report)
        raise


def execute(args):
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
            and Path(sys.executable).resolve() == PYTHON.resolve(), 'Use retained Python -I -S -B without -O')
    require(not any(name in os.environ for name in FORBIDDEN_ENV)
            and not any(name.startswith(('DYLD_','MECH_REBOL_')) for name in os.environ),
            'Ambient native injection or diagnostic environment forbidden')
    plan_path = args.plan.absolute()
    if args.mode == 'prepare':
        source_ref = reference(args.source_review.absolute(),args.source_review_sha256)
        qualification_ref = reference(args.qualification_manifest.absolute(),args.qualification_manifest_sha256)
        output = args.output.absolute();check_output_paths(plan_path,output)
        saved = None
    else:
        plan_ref = reference(plan_path,args.plan_sha256)
        raw = read_bytes(plan_path);require(digest(raw) == plan_ref['sha256'], 'Reviewed prepared plan changed')
        saved = json.loads(raw);source_ref = saved['source_review'];qualification_ref = saved['qualification_manifest']
        output = Path(saved['output'])
        require(output.parent.resolve(strict=True) == output.parent and output.is_relative_to(PACKET)
                and output != PACKET and plan_path.parent.resolve(strict=True) == plan_path.parent
                and plan_path.is_relative_to(PACKET) and not os.path.lexists(output), 'Fresh physical output required')
    q,source_pins = source_intake(source_ref)
    state,prepared = {},{}
    with final_failure_guard(state), suite_lease() as check_lease:
        def final_check():
            if prepared:verify_written(plan_path,prepared['raw'],prepared['identity'])
            check_lease()
            finalize_once(state)
        def exit_failure():
            finalize_once(state,AssertionError('Qualification context or body failed before lease release'))
        with q.review_context(Path(qualification_ref['path']),qualification_ref['sha256'],
                on_exit_failure=exit_failure,final_consumer_check=final_check) as (admission,held):
            helpers = load(HELPERS,HELPERS_SHA,'rebol_full90_frozen_timing_helpers')
            receipts = load(RECEIPTS,RECEIPTS_SHA,'rebol_full90_independent_receipts')
            helpers.checked_runtime()
            plan = build_plan(admission,held,helpers,receipts,output,qualification_ref,source_ref,source_pins)
            if saved is not None:require(plan == saved, 'Prepared plan differs from exact qualification/schedule/pins')
            guard,harness = helpers.load_measurement()
            check_inputs(plan,held,helpers,harness,check_lease)
            if args.mode == 'prepare':
                raw,identity = write_new(plan_path,plan)
                prepared.update(raw=raw,identity=identity)
            else:
                held.evidence.pin(held.pins,held.resolutions,plan_path,plan_ref['sha256'])
                supervisor = load(helpers.SUPERVISOR,helpers.SUPERVISOR_SHA,'rebol_full90_frozen_supervisor')
                state.update(plan=plan,plan_ref=plan_ref,held=held,helpers=helpers,receipts=receipts,guard=guard,
                             harness=harness,supervisor=supervisor,check_lease=check_lease)
                run_loop(state)
    print(json.dumps(dict(plan=str(plan_path),sha256=sha(plan_path),full_processes=90,
        native_executions=0 if args.mode == 'prepare' else state['report']['full_performance_runs'],
        status=plan['status'] if args.mode == 'prepare' else state['report']['status'])),flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode',required=True)
    prepare = modes.add_parser('prepare',help='Strict actual prerequisite replay under the original common mutex; no native process')
    for name in ('qualification-manifest','source-review'):
        prepare.add_argument('--'+name,type=Path,required=True)
        prepare.add_argument('--'+name+'-sha256',required=True)
    prepare.add_argument('--plan',type=Path,required=True);prepare.add_argument('--output',type=Path,required=True)
    run = modes.add_parser('run',help='Run the independently reviewed exact prepared full90 plan once')
    run.add_argument('--plan',type=Path,required=True);run.add_argument('--plan-sha256',required=True)
    execute(parser.parse_args())


if __name__ == '__main__':main()
