#!/usr/bin/env python3
"""Read forty retained Kotlin inputs with their retained compiler's native PSI.

prepare pins the input/runtime closure; run builds a new Java diagnostic and
executes one parser JVM. Both commands require the common measurement mutex.
Canonical owner accounting remains separate; this stage admits no LOC/timing.
"""
import argparse
import base64
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import stat
import sys
import zipfile
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/kotlin/source-counts-v3'
HELPER = ROOT/'experiments/kotlin/helper-semantics/run-v3/report.json'
HELPER_SHA = '066592dc37ccf0ca60e5795e02c680a088e8fe9c17448baa049693d77c5679ad'
HELPER_TERMINAL_SHA = 'c8ffede3ba3ff3dd3827237e50d0b40b2f56fae40b02ea1409acc7c0411e1731'
COMPILED = ROOT/'experiments/kotlin/additive-compile-owners-v1/preparation-result.json'
COMPILED_SHA = '2ab7206a97782975827c743453bfdfee1c4a9f4c95c926a55b157fc07200db8a'
SUPERVISOR = ROOT/'tools/qualification/kotlin_bounded_v2.py'
SUPERVISOR_SHA = 'c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc'
PYTHON = Path('/Users/cim310/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12')
PYTHON_SHA = 'ac60cfe0268614638d0ffa35f3b0284fc7b3a11482723793455e17eeb278509e'
LOCK = Path('/tmp/mech-clbg-timing.lock')
LOCK_INODE = 79859134
JARS = ('kotlin-compiler.jar', 'annotations-13.0.jar', 'kotlin-stdlib.jar',
        'kotlin-reflect.jar', 'kotlin-script-runtime.jar', 'kotlinx-coroutines-core-jvm.jar')
SIGNALS = {signal.SIGINT, signal.SIGTERM, signal.SIGHUP}


def require(value, message):
    if not value:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def bind(path, expected, pins):
    path = Path(path)
    require(sha(path) == expected, 'Pinned input changed: '+str(path))
    require(str(path) not in pins or pins[str(path)] == expected, 'Conflicting input pin')
    pins[str(path)] = expected
    return path


def read(path, expected, pins):
    return json.loads(bind(path, expected, pins).read_bytes())


def module():
    raw = SUPERVISOR.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == SUPERVISOR_SHA, 'Reviewed supervisor changed')
    spec = importlib.util.spec_from_file_location('kotlin_source_reader_supervisor', SUPERVISOR)
    result = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(SUPERVISOR), 'exec'), result.__dict__)
    return result


def inventory(compiled, helper):
    """Metadata-only inventory; deliberately performs no native launch or hashes."""
    rows = compiled['profiles']
    require(compiled['status'] == 'Kotlin20-classes-and-bytecode-captured-awaiting-scored-owner-and-runtime-review'
            and compiled['total_compiled_profiles'] == len(rows) == 20 and
            compiled['subject_main_executions'] == 0 and compiled['chart_admission'] is False,
            'Unexpected retained compile cohort')
    require([r['id'] for r in rows] == helper['completed_profile_ids'], 'Helper and source cohorts differ')
    runtime, environment = rows[0]['runtime_command'][0], rows[0]['runtime_environment']
    inputs, bundles = [], []
    for row in rows:
        require(row['runtime_command'][0] == runtime and row['source_to_compile_command_binding'] is True
                and len(row['physical_inputs']) == 2 and
                {p['role'] for p in row['physical_inputs']} == {'application', 'application-helper'},
                'Incomplete retained source binding')
        bundle = dict(id=row['id'], benchmark=row['benchmark'], variant=row['variant'], inputs=[])
        for item in row['physical_inputs']:
            key = row['id']+'--'+item['role']
            require(item['counted'] is True and re.fullmatch(r'[a-z0-9-]+', key), 'Uncounted/unsafe source input')
            inputs.append(dict(id=key, kind='application', path=item['path'], sha256=item['sha256'],
                               role=item['role'], expected_parse='ok'))
            bundle['inputs'].append(key)
        bundles.append(bundle)
    require(len(inputs) == len({i['id'] for i in inputs}) == len({i['path'] for i in inputs}) == 40,
            'Expected forty distinct physical source inputs')
    return inputs, bundles, runtime, environment


