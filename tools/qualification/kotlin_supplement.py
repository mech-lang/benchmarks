#!/usr/bin/env python3
"""Add the original Kotlin specification's 15 missing references / 30 form cases.

The closed 156-case run remains immutable. This stage requires its explicit
completed report hashes and uses the same exact classes and atomic observer.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import importlib.util
import json
from pathlib import Path
import os
import re
import signal
import stat
import sys

ROOT = Path(__file__).resolve().parents[2]
PACKET = ROOT/'experiments/kotlin/specified-cases-v1'
BOUNDED_CONTROLLER_SHA = 'c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc'
SPEC = ROOT/'experiments/kotlin/source-owner-review-v1/bounded-checks.json'
SPEC_SHA = '8ba71e98e63e29f40351b028368c8e2bcf0ddf8d47ac240b69aa48d562e812cd'
NUMERIC = {'pidigits':[100], 'fasta':[19,20,21,59,1000], 'mandelbrot':[64],
           'nbody':[10,1000], 'spectralnorm':[10]}
STREAMS = {'revcomp':['specified-record-boundaries-and-cr'],
           'regexredux':['specified-all-count-alternatives','specified-overlapping-candidates'],
           'knucleotide':['specified-composite-space','specified-composite-tab']}
SUCCESS = 'specified-30-cases-passed-awaiting-work-JIT-and-LOC'


def require(value, message):
    if not value: raise AssertionError(message)


def sha(path):
    with Path(path).open('rb') as stream: return hashlib.file_digest(stream,'sha256').hexdigest()


def module(path, digest, name):
    raw = Path(path).read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'Reviewed module changed: '+str(path))
    spec = importlib.util.spec_from_file_location(name,path)
    result = importlib.util.module_from_spec(spec)
    exec(compile(raw,str(path),'exec'),result.__dict__)
    return result


kb = module(ROOT/'tools/qualification/kotlin_bounded_v2.py', BOUNDED_CONTROLLER_SHA, 'supplement_bounded')
save, atomic, LOCK, FLAGS = kb.save, kb.atomic, kb.LOCK, kb.FLAGS


def bind(path, digest, pins):
    path = Path(path).resolve()
    require(sha(path) == digest and (str(path) not in pins or pins[str(path)] == digest), 'Changed/conflicting input: '+str(path))
    pins[str(path)] = digest
    return path


def read(path, digest, pins):
    path = bind(path,digest,pins); raw = path.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == digest, 'JSON changed during read')
    return json.loads(raw)


def validate_bounded(report, terminal, digest):
    require(report['schema'] == 'kotlin-retained-classes-bounded-results-v1' and
        report['status'] == terminal['status'] == 'all20-bounded-output-passed-awaiting-work-JIT-and-LOC' and
        report['bounded_outputs_qualified'] is True and terminal['report_sha256'] == digest and
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
        terminal['artifact_errors'] == terminal['process_receipt_errors'] == [], 'Completed 156-case prerequisite missing')


def fixture_schedule(fixtures):
    expected = [(bench,'n-'+str(n),n) for bench,ns in NUMERIC.items() for n in ns]
    expected += [(bench,name,0) for bench,names in STREAMS.items() for name in names]
    require([(f['benchmark'],f['case'],f['n']) for f in fixtures] == expected and len(fixtures) == 15,
            'Specified supplemental fixture inventory differs')
    require(all(('stdin_ascii' in f) == (f['benchmark'] in STREAMS) for f in fixtures), 'Wrong supplemental input kind')
    require(all(re.fullmatch('[a-z0-9-]+',f['case']) and type(f['n']) is int for f in fixtures), 'Unsafe supplemental case name/size')
    return expected


def validate_coverage(profiles, fixtures):
    fixture_schedule(fixtures)
    require(len(profiles) == len({p['id'] for p in profiles}) == 20 and
            set(p['benchmark'] for p in profiles) == set(kb.CASE_NAMES), 'Incomplete retained profile cohort')
    for bench in kb.CASE_NAMES:
        require({p['variant'] for p in profiles if p['benchmark'] == bench} == {'compact','optimized'} and
                len([p for p in profiles if p['benchmark'] == bench]) == 2, 'Missing independently retained form')
    schedule = []
    for row in profiles:
        require(row['id'] == 'kotlin-'+row['benchmark']+'-'+row['variant'], 'Wrong retained profile ID')
        expected = [(f['case'],f['n']) for f in fixtures if f['benchmark'] == row['benchmark']]
        require([(c['case'],c['n']) for c in row['bounded_cases']] == expected, 'Supplemental case schedule differs')
        for case in row['bounded_cases']:
            require((case['stdin'] is not None) == (row['benchmark'] in STREAMS), 'Supplemental stdin binding differs')
            schedule.append((row['id'],case['case']))
    require(len(schedule) == len(set(schedule)) == 30, 'Expected thirty distinct form cases')
    return schedule


def validate_completed(report, terminal, digest, bounded_digest):
    require(report['schema'] == 'kotlin-specified-cases-results-v1' and report['status'] == terminal['status'] == SUCCESS and
        terminal['report_sha256'] == digest and report['bounded_report_sha256'] == terminal['bounded_report_sha256'] == bounded_digest and
        report['specified_case_coverage_qualified'] is terminal['specified_case_coverage_qualified'] is True and
        report['qualified_supplemental_cases'] == terminal['qualified_supplemental_cases'] == 30 and
        report['native_processes_started'] == terminal['native_processes_started'] == 31 and
        report['diagnostic_compiler_processes_started'] == terminal['diagnostic_compiler_processes_started'] == 1 and
        report['supplemental_jvm_processes_started'] == terminal['supplemental_jvm_processes_started'] == 30 and
        report['observed_subject_main_invocations'] == terminal['observed_subject_main_invocations'] == 30 and
        report['observed_subject_main_returns'] == terminal['observed_subject_main_returns'] == 30 and
        report['combined_qualified_form_cases'] == terminal['combined_qualified_form_cases'] == 186 and
        len(report['profiles']) == len(set(report['profiles'])) == 20 and len(report['cases']) == 30 and
        report['active'] is None and report['subject_recompilations'] == report['benchmark_samples'] == 0 and
        report['chart_admission'] is False and terminal['common_mutex_held'] is True and
        terminal['common_mutex_inode'] == kb.LOCK_INODE and
        report['integrity_errors'] == report['process_receipt_errors'] == terminal['integrity_errors'] ==
        terminal['artifact_errors'] == terminal['process_receipt_errors'] == [], 'Completed specified-case prerequisite missing')


def bind_artifacts(directory, terminal, pins):
    for name,item in terminal['available_evidence'].items():
        require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'Unsafe prerequisite artifact path')
        path = bind(directory/name,item['sha256'],pins)
        require(path.stat().st_size == item['bytes'], 'Prerequisite artifact size differs')


def original_case_bindings(report,terminal,bounded,directory,pins):
    """Bind the saved 156 output proofs; this observes no new runtime work."""
    directory=Path(directory).resolve()
    completed={(c['id'],c['case']):c for c in report['cases']}
    expected={(r['id'],c['case']) for r in bounded['profiles'] for c in r['bounded_cases']}
    require(len(completed)==len(report['cases'])==156 and set(completed)==expected,'Original case output inventory differs')
    def artifact(relative,digest):
        path=directory/relative; metadata=terminal['available_evidence'].get(str(relative))
        require(metadata is not None and metadata['sha256']==digest,'Original report and terminal artifact hashes differ')
        bind(path,digest,pins)
        require(type(metadata['bytes']) is int and metadata['bytes']==path.stat().st_size,'Original terminal artifact size differs')
        return path
    for row in bounded['profiles']:
        for case in row['bounded_cases']:
            record=completed[(row['id'],case['case'])]; relative=Path(row['id'])/case['case']; target=directory/relative
            require(record['status']=='bounded-output-passed','Original case status differs')
            for field in ('validated','process'):
                require(Path(record[field]).resolve()==target/(field+'.json'),'Original case references another command artifact')
                artifact(relative/(field+'.json'),record[field+'_sha256'])
            validated=read(record['validated'],record['validated_sha256'],pins)
            receipt=read(record['process'],record['process_sha256'],pins)
            require(validated['status']=='bounded-output-passed' and validated['id']==row['id'] and
                validated['case']==case['case'] and validated['n']==case['n'] and validated['reference_evidence']==case and
                validated['main_invocations']==validated['main_returns']==1 and
                validated['validation']['reference_match'] is True,'Original saved output proof differs')
            validate_receipt(receipt,'bounded-main',target)
            validation=validated['validation']
            require(validation['stdout_sha256']==receipt['stdout_sha256'] and
                validation['stdout_bytes']==receipt['stdout_bytes'] and
                validation['expected_sha256']==case['expected']['sha256'],'Original output/receipt/reference hashes differ')
            actual=artifact(relative/'stdout.bin',validation['stdout_sha256'])
            expected_path=artifact(relative/'expected.stdout',validation['expected_sha256'])
            artifact(relative/'stderr.bin',receipt['stderr_sha256'])
            artifact(relative/'stdin.bin',receipt['stdin_sha256'])
            expected_input=case['stdin']['sha256'] if case['stdin'] else hashlib.sha256(b'').hexdigest()
            require(receipt['stdin_sha256']==expected_input,'Original input receipt/reference differs')
            require(kb.eb.output_validation(row['benchmark'],actual.read_bytes(),expected_path.read_bytes())==validation,
                    'Original saved output validation does not match retained bytes')
    return dict(original_cases=156,saved_output_and_receipt_artifacts_bound=True,new_native_executions=0,
        runtime_work_proved=False,source_work_qualified=False,chart_admission=False)


def prepare(args):
    references = args.plan.with_name(args.plan.stem+'-references').resolve()
    require(not args.plan.exists() and not args.output.exists() and not references.exists() and
            not args.plan.resolve().is_relative_to(args.output.resolve()) and
            not references.is_relative_to(args.output.resolve()), 'Fresh plan/reference directory outside fresh output required')
    pins = {}
    report = read(args.bounded_report,args.bounded_report_sha256,pins)
    terminal = read(args.bounded_report.with_name('terminal.json'),args.bounded_terminal_sha256,pins)
    validate_bounded(report,terminal,args.bounded_report_sha256)
    bounded = read(report['plan'],report['plan_sha256'],pins)
    require(bounded['schema'] == 'kotlin-retained-classes-bounded-plan-v1' and
            bounded['controller_sha256'] == BOUNDED_CONTROLLER_SHA and
            [r['id'] for r in bounded['profiles']] == report['profiles'], 'Wrong completed bounded plan')
    kb.bounded_schedule(bounded['profiles'])
    require({(c['id'],c['case']) for c in report['cases']} ==
            {(r['id'],c['case']) for r in bounded['profiles'] for c in r['bounded_cases']}, 'Incomplete original bounded cases')
    for path,digest in report['pins'].items(): bind(path,digest,pins)
    bind_artifacts(args.bounded_report.parent,terminal,pins)
    original_proof=original_case_bindings(report,terminal,bounded,args.bounded_report.parent,pins)
    require(kb.aliases(bounded['profiles']) == bounded['alias_pairs'] == report['alias_pairs'], 'Alias pairs differ')
    spec = read(SPEC,SPEC_SHA,pins)
    for bench,ns in NUMERIC.items():
        required = [0,1,9,10,11,27,100] if bench == 'pidigits' else spec['work_stage']['other_bounded_workloads'][bench]['sizes']
        require(set(required)-set(kb.NUMERIC[bench]) == set(ns), 'Original numeric specification gap differs')
    fixture_path = PACKET/'fixtures.json'; fixtures = read(fixture_path,sha(fixture_path),pins); fixture_schedule(fixtures)
    gap = read(PACKET/'gap-analysis.json',sha(PACKET/'gap-analysis.json'),pins)
    require(gap['original_specification_sha256'] == SPEC_SHA and gap['planned_supplemental_reference_cases'] == 15 and
            gap['planned_supplemental_form_cases'] == 30 and gap['status'] == 'source-only-not-executed', 'Gap receipt differs')
    oracle_path = PACKET/'oracles.py'; bind(oracle_path,sha(oracle_path),pins)
    oracle = module(oracle_path,pins[str(oracle_path)],'specified_output_oracles')
    bind(oracle.REFERENCE,oracle.REFERENCE_SHA,pins); independent = oracle.legacy()
    references.mkdir(parents=True)
    cases = {bench:[] for bench in kb.CASE_NAMES}
    for fixture in fixtures:
        directory = references/fixture['benchmark']/fixture['case']; directory.mkdir(parents=True)
        expected = oracle.expected(fixture,independent); path = directory/'expected.stdout'; path.write_bytes(expected)
        output_ref = dict(path=str(path),sha256=sha(path)); bind(path,output_ref['sha256'],pins)
        stdin = None
        if 'stdin_ascii' in fixture:
            path = directory/'stdin.bin'; path.write_bytes(fixture['stdin_ascii'].encode('ascii'))
            stdin = dict(path=str(path),sha256=sha(path)); bind(path,stdin['sha256'],pins)
        cases[fixture['benchmark']].append(dict(case=fixture['case'],n=fixture['n'],stdin=stdin,expected=output_ref,
            fixture=fixture,oracle_source=dict(path=str(oracle_path),sha256=pins[str(oracle_path)]),
            retained_independent_oracle=dict(path=str(oracle.REFERENCE),sha256=oracle.REFERENCE_SHA),
            validation='finite-two-energy-lines-within-1e-8' if fixture['benchmark']=='nbody' else 'exact-complete-bytes'))
    rows = [dict(row,bounded_cases=cases[row['benchmark']]) for row in bounded['profiles']]
    schedule = validate_coverage(rows,fixtures)
    for path in (Path(__file__).resolve(),ROOT/'tools/qualification/kotlin_bounded_v2.py',
                 ROOT/'experiments/kotlin/bounded-work-v1/BoundedProbe.java',kb.kh.PYTHON): bind(path,sha(path),pins)
    require(pins[str(kb.kh.PYTHON)] == kb.kh.PYTHON_SHA, 'Wrong controller interpreter')
    plan = dict(schema='kotlin-specified-cases-plan-v1',status='prepared-awaiting-native-supplemental-execution',
        controller_sha256=sha(__file__),bounded_report=str(args.bounded_report.resolve()),bounded_report_sha256=args.bounded_report_sha256,
        bounded_terminal_sha256=args.bounded_terminal_sha256,original_specification_sha256=SPEC_SHA,
        original_output_artifact_binding=original_proof,
        fixtures=fixtures,profiles=rows,alias_pairs=bounded['alias_pairs'],pins=pins,java=bounded['java'],javac=bounded['javac'],
        stdlib=bounded['stdlib'],runtime_expected=bounded['runtime_expected'],probe_source=bounded['probe_source'],
        reference_directory=str(references),output=str(args.output.resolve()),case_schedule=schedule,
        distinct_supplemental_references=15,planned_subject_main_invocations=30,planned_native_commands=31,
        original_qualified_cases=156,combined_planned_form_cases=186,oracle_generator_executions=15,
        automatic_retry=False,subject_recompilations=0,benchmark_samples=0,specified_case_coverage_qualified=False,
        process_timeout_seconds=30,cleanup_timeout_seconds=5,maximum_process_group_rss_bytes=kb.RSS_LIMIT,
        native_file_limit_bytes=kb.FILE_LIMIT,source_work_qualified=False,subject_JIT_method_evidence_qualified=False,
        actual_subject_runtime_dependency_closure_qualified=False,canonical_loc=None,formatted_loc=None,
        full_timings_qualified=False,chart_admission=False)
    args.plan.parent.mkdir(parents=True,exist_ok=True); save(args.plan,plan)
    print(json.dumps(dict(plan=str(args.plan),sha256=sha(args.plan),native_executions=0)),flush=True)


def inventory_files(root, errors):
    files = []
    def failed(error,path=None):
        errors.append(dict(path=str(path if path is not None else getattr(error,'filename',root)),error=str(error) or type(error).__name__))
    try:
        for directory,children,names in os.walk(root,onerror=failed,followlinks=False):
            retained = []
            for name in children+names:
                path = Path(directory)/name
                try:
                    mode = path.lstat().st_mode
                    require(not stat.S_ISLNK(mode),'Unexpected output symlink')
                    if stat.S_ISREG(mode): files.append(path)
                    else:
                        require(stat.S_ISDIR(mode),'Unexpected non-file output artifact')
                        if name in children: retained.append(name)
                except BaseException as error: failed(error,path)
            children[:] = retained
    except BaseException as error: failed(error)
    return files


def validate_receipt(receipt,kind,directory):
    require(receipt['kind'] == kind and receipt['status'] == 'native-passed' and receipt['native_process_started'] is True and
        type(receipt['pid']) is int and receipt['pid']>0 and type(receipt['pgid']) is int and receipt['pgid']==receipt['pid'] and
        type(receipt['exit_status']) is int and receipt['exit_status']==0 and receipt['cwd']==str(directory) and
        receipt['direct_child_reaped'] is True and receipt['remaining_process_group']==[] and
        receipt['inherited_common_mutex'] is True and receipt['common_mutex_inode']==kb.LOCK_INODE and
        not any(receipt.get(k) for k in ('error','error_type','cleanup_errors','artifact_errors','stop_signals','remaining_after_cleanup','timed_out')),
        'Supplement command did not have a clean owned exit')
    require(receipt['process_timeout_seconds']==kb.TIMEOUT and receipt['cleanup_timeout_seconds']==kb.CLEANUP_TIMEOUT and
        receipt['maximum_process_group_rss_bytes']==kb.RSS_LIMIT and receipt['native_file_limit_bytes']==kb.FILE_LIMIT and
        receipt['stdout_capture_limit_bytes']==kb.FILE_LIMIT+kb.PIPE_CHUNK and
        type(receipt['kernel_monitor_samples']) is int and receipt['kernel_monitor_samples']>0 and
        type(receipt['observed_peak_process_group_rss_bytes']) is int and
        0<=receipt['observed_peak_process_group_rss_bytes']<=kb.RSS_LIMIT,'Supplement resource receipt differs')
    before,after=receipt['identity'],receipt['leader_identity_before_reap']
    fields=('pid','ppid','pgid','birth_seconds','birth_microseconds')
    require(all(type(before[key]) is int and type(after[key]) is int and before[key]==after[key] for key in fields) and
        before['pid']==before['pgid']==receipt['pid'] and before['ppid']>0 and type(after['status']) is int and after['status']==5,
        'Supplement ownership observations differ')
    for name in ('stdout','stderr'):
        path=directory/(name+'.bin'); count=receipt[name+'_bytes']
        limit=kb.FILE_LIMIT+kb.PIPE_CHUNK if name=='stdout' and kind=='bounded-main' else 0
        require(type(count) is int and 0<=count<=limit and count==path.stat().st_size and receipt[name+'_sha256']==sha(path),
            'Supplement stream receipt differs')
    payload=(directory/'stdin.bin').read_bytes() if kind=='bounded-main' else b''
    require(type(receipt['stdin_bytes']) is int and receipt['stdin_bytes']==len(payload) and
        receipt['stdin_sha256']==hashlib.sha256(payload).hexdigest(),'Supplement stdin receipt differs')


def snapshot_command(directory,kind):
    errors=[];paths=inventory_files(directory,errors)
    required={'stdout.bin','stderr.bin','process.json','start.json','active.json'}
    required |= ({'BoundedProbe.java'} if kind=='diagnostic-compile' else
                 {'stdin.bin','expected.stdout','owners.txt','summary.json','classes.log','gc.log','validated.json'})
    require(not errors and required<={str(p.relative_to(directory)) for p in paths},'Required supplemental artifact missing')
    return {str(p.relative_to(directory)):dict(sha256=sha(p),bytes=p.stat().st_size) for p in paths}


def reconcile_native(output, report):
    records, errors, missing = [], [], []
    report['observed_subject_main_invocations'] = report['observed_subject_main_returns'] = 0
    for path in inventory_files(output,errors):
        if path.name != 'process.json': continue
        try:
            receipt = json.loads(path.read_bytes()); kind = receipt['kind']
            require(kind in ('diagnostic-compile','bounded-main'), 'Unexpected saved native kind')
            profile_id,case = (None,None) if kind=='diagnostic-compile' else (path.parent.parent.name,path.parent.name)
            if receipt['native_process_started']:
                require(type(receipt['pid']) is int and receipt['pid']>0 and type(receipt['pgid']) is int and
                    receipt['pgid']==receipt['pid'],'Invalid supplemental native PID/PGID')
                records.append(dict(kind=kind,id=profile_id,case=case,pid=receipt['pid'],pgid=receipt['pgid']))
            if report['specified_case_coverage_qualified']: validate_receipt(receipt,kind,path.parent)
            if kind == 'bounded-main' and receipt['native_process_started']:
                summary = path.with_name('summary.json')
                if summary.is_file():
                    value = json.loads(summary.read_bytes())
                    for source,target in (('benchmark_main_invocations','observed_subject_main_invocations'),
                                          ('benchmark_main_returns','observed_subject_main_returns')):
                        require(type(value[source]) is int and 0 <= value[source] <= 1,'Invalid observed main count')
                        report[target] += value[source]
                else: missing.append(str(summary))
        except BaseException as error: errors.append(dict(path=str(path),error=str(error) or type(error).__name__))
    if sorted(records,key=lambda r:r['pid']) != sorted(report['native_process_ids'],key=lambda r:r['pid']) or len(records)!=report['native_processes_started']:
        errors.append(dict(error='Actual native starts and saved process receipt inventories differ'))
    if report['specified_case_coverage_qualified'] and not (
            len(records)==31 and report['observed_subject_main_invocations']==report['observed_subject_main_returns']==30 and not missing):
        errors.append(dict(error='Successful supplement native/main inventory is incomplete'))
    report['registered_native_commands'] = records
    report['unobserved_main_summaries'] = missing
    snapshots=report['validated_command_artifacts']
    if report['specified_case_coverage_qualified']:
        expected={'diagnostic-compile'}|{c['id']+'/'+c['case'] for c in report['cases']}
        if len(expected)!=31 or set(snapshots)!=expected:
            errors.append(dict(error='Successful supplemental artifact snapshot inventory differs'))
    for name,expected in snapshots.items():
        try:
            kind='diagnostic-compile' if name=='diagnostic-compile' else 'bounded-main'
            require(snapshot_command(output/name,kind)==expected,'Validated supplemental artifact inventory or bytes changed')
        except BaseException as error: errors.append(dict(path=str(output/name),error=str(error) or type(error).__name__))
    return errors


def finalize(report,pins,output,lock):
    errors = reconcile_native(output,report); integrity = []
    for path,digest in pins.items():
        try: require(sha(path)==digest,'Pinned input changed')
        except BaseException as error: integrity.append(dict(path=path,error=str(error) or type(error).__name__))
    if errors or integrity: report.update(status='failed-input-or-native-integrity',specified_case_coverage_qualified=False)
    report.update(process_receipt_errors=errors,integrity_errors=integrity,finished_at=datetime.now(timezone.utc).isoformat())
    save(output/'report.json',report)
    artifacts,artifact_errors = {},[]
    for path in inventory_files(output,artifact_errors):
        try: artifacts[str(path.relative_to(output))] = dict(sha256=sha(path),bytes=path.stat().st_size)
        except BaseException as error: artifact_errors.append(dict(path=str(path),error=str(error) or type(error).__name__))
    for directory,snapshot in report['validated_command_artifacts'].items():
        for name,expected in snapshot.items():
            if artifacts.get(directory+'/'+name)!=expected:
                artifact_errors.append(dict(path=directory+'/'+name,error='Terminal artifact differs from supplemental validated snapshot'))
    if artifact_errors:
        report.update(status='failed-artifact-integrity',specified_case_coverage_qualified=False,artifact_errors=artifact_errors)
        save(output/'report.json',report)
        artifacts['report.json'] = dict(sha256=sha(output/'report.json'),bytes=(output/'report.json').stat().st_size)
    kb.kh.verify_lock(lock)
    fields = ('status','bounded_report_sha256','specified_case_coverage_qualified','native_processes_started',
              'diagnostic_compiler_processes_started','supplemental_jvm_processes_started','qualified_supplemental_cases',
              'observed_subject_main_invocations','observed_subject_main_returns','combined_qualified_form_cases',
              'original_output_artifact_binding')
    save(output/'terminal.json',dict({k:report[k] for k in fields},report_sha256=sha(output/'report.json'),
        available_evidence=artifacts,process_receipt_errors=errors,integrity_errors=integrity,artifact_errors=artifact_errors,
        common_mutex_held=True,common_mutex_inode=kb.LOCK_INODE,subject_recompilations=0,benchmark_samples=0,
        source_work_qualified=False,subject_JIT_method_evidence_qualified=False,actual_subject_runtime_dependency_closure_qualified=False,
        canonical_loc=None,formatted_loc=None,full_timings_qualified=False,chart_admission=False))
    require(not errors and not integrity and not artifact_errors,'Supplement input/output/native integrity failed')


def run(args,lock):
    require(sha(args.plan)==args.plan_sha256,'Reviewed supplement plan changed')
    plan = json.loads(args.plan.read_bytes())
    require(plan['schema']=='kotlin-specified-cases-plan-v1' and plan['controller_sha256']==sha(__file__) and
            plan['planned_subject_main_invocations']==30 and plan['distinct_supplemental_references']==15 and
            plan['planned_native_commands']==31 and plan['automatic_retry'] is False,'Wrong supplemental plan')
    schedule = validate_coverage(plan['profiles'],plan['fixtures'])
    require([list(v) for v in schedule]==plan['case_schedule'] and kb.aliases(plan['profiles'])==plan['alias_pairs'],
            'Supplemental schedule or aliases differ')
    output = Path(plan['output']); require(not output.exists(),'Fresh supplemental output required; no automatic retry')
    pins = dict(plan['pins']); bind(args.plan,args.plan_sha256,pins)
    for path,digest in pins.items(): require(sha(path)==digest,'Preflight input changed: '+path)
    output.mkdir(parents=True)
    report = dict(schema='kotlin-specified-cases-results-v1',status='running',plan=str(args.plan.resolve()),plan_sha256=args.plan_sha256,
        bounded_report_sha256=plan['bounded_report_sha256'],pins=pins,started_at=datetime.now(timezone.utc).isoformat(),
        original_output_artifact_binding=plan['original_output_artifact_binding'],
        profiles=[],cases=[],alias_pairs=plan['alias_pairs'],active=None,native_launch_requests=0,native_processes_started=0,
        diagnostic_compiler_processes_started=0,supplemental_jvm_processes_started=0,native_process_ids=[],validated_command_artifacts={},
        qualified_supplemental_cases=0,observed_subject_main_invocations=0,observed_subject_main_returns=0,
        specified_case_coverage_qualified=False,original_qualified_cases=156,combined_planned_form_cases=186,
        combined_qualified_form_cases=156,
        subject_recompilations=0,benchmark_samples=0,source_work_qualified=False,subject_JIT_method_evidence_qualified=False,
        actual_subject_runtime_dependency_closure_qualified=False,canonical_loc=None,formatted_loc=None,
        full_timings_qualified=False,chart_admission=False)
    save(output/'report.json',report)
    def register(kind,directory,profile_id=None,label=None):
        report['native_launch_requests'] += 1
        report['active'] = dict(kind=kind,id=profile_id,case=label,receipt=str(directory/'process.json'),pid=None)
        save(output/'report.json',report)
        def started(pid):
            report['native_processes_started'] += 1
            report['diagnostic_compiler_processes_started' if kind=='diagnostic-compile' else 'supplemental_jvm_processes_started'] += 1
            report['native_process_ids'].append(dict(kind=kind,id=profile_id,case=label,pid=pid,pgid=pid))
            report['active']['pid'] = pid; save(output/'report.json',report)
        return started
    try:
        compiler = output/'diagnostic-compile'; compiler.mkdir()
        env = kb.kh.environment(plan['profiles'][0]['runtime_environment'],compiler)
        classes = output/'probe-classes'; classes.mkdir()
        source = compiler/'BoundedProbe.java'; source.write_bytes(Path(plan['probe_source']).read_bytes())
        require(sha(source)==pins[plan['probe_source']],'Diagnostic source changed during copy')
        command = [plan['javac']]+['-J'+f for f in FLAGS]+['-J-Duser.home='+str(compiler/'home'),
            '-J-Djava.io.tmpdir='+str(compiler/'tmp'),'--release','17','-proc:none','-d',str(classes),str(source)]
        receipt = kb.observe(command,env,compiler,b'',lock,register('diagnostic-compile',compiler),kind='diagnostic-compile')
        validate_receipt(receipt,'diagnostic-compile',compiler)
        generated = {str(p.relative_to(classes)) for p in classes.rglob('*') if p.is_file()}
        require(generated=={'boundedqualification/BoundedProbe.class','boundedqualification/BoundedProbe$SubjectLoader.class'} and
                not any(p.is_symlink() for p in classes.rglob('*')),'Unexpected diagnostic generated class set')
        for relative in generated:
            path = classes/relative; raw = path.read_bytes()
            require(raw[:4]==b'\xca\xfe\xba\xbe' and int.from_bytes(raw[6:8],'big')==61,'Wrong Java diagnostic target')
            pins[str(path)] = sha(path)
        report['validated_command_artifacts']['diagnostic-compile']=snapshot_command(compiler,'diagnostic-compile')
        report['active'] = None; save(output/'report.json',report)
        for row in plan['profiles']:
            for case in row['bounded_cases']:
                kb.kh.verify_lock(lock)
                require({str(p.relative_to(row['classes'])) for p in Path(row['classes']).rglob('*') if p.is_file()}==
                    {a['relative_path'] for a in row['class_artifacts']} and
                    not any(p.is_symlink() for p in Path(row['classes']).rglob('*')),'Retained class directory changed')
                hot = row['physical_inputs']+row['class_artifacts']+[case['expected']]+([case['stdin']] if case['stdin'] else [])
                for item in hot: require(sha(item['path'])==item['sha256'],'Active source/class/reference changed')
                for relative in generated: require(sha(classes/relative)==pins[str(classes/relative)],'Diagnostic class changed')
                directory = output/row['id']/case['case']; directory.mkdir(parents=True)
                env = kb.kh.environment(row['runtime_environment'],directory)
                payload = Path(case['stdin']['path']).read_bytes() if case['stdin'] else b''
                expected = Path(case['expected']['path']).read_bytes()
                (directory/'stdin.bin').write_bytes(payload); (directory/'expected.stdout').write_bytes(expected)
                (directory/'owners.txt').write_text('\n'.join(row['class_owner_names'])+'\n')
                options = FLAGS+['-Duser.home='+str(directory/'home'),'-Djava.io.tmpdir='+str(directory/'tmp'),
                    '-Xlog:class+load=info:file='+str(directory/'classes.log')+':uptime,tags',
                    '-Xlog:gc*=info:file='+str(directory/'gc.log')+':uptime,tags']
                command = [plan['java']]+options+['-cp',str(classes),'boundedqualification.BoundedProbe',row['classes'],
                    plan['stdlib'],str(directory/'owners.txt'),str(directory/'summary.json'),row['main_owner'],str(case['n'])]
                receipt = kb.observe(command,env,directory,payload,lock,register('bounded-main',directory,row['id'],case['case']))
                validate_receipt(receipt,'bounded-main',directory)
                summary = json.loads((directory/'summary.json').read_bytes())
                kb.validate_summary(summary,row,case,plan,classes,directory,options)
                loaded = kb.validate_log((directory/'classes.log').read_text(),Path(row['classes']),Path(plan['stdlib']),classes,set(row['class_owner_names']))
                require(row['main_owner'] in loaded,'Class log omits retained main')
                logged = {owner:source for owner,source in loaded.items() if owner.startswith(('clbg.','kotlin.'))}
                require(set(logged)==set(summary['non_platform_class_origins']) and
                    all(kb.uri_path(source)==kb.uri_path(summary['non_platform_class_origins'][owner]) for owner,source in logged.items()),
                    'JVM and loader origins differ')
                require('Using G1' in (directory/'gc.log').read_text(),'Missing original G1 runtime evidence')
                validation = kb.eb.output_validation(row['benchmark'],(directory/'stdout.bin').read_bytes(),expected)
                value = dict(status='specified-case-output-passed',id=row['id'],case=case['case'],n=case['n'],reference_evidence=case,
                    validation=validation,loaded_classes=loaded,main_invocations=1,main_returns=1,
                    exact_retained_main_and_helper_loaded=True,runtime_identity_observed=True,subject_recompilations=0,
                    benchmark_samples=0,source_work_qualified=False,full_timings_qualified=False,chart_admission=False)
                save(directory/'validated.json',value)
                report['validated_command_artifacts'][str(directory.relative_to(output))]=snapshot_command(directory,'bounded-main')
                report['cases'].append(dict(id=row['id'],case=case['case'],process=str(directory/'process.json'),process_sha256=sha(directory/'process.json'),
                    validated=str(directory/'validated.json'),validated_sha256=sha(directory/'validated.json'),status=value['status']))
                report['qualified_supplemental_cases'] += 1
                report['combined_qualified_form_cases'] = 156+report['qualified_supplemental_cases']
                report['active'] = None; save(output/'report.json',report)
            report['profiles'].append(row['id']); save(output/'report.json',report)
        require(report['supplemental_jvm_processes_started']==report['qualified_supplemental_cases']==30 and
            report['diagnostic_compiler_processes_started']==1 and report['native_launch_requests']==31 and
            len(report['profiles'])==20 and {(c['id'],c['case']) for c in report['cases']}==set(schedule),
            'Incomplete supplemental execution ledger')
        report.update(status=SUCCESS,specified_case_coverage_qualified=True)
    except BaseException as error:
        report.update(status='failed',specified_case_coverage_qualified=False,error=str(error) or type(error).__name__,error_type=type(error).__name__)
        raise
    finally:
        with atomic(): finalize(report,pins,output,lock)


def main():
    parser = argparse.ArgumentParser(description=__doc__); sub = parser.add_subparsers(dest='action',required=True)
    prep = sub.add_parser('prepare'); prep.add_argument('--bounded-report',type=Path,required=True)
    prep.add_argument('--bounded-report-sha256',required=True); prep.add_argument('--bounded-terminal-sha256',required=True)
    prep.add_argument('--plan',type=Path,required=True); prep.add_argument('--output',type=Path,required=True)
    run_parser = sub.add_parser('run'); run_parser.add_argument('--plan',type=Path,required=True); run_parser.add_argument('--plan-sha256',required=True)
    args = parser.parse_args()
    require(Path(sys.executable).resolve()==kb.kh.PYTHON.resolve() and sys.flags.isolated and sys.flags.no_site and
            sys.flags.dont_write_bytecode and not sys.flags.optimize,'Use retained Python with -I -S -B and no -O')
    def interrupted(signum,frame): raise KeyboardInterrupt('Kotlin supplement interrupted: '+str(signum))
    for sig in kb.kh.SIGNALS: signal.signal(sig,interrupted)
    with LOCK.open('rb') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB); kb.kh.verify_lock(lock)
        require(sha(kb.kh.PYTHON)==kb.kh.PYTHON_SHA,'Wrong controller interpreter bytes')
        if args.action=='prepare': prepare(args)
        else: run(args,lock)


if __name__=='__main__': main()
