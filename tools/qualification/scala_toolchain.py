#!/usr/bin/env python3
"""Retain serial Scala toolchain and reader compilation diagnostics.

Uses the existing bounded native observer without changing its limits or raw
receipts. This does not execute benchmark mains or admit source counts/timings.
The output directory is exclusive; failed attempts remain available for review.
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
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/scala'
OBSERVER_SHA = 'c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc'
SELECTION_SHA = 'b10ab737d3b99c3a3d34c27f95b914a048fbc56779b6eeea5581b25351a82b26'
READERS = {
    'frozen': ('source-counts-v1/SourceReader.scala',
               'e199fd37269ef7fde8b1fd22414c28450172581719336b48a3f4fd3379c1f89c'),
    'token-candidate': ('source-counts-v1/candidate-token-capture-v1/SourceReader.scala',
                        'b786fb092aa62ed0df3d7bd5e32c3a55aa555eee07cd66fb963fb2ea39560bce'),
}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load_observer():
    path = ROOT / 'tools/qualification/kotlin_bounded_v2.py'
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == OBSERVER_SHA, 'Native observer changed')
    spec = importlib.util.spec_from_file_location('scala_bounded_observer', path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def manifest_dependencies(path, extraction):
    with zipfile.ZipFile(path) as archive:
        manifest = archive.read('META-INF/MANIFEST.MF').decode('utf8').replace('\r\n ', '')
    fields = dict(line.split(': ', 1) for line in manifest.splitlines() if ': ' in line)
    entries = fields['Class-Path'].split()
    dependencies = [(path.parent / entry).resolve() for entry in entries]
    require(len(dependencies) == len(set(dependencies)) and
            all(p.is_relative_to(extraction) and p.is_file() for p in dependencies),
            'Missing, duplicate or external compiler dependency')
    return dependencies


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    require(out.is_relative_to(BASE) and not out.exists(), 'Fresh Scala output directory required')
    observer = load_observer()
    require(Path(sys.executable).resolve() == observer.kh.PYTHON.resolve() and
            digest(sys.executable) == observer.kh.PYTHON_SHA, 'Unexpected Python runtime')
    with observer.LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        observer.kh.verify_lock(lock)
        pins = {}

        def bind(path, expected=None):
            path = Path(path).resolve()
            value = digest(path)
            require(expected is None or value == expected, 'Input changed: ' + str(path))
            pins[str(path)] = value
            return path

        selection = json.loads(bind(BASE/'toolchain-v1/selection.json', SELECTION_SHA).read_text())
        retention_path = bind(BASE/'toolchain-v1/retained-distribution-v1.json')
        retention = json.loads(retention_path.read_text())
        require(retention['archive_sha256'] == selection['compiler_archive_integrity']['expected_digest']
                and retention['symlinks'] == {}, 'Distribution identity differs')
        bind(retention['archive'], retention['archive_sha256'])
        extraction = Path(retention['extraction_root']).resolve()
        actual = {str(p.relative_to(extraction)) for p in extraction.rglob('*') if p.is_file()}
        require(actual == set(retention['files']), 'Distribution file inventory differs')
        for relative, item in retention['files'].items():
            path = bind(extraction/relative, item['sha256'])
            require(path.is_relative_to(extraction) and path.stat().st_size == item['bytes'],
                    'Distribution member size or location differs')
        distribution = extraction/'scala3-3.10.0-aarch64-apple-darwin'
        pathing = [distribution/'lib/scala.jar', distribution/'lib/with_compiler.jar']
        dependencies = list(dict.fromkeys(p for jar in pathing
                                         for p in manifest_dependencies(jar, extraction)))
        compiler_classpath = os.pathsep.join(str(p) for p in pathing)
        source_classpath = os.pathsep.join(str(p) for p in dependencies)
        historical_path = bind(ROOT/selection['runtime']['historical_receipt'])
        historical = json.loads(historical_path.read_text())
        java = Path(selection['runtime']['candidate'])
        java_home = java.parent.parent
        runtime_pins = {p:h for p,h in historical['pins'].items()
                        if Path(p).is_relative_to(java_home)}
        require(len(runtime_pins) == 400 and str(java) in runtime_pins,
                'Retained JDK input inventory differs')
        for path, value in runtime_pins.items():
            bind(path, value)
        for path in (__file__, observer.__file__, observer.kh.__file__, observer.eb.__file__, sys.executable):
            bind(path)
        for relative, value in READERS.values():
            bind(BASE/relative, value)

        out.mkdir()
        report = dict(schema='scala-toolchain-native-diagnostics-v1', status='running',
                      started_at=datetime.now(timezone.utc).isoformat(), pins=pins,
                      java=str(java), compiler_classpath=compiler_classpath,
                      compiler_dependencies=[str(p) for p in dependencies], commands=[],
                      native_processes_started=0, subject_main_executions=0, benchmark_samples=0,
                      canonical_loc=None, formatted_loc=None, chart_admission=False)
        observer.save(out/'report.json', report)
        flags = ['-XX:ActiveProcessorCount=8', '-Xms64m', '-Xmx1g', '-XX:+UseG1GC']
        jobs = [('java-version', ['--version']),
                ('scala-version', ['-cp', compiler_classpath, 'dotty.tools.dotc.Main', '-version'])]
        for name, (relative, _) in READERS.items():
            classes = out/('compile-'+name)/'classes'
            jobs.append(('compile-'+name, ['-cp', compiler_classpath, 'dotty.tools.dotc.Main',
                        '-classpath', source_classpath, '-encoding', 'UTF-8', '-color:never',
                        '-d', str(classes), str(BASE/relative)]))
        try:
            for name, arguments in jobs:
                directory = out/name
                directory.mkdir()
                for child in ('home', 'tmp', 'classes'):
                    (directory/child).mkdir()
                environment = dict(PATH='/usr/bin:/bin', HOME=str(directory/'home'),
                                   TMPDIR=str(directory/'tmp')+'/', JAVA_HOME=str(java_home),
                                   LC_ALL='C', LANG='C', TZ='UTC')
                command = [str(java)]+flags+['-Duser.home='+environment['HOME'],
                           '-Djava.io.tmpdir='+environment['TMPDIR']]+arguments
                def launched(pid):
                    report['native_processes_started'] += 1
                    report['active'] = dict(id=name, pid=pid)
                    observer.save(out/'report.json', report)
                record = observer.observe(command, environment, directory, b'', lock, launched,
                                          kind='diagnostic-compile' if name.startswith('compile-')
                                          else 'toolchain-version')
                report['commands'].append(dict(id=name, process=str(directory/'process.json'),
                                               process_sha256=digest(directory/'process.json')))
                report['active'] = None
                observer.save(out/'report.json', report)
            report['status'] = 'versions-and-readers-compiled-awaiting-parser-execution'
        except BaseException as error:
            report.update(status='failed', error=str(error) or type(error).__name__,
                          error_type=type(error).__name__)
        finally:
            report['integrity_errors'] = [path for path, value in pins.items() if digest(path) != value]
            if report['integrity_errors']:
                report['status'] = 'failed-input-integrity'
            report['finished_at'] = datetime.now(timezone.utc).isoformat()
            report['artifacts'] = {str(p.relative_to(out)):dict(sha256=digest(p), bytes=p.stat().st_size)
                                   for p in out.rglob('*') if p.is_file() and p != out/'report.json'}
            observer.save(out/'report.json', report)
            observer.save(out/'terminal.json', dict(status=report['status'], report_sha256=digest(out/'report.json'),
                          native_processes_started=report['native_processes_started'],
                          benchmark_samples=0, chart_admission=False))
        print(json.dumps(dict(status=report['status'], native_processes=report['native_processes_started'],
                              report=str(out/'report.json'), sha256=digest(out/'report.json'))))
        return 0 if report['status'].startswith('versions-and-readers-compiled-') else 1


if __name__ == '__main__':
    raise SystemExit(main())
