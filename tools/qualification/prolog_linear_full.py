"""Add 81 full processes to nine preserved Prolog regex-redux samples.

Only the cancelled quadratic reverse-complement implementation is replaced.
Preparation and execution verify closed evidence under the existing mutex;
execution keeps that mutex for the entire fresh, non-retrying continuation.
The original sampler, resource limits and ownership supervisor are unchanged.
"""
import argparse
import copy
from contextlib import contextmanager, ExitStack
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
PACKET = ROOT / 'experiments/prolog/full81-linear-v1'
OLD = ROOT / 'experiments/prolog/full90-v1'
LINEAR = ROOT / 'experiments/prolog/revcomp-linear-v1'
FULL_SHA = '0d75d33bb77d3715ca7adcd8c07fcf3b659be472c2ef84c063dec57ee4b8eb94'
RECONCILE_SHA = 'a69b498cc0664b2951c1ef5ef2281f06f34e6415fcf6adfe8b723f06ca127cfe'
LOC_SHA = 'e135716a6f4f2778e06d222e5351c16944cb34d68dc067041772f86b907d74ef'
SUPERVISOR_SHA = '5458bdf5e58465cb21156a2140657066b4706aa2a0941fe3efde8758207574b4'
SOURCE_SHA = 'bb4826e39721c6e4e61330ee3f56db604e1d48498c32fdd9453b133e35508322'
QLF_SHA = 'c4526a2d463d5c9c570e88b5ab68237ecf61244d104825ab1e4fbb66b13c1f9e'
WORK_SHA = '2225c08c30bf3e5aa518c57d96d6e6ffd9596c50e7858abfde96dab03ca7c1ae'
COUNT_SHA = '808f8d4f98d2826925a27b34f4116e5a84d454cc7cb0d55935c0af7a9b4e9677'
SCHEMA = 'prolog-linear-continuation81-v1'
FIXED = {
    OLD/'plan.json': '55c09837581e1ed1ff0d317ec86155733962d68122338a353d3b0dce4fa8db6a',
    OLD/'results/report.json': '88e9dad8e6ed707f8794c62ba081c10a0ffc75f2b2d7208db58489abe2f657b0',
    OLD/'results/terminal.json': 'afc0be094e361a5240b8ccf23f1f5f1ab8e82db219aa7a8684091c567c863908',
    OLD/'owned-jobs/full90/terminal.json': '82241a16edf0874e80dad2aadb37c6d3e5b67e37e50a48ac37d070e883d4c229',
    OLD/'cancellation-v1.json': 'bd60e5b703fde262392e039780c93ba1bc4ad3ee20fb49356ce2182f6aa4dd0a',
    OLD/'cancellation-review-v1.json': 'd1ada9b81eaeba324fed6a20e2eacde7bfe755b1f845c56fff3b36cd05ffd2c9',
    LINEAR/'source-counts-v1/plan-v1.json': 'cf930c86bfdef0a67d26dac59004145cfa31e213c0b488fe0ac3dc0c3a31166f',
    LINEAR/'source-counts-v1/run-v1/report.json': '5f78980dce62e2b4971ac49b21ad2f42465c703d80edc176f96cb3be238e5c3a',
    LINEAR/'source-counts-v1/run-v1/terminal.json': '480786857754dc6077baab4f23e52462de4947779744657aae75843b0b76da88',
    OLD/'owned-jobs/revcomp-linear-source-counts9-v1/terminal.json': 'e8de58e22d2d47d03cdd7f47a032931e2f0cfab3224551c9b3854a7aa519e0b9',
    LINEAR/'source-counts-v1/run-v1/candidate-original-source/projection.json': '7c42ea94e407bdd62778960292e305e95f51bb5df6067862ee83cb4925f006c5',
    LINEAR/'source-counts-v1/source-count-review.json': COUNT_SHA,
    LINEAR/'compiled-work-review.md': WORK_SHA,
    LINEAR/'candidate.pl': SOURCE_SHA,
    LINEAR/'bounded-run-v1/authored/candidate.pl': SOURCE_SHA,
    LINEAR/'bounded-run-v1/authored/candidate.qlf': QLF_SHA,
}


def require(value, message):
    if not value:
        raise AssertionError(message)


def load(path, digest, name):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'Frozen controller changed: '+str(path))
    module = types.ModuleType(name)
    module.__file__ = str(path)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


# Imports inspect only these small, pinned Python definitions. Runtime closure
# verification and the sampler loader are called solely while holding the lock.
f = load(ROOT/'tools/qualification/prolog_full.py', FULL_SHA, 'linear_full_frozen')
r = load(ROOT/'tools/qualification/prolog_reconcile.py', RECONCILE_SHA, 'linear_full_reconcile')
sha, merge = f.sha, f.merge


def bind(pins, path, digest):
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts and path.resolve() == path,
            'Noncanonical evidence path: '+str(path))
    require(str(path) not in pins or pins[str(path)] == digest, 'Conflicting evidence pin')
    require(sha(path) == digest, 'Pinned bytes changed: '+str(path))
    pins[str(path)] = digest
    return path


