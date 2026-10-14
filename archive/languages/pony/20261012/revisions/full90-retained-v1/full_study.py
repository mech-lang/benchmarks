"""Complete Pony compact/optimized suite with fresh unchanged Mech controls.

Each benchmark uses its own reviewed manifest and actual three-process samples;
source/hash/compilation checks are outside elapsed timing. All ownership and
complete-output qualification comes from the frozen shared sampler guard.
"""
import argparse
from contextlib import ExitStack
import copy
import fcntl
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import statistics
import sys
import types

HERE = Path(__file__).resolve().parent
COHORT = HERE.parents[1]
CLBG = COHORT.parents[1]
REPOSITORY = CLBG.parent.parent
HOST = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech')
HOST_CLBG = HOST / 'benchmarks/clbg'
HOST_COHORT = HOST_CLBG / 'pony-comparison/20261012'
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
LOCK = Path('/tmp/mech-clbg-timing.lock')
SOURCE_AUDIT = HOST_CLBG / 'r-apl-uiua-comparison/20261011/source-audit-r.json'
MANDEL = HOST_CLBG / 'mandelbrot/experiments/20261011-array-state/source-modes-study/full-study/manifest.json'
QUALIFICATION = HOST_COHORT / 'qualification/private-v8/report.json'
Q_SHA = '4da05f6dd351609923f5f1ca227d3db2b33a354925614b74f9c5dae39839d159'
WORK = HOST_COHORT / 'work-qualification/private-v8-work-reviewed-v1/report.json'
WORK_SHA = 'aa7786b7cd16565a5ef21cb0bb56e8e0b7ccf77ddf5e98cbcfd1710b6b6aa421'
ALLOCATION = WORK.with_name('allocation.json')
ALLOCATION_SHA = '354f4eab47aef151f1f5cf29824c2b7b4f45f582b307b2373ca0ec316434d346'
LOC = HOST_COHORT / 'source-counts/loc-reviewed-seal-v1/qualified-loc-overlay.json'
LOC_SHA = '5831dd9675da58865a39edab9f86ecbdb36377a470052814aeb06a981fbbe182'
LOC_TERMINAL_SHA = '80d86166ffd0a8175a437579b923652238b87188b32ab4d9bda23162b8d17073'
LOC_ROOT = CLBG / 'continuation/jobs/pony-reviewed-loc-closed-review-v1/receipt.json'
LOC_ROOT_SHA = '4c0d830178406cd4ab4bd800eabfe6493a68816e363c52eeb2e6f20dfc0e72de'
LOC_OWNER = CLBG / 'continuation/owned-jobs/pony-reviewed-loc-seal-v1'
PRIOR = HOST_COHORT / 'revisions/work-full-v5'
PRIOR_FULL_SHA = 'd9c80514f5625c73729bd94a3736c47005dbc7f6781d91f3b3be57a10108655b'
TREE_SHA = '87c0dcaf5c952366e487e2c0205fc39aacbe3c6ef2c2b39bec8fe99a39a49239'
PREPARATION_SHA = '4cc9e102a846c6ac79cffdface18da6e83c5d036a40184cd311995722f32ca03'
FULL_FIXTURES = HOST_COHORT / 'work-qualification/private-v8-work-v2/fixtures/full-gates/full-gates-fixture-receipt.json'
FULL_FIXTURES_SHA = '21a39ab9e02a83a743a469bf7477b752b8bd305470fe54b56e1e495a4d3280b2'
preparation = None


def bind(path, digest, pins):
    path = Path(path).absolute()
    assert len(digest) == 64 and all(c in '0123456789abcdef' for c in digest)
    with path.open('rb') as stream: actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    assert actual == digest, ('Pinned input changed', str(path))
    assert str(path) not in pins or pins[str(path)] == digest
    pins[str(path)] = digest
    return path


def read(path, digest, pins):
    return json.loads(bind(path, digest, pins).read_bytes())


def absorb(values, pins):
    assert type(values) is dict and values
    for path, digest in values.items():
        assert Path(path).is_absolute()
        bind(path, digest, pins)


