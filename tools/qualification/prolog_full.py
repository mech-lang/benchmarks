"""Prepare and execute Prolog full90 from the immutable original22-v2 seal.

Preparation is metadata only. Run requires its exact plan digest and a new
output directory. Launch run through the existing durable job owner. All native
lifetimes use the unchanged frozen sampler and inherit the common timing lock.
"""
import argparse
import ast
import copy
from contextlib import contextmanager
import fcntl
import hashlib
import importlib.machinery
import json
import math
import os
from pathlib import Path
import statistics
import sys
import traceback
import types

ROOT = Path(__file__).resolve().parents[2]
QUALIFIED = ROOT / 'experiments/prolog/qualified-original22-v2'
HOST = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech')
CLBG = HOST / 'benchmarks/clbg'
LOCK = Path('/tmp/mech-clbg-timing.lock')
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
SUPERVISOR = ROOT / 'tools/qualification/prolog_supervisor.py'
OUTCOME_SHA = 'c6ff85042d9cc72f590b730825a4bba60bd85f0dd764d67ab64bffb4a5d6b69e'
STORAGE_SHA = '3538de1dfd61b923970c81db881342cf8ff15cb45c691817ce73433a7c9c1340'
SEALER_SHA = '21ef86135f7212fff9ed7465e2831ff177d9b44b2981996f4a19c90a7f69bafe'
READER_SHA = '3b3bc74aa48a15290778ca212fc8184b5914eb3bb71b0e0bc4e0efa9c072f05f'
OVERRIDES_SHA = 'c10db7e36edf419be6225ee5198509131ca36b80e11847dea9b96688081a523e'
GUARD = CLBG / 'r-apl-uiua-comparison/20261011/uiua-fann-compact-v5/controller_rev2/remaining_owner.py'
GUARD_SHA = '55581d56609803243b3be264e6a2e37229be06789c22788bbf8cdb6ff6828544'
AUDIT = CLBG / 'r-apl-uiua-comparison/20261011/source-audit-r.json'
AUDIT_SHA = 'd76be20504617addb9efd5915bf7074877e727e3a49ccbd36585b4be5c763af3'
MANDEL = CLBG / 'mandelbrot/experiments/20261011-array-state/source-modes-study/full-study/manifest.json'
MANDEL_SHA = 'fbffba7b5674e889ac9e5088bbb2e2d8499df41f5d9b4c677be38d831091680f'
BENCHES = ['regexredux', 'revcomp', 'pidigits', 'spectralnorm', 'mandelbrot',
           'fasta', 'knucleotide', 'binarytrees', 'nbody', 'fannkuchredux']
GATES = {'sampler_exited_normally', 'authoritative_native_group_received', 'native_inherited_common_mutex',
    'native_exited_normally', 'no_execution_error', 'no_wrapper_integrity_error', 'no_resource_violation',
    'no_resource_monitor_errors', 'no_compiler_power_monitor_errors', 'no_monitor_finish_error',
    'no_execute_cleanup_error', 'no_remaining_execute_group', 'no_supervisor_cleanup',
    'no_supervisor_remaining_group', 'valid_environment', 'actual_full_workload', 'exact_command_and_group',
    'complete_output_reference_match', 'complete_output_bytes_and_hash', 'pins_unchanged'}
SAFE = GATES - {'native_exited_normally', 'no_execution_error', 'no_resource_violation',
                'complete_output_reference_match', 'complete_output_bytes_and_hash'}
EXECUTION_FIELDS = ('id', 'key', 'benchmark', 'language', 'source', 'source_sha256',
                    'binary', 'binary_sha256', 'command', 'cwd', 'runtime_environment')


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def merge(*groups):
    result = {}
    for group in groups:
        for path, digest in group.items():
            require(path not in result or result[path] == digest, ('Conflicting pin', path))
            result[path] = digest
    return result