def read(pins, path, digest=None):
    path = Path(path)
    expected = FIXED[path] if digest is None else digest
    raw = bind(pins, path, expected).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, 'Evidence changed during read')
    return json.loads(raw)


def file_inventory(directory, exclude=()):
    result = {}
    for path in sorted(directory.rglob('*')):
        require(not path.is_symlink(), 'Symlink in receipt directory')
        if path.is_file() and path.relative_to(directory).as_posix() not in exclude:
            result[str(path)] = sha(path)
        else:
            require(path.is_dir() or path.is_file(), 'Nonregular receipt artifact')
    return result


@contextmanager
def owned_locks():
    # The old durable lease and suite lease prove that the cancelled owner has
    # released ownership. Opening existing files never recreates a missing lease.
    with ExitStack() as stack:
        for path, inode in ((OLD/'owned-jobs/full90/owner.lock', 81764070),
                (ROOT/'experiments/prolog/prolog-full90.owner.lock', 81764078)):
            lease = stack.enter_context(path.open('rb'))
            fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
            held, named = os.fstat(lease.fileno()), path.stat()
            require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino)
                    and held.st_ino == inode, 'Original owner lease changed')
        lock = stack.enter_context(f.common_lock())
        f.checked_runtime()
        yield lock


def retained_checks(plan, report, terminal, durable, cancellation, closure):
    slots, profiles = r.schedule(plan)
    require(report['status'] == terminal['status'] == 'stopped-unqualified'
            and report['active'] is None and len(report['attempts']) == 10
            and report['qualified_samples'] == terminal['qualified_samples'] == 9
            and report['completed_benchmarks'] == ['regexredux'], 'Wrong cancelled study boundary')
    require(report['plan'] == str(OLD/'plan.json') and report['plan_sha256'] == FIXED[OLD/'plan.json']
            and terminal['report'] == str(OLD/'results/report.json')
            and terminal['report_sha256'] == FIXED[OLD/'results/report.json'], 'Old report linkage differs')
    require(report['supervisor']['pid'] == durable['command_pid'] == cancellation['controller_pid'] == 83209
            and durable['command_identity']['pid'] == 83209 and durable['actual_command_started'] is True
            and durable['status'] == 'command-failed' and durable['exit_code'] == -2
            and durable['qualification_granted'] is durable['automatic_retry'] is False
            and durable['command_identity_observation_missing'] is False, 'Old durable stop differs')
    command = [str(f.PYTHON), '-I', '-S', '-B', '-u', str(ROOT/'tools/qualification/prolog_full.py'),
               'run', '--plan', str(OLD/'plan.json'), '--plan-sha256', FIXED[OLD/'plan.json']]
    require(durable['command_identity']['listing'].endswith(' '.join(command)), 'Old durable command differs')
    require(report['pins_unchanged_at_end'] is terminal['common_mutex_held'] is True
            and terminal['integrity_errors'] == [] and report['error_type'] == 'KeyboardInterrupt',
            'Cancelled producer did not close its pin/lock state')
    require(terminal['prerequisite_pins'] == merge(plan['pins'], {str(OLD/'plan.json'): FIXED[OLD/'plan.json']}),
            'Cancelled terminal prerequisite closure differs')
    for value in (report, terminal):
        require(value['registered_native_attempts'] == list(range(1, 11))
                and value['native_launch_unconfirmed_attempts'] == [] and value['saved_attempts'] == 10
                and value['full_performance_runs'] == 10 and value['chart_admission'] is False,
                'Cancelled native accounting differs')
    require(closure['status'] == 'owned-cancellation-closed-no-measurement-admission'
            and closure['preserved_completed_attempt_files'] == 27 and closure['preserved_completed_samples'] == 9
            and closure['interrupted_attempt'] == 10 and closure['owned_sampler_reaped'] is True
            and closure['cleanup_errors'] == closure['remaining_owned_processes_or_groups'] == []
            and closure['deadline_expired'] is closure['measurement_qualification'] is closure['chart_admission'] is False,
            'Cancellation closure is not the reviewed deliberate stop')
    require(cancellation['attempt'] == 10 and cancellation['signal'] == 15
            and cancellation['cancellation_is_timeout'] is cancellation['cancellation_is_timing'] is False
            and cancellation['automatic_retry'] is False, 'Cancellation was relabeled as a measurement')
    require(report['attempts'][9]['qualified'] is False and report['attempts'][9]['wrapper_supervisor_failure'] is True
            and report['attempts'][9]['id'] == 'prolog-revcomp-compact', 'Interrupted attempt changed')
    return slots, profiles


