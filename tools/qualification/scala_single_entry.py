#!/usr/bin/env python3
"""Capture two fresh Scala mains with retained classes and JVM diagnostics.

Reuses the immutable native lifecycle and machine-byte reader from the Kotlin
qualification. No subject compilation, wrapper warmup or timing occurs here.
Capture completeness never grants allocation/lifetime or division semantics.
"""
import argparse
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
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/scala/single-entry-work-v1'
BOUNDED = ROOT/'experiments/scala/bounded-v1'
BOUNDED_CONTROLLER_SHA = '01fc678cda57d971e6b48df7ab7ce3904a0fd135056280920453643bddee0d16'
BOUNDED_PLAN_SHA = '8dcc5342826524ef290ee0ed55e3d77fec89d50642fb82f51ece405ba67bacbc'
BOUNDED_REPORT_SHA = 'a5d794e06c554f2d89fe4430f55eefc9ebfa03e3a35f55c512ff5816d7c774b8'
BOUNDED_TERMINAL_SHA = 'e85b8306e290deb148f41a02ae6ad4e3ed516ba0d364d249720406b8ac807161'
CAPTURE_SHA = 'baeb42da62b8bb4020fe019a2c0c22e47f4bb401852339d6c383b93ad76fd7a4'
SUPERVISOR_SHA = '1b94c74eaeab6eb21046084fd648ae5759307c86d747773b32f0c9b32242888b'
INPUTS = {'binarytrees': 21, 'pidigits': 10000}
OUTPUTS = {
    'binarytrees': (455, '341de11a51feab3d8122b4b5d6a68b038a2d14434aa9bc2372f39300bf5f48e1'),
    'pidigits': (16893, 'bdfa7b6c756d96492f472f97aee9cc139bee954d271eacedfd7ace5d2875f06c'),
}
PRINT_TARGETS = {
    'binarytrees': ['Main::main', 'Main$::main', 'Main$::tree', 'Main$Node::*', 'Main$$anon$1::call'],
    'pidigits': ['Main::main', 'Main$::main', 'scala.math.BigInt::$div',
                'java.math.BigInteger::divide*', 'java.math.MutableBigInteger::divide*'],
}
SUCCESS = 'two-native-captures-complete-awaiting-instruction-review'


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def module(name, digest, identity):
    path = Path(__file__).with_name(name)
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'Frozen dependency changed: '+name)
    spec = importlib.util.spec_from_file_location(identity, path)
    value = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), value.__dict__)
    return value


b = module('scala_bounded.py', BOUNDED_CONTROLLER_SHA, 'scala_single_entry_prerequisites')
capture = module('kotlin_single_entry_capture.py', CAPTURE_SHA, 'scala_machine_byte_reader')
supervisor_module = module('kotlin_single_entry_supervisor.py', SUPERVISOR_SHA, 'scala_full_input_policy')
kb = supervisor_module.supervisor
# A separate private module selects the already reviewed 10 GiB observer policy
# for new receipts. The prerequisite validator retains its original 2 GiB limit.
receipt_reader = module('scala_bounded.py', BOUNDED_CONTROLLER_SHA, 'scala_full_input_receipts')
receipt_reader.kb = kb


def expected_output(benchmark):
    if benchmark == 'pidigits':
        raw = (ROOT/'archive/workloads/pidigits/inputs/output-full.txt').read_bytes()
    else:
        require(benchmark == 'binarytrees', 'Unexpected diagnostic workload')
        n = INPUTS[benchmark]
        rows = [f'stretch tree of depth {n+1}\t check: {(1 << (n+2))-1}\n']
        for depth in range(4, n+1, 2):
            count = 1 << (n-depth+4)
            rows.append(f'{count}\t trees of depth {depth}\t check: {count*((1 << (depth+1))-1)}\n')
        rows.append(f'long lived tree of depth {n}\t check: {(1 << (n+1))-1}\n')
        raw = ''.join(rows).encode('ascii')
    require((len(raw), hashlib.sha256(raw).hexdigest()) == OUTPUTS[benchmark], 'Full output oracle changed')
    return raw


