"""Synthetic future full60 ledger faults and small saved qualification joins.

No actual prepared plan, new timing result, runtime launch or runtime hashing.
The in-memory cohort uses immutable source/count metadata and invented receipts.
"""
import copy
from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

HERE=Path(__file__).parent
audit=load('scala_reconciliation_under_test',HERE/'scala_reconcile.py')
base=load('scala_synthetic_receipt_templates',HERE/'test_prolog_reconcile.py')
SHA='1'*64
PLAN=str(audit.PACKET/'synthetic-plan-never-written.json')
DOCUMENTS={};SIZES={}
for name,(relative,digest) in {**audit.QUALIFICATION_REFS,**audit.CONTROL_REFS}.items():
    raw=(audit.ROOT/relative).read_bytes()
    assert audit.hashlib.sha256(raw).hexdigest()==digest
    DOCUMENTS[name]=audit.p.strict_json(raw);SIZES[name]=len(raw)


def plan_fixture():
    """Construct only in memory; every timing status and plan digest is synthetic."""
    d=DOCUMENTS;runtime=d['capture_plan']['compiled'];pins=dict(audit.SUPPORT_PINS)
    pins.update({str(audit.ROOT/path):sha for path,sha in audit.QUALIFICATION_REFS.values()})
    pins.update(dict(audit.CONTROL_REFS.values()))
    for name in ('compiled_report','bounded_plan','bounded_report','capture_plan','capture_report','parser_report'):
        pins.update(d[name]['pins'])
    pins.update(d['loc']['evidence_pins'])
    closures=[]
    for name in ('compiled','bounded','capture','parser'):
        directory=(audit.ROOT/audit.QUALIFICATION_REFS[name+'_report'][0]).parent
        artifacts=copy.deepcopy(d[name+'_terminal']['available_evidence'] if name in ('bounded','capture') else d[name+'_report']['artifacts'])
        for kind in ('report','terminal'):
            key=name+'_'+kind;artifacts[kind+'.json']=dict(bytes=SIZES[key],sha256=audit.QUALIFICATION_REFS[key][1])
        closures.append(dict(directory=str(directory),artifacts=artifacts))
    directory=(audit.ROOT/audit.QUALIFICATION_REFS['projection_review'][0]).parent
    artifacts=copy.deepcopy(d['projection_review']['artifacts'])
    artifacts['review.json']=dict(bytes=SIZES['projection_review'],sha256=audit.QUALIFICATION_REFS['projection_review'][1])
    closures.append(dict(directory=str(directory),artifacts=artifacts))
    for closure in closures:
        pins.update({str(Path(closure['directory'])/rel):v['sha256'] for rel,v in closure['artifacts'].items()})
    controller=str(audit.ROOT/'tools/qualification/scala_full.py');pins[controller]=audit.CONTROLLER_SHA
    plan=dict(schema='scala-qualified-retained-full60-v1',status='prepared-awaiting-independent-review',pins_verified=True,
        controller=controller,controller_sha256=audit.CONTROLLER_SHA,repository=str(audit.ROOT),
        output=str(audit.PACKET/'synthetic-output-never-created'),source_work_profiles=10,canonical_loc_profiles=10,
        formatted_loc_profiles=0,formatted_loc_qualified=False,retained_bounded_cases=149,samples=3,
        full_processes=60,scala_samples=30,matched_mech_samples=30,new_native_probes=0,compiler_invocations=0,
        fixture_reexecutions=0,bounded_reexecutions=0,count_replays=0,original_files_mutated=False,chart_admission=False,
        full_timings_qualified=False,no_automatic_retry=True,continuous_common_mutex=True,shared_timing_lock=str(audit.LOCK),
        common_mutex_inode=audit.p.LOCK_INODE,timing_policy=audit.TIMING_POLICY,
        qualified_work=dict(path=str(audit.ROOT/audit.QUALIFICATION_REFS['work'][0]),sha256=audit.WORK_SHA),
        qualified_source_counts=dict(path=str(audit.ROOT/audit.QUALIFICATION_REFS['loc'][0]),sha256=audit.LOC_SHA),
        pins=pins,prerequisite_artifact_closures=closures,manifests={},schedule=[])
    counts={row['id']:row for row in d['loc']['profiles']}
    sources={row['benchmark']:row for row in runtime['profiles']}
    for bi,bench in enumerate(audit.BENCHES):
        source=sources[bench];count=counts[source['id']];directory=Path(source['classes']).parent
        env=dict(PATH='/usr/bin:/bin',HOME=str(directory/'home'),TMPDIR=str(directory/'tmp')+'/',
                 JAVA_HOME=str(Path(runtime['java']).parent.parent),LC_ALL='C',LANG='C',TZ='UTC',CLASSPATH='')
        command=[runtime['java'],*audit.JVM_FLAGS,'-Duser.home='+env['HOME'],'-Djava.io.tmpdir='+env['TMPDIR'],
                 '-cp',source['runtime_classpath'],'Main']
        if bench not in ('regexredux','revcomp','knucleotide'):command.append('{n}')
        row=dict(id=source['id'],key=source['id'],benchmark=bench,variant='jvm-v1',language='scala',
            source=source['source'],source_sha256=source['source_sha256'],compiled_source=source['compiled_source'],
            binary=runtime['java'],binary_sha256=pins[runtime['java']],command=command,cwd=str(directory),runtime_environment=env,
            maximum_workers=8,classes=source['classes'],class_artifacts=copy.deepcopy(source['artifacts']),
            runtime_libraries=runtime['runtime_libraries'][:],main_owner='Main',source_alias_of=None,optimization_claim=False,
            source_work_qualified=True,canonical_loc_qualified=True,formatted_loc_qualified=False,formatted_loc=None,
            loc=count['canonical_loc'],canonical_loc=count['canonical_loc'],physical_loc=count['physical_loc'],
            physical_inputs=[dict(path=source['source'],sha256=source['source_sha256'],role='application',counted=True)],
            source_count_projection=dict(path=count['projection'],sha256=count['projection_sha256']),
            memory_policy='Retained -Xms64m -Xmx8g G1; ActiveProcessorCount=8; default tiered compilation',
            diagnostic_flags=[],runtime_policy_changes=[],chart_admission=False)
        name='control_mandel' if bench=='mandelbrot' else 'control_audit'
        origin=(next(v for v in d[name]['profiles'] if v['id']=='row16-aot-control') if bench=='mandelbrot'
                else next(v for v in d[name]['controls'] if v['benchmark']==bench))
        control={k:copy.deepcopy(origin[k]) for k in ('id','key','benchmark','language','source','source_sha256','binary',
                'binary_sha256','command','cwd','runtime_environment')}
        control.update(id='mech-aot-control',key=bench+':scala-full-study:mech-control',maximum_workers=8,loc=None,
            role='Fresh unchanged matched Mech AOT control',chart_admission=False,
            control_provenance=dict(path=audit.CONTROL_REFS[name][0],sha256=audit.CONTROL_REFS[name][1],original_id=origin['id']))
        for k in ('source','binary'):pins[origin[k]]=origin[k+'_sha256']
        pins.update(origin.get('support',{}))
        ids=[row['id'],control['id']]
        orders=[dict(round=i+1,profiles=ids[(i+bi)%2:]+ids[:(i+bi)%2]) for i in range(3)]
        manifest=dict(benchmark=bench,size=audit.SIZES[bench],samples=3,timeout_seconds=21600,supervisor_timeout_seconds=22200,
            maximum_rss_mib=10240,canonical_full_workload=True,chart_admission=False,no_automatic_retry=True,
            shared_timing_lock=str(audit.LOCK),retained_subject_compilation_outside_timer=True,runtime_and_class_loading_inside_timer=True,
            runtime_JIT_inside_timer=True,direct_main_invocations_per_sample=1,profiles=[row,control],orders=orders,
            full_output_reference=copy.deepcopy(audit.FULL_REFERENCES[bench]))
        plan['manifests'][bench]=manifest
        keys={v['id']:v['key'] for v in (row,control)}
        plan['schedule'].extend([bench,o['round'],identity,keys[identity]] for o in orders for identity in o['profiles'])
    for relative in ('knucleotide/.build/knucleotide-input25000000.txt','regexredux/.build/input5000000.txt',
                     'pidigits/inputs/output-full.txt','regexredux/inputs/output-full.txt'):
        path=str(audit.CLBG/relative);pins[path]=d['control_audit']['pins'][path]
    return plan