def old_prerequisite(pins):
    plan, report, terminal, durable, cancellation, closure = [read(pins, path) for path in (
        OLD/'plan.json', OLD/'results/report.json', OLD/'results/terminal.json',
        OLD/'owned-jobs/full90/terminal.json', OLD/'cancellation-v1.json', OLD/'cancellation-review-v1.json')]
    slots, profiles = retained_checks(plan, report, terminal, durable, cancellation, closure)
    pins.update(merge(pins, plan['pins']))
    for path, digest in closure['evidence_sha256'].items():
        bind(pins, path, digest)
    actual = file_inventory(OLD/'results', exclude=('terminal.json',))
    require(actual == terminal['available_evidence_pins'], 'Cancelled artifact inventory changed')
    pins.update(merge(pins, actual))
    preserved, reused, provenance, gaps = {}, [], [], []
    derived = {key: [] for key in profiles if key.startswith('regexredux:')}
    for index, slot in enumerate(slots[:9], 1):
        attempt = report['attempts'][index-1]
        require(attempt['attempt'] == index and attempt['qualified'] is True, 'Missing retained successful sample')
        paths = [OLD/'results/attempts'/f'{index:03d}-{slot[2]}{suffix}'
                 for suffix in ('.json', '.supervisor.json')]
        outer_path = OLD/'results/outer-supervisor'/f'{index:03d}-{slot[2]}.json'
        values = [json.loads(path.read_bytes()) for path in (*paths, outer_path)]
        r.check_attempt(attempt, values[0], values[1], slot, profiles[slot[3]],
                        plan['manifests'][slot[0]], fingerprint_pins(plan, terminal['prerequisite_pins']), provenance)
        gaps.extend(r.check_outer(values[2], attempt, 83209))
        require(attempt['result_path'] == str(paths[0]) and attempt['supervisor_result_path'] == str(paths[1]),
                'Retained sample receipt paths differ')
        for path in (*paths, outer_path):
            preserved[str(path.relative_to(OLD))] = actual[str(path)]
        derived[slot[3]].append(attempt['seconds'])
        reused.append(dict(slot=slot, original_attempt=index, raw=str(paths[0]), raw_sha256=actual[str(paths[0])],
            supervised=str(paths[1]), supervised_sha256=actual[str(paths[1])], outer=str(outer_path),
            outer_sha256=actual[str(outer_path)], seconds=attempt['seconds'], validation=attempt['validation']))
    require(preserved == cancellation['preserved_completed_attempt_files'] and len(preserved) == 27,
            'The 27 preserved receipts differ')
    require(derived == cancellation['preserved_completed_samples']
            and all(derived[key] == report['programs'][key]['samples_seconds'] for key in derived),
            'Retained regex sample summary differs')
    return plan, dict(plan=str(OLD/'plan.json'), plan_sha256=FIXED[OLD/'plan.json'],
        report=str(OLD/'results/report.json'), report_sha256=FIXED[OLD/'results/report.json'],
        cancellation_review=str(OLD/'cancellation-review-v1.json'),
        cancellation_review_sha256=FIXED[OLD/'cancellation-review-v1.json'],
        reused_samples=reused, excluded_original_attempt=10, reused_native_processes=9,
        descriptive_provenance=provenance, kernel_identity_observation_gaps=gaps)


def count_review_checks(review, projection):
    require(review['schema'] == 'prolog-linear-canonical-owner-review-v1'
            and review['status'] == 'candidate-canonical-source-count-qualified'
            and review['canonical_LOC_admitted'] is True and review['canonical_loc'] == 242
            and review['physical_loc'] == 146 and review['formatted_loc'] is None
            and review['source_sha256'] == SOURCE_SHA and review['predicate_count'] == 22
            and review['owner_events'] == 253 and review['native_source_reader_processes_replayed'] == 9
            and review['fixture_projections_replayed'] == 7 and review['candidate_projections_replayed'] == 1
            and review['all_owner_source_slices_and_utf8_offsets_verified'] is True
            and review['all_candidate_owners_manually_reviewed'] is True
            and review['original_producer_receipts_unchanged'] is True
            and review['benchmark_samples'] == 0 and review['chart_admission'] is False,
            'Canonical owner review differs')
    metric = projection['projection']
    require(metric['normalized_loc'] == 242 and metric['physical_loc'] == 146
            and metric['diagnostics'] == [] and len(metric['canonical_events']) == 253
            and projection['source_sha256'] == SOURCE_SHA
            and projection['exact_original_and_compiled_bytes_equal'] is True
            and len(projection['compiled_predicate_inventory']) == 22
            and projection['canonical_LOC_admitted'] is projection['source_work_qualified'] is
                projection['chart_admission'] is False, 'Original candidate projection differs')


