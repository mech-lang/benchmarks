#!/usr/bin/env python3
"""Record bounded required-work witnesses and actual Kotlin JIT/dependency evidence.

Requires explicit completed 156-case and 30-case supplement report hashes. No subject
compiler runs. A new Java diagnostic is compiled once with the original javac;
all20 exact retained forms are then observed under the common timing mutex.
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
import stat
import sys
from urllib.parse import unquote, urlparse
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/kotlin/compiled-work-v1'
BOUNDED_CONTROLLER_SHA = 'c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc'
SUPPLEMENT_CONTROLLER_SHA = '107d32625ca4cace589c9e94b6110fa79cdb256ebfc8330adf98fcbce7368685'


def require(value,message):
    if not value: raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def load_bounded():
    path = ROOT/'tools/qualification/kotlin_bounded_v2.py'; raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == BOUNDED_CONTROLLER_SHA, 'Qualified supervision source changed')
    spec = importlib.util.spec_from_file_location('retained_kotlin_bounded',path)
    module = importlib.util.module_from_spec(spec); exec(compile(raw,str(path),'exec'),module.__dict__)
    return module


kb = load_bounded()
save, atomic, LOCK, FLAGS = kb.save,kb.atomic,kb.LOCK,kb.FLAGS


def bind(path,digest,pins):
    path = Path(path).resolve()
    require(sha(path) == digest and (str(path) not in pins or pins[str(path)] == digest), 'Changed/conflicting input: '+str(path))
    pins[str(path)] = digest; return path


def read(path,digest,pins):
    path = bind(path,digest,pins); raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'JSON changed during read')
    return json.loads(raw)


def validate_prerequisite(report,terminal,report_sha):
    require(report['schema'] == 'kotlin-retained-classes-bounded-results-v1' and
            report['status'] == terminal['status'] == 'all20-bounded-output-passed-awaiting-work-JIT-and-LOC' and
            report['bounded_outputs_qualified'] is True and terminal['report_sha256'] == report_sha and
            report['qualified_bounded_cases'] == terminal['qualified_bounded_cases'] == 156 and
            report['native_processes_started'] == terminal['native_processes_started'] == 157 and
            report['diagnostic_compiler_processes_started'] == terminal['diagnostic_compiler_processes_started'] == 1 and
            report['bounded_jvm_processes_started'] == terminal['bounded_jvm_processes_started'] == 156 and
            report['observed_subject_main_invocations'] == terminal['observed_subject_main_invocations'] == 156 and
            report['observed_subject_main_returns'] == terminal['observed_subject_main_returns'] == 156 and
            len(report['profiles']) == len(set(report['profiles'])) == 20 and len(report['cases']) == 156 and
            report['active'] is None and report['subject_recompilations'] == report['benchmark_samples'] == 0 and
            report['chart_admission'] is False and terminal['common_mutex_held'] is True and
            terminal['common_mutex_inode'] == kb.LOCK_INODE and
            report['integrity_errors'] == report['process_receipt_errors'] == terminal['integrity_errors'] ==
            terminal['artifact_errors'] == terminal['process_receipt_errors'] == [], 'Completed bounded prerequisite missing')


def terminal_reference(path,digest,directory,terminal):
    path,directory = Path(path).resolve(),Path(directory).resolve()
    require(path.is_relative_to(directory),'Supplement reference escapes terminal directory')
    name = str(path.relative_to(directory)); item = terminal['available_evidence'].get(name)
    require(item is not None and item['sha256'] == digest and item['bytes'] == path.stat().st_size,
            'Supplement reference and terminal inventory differ')


def supplemental_prerequisite(args,bounded,pins,original_report,original_terminal):
    source = ROOT/'tools/qualification/kotlin_supplement.py'
    bind(source,SUPPLEMENT_CONTROLLER_SHA,pins)
    spec = importlib.util.spec_from_file_location('required_kotlin_specified_cases',source)
    supplement = importlib.util.module_from_spec(spec)
    raw = source.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == SUPPLEMENT_CONTROLLER_SHA,'Supplement controller changed during read')
    exec(compile(raw,str(source),'exec'),supplement.__dict__)
    report = read(args.supplement_report,args.supplement_report_sha256,pins)
    terminal = read(args.supplement_report.with_name('terminal.json'),args.supplement_terminal_sha256,pins)
    supplement.validate_completed(report,terminal,args.supplement_report_sha256,args.bounded_report_sha256)
    original_proof = supplement.original_case_bindings(original_report,original_terminal,bounded,args.bounded_report.parent,pins)
    plan = read(report['plan'],report['plan_sha256'],pins)
    require(plan['schema'] == 'kotlin-specified-cases-plan-v1' and
            plan['controller_sha256'] == SUPPLEMENT_CONTROLLER_SHA and
            plan['bounded_report_sha256'] == args.bounded_report_sha256 and
            plan['bounded_terminal_sha256'] == args.bounded_terminal_sha256 and
            plan['original_specification_sha256'] == supplement.SPEC_SHA and
            plan['original_output_artifact_binding'] == report['original_output_artifact_binding'] ==
            terminal['original_output_artifact_binding'] == original_proof and
            [r['id'] for r in plan['profiles']] == report['profiles'] == [r['id'] for r in bounded['profiles']],
            'Wrong completed supplemental plan/cohort')
    for original,additional in zip(bounded['profiles'],plan['profiles']):
        require({k:v for k,v in original.items() if k != 'bounded_cases'} ==
                {k:v for k,v in additional.items() if k != 'bounded_cases'}, 'Supplement changed retained class/source/runtime bindings')
    schedule = supplement.validate_coverage(plan['profiles'],plan['fixtures'])
    require({(c['id'],c['case']) for c in report['cases']} == set(schedule) and
            plan['alias_pairs'] == report['alias_pairs'] == bounded['alias_pairs'], 'Supplement case/alias inventory differs')
    for path,digest in report['pins'].items(): bind(path,digest,pins)
    supplement.bind_artifacts(args.supplement_report.parent,terminal,pins)
    terminal_reference(args.supplement_report,args.supplement_report_sha256,args.supplement_report.parent,terminal)
    snapshots = report['validated_command_artifacts']
    require(set(snapshots) == {'diagnostic-compile'} | {identity+'/'+case for identity,case in schedule},
            'Supplement validated artifact snapshot inventory differs')
    for directory,snapshot in snapshots.items():
        for name,item in snapshot.items():
            require(terminal['available_evidence'].get(directory+'/'+name) == item,
                    'Supplement validated artifacts and terminal inventory differ')
    completed = {(c['id'],c['case']):c for c in report['cases']}
    for row in plan['profiles']:
        for case in row['bounded_cases']:
            record = completed[(row['id'],case['case'])]
            for field in ('validated','process'):
                terminal_reference(record[field],record[field+'_sha256'],args.supplement_report.parent,terminal)
                require(Path(record[field]).resolve() == args.supplement_report.parent.resolve()/row['id']/case['case']/(field+'.json'),
                        'Supplement case references another command artifact')
            value = read(record['validated'],record['validated_sha256'],pins)
            require(value['status'] == record['status'] == 'specified-case-output-passed' and
                    value['id'] == row['id'] and value['case'] == case['case'] and value['reference_evidence'] == case and
                    value['main_invocations'] == value['main_returns'] == 1 and value['validation']['reference_match'] is True,
                    'Specified supplemental output is not qualified')
            supplement.validate_receipt(read(record['process'],record['process_sha256'],pins),'bounded-main',Path(record['process']).parent)
    return dict(report=str(args.supplement_report.resolve()),report_sha256=args.supplement_report_sha256,
                terminal_sha256=args.supplement_terminal_sha256,qualified_cases=30,
                combined_qualified_form_cases=186,specified_case_coverage_qualified=True)


def prepare(args):
    require(not args.plan.exists() and not args.output.exists() and
            not args.plan.resolve().is_relative_to(args.output.resolve()), 'Fresh plan outside fresh output required')
    pins = {}
    report = read(args.bounded_report,args.bounded_report_sha256,pins)
    terminal = read(args.bounded_report.with_name('terminal.json'),args.bounded_terminal_sha256,pins)
    validate_prerequisite(report,terminal,args.bounded_report_sha256)
    bounded = read(report['plan'],report['plan_sha256'],pins)
    require(bounded['schema'] == 'kotlin-retained-classes-bounded-plan-v1' and
            bounded['controller_sha256'] == BOUNDED_CONTROLLER_SHA and
            [row['id'] for row in bounded['profiles']] == report['profiles'], 'Wrong completed bounded plan')
    kb.bounded_schedule(bounded['profiles'])
    for path,digest in report['pins'].items(): bind(path,digest,pins)
    for name,item in terminal['available_evidence'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'Unsafe bounded artifact path')
        path = bind(args.bounded_report.parent/name,item['sha256'],pins)
        require(path.stat().st_size == item['bytes'], 'Bounded artifact size differs')
    require(kb.aliases(bounded['profiles']) == bounded['alias_pairs'] == report['alias_pairs'], 'Alias pairs differ')
    supplemental = supplemental_prerequisite(args,bounded,pins,report,terminal)
    spec_path = PACKET/'work-spec.json'; specification = read(spec_path,sha(spec_path),pins)
    require(specification['schema'] == 'kotlin-retained-compiled-work-spec-v1' and
            set(specification['profiles']) == set(kb.CASE_NAMES) and
            specification['maximum_main_invocations_per_profile'] == 10000 and
            specification['main_invocation_time_bound_milliseconds'] == 20000 and
            specification['per_native_command_timeout_seconds'] == kb.TIMEOUT == 30 and
            specification['automatic_retries'] == 0 and
            specification['required_output_prerequisites'] == {'original_cases':156,'specified_supplemental_cases':30,
                'combined_form_cases':186,'explicit_completed_report_and_terminal_hashes':True}, 'Unreviewed work/JIT bounds')
    review_path = ROOT/'experiments/kotlin/source-owner-review-v1/review.json'
    review = read(review_path,pins[str(review_path)],pins)
    review_text = ROOT/'experiments/kotlin/source-owner-review-v1/README.md'
    bind(review_text,sha(review_text),pins)
    require(review['schema'] == 'kotlin-source-owner-review-v1' and
            [r['id'] for r in review['profiles']] == report['profiles'], 'Source/bytecode review differs')
    completed = {(c['id'],c['case']):c for c in report['cases']}
    require(len(completed) == 156, 'Duplicate bounded case evidence')
    rows = []
    for row,reviewed in zip(bounded['profiles'],review['profiles']):
        scoped = specification['profiles'][row['benchmark']]
        case = next(c for c in row['bounded_cases'] if c['case'] == scoped['case'])
        closed_case = completed[(row['id'],case['case'])]
        validated = read(closed_case['validated'],closed_case['validated_sha256'],pins)
        require(validated['status'] == 'bounded-output-passed' and validated['id'] == row['id'] and
                validated['case'] == case['case'] and validated['reference_evidence'] == case and
                validated['main_invocations'] == validated['main_returns'] == 1 and
                validated['validation']['reference_match'] is True, 'Selected main case is not qualified')
        disassembly = bind(ROOT/reviewed['disassembly_path'],reviewed['recorded_disassembly_sha256'],pins)
        body = disassembly.read_text()
        methods = []
        for name,descriptor in scoped['methods'].items():
            require(re.search(r'\b'+re.escape(name)+r'\([^\n]*\);\s*descriptor: '+re.escape(descriptor)+r'(?=\s)',body),
                    'Required method descriptor absent in retained javap: '+row['id']+' '+name)
            methods.append(dict(owner=row['main_owner'],name=name,descriptor=descriptor))
        rows.append(dict(row,diagnostic_case=case,required_jit_methods=methods,
            source_owner_review=dict(path=str(review_path),sha256=pins[str(review_path)]),
            retained_disassembly=dict(path=str(disassembly),sha256=reviewed['recorded_disassembly_sha256'])))
    for path in (Path(__file__).resolve(),ROOT/'tools/qualification/kotlin_bounded_v2.py',
            PACKET/'WorkProbe.java',ROOT/'experiments/kotlin/bounded-work-v1/BoundedProbe.java',kb.kh.PYTHON):
        bind(path,sha(path),pins)
    require(pins[str(kb.kh.PYTHON)] == kb.kh.PYTHON_SHA, 'Wrong controller interpreter')
    java_home = Path(bounded['java']).parent.parent
    for path in (java_home/'lib/modules',java_home/'lib/server/classes.jsa'):
        require(str(path) in pins, 'Unpinned JVM class/CDS image')
    plan = dict(schema='kotlin-retained-compiled-work-plan-v1',status='prepared-awaiting-native-witness-execution',
        controller_sha256=sha(__file__),bounded_report=str(args.bounded_report.resolve()),
        bounded_report_sha256=args.bounded_report_sha256,bounded_terminal_sha256=args.bounded_terminal_sha256,
        supplemental_output_prerequisite=supplemental,specified_case_coverage_qualified=True,
        pins=pins,profiles=rows,alias_pairs=bounded['alias_pairs'],java=bounded['java'],javac=bounded['javac'],
        stdlib=bounded['stdlib'],runtime_expected=bounded['runtime_expected'],output=str(args.output.resolve()),
        probe_source=str(PACKET/'WorkProbe.java'),loader_source=str(ROOT/'experiments/kotlin/bounded-work-v1/BoundedProbe.java'),
        process_timeout_seconds=30,cleanup_timeout_seconds=5,maximum_main_invocations_per_profile=10000,
        main_invocation_time_bound_milliseconds=20000,planned_native_commands=21,
        subject_recompilations=0,benchmark_samples=0,source_work_qualified=False,
        optimized_main_allocation_and_lifetime_proved=False,canonical_loc=None,formatted_loc=None,
        full_timings_qualified=False,chart_admission=False)
    args.plan.parent.mkdir(parents=True,exist_ok=True); require(not args.plan.exists(),'Plan appeared during prepare')
    save(args.plan,plan); print(json.dumps(dict(plan=str(args.plan),sha256=sha(args.plan),native_executions=0)),flush=True)


def jit_records(path,targets):
    root = ET.parse(path).getroot(); require(root.tag == 'hotspot_log','Not a complete HotSpot compilation log')
    rows = []
    for node in root.iter('nmethod'):
        method = node.get('method','').split(' ',2)
        if len(method) != 3: continue
        owner,name,descriptor = method
        if not owner.startswith('clbg.'): continue
        require(node.get('compiler') in ('c1','c2','jvmci') and node.get('compile_id','').isdigit() and
                re.fullmatch(r'0x[0-9a-fA-F]+',node.get('address','')), 'Malformed subject native compilation record')
        rows.append(dict(owner=owner,name=name,descriptor=descriptor,compiler=node.get('compiler'),
            compile_id=node.get('compile_id'),level=node.get('level'),compile_kind=node.get('compile_kind'),
            address=node.get('address'),entry=node.get('entry'),stamp=node.get('stamp')))
    present = {(r['owner'],r['name'],r['descriptor']) for r in rows}
    missing = [t for t in targets if (t['owner'],t['name'],t['descriptor']) not in present]
    return dict(subject_native_methods=rows,required_methods=targets,missing_methods=missing,
                subject_JIT_method_evidence_qualified=not missing)


def validate_log(text,classes,stdlib,probe_classes,owners):
    # Reuse the bounded strict platform/subject-origin rules. The only new
    # probe owner is independently checked before adapting its name for that
    # immutable parser. Preserve all original names in the returned inventory.
    original = {}
    for line in text.splitlines():
        if '[class,load]' not in line: continue
        match = re.search(r'\[class,load\]\s+(\S+) source: (.+)$',line)
        require(match,'Malformed class log'); owner,source = match.groups(); original[owner] = source
        if owner == 'boundedqualification.WorkProbe':
            require(kb.uri_path(source) == probe_classes,'Wrong work probe class origin')
    require('boundedqualification.WorkProbe' in original,'Work probe missing from class log')
    adapted = text.replace('] boundedqualification.WorkProbe source:','] boundedqualification.BoundedProbe source:')
    kb.validate_log(adapted,classes,stdlib,probe_classes,owners)
    return original


def native_libraries(text,pins,java_home):
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    require(lines and lines[0] == 'Dynamic libraries:','Missing VM.dynlibs header')
    result = []; unresolved = []
    for line in lines[1:]:
        match = re.fullmatch(r'(0x[0-9a-fA-F]+)\s+(/.+)',line)
        require(match, 'Unrecognized actual dynamic-library observation: '+line)
        address,name = match.groups(); path = Path(name)
        if str(path).startswith(('/usr/lib/','/System/Library/','/System/Volumes/Preboot/Cryptexes/OS/')):
            result.append(dict(path=name,address=address,scope='operating-system-image-install-name-not-file-pinned'))
        else:
            resolved = path.resolve(); digest = pins.get(str(path)) or pins.get(str(resolved))
            if digest is None or not resolved.is_relative_to(java_home):
                unresolved.append(name)
                result.append(dict(path=name,address=address,scope='unresolved-non-platform-origin'))
            else:
                require(sha(resolved) == digest,'Observed native library bytes changed')
                result.append(dict(path=name,resolved_path=str(resolved),address=address,sha256=digest,scope='pinned-original-jdk-image'))
    require(any(Path(r['path']).name == 'libjvm.dylib' for r in result),'Actual JVM native image missing')
    require(any(Path(r['path']).name == 'libjava.dylib' for r in result),'Actual Java native image missing')
    return dict(images=result,unresolved_non_platform_images=unresolved,
                native_non_platform_images_qualified=not unresolved,
                os_image_scope='Existing operating-system vendor primitive boundary; install names observed, files not newly hashed')


def validate_witness(summary,row,plan,case_dir,probe_classes,options):
    require(summary['status'] == 'work-witnesses-recorded' and summary['benchmark'] == row['benchmark'] and
            summary['main_owner'] == row['main_owner'] and summary['subject_owner_names'] == row['class_owner_names'] and
            summary['denied_owner_canary'] is True and summary['denied_owners'] == ['clbg.UnexpectedOwner'],
            'Wrong retained work witness/owner inventory')
    count = summary['main_invocations']
    require(type(count) is int and 0 < count <= 10000 and count == summary['main_returns'] == summary['main_output_checks'] and
            summary['maximum_main_invocations'] == 10000 and summary['warmup_deadline_milliseconds'] == 20000 and
            summary['main_argument'] == str(row['diagnostic_case']['n']), 'Main diagnostic count/size bound differs')
    runtime = summary['runtime']
    require({k:runtime[k] for k in kb.RUNTIME_KEYS} == plan['runtime_expected'] and runtime['flags'] == options and
            runtime['CLASS_PATH'] == str(probe_classes) and runtime['USER_HOME'] == str(case_dir/'home') and
            runtime['JAVA_TMPDIR'] == str(case_dir/'tmp') and runtime['JVM_MAIN'] == 'boundedqualification.WorkProbe',
            'Actual work-witness runtime differs')
    classes,stdlib = Path(row['classes']),Path(plan['stdlib'])
    require(kb.uri_path(summary['probe_code_source']) == probe_classes and kb.uri_path(summary['main_code_source']) == classes,
            'Actual work/main origin differs')
    origins = summary['non_platform_class_origins']; resources = summary['non_platform_class_resources']
    require(row['main_owner'] in origins and 'clbg.Support' in origins and set(origins) == set(resources),'Missing actual subject/helper origins')
    for owner,source in origins.items():
        require(owner in row['class_owner_names'] or owner.startswith('kotlin.'),'Unexpected observed dependency')
        expected = classes if owner in row['class_owner_names'] else stdlib
        require(kb.uri_path(source) == expected,'Observed class source differs')
        suffix = owner.replace('.','/')+'.class'
        if owner in row['class_owner_names']: require(kb.uri_path(resources[owner]) == classes/suffix,'Wrong subject resource')
        else:
            require(resources[owner].startswith('jar:') and '!/' in resources[owner],'Expected stdlib jar resource')
            jar,member = resources[owner][4:].split('!/',1)
            require(kb.uri_path(jar) == stdlib and member == suffix,'Wrong stdlib resource')
    result = dict(constructor_or_container_witness_applicable=False,constructor_or_container_witness_qualified=None,
                  optimized_main_allocation_and_lifetime_proved=False,runtime_pi_division_counts_proved=False)
    if row['benchmark'] == 'binarytrees':
        tree = summary['tree_witness']; cases = tree['fresh_identity_cases']
        require([(c['depth'],c['repetition'],c['nodes']) for c in cases] ==
                [(d,r,2**(d+1)-1) for d in (0,1,4,6,8) for r in (0,1)] and tree['all_graphs_disjoint'] is True and
                tree['retained_root_depth'] == 8 and tree['retained_descendants'] == 511 and
                tree['only_root_strong_during_pressure'] is True and tree['descendant_identity_preserved'] is True and
                0 <= tree['pressure_allocated_bytes'] <= 256*1024*1024 and tree['pressure_retained_bound_bytes'] == 32*1024*1024 and
                tree['tree_root_requests'] == tree['check_root_requests'] == 11 and
                tree['normal_gc_observed'] == (tree['gc_count_after'] > tree['gc_count_before']) and
                tree['optimized_main_allocation_and_lifetime_proved'] is False,'Invalid scored tree witness')
        result.update(constructor_or_container_witness_applicable=True,
                      constructor_or_container_witness_qualified=tree['normal_gc_observed'],tree_identity_qualified=True)
    elif row['benchmark'] == 'knucleotide':
        maps = summary['map_witness']
        seed = 'GGTATTTTAATTTATAGTACGTACGTTGCA'
        sequences = [seed[:n] for n in (0,1,2,17,18,19)] + [seed+'AAAAACCCCCGGGGGTTTTT'+seed+'ACGTACGT']
        require(len(maps) == 7 and [m['sequence'] for m in maps] == sequences,'Wrong full-map case inventory')
        for case in maps:
            require(case['length'] == len(case['sequence']) and case['seven_distinct_simultaneously_retained'] is True and
                    case['repeat_is_fresh'] is True and case['earlier_maps_unchanged'] is True and case['table_invocations'] == 8 and
                    [m['k'] for m in case['maps']] == [1,2,3,4,6,12,18],'Incomplete seven-map witness')
            for table in case['maps']:
                sequence,k = case['sequence'],table['k']; expected = {}
                for index in range(max(0,len(sequence)-k+1)):
                    word = sequence[index:index+k]; expected[word] = expected.get(word,0)+1
                require(table['entries'] == expected and table['count_sum'] == max(0,len(sequence)-k+1),'Independent complete map mismatch')
        result.update(constructor_or_container_witness_applicable=True,constructor_or_container_witness_qualified=True)
    elif row['benchmark'] == 'fannkuchredux':
        cases = summary['copy_witness']
        require([c['permutation'] for c in cases] == [[0],[1,0],[2,0,1],[3,2,1,0],[1,3,0,2]] and
                all(c['original_unchanged'] is True for c in cases),'Wrong copied-permutation witness')
        for case in cases:
            work = list(case['permutation']); total = 0
            while work[0]: work[:work[0]+1] = reversed(work[:work[0]+1]); total += 1
            require(case['flips'] == total,'Independent flip count differs')
        result.update(constructor_or_container_witness_applicable=True,constructor_or_container_witness_qualified=True)
    return result


def inventory_files(root,errors):
    files = []
    def failed(error,path=None):
        errors.append(dict(path=str(path if path is not None else getattr(error,'filename',root)),
                           error=str(error) or type(error).__name__))
    try:
        for directory,children,names in os.walk(root,onerror=failed,followlinks=False):
            retained = []
            for name in children+names:
                path = Path(directory)/name
                try:
                    mode = path.lstat().st_mode
                    require(not stat.S_ISLNK(mode),'Artifact symlink')
                    if stat.S_ISREG(mode): files.append(path)
                    else:
                        require(stat.S_ISDIR(mode),'Unexpected non-file artifact')
                        if name in children: retained.append(name)
                except BaseException as error: failed(error,path)
            children[:] = retained
    except BaseException as error: failed(error)
    return files


def validate_native_receipt(receipt,kind,directory):
    require(receipt['kind'] == kind and receipt['status'] == 'native-passed' and
            receipt['native_process_started'] is True and type(receipt['pid']) is int and receipt['pid'] > 0 and
            type(receipt['pgid']) is int and receipt['pgid'] == receipt['pid'] and
            type(receipt['exit_status']) is int and receipt['exit_status'] == 0 and receipt['direct_child_reaped'] is True and
            receipt['remaining_process_group'] == [] and receipt['inherited_common_mutex'] is True and
            receipt['common_mutex_inode'] == kb.LOCK_INODE and receipt['cwd'] == str(directory) and
            type(receipt['stdin_bytes']) is int and receipt['stdin_bytes'] == 0 and receipt['stdin_sha256'] == hashlib.sha256(b'').hexdigest() and
            not any(receipt.get(key) for key in ('error','error_type','cleanup_errors','artifact_errors','stop_signals',
                                                'remaining_after_cleanup','timed_out')), 'Native work receipt is not a clean owned exit')
    require(receipt['process_timeout_seconds'] == kb.TIMEOUT and receipt['cleanup_timeout_seconds'] == kb.CLEANUP_TIMEOUT and
            receipt['maximum_process_group_rss_bytes'] == kb.RSS_LIMIT and receipt['native_file_limit_bytes'] == kb.FILE_LIMIT and
            receipt['stdout_capture_limit_bytes'] == kb.FILE_LIMIT+kb.PIPE_CHUNK and
            type(receipt['kernel_monitor_samples']) is int and receipt['kernel_monitor_samples'] > 0 and
            type(receipt['observed_peak_process_group_rss_bytes']) is int and
            0 <= receipt['observed_peak_process_group_rss_bytes'] <= kb.RSS_LIMIT, 'Native work resource receipt differs')
    before,after = receipt['identity'],receipt['leader_identity_before_reap']
    require(all(type(before[key]) is int and type(after[key]) is int and before[key] == after[key]
                for key in ('pid','ppid','pgid','birth_seconds','birth_microseconds')) and
            before['pid'] == before['pgid'] == receipt['pid'] and before['ppid'] > 0 and type(after['status']) is int and after['status'] == 5,
            'Native work ownership observations differ')
    for name in ('stdout','stderr'):
        path = directory/(name+'.bin')
        require(type(receipt[name+'_bytes']) is int and receipt[name+'_bytes'] == path.stat().st_size == 0 and receipt[name+'_sha256'] == sha(path),
                'Native work stream receipt differs')


def snapshot_command(directory):
    errors = []; paths = inventory_files(directory,errors)
    required = {'stdout.bin','stderr.bin','process.json','start.json','active.json'}
    required |= ({'WorkProbe.java','BoundedProbe.java'} if directory.name == 'diagnostic-compile' else
                 {'stdin.bin','expected.stdout','owners.txt','summary.json','first.stdout','last.stdout',
                  'native-libraries.txt','classes.log','gc.log','hotspot.xml','validated.json'})
    require(not errors and required <= {str(p.relative_to(directory)) for p in paths}, 'Required native work artifact missing')
    return {str(p.relative_to(directory)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in paths}


def reconcile_native(report,output,plan):
    records,errors = [],[]
    report['observed_main_invocations'] = report['observed_main_returns'] = 0
    report['missing_main_observations'] = []
    passed = report['status'] == 'all20-bounded-work-witnesses-recorded-with-separate-open-gates'
    expected_ids = [row['id'] for row in plan['profiles']]
    qualified = {row['id']:row for row in report['profiles']}
    if passed and (len(qualified) != len(report['profiles']) or list(qualified) != expected_ids or report['active'] is not None):
        errors.append(dict(error='Successful work profile inventory differs'))
    for path in inventory_files(output,errors):
        if path.name != 'process.json': continue
        try:
            record = json.loads(path.read_bytes()); directory = path.parent
            require(directory.parent == output,'Unexpected nested native receipt')
            kind = 'diagnostic-compile' if directory.name == 'diagnostic-compile' else 'compiled-work'
            identity = None if kind == 'diagnostic-compile' else directory.name
            require(identity is None or identity in expected_ids,'Unknown work receipt profile')
            require(record['kind'] == kind,'Native receipt kind differs')
            if record['native_process_started']:
                require(type(record['pid']) is int and record['pid'] > 0 and type(record['pgid']) is int and record['pgid'] == record['pid'],
                        'Invalid saved native PID/PGID')
                records.append(dict(kind=kind,id=identity,pid=record['pid'],pgid=record['pgid']))
            if passed: validate_native_receipt(record,kind,directory)
            if kind == 'compiled-work' and record['native_process_started']:
                summary_path = directory/'summary.json'
                if summary_path.is_file():
                    summary = json.loads(summary_path.read_bytes())
                    for source,target in (('main_invocations','observed_main_invocations'),('main_returns','observed_main_returns')):
                        require(type(summary[source]) is int and 0 <= summary[source] <= 10000,'Invalid main observation count')
                        report[target] += summary[source]
                    if passed:
                        profile = qualified[identity]
                        require(summary['status'] == 'work-witnesses-recorded' and
                                0 < summary['main_invocations'] == summary['main_returns'] == summary['main_output_checks'] ==
                                profile['main_invocations'] == profile['main_returns'], 'Successful summary/profile counts differ')
                else:
                    report['missing_main_observations'].append(str(summary_path))
        except BaseException as error: errors.append(dict(path=str(path),error=str(error) or type(error).__name__))
    key = lambda row:(row['kind'],row['id'] or '',row['pid'],row['pgid'])
    if sorted(records,key=key) != sorted(report['native_process_ids'],key=key) or len(records) != report['native_processes_started']:
        errors.append(dict(error='Native start and saved kind/profile/PID/PGID inventories differ'))
    if passed:
        expected = {('diagnostic-compile',None)} | {('compiled-work',identity) for identity in expected_ids}
        if (len(records) != 21 or {(r['kind'],r['id']) for r in records} != expected or
                report['diagnostic_compiler_processes_started'] != 1 or report['work_jvm_processes_started'] != 20 or
                report['missing_main_observations'] or report['observed_main_invocations'] != report['observed_main_returns'] or
                report['observed_main_invocations'] != sum(r['main_invocations'] for r in report['profiles'])):
            errors.append(dict(error='Successful native/main observation inventory is incomplete'))
        flags = dict(required_work_witnesses_qualified=all(r['witness']['constructor_or_container_witness_qualified'] is not False for r in report['profiles']),
            subject_JIT_method_evidence_qualified=all(r['jit']['subject_JIT_method_evidence_qualified'] for r in report['profiles']),
            actual_subject_runtime_dependency_closure_qualified=all(r['actual_subject_runtime_dependency_closure_qualified'] for r in report['profiles']))
        if any(report[key] is not value for key,value in flags.items()): errors.append(dict(error='Work aggregate qualification flags differ'))
    snapshots = report['validated_command_artifacts']
    if passed and set(snapshots) != {'diagnostic-compile'} | set(expected_ids):
        errors.append(dict(error='Successful native artifact snapshot inventory differs'))
    for name,expected in snapshots.items():
        try:
            require(snapshot_command(output/name) == expected,'Validated command artifact inventory or bytes changed')
            if name in qualified:
                require(json.loads((output/name/'validated.json').read_bytes()) == qualified[name],
                        'Validated profile artifact and report differ')
        except BaseException as error: errors.append(dict(path=str(output/name),error=str(error) or type(error).__name__))
    report['registered_native_commands'] = records
    return errors


def finalize(report,pins,output,lock,plan):
    receipt_errors = reconcile_native(report,output,plan)
    integrity_errors = []
    for path,digest in pins.items():
        try: require(sha(path) == digest,'Pinned input changed')
        except BaseException as error: integrity_errors.append(dict(path=path,error=str(error)))
    report.update(integrity_errors=integrity_errors,process_receipt_errors=receipt_errors,
                  finished_at=datetime.now(timezone.utc).isoformat())
    if integrity_errors or receipt_errors:
        report.update(status='failed-input-or-native-integrity',required_work_witnesses_qualified=False,
            subject_JIT_method_evidence_qualified=False,actual_subject_runtime_dependency_closure_qualified=False)
    save(output/'report.json',report)
    artifacts = {}; artifact_errors = []
    for path in inventory_files(output,artifact_errors):
        try: artifacts[str(path.relative_to(output))] = dict(sha256=sha(path),bytes=path.stat().st_size)
        except BaseException as error: artifact_errors.append(dict(path=str(path),error=str(error)))
    for directory,snapshot in report['validated_command_artifacts'].items():
        for name,expected in snapshot.items():
            if artifacts.get(directory+'/'+name) != expected:
                artifact_errors.append(dict(path=directory+'/'+name,error='Terminal artifact differs from validated command snapshot'))
    if artifact_errors:
        report.update(status='failed-artifact-retention',required_work_witnesses_qualified=False,
            subject_JIT_method_evidence_qualified=False,actual_subject_runtime_dependency_closure_qualified=False,
            artifact_errors=artifact_errors)
        save(output/'report.json',report)
        artifacts['report.json'] = dict(sha256=sha(output/'report.json'),bytes=(output/'report.json').stat().st_size)
    kb.kh.verify_lock(lock)
    save(output/'terminal.json',dict(status=report['status'],report_sha256=sha(output/'report.json'),
        available_evidence=artifacts,integrity_errors=integrity_errors,artifact_errors=artifact_errors,
        process_receipt_errors=receipt_errors,native_processes_started=report['native_processes_started'],
        observed_main_invocations=report['observed_main_invocations'],observed_main_returns=report['observed_main_returns'],
        missing_main_observations=report['missing_main_observations'],
        diagnostic_compiler_processes_started=report['diagnostic_compiler_processes_started'],
        work_jvm_processes_started=report['work_jvm_processes_started'],
        required_work_witnesses_qualified=report['required_work_witnesses_qualified'],
        subject_JIT_method_evidence_qualified=report['subject_JIT_method_evidence_qualified'],
        actual_subject_runtime_dependency_closure_qualified=report['actual_subject_runtime_dependency_closure_qualified'],
        supplemental_output_prerequisite=report['supplemental_output_prerequisite'],
        specified_case_coverage_qualified=report['specified_case_coverage_qualified'],
        common_mutex_held=True,common_mutex_inode=kb.LOCK_INODE,subject_recompilations=0,benchmark_samples=0,
        source_work_qualified=False,canonical_loc=None,formatted_loc=None,full_timings_qualified=False,chart_admission=False))
    require(not integrity_errors and not receipt_errors and not artifact_errors,'Work witness evidence incomplete')


def run(args,lock):
    pins = {}; plan = read(args.plan,args.plan_sha256,pins)
    require(plan['schema'] == 'kotlin-retained-compiled-work-plan-v1' and plan['controller_sha256'] == sha(__file__) and
            plan['planned_native_commands'] == 21 and len(plan['profiles']) == 20 and
            plan['specified_case_coverage_qualified'] is True and
            plan['supplemental_output_prerequisite']['specified_case_coverage_qualified'] is True and
            plan['supplemental_output_prerequisite']['qualified_cases'] == 30 and
            plan['supplemental_output_prerequisite']['combined_qualified_form_cases'] == 186,'Wrong compiled-work plan')
    pins.update(plan['pins'])
    for path,digest in pins.items(): require(sha(path) == digest,'Preflight input changed: '+path)
    output = Path(plan['output']); require(not output.exists(),'Fresh output required; no retry')
    output.mkdir(parents=True)
    report = dict(schema='kotlin-retained-compiled-work-results-v1',status='running',plan=str(args.plan.resolve()),
        plan_sha256=args.plan_sha256,pins=pins,profiles=[],active=None,native_processes_started=0,
        diagnostic_compiler_processes_started=0,work_jvm_processes_started=0,native_process_ids=[],validated_command_artifacts={},
        observed_main_invocations=0,observed_main_returns=0,missing_main_observations=[],subject_recompilations=0,benchmark_samples=0,
        supplemental_output_prerequisite=plan['supplemental_output_prerequisite'],specified_case_coverage_qualified=True,
        source_and_retained_bytecode_review_bound=True,required_work_witnesses_qualified=False,
        subject_JIT_method_evidence_qualified=False,actual_subject_runtime_dependency_closure_qualified=False,
        source_work_qualified=False,optimized_main_allocation_and_lifetime_proved=False,
        canonical_loc=None,formatted_loc=None,full_timings_qualified=False,chart_admission=False)
    save(output/'report.json',report)
    def register(kind,directory,identity=None):
        report['active'] = dict(kind=kind,id=identity,receipt=str(directory/'process.json'),pid=None)
        save(output/'report.json',report)
        def launched(pid):
            report['native_processes_started'] += 1
            report['diagnostic_compiler_processes_started' if kind == 'diagnostic-compile' else 'work_jvm_processes_started'] += 1
            report['native_process_ids'].append(dict(kind=kind,id=identity,pid=pid,pgid=pid))
            report['active']['pid'] = pid; save(output/'report.json',report)
        return launched
    try:
        compilation = output/'diagnostic-compile'; compilation.mkdir()
        env = kb.kh.environment(plan['profiles'][0]['runtime_environment'],compilation)
        classes = output/'probe-classes'; classes.mkdir()
        sources = []
        for field in ('probe_source','loader_source'):
            source = Path(plan[field]); copy = compilation/source.name; copy.write_bytes(source.read_bytes())
            require(sha(copy) == pins[str(source)],'Diagnostic source changed while copying'); sources.append(str(copy))
        command = [plan['javac']]+['-J'+x for x in FLAGS]+['-J-Duser.home='+str(compilation/'home'),
            '-J-Djava.io.tmpdir='+str(compilation/'tmp'),'--release','17','-d',str(classes)]+sources
        receipt = kb.observe(command,env,compilation,b'',lock,register('diagnostic-compile',compilation),kind='diagnostic-compile')
        validate_native_receipt(receipt,'diagnostic-compile',compilation)
        generated = {str(p.relative_to(classes)) for p in classes.rglob('*') if p.is_file()}
        require(generated == {'boundedqualification/WorkProbe.class','boundedqualification/BoundedProbe.class',
                             'boundedqualification/BoundedProbe$SubjectLoader.class'},'Wrong diagnostic class inventory')
        for relative in generated:
            path = classes/relative; raw = path.read_bytes()
            require(raw[:4] == b'\xca\xfe\xba\xbe' and int.from_bytes(raw[6:8],'big') == 61,'Wrong diagnostic target')
            pins[str(path)] = sha(path)
        report['validated_command_artifacts']['diagnostic-compile'] = snapshot_command(compilation)
        report['active'] = None; save(output/'report.json',report)
        for row in plan['profiles']:
            kb.kh.verify_lock(lock)
            selected = Path(row['classes'])
            require({str(p.relative_to(selected)) for p in selected.rglob('*') if p.is_file()} ==
                    {a['relative_path'] for a in row['class_artifacts']} and not any(p.is_symlink() for p in selected.rglob('*')),
                    'Retained class inventory changed')
            case = row['diagnostic_case']
            hot = row['physical_inputs']+row['class_artifacts']+[case['expected']]
            if case['stdin']: hot.append(case['stdin'])
            for item in hot: require(sha(item['path']) == item['sha256'],'Active input changed')
            for relative in generated: require(sha(classes/relative) == pins[str(classes/relative)],'Diagnostic class changed')
            directory = output/row['id']; directory.mkdir()
            env = kb.kh.environment(row['runtime_environment'],directory)
            payload = Path(case['stdin']['path']).read_bytes() if case['stdin'] else b''
            expected = Path(case['expected']['path']).read_bytes()
            (directory/'stdin.bin').write_bytes(payload); (directory/'expected.stdout').write_bytes(expected)
            (directory/'owners.txt').write_text('\n'.join(row['class_owner_names'])+'\n')
            options = FLAGS+[f'-Duser.home={directory}/home',f'-Djava.io.tmpdir={directory}/tmp',
                '-XX:+UnlockDiagnosticVMOptions','-XX:+LogCompilation',f'-XX:LogFile={directory}/hotspot.xml',
                f'-Xlog:class+load=info:file={directory}/classes.log:uptime,tags',
                f'-Xlog:gc*=info:file={directory}/gc.log:uptime,tags']
            command = [plan['java']]+options+['-cp',str(classes),'boundedqualification.WorkProbe',row['classes'],plan['stdlib'],
                str(directory/'owners.txt'),row['benchmark'],str(directory/'stdin.bin'),str(directory/'expected.stdout'),
                str(case['n']),str(directory),'10000','20000']
            receipt = kb.observe(command,env,directory,b'',lock,register('compiled-work',directory,row['id']),kind='compiled-work')
            validate_native_receipt(receipt,'compiled-work',directory)
            require((directory/'stdout.bin').read_bytes() == b'','Diagnostic leaked stdout')
            summary = json.loads((directory/'summary.json').read_bytes())
            witness = validate_witness(summary,row,plan,directory,classes,options)
            require(summary['stdin_sha256'] == hashlib.sha256(payload).hexdigest() and
                    summary['expected_stdout_sha256'] == hashlib.sha256(expected).hexdigest(),'Actual diagnostic input binding differs')
            validations = {name:kb.eb.output_validation(row['benchmark'],(directory/name).read_bytes(),expected)
                           for name in ('first.stdout','last.stdout')}
            loaded = validate_log((directory/'classes.log').read_text(),selected,Path(plan['stdlib']),classes,set(row['class_owner_names']))
            observed = {owner:source for owner,source in loaded.items() if owner.startswith(('clbg.','kotlin.'))}
            require(set(observed) == set(summary['non_platform_class_origins']) and
                    all(kb.uri_path(source) == kb.uri_path(summary['non_platform_class_origins'][owner]) for owner,source in observed.items()),
                    'JVM and loader dependency observations differ')
            gc = (directory/'gc.log').read_text(); require('Using G1' in gc,'Actual G1 evidence missing')
            if row['benchmark'] == 'binarytrees' and summary['tree_witness']['normal_gc_observed']:
                require('Pause Young' in gc or 'Concurrent Mark Cycle' in gc,'Collection counter lacks G1 log evidence')
            jit = jit_records(directory/'hotspot.xml',row['required_jit_methods'])
            native = native_libraries((directory/'native-libraries.txt').read_text(),pins,Path(plan['java']).parent.parent)
            qualified = dict(id=row['id'],status='bounded-work-and-runtime-observations-recorded',witness=witness,jit=jit,
                actual_loaded_classes=loaded,native_libraries=native,validation=validations,
                main_invocations=summary['main_invocations'],main_returns=summary['main_returns'],
                actual_subject_runtime_dependency_closure_qualified=native['native_non_platform_images_qualified'],
                source_work_qualified=False,optimized_main_allocation_and_lifetime_proved=False,
                canonical_loc=None,formatted_loc=None,full_timings_qualified=False,chart_admission=False)
            save(directory/'validated.json',qualified)
            report['validated_command_artifacts'][row['id']] = snapshot_command(directory)
            report['profiles'].append(qualified); report['active'] = None
            save(output/'report.json',report); print('Recorded Kotlin compiled-work witness: '+row['id'],flush=True)
        require(len(report['profiles']) == 20 and report['work_jvm_processes_started'] == 20 and
                report['diagnostic_compiler_processes_started'] == 1,'Incomplete actual diagnostic ledger')
        report.update(status='all20-bounded-work-witnesses-recorded-with-separate-open-gates',
            required_work_witnesses_qualified=all(p['witness']['constructor_or_container_witness_qualified'] is not False for p in report['profiles']),
            subject_JIT_method_evidence_qualified=all(p['jit']['subject_JIT_method_evidence_qualified'] for p in report['profiles']),
            actual_subject_runtime_dependency_closure_qualified=all(p['actual_subject_runtime_dependency_closure_qualified'] for p in report['profiles']))
    except BaseException as error:
        report.update(status='failed',error=str(error) or type(error).__name__,error_type=type(error).__name__)
        raise
    finally:
        with atomic(): finalize(report,pins,output,lock,plan)


def main():
    parser = argparse.ArgumentParser(description=__doc__); commands = parser.add_subparsers(dest='action',required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--bounded-report',type=Path,required=True); prep.add_argument('--bounded-report-sha256',required=True)
    prep.add_argument('--bounded-terminal-sha256',required=True)
    prep.add_argument('--supplement-report',type=Path,required=True); prep.add_argument('--supplement-report-sha256',required=True)
    prep.add_argument('--supplement-terminal-sha256',required=True)
    prep.add_argument('--plan',type=Path,required=True); prep.add_argument('--output',type=Path,required=True)
    execute = commands.add_parser('run'); execute.add_argument('--plan',type=Path,required=True); execute.add_argument('--plan-sha256',required=True)
    args = parser.parse_args()
    require(Path(sys.executable).resolve() == kb.kh.PYTHON.resolve() and sys.flags.isolated and sys.flags.no_site and
            sys.flags.dont_write_bytecode and not sys.flags.optimize,'Use pinned Python with -I -S -B')
    def interrupted(signum,frame): raise KeyboardInterrupt('Kotlin compiled-work interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS: signal.signal(sig,interrupted)
    with LOCK.open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); kb.kh.verify_lock(lock)
        if args.action == 'prepare': prepare(args)
        else: run(args,lock)


if __name__ == '__main__': main()