TEMPLATE_PLAN=plan_fixture()


def fingerprint(row):
    support={}
    def collect(value):
        if isinstance(value,dict):
            if value.get('path') and audit.p.digest(value.get('sha256')):support[value['path']]=value['sha256']
            for child in value.values():collect(child)
        elif isinstance(value,list):
            for child in value:collect(child)
    collect(row)
    return json.dumps(dict(source_sha256=row['source_sha256'],binary_sha256=row['binary_sha256'],
        command=[v.replace(row['source'],'{source}') for v in row['command']],cwd=row['cwd'],
        environment=row['runtime_environment'],support=support),sort_keys=True)


def fixture(failure=None,failure_round=1):
    old=base.fixture();plan=copy.deepcopy(TEMPLATE_PLAN);output=plan['output']
    report,terminal=copy.deepcopy(old['report']),copy.deepcopy(old['terminal'])
    report.update(schema='scala-full60-results-v1',plan=PLAN,plan_sha256=SHA,source_work_profiles=10,canonical_loc_profiles=10,
        formatted_loc_profiles=0,planned_scala_samples=30,planned_matched_mech_samples=30,full_timings_qualified=False,
        programs={},attempts=[],independent_supervisors=[],skipped_failed_profile_slots=[],isolated_failed_profiles=[])
    terminal.update(schema='scala-full60-terminal-v1',full_timings_qualified=False,prerequisite_pins=dict(plan['pins'],**{PLAN:SHA}),
        common_mutex_held_continuously=True,common_mutex_inode=audit.p.LOCK_INODE,available_evidence_pins={output+'/report.json':SHA})
    originals={v['key']:v for m in plan['manifests'].values() for v in m['profiles']}
    for key,row in originals.items():report['programs'][key]=dict(copy.deepcopy(row),attempts=[],samples_seconds=[],sample_validation=[])
    raw,supervised,outer,failed={},{},{},set()
    start=datetime(2026,10,14,tzinfo=timezone.utc)
    def at(seconds):return (start+timedelta(seconds=seconds)).isoformat()
    template=old['report']['attempts'][0];outer_template=next(iter(old['outer'].values()))
    for bench,round_number,identity,key in plan['schedule']:
        if key in failed:
            report['skipped_failed_profile_slots'].append(dict(benchmark=bench,round=round_number,id=identity,key=key));continue
        a=copy.deepcopy(template);i=len(report['attempts'])+1;row=originals[key];path=output+f'/attempts/{i:03d}-{identity}'
        command=[v.replace('{n}',str(audit.SIZES[bench])) for v in row['command']]
        ref=plan['manifests'][bench]['full_output_reference'] or dict(bytes=44,sha256=SHA)
        validation=dict(ref,reference_match=True)
        if bench=='nbody':validation.update(tolerance=1e-8,energies=[-0.169075164,-0.169059907])
        a.update(key=key,id=identity,benchmark=bench,language=row['language'],source_sha256=row['source_sha256'],command=command,
            cwd=row['cwd'],runtime_environment=copy.deepcopy(row['runtime_environment']),execution_fingerprint=fingerprint(row),
            started_at=at(i*20),finished_at=at(i*20+round_number),seconds=float(round_number),workload_n=audit.SIZES[bench],
            stdout_bytes=ref['bytes'],stdout_sha256=ref['sha256'],validation=validation,round=round_number,attempt=i,
            result_path=path+'.json',supervisor_result_path=path+'.supervisor.json',
            supervised_native_group=dict(type='native-group-started',pid=1000+i,pgid=1000+i,command=command,inherited_common_mutex=True))
        profile=report['programs'][key];profile['attempts'].append(i)
        if key==failure and round_number==failure_round:
            a.update(qualified=False,error='synthetic wrong output',error_type='OutputValidationError')
            for k in ('no_execution_error','complete_output_reference_match','complete_output_bytes_and_hash'):a['qualification_checks'][k]=False
            a['validation']['reference_match']=False;failed.add(key);report['isolated_failed_profiles'].append(key)
            profile.update(measurement_status='failed-full-workload',full_failure=copy.deepcopy(a))
        else:
            profile['samples_seconds'].append(a['seconds']);profile['sample_validation'].append(copy.deepcopy(validation))
        report['attempts'].append(a)
        raw[a['result_path']]={k:copy.deepcopy(v) for k,v in a.items() if k not in audit.p.SUPERVISOR_FIELDS}
        supervised[a['supervisor_result_path']]=copy.deepcopy(a)
        opath=output+f'/outer-supervisor/{i:03d}-{identity}.json';o=copy.deepcopy(outer_template)
        child=dict(pid=2000+i,ppid=99,pgid=98,status=2,birth_seconds=100,birth_microseconds=123)
        o.update(native_registrations=[copy.deepcopy(a['supervised_native_group'])],
            owned_sampler_children={str(2000+i):dict(identity=child,reaped=True)},
            owned_groups={str(2000+i):child,str(1000+i):dict(pid=1000+i,ppid=2000+i,pgid=1000+i,status=2,birth_seconds=101,birth_microseconds=456)})
        outer[opath]=o;report['independent_supervisors'].append(dict(path=opath,sha256=SHA,status='returned'))
        terminal['available_evidence_pins'].update({a['result_path']:SHA,a['supervisor_result_path']:SHA,opath:SHA})
    for key,row in report['programs'].items():
        control=row['benchmark']+':scala-full-study:mech-control'
        row.update(time_x_mech=None if key in failed or control in failed else 1.0,matched_mech_control=control,
            matched_mech_source_sha256=originals[control]['source_sha256'])
        if key not in failed:row.update(measurement_status='measured',median_seconds=2.0,sample_stdev_seconds=1.0)
    for item in (report,terminal):
        item.update(status='complete-with-unqualified-profiles' if failed else 'complete',saved_attempts=len(report['attempts']),
            full_performance_runs=len(report['attempts']),qualified_samples=sum(a['qualified'] for a in report['attempts']),
            registered_native_attempts=list(range(1,len(report['attempts'])+1)),
            validated_attempt_artifacts={p:s for p,s in terminal['available_evidence_pins'].items() if p!=output+'/report.json'})
    terminal['skipped_failed_profile_slots']=copy.deepcopy(report['skipped_failed_profile_slots'])
    durable=copy.deepcopy(old['durable']);command=[audit.p.PYTHON,'-I','-S','-B','-u',plan['controller'],'run','--plan',PLAN,'--plan-sha256',SHA]
    for name in ('request','launch','worker-started','command-started'):durable[name].update(command=command,cwd=str(audit.ROOT))
    listing='Wed Oct 14 00:00:01 2026 '+' '.join(command);report['supervisor']['process_listing']=listing
    for name in ('command-started','terminal'):durable[name]['command_identity']['listing']='99 98 '+listing
    return dict(plan=plan,report=report,terminal=terminal,raw=raw,supervised=supervised,outer=outer,durable=durable,plan_path=PLAN,plan_sha=SHA)