def linear_prerequisite(pins):
    loc = load(ROOT/'tools/qualification/prolog_revcomp_loc.py', LOC_SHA, 'linear_full_source_proof')
    plan = read(pins, LINEAR/'source-counts-v1/plan-v1.json')
    loc.validate_plan(plan)
    prior = plan['prerequisite']
    args = types.SimpleNamespace(bounded_report=Path(prior['report']), bounded_report_sha256=prior['report_sha256'],
        bounded_terminal_sha256=prior['terminal_sha256'], bounded_durable=Path(prior['durable']),
        bounded_durable_sha256=prior['durable_sha256'])
    require(loc.bounded_prerequisite(args, pins) == prior, 'Closed 542-process prerequisite differs')
    for path, digest in plan['pins'].items():
        bind(pins, path, digest)
    report = read(pins, LINEAR/'source-counts-v1/run-v1/report.json')
    terminal = read(pins, LINEAR/'source-counts-v1/run-v1/terminal.json')
    durable = read(pins, OLD/'owned-jobs/revcomp-linear-source-counts9-v1/terminal.json')
    directory = Path(plan['output'])
    require(report['status'] == terminal['status'] == loc.COMPLETE
            and report['plan'] == str(LINEAR/'source-counts-v1/plan-v1.json')
            and report['plan_sha256'] == FIXED[LINEAR/'source-counts-v1/plan-v1.json']
            and terminal['report_sha256'] == FIXED[LINEAR/'source-counts-v1/run-v1/report.json']
            and report['prerequisite'] == prior and report['active'] is None
            and report['native_processes_started'] == terminal['native_processes_started'] == 9,
            'Nine source readers are not closed')
    require(report['native_receipt_errors'] == report['integrity_errors'] == terminal['native_receipt_errors'] ==
            terminal['integrity_errors'] == terminal['artifact_errors'] == []
            and terminal['common_mutex_held'] is True and terminal['common_mutex_inode'] == 79859134,
            'Source reader closure has errors')
    require(durable['status'] == 'command-exited-zero-awaiting-report-review' and durable['exit_code'] == 0
            and durable['actual_command_started'] is True and durable['command_pid'] == 59675
            and durable['command_identity']['pid'] == 59675 and durable['stop_signals'] == []
            and durable['command_identity_observation_missing'] is False and durable['qualification_granted'] is False,
            'Source reader durable owner differs')
    command = [str(f.PYTHON), '-I', '-S', '-B', str(ROOT/'tools/qualification/prolog_revcomp_loc.py'),
        'run', '--plan', report['plan'], '--plan-sha256', report['plan_sha256']]
    require(durable['command_identity']['listing'].endswith(' '.join(command)), 'Source reader command differs')
    loc.closed_artifacts(directory, terminal, pins)
    require([entry['id'] for entry in report['commands']] == [row['id'] for row in plan['schedule']]
            and len({entry['pid'] for entry in report['commands']}) == 9, 'Source reader command inventory differs')
    for row, entry in zip(plan['schedule'], report['commands']):
        require(entry['argv'] == row['argv'] and entry['status'] == 'reader-validated', 'Unvalidated source reader')
        loc.saved_receipt(directory/row['id'], row['argv'], prior['environment'], b'', entry['pid'], 59675)
        require(entry['process_sha256'] == sha(directory/row['id']/'process.json'), 'Source reader receipt differs')
    require(len(report['projections']) == 8, 'Incomplete source projections')
    for entry in report['projections']:
        require(sha(directory/entry['id']/'projection.json') == entry['projection_sha256'], 'Projection linkage differs')
    review = read(pins, LINEAR/'source-counts-v1/source-count-review.json')
    projection = read(pins, directory/'candidate-original-source/projection.json')
    count_review_checks(review, projection)
    for relative, digest in review['pins'].items():
        path = Path(relative)
        require(not path.is_absolute() and '..' not in path.parts, 'Nonrepository owner-review reference')
        bind(pins, ROOT/path, digest)
    for path in (LINEAR/'compiled-work-review.md', LINEAR/'candidate.pl',
                 LINEAR/'bounded-run-v1/authored/candidate.pl', LINEAR/'bounded-run-v1/authored/candidate.qlf'):
        bind(pins, path, FIXED[path])
    require(prior['compiled_qlf']['sha256'] == QLF_SHA and prior['compiler_source_sha256'] == SOURCE_SHA,
            'Reviewed source/QLF identity differs')
    return dict(bounded=prior, source_plan=str(LINEAR/'source-counts-v1/plan-v1.json'),
        source_plan_sha256=FIXED[LINEAR/'source-counts-v1/plan-v1.json'],
        source_count_review=dict(path=str(LINEAR/'source-counts-v1/source-count-review.json'), sha256=COUNT_SHA),
        projection=dict(path=str(directory/'candidate-original-source/projection.json'),
                        sha256=FIXED[directory/'candidate-original-source/projection.json']),
        required_work_review=dict(path=str(LINEAR/'compiled-work-review.md'), sha256=WORK_SHA, status='passed'),
        canonical_loc=242, physical_loc=146, source_work_qualified=True, canonical_LOC_admitted=True,
        measured_runtime_scaling_qualified=False, full_timings_qualified=False, chart_admission=False)