def bounded_prerequisite(pins):
    plan = b.document(BOUNDED/'plan-v1.json', BOUNDED_PLAN_SHA, pins)
    report = b.document(BOUNDED/'run-v1/report.json', BOUNDED_REPORT_SHA, pins)
    terminal = b.document(BOUNDED/'run-v1/terminal.json', BOUNDED_TERMINAL_SHA, pins)
    require(plan['controller_sha256'] == BOUNDED_CONTROLLER_SHA and
            report['status'] == terminal['status'] == b.SUCCESS and
            report['plan_sha256'] == BOUNDED_PLAN_SHA and terminal['report_sha256'] == BOUNDED_REPORT_SHA and
            report['active'] is None and report['integrity_errors'] == terminal['integrity_errors'] == [] and
            report['process_receipt_errors'] == terminal['process_receipt_errors'] == [] and
            report['native_processes_started'] == terminal['native_processes_started'] == 149 and
            report['qualified_cases'] == terminal['qualified_cases'] == 149 and
            (report['successful_cases'], report['rejected_cases']) == (142, 7) and
            report['bounded_outputs_qualified'] is terminal['bounded_outputs_qualified'] is True and
            terminal['common_mutex_held'] is True and terminal['common_mutex_inode'] == 79859134,
            'Closed successful Scala149 prerequisite required')
    for name, digest in {**plan['pins'], **report['pins']}.items():
        b.bind(pins, name, digest)
    require(all(report['pins'].get(n) == h for n, h in plan['pins'].items()), 'Bounded input closure differs')
    compiled = b.compiled_prerequisite(Path(plan['compiled']['report']), plan['compiled']['report_sha256'],
                                       plan['compiled']['terminal_sha256'], pins)
    require(compiled == plan['compiled'] and plan['schedule'] == b.corpus(pins), 'Bounded plan cohort differs')
    output = BOUNDED/'run-v1'
    closure = b.inventory(output, ('terminal.json',))
    require(closure == terminal['available_evidence'] and
            {n: v for n, v in closure.items() if n != 'report.json'} == report['artifacts'],
            'Bounded artifact closure differs')
    require(b.process_closure(report, plan, output) == [], 'Bounded native lifecycles differ')
    b.final_snapshot(report, closure)
    parent = None
    previous = b.stamp(report['started_at'])
    for slot, result in zip(plan['schedule'], report['cases']):
        directory = output/slot['directory']
        raw = json.loads((directory/'process.json').read_bytes())
        if parent is None:
            parent = raw['identity']['ppid']
        require(previous <= b.stamp(raw['started_at']) <= b.stamp(raw['finished_at']),
                'Bounded native schedule overlaps')
        previous = b.stamp(raw['finished_at'])
        require(b.checked_case(plan, slot, directory, parent) == result, 'Bounded output/lifecycle replay differs')
    require(len(report['cases']) == 149 and previous <= b.stamp(report['finished_at']), 'Incomplete bounded replay')
    require(b.inventory(output, ('terminal.json',)) == closure, 'Bounded evidence changed during replay')
    for name, item in closure.items():
        b.bind(pins, output/name, item['sha256'])
    return compiled, dict(plan=str(BOUNDED/'plan-v1.json'), plan_sha256=BOUNDED_PLAN_SHA,
        report=str(output/'report.json'), report_sha256=BOUNDED_REPORT_SHA,
        terminal=str(output/'terminal.json'), terminal_sha256=BOUNDED_TERMINAL_SHA,
        cases_replayed=149, successful_cases=142, rejected_cases=7, artifacts=closure)