class Qualification(unittest.TestCase):
    def test_actual_saved_binding_metadata_only(self):
        result=audit.qualified_bindings(TEMPLATE_PLAN,DOCUMENTS,SIZES)
        self.assertEqual((result['qualified_sources'],result['canonical_counts'],result['bounded_cases']),(10,10,149))
        self.assertEqual(len(audit.schedule(TEMPLATE_PLAN)[0]),60)

    def test_self_consistent_unqualified_source_count_and_control_reject(self):
        for mutate in [lambda p:p['manifests']['nbody']['profiles'][0].update(canonical_loc=1,loc=1),
                lambda p:p['manifests']['nbody']['profiles'][0].update(binary='/different/java'),
                lambda p:p['manifests']['nbody']['profiles'][1]['command'].append('extra'),
                lambda p:p['manifests']['nbody']['profiles'][0]['class_artifacts'][0].update(sha256='0'*64)]:
            plan=copy.deepcopy(TEMPLATE_PLAN);mutate(plan)
            with self.assertRaises(ValueError):audit.qualified_bindings(plan,DOCUMENTS,SIZES)

    def test_omitted_inherited_pin_and_closed_artifact_reject(self):
        plan=copy.deepcopy(TEMPLATE_PLAN)
        inherited=next(iter(DOCUMENTS['parser_report']['pins']));plan['pins'].pop(inherited)
        with self.assertRaisesRegex(ValueError,'pin omitted'):audit.qualified_bindings(plan,DOCUMENTS,SIZES)
        plan=copy.deepcopy(TEMPLATE_PLAN);plan['prerequisite_artifact_closures'][0]['artifacts'].popitem()
        with self.assertRaisesRegex(ValueError,'inventory differs'):audit.qualified_bindings(plan,DOCUMENTS,SIZES)

    def test_pending_work_counts_or_native_output_decision_reject(self):
        for mutate in [lambda d:d['work'].update(source_work_qualified=False),
                lambda d:d['loc'].update(canonical_LOC_admitted=False),
                lambda d:d['pi_peer'].update(both_division_calls_dominate_comparison=False),
                lambda d:d['bounded_review'].update(all_native_children_reaped=False)]:
            d=copy.deepcopy(DOCUMENTS);mutate(d)
            with self.assertRaises(ValueError):audit.qualified_bindings(TEMPLATE_PLAN,d,SIZES)


