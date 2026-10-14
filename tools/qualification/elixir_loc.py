#!/usr/bin/env python3
"""Collect native source-reader evidence for the retained Elixir source bundles.

No source count is admitted by this command. Canonical owner accounting is a
separate review of these exact parser positions and source bytes.
"""
import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/elixir/source-counts-v1'
BOUNDED = ROOT/'experiments/elixir/bounded-work-v1'
PLAN_SHA = '4ca22a19e8c29b13764c20047c2230b73708189c0bb402c7cdb92fcb95b4e808'
REPORT_SHA = 'a7f2700bebd56df569478721fc254e93a2982e230d27862026dc88a38cfe06f2'
TERMINAL_SHA = 'b4e85ac05e86d25c2dc2b25a3243da2b43344f58e25ba50c95577c9d3f71f672'
SUPERVISOR = ROOT/'tools/qualification/rebol_sdk_supervisor.py'
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
LOCK = Path('/tmp/mech-clbg-timing.lock')
SIGNALS = {signal.SIGINT, signal.SIGTERM, signal.SIGHUP}


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())


def bind(path, expected, pins):
    path = Path(path)
    require(sha(path) == expected, 'Pinned input changed: '+str(path))
    require(str(path) not in pins or pins[str(path)] == expected, 'Conflicting pin: '+str(path))
    pins[str(path)] = expected
    return path


def read(path, expected, pins):
    return json.loads(bind(path, expected, pins).read_bytes())


@contextmanager
def common():
    with LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        opened, named = os.fstat(lock.fileno()), LOCK.stat()
        require((opened.st_dev, opened.st_ino) == (named.st_dev, named.st_ino)
                and opened.st_ino == 79859134, 'Common timing mutex changed')
        yield lock


def prepare(args):
    require(not args.plan.exists() and not args.output.exists(), 'Fresh plan/output paths required')
    require(not args.plan.resolve().is_relative_to(args.output.resolve()), 'Plan must be outside output')
    pins = {}
    bounded = read(BOUNDED/'plan.json', PLAN_SHA, pins)
    result = read(BOUNDED/'results-v1/report.json', REPORT_SHA, pins)
    terminal = read(BOUNDED/'results-v1/terminal.json', TERMINAL_SHA, pins)
    require(result['status'] == terminal['status'] ==
            'all20-bounded-output-passed-awaiting-compiled-work-and-LOC' and
            result['qualified_bounded_cases'] == terminal['qualified_bounded_cases'] == 156 and
            terminal['report_sha256'] == REPORT_SHA and terminal['integrity_errors'] ==
            terminal['artifact_errors'] == [], 'Completed retained cohort is required')
    for path, digest in bounded['pins'].items():
        bind(path, digest, pins)
    profiles = bounded['profiles']
    require(len(profiles) == len({p['id'] for p in profiles}) == 20, 'Expected twenty retained forms')
    inputs, bundles = [], []
    runtime = profiles[0]['command'][0]
    for row in profiles:
        require(row['command'][0] == runtime and len(row['physical_inputs']) == 3 and
                {p['role'] for p in row['physical_inputs']} ==
                {'application', 'application-helper', 'application-launcher'}, 'Incomplete source bundle')
        bundle = dict(id=row['id'], benchmark=row['benchmark'], variant=row['variant'], inputs=[])
        for item in row['physical_inputs']:
            require(item['counted'] is True, 'Authored input omitted from source count')
            bind(item['path'], item['sha256'], pins)
            key = row['id']+'--'+item['role']
            require(re.fullmatch(r'[a-z0-9-]+', key), 'Unsafe source artifact identifier')
            inputs.append(dict(id=key, kind='application', path=item['path'], sha256=item['sha256'],
                               role=item['role'], expected_parse='ok'))
            bundle['inputs'].append(key)
        bundles.append(bundle)
    require(len(inputs) == len({i['id'] for i in inputs}) == len({i['path'] for i in inputs}) == 60,
            'Expected sixty distinct physical authored inputs')
    fixtures = read(PACKET/'fixtures.json', sha(PACKET/'fixtures.json'), pins)
    require(len(fixtures) == len({f['id'] for f in fixtures}) == 14, 'Wrong fixture inventory')
    for fixture in fixtures:
        require(re.fullmatch(r'[a-z0-9-]+', fixture['id']) and fixture['expected_parse'] in ('ok', 'error'),
                'Invalid parser fixture')
        inputs.append(dict(fixture, id='fixture--'+fixture['id'], kind='fixture', path='fixture:'+fixture['id'],
                           sha256=hashlib.sha256(fixture['text'].encode()).hexdigest()))
    for path in (Path(__file__).resolve(), PACKET/'read_sources.exs', SUPERVISOR, PYTHON):
        bind(path, sha(path), pins)
    require(pins[str(PYTHON)] == PYTHON_SHA, 'Wrong measurement interpreter')
    require(str(runtime) in pins, 'Retained Elixir launcher is not pinned')
    plan = dict(schema='elixir-source-reader-plan-v1', status='prepared-awaiting-native-reader-execution',
                controller=str(Path(__file__).resolve()), controller_sha256=sha(__file__),
                bounded_plan_sha256=PLAN_SHA, bounded_report_sha256=REPORT_SHA,
                runtime=runtime, runtime_environment=profiles[0]['runtime_environment'],
                reader=str(PACKET/'read_sources.exs'), supervisor=str(SUPERVISOR),
                output=str(args.output.resolve()), profiles=bundles, inputs=inputs, pins=pins,
                native_reader_processes_planned=1, application_files=60, fixtures=14,
                subject_recompilations=0, subject_main_invocations=0, source_evaluations=0,
                timeout_seconds=300, cleanup_timeout_seconds=5, automatic_retry=False,
                canonical_loc=None, formatted_loc=None, chart_admission=False)
    args.plan.parent.mkdir(parents=True, exist_ok=True)
    write(args.plan, plan)
    print(json.dumps(dict(plan=str(args.plan), sha256=sha(args.plan), native_processes=0)), flush=True)