def build_plan(output):
    b.physical(output)
    require(output.is_relative_to(PACKET) and output != PACKET and not output.exists(), 'Fresh diagnostic output required')
    pins = {}
    compiled, prior = bounded_prerequisite(pins)
    for path, digest in ((Path(__file__).resolve(), sha(__file__)),
            (Path(__file__).with_name('test_scala_single_entry.py'), sha(Path(__file__).with_name('test_scala_single_entry.py'))),
            (PACKET/'README.md', sha(PACKET/'README.md')),
            (Path(b.__file__), BOUNDED_CONTROLLER_SHA), (Path(capture.__file__), CAPTURE_SHA),
            (Path(supervisor_module.__file__), SUPERVISOR_SHA),
            (Path(capture.stage.__file__), capture.CONTROLLER_SHA),
            (Path(capture.stage.kw.__file__), capture.stage.WORK_CONTROLLER_SHA),
            (Path(kb.__file__), supervisor_module.SOURCE_SHA),
            (ROOT/'archive/workloads/pidigits/inputs/output-full.txt', OUTPUTS['pidigits'][1])):
        b.bind(pins, path, digest)
    release = Path(compiled['java']).parent.parent/'release'
    require(str(release) in pins, 'JDK release metadata not pinned')
    release_values = dict(line.split('=', 1) for line in release.read_text().splitlines() if '=' in line)
    release_values = {k: v.strip('"') for k, v in release_values.items()}
    owners = {}
    for jar in compiled['runtime_libraries']:
        with zipfile.ZipFile(jar) as archive:
            for name in archive.namelist():
                if name.endswith('.class') and not name.startswith('META-INF/'):
                    owner = name[:-6].replace('/', '.')
                    require(owner not in owners, 'Ambiguous runtime class owner: '+owner)
                    owners[owner] = jar
    profiles = [next(p for p in compiled['profiles'] if p['benchmark'] == bench) for bench in INPUTS]
    return dict(schema='scala-two-single-entry-plan-v1', status='prepared-awaiting-independent-review',
        controller=str(Path(__file__).resolve()), controller_sha256=sha(__file__), output=str(output), pins=pins,
        compiled=compiled, bounded_prerequisite=prior, profiles=profiles, runtime_class_owners=owners,
        jdk_release=release_values, inputs=INPUTS, print_targets=PRINT_TARGETS,
        runtime_flags=kb.FLAGS, native_processes=2, compiler_invocations=0,
        timeout_seconds=kb.TIMEOUT, cleanup_seconds=kb.CLEANUP_TIMEOUT,
        maximum_process_group_rss_bytes=kb.RSS_LIMIT, native_file_limit_bytes=kb.FILE_LIMIT,
        common_mutex_inode=79859134, automatic_retries=0, source_work_qualified=False,
        full_timings_qualified=False, benchmark_samples=0, chart_admission=False)


def options(benchmark, directory):
    return kb.FLAGS + [f'-Duser.home={directory}/home', f'-Djava.io.tmpdir={directory}/tmp/',
        '-XX:+UnlockDiagnosticVMOptions', '-XX:+LogCompilation', '-XX:+LogVMOutput',
        '-XX:-DisplayVMOutput', f'-XX:LogFile={directory}/hotspot.xml', '-XX:CompileCommand=quiet'] + [
        '-XX:CompileCommand=print,'+p for p in PRINT_TARGETS[benchmark]] + [
        f'-Xlog:class+load=info:file={directory}/classes.log:uptime,tags',
        f'-Xlog:gc*=info:file={directory}/gc.log:uptime,tags',
        '-Xlog:all=warning,os=off:stdout:uptime,level,tags',
        f'-Xlog:os=warning:file={directory}/os.log:uptime,level,tags']


def command_for(plan, profile, directory):
    java = plan['compiled']['java']
    return ([java]+options(profile['benchmark'], directory)+['-cp', profile['runtime_classpath'],
            'Main', str(INPUTS[profile['benchmark']])], b.environment(directory, java))


