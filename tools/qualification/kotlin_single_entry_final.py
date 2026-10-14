#!/usr/bin/env python3
"""Reuse three closed Kotlin captures and observe only the unstarted pi form.

All earlier reports retain their failed status. An uncompiled main is accepted
as capture evidence only with complete compiler logs and the retained bytecode
control flow; neither path grants instruction/work or timing qualification.
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
PACKET = ROOT/'experiments/kotlin/single-entry-final-v1'
SECOND = ROOT/'experiments/kotlin/single-entry-remaining-v1'
SECOND_JOB = ROOT/'experiments/kotlin/dispatch-v1/owned-jobs/single-entry-remaining-three-v1'
REMAINING_SHA = '1daa20808a0f023041ce72c6e5d7578430ac69fcea6ca3ff30f7c48e0ebc5297'
SECOND_PLAN_SHA = 'c56c0e576b4dca9c7867ae2ef66eeddd2a822d43eb130a188d01c2602a4fdf0f'
SECOND_REPORT_SHA = '6602c54ba432d58dc9eca543c1984f3632f3ae02f9659c12d388daf02e951a96'
SECOND_TERMINAL_SHA = '27d43373ff5a30a96ba6682edd1e68daf88170614b110546cbac600d700bb2c9'
SECOND_DURABLE_SHA = '0866dfe66db63fca769a2a3a422116cb017121685936d3c8fae6c1500d0c22d7'
FINAL_ID = 'kotlin-pidigits-optimized'
SECOND_IDS = ['kotlin-binarytrees-optimized', 'kotlin-pidigits-compact']
PI_MAIN = 'clbg.pidigits.MainKt main ([Ljava/lang/String;)V'
PI_SOURCE_SHA = '19685b96cc0e7ec10bbab086f55d1b3d8bfb06268e1c9685d1772dcd9d65b9a6'
PI_CLASS_SHA = 'e9053276207d5211a8ea166af93f8e77a66ec395467eebf879b4da171f2c7456'
COMPLETE = 'final-single-entry-capture-recorded-awaiting-instruction-review'
REVIEW_FILES = {
    'actual-instruction-review.md': '8c54a1f182a18659278dd09d0165796f8d37e92ee04b819309d2733622fcc705',
    'actual-instruction-review-evidence.json': 'ee747ebe79427e53b4b67f435074dc95b55c3298a4b00cf9aecc56dd19f80806',
}


def require(value, message):
    if not value: raise AssertionError(message)


def load_remaining():
    path = ROOT/'tools/qualification/kotlin_single_entry_remaining.py'
    raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == REMAINING_SHA, 'Frozen remaining controller changed')
    spec = importlib.util.spec_from_file_location('final_retained_remaining', path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


previous = load_remaining()
capture, base, kb = previous.capture, previous.base, previous.kb
sha, save, bind, read = base.sha, base.save, base.bind, base.read
REUSED_IDS = [previous.FIRST_ID]+SECOND_IDS


def pi_bytecode(row):
    """Check pinned javap ownership and each normal path through the pi loop."""
    require(row['benchmark'] == 'pidigits' and row['main_owner'] == 'clbg.pidigits.MainKt',
            'Wrong pi source owner')
    source = next(p for p in row['reviewed_source_copies'] if p['role'] == 'application')
    require(source['sha256'] == PI_SOURCE_SHA and sha(source['path']) == PI_SOURCE_SHA,
            'Pi reviewed source changed')
    physical = next(p for p in row['physical_inputs'] if p['role'] == 'application')
    require(physical['sha256'] == PI_SOURCE_SHA, 'Pi physical source binding differs')
    artifact = next(a for a in row['class_artifacts'] if a['relative_path'] == 'clbg/pidigits/MainKt.class')
    require(artifact['sha256'] == PI_CLASS_SHA and sha(artifact['path']) == PI_CLASS_SHA and
            Path(artifact['path']) == Path(row['classes'])/artifact['relative_path'], 'Pi class binding differs')
    disassembly = row['retained_disassembly']; raw = Path(disassembly['path']).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == disassembly['sha256'], 'Retained pi disassembly changed')
    sections = [s for s in re.split(r'(?m)^Classfile ', raw.decode()) if
                '\npublic final class clbg.pidigits.MainKt\n' in s]
    require(len(sections) == 1, 'Missing or duplicate pi disassembly owner')
    section = sections[0]
    require(section.splitlines()[0] == artifact['path'] and
            'SHA-256 checksum '+PI_CLASS_SHA in section, 'Disassembly class origin/checksum differs')
    signature = '  public static final void main(java.lang.String[]);'
    require(section.count(signature) == 1, 'Pi main disassembly missing/duplicated')
    method = section.split(signature, 1)[1].split('\n  public ', 1)[0]
    require('descriptor: ([Ljava/lang/String;)V' in method and 'Exception table:' not in method,
            'Pi main descriptor or exception edges changed')
    code = method.split('    Code:\n', 1)[1].split('      StackMapTable:', 1)[0]
    instructions = {}
    for line in code.splitlines()[1:]:
        match = re.fullmatch(r'\s*(\d+):\s+(\w+)(?:\s+(.*))?', line)
        require(match and int(match[1]) not in instructions, 'Malformed/duplicate pi bytecode row')
        instructions[int(match[1])] = (match[2], match[3] or '')
    positions = list(instructions)
    require(positions == sorted(positions) and positions[0] == 0 and positions[-1] == 559 and
            instructions[559] == ('return', ''), 'Pi bytecode bounds differ')
    divide = 'Method java/math/BigInteger.divide:(Ljava/math/BigInteger;)Ljava/math/BigInteger;'
    equal = 'Method kotlin/jvm/internal/Intrinsics.areEqual:(Ljava/lang/Object;Ljava/lang/Object;)Z'
    require([p for p, (op, args) in instructions.items() if divide in args] == [122, 201] and
            all(instructions[p][0] == 'invokevirtual' for p in (122, 201)) and
            [p for p, (op, args) in instructions.items() if equal in args] == [216] and
            instructions[216][0] == 'invokestatic', 'Pi divides/comparison differ')
    edges = {}
    for index, position in enumerate(positions):
        op, args = instructions[position]
        require(op not in ('tableswitch', 'lookupswitch', 'jsr', 'jsr_w', 'ret', 'athrow', 'wide'),
                'Unsupported pi control-flow instruction')
        following = positions[index+1:index+2]
        if op.startswith('if') or op in ('goto', 'goto_w'):
            require(re.fullmatch(r'\d+', args), 'Malformed pi branch')
            target = int(args); require(target in instructions, 'Pi branch outside instruction boundaries')
            edges[position] = [target]+(following if op.startswith('if') else [])
        elif op.endswith('return'):
            edges[position] = []
        else:
            require(following, 'Pi bytecode falls out of method')
            edges[position] = following
    backedges = [(p, q) for p, targets in edges.items() for q in targets if q <= p]
    require(backedges == [(381, 48), (388, 48), (539, 48)] and edges[51] == [542, 54],
            'Pi loop boundary/backedges differ')
    def reachable(start, forbidden=None):
        seen = set(); pending = [start]
        while pending:
            position = pending.pop()
            if position == forbidden or position in seen: continue
            seen.add(position); pending.extend(edges[position])
        return seen
    require(set(positions) == reachable(0), 'Unexpected unreachable pi bytecode')
    require(all(216 not in reachable(48, p) for p in (122, 201)) and
            201 not in reachable(48, 122) and 216 in reachable(48),
            'Both ordered general divides must dominate every comparison')
    return dict(source_sha256=PI_SOURCE_SHA, class_sha256=PI_CLASS_SHA,
        disassembly=disassembly, bytecode_length=560, loop_header_bci=48, divide_bcis=[122, 201], comparison_bci=216,
        backedges=[list(edge) for edge in backedges], exception_handlers=0,
        ordered_divides_dominate_each_comparison=True, numeric_runtime_division_count_proved=False)


def compilation_closure(root):
    records = {}
    for tag in ('task_queued', 'task', 'nmethod'):
        nodes = list(root.iter(tag)); records[tag] = {n.get('compile_id'): n for n in nodes}
        require(None not in records[tag] and len(nodes) == len(records[tag]),
                'Missing/duplicate '+tag+' compilation identity')
    installed = {key: node for key, node in records['nmethod'].items() if node.get('compiler') in ('c1', 'c2')}
    require(set(records['task_queued']) == set(records['task']) == set(installed),
            'Queued/task/installed compiler inventory incomplete')
    for identity, node in installed.items():
        task, queued = records['task'][identity], records['task_queued'][identity]
        require(all(node.get(k) == task.get(k) == queued.get(k) for k in ('method', 'compile_kind', 'bytes')) and
                task.get('osr_bci') == queued.get('osr_bci'), 'Compilation method/entry linkage differs')
        done = list(task.iter('task_done'))
        require(len(done) == 1 and done[0].get('success') == '1', 'Compiler task lacks one successful completion')
        if node.get('compile_kind') == 'osr':
            require(re.fullmatch(r'\d+', task.get('osr_bci', '')), 'OSR compilation entry missing')
    require(all(node.get('compile_kind') in ('c2n', 'cnt') for key, node in records['nmethod'].items()
                if key not in installed), 'Unknown non-compiler native installation')
    return dict(queued_tasks=len(records['task_queued']), completed_tasks=len(records['task']),
                installed_compiler_methods=len(installed), installed_native_wrappers=len(records['nmethod'])-len(installed))


def pi_index(path, row):
    root = ET.parse(path).getroot()
    require(root.tag == 'hotspot_log' and len(root.findall('hotspot_log_done')) == 1 and
            root.find('vm_arguments') is not None, 'Incomplete actual HotSpot XML')
    bad_tags = {'failure', 'error', 'fatal_error', 'code_cache_full', 'compilation_disabled',
                'compiler_thread_error', 'make_not_compilable', 'log_error'}
    require(not any(n.tag in bad_tags for n in root.iter()) and
            all(n.get('success') == '1' for n in root.iter('task_done')),
            'Compiler or logging failure prevents complete execution-path evidence')
    closure = compilation_closure(root)
    bytecode = pi_bytecode(row)
    main_events = {tag: [n for n in root.iter(tag) if n.get('method') == PI_MAIN]
                   for tag in ('task_queued', 'task', 'nmethod')}
    main_references = []
    for task in root.iter('task'):
        classes = {n.get('id'): n.get('name', '').replace('/', '.') for n in task.iter('klass')}
        for method in task.iter('method'):
            if classes.get(method.get('holder')) == 'clbg.pidigits.MainKt' and method.get('name') == 'main':
                main_references.append(dict(compile_id=task.get('compile_id'), owner=task.get('method'),
                                            method_id=method.get('id')))
    compiled = bool(main_events['nmethod'])
    if compiled:
        require(all(ref['owner'] == PI_MAIN for ref in main_references),
                'Pi main referenced in another compiled caller; caller capture required')
    else:
        require(not any(main_events.values()) and not main_references,
                'Interpreted pi main has queued/task/inline compilation evidence')
    prints = {}
    for node in root.iter('print_nmethod'):
        identity = node.get('compile_id')
        require(identity and identity not in prints, 'Missing/duplicate native print identity')
        prints[identity] = node
    natives = [n for n in root.iter('nmethod') if base.targeted(n.get('method', ''), 'pidigits')]
    required = {('java.math.BigInteger', 'divide'), ('java.math.BigInteger', 'divideKnuth'),
                ('java.math.MutableBigInteger', 'divideKnuth'), ('java.math.MutableBigInteger', 'divideMagnitude')}
    require(required <= {tuple(n.get('method', '').split(' ')[:2]) for n in natives},
            'General BigInteger division native capture missing')
    rows = []; identities = set()
    for node in natives:
        identity = node.get('compile_id'); printed = prints.get(identity)
        text = ''.join(printed.itertext()) if printed is not None else ''
        require(identity not in identities and node.get('compiler') in ('c1', 'c2') and text,
                'Missing/duplicate emitted native version: '+str(identity))
        identities.add(identity)
        require(all(printed.get(key) == node.get(key) for key in ('compiler', 'level', 'compile_kind')),
                'Printed native compiler/level/entry differs')
        methods = re.findall(r"(?m)^[ \t]*# \{method\} \{0x[0-9a-fA-F]+\} '([^']+)' '([^']+)' in '([^']+)'[ \t]*$", text)
        require(len(methods) == 1 and
                methods[0][2].replace('/', '.')+' '+methods[0][0]+' '+methods[0][1] == node.get('method'),
                'Printed native method owner/name/descriptor differs')
        headers = re.findall(r'(?m)^Compiled method \((c[12])\)\s+\d+\s+(\d+)\s', text)
        header_lines = re.findall(r'(?m)^Compiled method .*$', text)
        method_owner, method_name, _ = node.get('method').split(' ', 2)
        header_method = re.search(re.escape(method_owner+'::'+method_name)+r'(?: @ (\d+))? \((\d+) bytes\)$',
                                  header_lines[0]) if len(header_lines) == 1 else None
        task = next(t for t in root.iter('task') if t.get('compile_id') == identity)
        expected_osr = task.get('osr_bci') if node.get('compile_kind') == 'osr' else None
        require(headers == [(node.get('compiler'), identity)] and len(header_lines) == 1 and
                header_method is not None and header_method[1] == expected_osr and header_method[2] == node.get('bytes'),
                'Printed native version header or OSR entry differs')
        if node.get('method') == PI_MAIN:
            require(node.get('bytes') == str(bytecode['bytecode_length']), 'Compiled main bytecode length differs')
        coverage = capture.instruction_coverage(text, node.get('entry', ''))
        maps = [line.strip() for line in text.splitlines() if 'ImmutableOopMap' in line]
        if node.get('method') == PI_MAIN: require(maps, 'Compiled pi main lacks OopMap capture')
        rows.append(dict(node.attrib, instruction_coverage=coverage, oopmap_count=len(maps),
                         native_text_sha256=hashlib.sha256(text.encode()).hexdigest()))
    return dict(status='pi-execution-path-captured-awaiting-instruction-review',
        main_execution_path='compiled-main-versions-captured' if compiled else 'interpreted-main',
        main_compilation_events={tag: len(events) for tag, events in main_events.items()},
        main_method_references=main_references, complete_hotspot_xml=True, compilation_log_closure=closure,
        compiler_or_logging_failures=[],
        retained_bytecode=bytecode, native_methods=rows, node_allocation_eliminations=[],
        source_work_qualified=False, optimized_main_allocation_and_lifetime_proved=False,
        runtime_pi_division_counts_proved=False)


def validate_durable(documents, first=False):
    controller, worker, launcher = (23659, 23655, 23654) if first else (57903, 57899, 57885)
    birth = ['Wed', 'Oct', '14', '04:07:42' if first else '07:03:31', '2026']
    job = previous.DURABLE.parent if first else SECOND_JOB
    command = [str(kb.kh.PYTHON), '-I', '-S', '-B']+([] if first else ['-u'])+[
        str(ROOT/'tools/qualification'/('kotlin_single_entry.py' if first else 'kotlin_single_entry_remaining.py')),
        'run', '--plan', str((previous.ORIGINAL if first else SECOND)/'plan-v1.json'),
        '--plan-sha256', previous.FIRST_PLAN_SHA if first else SECOND_PLAN_SHA]
    for name in ('request.json', 'launch.json', 'worker-started.json', 'command-started.json'):
        record = documents[name]
        require(record['command'] == command and record['cwd'] == str(ROOT), 'Prior durable command/cwd differs')
    terminal = documents['terminal.json']; started = documents['command-started.json']
    require(terminal['status'] == 'command-failed' and terminal['actual_command_started'] is True and
            terminal['exit_code'] == 1 and terminal['qualification_granted'] is False and
            terminal['automatic_retry'] is False and terminal['stop_signals'] == [] and
            terminal['command_identity_observation_missing'] is False and
            started['command_identity_observation_missing'] is False and
            terminal['command_pid'] == started['command_pid'] == controller and
            terminal['command_identity'] == started['command_identity'], 'Prior durable terminal differs')
    identity = terminal['command_identity']; parts = identity['listing'].split(None, 7)
    require(identity['pid'] == controller and len(parts) == 8 and parts[:2] == [str(controller), str(worker)] and
            parts[2:7] == birth and parts[7] == ' '.join(command),
            'Prior durable observed command identity differs')
    worker_command = [str(kb.kh.PYTHON), '-B', '-u', str(ROOT/'experiments/kotlin/dispatch-v1/launch_durable.py'),
                      '--worker', str(job), '--lease-fd', '3', '--go-fd', '4']
    for name in ('launch.json', 'worker-started.json', 'terminal.json'):
        identity = documents[name]['worker_identity']; parts = identity['listing'].split(None, 7)
        require(identity['pid'] == worker and len(parts) == 8 and
                parts[:2] == [str(worker), str(launcher) if name == 'launch.json' else '1'] and
                parts[2:7] == birth and
                parts[7] == ' '.join(worker_command), 'Prior durable worker identity differs')
    require(documents['request.json']['automatic_retry'] is False and
            documents['launch.json']['automatic_retry'] is False and
            documents['launch.json']['detached_session'] is True and
            documents['request.json']['common_mutex_owned_by_target_command'] is True and
            documents['worker-started.json']['inherited_private_lease'] is True and
            documents['worker-started.json']['detached_session'] is True and
            documents['worker-started.json']['common_mutex_owned_by_target_command'] is True and
            all(documents[n]['qualification_granted'] is False for n in
                ('request.json', 'launch.json', 'worker-started.json')), 'Prior durable policy differs')


def closed_inventory(directory, terminal, pins, verify_artifact_closure):
    if verify_artifact_closure:
        base.closed_artifacts(directory, terminal, pins)
        return
    errors = []; files = base.kw.inventory_files(directory, errors)
    require(not errors and {str(p.relative_to(directory)) for p in files
            if p != directory/'terminal.json'} == set(terminal['available_evidence']),
            'Closed artifact inventory changed')
    require(all(pins.get(str((directory/name).resolve())) == item['sha256']
                for name, item in terminal['available_evidence'].items()),
            'Prepared closed artifact pins incomplete')


def durable_inventory(directory, pins, verify_artifact_closure):
    errors = []; files = base.kw.inventory_files(directory, errors)
    require(not errors, 'Prior durable inventory error')
    expected = {'request.json', 'launch.json', 'worker-started.json', 'command-started.json',
                'terminal.json', 'command.stdout', 'command.stderr', 'worker.log', 'owner.lock'}
    require({str(p.relative_to(directory)) for p in files} == expected, 'Prior durable file inventory differs')
    for path in files:
        digest = sha(path)
        if verify_artifact_closure: bind(path, digest, pins)
        else: require(pins.get(str(path.resolve())) == digest, 'Prepared durable artifact pin missing/changed')


def validate_start_records(directory, receipt):
    for name in ('start.json', 'active.json'):
        record = json.loads((directory/name).read_bytes())
        require(all(record[k] == receipt[k] for k in ('kind', 'command', 'environment', 'cwd', 'started_at')),
                'Saved native start/final linkage differs')
        if name == 'active.json': require(record['identity'] == receipt['identity'], 'Saved active birth differs')


def expected_environment(saved, directory):
    # The retained helper also creates fresh home/tmp/config directories. Replay
    # its exact environment transformation without changing closed evidence.
    result = dict(saved)
    require(not any(key in result for key in ('JDK_JAVA_OPTIONS', 'JAVA_TOOL_OPTIONS', '_JAVA_OPTIONS')),
            'Injected JVM environment options')
    result.update(HOME=str(directory/'home'), XDG_CONFIG_HOME=str(directory/'config'),
                  TMPDIR=str(directory/'tmp')+os.sep)
    result['JAVA_OPTS'] = ' '.join(kb.kh.FLAGS+[f'-Duser.home={directory}/home', f'-Djava.io.tmpdir={directory}/tmp'])
    require(all(result[key] == '' for key in ('CLASSPATH', 'KOTLIN_RUNNER', 'KOTLIN_COMPILER', 'KOTLIN_TOOL')),
            'Injected Kotlin/classpath environment')
    return result


def validate_capture(directory, row, plan, command, environment, parent_pid):
    require(environment == expected_environment(row['runtime_environment'], directory),
            'Retained runtime environment differs')
    receipt = json.loads((directory/'process.json').read_bytes())
    previous.validate_saved_receipt(receipt, directory, command, environment, parent_pid)
    validate_start_records(directory, receipt)
    expected = base.expected_output(row['benchmark'])
    require((directory/'stdout.bin').read_bytes() == (directory/'expected.stdout').read_bytes() == expected,
            'Prescribed complete stdout differs')
    os_log = previous.validate_os_log((directory/'os.log').read_bytes())
    previous.validate_vm_identity(directory/'hotspot.xml', row, plan, directory, receipt)
    loaded = base.validate_classes((directory/'classes.log').read_text(), row, plan['stdlib'])
    require('Using G1' in (directory/'gc.log').read_text(), 'Actual G1 evidence missing')
    if row['benchmark'] == 'pidigits':
        require(all(loaded.get(owner, '').startswith(('jrt:/', 'shared objects file')) for owner in
                    ('java.math.BigInteger', 'java.math.MutableBigInteger')), 'Platform division origins missing')
        index = pi_index(directory/'hotspot.xml', row)
    else:
        index = capture.capture_index(directory/'hotspot.xml', 'binarytrees')
        require(not any(n['installed_nmethod'] for n in index['node_allocation_eliminations']),
                'Installed Node allocation elimination needs review')
    return dict(id=row['id'], n=base.INPUTS[row['benchmark']], status=index['status'], complete_output_match=True,
        actual_loaded_classes=loaded, os_diagnostics=os_log, capture=index, source_work_qualified=False,
        main_entry='direct JVM launcher; one main call inferred from pinned launch/source, not a probe counter')


def reconcile_prior(pins, verify_artifact_closure):
    original, first = previous.reconcile_first(pins, verify_artifact_closure)
    first_terminal = read(previous.ORIGINAL/'run-v1/terminal.json', previous.FIRST_TERMINAL_SHA, pins)
    if not verify_artifact_closure:
        closed_inventory(previous.ORIGINAL/'run-v1', first_terminal, pins, False)
    first_documents = {name: json.loads((previous.DURABLE.parent/name).read_bytes()) for name in
                       ('request.json', 'launch.json', 'worker-started.json', 'command-started.json', 'terminal.json')}
    validate_durable(first_documents, first=True)
    durable_inventory(previous.DURABLE.parent, pins, verify_artifact_closure)
    plan = read(SECOND/'plan-v1.json', SECOND_PLAN_SHA, pins)
    report = read(SECOND/'run-v1/report.json', SECOND_REPORT_SHA, pins)
    terminal = read(SECOND/'run-v1/terminal.json', SECOND_TERMINAL_SHA, pins)
    durable = read(SECOND_JOB/'terminal.json', SECOND_DURABLE_SHA, pins)
    documents = {name: json.loads((SECOND_JOB/name).read_bytes()) for name in
                 ('request.json', 'launch.json', 'worker-started.json', 'command-started.json')}
    documents['terminal.json'] = durable; validate_durable(documents)
    require(plan['controller_sha256'] == REMAINING_SHA and plan['capture_sha256'] == previous.CAPTURE_SHA and
            plan['ids'] == SECOND_IDS+[FINAL_ID] and plan['profiles'] == original['profiles'][1:] and
            all(plan[k] == original[k] for k in ('java', 'stdlib', 'runtime_expected')) and
            plan['first_capture_reconciliation'] == report['first_capture_reconciliation'] == first and
            json.loads((SECOND/'run-v1/first-capture-reconciliation.json').read_bytes()) == first,
            'Prior plan or first-capture reconciliation differs')
    registered = [dict(id=identity, pid=pid, pgid=pid) for identity, pid in zip(SECOND_IDS, (57905, 57906))]
    require(report['schema'] == 'kotlin-single-entry-remaining-results-v1' and
            report['plan_sha256'] == SECOND_PLAN_SHA and report['status'] == terminal['status'] == 'failed' and
            report['error'] == 'Required single-entry JIT methods missing' and report['error_type'] == 'AssertionError' and
            report['active'] is None and report['native_processes_started'] == terminal['native_processes_started'] == 2 and
            report['registered_native_commands'] == terminal['registered_native_commands'] == registered and
            terminal['report_sha256'] == SECOND_REPORT_SHA and terminal['common_mutex_held'] is True and
            terminal['common_mutex_inode'] == kb.LOCK_INODE and report['prior_native_commands_reused'] == 1 and
            set(report['commands']) == set(SECOND_IDS) and
            [p['id'] for p in report['profiles']] == [SECOND_IDS[0]] and
            set(report['validated_command_artifacts']) == {SECOND_IDS[0]}, 'Exact second failed attempt differs')
    require(all(report[k] == terminal[k] == [] for k in ('process_receipt_errors', 'integrity_errors')) and
            terminal['artifact_errors'] == [] and report['remaining_receipt_errors'] == [] and
            all(report[k] == terminal[k] == 0 for k in ('subject_recompilations', 'diagnostic_compilations', 'benchmark_samples')) and
            all(report[k] is False and terminal[k] is False for k in
                ('source_work_qualified', 'full_timings_qualified', 'chart_admission')), 'Second closure/scope differs')
    if verify_artifact_closure:
        for path, digest in report['pins'].items(): bind(path, digest, pins)
    else:
        require(all(pins.get(path) == digest for path, digest in report['pins'].items()),
                'Prepared inherited pin inventory incomplete')
    closed_inventory(SECOND/'run-v1', terminal, pins, verify_artifact_closure)
    durable_inventory(SECOND_JOB, pins, verify_artifact_closure)
    require({str(p.parent.relative_to(SECOND/'run-v1')) for p in (SECOND/'run-v1').rglob('process.json')} == set(SECOND_IDS) and
            not (SECOND/'run-v1'/FINAL_ID).exists(), 'Unstarted optimized pi inventory differs')
    reused = []
    for row in plan['profiles'][:2]:
        directory = (SECOND/'run-v1'/row['id']).resolve()
        command = [plan['java']]+previous.options(row['benchmark'], directory)+[
            '-cp', row['classes']+os.pathsep+plan['stdlib'], row['main_owner'], str(base.INPUTS[row['benchmark']])]
        saved = report['commands'][row['id']]
        require(saved['argv'] == command, 'Prior exact native command differs')
        result = validate_capture(directory, row, plan, command, saved['environment'], 57903)
        if row['id'] == SECOND_IDS[0]:
            require(result == report['profiles'][0] == json.loads((directory/'validated.json').read_bytes()) and
                    result['capture'] == json.loads((directory/'capture-index.json').read_bytes()) and
                    base.snapshot(directory) == report['validated_command_artifacts'][row['id']],
                    'Prior validated tree snapshot differs')
        else:
            require(not (directory/'validated.json').exists() and not (directory/'capture-index.json').exists() and
                    result['capture']['main_execution_path'] == 'interpreted-main', 'Prior pi failure boundary differs')
        reused.append(result)
    proof = dict(schema='kotlin-three-single-entry-additive-reconciliation-v1', reused_ids=REUSED_IDS,
        first_capture=first, second_original_status='failed', second_original_error=report['error'],
        second_plan_sha256=SECOND_PLAN_SHA, second_report_sha256=SECOND_REPORT_SHA,
        second_terminal_sha256=SECOND_TERMINAL_SHA, second_durable_terminal_sha256=SECOND_DURABLE_SHA,
        second_captures=reused, native_commands_reexecuted=0, source_work_qualified=False,
        benchmark_samples=0, full_timings_qualified=False, chart_admission=False)
    return plan, proof


def prepare(args):
    require(not args.plan.exists() and not args.output.exists() and
            not args.plan.resolve().is_relative_to(args.output.resolve()), 'Fresh separate plan/output required')
    pins = {}; prior, proof = reconcile_prior(pins, True)
    for path in (Path(__file__).resolve(), Path(__file__).with_name('test_kotlin_single_entry_final.py'),
                 PACKET/'README.md', kb.kh.PYTHON):
        bind(path, sha(path), pins)
    for name, digest in REVIEW_FILES.items(): bind(SECOND/name, digest, pins)
    require(pins[str(kb.kh.PYTHON)] == kb.kh.PYTHON_SHA, 'Retained interpreter differs')
    row = prior['profiles'][-1]; bytecode = pi_bytecode(row)
    plan = dict(schema='kotlin-single-entry-final-plan-v1', controller_sha256=sha(__file__),
        remaining_controller_sha256=REMAINING_SHA, capture_sha256=previous.CAPTURE_SHA,
        status='prepared-awaiting-one-final-capture', ids=[FINAL_ID], reused_ids=REUSED_IDS, profiles=[row],
        prior_capture_reconciliation=proof, retained_pi_bytecode=bytecode, pins=pins,
        java=prior['java'], stdlib=prior['stdlib'], runtime_expected=prior['runtime_expected'],
        prescribed_inputs=base.INPUTS, output=str(args.output.resolve()), planned_native_commands=1,
        prior_native_commands_reused=3, automatic_retries=0, process_timeout_seconds=kb.TIMEOUT,
        cleanup_timeout_seconds=kb.CLEANUP_TIMEOUT, maximum_process_group_rss_bytes=kb.RSS_LIMIT,
        native_file_limit_bytes=kb.FILE_LIMIT, subject_recompilations=0, diagnostic_compilations=0,
        benchmark_samples=0, source_work_qualified=False, full_timings_qualified=False, chart_admission=False)
    # Recheck every inherited/new binding after reconciliation and the evidence snapshots.
    for path, digest in pins.items(): require(sha(path) == digest, 'Preparation input changed: '+path)
    args.plan.parent.mkdir(parents=True, exist_ok=True); require(not args.plan.exists(), 'Plan appeared during prepare')
    save(args.plan, plan)
    print(json.dumps(dict(plan=str(args.plan), sha256=sha(args.plan), native_executions=0, reused_native_commands=3)), flush=True)


def finish(report, plan, pins, output, lock):
    errors = []
    require(not (output/'terminal.json').exists(), 'Unexpected terminal before finalization')
    if report['status'] == COMPLETE:
        try:
            require([p['id'] for p in report['profiles']] == [FINAL_ID] and report['native_processes_started'] == 1 and
                    set(report['commands']) == set(report['validated_command_artifacts']) == {FINAL_ID} and
                    [r['id'] for r in report['registered_native_commands']] == [FINAL_ID] and report['active'] is None,
                    'Successful final-one inventory differs')
            require(json.loads((output/'prior-capture-reconciliation.json').read_bytes()) ==
                    report['prior_capture_reconciliation'] == plan['prior_capture_reconciliation'],
                    'Saved prior-capture reconciliation differs')
            directory = output/FINAL_ID
            require(json.loads((directory/'validated.json').read_bytes()) == report['profiles'][0],
                    'Saved final profile differs')
            previous.validate_saved_receipt(json.loads((directory/'process.json').read_bytes()), directory,
                report['commands'][FINAL_ID]['argv'], report['commands'][FINAL_ID]['environment'], os.getpid())
        except BaseException as error: errors.append(str(error) or type(error).__name__)
    try:
        receipt_ids = {str(p.parent.relative_to(output)) for p in output.rglob('process.json')}
        require(receipt_ids <= {FINAL_ID} and (report['status'] != COMPLETE or receipt_ids == {FINAL_ID}),
                'Unexpected final native receipt')
    except BaseException as error: errors.append(str(error) or type(error).__name__)
    report['final_receipt_errors'] = errors
    if errors: report['status'] = 'failed-final-native-reconciliation'
    base.finish(report, plan, pins, output, lock)
    # The inherited finalizer checks snapshots, registered/reaped PIDs and pins;
    # repeat pins after its complete artifact inventory, still under the mutex.
    changed = []
    for path, digest in pins.items():
        try: require(sha(path) == digest, 'Pinned input changed after final artifact snapshot')
        except BaseException as error: changed.append(dict(path=path, error=str(error)))
    kb.kh.verify_lock(lock)
    if changed:
        report['integrity_errors'].extend(changed); report['status'] = 'failed-integrity-or-closure'
        save(output/'report.json', report)
        terminal = json.loads((output/'terminal.json').read_bytes())
        terminal.update(status=report['status'], report_sha256=sha(output/'report.json'),
                        integrity_errors=report['integrity_errors'])
        terminal['available_evidence']['report.json'] = dict(bytes=(output/'report.json').stat().st_size,
                                                             sha256=sha(output/'report.json'))
        save(output/'terminal.json', terminal)
    require(not errors and not changed, 'Final native reconciliation or post-snapshot pin check failed')


def run(args, lock):
    pins = {}; plan = read(args.plan, args.plan_sha256, pins)
    require(plan['schema'] == 'kotlin-single-entry-final-plan-v1' and plan['controller_sha256'] == sha(__file__) and
            plan['remaining_controller_sha256'] == REMAINING_SHA and plan['capture_sha256'] == previous.CAPTURE_SHA and
            plan['ids'] == [FINAL_ID] and plan['reused_ids'] == REUSED_IDS and
            [r['id'] for r in plan['profiles']] == [FINAL_ID] and plan['planned_native_commands'] == 1 and
            plan['prior_native_commands_reused'] == 3 and plan['prescribed_inputs'] == base.INPUTS and
            plan['maximum_process_group_rss_bytes'] == kb.RSS_LIMIT and plan['process_timeout_seconds'] == kb.TIMEOUT and
            plan['cleanup_timeout_seconds'] == kb.CLEANUP_TIMEOUT and plan['native_file_limit_bytes'] == kb.FILE_LIMIT and
            plan['automatic_retries'] == 0 and all(plan[k] is False for k in
                ('source_work_qualified', 'full_timings_qualified', 'chart_admission')) and
            plan['subject_recompilations'] == plan['diagnostic_compilations'] == plan['benchmark_samples'] == 0,
            'Wrong final-one plan')
    for path, digest in plan['pins'].items(): bind(path, digest, pins)
    require(pins.get(str(Path(__file__).resolve())) == plan['controller_sha256'] and
            pins.get(str(kb.kh.PYTHON)) == kb.kh.PYTHON_SHA and
            all(str(path.resolve()) in pins for path in
                (Path(__file__).with_name('test_kotlin_single_entry_final.py'), PACKET/'README.md')) and
            all(pins.get(str(SECOND/name)) == digest for name, digest in REVIEW_FILES.items()),
            'Final controller/interpreter/review pins missing')
    prior, proof = reconcile_prior(pins, False)
    require(proof == plan['prior_capture_reconciliation'] and plan['profiles'] == prior['profiles'][-1:] and
            all(plan[k] == prior[k] for k in ('java', 'stdlib', 'runtime_expected')) and
            pi_bytecode(plan['profiles'][0]) == plan['retained_pi_bytecode'], 'Prior captures or final inputs differ')
    output = Path(plan['output'])
    require(output.is_absolute() and str(output.resolve()) == plan['output'] and
            not args.plan.resolve().is_relative_to(output), 'Absolute physical separate output path required')
    require(not output.exists(), 'Fresh output required; no retry'); output.mkdir(parents=True)
    report = dict(schema='kotlin-single-entry-final-results-v1', status='running', plan=str(args.plan.resolve()),
        plan_sha256=args.plan_sha256, pins=pins, started_at=datetime.now(timezone.utc).isoformat(),
        prior_capture_reconciliation=proof, prior_native_commands_reused=3, profiles=[], active=None,
        native_processes_started=0, registered_native_commands=[], commands={}, validated_command_artifacts={},
        subject_recompilations=0, diagnostic_compilations=0, benchmark_samples=0, source_work_qualified=False,
        optimized_main_allocation_and_lifetime_proved=False, runtime_pi_division_counts_proved=False,
        full_timings_qualified=False, chart_admission=False)
    save(output/'prior-capture-reconciliation.json', proof); save(output/'report.json', report)
    try:
        kb.kh.verify_lock(lock); row = plan['profiles'][0]; classes = Path(row['classes'])
        require(row['id'] == FINAL_ID and {str(p.relative_to(classes)) for p in classes.rglob('*') if p.is_file()} ==
                {a['relative_path'] for a in row['class_artifacts']} and
                not any(p.is_symlink() for p in classes.rglob('*')), 'Final retained class inventory changed')
        for item in row['physical_inputs']+row['class_artifacts']:
            require(sha(item['path']) == item['sha256'], 'Active source/class changed')
        directory = output/FINAL_ID; directory.mkdir()
        environment = kb.kh.environment(row['runtime_environment'], directory)
        (directory/'expected.stdout').write_bytes(base.expected_output('pidigits'))
        command = [plan['java']]+previous.options('pidigits', directory)+[
            '-cp', row['classes']+os.pathsep+plan['stdlib'], row['main_owner'], '10000']
        report['commands'][FINAL_ID] = dict(argv=command, environment=environment)
        report['active'] = dict(id=FINAL_ID, receipt=str(directory/'process.json'), pid=None)
        save(output/'report.json', report)
        def launched(pid):
            report['native_processes_started'] += 1
            report['registered_native_commands'].append(dict(id=FINAL_ID, pid=pid, pgid=pid))
            report['active']['pid'] = pid; save(output/'report.json', report)
        kb.observe(command, environment, directory, b'', lock, launched, kind='single-entry-work')
        result = validate_capture(directory, row, plan, command, environment, os.getpid())
        save(directory/'capture-index.json', result['capture']); save(directory/'validated.json', result)
        report['validated_command_artifacts'][FINAL_ID] = base.snapshot(directory)
        report['profiles'].append(result); report['active'] = None; report['status'] = COMPLETE
    except BaseException as error:
        report.update(status='failed', error=str(error) or type(error).__name__, error_type=type(error).__name__); raise
    finally:
        with kb.atomic(): finish(report, plan, pins, output, lock)


def main():
    parser = argparse.ArgumentParser(description=__doc__); commands = parser.add_subparsers(dest='action', required=True)
    prep = commands.add_parser('prepare'); prep.add_argument('--plan', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    execute = commands.add_parser('run'); execute.add_argument('--plan', type=Path, required=True)
    execute.add_argument('--plan-sha256', required=True)
    args = parser.parse_args()
    require(Path(sys.executable).resolve() == kb.kh.PYTHON.resolve() and sys.flags.isolated and sys.flags.no_site and
            sys.flags.dont_write_bytecode and not sys.flags.optimize, 'Use retained Python with -I -S -B')
    def interrupted(signum, frame): raise KeyboardInterrupt('Final capture interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS: signal.signal(sig, interrupted)
    with kb.LOCK.open('rb') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB); kb.kh.verify_lock(lock)
        require(sha(kb.kh.PYTHON) == kb.kh.PYTHON_SHA, 'Retained interpreter changed')
        if args.action == 'prepare': prepare(args)
        else: run(args, lock)


if __name__ == '__main__': main()
