"""Prepare and execute the qualified retained Elixir full90 cohort.

Draft reads saved metadata only. Prepare verifies its exact flat closure under
the common mutex. Run requires the independently reviewed prepared plan digest.
The frozen serial sampler, validators and independent process supervisor are
reused unchanged. No historical-language resolver or native probe is involved.
"""
import argparse
import copy
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import statistics
import sys
import traceback
import types

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'experiments/elixir/full90-v1'
SHARED = ROOT / 'tools/qualification/prolog_full.py'
SHARED_SHA = '0d75d33bb77d3715ca7adcd8c07fcf3b659be472c2ef84c063dec57ee4b8eb94'


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def cold(path, expected, name):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, ('Python source changed', str(path)))
    require(name not in sys.modules, ('Cached module', name))
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


# Definition-only import. Only these language-neutral helpers are used; the
# Prolog Resolver, evidence_closure, candidate, prepare and run are never called.
shared = cold(SHARED, SHARED_SHA, 'elixir_full_shared_receipt_checks')
merge, new_json, verify = shared.merge, shared.new_json, shared.verify
qualified_sample, isolated_failure = shared.qualified_sample, shared.isolated_failure
refresh_attempt_accounting = shared.refresh_attempt_accounting
preserve_wrapper_failure = shared.preserve_wrapper_failure
HOST, CLBG, LOCK = shared.HOST, shared.CLBG, shared.LOCK
PYTHON, PYTHON_SHA, BENCHES = shared.PYTHON, shared.PYTHON_SHA, shared.BENCHES
GUARD, GUARD_SHA, SUPERVISOR = shared.GUARD, shared.GUARD_SHA, shared.SUPERVISOR
SUPERVISOR_SHA = '5458bdf5e58465cb21156a2140657066b4706aa2a0941fe3efde8758207574b4'
AUDIT, AUDIT_SHA, MANDEL, MANDEL_SHA = shared.AUDIT, shared.AUDIT_SHA, shared.MANDEL, shared.MANDEL_SHA
BOUNDED = ROOT / 'experiments/elixir/bounded-work-v1/plan.json'
BOUNDED_SHA = '4ca22a19e8c29b13764c20047c2230b73708189c0bb402c7cdb92fcb95b4e808'
WORK = ROOT / 'experiments/elixir/compiled-work-v1/qualified-work-v1.json'
WORK_SHA = 'a96ed85f0f0d1da05cca428d18dfeb9d0d702158b7aa0f7a5c87ae827b4588bf'
LOC = ROOT / 'experiments/elixir/source-units-v1/qualified-source-counts.json'
LOC_SHA = '1fd0401a8dc46a70268beb6dd2a287b7725e74b9a4a0d33d4c6e92d8ff1df755'
SAMPLER_PINS = {str(CLBG / path): digest for path, digest in {
    'r-apl-uiua-comparison/20261011/run.py': '5b2a038cfae4112e9e2eee79c3cd57ccc6a1521812828c47bf28986d6a8e139b',
    'r-apl-uiua-comparison/20261011/prepare.py': '27fcf050ed21db40e747f2e8801ca6f227d82f1ea98f8592bba7b10a768109e5',
    'array-comparison/all-20261009/run.py': '8b7f1b408fb5838dc6adc2404bcfa6146e48e770e602fbe78255454f3cacb8c7',
    'compact/run.py': '6926e288a7b9b59b030c9226227df967aa1d92b3e395789467706e2241d987ae',
    'nbody/run.py': 'e907f71b3fdf8fc6f65adc76aab6dfc424811875388c14f0eb2f31e14e9cffcf',
}.items()} | {str(GUARD): GUARD_SHA}
FULL = {
    'regexredux': (5000000, 298, 'a37e6da1d43b332d5c0f4fc25b76090e9095d4c97c25f1a7186385e87706e4af'),
    'revcomp': (25000000, 254166745, 'e5730d4fd55c464f276e5c6062c80f46e0a735281de15d8c957e2731a9baf70e'),
    'pidigits': (10000, 16893, 'bdfa7b6c756d96492f472f97aee9cc139bee954d271eacedfd7ace5d2875f06c'),
    'spectralnorm': (5500, 12, 'f9d5b5e3eb7657cf1bbba4cc856651864df9cd9fd9a6be9b9bc5fcbb67150deb'),
    'mandelbrot': (16000, 32000015, '609262469ee6a0262ccd03932e557f745c9e7b997ad17835a02a0232a64807be'),
    'fasta': (25000000, 254166745, '3fcf4f78104c8a65ef210fe1d469f4e473456c791225f2f1f9114f4986aa09fa'),
    'knucleotide': (25000000, 259, 'f8c042fe770dda8f870b967605ea40ca2e353f2bdf92e89a327209dd31d445c7'),
    'binarytrees': (21, 455, '341de11a51feab3d8122b4b5d6a68b038a2d14434aa9bc2372f39300bf5f48e1'),
    'nbody': (50000000, None, None),
    'fannkuchredux': (12, 29, '4265a65135c506a68d90d6474003fb9030b7ee244a06c046bd89b3932a28ce20'),
}
ROLES = ['application', 'application-helper', 'application-launcher']