class Ledger(unittest.TestCase):
    def test_full60_is_not_publication(self):
        result=audit.reconcile(**fixture())
        self.assertEqual((result['actual_full_native_processes'],result['actual_scala_processes'],result['actual_matched_mech_processes']),(60,30,30))
        self.assertEqual(result['qualified_samples'],60)
        self.assertFalse(result['chart_admission']);self.assertFalse(result['file_integrity_verified'])
        self.assertFalse(result['full_timings_qualified'])

    def test_failures_in_every_round_preserve_successes_without_partial_median(self):
        key='scala-revcomp-jvm-v1'
        for round_number in (1,2,3):
            result=audit.reconcile(**fixture(key,round_number))
            self.assertEqual(result['actual_full_native_processes'],57+round_number)
            self.assertEqual(len(result['profiles'][key]['samples_seconds']),round_number-1)
            self.assertIsNone(result['profiles'][key]['median_seconds'])
            self.assertIsNone(result['profiles'][key]['time_x_mech'])
        value=fixture(key,2);value['report']['programs'][key]['median_seconds']=1.0
        with self.assertRaisesRegex(ValueError,'partial timings'):audit.reconcile(**value)

    def test_failed_control_retains_scala_samples_without_ratio(self):
        result=audit.reconcile(**fixture('revcomp:scala-full-study:mech-control'))
        row=result['profiles']['scala-revcomp-jvm-v1']
        self.assertEqual(len(row['samples_seconds']),3);self.assertTrue(row['full_workload_qualified']);self.assertIsNone(row['time_x_mech'])

    def test_changed_schedule_runtime_source_policy_or_reference_reject(self):
        for mutate in [lambda p:p['schedule'].reverse(),lambda p:p.update(pins_verified=False),
                lambda p:p['manifests']['nbody']['profiles'][0]['runtime_environment'].update(JAVA_TOOL_OPTIONS='-Xint'),
                lambda p:p['manifests']['nbody']['profiles'][0].update(formatted_loc=2),
                lambda p:p['manifests']['fasta']['full_output_reference'].update(sha256='0'*64),
                lambda p:p.update(timing_policy='kernel only'),lambda p:p['pins'].pop(audit.p.PYTHON),
                lambda p:p['manifests']['nbody']['profiles'][0].update(source_alias_of='another')]:
            value=fixture();mutate(value['plan'])
            with self.assertRaises((ValueError,KeyError)):audit.reconcile(**value)

    def test_missing_duplicate_or_orphan_attempts_reject(self):
        for mutate in [lambda v:v['report']['attempts'].pop(),lambda v:v['report']['attempts'][1].update(attempt=1),
                lambda v:v['terminal']['available_evidence_pins'].update({'/orphan':'0'*64}),
                lambda v:v['report']['validated_attempt_artifacts'].popitem()]:
            value=fixture();mutate(value)
            with self.assertRaises(ValueError):audit.reconcile(**value)

    def test_exact_durable_argv_parent_birth_cwd_and_exit(self):
        for mutate in [lambda v:v['durable']['request']['command'].remove('-u'),
                lambda v:v['durable']['worker-started'].update(cwd='/elsewhere'),
                lambda v:v['durable']['terminal'].update(exit_code=1),
                lambda v:v['durable']['terminal']['command_identity'].update(listing='99 999 '+v['report']['supervisor']['process_listing']),
                lambda v:v['report']['supervisor'].update(process_listing=v['report']['supervisor']['process_listing'].replace('00:00:01','00:00:02'))]:
            value=fixture();mutate(value)
            with self.assertRaises(ValueError):audit.reconcile(**value)

    def test_ownership_cleanup_output_and_raw_receipt_mutations_reject(self):
        for mutate in [lambda v:next(iter(v['outer'].values()))['cleanup_errors'].append('alive'),
                lambda v:next(iter(v['outer'].values()))['owned_sampler_children']['2001']['identity'].update(ppid=999),
                lambda v:next(iter(v['raw'].values())).update(stdout_sha256='0'*64),
                lambda v:next(iter(v['supervised'].values())).update(seconds=0.01)]:
            value=fixture();mutate(value)
            with self.assertRaises(ValueError):audit.reconcile(**value)

    def test_consistent_overlap_and_invalid_numbers_reject(self):
        value=fixture();a=value['report']['attempts'][1];a['started_at']=value['report']['attempts'][0]['started_at']
        value['raw'][a['result_path']]={k:copy.deepcopy(v) for k,v in a.items() if k not in audit.p.SUPERVISOR_FIELDS}
        value['supervised'][a['supervisor_result_path']]=copy.deepcopy(a)
        with self.assertRaisesRegex(ValueError,'overlap'):audit.reconcile(**value)
        for field,number in [('median_seconds',float('nan')),('sample_stdev_seconds',-1e-13),('time_x_mech',True)]:
            value=fixture();next(iter(value['report']['programs'].values()))[field]=number
            with self.assertRaises(ValueError):audit.reconcile(**value)