def manifests_for(old_plan, linear):
    manifests = copy.deepcopy(old_plan['manifests'])
    prior = linear['bounded']
    source = str(LINEAR/'candidate.pl')
    for offset, variant in enumerate(('compact', 'optimized')):
        identifier = 'prolog-revcomp-linear-'+variant
        old = old_plan['manifests']['revcomp']['profiles'][offset]
        require(prior['binary'] == old['binary'] and prior['environment'] == old['runtime_environment'],
                'Linear candidate changed the retained runtime')
        row = dict(id=identifier, key='revcomp:'+identifier, benchmark='revcomp', language='prolog',
            source=source, source_sha256=SOURCE_SHA, binary=old['binary'], binary_sha256=old['binary_sha256'],
            command=[old['binary'], '-q', '-O', '-f', 'none', '--stack-limit=8g', '-s',
                     prior['compiled_qlf']['path'], '-g', 'clbg_revcomp_linear:run'],
            cwd=str(Path(prior['compiler_source']).parent), runtime_environment=copy.deepcopy(prior['environment']),
            variant=variant, maximum_workers=1, source_alias_of='prolog-revcomp-linear-compact' if offset else None,
            optimization_claim=('explicit equivalent-source alias; no distinct optimization admitted' if offset else
                                'bounded-chunk full-record reverse-complement; source-linear traversal'),
            measured_source=prior['compiler_source'], loc=242, canonical_loc=242, physical_loc=146,
            source_bundle=[dict(path=prior['compiler_source'], origin=source, sha256=SOURCE_SHA,
                                normalized_loc=242, physical_loc=146)],
            compiled_artifact=copy.deepcopy(prior['compiled_qlf']),
            compiler_bound_input_inventory=dict(path=str(LINEAR/'bounded-run-v1/inspect/loaded-inputs.json'),
                sha256='54891639e089420313cf51823b24ce5dfa70f4c69497feecacc0a2967808e764',
                status='qualified-exact-authored-compiler-inputs'),
            required_work_review=copy.deepcopy(linear['required_work_review']),
            source_count_review=copy.deepcopy(linear['source_count_review']),
            canonical_source_projection=copy.deepcopy(linear['projection']),
            memory_policy=old['memory_policy'], execution_mode=old['execution_mode'],
            eligible_for_chart=False, chart_admission=False)
        manifests['revcomp']['profiles'][offset] = row
    ids = [row['id'] for row in manifests['revcomp']['profiles']]
    manifests['revcomp']['orders'] = [dict(round=i+1, profiles=ids[i:]+ids[:i]) for i in range(3)]
    return manifests


def schedule_for(manifests):
    require(set(manifests) == set(f.BENCHES), 'Wrong continuation workload inventory')
    slots = []
    for bench in f.BENCHES:
        rows = manifests[bench]['profiles']
        prefix = 'prolog-revcomp-linear' if bench == 'revcomp' else 'prolog-'+bench
        ids = [prefix+'-compact', prefix+'-optimized', 'mech-aot-control']
        require([row['id'] for row in rows] == ids and [row['language'] for row in rows] == ['prolog','prolog','mech'],
                'Wrong continuation profiles')
        orders = [dict(round=i+1, profiles=ids[i:]+ids[:i]) for i in range(3)]
        require(manifests[bench]['orders'] == orders, 'Continuation rotation changed')
        keys = {row['id']: row['key'] for row in rows}
        slots.extend([bench, order['round'], name, keys[name]] for order in orders for name in order['profiles'])
    require(len(slots) == len({tuple(slot) for slot in slots}) == 90, 'Duplicate/incomplete continuation schedule')
    require(all(slot[0] == 'regexredux' for slot in slots[:9]) and len(slots[9:]) == 81,
            'Retained/new schedule boundary changed')
    return slots


def own_pins():
    return {str(path): digest for path, digest in (
        (Path(__file__).resolve(), sha(__file__)), (ROOT/'tools/qualification/prolog_full.py', FULL_SHA),
        (ROOT/'tools/qualification/prolog_reconcile.py', RECONCILE_SHA), (r.HELPER, r.HELPER_SHA),
        (ROOT/'tools/qualification/prolog_revcomp_loc.py', LOC_SHA), (f.SUPERVISOR, SUPERVISOR_SHA),
        (f.PYTHON.resolve(), f.PYTHON_SHA))}


def build_plan(output):
    pins = own_pins()
    old_plan, retained = old_prerequisite(pins)
    linear = linear_prerequisite(pins)
    manifests = manifests_for(old_plan, linear)
    slots = schedule_for(manifests)
    require(slots[:9] == old_plan['schedule'][:9], 'Preserved regex rotation changed')
    f.verify(pins)
    return dict(schema=SCHEMA, status='prepared-awaiting-independent-review', repository=str(ROOT),
        controller=str(Path(__file__).resolve()), controller_sha256=sha(__file__), output=str(output),
        pins=pins, historical_pins=old_plan['historical_pins'], retained=retained, linear_qualification=linear,
        manifests=manifests, schedule=slots, retained_slots=slots[:9], remaining_slots=slots[9:],
        samples=3, full_processes=81, combined_sample_slots=90, retained_qualified_samples=9,
        new_prolog_processes=54, new_mech_processes=27, source_work_profiles=20, canonical_loc_profiles=20,
        shared_timing_lock=str(f.LOCK), common_mutex_held_continuously=True, no_automatic_retry=True,
        compiler_invocations=0, fixture_reexecutions=0, bounded_reexecutions=0, count_replays=0,
        repeated_completed_samples=0, original_files_mutated=False, full_timings_qualified=False, chart_admission=False,
        timing_policy='Fresh process including runtime startup, QLF loading, full input, all work, complete output, and shutdown; compilation, pin hashing and output validation excluded')