def manifest_fields(raw):
    # JAR manifest continuation lines begin with one space; sections after the
    # first blank line are per-entry attributes, not main classpath attributes.
    text = raw.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    lines = []
    for line in text.split('\n'):
        if not line:
            break
        if line.startswith(' '):
            require(lines, 'Orphan JAR manifest continuation')
            lines[-1] += line[1:]
        else:
            lines.append(line)
    fields = {}
    for line in lines:
        key, separator, value = line.partition(': ')
        require(separator and key.lower() not in fields, 'Malformed or duplicate manifest attribute')
        fields[key.lower()] = value
    return fields


def prepare(args, supervisor):
    require(not args.plan.exists() and not args.output.exists(), 'Fresh plan and output paths required')
    require(not args.plan.resolve().is_relative_to(args.output.resolve()), 'Plan must be outside output')
    pins = {}
    helper = read(HELPER, HELPER_SHA, pins)
    terminal = read(HELPER.with_name('terminal.json'), HELPER_TERMINAL_SHA, pins)
    require(helper['status'] == terminal['status'] == 'twenty-retained-helper-semantics-passed'
            and helper['helper_formatting_and_stdio_qualified'] is True and
            terminal['report_sha256'] == HELPER_SHA and helper['integrity_errors'] ==
            terminal['integrity_errors'] == terminal['artifact_errors'] == [], 'Closed helper evidence required')
    for path, digest in helper['pins'].items():
        bind(path, digest, pins)
    for record in helper['closed_evidence_resolution'].values():
        bind(record['resolved_path'], record['active_sha256'], pins)
    compiled = read(COMPILED, COMPILED_SHA, pins)
    inputs, bundles, java, environment = inventory(compiled, helper)
    for item in inputs:
        bind(item['path'], item['sha256'], pins)
    compiler = [Path(p) for p in compiled['pins'] if p.endswith('/kotlin-compiler.jar')]
    require(len(compiler) == 1, 'Ambiguous retained compiler')
    directory = compiler[0].parent
    jars, manifests = [], {}
    for name in JARS:
        path = directory/name
        require(str(path) in compiled['pins'], 'Unretained compiler dependency')
        bind(path, compiled['pins'][str(path)], pins)
        with zipfile.ZipFile(path) as jar:
            fields = manifest_fields(jar.read('META-INF/MANIFEST.MF'))
        require(all(dep in JARS for dep in fields.get('class-path', '').split()),
                'Compiler manifest names an unreviewed dependency')
        jars.append(str(path)); manifests[name] = fields
    require(manifests[JARS[0]]['implementation-version'] == '2.4.21' and
            manifests[JARS[0]]['class-path'].split() == list(JARS[1:]), 'Retained compiler manifest differs')
    for path in (Path(java), Path(java).with_name('javac')):
        require(str(path) in helper['pins'], 'Retained JDK command missing from closure')
        bind(path, helper['pins'][str(path)], pins)
    summary_path = HELPER.parent/bundles[0]['id']/'summary.json'
    runtime = read(summary_path, helper['pins'][str(summary_path)], pins)['runtime']
    fixtures = read(PACKET/'fixtures.json', sha(PACKET/'fixtures.json'), pins)
    require(len(fixtures) == len({f['id'] for f in fixtures}) == 14 and
            sum(f['expected_parse'] == 'error' for f in fixtures) == 2, 'Fixture inventory differs')
    for fixture in fixtures:
        require(re.fullmatch(r'[a-z0-9-]+', fixture['id']) and fixture['expected_parse'] in ('ok', 'error'),
                'Unsafe parser fixture')
        inputs.append(dict(fixture, id='fixture--'+fixture['id'], kind='fixture', path='fixture:'+fixture['id'],
                           sha256=hashlib.sha256(fixture['text'].encode()).hexdigest()))
    for path in (Path(__file__).resolve(), PACKET/'SourceReader.java', SUPERVISOR, PYTHON,
                 ROOT/'tools/qualification/kotlin_helpers.py', ROOT/'tools/qualification/elixir_bounded.py'):
        bind(path, sha(path), pins)
    require(pins[str(PYTHON)] == PYTHON_SHA and pins[str(SUPERVISOR)] == SUPERVISOR_SHA,
            'Controller runtime or supervisor differs')
    plan = dict(schema='kotlin-native-source-reader-plan-v1', status='prepared-awaiting-native-reader-execution',
                controller=str(Path(__file__).resolve()), controller_sha256=sha(__file__),
                helper_report_sha256=HELPER_SHA, compile_preparation_sha256=COMPILED_SHA,
                java=java, javac=str(Path(java).with_name('javac')), compiler_version='2.4.21',
                compiler_jars=jars, compiler_jar_manifests=manifests, runtime_environment=environment,
                expected_java_home=runtime['JAVA_HOME'], expected_runtime_version=runtime['RUNTIME_VERSION'],
                runtime_flags=supervisor.FLAGS+['-Djava.awt.headless=true'], reader=str(PACKET/'SourceReader.java'),
                output=str(args.output.resolve()), profiles=bundles, inputs=inputs, pins=pins,
                planned_diagnostic_compiler_processes=1, planned_parser_jvm_processes=1,
                application_files=40, fixture_files=14, subject_recompilations=0, subject_main_invocations=0,
                source_evaluations=0, benchmark_samples=0, automatic_retry=False,
                process_timeout_seconds=supervisor.TIMEOUT, cleanup_timeout_seconds=supervisor.CLEANUP_TIMEOUT,
                maximum_process_group_rss_bytes=supervisor.RSS_LIMIT, native_file_limit_bytes=supervisor.FILE_LIMIT,
                canonical_loc=None, formatted_loc=None, chart_admission=False)
    args.plan.parent.mkdir(parents=True, exist_ok=True)
    supervisor.save(args.plan, plan)
    print(json.dumps(dict(plan=str(args.plan), sha256=sha(args.plan), native_processes=0)), flush=True)


