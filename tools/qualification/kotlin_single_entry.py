#!/usr/bin/env python3
"""Capture four unchanged Kotlin mains once, at prescribed tree/pi inputs.

prepare verifies retained closures under the common mutex; run starts only the
four JVMs. Native code capture is evidence for an explicit owner review, never
an automatic claim that machine-code semantics satisfy the work contract.
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

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/kotlin/single-entry-work-v1'
WORK = ROOT/'experiments/kotlin/compiled-work-v1'
# The exact previously reviewed work-controller bytes, not a mutable import.
WORK_CONTROLLER_SHA = '7a24ddefd83ca03e3135adc43334f91e935f944379e435da1d37be78a5bbecc2'
REPORT_SHA = '85060333d1a2287ecd0897d80c86d77712c8b7ddffc5a97a077a2ea4d62f3d24'
TERMINAL_SHA = '38070e4fd756fbb4c8dc8888b3f87a5063b4f38313ca2c50971e714bca234b25'
SUPERVISOR_SHA = '1b94c74eaeab6eb21046084fd648ae5759307c86d747773b32f0c9b32242888b'
INPUTS = {'binarytrees': 21, 'pidigits': 10000}
IDS = ['kotlin-'+bench+'-'+form for bench in INPUTS for form in ('compact','optimized')]
FULL_OUTPUTS = {
    'binarytrees': (455, '341de11a51feab3d8122b4b5d6a68b038a2d14434aa9bc2372f39300bf5f48e1'),
    'pidigits': (16893, 'bdfa7b6c756d96492f472f97aee9cc139bee954d271eacedfd7ace5d2875f06c'),
}
PRINT_TARGETS = {
    'binarytrees': ['clbg.binarytrees.MainKt::main', 'clbg.binarytrees.MainKt::tree',
                    'clbg.binarytrees.MainKt::check'],
    'pidigits': ['clbg.pidigits.MainKt::main', 'java.math.BigInteger::divide*',
                'java.math.MutableBigInteger::divide*'],
}


def require(value, message):
    if not value: raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream, 'sha256').hexdigest()


def load_work():
    path = ROOT/'tools/qualification/kotlin_work_v2.py'
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == WORK_CONTROLLER_SHA, 'Work controller changed')
    spec = importlib.util.spec_from_file_location('single_entry_retained_work', path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


kw = load_work()


def load_supervisor():
    path = ROOT/'tools/qualification/kotlin_single_entry_supervisor.py'
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == SUPERVISOR_SHA, 'Single-entry supervisor policy changed')
    spec = importlib.util.spec_from_file_location('single_entry_supervisor_policy',path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),module.__dict__)
    return module.supervisor


kb = load_supervisor()
save, atomic = kb.save, kb.atomic


def bind(path, digest, pins):
    path = Path(path).resolve()
    require(sha(path) == digest and pins.get(str(path), digest) == digest, 'Pinned input changed: '+str(path))
    pins[str(path)] = digest
    return path


def read(path, digest, pins):
    path = bind(path, digest, pins)
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'JSON changed during read')
    return json.loads(raw)


def expected_output(benchmark):
    if benchmark == 'pidigits':
        result = (ROOT/'archive/workloads/pidigits/inputs/output-full.txt').read_bytes()
    else:
        require(benchmark == 'binarytrees', 'Unexpected workload')
        n = INPUTS[benchmark]
        rows = [f'stretch tree of depth {n+1}\t check: {(1 << (n+2))-1}\n']
        for depth in range(4, n+1, 2):
            iterations = 1 << (n-depth+4)
            rows.append(f'{iterations}\t trees of depth {depth}\t check: {iterations*((1 << (depth+1))-1)}\n')
        rows.append(f'long lived tree of depth {n}\t check: {(1 << (n+1))-1}\n')
        result = ''.join(rows).encode('ascii')
    require((len(result), hashlib.sha256(result).hexdigest()) == FULL_OUTPUTS[benchmark],
            'Prescribed complete output reference changed')
    return result


def options(benchmark, directory):
    return kb.FLAGS + [f'-Duser.home={directory}/home', f'-Djava.io.tmpdir={directory}/tmp',
        '-XX:+UnlockDiagnosticVMOptions', '-XX:+LogCompilation', '-XX:+LogVMOutput',
        '-XX:-DisplayVMOutput', f'-XX:LogFile={directory}/hotspot.xml',
        '-XX:CompileCommand=quiet'] + ['-XX:CompileCommand=print,'+p for p in PRINT_TARGETS[benchmark]] + [
        f'-Xlog:class+load=info:file={directory}/classes.log:uptime,tags',
        f'-Xlog:gc*=info:file={directory}/gc.log:uptime,tags']


def validate_prerequisite(report, terminal):
    status = 'all20-bounded-work-witnesses-recorded-with-separate-open-gates'
    require(report['schema'] == 'kotlin-retained-compiled-work-results-v1' and
            report['status'] == terminal['status'] == status and terminal['report_sha256'] == REPORT_SHA and
            report['active'] is None and len(report['profiles']) == 20 and
            len({p['id'] for p in report['profiles']}) == 20, 'Incomplete original work cohort')
    for key, value in [('native_processes_started', 21), ('diagnostic_compiler_processes_started', 1),
                       ('work_jvm_processes_started', 20), ('observed_main_invocations', 200000),
                       ('observed_main_returns', 200000)]:
        require(report[key] == terminal[key] == value, 'Wrong original execution count: '+key)
    for key in ('required_work_witnesses_qualified', 'subject_JIT_method_evidence_qualified',
                'actual_subject_runtime_dependency_closure_qualified', 'specified_case_coverage_qualified'):
        require(report[key] is True and terminal[key] is True, 'Original prerequisite unqualified: '+key)
    for key in ('integrity_errors', 'process_receipt_errors', 'missing_main_observations'):
        require(report[key] == terminal[key] == [], 'Original work integrity error')
    require(terminal['artifact_errors'] == [] and terminal['common_mutex_held'] is True and
            terminal['common_mutex_inode'] == kb.LOCK_INODE and
            report['source_work_qualified'] is False and report['benchmark_samples'] == 0,
            'Wrong original work scope or closure')


def closed_artifacts(directory, terminal, pins):
    errors = []
    paths = kw.inventory_files(directory, errors)
    actual = {str(p.relative_to(directory)) for p in paths if p != directory/'terminal.json'}
    require(not errors and actual == set(terminal['available_evidence']), 'Original artifact inventory changed')
    for name, item in terminal['available_evidence'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'Unsafe artifact path')
        path = bind(directory/name, item['sha256'], pins)
        require(path.stat().st_size == item['bytes'], 'Original artifact size changed')


def prepare(args):
    require(not args.plan.exists() and not args.output.exists() and
            not args.plan.resolve().is_relative_to(args.output.resolve()), 'Fresh plan and separate fresh output required')
    pins = {}
    report = read(WORK/'run-v2/report.json', REPORT_SHA, pins)
    terminal = read(WORK/'run-v2/terminal.json', TERMINAL_SHA, pins)
    validate_prerequisite(report, terminal)
    prior = read(report['plan'], report['plan_sha256'], pins)
    require(prior['controller_sha256'] == WORK_CONTROLLER_SHA and prior['planned_native_commands'] == 21,
            'Wrong original work plan/controller')
    for path, digest in report['pins'].items(): bind(path, digest, pins)
    closed_artifacts(WORK/'run-v2', terminal, pins)
    require(kw.reconcile_native(report, WORK/'run-v2', prior) == [], 'Original native receipts do not reconcile')
    validate_prerequisite(report, terminal)
    rows = [next(row for row in prior['profiles'] if row['id'] == identity) for identity in IDS]
    require(all(row['benchmark'] in INPUTS and row['main_owner'] == 'clbg.'+row['benchmark']+'.MainKt'
                for row in rows), 'Wrong retained main inventory')
    # All source/class/runtime pins remain inherited, including both alias sets.
    for path in (Path(__file__).resolve(), ROOT/'tools/qualification/kotlin_work_v2.py',
                 ROOT/'tools/qualification/kotlin_single_entry_supervisor.py',
                 WORK/'single-entry-review.md', PACKET/'README.md', PACKET/'capture-capability.json',
                 PACKET/'capture-capability.md',
                 ROOT/'archive/workloads/pidigits/inputs/output-full.txt', kb.kh.PYTHON):
        bind(path, sha(path), pins)
    require(pins[str(kb.kh.PYTHON)] == kb.kh.PYTHON_SHA, 'Wrong controller interpreter')
    capability = json.loads((PACKET/'capture-capability.json').read_bytes())
    require(capability['schema'] == 'kotlin-single-entry-capture-capability-v1' and
            capability['retained_java'] == prior['java'] and
            capability['native_execution_performed'] is False and
            capability['diagnostic_output_route'] == 'HotSpot XML print_nmethod; VM display disabled' and
            capability['runtime_policy_changes'] == [] and capability['capture_requires_actual_validation'] is True,
            'Unreviewed capture capability audit')
    java_home = Path(prior['java']).parent.parent
    require(set(capability['retained_runtime_pins']) ==
            {prior['java'], str(java_home/'lib/server/libjvm.dylib')}, 'Capture audit runtime pins incomplete')
    for path, digest in capability['retained_runtime_pins'].items():
        require(prior['pins'].get(path) == digest, 'Capability audit names a different runtime')
    for benchmark in INPUTS: expected_output(benchmark)
    plan = dict(schema='kotlin-single-entry-work-plan-v1', status='prepared-awaiting-four-native-captures',
        controller_sha256=sha(__file__), prior_report=str((WORK/'run-v2/report.json').resolve()),
        prior_report_sha256=REPORT_SHA, prior_terminal_sha256=TERMINAL_SHA, pins=pins,
        profiles=rows, ids=IDS, prescribed_inputs=INPUTS, print_targets=PRINT_TARGETS,
        java=prior['java'], stdlib=prior['stdlib'], runtime_expected=prior['runtime_expected'],
        output=str(args.output.resolve()), capability=capability, full_outputs=FULL_OUTPUTS,
        planned_native_commands=4, main_entry='direct JVM launcher; one main call; no warmup wrapper',
        process_timeout_seconds=kb.TIMEOUT, cleanup_timeout_seconds=kb.CLEANUP_TIMEOUT,
        maximum_process_group_rss_bytes=kb.RSS_LIMIT, native_file_limit_bytes=kb.FILE_LIMIT,
        supervisor_policy_sha256=SUPERVISOR_SHA,
        automatic_retries=0, subject_recompilations=0, diagnostic_compilations=0,
        benchmark_samples=0, source_work_qualified=False, full_timings_qualified=False, chart_admission=False)
    args.plan.parent.mkdir(parents=True, exist_ok=True)
    require(not args.plan.exists(), 'Plan appeared during prepare')
    save(args.plan, plan)
    print(json.dumps(dict(plan=str(args.plan), sha256=sha(args.plan), native_executions=0)), flush=True)


def validate_classes(text, row, stdlib):
    observed = {}
    owners = set(row['class_owner_names'])
    for line in text.splitlines():
        if '[class,load]' not in line: continue
        match = re.search(r'\[class,load\]\s+(\S+) source: (.+)$', line)
        require(match, 'Malformed class-load record')
        owner, source = match.groups()
        if owner.startswith('clbg.'): require(owner in owners, 'Unexpected subject owner')
        if source.startswith('file:'):
            require(owner in owners or owner.startswith('kotlin.'), 'Unexpected non-platform owner')
            require(kb.uri_path(source) == Path(row['classes'] if owner in owners else stdlib).resolve(),
                    'Unexpected actual class origin')
        else:
            hidden = re.fullmatch(r'(.+)\$\$Lambda(?:\$\d+)?/0x[0-9a-fA-F]+', owner)
            enclosing = hidden[1] if hidden else None
            host = observed.get(source, '')
            platform_lambda = (enclosing is not None and (enclosing == source or enclosing.startswith(source+'$'))
                and source.startswith(('java.', 'jdk.', 'sun.', 'com.sun.'))
                and host.startswith(('jrt:/', 'shared objects file')) and observed.get(enclosing) == host)
            require(source.startswith(('jrt:/', 'shared objects file')) or platform_lambda or
                    (source == '__JVM_LookupDefineClass__' and owner.startswith(('java.', 'jdk.'))),
                    'Unknown actual class origin')
        observed[owner] = source
    require(row['main_owner'] in observed and 'clbg.Support' in observed, 'Main/helper class evidence missing')
    return observed


def targeted(method, benchmark):
    parts = method.split(' ', 2)
    if len(parts) != 3: return False
    owner, name, _ = parts
    return (owner == 'clbg.'+benchmark+'.MainKt' and name in
            ({'main','tree','check'} if benchmark == 'binarytrees' else {'main'})) or (
            benchmark == 'pidigits' and owner in ('java.math.BigInteger','java.math.MutableBigInteger')
            and name.startswith('divide'))


def instruction_coverage(text, entry):
    require(text.count('[MachCode]') == text.count('[/MachCode]') == 1, 'Incomplete native MachCode boundaries')
    region = re.search(r'main code\s+\[(0x[0-9a-fA-F]+),(0x[0-9a-fA-F]+)\]\s*=\s*(\d+)', text)
    require(region, 'Missing native main-code address range')
    start, end, size = int(region[1],16), int(region[2],16), int(region[3])
    require(end-start == size and size > 0 and start <= int(entry,16) < end,
            'Native main-code range/entry differs')
    body = text.split('[MachCode]',1)[1].split('[/MachCode]',1)[0]
    lines = re.findall(r'^\s*(0x[0-9a-fA-F]+):\s+((?:[0-9a-fA-F]{2,16}(?:[\s|]+|$))+)', body, re.M)
    coverage = set()
    for address, raw in lines:
        digits = ''.join(re.split(r'[\s|]+',raw.strip()))
        require(len(digits)%2 == 0, 'Malformed native byte group')
        position = int(address,16)
        for offset in range(len(digits)//2):
            byte = position+offset
            if start <= byte < end:
                require(byte not in coverage, 'Overlapping native byte rows')
                coverage.add(byte)
    require(len(coverage) == size, 'Native instruction bytes do not cover the main-code range')
    return dict(start=hex(start), end=hex(end), bytes=size, retained_instruction_rows=len(lines))


def capture_index(path, benchmark):
    root = ET.parse(path).getroot()
    require(root.tag == 'hotspot_log' and root.find('hotspot_log_done') is not None, 'Incomplete HotSpot XML')
    require(root.find('vm_arguments') is not None, 'Missing actual JVM command identity')
    prints = {}
    for node in root.iter('print_nmethod'):
        identity = node.get('compile_id')
        require(identity and identity not in prints, 'Missing/duplicate native print identity')
        prints[identity] = ''.join(node.itertext())
    natives = [n for n in root.iter('nmethod') if targeted(n.get('method',''), benchmark)]
    owner = 'clbg.'+benchmark+'.MainKt '
    wanted = {owner+'main ([Ljava/lang/String;)V'}
    if benchmark == 'binarytrees':
        wanted |= {owner+'tree (I)Lclbg/binarytrees/Node;', owner+'check (Lclbg/binarytrees/Node;)J'}
    require(wanted <= {n.get('method') for n in natives}, 'Required single-entry JIT methods missing')
    rows = []
    for node in natives:
        identity = node.get('compile_id'); text = prints.get(identity, '')
        require(node.get('compiler') in ('c1','c2') and text, 'Missing emitted native code: '+str(identity))
        coverage = instruction_coverage(text,node.get('entry',''))
        maps = [line.strip() for line in text.splitlines() if 'ImmutableOopMap' in line]
        if node.get('method','').startswith('clbg.'):
            require(maps, 'Subject native code lacks OopMap capture: '+identity)
        rows.append(dict(node.attrib, instruction_coverage=coverage, oopmap_count=len(maps),
                         native_text_sha256=hashlib.sha256(text.encode()).hexdigest()))
    eliminated = []; installed = {n.get('compile_id') for n in root.iter('nmethod')}
    for task in root.iter('task'):
        names = {n.get('id'):n.get('name') for n in task.iter('klass')}
        methods = {n.get('id'):n.get('name') for n in task.iter('method')}
        for node in task.iter('eliminate_allocation'):
            if names.get(node.get('type')) != 'clbg.binarytrees.Node': continue
            eliminated.append(dict(compile_id=task.get('compile_id'), compilation=task.get('method'),
                compile_kind=task.get('compile_kind'),
                installed_nmethod=task.get('compile_id') in installed,
                locations=[dict(method=methods.get(n.get('method')), bci=n.get('bci')) for n in node]))
    return dict(status='native-code-and-oopmaps-captured-awaiting-instruction-review',
        native_methods=rows, node_allocation_eliminations=eliminated,
        source_work_qualified=False, optimized_main_allocation_and_lifetime_proved=False,
        runtime_pi_division_counts_proved=False)


def validate_vm_identity(path, row, plan, directory, receipt):
    root = ET.parse(path).getroot()
    require(root.get('process') == str(receipt['pid']), 'Compiler log belongs to another process')
    args = root.find('vm_arguments')
    require(args is not None and args.findtext('args','').strip().split() == options(row['benchmark'],directory) and
            args.findtext('command','').strip() == row['main_owner']+' '+str(INPUTS[row['benchmark']]) and
            args.findtext('launcher','').strip() == 'SUN_STANDARD', 'Actual JVM launch/flags differ')
    properties = dict(line.split('=',1) for line in args.findtext('properties','').strip().splitlines() if '=' in line)
    expected = {'java.home':str(Path(plan['java']).parent.parent),
                'java.class.path':row['classes']+os.pathsep+plan['stdlib'],
                'java.vm.version':plan['runtime_expected']['RUNTIME_VERSION'],
                'java.vm.name':plan['runtime_expected']['VM_NAME'],
                'java.vm.vendor':plan['runtime_expected']['VENDOR'],
                'user.home':str(directory/'home'), 'java.io.tmpdir':str(directory/'tmp')}
    require(all(properties.get(k) == v for k,v in expected.items()), 'Actual JVM identity properties differ')
    require('for bsd-'+plan['runtime_expected']['OS_ARCH']+' ' in root.findtext('vm_version/info',''),
            'Actual JVM architecture differs')


def validate_receipt(receipt, directory, command, environment):
    require(receipt['kind'] == 'single-entry-work' and receipt['status'] == 'native-passed' and
            receipt['native_process_started'] is True and receipt['direct_child_reaped'] is True and
            receipt['exit_status'] == 0 and receipt['command'] == command and
            receipt['environment'] == environment and receipt['cwd'] == str(directory) and
            receipt['pid'] == receipt['pgid'] and type(receipt['pid']) is int and receipt['pid'] > 0 and
            receipt['inherited_common_mutex'] is True and receipt['common_mutex_inode'] == kb.LOCK_INODE and
            receipt['stdin_bytes'] == 0 and receipt['stdin_sha256'] == hashlib.sha256(b'').hexdigest(),
            'Native single-entry receipt differs')
    for key in ('error','error_type','stop_signals','cleanup_errors','artifact_errors',
                'remaining_process_group','remaining_after_cleanup','timed_out'):
        require(not receipt.get(key), 'Native process did not close cleanly: '+key)
    for key, value in [('process_timeout_seconds',kb.TIMEOUT),('cleanup_timeout_seconds',kb.CLEANUP_TIMEOUT),
                       ('maximum_process_group_rss_bytes',kb.RSS_LIMIT),('native_file_limit_bytes',kb.FILE_LIMIT),
                       ('stdout_capture_limit_bytes',kb.FILE_LIMIT+kb.PIPE_CHUNK)]:
        require(receipt[key] == value, 'Native bound differs: '+key)
    before, after = receipt['identity'], receipt['leader_identity_before_reap']
    require(all(before[k] == after[k] for k in ('pid','pgid','ppid','birth_seconds','birth_microseconds')) and
            before['pid'] == before['pgid'] == receipt['pid'] and before['ppid'] == os.getpid() and
            after['status'] == 5 and receipt['kernel_monitor_samples'] > 0 and
            0 <= receipt['observed_peak_process_group_rss_bytes'] <= kb.RSS_LIMIT, 'Native ownership proof differs')
    for stream in ('stdout','stderr'):
        path = directory/(stream+'.bin')
        require(receipt[stream+'_bytes'] == path.stat().st_size and receipt[stream+'_sha256'] == sha(path),
                'Native stream receipt differs')
    require(receipt['stderr_bytes'] == 0, 'Unexpected native stderr')


def snapshot(directory):
    errors = []; paths = kw.inventory_files(directory, errors)
    require(not errors, 'Native artifact inventory failed')
    return {str(p.relative_to(directory)):dict(bytes=p.stat().st_size, sha256=sha(p)) for p in paths}


def finish(report, plan, pins, output, lock):
    errors = []; native = []
    for identity in IDS:
        path = output/identity/'process.json'
        if not path.exists(): continue
        try:
            receipt = json.loads(path.read_bytes())
            require(receipt['kind'] == 'single-entry-work', 'Unexpected native receipt kind')
            if receipt['native_process_started']:
                native.append(dict(id=identity, pid=receipt['pid'], pgid=receipt['pgid']))
            if report['status'] == 'all4-native-captures-awaiting-instruction-review':
                validate_receipt(receipt, path.parent, report['commands'][identity]['argv'],
                                 report['commands'][identity]['environment'])
            require((not receipt['native_process_started'] or receipt['direct_child_reaped']) and
                    not receipt.get('cleanup_errors') and
                    not receipt.get('remaining_after_cleanup') and not receipt.get('remaining_process_group'),
                    'Native process cleanup incomplete')
        except BaseException as error: errors.append(dict(path=str(path), error=str(error)))
    if native != report['registered_native_commands'] or len(native) != report['native_processes_started']:
        errors.append(dict(error='Registered and saved native identities differ'))
    if report['status'] == 'all4-native-captures-awaiting-instruction-review' and (
            [p['id'] for p in report['profiles']] != IDS or len(native) != 4 or
            set(report['validated_command_artifacts']) != set(IDS)):
        errors.append(dict(error='Incomplete successful four-form inventory'))
    for identity, prior in report['validated_command_artifacts'].items():
        try: require(snapshot(output/identity) == prior, 'Validated artifacts changed')
        except BaseException as error: errors.append(dict(id=identity, error=str(error)))
    integrity = []
    for path, digest in pins.items():
        try: require(sha(path) == digest, 'Pinned input changed')
        except BaseException as error: integrity.append(dict(path=path, error=str(error)))
    if errors or integrity: report['status'] = 'failed-integrity-or-closure'
    else: report['active'] = None
    report.update(process_receipt_errors=errors, integrity_errors=integrity,
                  finished_at=datetime.now(timezone.utc).isoformat())
    kb.kh.verify_lock(lock)
    save(output/'report.json', report)
    artifacts = {}; artifact_errors = []
    for path in kw.inventory_files(output, artifact_errors):
        try: artifacts[str(path.relative_to(output))] = dict(bytes=path.stat().st_size, sha256=sha(path))
        except BaseException as error: artifact_errors.append(dict(path=str(path), error=str(error)))
    if artifact_errors:
        report.update(status='failed-artifact-retention', artifact_errors=artifact_errors)
        save(output/'report.json', report)
        artifacts['report.json'] = dict(bytes=(output/'report.json').stat().st_size, sha256=sha(output/'report.json'))
    kb.kh.verify_lock(lock)
    save(output/'terminal.json', dict(schema='kotlin-single-entry-work-terminal-v1', status=report['status'],
        report_sha256=sha(output/'report.json'), available_evidence=artifacts,
        native_processes_started=report['native_processes_started'], registered_native_commands=native,
        process_receipt_errors=errors, integrity_errors=integrity, artifact_errors=artifact_errors, common_mutex_held=True,
        common_mutex_inode=kb.LOCK_INODE, source_work_qualified=False,
        subject_recompilations=0, diagnostic_compilations=0, benchmark_samples=0,
        full_timings_qualified=False, chart_admission=False))
    require(not errors and not integrity and not artifact_errors, 'Single-entry artifact or native closure failed')


def run(args, lock):
    pins = {}; plan = read(args.plan, args.plan_sha256, pins)
    require(plan['schema'] == 'kotlin-single-entry-work-plan-v1' and plan['controller_sha256'] == sha(__file__) and
            plan['ids'] == IDS and [p['id'] for p in plan['profiles']] == IDS and
            plan['prescribed_inputs'] == INPUTS and plan['print_targets'] == PRINT_TARGETS and
            plan['planned_native_commands'] == 4 and plan['prior_report_sha256'] == REPORT_SHA and
            plan['prior_terminal_sha256'] == TERMINAL_SHA and plan['automatic_retries'] == 0 and
            plan['supervisor_policy_sha256'] == SUPERVISOR_SHA and
            plan['maximum_process_group_rss_bytes'] == kb.RSS_LIMIT and
            plan['process_timeout_seconds'] == kb.TIMEOUT and plan['native_file_limit_bytes'] == kb.FILE_LIMIT,
            'Wrong single-entry plan/controller')
    pins.update(plan['pins'])
    for path, digest in pins.items(): require(sha(path) == digest, 'Preflight input changed: '+path)
    output = Path(plan['output']); require(not output.exists(), 'Fresh output required; no retry')
    output.mkdir(parents=True)
    report = dict(schema='kotlin-single-entry-work-results-v1', status='running', plan=str(args.plan.resolve()),
        plan_sha256=args.plan_sha256, started_at=datetime.now(timezone.utc).isoformat(), pins=pins,
        profiles=[], active=None, native_processes_started=0, registered_native_commands=[], commands={},
        validated_command_artifacts={}, subject_recompilations=0, diagnostic_compilations=0,
        benchmark_samples=0, source_work_qualified=False, optimized_main_allocation_and_lifetime_proved=False,
        runtime_pi_division_counts_proved=False, full_timings_qualified=False, chart_admission=False)
    save(output/'report.json', report)
    try:
        for row in plan['profiles']:
            identity = row['id']; benchmark = row['benchmark']; kb.kh.verify_lock(lock)
            classes = Path(row['classes'])
            require({str(p.relative_to(classes)) for p in classes.rglob('*') if p.is_file()} ==
                    {a['relative_path'] for a in row['class_artifacts']} and
                    not any(p.is_symlink() for p in classes.rglob('*')), 'Retained class directory changed')
            for item in row['physical_inputs']+row['class_artifacts']:
                require(sha(item['path']) == item['sha256'], 'Active retained source/class changed')
            directory = output/identity; directory.mkdir()
            environment = kb.kh.environment(row['runtime_environment'], directory)
            expected = expected_output(benchmark); (directory/'expected.stdout').write_bytes(expected)
            command = [plan['java']]+options(benchmark,directory)+['-cp',row['classes']+os.pathsep+plan['stdlib'],
                row['main_owner'],str(INPUTS[benchmark])]
            report['commands'][identity] = dict(argv=command, environment=environment)
            report['active'] = dict(id=identity, receipt=str(directory/'process.json'), pid=None)
            save(output/'report.json', report)
            def launched(pid):
                report['native_processes_started'] += 1
                report['registered_native_commands'].append(dict(id=identity,pid=pid,pgid=pid))
                report['active']['pid'] = pid; save(output/'report.json', report)
            receipt = kb.observe(command, environment, directory, b'', lock, launched, kind='single-entry-work')
            validate_receipt(receipt,directory,command,environment)
            require((directory/'stdout.bin').read_bytes() == expected, 'Prescribed complete stdout differs')
            loaded = validate_classes((directory/'classes.log').read_text(), row, plan['stdlib'])
            require('Using G1' in (directory/'gc.log').read_text(), 'Actual G1 log missing')
            validate_vm_identity(directory/'hotspot.xml',row,plan,directory,receipt)
            capture = capture_index(directory/'hotspot.xml', benchmark)
            save(directory/'capture-index.json', capture)
            require(not any(n['installed_nmethod'] for n in capture['node_allocation_eliminations']),
                    'Installed native code eliminates required Node allocation; retain for entry-reachability review')
            result = dict(id=identity, n=INPUTS[benchmark], status=capture['status'], complete_output_match=True,
                main_entry='direct JVM launcher; one main call inferred from pinned launch/source, not a probe counter',
                actual_loaded_classes=loaded, capture=capture, source_work_qualified=False)
            save(directory/'validated.json', result)
            report['validated_command_artifacts'][identity] = snapshot(directory)
            report['profiles'].append(result); report['active'] = None
            save(output/'report.json', report)
            print('Captured single-entry Kotlin native code: '+identity, flush=True)
        report['status'] = 'all4-native-captures-awaiting-instruction-review'
    except BaseException as error:
        report.update(status='failed', error=str(error) or type(error).__name__, error_type=type(error).__name__)
        raise
    finally:
        with atomic(): finish(report, plan, pins, output, lock)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='action', required=True)
    prep = commands.add_parser('prepare'); prep.add_argument('--plan', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    execute = commands.add_parser('run'); execute.add_argument('--plan', type=Path, required=True)
    execute.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    require(Path(sys.executable).resolve() == kb.kh.PYTHON.resolve() and sys.flags.isolated and
            sys.flags.no_site and sys.flags.dont_write_bytecode and not sys.flags.optimize,
            'Use the retained Python with -I -S -B and no optimization')
    def interrupted(signum, frame): raise KeyboardInterrupt('Single-entry diagnostic interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS: signal.signal(sig, interrupted)
    with kb.LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB); kb.kh.verify_lock(lock)
        require(sha(kb.kh.PYTHON) == kb.kh.PYTHON_SHA, 'Controller interpreter changed')
        if args.action == 'prepare': prepare(args)
        else: run(args, lock)


if __name__ == '__main__': main()
