#!/usr/bin/env python3
"""Compile one revised reader and repeat the retained 80-input parser capture.

The original toolchain and source inputs are reused with their exact hashes.
This collects native evidence; it does not admit coverage or canonical counts.
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
HELPER_SHA = '74e2576e38d742824cb346e7ce812f26d1a6b8e88525623b786d2e9bc9e0718b'
PREVIOUS_SHA = 'a72690ad68a0b2b1d0947cbe010811411739789584f18a4040e6e2a6fb293ac9'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reader', type=Path, required=True)
    parser.add_argument('--reader-sha256', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    helper_path = ROOT/'tools/qualification/scala_toolchain.py'
    raw = helper_path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == HELPER_SHA
    spec = importlib.util.spec_from_file_location('scala_revision_helper', helper_path)
    helper = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(helper_path), 'exec'), helper.__dict__)
    observer = helper.load_observer()
    output, reader = args.output.resolve(), args.reader.resolve()
    helper.require(output.is_relative_to(BASE) and reader.is_relative_to(BASE)
                   and reader.is_file() and not output.exists(), 'Fresh Scala revision output required')
    with observer.LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        observer.kh.verify_lock(lock)
        pins = {}
        def bind(path, expected=None):
            path = Path(path).resolve()
            actual = helper.digest(path)
            helper.require(expected is None or actual == expected, 'Input changed: '+str(path))
            pins[str(path)] = actual
            return path
        previous_path = bind(BASE/'source-counts-v1/native-token-capture-v1/report.json', PREVIOUS_SHA)
        previous = json.loads(previous_path.read_text())
        helper.require(previous['status'] == 'eighty-source-transports-retained-awaiting-independent-review'
                       and len(previous['inputs']) == 80 and previous['integrity_errors'] == [],
                       'Original native inputs are incomplete')
        for path, expected in previous['pins'].items():
            bind(path, expected)
        for relative, item in previous['artifacts'].items():
            path = previous_path.parent/relative
            helper.require(path.resolve().is_relative_to(previous_path.parent), 'Unsafe prior artifact')
            bind(path, item['sha256'])
        bind(reader, args.reader_sha256)
        bind(__file__)
        helper.require(Path(sys.executable).resolve() == observer.kh.PYTHON.resolve() and
                       helper.digest(sys.executable) == observer.kh.PYTHON_SHA, 'Wrong controller runtime')
        toolchain = json.loads((BASE/'toolchain-v1/native-v1/report.json').read_text())
        helper.require(pins[str(BASE/'toolchain-v1/native-v1/report.json')] ==
                       helper.digest(BASE/'toolchain-v1/native-v1/report.json'), 'Toolchain binding differs')
        output.mkdir()
        report = dict(schema='scala-parser-revision-native-v1', status='running',
                      started_at=datetime.now(timezone.utc).isoformat(), pins=pins,
                      reader=str(reader), reader_sha256=args.reader_sha256, inputs=previous['inputs'],
                      native_processes_started=0, subject_main_executions=0, benchmark_samples=0,
                      coverage_qualified=False, canonical_loc=None, formatted_loc=None, chart_admission=False)
        observer.save(output/'report.json', report)
        classes = output/'compile/classes'
        dependencies = os.pathsep.join(toolchain['compiler_dependencies'])
        jobs = [('compile', ['-cp', toolchain['compiler_classpath'], 'dotty.tools.dotc.Main',
                    '-classpath', dependencies, '-encoding', 'UTF-8', '-color:never', '-d', str(classes), str(reader)]),
                ('reader', ['-cp', str(classes)+os.pathsep+toolchain['compiler_classpath'],
                    'benchmark.scala310tokencapture.SourceReader', dependencies,
                    str(output/'reader/parser-output')]+[r['source'] for r in previous['inputs']])]
        try:
            for name, arguments in jobs:
                directory = output/name
                directory.mkdir()
                for child in ('home', 'tmp', 'classes'):
                    (directory/child).mkdir()
                environment = dict(PATH='/usr/bin:/bin', HOME=str(directory/'home'),
                                   TMPDIR=str(directory/'tmp')+'/',
                                   JAVA_HOME=str(Path(toolchain['java']).parent.parent), LC_ALL='C', LANG='C', TZ='UTC')
                command = [toolchain['java'], '-XX:ActiveProcessorCount=8', '-Xms64m', '-Xmx1g', '-XX:+UseG1GC',
                           '-Duser.home='+environment['HOME'], '-Djava.io.tmpdir='+environment['TMPDIR']]+arguments
                def launched(pid):
                    report['native_processes_started'] += 1
                    report['active'] = dict(stage=name, pid=pid)
                    observer.save(output/'report.json', report)
                observer.observe(command, environment, directory, b'', lock, launched,
                                 kind='diagnostic-compile' if name == 'compile' else 'source-reader')
                helper.require((directory/'stdout.bin').read_bytes() == b'', 'Unexpected native stdout')
                report['active'] = None
                if name == 'compile':
                    generated = [p for p in classes.rglob('*') if p.is_file()]
                    helper.require(generated, 'Reader compilation produced no classes')
                    for path in generated:
                        bind(path)
                    observer.save(output/'report.json', report)
            report['results'] = []
            for row in previous['inputs']:
                path = output/'reader/parser-output'/f'{row["index"]:04d}.json'
                result = json.loads(path.read_text())
                helper.require(result['source_sha256'] == row['source_sha256'] and
                               result['source_path'] == row['source'], 'Revision input identity differs')
                report['results'].append(dict(id=row['id'], path=str(path), sha256=helper.digest(path),
                       stock_parser_parity=result['stock_parser_parity'],
                       candidate_coverage_complete=result['candidate_coverage_complete']))
            report['status'] = 'revised-eighty-source-transports-retained-awaiting-independent-review'
        except BaseException as error:
            report.update(status='failed', error=str(error) or type(error).__name__, error_type=type(error).__name__)
        finally:
            report['integrity_errors'] = []
            for path, expected in pins.items():
                try:
                    helper.require(helper.digest(path) == expected, 'Pinned input changed')
                except BaseException as error:
                    report['integrity_errors'].append(dict(path=path, error=str(error)))
            if report['integrity_errors']:
                report['status'] = 'failed-input-integrity'
            report['finished_at'] = datetime.now(timezone.utc).isoformat()
            report['artifacts'] = {str(p.relative_to(output)):dict(sha256=helper.digest(p), bytes=p.stat().st_size)
                                  for p in output.rglob('*') if p.is_file() and p != output/'report.json'}
            observer.save(output/'report.json', report)
            observer.save(output/'terminal.json', dict(status=report['status'], report_sha256=helper.digest(output/'report.json'),
                          native_processes_started=report['native_processes_started']))
        print(json.dumps(dict(status=report['status'], report=str(output/'report.json'),
                              sha256=helper.digest(output/'report.json'))))
        return 0 if report['status'].startswith('revised-eighty-source-') else 1


if __name__ == '__main__':
    raise SystemExit(main())