def validate_reader(report, plan):
    require(report['schema'] == 'elixir-native-source-reader-v1' and
            report['status'] == 'read-awaiting-canonical-owner-review' and
            report['application_files'] == 60 and report['fixture_files'] == 14 and
            report['source_evaluations'] == report['subject_recompilations'] ==
            report['subject_main_invocations'] == 0 and
            report['canonical_loc_qualified'] is report['formatted_loc_qualified'] is
            report['chart_admission'] is False, 'Unexpected reader result or admission claim')
    require(len(report['items']) == len(plan['inputs']) == 74, 'Incomplete source reader results')
    for actual, expected in zip(report['items'], plan['inputs']):
        require(actual['id'] == expected['id'] and actual['source_sha256'] == expected['sha256'],
                'Reader input identity differs')
        status = 'parsed-and-formatted' if expected['expected_parse'] == 'ok' else 'expected-parse-rejection'
        require(actual['status'] == status and actual['canonical_loc'] is actual['formatted_loc'] is None,
                'Unexpected parser outcome/count')
        if expected['expected_parse'] == 'ok':
            require(actual['semantic_ast_preserved'] is True, 'Formatter semantic comparison failed')


def validate_artifacts(report, plan, output):
    output = Path(output)
    expected_ids = {item['id'] for item in plan['inputs']}
    require({p.name for p in output.iterdir()} == expected_ids | {'started.json', 'report.json'},
            'Reader output inventory differs')
    require(not any(p.is_symlink() for p in output.rglob('*')), 'Reader output contains a symlink')
    for observed, item in zip(report['items'], plan['inputs']):
        directory = output/item['id']
        require(directory.is_dir(), 'Missing per-source reader directory')
        expected = {'source.exs', 'parse-error.json'} if item['expected_parse'] == 'error' else {
            'source.exs', 'ast.etf', 'ast.json', 'formatted.exs', 'formatted-ast.json'}
        require({p.name for p in directory.iterdir()} == expected and
                all((directory/name).is_file() for name in expected), 'Missing or unexpected reader artifacts')
        require(sha(directory/'source.exs') == item['sha256'], 'Retained source artifact changed')
        if item['expected_parse'] == 'ok':
            require(sha(directory/'formatted.exs') == observed['formatted_sha256'],
                    'Formatted artifact hash differs')
            etf = (directory/'ast.etf').read_bytes()
            require(len(etf) > 1 and etf[0] == 131, 'Missing native ETF term')
            for name in ('ast.json', 'formatted-ast.json'):
                ast = json.loads((directory/name).read_bytes())
                require(set(ast) == {'ast', 'comments'} and
                        all(isinstance(ast[k], list) and len(ast[k]) == 2 for k in ast),
                        'Malformed tagged AST artifact')
        else:
            error = json.loads((directory/'parse-error.json').read_bytes())
            require(set(error) == {'error'} and isinstance(error['error'], list) and len(error['error']) == 2,
                    'Missing retained parser error')


def validate_receipt(receipt):
    require(type(receipt.get('pid')) is int and receipt['pid'] > 0 and receipt['pgid'] == receipt['pid'] and
            receipt['exit_status'] == receipt['final_exit_status'] == 0 and receipt['direct_child_reaped'] is True and
            receipt['inherited_common_mutex'] is True and receipt['common_mutex_inode'] == 79859134 and
            receipt['remaining_process_group'] == [] and not any(receipt.get(k) for k in
                ('error', 'cleanup_errors', 'monitor_errors', 'stop_signals', 'remaining_after_cleanup')),
            'Reader native receipt is not a clean owned exit')