def utf16(text):
    return text.encode('utf-16-le', errors='surrogatepass')


def validate_psi(evidence, source, parsed, expected):
    require(parsed == source or parsed == source.replace('\r\n', '\n').replace('\r', '\n'),
            'Parser changed source beyond newline normalization')
    raw = utf16(parsed); length = len(raw)//2
    require(evidence['schema'] == 'kotlin-native-psi-source-v1' and evidence['id'] == expected['id'] and
            evidence['source_sha256'] == expected['sha256'] and evidence['offset_units'] == 'UTF-16 code units'
            and evidence['source_utf16_length'] == length and evidence['leaf_coverage_complete'] is True and
            evidence['newline_normalization_observed'] is (parsed != source), 'PSI identity/offset metadata differs')
    require(evidence['psi_source_sha256'] == hashlib.sha256(parsed.encode()).hexdigest(), 'PSI source hash differs')
    nodes = evidence['nodes']; require(isinstance(nodes, list) and nodes, 'Missing native PSI nodes')
    visited, leaves = [], []
    def visit(index, parent, start, end):
        require(type(index) is int and index == len(visited) and index < len(nodes), 'PSI preorder/child inventory differs')
        node = nodes[index]; visited.append(index)
        a, b = node['start_utf16'], node['end_utf16']
        require(node['id'] == index and node['parent'] == parent and type(a) is int and type(b) is int and
                start <= a <= b <= end and isinstance(node['psi_class'], str) and node['psi_class'] and
                isinstance(node['element_type'], str) and type(node['comment']) is bool and
                type(node['whitespace']) is bool and isinstance(node['children'], list), 'PSI node range/parent differs')
        if node['children']:
            cursor = a
            for child in node['children']:
                c, d = visit(child, index, a, b)
                require(c == cursor, 'PSI child ranges do not partition parent')
                cursor = d
            require(cursor == b and 'text' not in node, 'PSI child range suffix/text differs')
        else:
            require(utf16(node['text']) == raw[2*a:2*b], 'PSI leaf text differs from exact source span')
            leaves.append((a, b))
        return a, b
    require(visit(0, -1, 0, length) == (0, length) and len(visited) == len(nodes), 'PSI root/inventory differs')
    cursor = 0
    for a, b in leaves:
        require(a == cursor, 'PSI leaves do not cover source exactly once'); cursor = b
    require(cursor == length, 'PSI leaf coverage omits suffix')
    errors = evidence['parse_errors']; require(isinstance(errors, list), 'Missing native parser error inventory')
    ids = [error['node'] for error in errors]
    require(len(ids) == len(set(ids)) and set(ids) == {n['id'] for n in nodes if n['element_type'] == 'ERROR_ELEMENT'},
            'PSI error-node inventory differs')
    for error in errors:
        node = nodes[error['node']]
        require(error['start_utf16'] == node['start_utf16'] and error['end_utf16'] == node['end_utf16'] and
                isinstance(error['message'], str) and error['message'], 'Missing native parser error description')
    require(bool(errors) == (expected['expected_parse'] == 'error'), 'Unexpected native parse outcome')


