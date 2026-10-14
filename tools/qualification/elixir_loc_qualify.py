#!/usr/bin/env python3
"""Qualify reviewed retained Elixir source counts; no native execution."""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/elixir/source-units-v1'
PLAN = ROOT/'experiments/elixir/source-counts-v1/plan-v1.json'
RUN = PLAN.parent/'run-v1'
REPLAY = PACKET/'replay-v2.json'
READER = ROOT/'tools/qualification/elixir_loc.py'
COUNTER = ROOT/'tools/qualification/elixir_source_units.py'
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
LOCK = Path('/tmp/mech-clbg-timing.lock')
LOCK_INODE = 79859134
PINS = {
    PLAN: 'f65ad1ee110f0dea5c4d20af4166752c2737eb06bccd964c08388896f709bad7',
    READER: '43b4014b5bc152a8725ab1c34ebbbd728d8dcf803edb85e8bf86d7f2d8c6a2b0',
    COUNTER: 'd1070e8f38fdebdfe2523c918bfb4367958667f34bf3c77efb6d6725544dc07f',
    REPLAY: '528add123d30b01dd0852cd299ab0738b7d75e551978eae62fa004b6fd08b096',
    PACKET/'review.md': '65f4407ece4c859fb54439fcd0078a920f1868b7e178e714ecb8304595ada773',
    PACKET/'fixture-contract.json': '50d60d1747e0ca1811dc8f8177a19ee00efa52d3c1f95f617f6d1760b939b4de',
    RUN/'report.json': '2e181c230e5ecfabe0c025782b9954ae5b78fcdaffa50c61596a2f5698b6625b',
    RUN/'terminal.json': 'f931ab6dd8fab02bafaacc1dfedf4755e2f00d370583298bc8e88780e60f917e',
    PLAN.parent/'owned-jobs/native-reader-v1/terminal.json':
        '952e053554da243e1ea9c050a894b7464c02685213aeed11197c3fcbe774e4d6',
    PYTHON: PYTHON_SHA,
}
# Independently reviewed (original physical, canonical, formatted physical).
EXPECTED = {
    'binarytrees': (78, 86, 96), 'fannkuchredux': (93, 105, 126),
    'fasta': (90, 100, 143), 'knucleotide': (93, 109, 119),
    'mandelbrot': (79, 87, 98), 'nbody': (114, 130, 186),
    'pidigits': (73, 81, 92), 'regexredux': (89, 101, 130),
    'revcomp': (80, 90, 100), 'spectralnorm': (80, 90, 99),
}
ROLES = {'application', 'application-helper', 'application-launcher'}


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def verify(pins):
    for path, digest in pins.items():
        require(sha(path) == digest, 'Pinned bytes changed: '+str(path))


