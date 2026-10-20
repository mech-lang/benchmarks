"""Exact normal Nim frontend inputs plus unchanged retained owner-policy replay.

Not a native AST/logical-unit counter. compileOnly runs semantic compilation and
standard compile-time machinery, but no native backend or application process.
"""
import argparse
import copy
import fcntl
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
PACKET = HERE.parent
QUAL = PACKET / 'qualification-v1'
sys.path.insert(0, str(QUAL))
from native_process import atom, now, one, sha, success
sys.path.pop(0)

LOCK = Path('/tmp/mech-clbg-timing.lock')
BASE = ROOT / 'archive/validation/loc-normalization/20261012'
FIXTURE = BASE / 'jobs/boundary-audit-18/fixture-receipt.json'
FIXTURE_SHA = 'b00afe351c40fb38e03a99ec81fe3d71bd69a82726f337aa87dfb40cfcaa6b6a'
CANONICAL = BASE / 'clojure-grammar-v3/jobs/grammar-v3-source-replay-v1/grammar-dependencies/canonical.py'
PYGMENTS = ROOT / 'archive/qualification/nim/records/formatted-nim-plan-v1/jobs/actual-plans-v1/imports/pygments'
ADAPTER = BASE / 'nim-source-replay-v1/input_inventory.py'
ADAPTER_SHA = 'e5d38ea288b5dcfba2466bceb173b8d496e8e772ee5a2ff83a3f44f9eef590c1'
ADAPTER_FIXTURE = BASE / 'nim-source-replay-v1/jobs/fixtures-v1/fixture-receipt.json'
PARENT_COUNTS = ROOT / 'archive/languages/nim/20261012/source-counts/helper-owners-v2/jobs/exact-source20-loc-v2/source-counts.json'
RESTORATION = ROOT / 'experiments/nim/optimization-v1/runtime-restoration.json'
BUILD_REPORT = QUAL / 'attempt-v3/report.json'
EXPECTED = {'parent-compact': (35, 35), 'parent-parallel': (64, 71),
    'compact-reverse-guarded': (31, 31), 'parallel-guarded-copy': (65, 72),
    'parallel-reverse-guarded': (60, 67), 'parallel-byte-reverse': (60, 67)}


def require(value, message):
    if not value:
        raise ValueError(message)


def ref(path):
    path = Path(path).resolve()
    return dict(path=str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path), sha256=sha(path))


def load(path):
    return json.loads(Path(path).read_bytes())


def check(value):
    path = ROOT / value['path']
    require(path.is_file() and sha(path) == value['sha256'], 'Changed pinned file: ' + value['path'])
    return path


