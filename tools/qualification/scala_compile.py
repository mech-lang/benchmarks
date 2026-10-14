#!/usr/bin/env python3
"""Compile ten retained Scala applications and retain every emitted class.

Compilation and javap inspection run serially through the frozen bounded native
observer. No application main is called, and no timing or source count is admitted.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import signal
import sys
import types
import zipfile

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'experiments/scala'
PACKET = BASE / 'compiled-applications-v1'
HELPER = ROOT / 'tools/qualification/scala_toolchain.py'
HELPER_SHA = '74e2576e38d742824cb346e7ce812f26d1a6b8e88525623b786d2e9bc9e0718b'
TOOLCHAIN = BASE / 'toolchain-v1/native-v1/report.json'
TOOLCHAIN_SHA = '600ff5668a7b1b76994213cdcaadb6b6cbd4026ce48204ef559f5928b7d84e39'
SOURCES = BASE / 'source-v1/source-manifest.json'
SOURCES_SHA = '03b26657e7e5fc189e02b193d222cd6a79bb721a7448af57865e40c349e9dbe1'
BENCHES = {'binarytrees', 'fannkuchredux', 'fasta', 'knucleotide', 'mandelbrot',
           'nbody', 'pidigits', 'regexredux', 'revcomp', 'spectralnorm'}
FLAGS = ['-XX:ActiveProcessorCount=8', '-Xms64m', '-Xmx1g', '-XX:+UseG1GC']


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def load_helper():
    raw = HELPER.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == HELPER_SHA, 'Frozen Scala helper changed')
    module = types.ModuleType('scala_application_toolchain')
    module.__file__ = str(HELPER)
    exec(compile(raw, str(HELPER), 'exec'), module.__dict__)
    return module


def source_rows(document):
    rows = document['programs']
    require(document['schema'] == 'scala-source-draft-manifest-v1' and len(rows) == 10
            and {r['benchmark'] for r in rows} == BENCHES, 'Exactly ten Scala source bundles required')
    for row in rows:
        bench = row['benchmark']
        require(row['id'] == 'scala-'+bench+'-jvm-v1' and row['language'] == 'scala'
                and row['variant'] == 'jvm' and len(row['sources']) == 1,
                'Unexpected Scala source profile')
        source = row['sources'][0]
        require(source['path'] == 'experiments/scala/source-v1/'+bench+'/Main.scala'
                and source['role'] == 'application' and type(source['bytes']) is int
                and source['bytes'] > 0, 'Source location, role or size differs')
    return rows


def runtime_jars(dependencies):
    names = ('scala3-library_3-3.10.0.jar', 'scala-library-3.10.0.jar')
    result = []
    for name in names:
        matches = [Path(p) for p in dependencies if Path(p).name == name]
        require(len(matches) == 1, 'Missing or ambiguous Scala runtime library: '+name)
        result.extend(matches)
    require(len(set(result)) == 2, 'Repeated Scala runtime library')
    return result


def class_inventory(directory):
    require(directory.is_dir() and not directory.is_symlink(), 'Missing or linked class directory')
    files = []
    for path in sorted(directory.rglob('*')):
        require(not path.is_symlink(), 'Linked generated artifact')
        require(path.is_dir() or path.is_file(), 'Nonregular generated artifact')
        if not path.is_file():
            continue
        relative = path.relative_to(directory).as_posix()
        require(path.suffix in ('.class', '.tasty'), 'Unexpected compiler output: '+relative)
        raw = path.read_bytes()
        if path.suffix == '.class':
            require(raw.startswith(b'\xca\xfe\xba\xbe') and len(raw) >= 10,
                    'Invalid class file: '+relative)
        files.append(dict(path=str(path), relative_path=relative,
                          sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw)))
    names = {r['relative_path'] for r in files}
    require({'Main.class', 'Main$.class', 'Main.tasty'} <= names,
            'Compiler did not emit the direct main, module and TASTy owners')
    return files


def closed_process(record, command, environment, directory):
    require(record['status'] == 'native-passed' and record['native_process_started'] is True
            and record['command'] == command and record['environment'] == environment
            and record['cwd'] == str(directory) and record['exit_status'] == 0
            and record['direct_child_reaped'] is True and record['remaining_process_group'] == []
            and record['cleanup_errors'] == [] and record['stop_signals'] == []
            and record.get('artifact_errors', []) == [] and record['stderr_bytes'] == 0
            and record['stdin_bytes'] == 0 and record['inherited_common_mutex'] is True
            and record['common_mutex_inode'] == 79859134, 'Native compilation/inspection did not close cleanly')
    for name in ('stdout', 'stderr'):
        raw = (directory/(name+'.bin')).read_bytes()
        require(len(raw) == record[name+'_bytes']
                and hashlib.sha256(raw).hexdigest() == record[name+'_sha256'],
                'Observed native stream changed: '+name)
    require(json.loads((directory/'process.json').read_bytes()) == record, 'Observed process receipt changed')


def artifact_inventory(directory):
    result = {}
    for path in sorted(directory.rglob('*')):
        require(not path.is_symlink() and (path.is_file() or path.is_dir()),
                'Linked or nonregular output artifact')
        if path.is_file() and path != directory/'report.json':
            raw = path.read_bytes()
            result[path.relative_to(directory).as_posix()] = dict(
                sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw))
    return result


def close_artifact_inventory(output, inventory, pins, saved, profiles):
    """Bind the final inventory back to already validated native evidence."""
    require(not ('terminal.json' in inventory), 'Unexpected pre-existing terminal artifact')
    for path, digest in {**pins, **saved}.items():
        path = Path(path)
        if path.is_relative_to(output):
            item = inventory.get(path.relative_to(output).as_posix())
            require(item is not None and item['sha256'] == digest,
                    'Final inventory differs from validated output: '+str(path))
    for profile in profiles:
        if 'artifacts' not in profile:
            continue  # A failed compiler has no successful class-inventory claim.
        classes = Path(profile['source']).parent/'classes'
        require(class_inventory(classes) == profile['artifacts'],
                'Final emitted class inventory differs from bytecode inspection')
        for item in profile['artifacts']:
            final = inventory[Path(item['path']).relative_to(output).as_posix()]
            require(final == {k:item[k] for k in ('sha256', 'bytes')},
                    'Final inventory changed an inspected class')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(PACKET) and output != PACKET and not output.exists(),
            'Fresh output beneath the Scala compilation packet required')
    require(sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
            and not sys.flags.optimize, 'Use isolated Python with -I -S -B and no -O')
    helper = load_helper()
    observer = helper.load_observer()
    require(Path(sys.executable).resolve() == observer.kh.PYTHON.resolve(), 'Unexpected Python runtime')

    def interrupted(signum, frame):
        raise KeyboardInterrupt('Scala compilation interrupted: '+str(signum))

    for sig in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(sig, interrupted)
    with observer.LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        observer.kh.verify_lock(lock)
        require(sha(sys.executable) == observer.kh.PYTHON_SHA, 'Unexpected Python runtime bytes')
        pins = {}

        def bind(path, expected=None):
            path = Path(path)
            require(path.is_absolute() and path.resolve() == path and path.is_file(),
                    'Noncanonical input path: '+str(path))
            digest = sha(path)
            require(expected is None or digest == expected, 'Pinned input changed: '+str(path))
            require(str(path) not in pins or pins[str(path)] == digest, 'Conflicting input pin')
            pins[str(path)] = digest
            return path

        toolchain = json.loads(bind(TOOLCHAIN, TOOLCHAIN_SHA).read_bytes())
        require(toolchain['status'] == 'versions-and-readers-compiled-awaiting-parser-execution'
                and toolchain['native_processes_started'] == 4
                and toolchain['integrity_errors'] == [], 'Verified Scala toolchain required')
        for path, digest in toolchain['pins'].items():
            bind(path, digest)
        rows = source_rows(json.loads(bind(SOURCES, SOURCES_SHA).read_bytes()))
        for row in rows:
            src = row['sources'][0]
            source = bind(ROOT/src['path'], src['sha256'])
            require(source.stat().st_size == src['bytes'], 'Source size changed')
        for path in (Path(__file__).resolve(), HELPER, Path(observer.__file__).resolve(),
                     Path(observer.kh.__file__).resolve(), Path(observer.eb.__file__).resolve(),
                     Path(sys.executable).resolve()):
            bind(path)
        libraries = runtime_jars(toolchain['compiler_dependencies'])
        for jar in libraries:
            require(str(jar) in pins, 'Runtime library lacks retained toolchain binding')
            with zipfile.ZipFile(jar) as archive:
                manifest = archive.read('META-INF/MANIFEST.MF').decode('utf8')
                require('Class-Path:' not in manifest, 'Runtime jar introduces transitive manifest dependencies')
        java = Path(toolchain['java'])
        javap = java.with_name('javap')
        require(str(java) in pins and str(javap) in pins, 'Retained JDK java/javap bindings required')
        output.mkdir(parents=True)
        report = dict(schema='scala-ten-applications-compile-v1', status='running', pins=pins,
                      started_at=datetime.now(timezone.utc).isoformat(), active=None, profiles=[],
                      native_processes_started=0, compiler_processes_started=0,
                      bytecode_reader_processes_started=0, subject_main_executions=0,
                      benchmark_samples=0, bounded_outputs_qualified=False, source_work_qualified=False,
                      canonical_loc=None, formatted_loc=None, full_timings_qualified=False,
                      chart_admission=False, runtime_libraries=[str(p) for p in libraries])
        saved = {}
        observer.save(output/'report.json', report)
        try:
            for row in rows:
                directory = output/row['benchmark']
                directory.mkdir()
                for name in ('home', 'tmp', 'classes', 'compile', 'bytecode'):
                    (directory/name).mkdir()
                source = directory/'Main.scala'
                raw = (ROOT/row['sources'][0]['path']).read_bytes()
                require(hashlib.sha256(raw).hexdigest() == row['sources'][0]['sha256'],
                        'Source changed before compiler copy')
                with source.open('xb') as stream:
                    stream.write(raw)
                bind(source, row['sources'][0]['sha256'])
                environment = dict(PATH='/usr/bin:/bin', HOME=str(directory/'home'),
                    TMPDIR=str(directory/'tmp')+'/', JAVA_HOME=str(java.parent.parent),
                    LC_ALL='C', LANG='C', TZ='UTC')
                cp = os.pathsep.join(str(p) for p in libraries)
                compile_command = [str(java)]+FLAGS+['-Duser.home='+environment['HOME'],
                    '-Djava.io.tmpdir='+environment['TMPDIR'], '-cp', toolchain['compiler_classpath'],
                    'dotty.tools.dotc.Main', '-classpath', cp, '-encoding', 'UTF-8', '-color:never',
                    '-d', str(directory/'classes'), str(source)]
                profile = dict(id=row['id'], benchmark=row['benchmark'], source=str(source),
                    source_sha256=row['sources'][0]['sha256'], original_source=row['sources'][0]['path'],
                    compile_command=compile_command, runtime_classpath=str(directory/'classes')+os.pathsep+cp,
                    main_owner='Main', source_work_qualified=False, chart_admission=False)
                report['profiles'].append(profile)
                for stage in ('compile', 'bytecode'):
                    where = directory/stage
                    if stage == 'compile':
                        command = compile_command
                    else:
                        owners = [x['relative_path'][:-6].replace('/', '.')
                                  for x in profile['artifacts'] if x['relative_path'].endswith('.class')]
                        command = [str(javap), '-J-XX:ActiveProcessorCount=8', '-J-Xms64m', '-J-Xmx1g',
                            '-J-XX:+UseG1GC', '-p', '-c', '-s', '-l', '-verbose',
                            '-classpath', profile['runtime_classpath']]+owners
                    def launched(pid):
                        report['native_processes_started'] += 1
                        report['compiler_processes_started' if stage == 'compile' else
                               'bytecode_reader_processes_started'] += 1
                        report['active'] = dict(id=row['id'], stage=stage, pid=pid)
                        observer.save(output/'report.json', report)
                    record = observer.observe(command, environment, where, b'', lock, launched,
                        kind='diagnostic-compile' if stage == 'compile' else 'bytecode-inspection')
                    closed_process(record, command, environment, where)
                    report['active'] = None
                    profile[stage+'_process'] = dict(path=str(where/'process.json'), sha256=sha(where/'process.json'))
                    if stage == 'compile':
                        profile['artifacts'] = class_inventory(directory/'classes')
                        for item in profile['artifacts']:
                            bind(item['path'], item['sha256'])
                    else:
                        require(record['stdout_bytes'] > 0, 'Empty bytecode inspection')
                        require(class_inventory(directory/'classes') == profile['artifacts'],
                                'Bytecode inspection changed class artifacts')
                    for path in where.rglob('*'):
                        if path.is_file():
                            saved[str(path)] = sha(path)
                    observer.save(output/'report.json', report)
            require(report['native_processes_started'] == 20
                    and report['compiler_processes_started'] == report['bytecode_reader_processes_started'] == 10,
                    'Incomplete application compilation/inspection accounting')
            report['status'] = 'ten-applications-compiled-and-inspected-awaiting-native-conformance'
        except BaseException as error:
            report.update(status='failed', error=str(error) or type(error).__name__, error_type=type(error).__name__)
        finally:
            with observer.atomic():
                errors = []
                for path, digest in {**pins, **saved}.items():
                    try:
                        require(sha(path) == digest, 'Input or validated artifact changed')
                    except BaseException as error:
                        errors.append(dict(path=path, error=str(error) or type(error).__name__))
                try:
                    report['artifacts'] = artifact_inventory(output)
                    close_artifact_inventory(output, report['artifacts'], pins, saved, report['profiles'])
                except BaseException as error:
                    errors.append(dict(path='<final-artifact-inventory>', error=str(error) or type(error).__name__))
                # Hashing the final inventory must not adopt changed prerequisite
                # bytes or replace an earlier validated stream/class digest.
                for path, digest in pins.items():
                    try:
                        require(sha(path) == digest, 'Prerequisite changed during final artifact closure')
                    except BaseException as error:
                        errors.append(dict(path=path, error=str(error) or type(error).__name__))
                report['integrity_errors'] = errors
                if errors:
                    report['status'] = 'failed-input-or-artifact-integrity'
                report['finished_at'] = datetime.now(timezone.utc).isoformat()
                observer.kh.verify_lock(lock)
                observer.save(output/'report.json', report)
                observer.save(output/'terminal.json', dict(status=report['status'],
                    report_sha256=sha(output/'report.json'), native_processes_started=report['native_processes_started'],
                    subject_main_executions=0, benchmark_samples=0, chart_admission=False))
        print(json.dumps(dict(status=report['status'], report=str(output/'report.json'),
                              sha256=sha(output/'report.json'))))
        return 0 if report['status'].startswith('ten-applications-compiled-') else 1


if __name__ == '__main__':
    raise SystemExit(main())
