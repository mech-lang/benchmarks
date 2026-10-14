#!/usr/bin/env python3
"""Observe retained Node and TypeScript versions under the common native mutex.

No package scripts, compiler inputs, source readers or benchmark mains run.
Version observations do not qualify the full Node runtime dependency closure.
"""
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'experiments/typescript/toolchain-v1'
RETENTION_SHA = '40fdd02167fa7cb5b2196255639bd28c0482b2a5e581746798f388b04d165810'
OBSERVER_SHA = 'c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc'
NODE = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node')
NODE_SHA = '27db838bb204ef7c21df2931f5656e4c8fb32e6e947f363a402b49714d32b5b1'


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    path = ROOT/'tools/qualification/kotlin_bounded_v2.py'
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == OBSERVER_SHA
    spec = importlib.util.spec_from_file_location('typescript_version_observer', path)
    observer = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), observer.__dict__)
    assert Path(sys.executable).resolve() == observer.kh.PYTHON.resolve()
    assert sha(sys.executable) == observer.kh.PYTHON_SHA and not sys.flags.optimize
    with observer.LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        observer.kh.verify_lock(lock)
        pins = {}
        def bind(path, expected):
            path = Path(path).resolve()
            assert sha(path) == expected, str(path)
            pins[str(path)] = expected
        receipt_path = BASE/'retained-packages-v1.json'
        bind(receipt_path, RETENTION_SHA)
        receipt = json.loads(receipt_path.read_text())
        assert len(receipt['packages']) == 4
        for package in receipt['packages']:
            directory = Path(package['installation_directory'])
            assert {str(p.relative_to(directory)) for p in directory.rglob('*') if p.is_file()} == set(package['files'])
            for relative, item in package['files'].items():
                p = directory/relative
                assert p.resolve().is_relative_to(directory) and p.stat().st_size == item['bytes']
                bind(p, item['sha256'])
            bind(package['archive'], package['archive_sha256'])
        bind(NODE, NODE_SHA)
        for p in (__file__, path, observer.kh.__file__, observer.eb.__file__, sys.executable):
            bind(p, sha(p))
        platform = next(p for p in receipt['packages'] if p['name'] == '@typescript/typescript-darwin-arm64')
        compiler = Path(platform['installation_directory'])/'lib/tsc'
        assert str(compiler) in pins
        output = BASE/'native-versions-v1'
        output.mkdir(exist_ok=False)
        report = dict(schema='typescript-native-versions-v1', status='running',
                      started_at=datetime.now(timezone.utc).isoformat(), pins=pins,
                      native_processes_started=0, observed_versions={}, subject_compilations=0,
                      source_reader_executions=0, subject_main_executions=0, benchmark_samples=0,
                      runtime_dependency_closure_qualified=False, chart_admission=False)
        observer.save(output/'report.json', report)
        try:
            for name, binary, expected in (('node', NODE, b'v24.19.0\n'), ('typescript', compiler, b'Version 7.0.2\n')):
                directory = output/name
                directory.mkdir()
                for child in ('home', 'tmp'):
                    (directory/child).mkdir()
                environment = dict(PATH='/usr/bin:/bin', HOME=str(directory/'home'),
                                   TMPDIR=str(directory/'tmp')+'/', LC_ALL='C', LANG='C', TZ='UTC', GOMAXPROCS='8')
                def launched(pid):
                    report['native_processes_started'] += 1
                    report['active'] = dict(id=name, pid=pid)
                    observer.save(output/'report.json', report)
                observer.observe([str(binary), '--version'], environment, directory, b'', lock, launched,
                                 kind='toolchain-version')
                actual = (directory/'stdout.bin').read_bytes()
                assert actual == expected, (name, actual)
                report['observed_versions'][name] = actual.decode().strip()
                report['active'] = None
            report['status'] = 'retained-node-and-typescript-versions-verified'
        except BaseException as error:
            report.update(status='failed', error=str(error) or type(error).__name__, error_type=type(error).__name__)
        finally:
            report['integrity_errors'] = []
            for path, expected in pins.items():
                try:
                    assert sha(path) == expected
                except BaseException as error:
                    report['integrity_errors'].append(dict(path=path, error=str(error)))
            if report['integrity_errors']:
                report['status'] = 'failed-input-integrity'
            report['finished_at'] = datetime.now(timezone.utc).isoformat()
            report['artifacts'] = {str(p.relative_to(output)):dict(sha256=sha(p), bytes=p.stat().st_size)
                                  for p in output.rglob('*') if p.is_file() and p != output/'report.json'}
            observer.save(output/'report.json', report)
            observer.save(output/'terminal.json', dict(status=report['status'], report_sha256=sha(output/'report.json'),
                                                      native_processes_started=report['native_processes_started']))
        print(json.dumps(dict(status=report['status'], observed_versions=report['observed_versions'],
                              report_sha256=sha(output/'report.json'))))
        return 0 if report['status'] == 'retained-node-and-typescript-versions-verified' else 1


if __name__ == '__main__':
    raise SystemExit(main())