def module(name, path):
    require(name not in sys.modules, 'Unexpected preloaded counter/adapter module: ' + name)
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def make_plan(output):
    require(output.parent == HERE and not output.exists(), 'Exclusive new count-capture output required')
    fixture = load(FIXTURE)
    require(sha(FIXTURE) == FIXTURE_SHA and fixture['status'] == 'passed'
        and fixture['tests_run'] == 672 and fixture['failures'] == fixture['errors'] == 0,
        'Exact qualified 672-fixture lineage required')
    counter = {}
    for name in ['foreign_nim.py', 'foreign_core.py', 'foreign_future_mask.py', 'canonical.py']:
        original = CANONICAL if name == 'canonical.py' else BASE / name
        expected = [digest for path, digest in fixture['frozen_dependency_pins'].items()
            if path.endswith('/' + name)]
        require(len(expected) == 1 and sha(original) == expected[0], 'Qualified counter bytes differ: ' + name)
        counter[name] = ref(original)
    require(sha(PYGMENTS / '__init__.py') == fixture['pygments_module_sha256']
        == 'ff7513f3a4c6a47b96f057a4759f2e2e2744647d4d86670b88ecb628a34f0ade',
        'Exact retained Pygments package identity required')
    adapter_fixture = load(ADAPTER_FIXTURE)
    require(sha(ADAPTER) == ADAPTER_SHA and adapter_fixture['tests_run'] == 6
        and adapter_fixture['failures'] == adapter_fixture['errors'] == adapter_fixture['skipped'] == 0
        and ADAPTER_SHA in adapter_fixture['pins_before'].values(), 'Qualified frontend adapter lineage differs')
    report = load(BUILD_REPORT)
    require(report['status'] == 'PASSED-BOUNDED-WORK-PENDING-INDEPENDENT-CODE-REVIEW'
        and report['pins_unchanged'] is True and set(report['programs']) == set(EXPECTED),
        'Exact six-source normal native build report required')
    proposal = load(PACKET / 'plan.json')
    programs = {}
    for name, row in report['programs'].items():
        build = row['builds']['normal']
        require(check(row['source']).read_bytes() == check(build['source']).read_bytes()
            == check(build['native_source']).read_bytes(), 'Normal source aliases differ')
        ledger = proposal['candidates'][name]['source_count_proposal'] if name in proposal['candidates'] else None
        programs[name] = dict(source=row['source'], normal_source_snapshot=build['source'],
            original_normal_command=build['command'], proposed_ledger=ledger,
            expected_physical_and_retained=list(EXPECTED[name]), normal_library_only=True)
    pins = [ref(path) for path in [__file__, QUAL / 'native_process.py', FIXTURE, ADAPTER,
        ADAPTER_FIXTURE, PARENT_COUNTS, RESTORATION, BUILD_REPORT, PACKET / 'plan.json']]
    pins += list(counter.values())
    pins += [row['source'] for row in programs.values()]
    pins += [row['proposed_ledger'] for row in programs.values() if row['proposed_ledger'] is not None]
    pins += [ref(path) for path in sorted(PYGMENTS.rglob('*.py'))]
    for value in pins:
        check(value)
    return dict(schema='nim-fannkuch-frontend-owner-plan.v1', status='PREPARED',
        output=str(output), controller=ref(__file__), pins=pins, counter=counter,
        adapter=ref(ADAPTER), pygments_root=str(PYGMENTS), programs=programs,
        runtime=ref(RESTORATION), environment=load(QUAL / 'native-plan-v3.json')['environment'],
        python=dict(executable=ref(Path(sys.executable).resolve()), version=sys.version),
        common_mutex=str(LOCK), common_mutex_inode=LOCK.stat().st_ino,
        qualification_scope='Native-frontend-bound lexical/source-owner retained policy; not native AST or uniform logical units.',
        compile_only_scope='Semantic compilation and standard included compile-time/template processing; no native backend, linking or application process.',
        fixture_reuse='Original exact 672 counter and six frontend-adapter fixture receipts reused; not rerun or relabelled.',
        application_loc=None, independent_review_approved=False,
        chart_admission=False, original_sources_or_counters_modified=False)


def counter_metric(base, source, expected_module):
    """Observe the unchanged counter's actual statement decisions at return."""
    captured = []
    def observe(frame, event, value):
        if event == 'return' and frame.f_code.co_name == 'count_owned' and Path(frame.f_code.co_filename).resolve() == expected_module:
            captured.append(copy.deepcopy({key: frame.f_locals[key] for key in
                ['statements', 'physical', 'owned', 'by_line']}))
    require(sys.getprofile() is None, 'Unexpected existing Python profiling hook')
    sys.setprofile(observe)
    try:
        metric = base.normalize(source, 'nim')
    finally:
        sys.setprofile(None)
    require(len(captured) == 1 and metric['diagnostics'] == []
        and metric['review_status'] == 'candidate-parser-pass', 'Counter diagnostics or decision capture differ')
    return metric, captured[0]


def decision_ledger(source, metric, captured, lexer, comment_token, error_token):
    rows = source.splitlines(keepends=True)
    starts, cursor = [], 0
    for row in rows:
        starts.append(cursor)
        cursor += len(row)
    owners = []
    for event in metric['canonical_events']:
        owners.append(dict(id=len(owners), kind='qualified-canonical-event', **event))
    for number, statements in captured['statements'].items():
        for statement in statements:
            owners.append(dict(id=len(owners), kind='qualified-counter-statement',
                start=starts[number - 1] + statement['start_column'] - 1,
                end=min(len(source), starts[number - 1] + statement['end_column'] - 1),
                units=statement['units'], line=number, decision=statement))
    ledger = []
    for number, row in enumerate(rows, 1):
        events = [owner for owner in owners if owner['start'] < starts[number - 1] + len(row)
            and owner['end'] > starts[number - 1]]
        units = sum(event['units'] for event in captured['by_line'].get(number, []))
        units += sum(item['units'] for item in captured['statements'].get(number, []))
        if number in captured['physical'] and not units and number not in captured['owned']:
            raise ValueError('Implicit physical-row fallback has no explicit source owner')
        ledger.append(dict(line=number, source=row.rstrip('\r\n'), units=units,
            owner_ids=[event['id'] for event in events]))
    require(sum(row['units'] for row in ledger) == metric['normalized_loc'], 'Per-row owner total differs')
    tokens, unowned, overlaps = [], [], []
    covered = 0
    for offset, kind, text in lexer.get_tokens_unprocessed(source):
        require(offset == covered and source[offset:offset + len(text)] == text,
            'Pygments source-token spans are discontinuous or altered')
        covered += len(text)
        require(kind not in error_token, 'Pygments Nim token diagnostic')
        if kind in comment_token and kind not in comment_token.Preproc:
            continue
        significant = [offset + index for index, char in enumerate(text) if not char.isspace()]
        if not significant:
            continue
        owner_ids = set()
        for position in significant:
            found = [owner['id'] for owner in owners if owner['start'] <= position < owner['end']]
            if not found:
                unowned.append(position)
            if len(found) > 1:
                overlaps.append(position)
            owner_ids.update(found)
        tokens.append(dict(offset=offset, end=offset + len(text), token=str(kind),
            text=text, owner_ids=sorted(owner_ids)))
    require(covered == len(source) and not unowned and not overlaps,
        'Significant source token is unowned or multiply owned')
    return dict(owners=owners, line_ledger=ledger, significant_tokens=tokens,
        unowned_significant_offsets=unowned, overlapping_significant_offsets=overlaps,
        exact_source_coverage=True, all_units_from_unchanged_counter=True)


