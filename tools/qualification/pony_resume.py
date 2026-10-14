"""Resume the retained Pony suite after archive relocation, without repeating samples.

Preparation verifies evidence and creates an immutable execution plan. Execution
uses the original sampler, process supervisor, validator, commands and workloads.
No compiler, source-count replay, benchmark pilot or publication runs here.
"""
import argparse
import copy
import csv
import fcntl
import hashlib
import importlib.machinery
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import types
from contextlib import ExitStack, contextmanager


ROOT = Path(__file__).resolve().parents[2]
OLD_ROOT = Path('/Users/cim310/mech-lang/benchmarks')
HOST = Path('/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech')
HOST_CLBG = HOST / 'benchmarks/clbg'
HOST_COHORT = HOST_CLBG / 'pony-comparison/20261012'
COHORT_REL = Path('benchmarks/clbg/pony-comparison/20261012')
ARCHIVE_REL = Path('archive/languages/pony/20261012')
OLD_STUDY = OLD_ROOT / COHORT_REL / 'full-studies/pony-retained20-full-v1'
RETAINED_STUDY = OLD_ROOT / COHORT_REL / 'full-studies/pony-retained20-resumed-v1'
LOCK = Path('/tmp/mech-clbg-timing.lock')
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
SUITE_SHA = '0bb51cf4b706d6bb7fa4e36447dd3e641665f513c9608d04217ae377126cb5e1'
FIRST_REPORT_SHA = 'b1536d6ba6e336eb61f06d1fcc6dd3e7437a8e29ad9d047808215f9e8d6b6588'
FIRST_TERMINAL_SHA = 'd8fffef67cf6039f41f64770c415d3e9ee7bdd657df67df5ecf67fa8d6d1e025'
RETAINED_REPORT_SHA = '24eec56b10bead949ffa7c182500a8b930829c322c4ee612bf88ad756ac85ef4'
APPROVED_REL = Path('benchmarks/clbg/continuation/jobs/pony-retained-full-manifest-review-v1/review.json')
APPROVED_SHA = 'ad48d5381906dca4a1b14b7a92333b8c12812da1fb739639e20d9af8af00fee7'
GUARD_PATH = HOST_CLBG / 'r-apl-uiua-comparison/20261011/uiua-fann-compact-v5/controller_rev2/remaining_owner.py'
GUARD_SHA = '55581d56609803243b3be264e6a2e37229be06789c22788bbf8cdb6ff6828544'
WORK_SHA = 'aa7786b7cd16565a5ef21cb0bb56e8e0b7ccf77ddf5e98cbcfd1710b6b6aa421'
LOC_SHA = '5831dd9675da58865a39edab9f86ecbdb36377a470052814aeb06a981fbbe182'
LOC_TERMINAL_SHA = '80d86166ffd0a8175a437579b923652238b87188b32ab4d9bda23162b8d17073'
LOC_ROOT_SHA = '4c0d830178406cd4ab4bd800eabfe6493a68816e363c52eeb2e6f20dfc0e72de'
ALLOCATION_SHA = '354f4eab47aef151f1f5cf29824c2b7b4f45f582b307b2373ca0ec316434d346'
BENCHES = ['regexredux', 'revcomp', 'pidigits', 'spectralnorm', 'mandelbrot',
           'fasta', 'knucleotide', 'binarytrees', 'nbody', 'fannkuchredux']
CONTROL_PINS = {
    'full90-retained-v1/full_study.py': 'ec044db2f618830ef9b445bc4a2ac063d96b77cbd4a1614acc4264f540d6fcc2',
    'full90-retained-v1/REVIEW.md': '29cb21d8c728de8fbf1f89d258bc4a18221888df95b4b8315b185c65fe605abc',
    'resume-full90-v1/resume.py': '4c5c1be5cb761fed661b91db394124201fb54e44345e70ce71821ae4acb21989',
    'resume-full90-v1/REVIEW.md': '43ada6073e8813a6e3f54f6301a8abfcc6a8b40717dd05c24d26bb4820d13713',
}


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


def manifest_technical_digest(raw):
    value = json.loads(raw)
    require(type(value.get('chart_policy')) is str, 'Manifest chart_policy must remain narrative text')
    value.pop('chart_policy')
    return hashlib.sha256((json.dumps(value, sort_keys=True, separators=(',', ':')) + '\n').encode()).hexdigest()