def fresh_paths(plan_path, output):
    require(plan_path.is_relative_to(PACKET) and output.is_relative_to(PACKET)
            and not plan_path.is_relative_to(output) and not output.is_relative_to(plan_path)
            and not plan_path.exists() and not output.exists(), 'Fresh separate plan/output paths required')


def prepare(args):
    plan_path, output = args.plan.resolve(), args.output.resolve()
    fresh_paths(plan_path, output)
    plan = build_plan(output)
    fresh_paths(plan_path, output)
    f.new_json(plan_path, plan)
    print(json.dumps(dict(plan=str(plan_path), sha256=sha(plan_path), full_processes=81,
                         retained_qualified_samples=9, native_executions=0)), flush=True)


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


def initial_rows(plan):
    rows = {row['key']:dict(copy.deepcopy(row), samples_seconds=[], sample_validation=[], attempts=[],
                           retained_attempts=[], measurement_status='pending')
            for manifest in plan['manifests'].values() for row in manifest['profiles']}
    require(len(rows) == 30, 'Profile inventory changed')
    for sample in plan['retained']['reused_samples']:
        row = rows[sample['slot'][3]]
        row['samples_seconds'].append(sample['seconds'])
        row['sample_validation'].append(copy.deepcopy(sample['validation']))
        row['retained_attempts'].append(sample['original_attempt'])
        row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
    require(summarize(rows, plan['manifests']['regexredux']), 'Retained regex group incomplete')
    return rows


def attempt_paths(output, attempt):
    stem = f'{attempt["attempt"]:03d}-{attempt["id"]}'
    return (output/'attempts'/(stem+'.json'), output/'attempts'/(stem+'.supervisor.json'),
            output/'outer-supervisor'/(stem+'.json'))


def fingerprint_pins(plan, physical):
    # Match the immutable reconciler: historical support aliases describe the
    # exact already-sealed bytes; verified current physical files take precedence.
    result = dict(plan['historical_pins'])
    result.update(physical)
    return result


def check_new_attempt(output, attempt, slot, row, manifest, pins, parent):
    paths = attempt_paths(output, attempt)
    require(attempt['result_path'] == str(paths[0]) and attempt['supervisor_result_path'] == str(paths[1]),
            'New attempt receipt escaped its output directory')
    raw, supervised, outer = [json.loads(path.read_bytes()) for path in paths]
    provenance = []
    r.check_attempt(attempt, raw, supervised, slot, row, manifest, pins, provenance)
    gaps = r.check_outer(outer, attempt, parent)
    return {str(path):sha(path) for path in paths}, provenance, gaps


def check_success_ledger(plan, report):
    expected = plan['remaining_slots']
    attempts = {tuple([a[k] for k in ('benchmark','round','id','key')]): a for a in report['attempts']}
    skipped = {tuple(s[k] for k in ('benchmark','round','id','key')) for s in report['skipped_failed_profile_slots']}
    require(len(attempts) == len(report['attempts']) and len(skipped) == len(report['skipped_failed_profile_slots'])
            and not set(attempts).intersection(skipped) and set(attempts).union(skipped) == {tuple(s) for s in expected},
            'Missing, duplicate or extra continuation slot')
    require([a['attempt'] for a in report['attempts']] == list(range(1, len(attempts)+1))
            and report['full_performance_runs'] == len(attempts) and report['native_launch_unconfirmed_attempts'] == []
            and report['active'] is None and report['completed_benchmarks'] == f.BENCHES,
            'Incomplete native ledger or workload summaries')
    rows = initial_rows(plan)
    failed = []
    for slot in expected:
        key = slot[3]; row = rows[key]
        if tuple(slot) in skipped:
            require(row.get('full_failure'), 'Skipped slot has no earlier isolated profile failure')
            continue
        attempt = attempts[tuple(slot)]
        require(not row.get('full_failure'), 'Retried failed profile')
        row['attempts'].append(attempt['attempt'])
        if attempt['qualified']:
            row['samples_seconds'].append(attempt['seconds']); row['sample_validation'].append(attempt['validation'])
            row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
        else:
            row['full_failure'] = attempt; row['measurement_status'] = 'failed-full-workload'; failed.append(key)
    for manifest in plan['manifests'].values():
        require(summarize(rows, manifest), 'Missing completed workload summary')
    require(rows == report['programs'] and failed == report['isolated_failed_profiles'], 'Summary does not replay ledger')
    require(report['qualified_samples'] == sum(len(row['samples_seconds']) for row in rows.values()),
            'Wrong retained plus new qualified sample count')
    require(report['retained_qualified_samples'] == 9 and report['repeated_completed_samples'] == 0,
            'Retained sample accounting changed')