def verify_lock(lock):
    held, named = os.fstat(lock.fileno()), LOCK.stat()
    require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) and held.st_ino == 79859134,
            'Original common mutex identity changed')


@contextmanager
def common_lock():
    with LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify_lock(lock)
        yield lock
        verify_lock(lock)


@contextmanager
def held_lock(lock):
    """Check the one continuously held descriptor around each native lifetime."""
    verify_lock(lock)
    yield lock
    verify_lock(lock)


def checked_runtime():
    shared.checked_runtime()


def read_metadata(path, expected, pins):
    """Verify a named metadata file, never traverse or hash its closure here."""
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'Metadata path must be absolute')
    require(sha(path) == expected, ('Saved metadata changed', str(path)))
    pins.update(merge(pins, {str(path): expected}))
    return json.loads(path.read_bytes())


def artifact_pins(directory, inventory):
    result = {}
    for relative, record in inventory.items():
        part = Path(relative)
        require(not part.is_absolute() and '..' not in part.parts, 'Artifact escaped its retained directory')
        require(type(record['bytes']) is int and record['bytes'] >= 0, 'Invalid artifact size')
        result[str(directory / part)] = record['sha256']
    return result


def keyed(profiles):
    result = {p['id']: p for p in profiles}
    expected = {f'elixir-{b}-{v}' for b in BENCHES for v in ('compact', 'optimized')}
    require(len(profiles) == len(result) == 20 and set(result) == expected, 'Elixir cohort changed')
    return result