def run(plan_path, reviewed_sha):
    require(sha(plan_path) == reviewed_sha, 'Exact reviewed plan hash required')
    plan = load(plan_path)
    output = Path(plan['output'])
    with LOCK.open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        require(plan == make_plan(output) and os.fstat(lock.fileno()).st_ino == plan['common_mutex_inode'],
            'Capture plan or common mutex identity changed')
        inherited = fcntl.fcntl(lock.fileno(), fcntl.F_DUPFD, 64)
        output.mkdir()
        report = dict(schema='nim-fannkuch-frontend-owner-capture.v1', status='RUNNING',
            plan=ref(plan_path), controller=ref(__file__), started_utc=now(), active=None,
            profiles={}, common_mutex_inode=plan['common_mutex_inode'],
            scope=plan['qualification_scope'], application_loc=None,
            independent_review_approved=False, native_backend_compilations=0,
            application_processes=0, chart_admission=False)
        atom(output / 'report.json', report)
        try:
            restored = load(RESTORATION)
            distribution = Path(restored['distribution'])
            require(len(restored['checked_distribution_pins']) == 6770, 'Exact restored tree required')
            for relative, digest in restored['checked_distribution_pins'].items():
                require(sha(distribution / relative) == digest, 'Restored compiler tree changed')
            counter = output / 'counter-snapshot'
            counter.mkdir()
            for name, value in plan['counter'].items():
                shutil.copyfile(check(value), counter / name)
                (counter / name).chmod(0o444)
            adapter = module('qualified_nim_input_inventory', check(plan['adapter']))
            require(not any(name in sys.modules for name in ['foreign_nim', 'foreign_core', 'foreign_future_mask', 'canonical', 'pygments']),
                'Unexpected preloaded counter or lexer')
            sys.path[:0] = [str(counter), str(PYGMENTS.parent)]
            base = importlib.import_module('foreign_nim')
            lexical = importlib.import_module('pygments')
            require(lexical.__version__ == '2.19.2' and Path(lexical.__file__).resolve() == PYGMENTS / '__init__.py',
                'Unexpected lexer package loaded')
            for name in plan['counter']:
                require(Path(sys.modules[Path(name).stem].__file__).resolve() == counter / name,
                    'Unexpected counter dependency loaded')
            from pygments.lexers import get_lexer_by_name
            from pygments.token import Comment, Error
            lexer = get_lexer_by_name('nim', stripnl=False, ensurenl=False, tabsize=0)
            prior_counts = load(PARENT_COUNTS)['source_counts']
            for name, descriptor in plan['programs'].items():
                report['active'] = name
                atom(output / 'report.json', report)
                original = check(descriptor['source'])
                folder = output / 'frontend' / name
                folder.mkdir(parents=True)
                source = folder / 'fannkuch.nim'
                shutil.copyfile(original, source)
                require(source.read_bytes() == original.read_bytes(), 'Exact input copy differs')
                normal = list(descriptor['original_normal_command'])
                normal[-1] = str(source)
                never_binary, cache = folder / 'never-scored-binary', folder / 'cache'
                command = adapter.audit_command(normal, cache, never_binary)
                process = one(command, folder / 'process', plan['environment'], ROOT, inherited, timeout=90)
                success(process)
                stderr = Path(process['stderr']['path']).read_text()
                require(not re.search(r'\b(?:warning|error):', stderr, re.IGNORECASE), 'Unreviewed frontend diagnostic')
                require(not never_binary.exists() and not list(folder.rglob('*.o')),
                    'compileOnly unexpectedly produced native code')
                vendor_roots = [Path(value.split(':', 1)[1]) for value in command if value.startswith(('--lib:', '--path:'))]
                inventory = adapter.processing_inputs(stderr, source, [], vendor_roots)
                for row in inventory['files']:
                    path = Path(row['path'])
                    row['sha256'] = sha(path)
                    if row['counted']:
                        require(path == source and sha(path) == descriptor['source']['sha256'], 'Authored input inventory differs')
                    else:
                        relative = str(path.relative_to(distribution))
                        require(row['sha256'] == restored['checked_distribution_pins'][relative],
                            'Normal compiler loaded an unpinned general/vendor source')
                metric, decisions = counter_metric(base, source.read_text(), counter / 'foreign_core.py')
                require([metric['physical_loc'], metric['normalized_loc']] == descriptor['expected_physical_and_retained'],
                    'Actual counter result differs from source proposal')
                owner_ledger = decision_ledger(source.read_text(), metric, decisions, lexer, Comment, Error)
                if name.startswith('parent-'):
                    parent_file = 'compact.nim' if name == 'parent-compact' else 'optimized.nim'
                    saved = [value for path, value in prior_counts.items()
                        if path.endswith('/fannkuchredux/' + parent_file)]
                    require(len(saved) == 1 and metric == saved[0]['metric'],
                        'Complete historical parent metric/events changed')
                    reconciliation = 'Complete historical metric and event arrays match exactly.'
                else:
                    proposed = load(check(descriptor['proposed_ledger']))
                    require(proposed['source_sha256'] == descriptor['source']['sha256']
                        and len(proposed['line_ledger']) == len(owner_ledger['line_ledger']), 'Proposal source/rows differ')
                    for actual, prior in zip(owner_ledger['line_ledger'], proposed['line_ledger']):
                        require(actual['line'] == prior['line'] and actual['source'] == prior['source']
                            and actual['units'] == prior['retained_rule_proposed_units'], 'Per-file source-owner decision differs')
                    reconciliation = 'Every proposed row and owner-unit decision matches the unchanged qualified counter.'
                inventory_path = folder / 'compiler-input-inventory.json'
                atom(inventory_path, inventory)
                counted = dict(schema='nim-exact-source-owner-capture.v1', source=descriptor['source'],
                    compiler_input=ref(source), frontend_inventory=ref(inventory_path),
                    frontend_process=ref(folder / 'process/process.json'), metric=metric,
                    **owner_ledger, reconciliation=reconciliation, application_loc=None,
                    independent_review_approved=False, native_ast_claim=False,
                    uniform_logical_metric_claim=False, native_frontend_bound=True)
                counted_path = output / (name + '-counts.json')
                atom(counted_path, counted)
                report['profiles'][name] = dict(source=descriptor['source'], physical_loc=metric['physical_loc'],
                    retained_policy_count=metric['normalized_loc'], counts=ref(counted_path),
                    frontend_inventory=ref(inventory_path), frontend_process=ref(folder / 'process/process.json'),
                    diagnostics=[], unowned_significant_tokens=0, application_loc=None)
                atom(output / 'report.json', report)
            imports = []
            for name, value in sorted(sys.modules.items()):
                filename = getattr(value, '__file__', None)
                if filename is None or not str(filename).endswith('.py'):
                    continue
                path = Path(filename).resolve()
                if path.is_relative_to(counter) or path.is_relative_to(PYGMENTS):
                    imports.append(dict(module=name, **ref(path)))
            for value in plan['pins']:
                check(value)
            for relative, digest in restored['checked_distribution_pins'].items():
                require(sha(distribution / relative) == digest, 'Compiler tree changed during capture')
            report.update(status='CAPTURED-ZERO-DIAGNOSTICS-PENDING-INDEPENDENT-REVIEW',
                active=None, finished_utc=now(), imported_counter_lexer_closure=imports,
                frontend_commands=6, exact_authored_sources=6, pins_unchanged=True,
                original_counter_and_helpers_changed=False, constant_monkeypatching=False,
                native_ast_claim=False, uniform_logical_metric_claim=False,
                compile_only_scope=plan['compile_only_scope'], fixture_lineage_reused=True)
        except BaseException as error:
            report.update(status='FAILED', error=repr(error), finished_utc=now())
            raise
        finally:
            atom(output / 'report.json', report)
            os.close(inherited)
    print(report['status'], len(report['profiles']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--plan', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--reviewed-plan-sha256')
    args = parser.parse_args()
    if args.prepare:
        require(args.output is not None and not args.plan.exists(), 'Fresh plan/output required')
        with LOCK.open('a+') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            atom(args.plan, make_plan(args.output.resolve()))
        print(sha(args.plan))
    else:
        require(args.reviewed_plan_sha256 is not None, 'Reviewed plan digest required')
        run(args.plan.resolve(), args.reviewed_plan_sha256)
