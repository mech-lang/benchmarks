#!/usr/bin/env python3
"""Run the retained Scala parser candidate on 70 fixtures and ten sources.

Retains both stock and observed parser transports. Native completion and the
candidate's coverage claims remain separate from independent source-count
qualification. No benchmark main is compiled or executed by this command.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'experiments/scala'
TOOLCHAIN_SHA = '74e2576e38d742824cb346e7ce812f26d1a6b8e88525623b786d2e9bc9e0718b'
NATIVE_SHA = '600ff5668a7b1b76994213cdcaadb6b6cbd4026ce48204ef559f5928b7d84e39'
CONTRACTS = (
    ('owner', 'source-counts-v1/fixtures.json',
     '874dad522020c810beadbd6d019bd11a8d7378ea4226ba45e8df22db599c245d', 41),
    ('capture', 'source-counts-v1/candidate-token-capture-v1/fixtures.json',
     'aa075a277e52201f22e28aa5f44020d03b1b7b0d5a1b87e04468ab5bdf6435e0', 29),
)


def main():
    helper_path = ROOT/'tools/qualification/scala_toolchain.py'
    raw = helper_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == TOOLCHAIN_SHA
    spec = importlib.util.spec_from_file_location('scala_toolchain_helpers', helper_path)
    helper = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(helper_path), 'exec'), helper.__dict__)
    observer = helper.load_observer()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    helper.require(out.is_relative_to(BASE) and not out.exists(), 'Fresh Scala output required')
    with observer.LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        observer.kh.verify_lock(lock)
        pins = {}
        def bind(path, expected=None):
            path = Path(path).resolve()
            digest = helper.digest(path)
            helper.require(expected is None or digest == expected, 'Input changed: '+str(path))
            pins[str(path)] = digest
            return path
        native_path = bind(BASE/'toolchain-v1/native-v1/report.json', NATIVE_SHA)
        native = json.loads(native_path.read_text())
        helper.require(native['status'] == 'versions-and-readers-compiled-awaiting-parser-execution'
                       and native['native_processes_started'] == 4 and native['integrity_errors'] == [],
                       'Toolchain diagnostics did not complete')
        terminal = json.loads(bind(native_path.with_name('terminal.json')).read_text())
        helper.require(terminal['report_sha256'] == NATIVE_SHA, 'Toolchain terminal differs')
        for path, expected in native['pins'].items():
            bind(path, expected)
        for relative, item in native['artifacts'].items():
            path = native_path.parent/relative
            helper.require(path.resolve().is_relative_to(native_path.parent), 'Unsafe native artifact')
            bind(path, item['sha256'])
            helper.require(path.stat().st_size == item['bytes'], 'Native artifact size differs')
        bind(__file__)
        helper.require(Path(sys.executable).resolve() == observer.kh.PYTHON.resolve()
                       and helper.digest(sys.executable) == observer.kh.PYTHON_SHA,
                       'Unexpected controller runtime')
        rows = []
        for group, relative, expected, count in CONTRACTS:
            contract = json.loads(bind(BASE/relative, expected).read_text())
            helper.require(len(contract['fixtures']) == count, 'Fixture inventory differs')
            for case in contract['fixtures']:
                payload = case['text'].encode('utf8')
                digest = hashlib.sha256(payload).hexdigest()
                helper.require(case.get('source_sha256', digest) == digest, 'Fixture bytes differ')
                rows.append(dict(id=group+'-'+case['id'], group=group, contract=relative,
                                 source_sha256=digest, fixture=case))
        manifest = json.loads(bind(BASE/'source-v1/source-manifest.json',
                                  '03b26657e7e5fc189e02b193d222cd6a79bb721a7448af57865e40c349e9dbe1').read_text())
        helper.require(len(manifest['programs']) == 10, 'Ten applications required')
        for row in manifest['programs']:
            helper.require(len(row['sources']) == 1, 'Unexpected source bundle')
            source = row['sources'][0]
            path = bind(ROOT/source['path'], source['sha256'])
            rows.append(dict(id=row['id'], group='application', source=str(path),
                             source_sha256=source['sha256']))
        helper.require(len(rows) == 80 and len({r['id'] for r in rows}) == 80, 'Duplicate or missing source')
        out.mkdir()
        inputs = out/'inputs'
        inputs.mkdir()
        for index, row in enumerate(rows):
            if 'fixture' in row:
                path = inputs/(f'{index:04d}-'+row['id']+'.scala')
                path.write_bytes(row['fixture']['text'].encode('utf8'))
                row['source'] = str(bind(path, row['source_sha256']))
            row['index'] = index
        observer.save(out/'inputs.json', rows)
        bind(out/'inputs.json')
        directory = out/'native'
        directory.mkdir()
        for name in ('home', 'tmp'):
            (directory/name).mkdir()
        classes = native_path.parent/'compile-token-candidate/classes'
        classpath = str(classes)+os.pathsep+native['compiler_classpath']
        dependency_classpath = os.pathsep.join(native['compiler_dependencies'])
        environment = dict(PATH='/usr/bin:/bin', HOME=str(directory/'home'),
                           TMPDIR=str(directory/'tmp')+'/', JAVA_HOME=str(Path(native['java']).parent.parent),
                           LC_ALL='C', LANG='C', TZ='UTC')
        command = [native['java'], '-XX:ActiveProcessorCount=8', '-Xms64m', '-Xmx1g', '-XX:+UseG1GC',
                   '-Duser.home='+environment['HOME'], '-Djava.io.tmpdir='+environment['TMPDIR'],
                   '-cp', classpath, 'benchmark.scala310tokencapture.SourceReader', dependency_classpath,
                   str(directory/'parser-output')]+[r['source'] for r in rows]
        report = dict(schema='scala-parser-native-diagnostics-v1', status='running',
                      started_at=datetime.now(timezone.utc).isoformat(), pins=pins, inputs=rows,
                      native_processes_started=0, subject_main_executions=0, benchmark_samples=0,
                      native_fixture_transport_verified=False, physical_coverage_qualified=False,
                      canonical_loc=None, formatted_loc=None, chart_admission=False)
        observer.save(out/'report.json', report)
        try:
            def launched(pid):
                report.update(native_processes_started=1, native_pid=pid)
                observer.save(out/'report.json', report)
            observer.observe(command, environment, directory, b'', lock, launched, kind='source-reader')
            helper.require((directory/'stdout.bin').read_bytes() == b'', 'Unexpected reader stdout')
            report['results'] = []
            for row in rows:
                result_path = directory/'parser-output'/f'{row["index"]:04d}.json'
                result = json.loads(result_path.read_text())
                helper.require(result['source_sha256'] == row['source_sha256'] and
                               result['source_path'] == row['source'], 'Reader source identity differs')
                report['results'].append(dict(id=row['id'], path=str(result_path),
                        sha256=helper.digest(result_path), stock_parser_parity=result['stock_parser_parity'],
                        candidate_coverage_complete=result['candidate_coverage_complete']))
            report['status'] = 'eighty-source-transports-retained-awaiting-independent-review'
        except BaseException as error:
            report.update(status='failed', error=str(error) or type(error).__name__,
                          error_type=type(error).__name__)
        finally:
            report['integrity_errors'] = [path for path, value in pins.items() if helper.digest(path) != value]
            if report['integrity_errors']:
                report['status'] = 'failed-input-integrity'
            report['finished_at'] = datetime.now(timezone.utc).isoformat()
            report['artifacts'] = {str(p.relative_to(out)):dict(sha256=helper.digest(p), bytes=p.stat().st_size)
                                   for p in out.rglob('*') if p.is_file() and p != out/'report.json'}
            observer.save(out/'report.json', report)
            observer.save(out/'terminal.json', dict(status=report['status'], report_sha256=helper.digest(out/'report.json'),
                                                   native_processes_started=report['native_processes_started']))
        print(json.dumps(dict(status=report['status'], report=str(out/'report.json'),
                              sha256=helper.digest(out/'report.json'))))
        return 0 if report['status'].startswith('eighty-source-') else 1


if __name__ == '__main__':
    raise SystemExit(main())