def prerequisites():
    pins = {}
    work = read_metadata(WORK, WORK_SHA, pins)
    loc = read_metadata(LOC, LOC_SHA, pins)
    bounded = read_metadata(BOUNDED, BOUNDED_SHA, pins)
    require(work['schema'] == 'elixir-retained-compiled-work-qualified-v1'
            and work['status'] == 'all20-compiled-required-work-qualified'
            and work['source_work_qualified'] is True and work['compiled_work_profiles'] == 20
            and work['bounded_cases_reused'] == 156 and work['subject_recompilations'] == 0
            and work['benchmark_samples'] == 0 and work['chart_admission'] is False, 'Work qualification missing')
    require(loc['schema'] == 'elixir-qualified-source-counts-v1'
            and loc['status'] == 'twenty-retained-source-counts-qualified'
            and loc['canonical_loc_qualified'] is loc['formatted_loc_qualified'] is True
            and loc['chart_admission'] is False, 'Source-count qualification missing')
    report = read_metadata(work['report'], work['report_sha256'], pins)
    terminal = read_metadata(work['terminal'], work['terminal_sha256'], pins)
    read_metadata(work['decisions'], work['decisions_sha256'], pins)
    compiled = read_metadata(report['plan'], report['plan_sha256'], pins)
    require(report['status'] == terminal['status'] == 'all20-compiled-work-observed-awaiting-direct-instruction-review'
            and report['active'] is None and report['native_processes_started'] == 20
            and terminal['report_sha256'] == work['report_sha256']
            and terminal['integrity_errors'] == terminal['artifact_errors'] == terminal['process_receipt_errors'] == [],
            'Compiled-work terminal is not closed and clean')
    require(compiled['bounded_plan'] == str(BOUNDED)
            and compiled['bounded_plan_sha256_recorded'] == BOUNDED_SHA, 'Bounded prerequisite differs')
    source_plan = read_metadata(loc['source_plan'], loc['source_plan_sha256'], pins)
    reader_terminal_path = loc['native_artifact_closure']['terminal']
    reader_terminal = read_metadata(reader_terminal_path, loc['evidence_pins'][reader_terminal_path], pins)
    require(len(reader_terminal['artifacts']) == loc['native_artifact_closure']['files'] == 372
            and reader_terminal['artifact_errors'] == reader_terminal['integrity_errors'] == reader_terminal['receipt_errors'] == [],
            'Source reader artifact closure differs')
    pins = merge(pins, bounded['pins'], compiled['pins'], report['pins'], source_plan['pins'], loc['evidence_pins'],
                 artifact_pins(Path(work['terminal']).parent, terminal['available_evidence']),
                 artifact_pins(Path(reader_terminal_path).parent, reader_terminal['artifacts']))
    return keyed(bounded['profiles']), keyed(compiled['profiles']), keyed(loc['profiles']), loc['files'], pins


def candidate(original, compiled, counted, files, pins):
    require(original['id'] == compiled['id'] == counted['id'], 'Profile qualification identity differs')
    for field in ('physical_inputs', 'beams', 'owners', 'runtime_environment'):
        require(original[field] == compiled[field], ('Compiled retained identity differs', field))
    require(original['command'] == compiled['retained_command'], 'Retained launcher command differs')
    sources = original['physical_inputs']
    require([p['role'] for p in sources] == ROLES and all(p['counted'] is True for p in sources),
            'Whole authored bundle is required')
    counted_files = [files[i] for i in counted['inputs']]
    require([(p['path'], p['sha256'], p['role']) for p in sources] ==
            [(p['source'], p['source_sha256'], p['role']) for p in counted_files], 'LOC/source linkage differs')
    for aggregate, field in [('canonical_loc', 'canonical_loc'), ('formatted_loc', 'formatted_loc'),
                             ('original_physical_loc', 'original_physical_loc')]:
        require(type(counted[aggregate]) is int and counted[aggregate] > 0
                and counted[aggregate] == sum(p[field] for p in counted_files), 'Source-count aggregate differs')
    require(counted['canonical_loc_qualified'] is counted['formatted_loc_qualified'] is True, 'Profile LOC unqualified')
    command = original['command']
    require(command == [command[0], '-pa', original['ebin'], sources[2]['path'], '{n}']
            and Path(command[0]).name == 'elixir', 'Unexpected diagnostic or compilation command')
    require(len(original['beams']) == 2 and {Path(p['path']).name for p in original['beams']} ==
            {'Elixir.Clbg.Main.beam', 'Elixir.Clbg.Support.beam'}
            and all(str(Path(p['path']).parent) == original['ebin'] for p in original['beams']), 'Retained BEAM path differs')
    env = original['runtime_environment']
    require(env['ELIXIR_ERL_OPTIONS'] == '+S 8:8 +A 1 +SDcpu 1:1 +SDio 1'
            and all(env[k] == '' for k in ('ERL_FLAGS', 'ERL_AFLAGS', 'ERL_ZFLAGS', 'ERL_LIBS')),
            'Runtime policy or diagnostic flags changed')
    for item in sources + original['beams']:
        require(pins.get(item['path']) == item['sha256'], 'Unpinned retained subject artifact')
    # Ownership records are archived evidence, never execution paths. Bind the
    # already-qualified flat pin entries by exact content and filename; do not
    # resolve historical paths or read a different language's archive machinery.
    owner_evidence = []
    for item in original['owners']:
        retained = [path for path, digest in pins.items()
                    if digest == item['sha256'] and Path(path).name == Path(item['path']).name]
        require(len(retained) == 1, 'Ownership evidence has no unique qualified retained pin')
        owner_evidence.append(dict(path=retained[0], sha256=item['sha256'], origin=item['path']))
    require(command[0] in pins, 'Unpinned Elixir launcher')
    return dict(id=original['id'], key=original['id'], benchmark=original['benchmark'], variant=original['variant'],
        language='elixir', source=sources[0]['path'], source_sha256=sources[0]['sha256'], binary=command[0],
        binary_sha256=pins[command[0]], command=copy.deepcopy(command), cwd=str(Path(sources[0]['path']).parent),
        runtime_environment=copy.deepcopy(env), maximum_workers=8, physical_inputs=copy.deepcopy(sources),
        beams=copy.deepcopy(original['beams']), owners=copy.deepcopy(original['owners']),
        retained_owner_evidence=owner_evidence,
        source_alias_note=original['source_alias_note'], optimization_claim=False,
        source_work_qualified=True, canonical_loc_qualified=True, formatted_loc_qualified=True,
        loc=counted['canonical_loc'], canonical_loc=counted['canonical_loc'], formatted_loc=counted['formatted_loc'],
        physical_loc=counted['original_physical_loc'], memory_policy='Retained default BEAM garbage collection',
        runtime_policy_changes=[], diagnostic_flags=[], chart_admission=False)