class Resolver:
    """Resolve receipt paths without changing receipts or executable paths.

    Only four named, unused historical orchestration documents can have an
    explicitly recorded replacement hash. Sources, binaries, runtime, work,
    LOC, sampler and output evidence always retain the historical digest.
    """

    def __init__(self, root, retained, replacements):
        self.root, self.retained = Path(root).resolve(), Path(retained).resolve()
        self.mapping_path = self.root / 'migration/reorganization-paths.tsv'
        with self.mapping_path.open(newline='') as stream:
            rows = list(csv.DictReader(stream, delimiter='\t'))
        self.mapping = {row['original_path']: row['current_path'] for row in rows}
        require(len(self.mapping) == len(rows), 'Duplicate migration map entries')
        self.replacements_path = Path(replacements).resolve()
        changes = json.loads(self.replacements_path.read_text())
        require(changes['schema'] == 'pony-orchestration-supersessions-v1', 'Replacement schema')
        self.replacements = {}
        for entry in changes['artifacts']:
            name = entry['revision_path']
            require(name in CONTROL_PINS and entry['historical_sha256'] == CONTROL_PINS[name],
                    ('Only named historical orchestration may be superseded', name))
            logical = str(OLD_ROOT / COHORT_REL / 'revisions' / name)
            require(logical not in self.replacements, 'Duplicate replacement')
            current = self.root / ARCHIVE_REL / 'revisions' / name
            require(entry['archive_path'] == str(current.relative_to(self.root)), 'Replacement path changed')
            require(entry['executed'] is False and entry['source_or_runtime_evidence'] is False,
                    'Historical orchestration cannot become executable evidence')
            self.replacements[logical] = (entry['historical_sha256'], entry['archive_sha256'])
        require({str(OLD_ROOT / COHORT_REL / 'revisions' / name) for name in CONTROL_PINS if name.startswith('full90-')}
                <= set(self.replacements), 'The retired full controller and review must be disclosed')
        self.editorials_path = self.replacements_path.with_name('manifest-editorial-parity.json')
        self.editorials = {}
        if self.editorials_path.exists():
            editorial = json.loads(self.editorials_path.read_text())
            require(editorial['schema'] == 'pony-manifest-editorial-parity-v1', 'Manifest parity schema')
            allowed = {str((OLD_STUDY / 'manifest.json').relative_to(OLD_ROOT))}
            allowed.update(str((OLD_STUDY / bench / 'manifest.json').relative_to(OLD_ROOT)) for bench in BENCHES)
            for entry in editorial['artifacts']:
                relative = entry['historical_path']
                require(relative in allowed and relative not in self.editorials, 'Only exact historical manifests may have editorial parity')
                require(entry['changed_json_fields'] == ['chart_policy'] and entry['technical_content_preserved'] is True
                        and entry['original_bytes_digest_reconstructed_and_verified'] is True, 'Manifest technical changes are forbidden')
                require(self.mapping[relative] == entry['archive_path'], 'Manifest parity archive path changed')
                self.editorials[relative] = entry
            require(set(self.editorials) == allowed, 'Manifest parity must cover exactly the original eleven manifests')
        self.logical_pins, self.active_pins, self.relocations = {}, {}, {}

    def resolve(self, logical):
        path = Path(logical)
        require(path.is_absolute() and '..' not in path.parts, ('Invalid receipt path', logical))
        if path.is_relative_to(RETAINED_STUDY):
            return self.retained / path.relative_to(RETAINED_STUDY)
        if path.is_relative_to(OLD_ROOT):
            relative = str(path.relative_to(OLD_ROOT))
            if relative in self.mapping:
                current = (self.root / self.mapping[relative]).resolve()
                require(current.is_relative_to(self.root), 'Migration path escapes repository')
                return current
            revision = OLD_ROOT / COHORT_REL / 'revisions/resume-full90-v1'
            if path.is_relative_to(revision):
                return self.root / ARCHIVE_REL / 'revisions/resume-full90-v1' / path.relative_to(revision)
            raise AssertionError(('Historical repository path has no migration entry', logical))
        # Host executable, input, runtime and original source-work evidence are
        # intentionally left at their fingerprinted execution locations.
        return path

    def bind(self, logical, expected, pins=None):
        logical = str(Path(logical).absolute())
        require(len(expected) == 64 and all(c in '0123456789abcdef' for c in expected), 'Invalid SHA256')
        path = self.resolve(logical)
        actual_expected = expected
        if logical in self.replacements:
            prior, actual_expected = self.replacements[logical]
            require(expected == prior, ('Replacement does not match historical pin', logical))
        editorial = None
        if Path(logical).is_relative_to(OLD_ROOT):
            editorial = self.editorials.get(str(Path(logical).relative_to(OLD_ROOT)))
        if editorial:
            require(expected == editorial['historical_sha256'], 'Manifest parity historical pin changed')
            actual_expected = editorial['archive_sha256']
            raw = path.read_bytes()
            require(manifest_technical_digest(raw) == editorial['noneditorial_sha256'], 'Manifest technical content changed')
            require(hashlib.sha256(json.dumps(json.loads(raw)['chart_policy']).encode()).hexdigest()
                    == editorial['archive_field_sha256'], 'Manifest narrative changed after parity review')
        require(sha(path) == actual_expected, ('Pinned bytes changed', logical, str(path)))
        self.logical_pins = merge(self.logical_pins, {logical: expected})
        self.active_pins = merge(self.active_pins, {str(path): actual_expected})
        if str(path) != logical or actual_expected != expected:
            self.relocations[logical] = dict(path=str(path), historical_sha256=expected,
                active_sha256=actual_expected, superseded_orchestration=logical in self.replacements,
                manifest_editorial_parity=editorial)
        if pins is not None:
            require(logical not in pins or pins[logical] == expected, ('Conflicting proof pin', logical))
            pins[logical] = expected
        return path

    def read(self, logical, expected=None, pins=None):
        expected = expected or self.logical_pins[str(logical)]
        require(str(logical) not in self.replacements, 'Retired orchestration is not JSON evidence')
        return json.loads(self.bind(logical, expected, pins).read_bytes())

    def absorb(self, values, pins=None):
        require(type(values) is dict and values, 'Empty or invalid pin set')
        for logical, digest in values.items():
            self.bind(logical, digest, pins)

    def digest(self, logical):
        require(str(logical) not in self.replacements, 'Retired orchestration cannot satisfy source proof')
        expected = self.logical_pins[str(logical)]
        self.bind(logical, expected)
        return expected