def targeted(method, benchmark):
    parts = method.split(' ', 2)
    if len(parts) != 3:
        return False
    owner, name, _ = parts
    if owner in ('Main', 'Main$') and name == 'main':
        return True
    if benchmark == 'binarytrees':
        return ((owner == 'Main$' and name == 'tree') or owner == 'Main$Node' or
                (owner == 'Main$$anon$1' and name == 'call'))
    return ((owner == 'scala.math.BigInt' and name == '$div') or
            (owner in ('java.math.BigInteger', 'java.math.MutableBigInteger') and name.startswith('divide')))


def capture_index(root, benchmark):
    require(root.tag == 'hotspot_log' and len(root.findall('hotspot_log_done')) == 1,
            'Incomplete HotSpot XML')
    prints = {}
    for node in root.iter('print_nmethod'):
        key = node.get('compile_id')
        require(key and key not in prints, 'Duplicate/missing print identity')
        prints[key] = node
    methods = []
    installed_ids = set()
    for node in root.iter('nmethod'):
        require(node.get('compile_id') and node.get('compile_id') not in installed_ids,
                'Duplicate/missing installed method identity')
        installed_ids.add(node.get('compile_id'))
        if not targeted(node.get('method', ''), benchmark):
            continue
        key = node.get('compile_id')
        printed = prints.get(key)
        require(printed is not None and node.get('compiler') in ('c1', 'c2'), 'Targeted native code missing')
        text = ''.join(printed.itertext())
        require(all(printed.get(k) == node.get(k) for k in ('compiler', 'level', 'compile_kind')),
                'Printed native compiler identity differs')
        identity = re.findall(r"(?m)^[ \t]*# \{method\} \{0x[0-9a-fA-F]+\} '([^']+)' '([^']+)' in '([^']+)'[ \t]*$", text)
        require(len(identity) == 1 and identity[0][2].replace('/', '.')+' '+identity[0][0]+' '+identity[0][1] == node.get('method'),
                'Printed native method owner differs')
        coverage = capture.instruction_coverage(text, node.get('entry', ''))
        maps = [line.strip() for line in text.splitlines() if 'ImmutableOopMap' in line]
        methods.append(dict(node.attrib, instruction_coverage=coverage, oopmaps=maps,
                            native_text_sha256=hashlib.sha256(text.encode()).hexdigest()))
    installed = {n.get('compile_id') for n in root.iter('nmethod')}
    eliminated = []
    main_references = []
    for task in root.iter('task'):
        names = {n.get('id'): n.get('name', '').replace('/', '.') for n in task.iter('klass')}
        for method in task.iter('method'):
            if names.get(method.get('holder')) in ('Main', 'Main$') and method.get('name') == 'main':
                main_references.append(dict(compile_id=task.get('compile_id'), caller=task.get('method'),
                                            holder=names[method.get('holder')], method_id=method.get('id')))
        for node in task.iter('eliminate_allocation'):
            if names.get(node.get('type')) == 'Main$Node':
                eliminated.append(dict(compile_id=task.get('compile_id'), caller=task.get('method'),
                    installed_nmethod=task.get('compile_id') in installed,
                    locations=[dict(n.attrib) for n in node]))
    events = {tag: [dict(n.attrib) for n in root.iter(tag)] for tag in ('task_queued', 'task', 'nmethod')}
    return dict(status='retained-native-bytes-awaiting-instruction-review', native_methods=methods,
        compiler_events=events, main_method_references=main_references, node_allocation_eliminations=eliminated,
        allocation_and_lifetime_proved=False, both_pi_divisions_proved=False, source_work_qualified=False)