def controls(pins):
    audit = read_metadata(AUDIT, AUDIT_SHA, pins)
    special = read_metadata(MANDEL, MANDEL_SHA, pins)
    require(audit['status'] == 'reviewed' and {p['benchmark'] for p in audit['controls']} == set(BENCHES),
            'Matched control audit changed')
    result = {}
    for bench in BENCHES:
        origin = (next(p for p in special['profiles'] if p['id'] == 'row16-aot-control') if bench == 'mandelbrot'
                  else next(p for p in audit['controls'] if p['benchmark'] == bench))
        arguments = ([] if bench in ('regexredux', 'knucleotide', 'revcomp') else
                     ['{n}', '8'] if bench == 'mandelbrot' else ['{n}'])
        require(origin['language'] == 'mech' and origin['benchmark'] == bench
                and origin['command'] == [origin['binary']] + arguments, 'Matched control command changed')
        additions = {origin[k]: origin[k+'_sha256'] for k in ('source', 'binary')}
        pins.update(merge(pins, additions, origin.get('support', {})))
        row = {key: copy.deepcopy(origin[key]) for key in shared.EXECUTION_FIELDS}
        row.update(id='mech-aot-control', key=bench+':elixir-full-study:mech-control', maximum_workers=8,
            loc=None, role='Fresh unchanged matched Mech AOT control', chart_admission=False,
            control_provenance=dict(path=str(MANDEL if bench == 'mandelbrot' else AUDIT),
                sha256=MANDEL_SHA if bench == 'mandelbrot' else AUDIT_SHA, original_id=origin['id']))
        result[bench] = row
    for relative in ('knucleotide/.build/knucleotide-input25000000.txt', 'regexredux/.build/input5000000.txt',
                     'pidigits/inputs/output-full.txt', 'regexredux/inputs/output-full.txt'):
        path = str(CLBG / relative)
        pins.update(merge(pins, {path: audit['pins'][path]}))
    return result


def schedule_for(manifests):
    require(set(manifests) == set(BENCHES), 'Incomplete benchmark manifests')
    schedule = []
    for bench in BENCHES:
        manifest = manifests[bench]
        rows = manifest['profiles']
        ids = [f'elixir-{bench}-compact', f'elixir-{bench}-optimized', 'mech-aot-control']
        require([p['id'] for p in rows] == ids and [p['language'] for p in rows] == ['elixir', 'elixir', 'mech']
                and all(p['benchmark'] == bench for p in rows), 'Full cohort or profile order differs')
        orders = [dict(round=i+1, profiles=ids[i:]+ids[:i]) for i in range(3)]
        require(manifest['orders'] == orders and manifest['samples'] == 3, 'Three-round rotation changed')
        keys = {p['id']: p['key'] for p in rows}
        schedule.extend((bench, o['round'], p, keys[p]) for o in orders for p in o['profiles'])
    require(len(schedule) == len(set(schedule)) == 90 and len({s[3] for s in schedule}) == 30, 'Full90 schedule differs')
    return schedule