def uri_path(uri):
    value = urlparse(uri)
    require(value.scheme == 'file' and value.netloc in ('', 'localhost'), 'Nonlocal parser origin')
    return Path(unquote(value.path)).resolve()


def validate_reader(report, plan, output, probe_classes, options):
    require(report['schema'] == 'kotlin-native-source-reader-v1' and
            report['status'] == 'read-awaiting-canonical-owner-review' and
            report['source_evaluations'] == report['subject_recompilations'] == report['subject_main_invocations'] == 0
            and report['canonical_loc'] is report['formatted_loc'] is None and report['chart_admission'] is False,
            'Unexpected parser admission or execution claim')
    runtime = report['runtime']; jars = plan['compiler_jars']
    require(runtime['java_home'] == plan['expected_java_home'] and runtime['runtime_version'] == plan['expected_runtime_version']
            and runtime['class_path'] == os.pathsep.join([str(probe_classes)]+jars) and runtime['flags'] == options and
            runtime['compiler_version'] == plan['compiler_version'] and runtime['headless'] == 'true' and
            runtime['application_class_canary'] == 'clbg.Support unavailable', 'Parser runtime/configuration differs')
    origins = {'sourcequalification.SourceReader': probe_classes,
               'org.jetbrains.kotlin.cli.jvm.compiler.KotlinCoreEnvironment': Path(jars[0]),
               'org.jetbrains.kotlin.psi.KtPsiFactory': Path(jars[0]),
               'org.jetbrains.kotlin.config.CompilerConfiguration': Path(jars[0]),
               'com.intellij.openapi.util.Disposer': Path(jars[0]), 'kotlin.Unit': Path(jars[2])}
    require(set(runtime['class_origins']) == set(origins) and
            all(uri_path(runtime['class_origins'][owner]) == path.resolve() for owner, path in origins.items()),
            'Native parser class origins differ')
    require(json.loads((output/'started.json').read_bytes()) == runtime, 'Parser startup/final runtime differ')
    validate_artifacts(report, plan, output)