def cold(path, expected, name, resolver):
    require(str(path) not in resolver.replacements, 'Never execute retired orchestration')
    actual = resolver.bind(path, expected)
    require(actual == Path(path), 'Executable proof and measurement code must stay at the pinned host path')
    raw = actual.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == expected, 'Code changed during load')
    require(name not in sys.modules, 'Proof module already loaded')
    module = types.ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def load_measurement(resolver):
    guard = cold(GUARD_PATH, GUARD_SHA, 'pony_migrated_saved_guard', resolver)
    previous = importlib.machinery.SourceFileLoader.get_code

    def checked_code(loader, fullname):
        path = Path(loader.path).absolute()
        if path.is_relative_to(HOST_CLBG):
            require(path.suffix == '.py' and str(path) in resolver.logical_pins,
                    ('Unpinned harness import', str(path)))
            raw = resolver.bind(path, resolver.logical_pins[str(path)]).read_bytes()
            return compile(raw, str(path), 'exec')
        return previous(loader, fullname)

    importlib.machinery.SourceFileLoader.get_code = checked_code
    try:
        harness = guard.load_harness()
    finally:
        importlib.machinery.SourceFileLoader.get_code = previous
    # Some original loaders do not register their module in sys.modules; the
    # loader hook above verifies their bytes before execution as well.
    for module in list(sys.modules.values()):
        filename = getattr(module, '__file__', None)
        if filename and Path(filename).is_relative_to(HOST_CLBG):
            resolver.bind(filename, resolver.logical_pins[str(Path(filename).absolute())])
    require(harness.BENCHES == BENCHES, 'Frozen workload order changed')
    return guard, harness