def build_draft(output):
    original, compiled, counted, files, pins = prerequisites()
    control_rows = controls(pins)
    manifests = {}
    for bench in BENCHES:
        rows = [candidate(original[i], compiled[i], counted[i], files, pins)
                for i in (f'elixir-{bench}-compact', f'elixir-{bench}-optimized')]
        rows.append(control_rows[bench])
        ids = [r['id'] for r in rows]
        size, count, digest = FULL[bench]
        manifests[bench] = dict(benchmark=bench, profiles=rows, samples=3, size=size,
            canonical_full_workload=True, orders=[dict(round=i+1, profiles=ids[i:]+ids[:i]) for i in range(3)],
            timeout_seconds=21600, supervisor_timeout_seconds=22200, maximum_rss_mib=10240,
            full_output_reference=None if bench == 'nbody' else dict(bytes=count, sha256=digest),
            shared_timing_lock=str(LOCK), no_automatic_retry=True, chart_admission=False,
            retained_subject_compilation_outside_timer=True, runtime_and_BEAM_loading_inside_timer=True,
            launcher_evaluation_inside_timer=True)
    pins = merge(pins, SAMPLER_PINS, {str(SHARED): SHARED_SHA, str(SUPERVISOR): SUPERVISOR_SHA,
        str(PYTHON.resolve()): PYTHON_SHA, str(Path(__file__).resolve()): sha(__file__)})
    return dict(schema='elixir-qualified-retained-full90-v1', status='draft-metadata-only-not-executable',
        pins_verified=False, controller=str(Path(__file__).resolve()), controller_sha256=sha(__file__),
        repository=str(ROOT), output=str(Path(output).resolve()),
        qualified_work=dict(path=str(WORK), sha256=WORK_SHA), qualified_source_counts=dict(path=str(LOC), sha256=LOC_SHA),
        original_bounded_plan=dict(path=str(BOUNDED), sha256=BOUNDED_SHA), source_work_profiles=20,
        canonical_loc_profiles=20, formatted_loc_profiles=20, retained_bounded_cases=156,
        compiler_invocations=0, fixture_reexecutions=0, bounded_reexecutions=0, count_replays=0,
        new_native_probes=0, original_files_mutated=False, samples=3, elixir_samples=60, matched_mech_samples=30,
        full_processes=90, schedule=[list(s) for s in schedule_for(manifests)], manifests=manifests, pins=pins,
        shared_timing_lock=str(LOCK), common_mutex_inode=79859134, continuous_common_mutex=True,
        no_automatic_retry=True,
        full_timings_qualified=False, chart_admission=False,
        timing_policy='Fresh process including runtime startup, retained BEAM loading, launcher evaluation, full input, all work, complete output and shutdown; retained subject compilation, pin hashing and output validation excluded')


def validate_plan(plan, prepared=False):
    expected = build_draft(plan['output'])
    if prepared:
        expected.update(status='prepared-awaiting-independent-review', pins_verified=True)
    require(plan == expected, 'Plan differs from the exact qualified cohort, closure, schedule or policy')


def load_measurement():
    guard = cold(GUARD, GUARD_SHA, 'elixir_full_frozen_sampler')
    previous = importlib.machinery.SourceFileLoader.get_code
    loaded = set()

    def checked_code(loader, fullname):
        path = Path(loader.path).absolute()
        if path.is_relative_to(CLBG):
            require(str(path) in SAMPLER_PINS, ('Unpinned measurement import', str(path)))
            raw = path.read_bytes()
            require(hashlib.sha256(raw).hexdigest() == SAMPLER_PINS[str(path)], 'Measurement import changed')
            loaded.add(str(path))
            return compile(raw, str(path), 'exec')
        return previous(loader, fullname)

    importlib.machinery.SourceFileLoader.get_code = checked_code
    try:
        harness = guard.load_harness()
    finally:
        importlib.machinery.SourceFileLoader.get_code = previous
    require(loaded == set(SAMPLER_PINS) - {str(GUARD)}, 'Measurement import inventory differs')
    require(harness.BENCHES == BENCHES and harness.LOCK == LOCK, 'Frozen sampler suite or mutex differs')
    require(all(harness.WORK[b][1] == FULL[b][0] for b in BENCHES), 'Full workload changed')
    return guard, harness