def validate_classes(text, profile, plan):
    owners = {a['relative_path'][:-6].replace('/', '.') for a in profile['artifacts'] if a['relative_path'].endswith('.class')}
    observed = {}
    for line in text.splitlines():
        if '[class,load]' not in line:
            continue
        match = re.search(r'\[class,load\]\s+(\S+) source: (.+)$', line)
        require(match, 'Malformed class-load record')
        owner, source = match.groups()
        if source.startswith('file:'):
            expected = profile['classes'] if owner in owners else plan['runtime_class_owners'].get(owner)
            require(expected is not None and kb.uri_path(source) == Path(expected).resolve(), 'Unbound loaded class origin')
        elif source.startswith(('jrt:/', 'shared objects file')):
            require(owner not in owners and owner not in plan['runtime_class_owners'], 'Subject/runtime owner loaded from platform')
        else:
            hidden = re.fullmatch(r'(.+)\$\$Lambda(?:\$\d+)?/0x[0-9a-fA-F]+', owner)
            host = hidden[1] if hidden else None
            require((host is not None and host in observed and
                     (source == host or host.startswith(source+'$')) and source in observed) or
                    (source == '__JVM_LookupDefineClass__' and owner.startswith(('java.', 'jdk.'))),
                    'Unknown generated class origin')
        require(owner not in observed or observed[owner] == source, 'Conflicting loaded owner origin')
        observed[owner] = source
    require({'Main', 'Main$'} <= observed.keys(), 'Direct Main class origins missing')
    return observed


def validate_vm(root, profile, plan, directory, receipt):
    require(root.get('process') == str(receipt['pid']), 'HotSpot log belongs to another process')
    args = root.find('vm_arguments')
    require(args is not None and args.findtext('args', '').strip().split() == options(profile['benchmark'], directory)
            and args.findtext('command', '').strip() == 'Main '+str(INPUTS[profile['benchmark']])
            and args.findtext('launcher', '').strip() == 'SUN_STANDARD', 'Actual JVM invocation differs')
    props = dict(line.split('=', 1) for line in args.findtext('properties', '').splitlines() if '=' in line)
    expected = {'java.home': str(Path(plan['compiled']['java']).parent.parent),
        'java.class.path': profile['runtime_classpath'], 'java.vm.version': plan['jdk_release']['JVM_VERSION'],
        'java.vm.vendor': plan['jdk_release']['IMPLEMENTOR'], 'user.home': str(directory/'home'),
        'java.io.tmpdir': str(directory/'tmp')+'/'}
    require(all(props.get(k) == v for k, v in expected.items()), 'Actual JVM properties differ')
    require('for bsd-'+plan['jdk_release']['OS_ARCH']+' ' in root.findtext('vm_version/info', ''), 'JVM architecture differs')


def checked_capture(plan, profile, directory, parent):
    command, env = command_for(plan, profile, directory)
    receipt, stdout, stderr = receipt_reader.native_receipt(directory, command, env, b'', parent, 'scala-single-entry-work')
    expected = expected_output(profile['benchmark'])
    require(stdout == expected and stderr == b'' and (directory/'expected.stdout').read_bytes() == expected,
            'Complete subject output differs')
    raw = (directory/'os.log').read_bytes()
    lines = raw.decode('ascii').splitlines()
    require(len(lines) <= 1 and all(re.fullmatch(r'\[[0-9]+\.[0-9]+s\]\[warning\]\[os\] Loading hsdis library failed', s)
                                  for s in lines), 'Unexpected OS diagnostic')
    root = ET.parse(directory/'hotspot.xml').getroot()
    validate_vm(root, profile, plan, directory, receipt)
    loaded = validate_classes((directory/'classes.log').read_text(), profile, plan)
    require('Using G1' in (directory/'gc.log').read_text(), 'Actual G1 evidence missing')
    index = capture_index(root, profile['benchmark'])
    return dict(id=profile['id'], benchmark=profile['benchmark'], pid=receipt['pid'],
        process_sha256=sha(directory/'process.json'), complete_output_match=True,
        output_sha256=hashlib.sha256(stdout).hexdigest(), output_bytes=len(stdout),
        actual_loaded_classes=loaded, os_diagnostic=dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), lines=lines),
        capture=index, source_work_qualified=False, benchmark_samples=0, chart_admission=False)