def finish(plan, report, pins, snapshots, guard, lock):
    errors = []
    for path, digest in merge(pins, snapshots).items():
        try:
            require(sha(path) == digest, 'Pinned or validated bytes changed')
        except BaseException as error:
            errors.append(dict(path=path, error=str(error) or type(error).__name__))
    f.refresh_attempt_accounting(report)
    try:
        require(report['active'] is None, 'Active attempt remains after supervisor cleanup')
        if report['status'] in ('complete', 'complete-with-unqualified-profiles'):
            check_success_ledger(plan, report)
            expected_files = set()
            by_slot = {tuple(s):s for s in plan['remaining_slots']}
            for attempt in report['attempts']:
                slot = [attempt[k] for k in ('benchmark','round','id','key')]
                require(tuple(slot) in by_slot, 'Attempt outside new slots')
                manifest = plan['manifests'][attempt['benchmark']]
                row = next(row for row in manifest['profiles'] if row['key'] == attempt['key'])
                new, _, _ = check_new_attempt(guard.OUT, attempt, slot, row, manifest,
                                             fingerprint_pins(plan, pins), os.getpid())
                expected_files.update(new)
            require(set(snapshots) == expected_files, 'Missing validated attempt snapshot')
            observed = {str(path) for name in ('attempts','outer-supervisor') for path in (guard.OUT/name).rglob('*')
                        if path.is_file()}
            require(observed == expected_files, 'Extra or missing native attempt artifact')
    except BaseException as error:
        errors.append(dict(error=str(error) or type(error).__name__, error_type=type(error).__name__))
    held, named = os.fstat(lock.fileno()), f.LOCK.stat()
    if (held.st_dev, held.st_ino) != (named.st_dev, named.st_ino) or held.st_ino != 79859134:
        errors.append(dict(error='Common timing lock identity changed'))
    report['pins_unchanged_at_end'] = not errors
    report['validated_attempt_artifacts'] = snapshots
    if errors:
        report.update(status_before_terminal_integrity_failure=report['status'], status='failed-terminal-integrity',
                      terminal_integrity_errors=errors)
    guard.save(guard.REPORT, report)
    try:
        artifacts = file_inventory(guard.OUT)
    except BaseException as error:
        errors.append(dict(error='Artifact retention failed: '+str(error), error_type=type(error).__name__))
        artifacts = {str(guard.REPORT):sha(guard.REPORT)}
    # Close the inventory to the earlier validation, rather than allowing an
    # intervening edit to become a newly accepted terminal artifact digest.
    for path, digest in snapshots.items():
        if artifacts.get(path) != digest:
            errors.append(dict(path=path, error='Validated receipt changed during terminal inventory'))
    for path, digest in pins.items():
        try:
            require(sha(path) == digest, 'Prerequisite changed during terminal inventory')
        except BaseException as error:
            errors.append(dict(path=path, error=str(error) or type(error).__name__))
    if artifacts.get(str(guard.REPORT)) != sha(guard.REPORT):
        errors.append(dict(path=str(guard.REPORT), error='Report changed during terminal inventory'))
    if errors:
        report.update(status='failed-terminal-integrity', terminal_integrity_errors=errors, pins_unchanged_at_end=False)
        guard.save(guard.REPORT, report)
        artifacts[str(guard.REPORT)] = sha(guard.REPORT)
    f.new_json(guard.OUT/'terminal.json', dict(schema='prolog-linear-continuation-terminal-v1', status=report['status'],
        report=str(guard.REPORT), report_sha256=sha(guard.REPORT), prerequisite_pins=pins,
        available_evidence_pins=artifacts, integrity_errors=errors, common_mutex_held=True,
        common_mutex_held_continuously=True, common_mutex_inode=79859134,
        full_performance_runs=report['full_performance_runs'], saved_attempts=len(report['attempts']),
        registered_native_attempts=report['registered_native_attempts'],
        native_launch_unconfirmed_attempts=report['native_launch_unconfirmed_attempts'],
        qualified_samples=report['qualified_samples'], retained_qualified_samples=9,
        new_qualified_samples=report['qualified_samples']-9,
        skipped_failed_profile_slots=report['skipped_failed_profile_slots'], compiler_invocations=0,
        fixture_reexecutions=0, bounded_reexecutions=0, count_replays=0, repeated_completed_samples=0,
        original_files_mutated=False, full_timings_qualified=False, chart_admission=False))
    require(not errors, 'Terminal integrity failed; actual attempts preserved')