def check_execution_inputs(plan, harness):
    for bench, manifest in plan['manifests'].items():
        if bench in harness.INPUTS:
            require(str(harness.INPUTS[bench][1]) in plan['pins'], 'Unpinned full stdin')
        if bench in ('pidigits', 'regexredux'):
            path = CLBG / bench / 'inputs/output-full.txt'
            require(manifest['full_output_reference'] == dict(bytes=path.stat().st_size, sha256=plan['pins'][str(path)]),
                    'Full output oracle differs')
        if bench in harness.compact.HASHES:
            count, digest = harness.compact.HASHES[bench][1]
            require(manifest['full_output_reference'] == dict(bytes=count, sha256=digest), 'Full output reference differs')
        for row in manifest['profiles']:
            require(Path(row['cwd']).is_dir(), 'Native working directory missing')
            if row['language'] == 'elixir':
                beam_paths = {p['path'] for p in row['beams']}
                require({str(p) for p in Path(row['command'][2]).glob('*.beam')} == beam_paths,
                        'Retained application BEAM inventory changed')


def draft(args):
    require(not args.plan.exists() and not args.output.exists(), 'Draft plan and output must be new')
    plan = build_draft(args.output)
    new_json(args.plan, plan)
    print(json.dumps(dict(plan=str(args.plan), sha256=sha(args.plan), native_executions=0, pins_verified=False)), flush=True)


def prepare(args):
    checked_runtime()
    require(not args.plan.exists(), 'Prepared plan must be new')
    require(sha(args.draft) == args.draft_sha256, 'Reviewed draft changed')
    with common_lock() as lock:
        plan = json.loads(args.draft.read_bytes())
        validate_plan(plan)
        require(not Path(plan['output']).exists(), 'Output already exists')
        verify(plan['pins'])
        _, harness = load_measurement()
        check_execution_inputs(plan, harness)
        plan.update(status='prepared-awaiting-independent-review', pins_verified=True)
        verify_lock(lock)
        new_json(args.plan, plan)
        print(json.dumps(dict(plan=str(args.plan), sha256=sha(args.plan), full_processes=90, native_executions=0)), flush=True)