def validate_source_evidence(resolver, suite, harness):
    """Recheck the original work closure, allocation proof and complete LOC bundle."""
    closure_path = HOST_COHORT / 'revisions/loc-reviewed-seal-v1/seal.py'
    closure = cold(closure_path, '2b6983388a4cbcb15a64903238026a2920ee811391fc104151cb79c85dc04604',
                   'pony_migrated_work_closure', resolver)
    # This proof refers exclusively to unchanged original host paths. Its
    # original binder and semantic work checks execute without modification.
    closure_pins = {}
    work = closure.work_closure(closure_pins)
    resolver.absorb(closure_pins)
    require(resolver.logical_pins[str(HOST_COHORT / 'work-qualification/private-v8-work-reviewed-v1/report.json')] == WORK_SHA,
            'Original source-work receipt changed')
    qualification = resolver.read(suite['qualification'], suite['qualification_sha256'])
    resolver.absorb(qualification['pins'])
    require(len(qualification['profiles']) == len({r['id'] for r in qualification['profiles']}) == 20,
            'Pony cohort changed')
    require(qualification['reused_bounded_cases'] == 154 and qualification['fresh_unscored_primitive_cases'] == 1,
            'Original bounded qualification changed')
    allocation_path = HOST_COHORT / 'work-qualification/private-v8-work-reviewed-v1/allocation.json'
    allocation = resolver.read(allocation_path, ALLOCATION_SHA)
    tree_path = HOST_COHORT / 'revisions/work-full-v5/full_prerequisite.py'
    tree = cold(tree_path, '87c0dcaf5c952366e487e2c0205fc39aacbe3c6ef2c2b39bec8fe99a39a49239',
                'pony_migrated_tree_proof', resolver)
    tree_gate = tree.require_tree_proof(qualification, work, allocation, ALLOCATION_SHA,
                                      resolver.digest, resolver.read)
    require(tree_gate == suite['tree_allocation_prerequisite'], 'Allocation evidence changed')
    loc_path = HOST_COHORT / 'source-counts/loc-reviewed-seal-v1/qualified-loc-overlay.json'
    loc = resolver.read(loc_path, LOC_SHA)
    resolver.absorb(loc['pins'])
    root_path = OLD_ROOT / 'benchmarks/clbg/continuation/jobs/pony-reviewed-loc-closed-review-v1/receipt.json'
    root = resolver.read(root_path, LOC_ROOT_SHA)
    require(root['status'] == 'closed-qualified-Pony20-canonical-LOC' and root['verified_pins'] == 10750,
            'Original LOC closure missing')
    require((root['profiles'], root['unique_authored_sources'], root['bundle_entries'], root['original_diagnostics_preserved'])
            == (20, 21, 22, 6), 'LOC inventory changed')
    require(root['count_override'] is root['chart_admission'] is False and root['common_mutex_held'] is True,
            'LOC closure gates changed')
    require(root['overlay_path'] == str(loc_path) and root['overlay_sha256'] == LOC_SHA
            and root['body_terminal_sha256'] == LOC_TERMINAL_SHA, 'LOC closure linkage changed')
    require(all(type(root[k]) is int and root[k] == 0 for k in ('native_commands', 'count_replays', 'fixture_reexecutions', 'benchmark_runs')),
            'LOC closure execution declaration changed')
    terminal = resolver.read(loc_path.with_name('terminal.json'), LOC_TERMINAL_SHA)
    require(terminal['status'] == 'completed-Pony-LOC-metadata' and terminal['body_error'] is None
            and terminal['integrity_errors'] == [] and terminal['common_mutex_held'] is True, 'LOC terminal failed')
    resolver.absorb(terminal['available_evidence_pins'])
    resolver.absorb(root['new_repository_copies'])
    owner = OLD_ROOT / 'benchmarks/clbg/continuation/owned-jobs/pony-reviewed-loc-seal-v1'
    ended = resolver.read(owner / 'terminal.json', root['durable_terminal_sha256'])
    request = resolver.read(owner / 'request.json', root['request_sha256'])
    release = resolver.read(OLD_ROOT / 'benchmarks/clbg/continuation/jobs/pony-reviewed-loc-release-v1/release.json')
    started, worker = [resolver.read(owner / name) for name in ('command-started.json', 'worker-started.json')]
    require(ended['status'] == 'command-exited-zero-awaiting-report-review' and type(ended['exit_code']) is int
            and ended['exit_code'] == 0 and ended['stop_signals'] == [] and ended['actual_command_started'] is True
            and not ended.get('error'), 'LOC durable process failed')
    require(request['command'] == release['command'] and request['cwd'] == str(HOST), 'LOC command changed')
    require(all(item['command'] == request['command'] and item['cwd'] == str(HOST) for item in (started, worker)),
            'LOC process receipts disagree')
    require(ended['command_identity'] == started['command_identity'] and ended['worker_identity'] == worker['worker_identity'],
            'LOC process identity changed')
    require(ended['command_identity_observation_missing'] is started['command_identity_observation_missing'] is False,
            'LOC process identity missing')
    require(ended['automatic_retry'] is ended['qualification_granted'] is request['automatic_retry'] is request['qualification_granted'] is False,
            'LOC durable policy changed')
    require(loc['status'] == 'qualified-exact-source-LOC' and loc['canonical_LOC_admitted'] is True
            and loc['chart_admission'] is False and loc['profile_count'] == 20
            and loc['complete_authored_source_bundles'] is True and loc['unresolved'] == [], 'LOC proof incomplete')
    fixture_path = HOST_COHORT / 'work-qualification/private-v8-work-v2/fixtures/full-gates/full-gates-fixture-receipt.json'
    fixture = resolver.read(fixture_path, '21a39ab9e02a83a743a469bf7477b752b8bd305470fe54b56e1e495a4d3280b2')
    expected_tests = sorted('test_full_study.IsolatedFailures.' + name for name in (
        'test_real_source_failure_with_literal_safe_gates_is_isolated',
        'test_every_unsafe_gate_stops_and_truthy_values_do_not_waive_it',
        'test_missing_gates_and_non_source_failure_stop'))
    require(fixture['status'] == 'passed' and fixture['tests_run'] == 3 and fixture['actual_common_mutex_held'] is True,
            'Original isolated-failure fixtures are not qualified')
    require(all(sorted(fixture[k]) == expected_tests and len(fixture[k]) == 3
                for k in ('expected_ids', 'discovered_ids', 'started_ids')), 'Original fixture inventory changed')
    require(all(type(fixture[k]) is int and fixture[k] == 0 for k in
                ('failures', 'errors', 'skipped', 'expected_failures', 'unexpected_successes', 'native_probes')),
            'Original source-failure fixtures were not clean')
    resolver.bind(fixture['raw_log'], fixture['raw_log_sha256'])
    qualified = {row['id']: row for row in qualification['profiles']}
    reviewed = {row['id']: row for row in work['reviewed_sources']}
    require(set(qualified) == set(reviewed) == set(loc['profiles']) == set(loc['compiler_bound_input_inventory']),
            'Source/work/LOC cohorts differ')
    for row in suite['profiles']:
        require(Path(row['source']).is_relative_to(HOST) and Path(row['command'][0]).is_relative_to(HOST),
                'Measured paths must remain at the original host')
        require(resolver.bind(row['source'], row['source_sha256']) == Path(row['source']), 'Source path translated')
        require(resolver.bind(row['command'][0], row['binary_sha256']) == Path(row['command'][0]), 'Binary path translated')
        if row['language'] != 'pony':
            continue
        original, counted, inputs = qualified[row['id']], loc['profiles'][row['id']], loc['compiler_bound_input_inventory'][row['id']]
        require(all(row.get(field) == original.get(field) for field in
                    ('source', 'source_sha256', 'binary_sha256', 'command', 'cwd', 'runtime_environment')),
                'Pony execution changed')
        require(reviewed[row['id']]['source'] == row['source'] and reviewed[row['id']]['source_sha256'] == row['source_sha256'],
                'Source-work source changed')
        require(1 <= row['maximum_compute_actors'] <= 8 and row['command'][1:] == ['{n}', '--ponymaxthreads', '8'],
                'Pony worker limit changed')
        require(counted['source'] == row['source'] and counted['source_sha256'] == inputs['source_sha256'] == row['source_sha256']
                and inputs['binary_sha256'] == row['binary_sha256'], 'LOC is not bound to the scored binary')
        require(row['source_bundle'] == counted['source_bundle'] and row['compiler_bound_input_inventory'] == inputs,
                'Complete source inventory changed')
        require([(item['path'], item['sha256']) for item in counted['source_bundle']]
                == [(item['path'], item['sha256']) for item in inputs['files']], 'Counted package inventory changed')
        require(row['loc'] == counted['canonical_loc'] == sum(item['normalized_loc'] for item in counted['source_bundle'])
                and row['physical_loc'] == counted['physical_loc'] == sum(item['physical_loc'] for item in counted['source_bundle']),
                'Source count changed')
        require(all(type(counted[field]) is int and counted[field] > 0 for field in ('physical_loc', 'canonical_loc')),
                'Invalid source counts')
    return dict(source_work_profiles=20, bounded_cases_reused=155, canonical_loc_profiles=20,
                tree_allocation=tree_gate, new_native_probes=0, new_source_count_replays=0)