def process_closure(report, plan, output):
    records = []
    allowed = [p['benchmark'] for p in plan['profiles']]
    require({str(p.parent.relative_to(output)) for p in output.rglob('process.json')} <= set(allowed), 'Unscheduled native receipt')
    for bench in allowed:
        path = output/bench/'process.json'
        if not path.exists():
            continue
        item = json.loads(path.read_bytes())
        if item['native_process_started']:
            require(item['pid'] == item['pgid'] and item['direct_child_reaped'] is True
                    and not item.get('remaining_process_group') and not item.get('remaining_after_cleanup')
                    and not item.get('cleanup_errors'), 'Native cleanup incomplete')
            records.append(dict(benchmark=bench, pid=item['pid']))
    require(records == report['registered_commands'] and len(records) == report['native_processes_started']
            and len({r['pid'] for r in records}) == len(records) and
            [r['benchmark'] for r in records] == allowed[:len(records)], 'Registered native sequence differs')
    if report['status'] == SUCCESS:
        require(len(records) == len(report['profiles']) == 2 and
                [p['benchmark'] for p in report['profiles']] == allowed and
                set(report['validated_artifacts']) == set(allowed), 'Successful two-process capture incomplete')


def execution_closure(plan):
    b.execution_inputs(plan)
    require(b.inventory(Path(plan['compiled']['report']).parent, ('report.json', 'terminal.json'))
            == plan['compiled']['artifacts'], 'Compilation evidence changed')
    prior = plan['bounded_prerequisite']
    require(b.inventory(Path(prior['report']).parent, ('terminal.json',)) == prior['artifacts'],
            'Bounded prerequisite artifact inventory changed')


def finish(report, plan, output, pins, lock):
    errors = []
    available = {}
    held = False
    def check(action, name):
        try:
            action()
        except BaseException as error:
            errors.append(dict(path=name, error=str(error) or type(error).__name__))
    check(lambda: process_closure(report, plan, output), '<process-closure>')
    def artifacts():
        nonlocal available
        require(not (output/'terminal.json').exists(), 'Terminal already exists')
        available = b.inventory(output, ('report.json',))
        for bench, snapshot in report['validated_artifacts'].items():
            require({n[len(bench)+1:]: v for n, v in available.items() if n.startswith(bench+'/')} == snapshot,
                    'Validated capture artifacts changed')
        report['artifacts'] = available
    check(artifacts, '<artifact-inventory>')
    check(lambda: b.verify(pins), '<input-pins>')
    check(lambda: execution_closure(plan), '<execution-inputs>')
    try:
        kb.kh.verify_lock(lock)
        held = True
    except BaseException as error:
        errors.append(dict(path='<common-mutex>', error=str(error)))
    report.update(active=None, integrity_errors=errors, finished_at=datetime.now(timezone.utc).isoformat())
    if errors:
        report['status'] = 'failed-integrity'
    kb.save(output/'report.json', report)
    def final_inventory():
        nonlocal available
        current = b.inventory(output, ('terminal.json',))
        require({n: v for n, v in current.items() if n != 'report.json'} == report.get('artifacts'),
                'Final artifacts changed after validation')
        available = current
    check(final_inventory, '<terminal-inventory>')
    check(lambda: b.verify(pins), '<final-input-pins>')
    check(lambda: execution_closure(plan), '<final-execution-inputs>')
    try:
        kb.kh.verify_lock(lock)
    except BaseException as error:
        held = False
        errors.append(dict(path='<final-common-mutex>', error=str(error)))
    if errors:
        report['status'] = 'failed-integrity'
        kb.save(output/'report.json', report)
        available['report.json'] = dict(bytes=(output/'report.json').stat().st_size, sha256=sha(output/'report.json'))
    terminal = dict(schema='scala-two-single-entry-terminal-v1', status=report['status'],
        report_sha256=sha(output/'report.json'), available_evidence=available, integrity_errors=errors,
        native_processes_started=report['native_processes_started'], registered_commands=report['registered_commands'],
        common_mutex_held=held, common_mutex_inode=79859134, source_work_qualified=False,
        full_timings_qualified=False, benchmark_samples=0, chart_admission=False)
    with (output/'terminal.json').open('x') as stream:
        json.dump(terminal, stream, indent=2)
        stream.write('\n')