def run_locked(args, live_lock):
    checked_runtime()
    require(sha(args.plan) == args.plan_sha256, 'Reviewed plan changed')
    plan = json.loads(args.plan.read_bytes())
    validate_plan(plan, prepared=True)
    output = Path(plan['output'])
    require(not output.exists(), 'No overwrite, implicit resume, or repeated sample')
    output.parent.mkdir(parents=True,exist_ok=True)
    # The suite lease also excludes another cohort using a different output.
    lease_path = ROOT / 'experiments/elixir/elixir-full90.owner.lock'
    with lease_path.open('a+') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require((os.fstat(lease.fileno()).st_dev,os.fstat(lease.fileno()).st_ino) ==
                (lease_path.stat().st_dev,lease_path.stat().st_ino), 'Suite lease was replaced')
        with held_lock(live_lock) as lock:
            verify(plan['pins'])
            guard,harness = load_measurement()
            check_execution_inputs(plan, harness)
            supervisor = cold(SUPERVISOR, SUPERVISOR_SHA, 'elixir_full90_independent_supervisor')
            verify_lock(lock)
            schedule = schedule_for(plan['manifests'])
            require([list(slot) for slot in schedule] == plan['schedule'], 'Reviewed schedule changed')
            pins = merge(plan['pins'],{str(args.plan.resolve()):args.plan_sha256})
            manifests = {bench:dict(manifest,pins=pins) for bench,manifest in plan['manifests'].items()}
            for bench,manifest in manifests.items():
                require(manifest['size'] == harness.WORK[bench][1] and manifest['canonical_full_workload'] is True
                        and manifest['timeout_seconds'] == 21600 and manifest['supervisor_timeout_seconds'] == 22200
                        and manifest['maximum_rss_mib'] == 10240,
                        'Workload or resource policy changed')
            output.mkdir()
            guard.OUT,guard.REPORT = output,output/'report.json'
            harness.install_interrupt_handlers()
            rows = {row['key']:dict(copy.deepcopy(row),samples_seconds=[],sample_validation=[],attempts=[],measurement_status='pending')
                    for manifest in manifests.values() for row in manifest['profiles']}
            require(len(rows) == 30,'Full cohort changed')
            report = dict(status='running',started_at=guard.now(),supervisor=guard.identity(os.getpid()),
                plan=str(args.plan.resolve()),plan_sha256=args.plan_sha256,programs=rows,attempts=[],active=None,
                benchmark_order=BENCHES,completed_benchmarks=[],sample_count=3,full_performance_runs=0,
                skipped_failed_profile_slots=[],isolated_failed_profiles=[],shared_timing_lock=str(LOCK),
                source_work_profiles=20,canonical_loc_profiles=20,formatted_loc_profiles=20,
                planned_elixir_samples=60,planned_matched_mech_samples=30,full_timings_qualified=False,
                chart_admission=False,no_automatic_retry=True)
            refresh_attempt_accounting(report)
            guard.save(guard.REPORT,report)
        try:
            for bench,round_index,identifier,key in schedule:
                row,manifest = rows[key],manifests[bench]
                if row.get('full_failure'):
                    report['skipped_failed_profile_slots'].append(dict(benchmark=bench,round=round_index,id=identifier,key=key))
                    guard.save(guard.REPORT,report)
                    continue
                with held_lock(live_lock) as lock:
                    verify(pins)
                    harness.compact.wait_for_environment(harness.REQUIRED)
                    check_execution_inputs(plan, harness)
                    verify_lock(lock)
                    print('ELIXIR FULL',bench,round_index,identifier,manifest['size'],flush=True)
                    try:
                        attempt = supervisor.one_attempt(guard,harness,row,manifest,report,round_index,lock.fileno())
                    except BaseException as error:
                        preserve_wrapper_failure(guard,report,row,round_index,error)
                        raise
                    verify_lock(lock)
                    report['attempts'].append(attempt)
                    report['active']=None
                    row['attempts'].append(attempt['attempt'])
                    refresh_attempt_accounting(report)
                    guard.save(guard.REPORT,report)
                    # Frozen sampler and supervisor artifacts are never edited.
                    raw = json.loads(Path(attempt['result_path']).read_bytes())
                    supervised = json.loads(Path(attempt['supervisor_result_path']).read_bytes())
                    require(supervised == attempt and all(attempt.get(k) == v for k,v in raw.items()),
                            'Raw sampler and supervised records differ')
                    if attempt['qualified']:
                        qualified_sample(attempt,manifest,row,harness.execution_fingerprint(row))
                        row['samples_seconds'].append(attempt['seconds'])
                        row['sample_validation'].append(attempt['validation'])
                        row['measurement_status']='measured' if len(row['samples_seconds']) == 3 else 'partial'
                    elif isolated_failure(guard,attempt):
                        row['measurement_status']='failed-full-workload'
                        row['full_failure']=dict(attempt)
                        report['isolated_failed_profiles'].append(key)
                    else:
                        row['measurement_status']='stopped-unqualified'
                    refresh_attempt_accounting(report)
                    guard.save(guard.REPORT,report)
                    require(attempt['qualified'] or row.get('full_failure'), 'Integrity/environment/ownership failure; no retry')
                group = [rows[r['key']] for r in manifest['profiles']]
                if all(len(r['samples_seconds']) == 3 or r.get('full_failure') for r in group):
                    control = next(r for r in group if r['language']=='mech')
                    for r in group:
                        if not r.get('full_failure'):
                            r.update(median_seconds=statistics.median(r['samples_seconds']),
                                     sample_stdev_seconds=statistics.stdev(r['samples_seconds']))
                    for r in group:
                        r['time_x_mech'] = (r['median_seconds']/control['median_seconds']
                                           if not r.get('full_failure') and not control.get('full_failure') else None)
                        r['matched_mech_control']=control['key']
                        r['matched_mech_source_sha256']=control['source_sha256']
                    if bench not in report['completed_benchmarks']:
                        report['completed_benchmarks'].append(bench)
                    guard.save(guard.REPORT,report)
            require(len(report['attempts'])+len(report['skipped_failed_profile_slots']) == 90
                    and len(report['completed_benchmarks']) == 10,'Incomplete full90 accounting')
            require(report['full_performance_runs'] == len(report['attempts']),'Native attempt accounting mismatch')
            report.update(status='complete-with-unqualified-profiles' if report['isolated_failed_profiles'] else 'complete',
                          finished_at=guard.now())
        except BaseException as error:
            report.update(status='stopped-unqualified',finished_at=guard.now(),error=str(error) or type(error).__name__,
                          error_type=type(error).__name__)
            (output/'error.log').write_text(traceback.format_exc())
            raise
        finally:
            with held_lock(live_lock) as lock:
                errors=[]
                for path,expected in pins.items():
                    try:
                        require(sha(path)==expected,'Pinned bytes changed')
                    except BaseException as error:
                        errors.append(dict(path=path,error=str(error) or type(error).__name__,error_type=type(error).__name__))
                report['pins_unchanged_at_end'] = not errors
                refresh_attempt_accounting(report)
                if errors:
                    report['status_before_terminal_integrity_failure'] = report['status']
                    report['status'] = 'failed-terminal-integrity'
                    report['terminal_integrity_errors'] = errors
                verify_lock(lock)
                guard.save(guard.REPORT,report)
                available={str(p):sha(p) for p in output.rglob('*') if p.is_file()}
                new_json(output/'terminal.json',dict(status='failed-terminal-integrity' if errors else report['status'],
                    report=str(guard.REPORT),report_sha256=sha(guard.REPORT),prerequisite_pins=pins,
                    available_evidence_pins=available,integrity_errors=errors,common_mutex_held=True,
                    full_performance_runs=report['full_performance_runs'],saved_attempts=len(report['attempts']),
                    registered_native_attempts=report['registered_native_attempts'],
                    native_launch_unconfirmed_attempts=report['native_launch_unconfirmed_attempts'],
                    qualified_samples=report['qualified_samples'],
                    skipped_failed_profile_slots=report['skipped_failed_profile_slots'],
                    compiler_invocations=0,fixture_reexecutions=0,bounded_reexecutions=0,count_replays=0,
                    repeated_completed_samples=0,original_files_mutated=False,full_timings_qualified=False,chart_admission=False))
                verify_lock(lock)
                require(not errors,'Terminal integrity failed; actual attempts preserved')


def run(args):
    # A single inherited descriptor remains locked through environment waits,
    # all 90 slots, every cleanup and the final evidence/terminal write.
    with common_lock() as lock:
        run_locked(args, lock)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    source = modes.add_parser('draft', help='Create reviewable metadata only; no full pin verification or native run')
    source.add_argument('--plan', type=Path, required=True)
    source.add_argument('--output', type=Path, required=True)
    prep = modes.add_parser('prepare', help='Verify reviewed draft and all pins under the common mutex; no native run')
    prep.add_argument('--draft', type=Path, required=True)
    prep.add_argument('--draft-sha256', required=True)
    prep.add_argument('--plan', type=Path, required=True)
    execute = modes.add_parser('run', help='Execute the reviewed prepared plan under a durable external owner')
    execute.add_argument('--plan', type=Path, required=True)
    execute.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    {'draft': draft, 'prepare': prepare, 'run': run}[args.mode](args)


if __name__ == '__main__':
    main()