class Closure(unittest.TestCase):
    def test_callback_runs_after_final_check_before_lease_release(self):
        events=[]
        @contextmanager
        def lease():
            events.append('held')
            try:yield
            finally:events.append('released')
        def check():
            self.assertNotIn('released',events);events.append('check')
        def consumer():events.append('consumer');raise ValueError('late consumer pin')
        def restore():self.assertNotIn('released',events);events.append('restored')
        with self.assertRaisesRegex(ValueError,'late consumer'),lease():
            with audit._yield_verified({},check,restore,consumer):events.append('body')
        self.assertEqual(events,['held','check','body','check','consumer','restored','released'])

    def test_body_error_still_checks_and_dual_failure_survives(self):
        events=[]
        with self.assertRaisesRegex(RuntimeError,'body'):
            with audit._yield_verified({},lambda:events.append('check'),None):raise RuntimeError('body')
        self.assertEqual(events,['check','check'])
        def check():
            events.append('check')
            if len(events)==4:raise ValueError('closure')
        def restore():raise OSError('restoration')
        with self.assertRaises(BaseExceptionGroup) as caught:
            with audit._yield_verified({},check,restore):pass
        self.assertEqual([str(e) for e in caught.exception.exceptions],['closure','restoration'])

    def test_cli_removes_only_owned_receipt_after_failed_exit(self):
        events=[]
        @contextmanager
        def context(*args,on_exit_failure,**kwargs):
            events.append('held')
            try:
                yield {'status':'synthetic'}
                self.assertTrue(output.exists());on_exit_failure();events.append('removed');raise ValueError('late change')
            finally:events.append('released')
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'review.json'
            with mock.patch.object(audit,'review_files',context),self.assertRaisesRegex(ValueError,'late change'):
                audit.save_review_result(output,'plan',SHA,'job')
            self.assertFalse(output.exists())
        self.assertEqual(events,['held','removed','released'])

    def test_cli_cannot_return_success_after_result_mutation_or_replacement(self):
        for replace in (False,True):
            @contextmanager
            def context(*args,on_exit_failure,final_consumer_check):
                def check():
                    if output.exists():
                        if replace:
                            output.rename(output.with_suffix('.original'))
                            output.write_bytes(b'independent replacement')
                        else:output.write_bytes(b'independent same-inode edit')
                with audit._yield_verified({'status':'synthetic'},check,on_exit_failure,final_consumer_check) as result:
                    yield result
            with tempfile.TemporaryDirectory() as directory:
                output=Path(directory)/'review.json'
                with mock.patch.object(audit,'review_files',context),self.assertRaises(BaseExceptionGroup):
                    audit.save_review_result(output,'plan',SHA,'job')
                self.assertEqual(output.read_bytes(),b'independent replacement' if replace else b'independent same-inode edit')

    def test_inventory_retains_nested_terminal_and_rejects_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'nested').mkdir();(root/'nested/terminal.json').write_bytes(b'{}')
            self.assertEqual(audit.inventory(root),{str(root/'nested/terminal.json')})
            (root/'alias').symlink_to(root/'nested')
            with self.assertRaises(ValueError):audit.inventory(root)


if __name__=='__main__':unittest.main()