def run(args, lock):
    require(sha(args.plan) == args.plan_sha256, 'Reviewed plan changed')
    plan = json.loads(args.plan.read_bytes())
    require(plan['schema'] == 'elixir-source-reader-plan-v1' and
            plan['controller_sha256'] == sha(__file__) and plan['automatic_retry'] is False,
            'Unexpected source-reader plan')
    output = Path(plan['output'])
    require(not output.exists(), 'Fresh output required; no automatic retry')
    pins = dict(plan['pins'])
    bind(args.plan.resolve(), args.plan_sha256, pins)
    for path, digest in pins.items():
        require(sha(path) == digest, 'Preflight input changed: '+path)
    output.mkdir(parents=True)
    environment = dict(plan['runtime_environment'])
    for name, directory in [('HOME', 'home'), ('XDG_CONFIG_HOME', 'config'), ('TMPDIR', 'tmp')]:
        path = output/directory
        path.mkdir()
        environment[name] = str(path)+('/' if name == 'TMPDIR' else '')
    environment['ERL_CRASH_DUMP'] = str(output/'erl-crash.dump')
    supervisor_path = Path(plan['supervisor'])
    spec = importlib.util.spec_from_file_location('elixir_reader_supervisor', supervisor_path)
    supervisor = importlib.util.module_from_spec(spec)
    raw = supervisor_path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == pins[str(supervisor_path)], 'Supervisor changed')
    exec(compile(raw, str(supervisor_path), 'exec'), supervisor.__dict__)
    result = dict(schema='elixir-source-reader-results-v1', status='running',
                  started_at=datetime.now(timezone.utc).isoformat(), plan_sha256=args.plan_sha256,
                  native_reader_processes_started=0, canonical_loc=None, formatted_loc=None,
                  subject_recompilations=0, source_evaluations=0, chart_admission=False)
    write(output/'start.json', result)
    failure = None
    try:
        command = [plan['runtime'], plan['reader'], str(args.plan.resolve()), str(output/'reader'), str(lock.fileno())]
        supervisor.owned_command(command, environment, output, lock.fileno(), 300, 'source-reader', output)
        native = json.loads((output/'reader/report.json').read_bytes())
        validate_reader(native, plan)
        validate_artifacts(native, plan, output/'reader')
        validate_receipt(json.loads((output/'source-reader.json').read_bytes()))
        result.update(status='native-reader-complete-awaiting-canonical-owner-review',
                      application_files_read=60, grammar_fixtures_read=14)
    except BaseException as error:
        failure = error
        result.update(status='failed', error=str(error) or type(error).__name__, error_type=type(error).__name__)
    finally:
        with supervisor.atomic():
            receipt_errors = []
            receipt_path = output/'source-reader.json'
            try:
                receipt = json.loads(receipt_path.read_bytes())
                result['native_reader_processes_started'] = int(type(receipt.get('pid')) is int and receipt['pid'] > 0)
            except BaseException as error:
                receipt_errors.append(dict(path=str(receipt_path), error=str(error)))
            integrity_errors = []
            for path, digest in pins.items():
                try:
                    require(sha(path) == digest, 'Pinned input changed')
                except BaseException as error:
                    integrity_errors.append(dict(path=path, error=str(error)))
            result.update(finished_at=datetime.now(timezone.utc).isoformat(),
                          integrity_errors=integrity_errors, receipt_errors=receipt_errors)
            if integrity_errors or receipt_errors:
                result['status'] = 'failed-integrity-or-receipt'
            write(output/'report.json', result)
            artifacts, artifact_errors = {}, []
            for directory, _, files in os.walk(output, onerror=lambda error: artifact_errors.append(str(error))):
                for name in files:
                    path = Path(directory)/name
                    try:
                        require(not path.is_symlink(), 'Unexpected artifact symlink')
                        artifacts[str(path.relative_to(output))] = dict(sha256=sha(path), bytes=path.stat().st_size)
                    except BaseException as error:
                        artifact_errors.append(dict(path=str(path), error=str(error)))
            if artifact_errors:
                result.update(status='failed-artifact-retention', artifact_errors=artifact_errors)
                # This is the same attempt's final report, still under its mutex.
                # Preserve failed artifact paths even when the first scan lost a file.
                with (output/'report.json').open('w') as stream:
                    json.dump(result, stream, indent=2)
                    stream.write('\n')
                    stream.flush()
                    os.fsync(stream.fileno())
                artifacts['report.json'] = dict(sha256=sha(output/'report.json'), bytes=(output/'report.json').stat().st_size)
            write(output/'terminal.json', dict(status=result['status'],
                  report_sha256=sha(output/'report.json'), artifacts=artifacts, artifact_errors=artifact_errors,
                  integrity_errors=integrity_errors, receipt_errors=receipt_errors,
                  common_mutex_held=True, common_mutex_inode=79859134, chart_admission=False))
    if failure is not None:
        raise failure
    require(not integrity_errors and not receipt_errors and not artifact_errors, 'Reader evidence incomplete')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    preparation = commands.add_parser('prepare')
    preparation.add_argument('--plan', type=Path, required=True)
    preparation.add_argument('--output', type=Path, required=True)
    execution = commands.add_parser('run')
    execution.add_argument('--plan', type=Path, required=True)
    execution.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    require(Path(sys.executable).resolve() == PYTHON.resolve() and sys.flags.isolated and sys.flags.no_site
            and sys.dont_write_bytecode and not sys.flags.optimize, 'Use pinned Python with -I -S -B')
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Source reader interrupted: '+str(signum))
    for sig in SIGNALS:
        signal.signal(sig, interrupted)
    with common() as lock:
        if args.action == 'prepare':
            prepare(args)
        else:
            run(args, lock)


if __name__ == '__main__':
    main()