def prepare(args):
    b.physical(args.plan)
    require(not args.plan.exists() and not args.plan.is_relative_to(args.output), 'Fresh plan outside output required')
    with kb.LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        kb.kh.verify_lock(lock)
        b.checked_python()
        plan = build_plan(args.output)
        b.verify(plan['pins'])
        kb.kh.verify_lock(lock)
        args.plan.parent.mkdir(parents=True, exist_ok=True)
        with args.plan.open('x') as stream:
            json.dump(plan, stream, indent=2)
            stream.write('\n')
    print(json.dumps(dict(plan=str(args.plan), sha256=sha(args.plan), native_processes=0)))


def run(args):
    b.physical(args.plan)
    with kb.LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        kb.kh.verify_lock(lock)
        b.checked_python()
        pins = {}
        plan = b.document(args.plan, args.plan_sha256, pins)
        output = Path(plan['output'])
        require(plan == build_plan(output), 'Diagnostic plan differs from exact retained prerequisites')
        for name, digest in plan['pins'].items():
            b.bind(pins, name, digest)
        b.verify(pins)
        output.mkdir(parents=True, exist_ok=False)
        report = dict(schema='scala-two-single-entry-results-v1', status='running', pins=pins,
            plan=str(args.plan), plan_sha256=args.plan_sha256, started_at=datetime.now(timezone.utc).isoformat(),
            active=None, profiles=[], native_processes_started=0, registered_commands=[], validated_artifacts={},
            source_work_qualified=False, full_timings_qualified=False, benchmark_samples=0, chart_admission=False)
        kb.save(output/'report.json', report)
        try:
            for profile in plan['profiles']:
                b.execution_inputs(plan)
                kb.kh.verify_lock(lock)
                bench = profile['benchmark']
                directory = output/bench
                directory.mkdir()
                (directory/'home').mkdir()
                (directory/'tmp').mkdir()
                (directory/'expected.stdout').write_bytes(expected_output(bench))
                command, env = command_for(plan, profile, directory)
                def launched(pid):
                    report['native_processes_started'] += 1
                    report['registered_commands'].append(dict(benchmark=bench, pid=pid))
                    report['active'] = dict(benchmark=bench, pid=pid)
                    kb.save(output/'report.json', report)
                kb.observe(command, env, directory, b'', lock, launched, kind='scala-single-entry-work')
                snapshot = b.inventory(directory)
                result = checked_capture(plan, profile, directory, os.getpid())
                require(b.inventory(directory) == snapshot, 'Capture changed during validation')
                report['profiles'].append(result)
                report['validated_artifacts'][bench] = snapshot
                report['active'] = None
                kb.save(output/'report.json', report)
            report['status'] = SUCCESS
        except BaseException as error:
            report.update(status='failed', error=str(error) or type(error).__name__, error_type=type(error).__name__)
        finally:
            with kb.atomic():
                finish(report, plan, output, pins, lock)
        print(json.dumps(dict(status=report['status'], native_processes=report['native_processes_started'],
                              report_sha256=sha(output/'report.json'))))
        return 0 if report['status'] == SUCCESS else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='mode', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--plan', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    execute = commands.add_parser('run')
    execute.add_argument('--plan', type=Path, required=True)
    execute.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    def interrupted(signum, frame):
        raise KeyboardInterrupt('Scala diagnostic interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS:
        signal.signal(sig, interrupted)
    return prepare(args) if args.mode == 'prepare' else run(args)


if __name__ == '__main__':
    raise SystemExit(main())