def validate_artifacts(report, plan, output):
    require(len(report['items']) == len(plan['inputs']) and
            len({i['id'] for i in plan['inputs']}) == len(plan['inputs']), 'Incomplete/duplicate parser input inventory')
    require({p.name for p in output.iterdir()} == {i['id'] for i in plan['inputs']} | {'started.json', 'report.json'}
            and not any(p.is_symlink() for p in output.rglob('*')), 'Native parser artifact inventory differs')
    for actual, expected in zip(report['items'], plan['inputs']):
        require(actual['id'] == expected['id'] and actual['source_sha256'] == expected['sha256'] and
                actual['canonical_loc'] is actual['formatted_loc'] is None, 'Per-source parser identity/count differs')
        directory = output/expected['id']
        require(directory.is_dir() and {p.name for p in directory.iterdir()} == {'source.kt', 'psi-source.kt', 'psi.json'},
                'Missing or unexpected per-source artifacts')
        require(sha(directory/'source.kt') == expected['sha256'] and sha(directory/'psi.json') == actual['psi_sha256'] and
                sha(directory/'psi-source.kt') == actual['psi_source_sha256'], 'Native parser artifact hash differs')
        source = (directory/'source.kt').read_bytes().decode('utf-8')
        parsed = (directory/'psi-source.kt').read_bytes().decode('utf-8')
        evidence = json.loads((directory/'psi.json').read_bytes())
        require(evidence['source_path'] == expected['reader_path'], 'Parser inspected a different input path')
        validate_psi(evidence, source, parsed, expected)
        require(actual['nodes'] == len(evidence['nodes']) and actual['parse_errors'] == len(evidence['parse_errors']) and
                actual['psi_source_sha256'] == evidence['psi_source_sha256'] and
                actual['status'] == ('parsed' if expected['expected_parse'] == 'ok' else 'expected-parse-rejection'),
                'Native parser result summary differs from retained PSI')


def validate_receipt(receipt, kind):
    require(receipt['kind'] == kind and receipt['status'] == 'native-passed' and
            receipt['native_process_started'] is True and type(receipt['pid']) is int and receipt['pid'] > 0 and
            receipt['pgid'] == receipt['pid'] and receipt['exit_status'] == 0 and receipt['direct_child_reaped'] is True and
            receipt['inherited_common_mutex'] is True and receipt['common_mutex_inode'] == LOCK_INODE and
            receipt['remaining_process_group'] == [] and not any(receipt.get(key) for key in
                ('error', 'cleanup_errors', 'artifact_errors', 'stop_signals', 'remaining_after_cleanup')),
            'Parser command did not have a clean owned exit')


def inventory_files(root, errors):
    """Retain partial inventories while making every traversal failure explicit."""
    files = []
    def failed(error, path=None):
        errors.append(dict(path=str(path if path is not None else getattr(error, 'filename', root)),
                           error=str(error) or type(error).__name__))
    try:
        for directory, children, names in os.walk(root, onerror=failed, followlinks=False):
            retained_children = []
            for name in children + names:
                path = Path(directory)/name
                try:
                    mode = path.lstat().st_mode
                    require(not stat.S_ISLNK(mode), 'Unexpected output symlink')
                    if stat.S_ISREG(mode):
                        files.append(path)
                    else:
                        require(stat.S_ISDIR(mode), 'Unexpected non-file output artifact')
                        if name in children:
                            retained_children.append(name)
                except BaseException as error:
                    failed(error, path)
            children[:] = retained_children
    except BaseException as error:
        failed(error)
    return files