def run(args, lock):
    plan_path = args.plan.resolve()
    require(plan_path.is_relative_to(PACKET), 'Continuation plan outside its packet')
    pins = {}
    plan = read(pins, plan_path, args.plan_sha256)
    output = Path(plan['output'])
    require(output.is_absolute() and output.resolve() == output and output.is_relative_to(PACKET)
            and not plan_path.is_relative_to(output) and not output.exists(), 'Fresh continuation output required')
    require(plan == build_plan(output), 'Reviewed continuation plan differs from its exact prerequisites')
    pins = merge(plan['pins'], pins)
    resolver = f.Resolver(); resolver.logical = dict(plan['historical_pins'])
    guard, harness = f.load_measurement(resolver)
    require(all(pins.get(path) == digest for path, digest in resolver.active.items()), 'Frozen sampler loader pins changed')
    supervisor = f.cold(f.SUPERVISOR, SUPERVISOR_SHA, 'linear_full_owned_supervisor')
    manifests = {bench:dict(value, pins=pins) for bench,value in plan['manifests'].items()}
    for bench, manifest in manifests.items():
        require(manifest['size'] == harness.WORK[bench][1] and manifest['canonical_full_workload'] is True
                and manifest['timeout_seconds'] == 21600 and manifest['supervisor_timeout_seconds'] == 22200
                and manifest['maximum_rss_mib'] == 10240, 'Workload/resource policy changed')
    output.mkdir(parents=True)
    guard.OUT, guard.REPORT = output, output/'report.json'
    harness.install_interrupt_handlers()
    rows = initial_rows(plan)
    report = dict(schema=SCHEMA, status='running', started_at=guard.now(), supervisor=guard.identity(os.getpid()),
        plan=str(plan_path), plan_sha256=args.plan_sha256, programs=rows, attempts=[], active=None,
        reused_samples=plan['retained']['reused_samples'], retained_qualified_samples=9,
        benchmark_order=f.BENCHES, completed_benchmarks=['regexredux'], sample_count=3, full_performance_runs=0,
        skipped_failed_profile_slots=[], isolated_failed_profiles=[], shared_timing_lock=str(f.LOCK),
        common_mutex_held_continuously=True, source_work_profiles=20, canonical_loc_profiles=20,
        chart_admission=False, full_timings_qualified=False, no_automatic_retry=True, repeated_completed_samples=0,
        kernel_identity_observation_gaps=[], descriptive_provenance=[])
    snapshots = {}
    f.refresh_attempt_accounting(report); guard.save(guard.REPORT, report)
    try:
        for slot in plan['remaining_slots']:
            bench, round_index, identifier, key = slot
            row, manifest = rows[key], manifests[bench]
            if row.get('full_failure'):
                report['skipped_failed_profile_slots'].append(dict(benchmark=bench, round=round_index, id=identifier, key=key))
                guard.save(guard.REPORT, report); continue
            f.verify(pins)
            harness.compact.wait_for_environment(harness.REQUIRED)
            print('PROLOG LINEAR CONTINUATION', bench, round_index, identifier, manifest['size'], flush=True)
            previous_count = len(report['attempts'])
            try:
                attempt = supervisor.one_attempt(guard, harness, row, manifest, report, round_index, lock.fileno())
                with supervisor.lifecycle_atomic():
                    report['attempts'].append(attempt); report['active'] = None
                    row['attempts'].append(attempt['attempt'])
                    f.refresh_attempt_accounting(report); guard.save(guard.REPORT, report)
            except BaseException as error:
                with supervisor.lifecycle_atomic():
                    if len(report['attempts']) == previous_count:
                        f.preserve_wrapper_failure(guard, report, row, round_index, error)
                raise
            original_row = next(profile for profile in manifest['profiles'] if profile['key'] == key)
            captured, provenance, gaps = check_new_attempt(output, attempt, slot, original_row, manifest,
                                                           fingerprint_pins(plan, pins), os.getpid())
            snapshots.update(merge(snapshots, captured))
            report['descriptive_provenance'].extend(provenance); report['kernel_identity_observation_gaps'].extend(gaps)
            if attempt['qualified']:
                f.qualified_sample(attempt, manifest, row, harness.execution_fingerprint(row))
                row['samples_seconds'].append(attempt['seconds']); row['sample_validation'].append(attempt['validation'])
                row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
            elif f.isolated_failure(guard, attempt):
                row['full_failure'] = dict(attempt); row['measurement_status'] = 'failed-full-workload'
                report['isolated_failed_profiles'].append(key)
            else:
                row['measurement_status'] = 'stopped-unqualified'
            f.refresh_attempt_accounting(report); guard.save(guard.REPORT, report)
            require(attempt['qualified'] or row.get('full_failure'), 'Integrity/environment/ownership failure; no retry')
            if summarize(rows, manifest) and bench not in report['completed_benchmarks']:
                report['completed_benchmarks'].append(bench)
            guard.save(guard.REPORT, report)
        check_success_ledger(plan, report)
        report.update(status='complete-with-unqualified-profiles' if report['isolated_failed_profiles'] else 'complete',
                      finished_at=guard.now())
    except BaseException as error:
        report.update(status='stopped-unqualified', finished_at=guard.now(), error=str(error) or type(error).__name__,
                      error_type=type(error).__name__)
        (output/'error.log').write_text(traceback.format_exc())
        raise
    finally:
        # The same lock still covers all owned cleanup and final evidence.
        with supervisor.lifecycle_atomic():
            finish(plan, report, pins, snapshots, guard, lock)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    prep = modes.add_parser('prepare'); prep.add_argument('--plan', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    execute = modes.add_parser('run'); execute.add_argument('--plan', type=Path, required=True)
    execute.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode and not sys.flags.optimize
            and Path(sys.executable).resolve() == f.PYTHON.resolve(), 'Use the pinned Python with -I -S -B and no -O')
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Prolog continuation interrupted: '+str(signum))
    for signum in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(signum, interrupted)
    with owned_locks() as lock:
        prepare(args) if args.mode == 'prepare' else run(args, lock)


if __name__ == '__main__':
    main()