def schedule_for(suite, manifests):
    require(suite['benchmark_order'] == BENCHES and suite['samples'] == 3
            and suite['full_performance_runs_required'] == 90 and len(suite['profiles']) == 30, 'Suite shape changed')
    schedule = []
    for benchmark in BENCHES:
        manifest = manifests[benchmark]
        rows = manifest['profiles']
        require(len(rows) == 3 and {r['language'] for r in rows} == {'mech', 'pony'}, 'Benchmark cohort changed')
        identifiers = [row['id'] for row in rows]
        require(manifest['orders'] == [dict(round=i + 1, profiles=identifiers[i:] + identifiers[:i]) for i in range(3)],
                'Reviewed rotation changed')
        keys = {row['id']: row['key'] for row in rows}
        for order in manifest['orders']:
            schedule.extend((benchmark, order['round'], identifier, keys[identifier]) for identifier in order['profiles'])
    require(len(schedule) == len(set(schedule)) == 90, 'Duplicate schedule slots')
    return schedule


def validate_retained(resolver, terminal, guard, harness):
    before = resolver.read(RETAINED_STUDY / 'report.json', RETAINED_REPORT_SHA)
    require(terminal['report_sha256'] == RETAINED_REPORT_SHA and terminal['report'] == str(RETAINED_STUDY / 'report.json'),
            'Retained terminal/report linkage changed')
    require(terminal['status'] == 'failed-terminal-integrity' and terminal['common_mutex_held'] is True,
            'Unexpected recovery boundary')
    require((terminal['reused_completed_processes'], terminal['new_completed_processes'], terminal['full_performance_runs']) == (22, 32, 54),
            'Retained process inventory changed')
    require(terminal['repeated_completed_samples'] == terminal['compiler_invocations'] == terminal['fixture_reexecutions'] == 0
            and terminal['original_files_mutated'] is terminal['chart_admission'] is False, 'Retained execution scope changed')
    require(before['status'] == 'stopped' and before['active'] is None and before['error_type'] == 'FileNotFoundError'
            and before['error'] == "[Errno 2] No such file or directory: '" + str(OLD_ROOT / COHORT_REL / 'revisions/full90-retained-v1/full_study.py') + "'",
            'This controller admits only the reviewed relocation stop')
    require(len(terminal['integrity_errors']) == 76, 'Historical integrity failure inventory changed')
    for error in terminal['integrity_errors']:
        require(error['path'] in terminal['prerequisite_pins'] and error['error'].startswith('[Errno 2] No such file or directory:'),
                'Non-relocation integrity failure cannot be repaired here')
        resolver.bind(error['path'], terminal['prerequisite_pins'][error['path']])
    suite = resolver.read(OLD_STUDY / 'manifest.json', SUITE_SHA)
    require(before['manifest_sha256'] == SUITE_SHA and before['manifest'] == str(OLD_STUDY / 'manifest.json'), 'Retained suite changed')
    approved = resolver.read(OLD_ROOT / APPROVED_REL, APPROVED_SHA)
    require(approved['status'] == 'root-reviewed-exact-Pony20-Mech10-full90-manifests'
            and approved['manifest_sha256'] == SUITE_SHA and approved['benchmark_manifests'] == suite['benchmarks'],
            'Original exact suite review missing')
    require(approved['worker_sha256'] == CONTROL_PINS['full90-retained-v1/full_study.py']
            and approved['review_sha256'] == CONTROL_PINS['full90-retained-v1/REVIEW.md'], 'Original suite review linkage changed')
    resolver.absorb(suite['pins'])
    manifests = {bench: resolver.read(ref['path'], ref['sha256']) for bench, ref in suite['benchmarks'].items()}
    schedule = schedule_for(suite, manifests)
    initial = {row['key']: row for row in suite['profiles']}
    require(set(initial) == set(before['programs']) and len(initial) == 30, 'Retained profiles changed')
    first = resolver.read(OLD_STUDY / 'report.json', FIRST_REPORT_SHA)
    first_terminal = resolver.read(OLD_STUDY / 'terminal.json', FIRST_TERMINAL_SHA)
    require(first_terminal['status'] == first['status'] == 'stopped' and first_terminal['integrity_errors'] == [],
            'Initial retained boundary changed')
    require(first_terminal['report_sha256'] == FIRST_REPORT_SHA and len(first['attempts']) == 22
            and before['attempts'][:22] == first['attempts'], 'First 22 samples changed')
    require(before['full_performance_runs'] == len(before['attempts']) == 54
            and before['completed_benchmarks'] == BENCHES[:6], 'Expected exactly six completed workloads')
    for index, (attempt, slot) in enumerate(zip(before['attempts'], schedule), 1):
        benchmark, round_index, identifier, key = slot
        row, manifest = initial[key], manifests[benchmark]
        require((attempt['benchmark'], attempt['round'], attempt['id'], attempt['key']) == slot
                and attempt['attempt'] == index and attempt['qualified'] is True, 'Saved sample schedule changed')
        study = OLD_STUDY if index <= 22 else RETAINED_STUDY
        expected_result = study / 'attempts' / f'{index:03d}-{identifier}.json'
        require(attempt['result_path'] == str(expected_result)
                and attempt['supervisor_result_path'] == str(expected_result.with_suffix('.supervisor.json')),
                'Saved sample provenance path changed')
        raw = resolver.read(attempt['result_path'])
        supervisor = resolver.read(attempt['supervisor_result_path'])
        require(supervisor == attempt and all(attempt.get(k) == value for k, value in raw.items()),
                'Raw and supervised saved sample differ')
        checks = guard.qualification_checks(attempt, attempt['supervised_native_group'], manifest, row,
                                            attempt['sampler_wait_status'])
        require(checks == attempt['qualification_checks'] and all(value is True for value in checks.values()),
                'Saved sample fails frozen qualification')
        require(attempt['execution_fingerprint'] == harness.execution_fingerprint(row), 'Saved execution identity changed')
        require(type(attempt['seconds']) in (int, float) and attempt['seconds'] > 0, 'Invalid sample duration')
        require(not harness.group_members(attempt['supervised_native_group']['pgid']), 'Prior native group still exists')
    for key, row in before['programs'].items():
        require(harness.execution_fingerprint(row) == harness.execution_fingerprint(initial[key]), 'Saved program changed')
        require(all(row.get(field) == initial[key].get(field) for field in ('loc', 'physical_loc', 'source_bundle', 'compiler_bound_input_inventory')),
                'Saved source evidence changed')
        actual = [a for a in before['attempts'] if a['key'] == key]
        require(row['attempts'] == [a['attempt'] for a in actual]
                and row['samples_seconds'] == [a['seconds'] for a in actual]
                and row['sample_validation'] == [a['validation'] for a in actual] and not row.get('full_failure'),
                'Saved sample aggregate changed')
        if len(actual) == 3:
            require(row['median_seconds'] == statistics.median(row['samples_seconds'])
                    and row['sample_stdev_seconds'] == statistics.stdev(row['samples_seconds']), 'Saved statistics changed')
    listing = subprocess.run(['ps', '-axo', 'command='], capture_output=True, text=True, check=True).stdout.splitlines()
    require(not any(line == row['command'][0] or line.startswith(row['command'][0] + ' ')
                    for row in initial.values() for line in listing), 'A measured executable is already running')
    historical_controllers = [str(OLD_ROOT / COHORT_REL / 'revisions' / name)
                              for name in CONTROL_PINS if name.endswith('.py')]
    require(not any(path in line for path in historical_controllers for line in listing),
            'A historical timing controller is still running')
    return suite, manifests, schedule, before