def new_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def cold(path, expected, name):
    path = Path(path)
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, ('Executable Python changed', str(path)))
    require(name not in sys.modules, ('Cached module', name))
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def sealed_editorial_digest(raw, kind, original):
    """Reproduce the seal's Python 3.14 AST display using measurement Python 3.12."""
    if kind != 'python-migration-policy':
        return original(raw, kind)
    tree = ast.parse(raw)
    selected = [node for node in ast.walk(tree) if isinstance(node, ast.keyword)
                and node.arg == 'migration_policy']
    require(len(selected) == 1 and isinstance(selected[0].value, ast.Constant)
            and type(selected[0].value.value) is str, 'Invalid editorial migration policy')
    selected[0].value = ast.Constant(value=None)
    # Python 3.14 omits empty-list fields by default; 3.12 prints them. These
    # per-instance fields belong only to freshly parsed evidence, never code
    # that is executed. Every nonempty field and original raw-byte pin remains.
    for node in ast.walk(tree):
        node._fields = tuple(name for name in node._fields if getattr(node, name, None) != [])
    return hashlib.sha256(ast.dump(tree, include_attributes=False).encode()).hexdigest()


def install_sealed_editorial_reader(sealer):
    original = sealer.noneditorial_digest
    sealer.noneditorial_digest = lambda raw, kind: sealed_editorial_digest(raw, kind, original)


class Resolver:
    """Archive evidence may relocate; actual execution paths retain exact bytes."""
    def __init__(self):
        sealer = cold(ROOT / 'tools/qualification/prolog_seal.py', SEALER_SHA, 'full90_prolog_sealer')
        install_sealed_editorial_reader(sealer)
        reader = cold(ROOT / 'tools/qualification/prolog_storage.py', READER_SHA, 'full90_prolog_storage')
        overrides = ROOT / 'experiments/prolog/editorial-substitutions.json'
        require(sha(overrides) == OVERRIDES_SHA, 'Editorial inventory changed')
        self.evidence = sealer.Evidence(ROOT, json.loads(overrides.read_bytes()))
        self.storage = reader.Storage(ROOT, QUALIFIED / 'storage-manifest.json', STORAGE_SHA)
        self.active, self.logical, self.relocations = {}, {}, {}
        imported = ROOT / 'migration/qualification-artifacts.json'
        self.added_compression = {str(ROOT / item['current_path']): item
            for item in json.loads(imported.read_bytes())['files'] if item['encoding'] == 'gzip'}
        for path, digest in [(ROOT / 'tools/qualification/prolog_seal.py', SEALER_SHA),
                             (ROOT / 'tools/qualification/prolog_storage.py', READER_SHA), (overrides, OVERRIDES_SHA),
                             (imported, sha(imported)),
                             (ROOT / 'migration/reorganization-paths.tsv', sha(ROOT / 'migration/reorganization-paths.tsv'))]:
            self.active[str(path)] = digest

    def local(self, historical):
        raw = str(historical)
        for prefix in ('/tmp/mech-benchmark-completion/', '/private/tmp/mech-benchmark-completion/'):
            if raw.startswith(prefix):
                return ROOT / raw[len(prefix):]
        return Path(raw)

    def read_bytes(self, historical, expected):
        require(type(expected) is str and len(expected) == 64, 'Every evidence reference needs a digest')
        local = self.local(historical)
        if local.is_relative_to(QUALIFIED):
            raw = self.storage.read_bytes(local, expected)
            self.active = merge(self.active, self.storage.pins)
        else:
            resolved = self.evidence.path(str(local))
            if resolved.suffix == '.gz' and not str(local).endswith('.gz'):
                declared = self.added_compression.get(str(resolved))
                require(declared is not None and declared['content_sha256'] == declared['original_sha256'] == expected
                        and sha(resolved) == declared['archive_sha256'], 'Undeclared or changed added compression')
            raw = self.evidence.read_bytes(str(local), expected)
            record = self.evidence.verified[(str(local), expected)]
            path = record['resolved_path']
            self.active = merge(self.active, {path: sha(path)})
            if str(historical) != path or record['actual_content_sha256'] != expected:
                self.relocations[str(historical)] = record
        self.logical = merge(self.logical, {str(historical): expected})
        return raw

    def read(self, historical, expected):
        return json.loads(self.read_bytes(historical, expected))

    def absorb(self, pins):
        for path, expected in pins.items():
            if path not in self.logical:
                self.read_bytes(path, expected)
            else:
                require(self.logical[path] == expected, ('Conflicting historical pin', path))

    def host(self, path, expected):
        path = Path(path)
        require(path.is_absolute() and '..' not in path.parts, ('Invalid execution path', str(path)))
        require(sha(path) == expected, ('Exact host execution dependency changed', str(path)))
        self.active = merge(self.active, {str(path): expected})
        return path

    def verify(self):
        self.evidence.unchanged()
        verify(self.active)