def module(path, digest):
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'Reviewed helper changed: '+str(path))
    spec = importlib.util.spec_from_file_location('qualified_'+path.stem, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = result
    exec(compile(raw, str(path), 'exec'), result.__dict__)
    return result


@contextmanager
def common():
    with LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        verify_lock(lock)
        yield lock


def verify_lock(lock):
    opened, named = os.fstat(lock.fileno()), LOCK.stat()
    require((opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino)
            and opened.st_ino == LOCK_INODE, 'Common mutex changed')


def verify_artifact_closure(terminal):
    artifacts = terminal['artifacts']
    paths = list(RUN.rglob('*'))
    require(not any(p.is_symlink() or not (p.is_file() or p.is_dir()) for p in paths),
            'Unexpected native-reader artifact type')
    actual = {str(p.relative_to(RUN)) for p in paths if p.is_file()}
    require(actual == set(artifacts) | {'terminal.json'} and len(artifacts) == 372,
            'Reader artifact inventory differs')
    total = 0
    for name, evidence in artifacts.items():
        relative = Path(name)
        require(not relative.is_absolute() and '..' not in relative.parts, 'Unsafe artifact path')
        path = RUN/relative
        require(path.stat().st_size == evidence['bytes'] and sha(path) == evidence['sha256'],
                'Reader artifact changed: '+name)
        total += evidence['bytes']
    require(total == 7148218, 'Reader artifact byte total differs')
    return dict(files=len(artifacts), bytes=total, terminal=str(RUN/'terminal.json'))


def reviewed_counts(plan, replay):
    require(replay['status'] == 'candidate-replay-awaiting-owner-review' and
            replay['native_fixture_expectations_passed'] is True and
            len(replay['fixture_checks']) == 14 and all(c['passed'] is True for c in replay['fixture_checks']),
            'Native fixture expectations or replay status differ')
    inputs = {item['id']: item for item in plan['inputs']}
    require(len(inputs) == len(plan['inputs']) == 74, 'Reader input inventory differs')
    require({c['id'] for c in replay['fixture_checks']} ==
            {key for key, item in inputs.items() if item['kind'] == 'fixture'},
            'Native fixture identities differ')
    application = {key: item for key, item in inputs.items() if item['kind'] == 'application'}
    require(len(application) == 60 and len({i['path'] for i in application.values()}) == 60,
            'Expected sixty distinct authored inputs')
    wanted = {'elixir-'+bench+'-'+form for bench in EXPECTED for form in ('compact', 'optimized')}
    profiles = {p['id']: p for p in plan['profiles']}
    counted = {p['id']: p for p in replay['profiles']}
    require(len(profiles) == len(plan['profiles']) == len(counted) == len(replay['profiles']) == 20
            and set(profiles) == set(counted) == wanted, 'Expected twenty retained forms')
    files, bundles, used = {}, [], []
    for identity, profile in profiles.items():
        bench, form = profile['benchmark'], profile['variant']
        require(identity == 'elixir-'+bench+'-'+form and len(profile['inputs']) == 3
                and len(set(profile['inputs'])) == 3 and counted[identity]['inputs'] == profile['inputs'],
                'Profile identity or input membership differs')
        require(all(key in application for key in profile['inputs']) and
                {application[key]['role'] for key in profile['inputs']} == ROLES,
                'A counted source role is missing or replaced')
        rows = []
        for key in profile['inputs']:
            item, result = application[key], replay['files'][key]
            require(result['source_sha256'] == item['sha256'], 'Source-count identity differs')
            original, formatted = result['original'], result['formatted']
            require(original['diagnostics'] == formatted['diagnostics'] == [] and
                    all(type(n) is int and n > 0 for n in
                        (original['physical_loc'], original['normalized_loc'], formatted['physical_loc']))
                    and result['candidate_formatted_loc'] == formatted['physical_loc'],
                    'An authored count is ambiguous or invalid')
            directory = RUN/'reader'/key
            files[key] = dict(role=item['role'], source=item['path'], source_sha256=item['sha256'],
                retained_source=str(directory/'source.exs'), native_ast=str(directory/'ast.json'),
                formatted_source=str(directory/'formatted.exs'), formatted_ast=str(directory/'formatted-ast.json'),
                original_physical_loc=original['physical_loc'], canonical_loc=original['normalized_loc'],
                formatted_loc=formatted['physical_loc'], normalized_formatted_diagnostic=formatted['normalized_loc'])
            rows.append(files[key]); used.append(key)
        totals = tuple(sum(row[name] for row in rows) for name in
                       ('original_physical_loc', 'canonical_loc', 'formatted_loc'))
        require(totals == EXPECTED[bench] and counted[identity]['candidate_canonical_loc'] == totals[1],
                'Counts differ from the independent original-source review: '+identity)
        bundles.append(dict(id=identity, benchmark=bench, variant=form, inputs=profile['inputs'],
            original_physical_loc=totals[0], canonical_loc=totals[1], formatted_loc=totals[2],
            canonical_loc_qualified=True, formatted_loc_qualified=True,
            source_work_qualified=False, full_timings_qualified=False, chart_admission=False))
    require(len(used) == len(set(used)) == 60 and set(used) == set(application),
            'Authored files omitted or counted in multiple bundles')
    aliases = []
    for bench in EXPECTED:
        ids = ['elixir-'+bench+'-'+form for form in ('compact', 'optimized')]
        hashes = [{files[key]['role']: files[key]['source_sha256'] for key in profiles[i]['inputs']} for i in ids]
        require(hashes[0] == hashes[1], 'Retained equivalent-source pair differs: '+bench)
        aliases.append(dict(benchmark=bench, profiles=ids, source_hashes_by_role=hashes[0],
                            distinct_optimization_claimed=False))
    return files, bundles, aliases


def qualify(args, lock):
    require(not args.output.exists() and args.output.resolve().parent == PACKET,
            'Use a fresh output in the source-units packet')
    pins = dict(PINS)
    pins[Path(__file__).resolve()] = args.controller_sha256
    verify(pins)
    plan, terminal, report = read(PLAN), read(RUN/'terminal.json'), read(RUN/'report.json')
    require(plan['controller'] == str(READER) and plan['controller_sha256'] == PINS[READER]
            and plan['output'] == str(RUN), 'Wrong reviewed native-reader controller/output')
    for path, digest in plan['pins'].items():
        require(Path(path) not in pins or pins[Path(path)] == digest, 'Conflicting evidence pin')
        pins[Path(path)] = digest
    verify(pins)
    reader = module(READER, PINS[READER])
    counter = module(COUNTER, PINS[COUNTER])
    status = 'native-reader-complete-awaiting-canonical-owner-review'
    require(report['status'] == terminal['status'] == status
            and report['plan_sha256'] == PINS[PLAN] and terminal['report_sha256'] == PINS[RUN/'report.json']
            and report['native_reader_processes_started'] == 1 and terminal['common_mutex_held'] is True
            and terminal['common_mutex_inode'] == LOCK_INODE
            and all(terminal[k] == [] for k in ('integrity_errors', 'receipt_errors', 'artifact_errors'))
            and report['integrity_errors'] == report['receipt_errors'] == [], 'Native reader did not close cleanly')
    closure = verify_artifact_closure(terminal)
    native, receipt = read(RUN/'reader/report.json'), read(RUN/'source-reader.json')
    reader.validate_reader(native, plan)
    reader.validate_artifacts(native, plan, RUN/'reader')
    reader.validate_receipt(receipt)
    environment = dict(plan['runtime_environment'])
    environment.update(HOME=str(RUN/'home'), XDG_CONFIG_HOME=str(RUN/'config'),
                       TMPDIR=str(RUN/'tmp')+'/', ERL_CRASH_DUMP=str(RUN/'erl-crash.dump'))
    require(receipt['command'][:4] == [plan['runtime'], plan['reader'], str(PLAN), str(RUN/'reader')]
            and len(receipt['command']) == 5 and receipt['environment'] == environment
            and receipt['cwd'] == str(RUN), 'Wrong native source-reader command/environment')
    durable = read(PLAN.parent/'owned-jobs/native-reader-v1/terminal.json')
    require(durable['exit_code'] == 0 and durable['status'] == 'command-exited-zero-awaiting-report-review'
            and durable['command_pid'] == receipt['identity']['ppid'] and not durable.get('error'),
            'Durable reader command did not close cleanly')
    bounded_plan_path = reader.BOUNDED/'plan.json'
    bounded_report_path = reader.BOUNDED/'results-v1/report.json'
    bounded_terminal_path = reader.BOUNDED/'results-v1/terminal.json'
    bounded_plan, bounded_report, bounded_terminal = map(read,
        (bounded_plan_path, bounded_report_path, bounded_terminal_path))
    require(plan['bounded_plan_sha256'] == pins[bounded_plan_path]
            and plan['bounded_report_sha256'] == pins[bounded_report_path] == bounded_terminal['report_sha256']
            and bounded_report['qualified_bounded_cases'] == bounded_terminal['qualified_bounded_cases'] == 156
            and bounded_report['status'] == bounded_terminal['status'] ==
                'all20-bounded-output-passed-awaiting-compiled-work-and-LOC', 'Wrong retained bounded cohort')
    require({(p['id'], i['role'], i['path'], i['sha256'])
                for p in bounded_plan['profiles'] for i in p['physical_inputs'] if i['counted'] is True} ==
            {(p['id'], i['role'], i['path'], i['sha256'])
                for p in plan['profiles'] for i in plan['inputs'] if i['id'] in p['inputs']},
            'Reader source bundles differ from counted retained inputs')
    replay = read(REPLAY)
    require(counter.replay(PLAN, RUN/'reader') == replay, 'Saved replay is not reproducible')
    files, profiles, aliases = reviewed_counts(plan, replay)
    for row in files.values():
        row['artifact_bindings'] = {kind: terminal['artifacts'][str(Path(row[kind]).relative_to(RUN))]
            for kind in ('retained_source', 'native_ast', 'formatted_source', 'formatted_ast')}
    result = dict(schema='elixir-qualified-source-counts-v1', status='twenty-retained-source-counts-qualified',
        reviewed_at=datetime.now(timezone.utc).isoformat(), controller=str(Path(__file__).resolve()),
        controller_sha256=args.controller_sha256,
        evidence_pins={str(p): d for p, d in (PINS | {Path(__file__).resolve(): args.controller_sha256}).items()},
        source_plan=str(PLAN), source_plan_sha256=PINS[PLAN], verified_closure_pin_count=len(pins),
        native_artifact_closure=closure, rule_version=counter.RULE_VERSION, grammar=counter.GRAMMAR,
        reader_runtime=read(RUN/'reader/started.json'), formatter=native['formatter'],
        native_process_receipt=str(RUN/'source-reader.json'), original_native_reader_processes=1,
        bounded_prerequisite=dict(plan=str(bounded_plan_path), plan_sha256=plan['bounded_plan_sha256'],
            report=str(bounded_report_path), report_sha256=plan['bounded_report_sha256'],
            terminal=str(bounded_terminal_path), terminal_sha256=pins[bounded_terminal_path], qualified_cases=156),
        replay=str(REPLAY), review=str(PACKET/'review.md'), fixture_checks=replay['fixture_checks'],
        files=files, profiles=profiles, equivalent_source_pairs=aliases,
        canonical_loc_qualified=True, formatted_loc_qualified=True,
        source_work_qualified=False, full_timings_qualified=False, chart_admission=False,
        native_processes_started=0, subject_recompilations=0, subject_main_invocations=0,
        common_mutex_held=True, common_mutex_inode=LOCK_INODE, automatic_retry=False)
    # Recheck the exact closure after replay, before granting the source-only result.
    verify(pins)
    verify_artifact_closure(terminal)
    verify_lock(lock)
    reader.write(args.output, result)
    print(json.dumps(dict(output=str(args.output), sha256=sha(args.output), profiles=len(profiles),
                          canonical_loc_qualified=True, formatted_loc_qualified=True, chart_admission=False)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controller-sha256', required=True)
    parser.add_argument('--output', type=Path, default=PACKET/'qualified-source-counts.json')
    args = parser.parse_args()
    require(Path(sys.executable).resolve() == PYTHON.resolve() and sys.flags.isolated and sys.flags.no_site
            and sys.dont_write_bytecode and not sys.flags.optimize, 'Use pinned Python with -I -S -B')
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Source-count qualification interrupted: '+str(signum))
    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    with common() as lock:
        qualify(args, lock)


if __name__ == '__main__':
    main()