def run(args, lock, supervisor):
    require(sha(args.plan) == args.plan_sha256, 'Reviewed parser plan changed')
    plan = json.loads(args.plan.read_bytes())
    require(plan['schema'] == 'kotlin-native-source-reader-plan-v1' and plan['controller_sha256'] == sha(__file__) and
            plan['automatic_retry'] is False and plan['application_files'] == 40 and plan['fixture_files'] == 14,
            'Unexpected source parser plan')
    output = Path(plan['output']); require(not output.exists(), 'Fresh output required; no automatic retry')
    pins = dict(plan['pins']); bind(args.plan.resolve(), args.plan_sha256, pins)
    for path, digest in pins.items():
        require(sha(path) == digest, 'Preflight input changed: '+path)
    output.mkdir(parents=True)
    report = dict(schema='kotlin-native-source-reader-results-v1', status='running',
                  plan=str(args.plan.resolve()), plan_sha256=args.plan_sha256, pins=pins,
                  started_at=datetime.now(timezone.utc).isoformat(), native_processes_started=0,
                  native_launch_requests=0, native_processes=[], active=None, reader_evidence_validated=False,
                  subject_recompilations=0, subject_main_invocations=0, source_evaluations=0, benchmark_samples=0,
                  canonical_loc=None, formatted_loc=None, chart_admission=False)
    supervisor.save(output/'report.json', report)
    def launch(kind, directory):
        report['native_launch_requests'] += 1
        report['active'] = dict(kind=kind, directory=str(directory), pid=None)
        supervisor.save(output/'report.json', report)
        def started(pid):
            report['native_processes_started'] += 1
            report['native_processes'].append(dict(kind=kind, pid=pid, pgid=pid))
            report['active']['pid'] = pid
            supervisor.save(output/'report.json', report)
        return started
    try:
        compiler = output/'diagnostic-compile'; compiler.mkdir()
        environment = supervisor.kh.environment(plan['runtime_environment'], compiler)
        classes = output/'probe-classes'; classes.mkdir()
        source = compiler/'SourceReader.java'; source.write_bytes(Path(plan['reader']).read_bytes())
        require(sha(source) == pins[plan['reader']], 'Reader diagnostic changed during copy')
        command = [plan['javac']]+['-J'+f for f in plan['runtime_flags']]+[
            '-J-Duser.home='+str(compiler/'home'), '-J-Djava.io.tmpdir='+str(compiler/'tmp'),
            '--release', '17', '-proc:none', '-cp', os.pathsep.join(plan['compiler_jars']), '-d', str(classes), str(source)]
        receipt = supervisor.observe(command, environment, compiler, b'', lock,
                                     launch('diagnostic-compile', compiler), kind='diagnostic-compile')
        validate_receipt(receipt, 'diagnostic-compile')
        generated = [p for p in classes.rglob('*') if p.is_file()]
        require({str(p.relative_to(classes)) for p in generated} == {'sourcequalification/SourceReader.class'} and
                not any(p.is_symlink() for p in classes.rglob('*')), 'Unexpected diagnostic generated classes')
        for path in generated:
            raw = path.read_bytes()
            require(raw[:4] == b'\xca\xfe\xba\xbe' and int.from_bytes(raw[6:8], 'big') == 61, 'Wrong Java diagnostic target')
            pins[str(path)] = sha(path)
        reader = output/'native-reader'; reader.mkdir()
        environment = supervisor.kh.environment(plan['runtime_environment'], reader)
        fixtures = output/'fixture-inputs'; fixtures.mkdir()
        manifest, inputs = [], []
        for item in plan['inputs']:
            item = dict(item)
            if item['kind'] == 'fixture':
                path = fixtures/(item['id']+'.kt'); path.write_bytes(item['text'].encode())
            else:
                path = Path(item['path'])
            bind(path, item['sha256'], pins)
            item['reader_path'] = str(path); inputs.append(item)
            encoded = base64.b64encode(str(path).encode()).decode('ascii')
            manifest.append('\t'.join([item['id'], encoded, item['sha256'], item['expected_parse']]))
        manifest_path = output/'inputs.tsv'; manifest_path.write_text('\n'.join(manifest)+'\n')
        pins[str(manifest_path)] = sha(manifest_path)
        options = plan['runtime_flags']+['-Duser.home='+str(reader/'home'), '-Djava.io.tmpdir='+str(reader/'tmp')]
        parser_output = reader/'sources'
        command = [plan['java']]+options+['-cp', os.pathsep.join([str(classes)]+plan['compiler_jars']),
                                        'sourcequalification.SourceReader', str(manifest_path), str(parser_output)]
        receipt = supervisor.observe(command, environment, reader, b'', lock,
                                     launch('native-source-reader', reader), kind='native-source-reader')
        validate_receipt(receipt, 'native-source-reader')
        require((reader/'stdout.bin').read_bytes() == b'', 'Unexpected parser stdout')
        native = json.loads((parser_output/'report.json').read_bytes())
        validate_reader(native, dict(plan, inputs=inputs), parser_output, classes, options)
        require(report['native_processes_started'] == 2, 'Unexpected native process count')
        report.update(status='read-awaiting-canonical-owner-review', active=None, reader_evidence_validated=True,
                      native_reader_report=str(parser_output/'report.json'), native_reader_report_sha256=sha(parser_output/'report.json'),
                      profiles=plan['profiles'], inputs=inputs)
    except BaseException as error:
        report.update(status='failed', reader_evidence_validated=False,
                      error=str(error) or type(error).__name__, error_type=type(error).__name__)
        raise
    finally:
        with supervisor.atomic():
            receipts, errors = [], []
            for path in inventory_files(output, errors):
                if path.name != 'process.json':
                    continue
                try:
                    record = json.loads(path.read_bytes())
                    if record['native_process_started']:
                        receipts.append(dict(kind=record['kind'], pid=record['pid'], pgid=record['pgid']))
                    if report['reader_evidence_validated']:
                        validate_receipt(record, record['kind'])
                except BaseException as error:
                    errors.append(dict(path=str(path), error=str(error) or type(error).__name__))
            if sorted(receipts, key=lambda r:r['pid']) != sorted(report['native_processes'], key=lambda r:r['pid']):
                errors.append(dict(error='Native launch and saved process inventories differ'))
            integrity = []
            for path, digest in pins.items():
                try:
                    require(sha(path) == digest, 'Pinned bytes changed')
                except BaseException as error:
                    integrity.append(dict(path=path, error=str(error) or type(error).__name__))
            if errors or integrity:
                report.update(status='failed-input-or-native-integrity', reader_evidence_validated=False)
            report.update(process_receipt_errors=errors, integrity_errors=integrity,
                          finished_at=datetime.now(timezone.utc).isoformat())
            supervisor.save(output/'report.json', report)
            artifacts, artifact_errors = {}, []
            for path in inventory_files(output, artifact_errors):
                try:
                    artifacts[str(path.relative_to(output))] = dict(sha256=sha(path), bytes=path.stat().st_size)
                except BaseException as error:
                    artifact_errors.append(dict(path=str(path), error=str(error) or type(error).__name__))
            if artifact_errors:
                report.update(status='failed-artifact-integrity', reader_evidence_validated=False, artifact_errors=artifact_errors)
                supervisor.save(output/'report.json', report)
                artifacts['report.json'] = dict(sha256=sha(output/'report.json'), bytes=(output/'report.json').stat().st_size)
            supervisor.kh.verify_lock(lock)
            supervisor.save(output/'terminal.json', dict(status=report['status'], report_sha256=sha(output/'report.json'),
                available_evidence=artifacts, process_receipt_errors=errors, integrity_errors=integrity,
                artifact_errors=artifact_errors, native_processes_started=report['native_processes_started'],
                reader_evidence_validated=report['reader_evidence_validated'], common_mutex_held=True,
                common_mutex_inode=LOCK_INODE, canonical_loc=None, formatted_loc=None, chart_admission=False))
            require(not errors and not integrity and not artifact_errors, 'Parser input/output/native integrity failed')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    prepare_parser = sub.add_parser('prepare')
    prepare_parser.add_argument('--plan', type=Path, required=True)
    prepare_parser.add_argument('--output', type=Path, required=True)
    run_parser = sub.add_parser('run')
    run_parser.add_argument('--plan', type=Path, required=True)
    run_parser.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    require(Path(sys.executable).resolve() == PYTHON.resolve() and sys.flags.isolated and sys.flags.no_site and
            sys.flags.dont_write_bytecode and not sys.flags.optimize, 'Use retained Python with -I -S -B and no -O')
    supervisor = module()
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Kotlin source reader interrupted: '+str(signum))
    for sig in SIGNALS:
        signal.signal(sig, interrupted)
    with LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        supervisor.kh.verify_lock(lock)
        require(sha(PYTHON) == PYTHON_SHA, 'Wrong controller interpreter bytes')
        if args.action == 'prepare':
            prepare(args, supervisor)
        else:
            run(args, lock, supervisor)


if __name__ == '__main__':
    main()