def cold(path, digest, name, pins):
    path = bind(path, digest, pins)
    assert name not in sys.modules
    module = types.ModuleType(name); module.__file__ = str(path)
    sys.modules[name] = module
    raw = path.read_bytes(); assert hashlib.sha256(raw).hexdigest() == digest
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def prerequisites(args):
    global preparation
    pins = {}
    for name, digest in (('full_study.py', args.worker_sha256), ('REVIEW.md', args.review_sha256)):
        assert not (HERE / name).stat().st_mode & 0o222
        bind(HERE / name, digest, pins)
    bind(Path(sys.executable).resolve(), 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e', pins)
    retained = cold(HOST_COHORT / 'revisions/loc-reviewed-seal-v1/seal.py',
        '2b6983388a4cbcb15a64903238026a2920ee811391fc104151cb79c85dc04604', 'pony_full_retained_work_closure', pins)
    work = retained.work_closure(pins)
    assert pins[str(WORK)] == WORK_SHA
    q = read(QUALIFICATION, Q_SHA, pins); absorb(q['pins'], pins)
    assert len(q['profiles']) == len({row['id'] for row in q['profiles']}) == 20
    assert q['reused_bounded_cases'] == 154 and q['fresh_unscored_primitive_cases'] == 1
    allocation = read(ALLOCATION, ALLOCATION_SHA, pins)
    root = read(LOC_ROOT, LOC_ROOT_SHA, pins)
    assert root['status'] == 'closed-qualified-Pony20-canonical-LOC' and root['verified_pins'] == 10750
    assert (root['profiles'], root['unique_authored_sources'], root['bundle_entries'], root['original_diagnostics_preserved']) == (20,21,22,6)
    assert root['count_override'] is root['chart_admission'] is False and root['common_mutex_held'] is True
    assert root['overlay_path'] == str(LOC) and root['overlay_sha256'] == LOC_SHA and root['body_terminal_sha256'] == LOC_TERMINAL_SHA
    assert all(type(root[key]) is int and root[key] == 0 for key in ('native_commands','count_replays','fixture_reexecutions','benchmark_runs'))
    terminal = read(LOC.with_name('terminal.json'), LOC_TERMINAL_SHA, pins)
    assert terminal['status'] == 'completed-Pony-LOC-metadata' and terminal['body_error'] is None and terminal['integrity_errors'] == []
    assert terminal['common_mutex_held'] is True
    absorb(terminal['available_evidence_pins'], pins)
    ended = read(LOC_OWNER / 'terminal.json', root['durable_terminal_sha256'], pins)
    request = read(LOC_OWNER / 'request.json', root['request_sha256'], pins)
    release_path = CLBG / 'continuation/jobs/pony-reviewed-loc-release-v1/release.json'
    release = read(release_path, file_digest(release_path), pins)
    assert ended['status'] == 'command-exited-zero-awaiting-report-review' and type(ended['exit_code']) is int and ended['exit_code'] == 0
    assert ended['stop_signals'] == [] and ended['actual_command_started'] is True and not ended.get('error')
    assert request['command'] == release['command'] and request['cwd'] == str(HOST)
    started, worker = [read(LOC_OWNER / name, file_digest(LOC_OWNER / name), pins) for name in ('command-started.json','worker-started.json')]
    assert all(item['command'] == request['command'] and item['cwd'] == str(HOST) for item in (started, worker))
    assert ended['command_identity'] == started['command_identity'] and ended['worker_identity'] == worker['worker_identity']
    assert ended['command_pid'] == started['command_pid'] == root['command_pid'] == 11314 and worker['worker_identity']['pid'] == root['worker_pid'] == 11310
    assert ended['command_identity_observation_missing'] is started['command_identity_observation_missing'] is False
    assert ended['automatic_retry'] is ended['qualification_granted'] is request['automatic_retry'] is request['qualification_granted'] is False
    loc = read(LOC, LOC_SHA, pins); absorb(loc['pins'], pins)
    assert loc['status'] == 'qualified-exact-source-LOC' and loc['canonical_LOC_admitted'] is True and loc['chart_admission'] is False
    assert loc['profile_count'] == 20 and loc['complete_authored_source_bundles'] is True and loc['unresolved'] == []
    assert set(loc['profiles']) == set(loc['compiler_bound_input_inventory']) == {row['id'] for row in q['profiles']}
    for path, digest in root['new_repository_copies'].items():
        bind(path, digest, pins)
    fixture = read(FULL_FIXTURES, FULL_FIXTURES_SHA, pins)
    expected = sorted('test_full_study.IsolatedFailures.' + name for name in (
        'test_real_source_failure_with_literal_safe_gates_is_isolated',
        'test_every_unsafe_gate_stops_and_truthy_values_do_not_waive_it',
        'test_missing_gates_and_non_source_failure_stop'))
    assert fixture['status'] == 'passed' and fixture['tests_run'] == 3 and fixture['actual_common_mutex_held'] is True
    assert all(sorted(fixture[key]) == expected and len(fixture[key]) == 3 for key in ('expected_ids','discovered_ids','started_ids'))
    assert all(type(fixture[key]) is int and fixture[key] == 0 for key in ('failures','errors','skipped','expected_failures','unexpected_successes','native_probes'))
    bind(fixture['raw_log'], fixture['raw_log_sha256'], pins)
    bind(PRIOR / 'full_study.py', PRIOR_FULL_SHA, pins)
    tree = cold(PRIOR / 'full_prerequisite.py', TREE_SHA, 'pony_full_original_tree_gate', pins)
    tree_gate = tree.require_tree_proof(q, work, allocation, ALLOCATION_SHA, file_digest, lambda path: read(path, pins[str(Path(path).absolute())], pins))
    bind(SOURCE_AUDIT, args.source_audit_sha256, pins); bind(MANDEL, args.mandelbrot_manifest_sha256, pins)
    preparation = cold(HOST_COHORT / 'guarded_prepare_v6.py', PREPARATION_SHA, 'pony_full_original_preparation', pins)
    guard = cold(preparation.GUARD, preparation.GUARD_SHA, 'pony_full_original_guard', pins)
    # Existing loaders must compile the independently pinned original source,
    # including prepare -> arrays -> compact -> common; never consume old pyc.
    for module in sys.modules.values():
        filename = getattr(module, '__file__', None)
        if filename and Path(filename).is_relative_to(HOST_CLBG):
            assert str(Path(filename).absolute()) in pins
    original_get_code = importlib.machinery.SourceFileLoader.get_code
    def checked_code(loader, fullname):
        path = Path(loader.path).absolute()
        if path.is_relative_to(HOST_CLBG):
            assert path.suffix == '.py' and str(path) in pins
            raw = bind(path, pins[str(path)], pins).read_bytes()
            assert hashlib.sha256(raw).hexdigest() == pins[str(path)]
            return compile(raw, str(path), 'exec')
        return original_get_code(loader, fullname)
    importlib.machinery.SourceFileLoader.get_code = checked_code
    try:
        harness = guard.load_harness()
    finally:
        importlib.machinery.SourceFileLoader.get_code = original_get_code
    for module in sys.modules.values():
        filename = getattr(module, '__file__', None)
        if filename and Path(filename).is_relative_to(HOST_CLBG):
            assert str(Path(filename).absolute()) in pins
            bind(filename, pins[str(Path(filename).absolute())], pins)
    guard.verify(pins)
    return q, work, loc, guard, harness, pins, tree_gate


def file_digest(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def common_identity(lock):
    opened, named = os.fstat(lock.fileno()), LOCK.stat()
    assert (opened.st_dev,opened.st_ino) == (named.st_dev,named.st_ino) and opened.st_ino == 79859134


def full_reference(harness, benchmark):
    if benchmark == 'nbody': return None
    if benchmark in {'spectralnorm', 'fannkuchredux'}:
        data = b'1.274224153\n' if benchmark == 'spectralnorm' else b'3968050\nPfannkuchen(12) = 65\n'
        return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    if benchmark in {'pidigits', 'regexredux'}:
        reference = HOST_CLBG / benchmark / 'inputs/output-full.txt'
        return dict(bytes=reference.stat().st_size, sha256=preparation.sha(reference))
    size, digest = harness.compact.HASHES[benchmark][1]
    return dict(bytes=size, sha256=digest)


def seal(args):
    revision = args.revision
    output = COHORT / 'full-studies' / revision
    with LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        common_identity(lock)
        assert not output.exists(), 'Never replace a reviewed study revision'
        q, work, loc, guard, harness, pins, tree_gate = prerequisites(args)
        report_path, work_path = QUALIFICATION, WORK
        reviewed = {row['id']: row for row in work['reviewed_sources']}
        assert set(reviewed) == {row['id'] for row in q['profiles']}
        audit = json.loads(SOURCE_AUDIT.read_text()); assert audit['status'] == 'reviewed'
        mandel = json.loads(MANDEL.read_text())
        pins = preparation.merge(pins, audit['pins'], mandel['pins'],
                                 {str(SOURCE_AUDIT): args.source_audit_sha256, str(MANDEL): args.mandelbrot_manifest_sha256})
        rows = []
        for row in q['profiles']:
            assert reviewed[row['id']]['source'] == row['source'] and reviewed[row['id']]['source_sha256'] == row['source_sha256']
            assert 1 <= row['maximum_compute_actors'] <= 8
            assert row['command'][1:] == ['{n}', '--ponymaxthreads', '8']
            assert preparation.sha(row['source']) == row['source_sha256'] and preparation.sha(row['command'][0]) == row['binary_sha256']
            counted = loc['profiles'][row['id']]
            inputs = loc['compiler_bound_input_inventory'][row['id']]
            assert counted['source'] == row['source'] and counted['source_sha256'] == row['source_sha256']
            assert inputs['source_sha256'] == row['source_sha256'] and inputs['binary_sha256'] == row['binary_sha256']
            assert (counted['benchmark'], counted['variant']) == (row['benchmark'], row['variant'])
            assert all(type(counted[field]) is int and counted[field] > 0 for field in ('physical_loc','canonical_loc'))
            assert [(item['path'],item['sha256']) for item in counted['source_bundle']] == [(item['path'],item['sha256']) for item in inputs['files']]
            assert counted['canonical_loc'] == sum(item['normalized_loc'] for item in counted['source_bundle'])
            assert counted['physical_loc'] == sum(item['physical_loc'] for item in counted['source_bundle'])
            rows.append(dict(row, binary=row['command'][0], loc=counted['canonical_loc'], physical_loc=counted['physical_loc'],
                source_bundle=copy.deepcopy(counted['source_bundle']), canonical_source_evidence=dict(path=str(LOC),sha256=LOC_SHA),
                compiler_bound_input_inventory=copy.deepcopy(inputs), role='unchanged qualified Pony ' + row['variant'],
                execution_mode='native-aot', profile=row['variant'], source_profile=row['variant'],
                qualification_status='complete-bounded-output-production-work-and-canonical-LOC',
                measurement_status='pending', samples_seconds=[], sample_validation=[], attempts=[]))
        for benchmark in harness.BENCHES:
            if benchmark == 'mandelbrot':
                control = copy.deepcopy(next(row for row in mandel['profiles'] if row['id'] == 'row16-aot-control'))
            else:
                control = copy.deepcopy(next(row for row in audit['controls'] if row['benchmark'] == benchmark))
            assert preparation.sha(control['source']) == control['source_sha256'] and preparation.sha(control['binary']) == control['binary_sha256']
            pins[control['source']] = control['source_sha256']; pins[control['binary']] = control['binary_sha256']
            control.update(id='mech-' + benchmark + '-control', key=benchmark + ':pony-full:mech-control', role='unchanged reviewed Mech control with fresh three canonical processes', measurement_status='pending', samples_seconds=[], sample_validation=[], attempts=[])
            rows.append(control)
        assert len(rows) == 30
        output.mkdir(parents=True)
        common = dict(pins=pins, status='prepared-awaiting-root-review', samples=3, canonical_full_workload=True,
                      shared_timing_lock=str(LOCK), timeout_seconds=14400, maximum_rss_mib=10240,
                      maximum_compute_workers=8, required_power_profile=harness.REQUIRED,
                      qualification=str(report_path), qualification_sha256=preparation.sha(report_path),
                      source_work_qualification=str(work_path), source_work_qualification_sha256=preparation.sha(work_path),
                      tree_allocation_prerequisite=tree_gate,
                      source_metric='Whole authored Pony bundles from exact qualified canonical LOC overlay5831; original producer LOC/null/diagnostics retained in source evidence.',
                      canonical_source_evidence=dict(path=str(LOC),sha256=LOC_SHA), canonical_source_closed_review=dict(path=str(LOC_ROOT),sha256=LOC_ROOT_SHA),
                      original_full_pipeline=dict(path=str(PRIOR/'full_study.py'),sha256=PRIOR_FULL_SHA),
                      full_failure_fixtures=dict(path=str(FULL_FIXTURES),sha256=FULL_FIXTURES_SHA,reused=3,reexecuted=0),
                      original_work_fixture_tests_reused=14, fixture_reexecutions=0, bounded_reexecutions=0, trace_reexecutions=0,
                      original_host_artifacts_preserved=True, output_repository=str(REPOSITORY),
                      runtime_publication_metadata_qualified=False, live_dataset_mutations=0, chart_admission=False,
                      timing_boundary='Fresh process runtime/input/all workload/output/shutdown plus identical authoritative PGID registration. Compiler/source review/validation/hash outside elapsed.',
                      ownership='Frozen separate sampler and native process inherit held common mutex, authoritative PGID registration, full cleanup before release.',
                      retry_policy='Every failure preserved. Confirmed source output/time/RSS failure marks that exact profile failed and independent sources continue. Environment/pin/process/ownership failure stops controller. No automatic resumption/retry; corrected source requires new reviewed study.',
                      full_performance_runs_required=90, chart_policy='Publication requires all ten workloads, three recorded samples per program, and a fresh Mech control per benchmark.')
        manifests = {}
        for benchmark in harness.BENCHES:
            profiles = [row for row in rows if row['benchmark'] == benchmark]
            assert len(profiles) == 3
            identifiers = [row['id'] for row in profiles]
            orders = [dict(round=index + 1, profiles=identifiers[index:] + identifiers[:index]) for index in range(3)]
            manifest = dict(common, benchmark=benchmark, size=harness.WORK[benchmark][1], profiles=profiles, orders=orders,
                            full_output_reference=full_reference(harness, benchmark), required_processes=9)
            path = output / benchmark / 'manifest.json'
            preparation.new_json(path, manifest)
            manifests[benchmark] = dict(path=str(path), sha256=preparation.sha(path))
        guard.verify(pins)
        suite = dict(common, benchmark_order=harness.BENCHES, benchmarks=manifests, profiles=rows)
        preparation.new_json(output / 'manifest.json', suite)
        print(json.dumps(dict(manifest=str(output / 'manifest.json'), sha256=preparation.sha(output / 'manifest.json'), benchmarks=manifests), indent=2), flush=True)


def isolated_profile_failure(guard, attempt):
    """Require literal clean ownership gates before isolating a real source failure."""
    safe = ('sampler_exited_normally', 'authoritative_native_group_received', 'native_inherited_common_mutex',
            'no_wrapper_integrity_error', 'no_resource_monitor_errors', 'no_compiler_power_monitor_errors',
            'no_monitor_finish_error', 'no_execute_cleanup_error', 'no_remaining_execute_group',
            'no_supervisor_cleanup', 'no_supervisor_remaining_group', 'valid_environment',
            'actual_full_workload', 'exact_command_and_group', 'pins_unchanged')
    checks = attempt.get('qualification_checks', {})
    return guard.benchmark_failure(attempt) and all(checks.get(key) is True for key in safe)


def run(args):
    revision, digest = args.revision, args.manifest_sha256
    output = COHORT / 'full-studies' / revision
    with (output / 'owner.lock').open('a+') as owner:
        fcntl.flock(owner, fcntl.LOCK_EX | fcntl.LOCK_NB)
        report_path = output / 'report.json'
        assert not report_path.exists(), 'Existing report requires new explicit recovery review'
        with LOCK.open('r+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            common_identity(lock)
            _, _, _, guard, harness, prerequisite_pins, _ = prerequisites(args)
            harness.install_interrupt_handlers()
            assert preparation.sha(output / 'manifest.json') == digest
            suite = json.loads((output / 'manifest.json').read_text())
            assert all(suite['pins'].get(path) == expected for path,expected in prerequisite_pins.items())
            assert suite['status'] == 'prepared-awaiting-root-review' and suite['samples'] == 3 and suite['full_performance_runs_required'] == 90
            assert len(suite['profiles']) == len({row['id'] for row in suite['profiles']}) == 30
            assert suite['output_repository'] == str(REPOSITORY) and suite['chart_admission'] is False
            approved = read(args.approved_manifest_review, args.approved_manifest_review_sha256, prerequisite_pins)
            assert approved['status'] == 'root-reviewed-exact-Pony20-Mech10-full90-manifests'
            assert approved['manifest'] == str(output/'manifest.json') and approved['manifest_sha256'] == digest
            assert approved['benchmark_manifests'] == suite['benchmarks']
            assert approved['worker_sha256'] == args.worker_sha256 and approved['review_sha256'] == args.review_sha256
            assert (approved['pony_profiles'],approved['mech_controls'],approved['samples_per_profile'],approved['native_full_processes']) == (20,10,3,90)
            assert approved['extra_native_validation_processes'] == approved['fixture_reexecutions'] == approved['trace_reexecutions'] == 0
            assert approved['chart_admission'] is False and approved['original_host_paths_preserved'] is True
            guard.verify(suite['pins'])
        with LOCK.open('r+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX); common_identity(lock)
            report = dict(status='running', manifest=str(output / 'manifest.json'), manifest_sha256=digest,
                          sample_count=3, programs={row['key']: copy.deepcopy(row) for row in suite['profiles']},
                          attempts=[], active=None, completed_benchmarks=[], benchmark_order=suite['benchmark_order'],
                          full_performance_runs=0, source_metric=suite['source_metric'], source_work_qualification=suite['source_work_qualification'],
                          pins=suite['pins'], maximum_rss_mib=suite['maximum_rss_mib'], shared_timing_lock=str(LOCK))
            guard.OUT = output; guard.REPORT = report_path
            guard.save(report_path, report)
        try:
            for benchmark in suite['benchmark_order']:
                declared = suite['benchmarks'][benchmark]
                with LOCK.open('r+') as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX)
                    common_identity(lock)
                    assert preparation.sha(declared['path']) == declared['sha256']
                    manifest = json.loads(Path(declared['path']).read_text())
                    guard.verify(manifest['pins'])
                rows = {row['id']: report['programs'][row['key']] for row in manifest['profiles']}
                for order in manifest['orders']:
                    for identifier in order['profiles']:
                        row = rows[identifier]
                        if row.get('full_failure'):
                            continue
                        with LOCK.open('r+') as lock:
                            fcntl.flock(lock, fcntl.LOCK_EX)
                            common_identity(lock)
                            harness.compact.wait_for_environment(harness.REQUIRED)
                            guard.verify(manifest['pins'])
                            print('FULL PONY', benchmark, order['round'], identifier, manifest['size'], flush=True)
                            attempt = guard.one_attempt(harness, row, manifest, report, order['round'], lock.fileno())
                            report['attempts'].append(attempt); report['active'] = None
                            row['attempts'].append(attempt['attempt'])
                            report['full_performance_runs'] += 1
                            if attempt['qualified']:
                                row['samples_seconds'].append(attempt['seconds']); row['sample_validation'].append(attempt['validation'])
                                row.setdefault('full_validation', attempt['validation'])
                                row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
                            elif isolated_profile_failure(guard, attempt):
                                row['measurement_status'] = 'failed'
                                row['full_failure'] = dict(attempt)
                                print('CONFIRMED SOURCE FAILURE', benchmark, identifier, attempt.get('error'), flush=True)
                            else:
                                row['measurement_status'] = 'failed-qualification'
                            guard.save(report_path, report)
                            if not attempt['qualified'] and not row.get('full_failure'):
                                raise AssertionError(('Full integrity/environment/ownership failure retained; controller stops', benchmark, identifier, attempt.get('error')))
                with LOCK.open('r+') as lock:
                    fcntl.flock(lock, fcntl.LOCK_EX); common_identity(lock)
                    assert all(len(row['samples_seconds']) == 3 or row.get('full_failure') for row in rows.values())
                    for row in rows.values():
                        if not row.get('full_failure'):
                            row['median_seconds'] = statistics.median(row['samples_seconds']); row['sample_stdev_seconds'] = statistics.stdev(row['samples_seconds'])
                            row['qualification_status'] = 'three-canonical-processes-qualified-awaiting-independent-suite-and-runtime-publication-review'
                    report['completed_benchmarks'].append(benchmark); guard.save(report_path, report)
            with LOCK.open('r+') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX); common_identity(lock); guard.verify(suite['pins'])
                assert len(report['attempts']) == report['full_performance_runs']
                assert len(report['attempts']) == sum(len(row['samples_seconds']) + bool(row.get('full_failure')) for row in report['programs'].values())
                assert len(report['completed_benchmarks']) == 10
                assert all(len(row['samples_seconds']) == 3 or row.get('full_failure') for row in report['programs'].values())
                failed = [row['id'] for row in report['programs'].values() if row.get('full_failure')]
                if not failed:
                    assert len(report['attempts']) == 90
                report.update(status='complete-with-failures' if failed else 'complete', pins_unchanged_at_end=True, correctable_source_failures=failed, goal_complete=False if failed else None)
        except BaseException as error:
            report.update(status='stopped', error=str(error) or type(error).__name__, error_type=type(error).__name__)
            raise
        finally:
            with LOCK.open('r+') as lock:
                fcntl.flock(lock, fcntl.LOCK_EX); common_identity(lock)
                guard.save(report_path, report)
                available, integrity_errors = {}, []
                for path, expected in prerequisite_pins.items():
                    try: assert file_digest(path) == expected
                    except BaseException as error: integrity_errors.append(dict(path=path,error=str(error) or type(error).__name__))
                for path, expected in suite['pins'].items():
                    try: assert file_digest(path) == expected
                    except BaseException as error: integrity_errors.append(dict(path=path,error=str(error) or type(error).__name__))
                for path in output.rglob('*'):
                    if path.is_file() and path.name != 'owner.lock':
                        try: available[str(path)] = file_digest(path)
                        except BaseException as error: integrity_errors.append(dict(path=str(path),error=str(error) or type(error).__name__))
                preparation.new_json(output/'terminal.json',dict(status='failed-terminal-integrity' if integrity_errors else report['status'],
                    report=str(report_path),report_sha256=file_digest(report_path),full_performance_runs=report['full_performance_runs'],
                    prerequisite_pins=preparation.merge(suite['pins'],prerequisite_pins),available_evidence_pins=available,integrity_errors=integrity_errors,
                    common_mutex_held=True,original_host_artifacts_preserved=True,output_repository=str(REPOSITORY),
                    fixture_reexecutions=0,trace_reexecutions=0,bounded_reexecutions=0,compiler_invocations=0,live_dataset_mutations=0,chart_admission=False))
                if integrity_errors: raise RuntimeError('Full Pony terminal integrity failed; actual partial evidence retained')


def main():
    parser = argparse.ArgumentParser(); modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--seal', action='store_true'); modes.add_argument('--run', action='store_true')
    parser.add_argument('--revision', required=True)
    for name in ('worker','review','source-audit','mandelbrot-manifest'): parser.add_argument('--'+name+'-sha256', required=True)
    parser.add_argument('--manifest-sha256'); parser.add_argument('--approved-manifest-review',type=Path)
    parser.add_argument('--approved-manifest-review-sha256')
    args = parser.parse_args(); assert args.revision == 'pony-retained20-full-v1'
    assert sys.dont_write_bytecode and Path(sys.executable).resolve() == PYTHON.resolve()
    assert REPOSITORY == Path('/Users/cim310/mech-lang/benchmarks')
    for key,value in vars(args).items():
        if key.endswith('_sha256') and value is not None: assert len(value)==64 and all(c in '0123456789abcdef' for c in value)
    with ExitStack() as leases:
        for path in (HOST_CLBG/'continuation/owned-jobs/pony-reviewed-work-metadata-v1/owner.lock',LOC_OWNER/'owner.lock'):
            lease = leases.enter_context(path.open('rb')); fcntl.flock(lease,fcntl.LOCK_SH|fcntl.LOCK_NB)
            opened,named=os.fstat(lease.fileno()),path.stat(); assert (opened.st_dev,opened.st_ino)==(named.st_dev,named.st_ino)
        if args.seal:
            assert args.manifest_sha256 is args.approved_manifest_review is args.approved_manifest_review_sha256 is None
            seal(args)
        else:
            assert args.manifest_sha256 and args.approved_manifest_review and args.approved_manifest_review_sha256
            assert args.approved_manifest_review.is_absolute() and not args.approved_manifest_review.stat().st_mode & 0o222
            run(args)

if __name__ == '__main__': main()