@contextmanager
def common_lock():
    with LOCK.open('r+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        opened, named = os.fstat(lock.fileno()), LOCK.stat()
        require((opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino)
                and opened.st_ino == 79859134, 'Original common lock identity changed')
        yield lock


def verify_pins(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, ('Active pin changed', path))


def checked_runtime():
    require(sys.dont_write_bytecode and not sys.flags.optimize, 'Run Python with -I -S -B and without -O')
    require(sys.flags.isolated and sys.flags.no_site, 'Run Python with -I -S -B')
    require(Path(sys.executable).resolve() == PYTHON.resolve() and sha(PYTHON.resolve()) == PYTHON_SHA,
            'Original measurement Python changed')


def prepare(args):
    checked_runtime()
    require(not args.plan.exists() and not args.output.exists(), 'Plan and output must be new paths')
    with common_lock():
        resolver = Resolver(ROOT, args.retained_study, args.replacements)
        terminal_path = args.retained_study / 'terminal.json'
        require(sha(terminal_path) == args.retained_terminal_sha256, 'Retained terminal changed')
        terminal = json.loads(terminal_path.read_bytes())
        resolver.absorb(terminal['prerequisite_pins'])
        resolver.absorb(terminal['available_evidence_pins'])
        resolver.bind(RETAINED_STUDY / 'terminal.json', args.retained_terminal_sha256)
        guard, harness = load_measurement(resolver)
        suite, manifests, schedule, before = validate_retained(resolver, terminal, guard, harness)
        source_evidence = validate_source_evidence(resolver, suite, harness)
        additional = {str(Path(__file__).resolve()): sha(__file__), str(resolver.mapping_path): sha(resolver.mapping_path),
                      str(resolver.replacements_path): sha(resolver.replacements_path)}
        require(resolver.editorials_path.is_file() and len(resolver.editorials) == 11, 'Exact manifest editorial review required')
        additional[str(resolver.editorials_path)] = sha(resolver.editorials_path)
        pins = merge(resolver.active_pins, additional)
        guard.verify(pins)
        require(all(digest == resolver.logical_pins[path] for path, digest in suite['pins'].items()), 'Suite pins not covered')
        adapted = {}
        for bench, manifest in manifests.items():
            require(manifest['pins'] == suite['pins'], 'Benchmark pins differ from suite')
            require(manifest['size'] == harness.WORK[bench][1] and manifest['canonical_full_workload'] is True
                    and manifest['timeout_seconds'] == 14400 and manifest['maximum_rss_mib'] == 10240,
                    'Canonical workload or limits changed')
            adapted[bench] = {key: value for key, value in manifest.items() if key != 'pins'}
            adapted[bench]['original_manifest'] = suite['benchmarks'][bench]
        plan = dict(schema='pony-retained54-migration-plan-v1', status='verified-ready-for-explicit-execution',
            controller=str(Path(__file__).resolve()), controller_sha256=sha(__file__),
            repository=str(ROOT), retained_study=str(args.retained_study.resolve()),
            retained_terminal_sha256=args.retained_terminal_sha256,
            retained_report_sha256=RETAINED_REPORT_SHA, original_manifest_sha256=SUITE_SHA,
            replacements=str(resolver.replacements_path), replacements_sha256=sha(resolver.replacements_path),
            output=str(args.output.resolve()), source_evidence=source_evidence,
            retained_slots=schedule[:54], remaining_slots=schedule[54:],
            reused_completed_processes=54, new_process_slots=36, repeated_completed_samples=0,
            original_report=str(resolver.resolve(RETAINED_STUDY / 'report.json')),
            original_terminal=str(terminal_path.resolve()), original_files_mutated=False,
            pins=pins, historical_pins=resolver.logical_pins, path_reconciliation=resolver.relocations,
            manifests=adapted, chart_admission=False, runtime_publication_metadata_qualified=False,
            compiler_invocations=0, fixture_reexecutions=0, bounded_reexecutions=0, trace_reexecutions=0)
        new_json(args.plan, plan)
        print(json.dumps(dict(plan=str(args.plan), sha256=sha(args.plan), retained=54, remaining=36)), flush=True)


def isolated_failure(guard, attempt):
    safe = ('sampler_exited_normally', 'authoritative_native_group_received', 'native_inherited_common_mutex',
            'no_wrapper_integrity_error', 'no_resource_monitor_errors', 'no_compiler_power_monitor_errors',
            'no_monitor_finish_error', 'no_execute_cleanup_error', 'no_remaining_execute_group',
            'no_supervisor_cleanup', 'no_supervisor_remaining_group', 'valid_environment',
            'actual_full_workload', 'exact_command_and_group', 'pins_unchanged')
    return guard.benchmark_failure(attempt) and all(attempt.get('qualification_checks', {}).get(k) is True for k in safe)


def run(args):
    checked_runtime()
    require(sha(args.plan) == args.plan_sha256, 'Execution plan changed')
    plan = json.loads(args.plan.read_bytes())
    require(plan['schema'] == 'pony-retained54-migration-plan-v1' and plan['controller_sha256'] == sha(__file__)
            and plan['controller'] == str(Path(__file__).resolve()) and plan['repository'] == str(ROOT), 'Wrong controller or repository')
    output = Path(plan['output'])
    require(not output.exists(), 'Existing output requires a new reviewed recovery; never overwrite or automatically retry')
    output.parent.mkdir(parents=True, exist_ok=True)
    with ExitStack() as leases:
        # The durable suite lease also protects the verification-to-dispatch gap.
        lease_path = output.parent / 'pony-migrated-suite.owner.lock'
        lease = leases.enter_context(lease_path.open('a+'))
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require((os.fstat(lease.fileno()).st_dev, os.fstat(lease.fileno()).st_ino)
                == (lease_path.stat().st_dev, lease_path.stat().st_ino), 'Suite owner lock was replaced')
        original_work_lease = HOST_CLBG / 'continuation/owned-jobs/pony-reviewed-work-metadata-v1/owner.lock'
        work_lease = leases.enter_context(original_work_lease.open('rb'))
        fcntl.flock(work_lease, fcntl.LOCK_SH | fcntl.LOCK_NB)
        require((os.fstat(work_lease.fileno()).st_dev, os.fstat(work_lease.fileno()).st_ino)
                == (original_work_lease.stat().st_dev, original_work_lease.stat().st_ino), 'Original work lease changed')
        with common_lock():
            verify_pins(plan['pins'])
            resolver = Resolver(ROOT, plan['retained_study'], plan['replacements'])
            resolver.absorb(plan['historical_pins'])
            guard, harness = load_measurement(resolver)
            terminal = resolver.read(RETAINED_STUDY / 'terminal.json', plan['retained_terminal_sha256'])
            suite, original_manifests, schedule, before = validate_retained(resolver, terminal, guard, harness)
            source_evidence = validate_source_evidence(resolver, suite, harness)
            require(source_evidence == plan['source_evidence'] and [list(slot) for slot in schedule[54:]] == plan['remaining_slots'],
                    'Plan no longer matches retained evidence')
            for bench in BENCHES:
                expected = {key: value for key, value in original_manifests[bench].items() if key != 'pins'}
                expected['original_manifest'] = suite['benchmarks'][bench]
                require(plan['manifests'][bench] == expected, 'Adapted manifest changed more than path pins')
            output.mkdir()
            pins = merge(plan['pins'], {str(args.plan.resolve()): args.plan_sha256})
            manifests = {bench: dict(value, pins=pins) for bench, value in plan['manifests'].items()}
            report = copy.deepcopy(before)
            report.update(status='running', active=None, pins=pins, chart_admission=False,
                migration_plan=str(args.plan.resolve()), migration_plan_sha256=args.plan_sha256,
                retained_completed_processes=54, new_completed_processes=0,
                resumed_from=dict(report=plan['original_report'], report_sha256=RETAINED_REPORT_SHA,
                    terminal=plan['original_terminal'], terminal_sha256=plan['retained_terminal_sha256'],
                    reused_completed_processes=54, new_process_slots=36))
            report.pop('error', None)
            report.pop('error_type', None)
            guard.OUT, guard.REPORT = output, output / 'report.json'
            harness.install_interrupt_handlers()
            new_json(output / 'recovery.json', dict(plan=str(args.plan.resolve()), plan_sha256=args.plan_sha256,
                retained_slots=plan['retained_slots'], remaining_slots=plan['remaining_slots'],
                original_files_mutated=False, superseded_orchestration=resolver.replacements,
                path_reconciliation=resolver.relocations, retained_processes=54, new_process_slots=36,
                repeated_completed_samples=0, chart_admission=False))
            guard.save(guard.REPORT, report)
        try:
            for benchmark, round_index, identifier, key in schedule[54:]:
                row, manifest = report['programs'][key], manifests[benchmark]
                if row.get('full_failure'):
                    continue
                with common_lock() as lock:
                    harness.compact.wait_for_environment(harness.REQUIRED)
                    guard.verify(manifest['pins'])
                    print('PONY FULL', benchmark, round_index, identifier, manifest['size'], flush=True)
                    attempt = guard.one_attempt(harness, row, manifest, report, round_index, lock.fileno())
                    report['attempts'].append(attempt)
                    report['active'] = None
                    row['attempts'].append(attempt['attempt'])
                    report['full_performance_runs'] += 1
                    report['new_completed_processes'] += 1
                    if attempt['qualified']:
                        row['samples_seconds'].append(attempt['seconds'])
                        row['sample_validation'].append(attempt['validation'])
                        row.setdefault('full_validation', attempt['validation'])
                        row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
                    elif isolated_failure(guard, attempt):
                        row['measurement_status'], row['full_failure'] = 'failed', dict(attempt)
                    else:
                        row['measurement_status'] = 'failed-qualification'
                    guard.save(guard.REPORT, report)
                    require(attempt['qualified'] or row.get('full_failure'),
                            ('Integrity/environment/ownership failure; saved without retry', identifier, attempt.get('error')))
                    rows = [report['programs'][r['key']] for r in manifest['profiles']]
                    if all(len(r['samples_seconds']) == 3 or r.get('full_failure') for r in rows):
                        for r in rows:
                            if not r.get('full_failure'):
                                r.update(median_seconds=statistics.median(r['samples_seconds']),
                                    sample_stdev_seconds=statistics.stdev(r['samples_seconds']),
                                    qualification_status='three-canonical-processes-qualified-awaiting-independent-suite-and-runtime-publication-review')
                        if benchmark not in report['completed_benchmarks']:
                            report['completed_benchmarks'].append(benchmark)
                        guard.save(guard.REPORT, report)
            with common_lock():
                guard.verify(pins)
                require(report['attempts'][:54] == before['attempts'], 'Retained samples mutated')
                require(report['full_performance_runs'] == len(report['attempts']) == report['new_completed_processes'] + 54,
                        'Attempt accounting mismatch')
                require(len(report['completed_benchmarks']) == 10
                        and all(len(r['samples_seconds']) == 3 or r.get('full_failure') for r in report['programs'].values()),
                        'Suite did not finish')
                failures = [r['id'] for r in report['programs'].values() if r.get('full_failure')]
                if not failures:
                    require(len(report['attempts']) == 90 and report['new_completed_processes'] == 36, 'Incomplete successful suite')
                report.update(status='complete-with-failures' if failures else 'complete', pins_unchanged_at_end=True,
                              correctable_source_failures=failures, chart_admission=False)
        except BaseException as error:
            report.update(status='stopped', error=str(error) or type(error).__name__, error_type=type(error).__name__)
            raise
        finally:
            with common_lock():
                guard.save(guard.REPORT, report)
                errors = []
                for path, digest in pins.items():
                    try:
                        require(sha(path) == digest, 'Pinned bytes changed')
                    except BaseException as error:
                        errors.append(dict(path=path, error=str(error) or type(error).__name__))
                available = {str(path): sha(path) for path in output.rglob('*') if path.is_file()}
                new_json(output / 'terminal.json', dict(status='failed-terminal-integrity' if errors else report['status'],
                    report=str(guard.REPORT), report_sha256=sha(guard.REPORT), prerequisite_pins=pins,
                    available_evidence_pins=available, integrity_errors=errors, common_mutex_held=True,
                    reused_completed_processes=54, new_completed_processes=report['new_completed_processes'],
                    full_performance_runs=report['full_performance_runs'], repeated_completed_samples=0,
                    compiler_invocations=0, fixture_reexecutions=0, original_files_mutated=False, chart_admission=False))
                require(not errors, 'Terminal integrity failed; all attempts preserved')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest='mode', required=True)
    prep = modes.add_parser('prepare', help='Verify evidence and write a new plan without running benchmarks')
    prep.add_argument('--retained-study', type=Path, required=True)
    prep.add_argument('--retained-terminal-sha256', required=True)
    prep.add_argument('--replacements', type=Path, default=ROOT / 'experiments/pony/migration-resume-v1/orchestration-supersessions.json')
    prep.add_argument('--plan', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    execute = modes.add_parser('run', help='Execute only the 36 remaining slots in an exact prepared plan')
    execute.add_argument('--plan', type=Path, required=True)
    execute.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    (prepare if args.mode == 'prepare' else run)(args)


if __name__ == '__main__':
    main()