def verify(pins):
    for path, expected in pins.items():
        require(sha(path) == expected, ('Pinned bytes changed', path))


@contextmanager
def common_lock():
    with LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        held, named = os.fstat(lock.fileno()), LOCK.stat()
        require((held.st_dev, held.st_ino) == (named.st_dev, named.st_ino) and held.st_ino == 79859134,
                'Original common lock identity changed')
        yield lock


def checked_runtime():
    require(sys.dont_write_bytecode and sys.flags.isolated and sys.flags.no_site and not sys.flags.optimize,
            'Use the pinned Python with -I -S -B and without -O')
    require(Path(sys.executable).resolve() == PYTHON.resolve() and sha(PYTHON.resolve()) == PYTHON_SHA,
            'Measurement Python changed')


def load_measurement(resolver):
    resolver.host(GUARD, GUARD_SHA)
    guard = cold(GUARD, GUARD_SHA, 'full90_prolog_frozen_sampler')
    previous = importlib.machinery.SourceFileLoader.get_code

    def checked_code(loader, fullname):
        path = Path(loader.path).absolute()
        if path.is_relative_to(CLBG):
            require(path.suffix == '.py' and str(path) in resolver.logical, ('Unpinned harness import', str(path)))
            resolver.host(path, resolver.logical[str(path)])
            return compile(path.read_bytes(), str(path), 'exec')
        return previous(loader, fullname)

    importlib.machinery.SourceFileLoader.get_code = checked_code
    try:
        harness = guard.load_harness()
    finally:
        importlib.machinery.SourceFileLoader.get_code = previous
    require(harness.BENCHES == BENCHES and harness.LOCK == LOCK, 'Frozen suite order or lock changed')
    for module in list(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename and Path(filename).is_relative_to(CLBG):
            path = str(Path(filename).absolute())
            resolver.host(path, resolver.logical[path])
    return guard, harness


def require_bounded_preparation(prep):
    require(prep['all20_bounded_outputs_qualified'] is prep['terminal_evidence_complete'] is True
            and prep['new_bounded_cases'] == len(prep['attempts']) == 155
            and len(prep['reused_attempts']) == 1
            and prep['total_bounded_cases'] == len(prep['case_results'])
            == len(prep['attempts']) + len(prep['reused_attempts']) == 156,
            'Bounded evidence changed')


def evidence_closure(resolver):
    outcome = resolver.read(QUALIFIED / 'outcome.json', OUTCOME_SHA)
    require(outcome['status'] == 'qualified-original-Prolog20-work-and-LOC-awaiting-full90'
            and outcome['source_work_qualified'] is outcome['canonical_LOC_admitted'] is True
            and outcome['chart_admission'] is False, 'v2 source/work/LOC seal is not qualified')
    require((outcome['original_sources'], outcome['compiled_copy_reconciliations'], outcome['profiles'],
             outcome['native_commands'], outcome['benchmark_executions']) == (22, 44, 20, 0, 0), 'v2 seal scope changed')
    values = {}
    for filename, expected in outcome['outputs'].items():
        # Every original output remains checked, including all 20 independent
        # compiler-input wrappers. Compression changes storage, never identity.
        value = resolver.read(QUALIFIED / filename, expected)
        if filename in ('qualified-work20.json', 'qualified-loc-overlay.json', 'evidence-resolution.json'):
            values[filename] = value
    resolution = values['evidence-resolution.json']
    require(resolution['schema'] == 'portable-evidence-resolution-v1'
            and resolution['historical_receipts_unchanged'] is True, 'Seal evidence resolution changed')
    for record in resolution['records']:
        expected = record['expected_sha256'] or record['actual_content_sha256']
        raw = resolver.read_bytes(record['historical_path'], expected)
        require(hashlib.sha256(raw).hexdigest() == record['actual_content_sha256'], 'Sealed evidence content changed')
    work, loc = values['qualified-work20.json'], values['qualified-loc-overlay.json']
    require(work['status'] == 'qualified-required-source-work' and work['language'] == 'prolog'
            and work['chart_admission'] is False, 'Source work gate failed')
    require(loc['status'] == 'qualified-exact-source-LOC' and loc['canonical_LOC_admitted'] is True
            and loc['complete_authored_source_bundles'] is True and loc['unresolved'] == []
            and loc['chart_admission'] is False, 'Source count gate failed')
    resolver.absorb(work['pins'])
    resolver.absorb(loc['pins'])
    prep = resolver.read(work['original_bounded_preparation']['path'], work['original_bounded_preparation']['sha256'])
    require_bounded_preparation(prep)
    expected_ids = {f'prolog-{bench}-{variant}' for bench in BENCHES for variant in ('compact', 'optimized')}
    require(set(prep['profiles']) == set(work['profiles']) == set(loc['profiles'])
            == set(loc['compiler_bound_input_inventory']) == expected_ids, 'Prolog cohort changed')
    runtime = resolver.read(prep['runtime_config'], prep['runtime_config_sha256'])
    require(runtime['status'] == 'qualified-runtime-discovery' and runtime['version_components'] == [10, 0, 2]
            and runtime['architecture'] == 'arm64' and runtime['runtime_backend'] == 'swi-native-bytecode-vm'
            and runtime['default_gc_observed'] is True and runtime['bounded_observed'] is False, 'Runtime changed')
    return prep, work, loc, runtime


def require_execution(row, original):
    require(all(row.get(key) == original.get(key) for key in EXECUTION_FIELDS), 'Qualified execution identity changed')
    require(row['maximum_workers'] == original['maximum_workers'] == 1, 'Prolog worker limit changed')
    require(row['command'][0] == row['binary'], 'Command is not the pinned runtime')


def candidate(resolver, original, work, counted, inventory, runtime):
    require(original['bounded_output_qualified'] is True and work['status'] == work['source_review']['status'] == 'passed',
            'Profile prerequisite missing')
    require(original == inventory['independently_retained_compiler_input_evidence'], 'Compiled original profile changed')
    require(inventory['status'] == 'qualified-exact-authored-compiler-inputs'
            and inventory['original_compiler_input_evidence'] == original['compiler_bound_input_inventory']
            == work['compiler_bound_input_inventory'], 'Compiler inventory changed')
    require(counted['source'] == original['measured_source'] and counted['source_origin'] == original['source']
            and counted['source_sha256'] == inventory['source_sha256'] == work['source_sha256'] == original['source_sha256']
            and inventory['binary_sha256'] == work['binary_sha256'] == original['binary_sha256'], 'Work/count/runtime linkage changed')
    require(work['application_artifact_pins'] == original['application_artifact_pins'], 'Application artifacts changed')
    require(counted['source_bundle'] == inventory['files'], 'Whole authored source bundle changed')
    require(counted['canonical_loc'] == sum(f['normalized_loc'] for f in counted['source_bundle'])
            and counted['physical_loc'] == sum(f['physical_loc'] for f in counted['source_bundle']), 'LOC aggregate changed')
    require(original['binary'] == runtime['binary'] and original['binary_sha256'] == runtime['binary_sha256']
            and original['runtime_environment'] == runtime['environment'], 'Runtime configuration changed')
    require(original['runtime_policy'] == 'Default term/atom/clause garbage collection; uniform8g stack ceiling',
            'Default GC policy changed')
    for path, expected in merge(original['application_artifact_pins'], original['runtime_closure_pins'],
                               {original['source']: original['source_sha256'], original['binary']: original['binary_sha256']}).items():
        if path not in resolver.active:
            resolver.host(path, expected)
        else:
            require(resolver.active[path] == expected, 'Execution pin conflicts with evidence')
    require(Path(original['cwd']).is_dir(), 'Original working directory missing')
    for part in original['command']:
        if part.startswith('/'):
            require(part in resolver.active, ('Unpinned command artifact', part))
    for field in ('allocation_retention_witness', 'original_scored_vm_allocation_review') if original['benchmark'] == 'binarytrees' else (
                  ('seven_map_capacity_windows_witness',) if original['benchmark'] == 'knucleotide' else (
                  ('both_actual_divisions_witness',) if original['benchmark'] == 'pidigits' else ())):
        require(work[field]['status'] == 'passed', 'Required runtime work witness missing')
    row = {key: copy.deepcopy(original[key]) for key in EXECUTION_FIELDS}
    row.update(variant=original['variant'], maximum_workers=1, source_alias_of=original['source_alias_of'],
        optimization_claim=original['optimization_claim'], measured_source=original['measured_source'],
        loc=counted['canonical_loc'], canonical_loc=counted['canonical_loc'], physical_loc=counted['physical_loc'],
        source_bundle=[{key: item[key] for key in ('path','origin','sha256','normalized_loc','physical_loc')}
                       for item in counted['source_bundle']],
        compiler_bound_input_inventory=dict(path=str(QUALIFIED / (original['id']+'-compiled-inputs.json')),
            sha256=inventory['evidence_sha256'], status=inventory['status']),
        required_work_review=dict(status='passed', path=str(QUALIFIED / 'qualified-work20.json'),
            sha256='ae59de5a0a7ea2e1df99719e1d55df0d62d1007f700b7799be53df87efb3de6f'),
        memory_policy='Qualified default SWI term/atom/clause GC; gc=true, bounded=false',
        execution_mode=original['execution_mode'], eligible_for_chart=False, chart_admission=False)
    require_execution(row, original)
    return row


def bind_full_reference_pins(resolver, audit):
    # Bounded preparation retains small inputs; the unchanged control audit
    # supplies the canonical full inputs/oracles. reference_for verifies their
    # actual host bytes before they become active execution pins.
    paths = [str(CLBG / relative) for relative in (
        'knucleotide/.build/knucleotide-input25000000.txt',
        'regexredux/.build/input5000000.txt',
        'pidigits/inputs/output-full.txt', 'regexredux/inputs/output-full.txt')]
    resolver.logical = merge(resolver.logical, {path: audit['pins'][path] for path in paths})


def controls(resolver):
    audit = resolver.read(AUDIT, AUDIT_SHA)
    special = resolver.read(MANDEL, MANDEL_SHA)
    require(audit['status'] == 'reviewed' and {r['benchmark'] for r in audit['controls']} == set(BENCHES), 'Control audit changed')
    bind_full_reference_pins(resolver, audit)
    result = {}
    for bench in BENCHES:
        origin = (next(r for r in special['profiles'] if r['id'] == 'row16-aot-control') if bench == 'mandelbrot'
                  else next(r for r in audit['controls'] if r['benchmark'] == bench))
        require(origin['language'] == 'mech' and origin['benchmark'] == bench and origin['command'][0] == origin['binary'],
                'Control execution changed')
        for field in ('source', 'binary'):
            resolver.host(origin[field], origin[field+'_sha256'])
        for path, expected in origin.get('support', {}).items():
            resolver.host(path, expected)
        row = {key: copy.deepcopy(origin[key]) for key in EXECUTION_FIELDS}
        row.update(id='mech-aot-control', key=bench+':prolog-full-study:mech-control', maximum_workers=8,
            producer_loc=origin.get('loc'), loc=None, role='Fresh unchanged Mech AOT control', chart_admission=False,
            control_provenance=dict(path=str(MANDEL if bench == 'mandelbrot' else AUDIT),
                                   sha256=MANDEL_SHA if bench == 'mandelbrot' else AUDIT_SHA, original_id=origin['id']))
        result[bench] = row
    return result


def schedule_for(manifests):
    schedule = []
    require(set(manifests) == set(BENCHES), 'Incomplete benchmark manifest set')
    for bench in BENCHES:
        manifest = manifests[bench]
        rows = manifest['profiles']
        require(len(rows) == 3 and {r['language'] for r in rows} == {'prolog','mech'}, 'Benchmark cohort changed')
        ids = [r['id'] for r in rows]
        require(ids == [f'prolog-{bench}-compact', f'prolog-{bench}-optimized', 'mech-aot-control'], 'Profile order changed')
        orders = [dict(round=i+1, profiles=ids[i:]+ids[:i]) for i in range(3)]
        require(manifest['orders'] == orders, 'Three-round rotation changed')
        keys = {r['id']: r['key'] for r in rows}
        schedule.extend((bench, order['round'], identifier, keys[identifier]) for order in orders for identifier in order['profiles'])
    require(len(schedule) == len(set(schedule)) == 90, 'Invalid full90 schedule')
    return schedule


def reference_for(resolver, harness, bench):
    if bench in harness.INPUTS:
        path = harness.INPUTS[bench][1]
        require(str(path) in resolver.logical, 'Full stdin is not in the qualified closure')
        resolver.host(path, resolver.logical[str(path)])
    if bench == 'nbody':
        # Frozen validator reads the complete two-energy output and checks 1e-8.
        return None
    if bench in ('pidigits', 'regexredux'):
        path = CLBG / bench / 'inputs/output-full.txt'
        require(str(path) in resolver.logical, 'Full output oracle is not in the qualified closure')
        resolver.host(path, resolver.logical[str(path)])
        return dict(bytes=path.stat().st_size, sha256=resolver.logical[str(path)])
    if bench in ('spectralnorm', 'fannkuchredux'):
        raw = {'spectralnorm': b'1.274224153\n', 'fannkuchredux': b'3968050\nPfannkuchen(12) = 65\n'}[bench]
        return dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    count, digest = harness.compact.HASHES[bench][1]
    return dict(bytes=count, sha256=digest)


def prepare(args):
    checked_runtime()
    require(not args.plan.exists() and not args.output.exists(), 'Plan and output must be new')
    with common_lock():
        resolver = Resolver()
        prep, work, loc, runtime = evidence_closure(resolver)
        guard, harness = load_measurement(resolver)
        control_rows = controls(resolver)
        manifests = {}
        for bench in BENCHES:
            rows = [candidate(resolver, prep['profiles'][identifier], work['profiles'][identifier],
                              loc['profiles'][identifier], loc['compiler_bound_input_inventory'][identifier], runtime)
                    for identifier in (f'prolog-{bench}-compact', f'prolog-{bench}-optimized')]
            rows.append(control_rows[bench])
            ids = [row['id'] for row in rows]
            manifests[bench] = dict(benchmark=bench, profiles=rows, samples=3, size=harness.WORK[bench][1],
                canonical_full_workload=True, orders=[dict(round=i+1,profiles=ids[i:]+ids[:i]) for i in range(3)],
                timeout_seconds=21600, supervisor_timeout_seconds=22200, maximum_rss_mib=10240,
                full_output_reference=reference_for(resolver,harness,bench),
                shared_timing_lock=str(LOCK), no_automatic_retry=True, chart_admission=False,
                compilation_outside_timer=True, runtime_and_QLF_loading_inside_timer=True)
        schedule = schedule_for(manifests)
        resolver.active = merge(resolver.active, {str(Path(__file__).resolve()): sha(__file__),
            str(SUPERVISOR): sha(SUPERVISOR), str(PYTHON.resolve()): PYTHON_SHA})
        resolver.verify()
        plan = dict(schema='prolog-qualified-original22-full90-v1', status='prepared-awaiting-independent-review',
            controller=str(Path(__file__).resolve()), controller_sha256=sha(__file__), repository=str(ROOT),
            output=str(args.output.resolve()), sealed_source_outcome=dict(path=str(QUALIFIED/'outcome.json'),sha256=OUTCOME_SHA),
            storage_manifest=dict(path=str(QUALIFIED/'storage-manifest.json'),sha256=STORAGE_SHA),
            original_preparation=work['original_bounded_preparation'], source_work_profiles=20, canonical_loc_profiles=20,
            original_authored_sources=22, compiled_copy_reconciliations=44, retained_bounded_cases=156,
            original_files_mutated=False, new_native_probes=0, compiler_invocations=0, fixture_reexecutions=0,
            bounded_reexecutions=0, count_replays=0, chart_admission=False, samples=3, full_processes=90,
            schedule=schedule, manifests=manifests, pins=resolver.active, historical_pins=resolver.logical,
            path_reconciliation=resolver.relocations, shared_timing_lock=str(LOCK), no_automatic_retry=True,
            timing_policy='Fresh process including runtime startup, QLF loading, full input, all work, complete output, and shutdown; compilation, pin hashing and output validation excluded')
        new_json(args.plan, plan)
        print(json.dumps(dict(plan=str(args.plan),sha256=sha(args.plan),full_processes=90,native_executions=0)),flush=True)


def strict_checks(attempt):
    checks = attempt.get('qualification_checks')
    require(type(checks) is dict and set(checks) == GATES and all(type(flag) is bool for flag in checks.values()),
            'Qualification gate inventory or boolean values changed')
    return checks


def qualified_sample(attempt, manifest, row, fingerprint):
    checks = strict_checks(attempt)
    require(attempt.get('qualified') is True and all(checks.values()), 'Sample failed qualification')
    require(attempt['full_workload'] is True and attempt['workload_n'] == manifest['size'], 'Noncanonical sample')
    require(type(attempt['seconds']) in (int,float) and math.isfinite(attempt['seconds']) and attempt['seconds'] > 0,
            'Invalid measured duration')
    for name in ('attempt','workload_n','sampler_wait_status','stdout_bytes','exit_status'):
        require(type(attempt[name]) is int and attempt[name] >= 0, ('Invalid integer sample field',name))
    require(attempt['sampler_wait_status'] == attempt['exit_status'] == 0, 'Nonzero native or sampler exit')
    native = attempt['supervised_native_group']
    require(type(native['pid']) is int and native['pid'] > 0 and native['pgid'] == native['pid']
            and native['inherited_common_mutex'] is True, 'Native ownership changed')
    command = [part.replace('{n}',str(manifest['size'])) for part in row['command']]
    require(native['command'] == attempt['command'] == command and attempt['execution_fingerprint'] == fingerprint,
            'Measured command or environment changed')
    validation = attempt['validation']
    require(validation['reference_match'] is True and type(validation['bytes']) is int
            and validation['bytes'] == attempt['stdout_bytes'] and validation['sha256'] == attempt['stdout_sha256'],
            'Incomplete output validation')
    if manifest['full_output_reference'] is not None:
        require((attempt['stdout_bytes'],attempt['stdout_sha256']) ==
                (manifest['full_output_reference']['bytes'],manifest['full_output_reference']['sha256']),
                'Complete output differs from the frozen reference')


def isolated_failure(guard, attempt):
    checks = strict_checks(attempt)
    return guard.benchmark_failure(attempt) and all(checks[key] is True for key in SAFE)


def refresh_attempt_accounting(report):
    """Count registered native launches separately from receipts and samples."""
    registered, uncertain = [], []
    for attempt in report['attempts']:
        native = attempt.get('supervised_native_group') or attempt.get('wrapper_native_registration')
        if (type(native) is dict and type(native.get('pid')) is int and native['pid'] > 0
                and type(native.get('pgid')) is int and native['pgid'] == native['pid']
                and native.get('inherited_common_mutex') is True
                and type(native.get('command')) is list and native['command']):
            registered.append(attempt['attempt'])
        else:
            # Missing registration does not prove that a process never started.
            uncertain.append(attempt['attempt'])
    report.update(saved_attempts=len(report['attempts']), full_performance_runs=len(registered),
                  registered_native_attempts=registered, native_launch_unconfirmed_attempts=uncertain,
                  qualified_samples=sum(len(row['samples_seconds']) for row in report['programs'].values()))


def preserve_wrapper_failure(guard, report, row, round_index, error):
    index = len(report['attempts']) + 1
    raw = guard.OUT / 'attempts' / f'{index:03d}-{row["id"]}.json'
    supervised = raw.with_suffix('.supervisor.json')
    source = supervised if supervised.exists() else raw
    attempt = {}
    if source.exists():
        try:
            attempt = json.loads(source.read_bytes())
            require(type(attempt) is dict, 'Partial receipt is not an object')
        except BaseException as receipt_error:
            attempt = dict(partial_receipt=str(source), partial_receipt_sha256=sha(source),
                           partial_receipt_error=str(receipt_error) or type(receipt_error).__name__)
    active = report.get('active') or {}
    if active.get('native'):
        attempt['wrapper_native_registration'] = copy.deepcopy(active['native'])
    attempt.update(attempt=index,round=round_index,id=row['id'],key=row['key'],benchmark=row['benchmark'],
        qualified=False,wrapper_supervisor_failure=True,wrapper_error=str(error) or type(error).__name__,
        wrapper_error_type=type(error).__name__,chart_admission=False)
    new_json(raw.with_suffix('.wrapper.json'),attempt)
    report['attempts'].append(attempt)
    row['attempts'].append(index)
    row['measurement_status']='stopped-unqualified'
    report['active']=None
    refresh_attempt_accounting(report)
    guard.save(guard.REPORT,report)


def run(args):
    checked_runtime()
    require(sha(args.plan) == args.plan_sha256, 'Reviewed plan changed')
    plan = json.loads(args.plan.read_bytes())
    require(plan['schema'] == 'prolog-qualified-original22-full90-v1'
            and plan['controller'] == str(Path(__file__).resolve()) and plan['controller_sha256'] == sha(__file__)
            and plan['repository'] == str(ROOT), 'Wrong full90 controller or repository')
    require(plan['samples'] == 3 and plan['full_processes'] == 90 and plan['no_automatic_retry'] is True
            and plan['chart_admission'] is False and plan['shared_timing_lock'] == str(LOCK), 'Plan policy changed')
    output = Path(plan['output'])
    require(not output.exists(), 'No overwrite, implicit resume, or repeated sample')
    output.parent.mkdir(parents=True,exist_ok=True)
    # The lease remains held across lock-release gaps; different output paths
    # still cannot launch a second Prolog cohort concurrently.
    lease_path = ROOT / 'experiments/prolog/prolog-full90.owner.lock'
    with lease_path.open('a+') as lease:
        fcntl.flock(lease,fcntl.LOCK_EX|fcntl.LOCK_NB)
        require((os.fstat(lease.fileno()).st_dev,os.fstat(lease.fileno()).st_ino) ==
                (lease_path.stat().st_dev,lease_path.stat().st_ino), 'Suite lease was replaced')
        with common_lock():
            verify(plan['pins'])
            resolver = Resolver()
            resolver.logical = dict(plan['historical_pins'])
            guard,harness = load_measurement(resolver)
            supervisor = cold(SUPERVISOR,plan['pins'][str(SUPERVISOR)],'prolog_full90_independent_supervisor')
            require(all(plan['pins'].get(path) == digest for path,digest in resolver.active.items()), 'Measurement loader pins changed')
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
                source_work_profiles=20,canonical_loc_profiles=20,chart_admission=False,no_automatic_retry=True)
            refresh_attempt_accounting(report)
            guard.save(guard.REPORT,report)
        try:
            for bench,round_index,identifier,key in schedule:
                row,manifest = rows[key],manifests[bench]
                if row.get('full_failure'):
                    report['skipped_failed_profile_slots'].append(dict(benchmark=bench,round=round_index,id=identifier,key=key))
                    guard.save(guard.REPORT,report)
                    continue
                with common_lock() as lock:
                    verify(pins)
                    harness.compact.wait_for_environment(harness.REQUIRED)
                    print('PROLOG FULL',bench,round_index,identifier,manifest['size'],flush=True)
                    try:
                        attempt = supervisor.one_attempt(guard,harness,row,manifest,report,round_index,lock.fileno())
                    except BaseException as error:
                        preserve_wrapper_failure(guard,report,row,round_index,error)
                        raise
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
            with common_lock():
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
                    repeated_completed_samples=0,original_files_mutated=False,chart_admission=False))
                require(not errors,'Terminal integrity failed; actual attempts preserved')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    modes=parser.add_subparsers(dest='mode',required=True)
    prep=modes.add_parser('prepare',help='Verify exact evidence and create a fresh full90 plan; no native runs')
    prep.add_argument('--plan',type=Path,required=True)
    prep.add_argument('--output',type=Path,required=True)
    execute=modes.add_parser('run',help='Execute an independently reviewed plan under an external durable owner')
    execute.add_argument('--plan',type=Path,required=True)
    execute.add_argument('--plan-sha256',required=True)
    args=parser.parse_args()
    (prepare if args.mode=='prepare' else run)(args)


if __name__=='__main__':
    main()
