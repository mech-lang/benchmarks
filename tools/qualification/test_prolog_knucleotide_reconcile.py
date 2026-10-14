"""Small saved-prefix replay and synthetic future36 faults; no full pin replay.

The actual fourteen completed receipt trios and interrupted trio are retained.
Future timing records exist only in memory and never become evidence files.
"""
import copy
from contextlib import contextmanager
from datetime import datetime,timedelta,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('tested_knucleotide36_reconcile',HERE/'prolog_knucleotide_reconcile.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
c=a
SHA='1'*64
def read(path):return json.loads(path.read_bytes())

def lightweight_saved_fixture():
    """Replay actual small receipts with a reduced, explicitly synthetic pin map.

    No original multi-megabyte plan/terminal or runtime closure is read. The
    native verifier receives exact saved source/fingerprint bindings instead.
    Actual full prerequisite closure remains prepare/run work under leases.
    """
    report = read(c.PREVIOUS/'run-v1/report.json')
    before = read(c.STOP/'before-report.json'); request = read(c.STOP/'request.json')
    closure = read(c.STOP/'closure.json')
    durable = {name: read(c.PREVIOUS_JOB/(name+'.json')) for name in
               ('request', 'launch', 'worker-started', 'command-started', 'terminal')}
    aggregates = c.r.AGGREGATE | {'retained_attempts'}
    manifests, pins = {}, {}
    for bench in list(c.r.BENCHES):
        rows = [{k: copy.deepcopy(v) for k, v in row.items() if k not in aggregates}
                for row in report['programs'].values() if row['benchmark'] == bench]
        rows.sort(key=lambda row: 2 if row['language'] == 'mech' else 0 if row['variant'] == 'compact' else 1)
        ids = [row['id'] for row in rows]
        saved = next((a for a in report['attempts'][:14] if a['benchmark'] == bench), None)
        reference = dict(bytes=saved['stdout_bytes'], sha256=saved['stdout_sha256']) if saved else None
        manifests[bench] = dict(profiles=rows, orders=[dict(round=i+1, profiles=ids[i:]+ids[:i]) for i in range(3)],
            size=c.r.SIZES[bench], full_output_reference=reference)
    for attempt in report['attempts'][:14]:
        row = next(row for row in manifests[attempt['benchmark']]['profiles'] if row['key'] == attempt['key'])
        pins[row['source']] = row['source_sha256']; pins[row['binary']] = row['binary_sha256']
        for path, digest in json.loads(attempt['execution_fingerprint'])['support'].items():
            path = str(Path(path) if Path(path).is_absolute() else c.p.HOST_CLBG/Path(path))
            pins[os.path.normpath(path)] = digest
    slots=[]
    for bench in c.r.BENCHES:
        manifest=manifests[bench];keys={row['id']:row['key'] for row in manifest['profiles']}
        slots.extend([bench,order['round'],name,keys[name]] for order in manifest['orders'] for name in order['profiles'])
    retained = dict(reused_samples=copy.deepcopy(report['reused_samples']), completed_benchmarks=list(c.r.BENCHES)[:4])
    plan = dict(manifests=manifests, schedule=slots, retained_slots=slots[:40], remaining_slots=slots[40:],
        full_processes=50, retained_qualified_samples=40, new_prolog_processes=33, new_mech_processes=17,
        retained=retained, pins=pins, historical_pins={})
    artifacts = {path: read(Path(path)) for path in report['validated_attempt_artifacts']}
    cancelled = report['attempts'][-1]
    raw, _, outer = c.attempt_paths(c.PREVIOUS/'run-v1', cancelled)
    for path in (raw, raw.with_suffix('.wrapper.json'), outer): artifacts[str(path)] = read(path)
    inventory = dict(closure['completed_artifacts_unchanged'])
    for path in (raw, raw.with_suffix('.wrapper.json'), outer, c.PREVIOUS/'run-v1/error.log', c.PREVIOUS/'run-v1/report.json'):
        inventory[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    terminal = {name: copy.deepcopy(report[name]) for name in ('status', 'qualified_samples', 'retained_qualified_samples',
        'saved_attempts', 'full_performance_runs', 'common_mutex_held_continuously', 'full_timings_qualified',
        'chart_admission', 'registered_native_attempts', 'native_launch_unconfirmed_attempts', 'skipped_failed_profile_slots')}
    terminal.update(schema='prolog-linear-remaining50-terminal-v1', integrity_errors=[],
        report=str(c.PREVIOUS/'run-v1/report.json'), report_sha256=closure['controller_report_sha256'],
        prerequisite_pins=c.merge(pins, {str(c.PREVIOUS/'plan-v1.json'): c.PREVIOUS_PLAN_SHA}),
        common_mutex_held=True, common_mutex_inode=79859134, original_files_mutated=False,
        new_qualified_samples=14, available_evidence_pins=inventory)
    closure['prerequisite_pins_verified'] = len(terminal['prerequisite_pins'])
    return dict(plan=plan, before=before, report=report, terminal=terminal, durable=durable,
                request=request, closure=closure, artifacts=artifacts)


def replacement(plan):
    old = plan['manifests']['knucleotide']['profiles'][:2]
    q = dict(schema='prolog-knucleotide-linear-qualified-v1',
        status='qualified-source-work-and-canonical-counts-awaiting-full-timing', bounded_outputs_qualified=True,
        compiled_inputs_qualified=True, source_work_qualified=True, canonical_LOC_admitted=True,
        full_timings_qualified=False, chart_admission=False, pins=dict(c.SOURCES), evidence={},
        artifact_inventories={}, profiles=[])
    # These are synthetic bindings; no successful qualification file is written.
    for name in ('compilation', 'bounded', 'source_counts', 'required_work'):
        path = str(c.SOURCE/'synthetic'/f'{name}.json'); q['pins'][path] = 'a'*64
        q['evidence'][name] = dict(path=path, sha256='a'*64)
    q['artifact_inventories'][str(c.SOURCE/'synthetic')] = {name+'.json': 'a'*64 for name in q['evidence']}
    for index, original in enumerate(old):
        row = copy.deepcopy(original); origin = str(c.SOURCE/'sources/knucleotide'/('compact.pl' if not index else 'optimized.pl'))
        base = c.SOURCE/'synthetic/input'
        bundle = [dict(path=str(base/'sources/knucleotide/compact.pl'), origin=origin, sha256=c.SOURCE_SHA,
                       normalized_loc=101, physical_loc=81)]
        for name in ('clbg_io.pl', 'clbg_records.pl'):
            source = str(c.SOURCE/'support'/name)
            bundle.append(dict(path=str(base/'support'/name), origin=source, sha256=c.SOURCES[source],
                               normalized_loc=21, physical_loc=11))
        for entry in bundle:
            q['pins'][entry['path']] = entry['sha256']; q['pins'][str(Path(entry['path']).with_suffix('.qlf'))] = 'b'*64
        qlf = str(base/'sources/knucleotide/compact.qlf')
        extra = dict(path=str(c.SOURCE/'synthetic/loaded.json'), sha256='c'*64)
        q['pins'][extra['path']] = extra['sha256']; q['pins'][row['binary']] = row['binary_sha256']
        row.update(source=origin, source_sha256=c.SOURCE_SHA, measured_source=bundle[0]['path'], source_bundle=bundle,
            command=[row['binary'], '-q', '-O', '-f', 'none', '--stack-limit=8g', '-l', str(base/'support/clbg_io.qlf'),
                     '-l', str(base/'support/clbg_records.qlf'), '-s', qlf, '-g', 'clbg_io:run(clbg_knucleotide:main)'],
            cwd=str(base), compiled_artifact=dict(path=qlf, sha256='b'*64, bytes=123),
            compiler_bound_input_inventory=dict(extra, status='qualified-exact-authored-compiler-inputs'),
            required_work_review=dict(q['evidence']['required_work'], status='passed'),
            source_count_review=copy.deepcopy(q['evidence']['source_counts']), canonical_source_projection=extra,
            loc=143, canonical_loc=143, physical_loc=103, formatted_loc=None,
            source_alias_of=old[0]['id'] if index else None,
            optimization_claim='explicit equivalent-source alias; no distinct optimization admitted' if index else 'one conversion')
        q['profiles'].append(row)
    return q


def support(row):
    found={}
    def visit(value):
        if isinstance(value,dict):
            if value.get('path') and a.p.digest(value.get('sha256')):found[value['path']]=value['sha256']
            for key,child in value.items():
                if key in ('pins','libraries','pin_files','support_pins') and isinstance(child,dict):
                    found.update({name:digest for name,digest in child.items() if a.p.digest(digest)})
                visit(child)
        elif isinstance(value,list):
            for child in value:visit(child)
    visit(row);return found

def future(saved,failure=None,failure_round=1):
    stopped=copy.deepcopy(saved);retained=a.stopped_prefix(**stopped)
    plan=copy.deepcopy(stopped['plan']);qualification=replacement(plan)
    plan['manifests']['knucleotide']['profiles'][:2]=copy.deepcopy(qualification['profiles'])
    plan.update(output=str(a.PACKET/'run-v1'),retained=retained,retained_slots=plan['schedule'][:54],
        remaining_slots=plan['schedule'][54:],knucleotide_qualification=qualification,linear_qualification={},
        qualification=dict(path=str(a.QUALIFICATION),sha256=a.QUALIFICATION_SHA))
    plan['pins'].update(qualification['pins'])
    for manifest in plan['manifests'].values():
        if manifest['profiles'][0]['benchmark']!='nbody' and manifest['full_output_reference'] is None:
            manifest['full_output_reference']=dict(bytes=26,sha256=SHA)
        for row in manifest['profiles']:
            plan['pins'][row['source']]=row['source_sha256'];plan['pins'][row['binary']]=row['binary_sha256']
            for path,digest in support(row).items():
                path=str(Path(path) if Path(path).is_absolute() else a.p.HOST_CLBG/Path(path))
                plan['pins'][os.path.normpath(path)]=digest
    def observation(sample):
        bench,round_,identity,key=sample['slot']
        return dict(benchmark=bench,round=round_,id=identity,key=key,attempt=sample['original_attempt'],
            result_path=sample['raw'],qualified=True,seconds=sample['seconds'],validation=sample['validation'])
    old_attempts=[observation(s) for s in retained['reused_samples'][:9]]
    original=dict(report=dict(attempts=old_attempts),plan=dict(sealed_source_outcome=dict(path='/synthetic/outcome',sha256=SHA)))
    prior=dict(report=dict(attempts=[observation(s) for s in retained['reused_samples'][9:40]]))
    old_raw={};old_supervised={};old_outer={}
    start=datetime(2027,1,1,tzinfo=timezone.utc)
    def at(seconds):return (start+timedelta(seconds=seconds)).isoformat()
    parent=66708;worker_pid=66704
    command=[a.p.PYTHON,'-I','-S','-B',str(a.CONTROLLER),'run','--plan',str(a.PLAN),'--plan-sha256',a.PLAN_SHA]
    parent_listing='66708 66704 Fri Jan 1 00:00:00 2027 '+' '.join(command)
    parent_identity=dict(pid=parent,listing=parent_listing)
    worker_identity=dict(pid=worker_pid,listing='66704 1 Fri Jan 1 00:00:00 2027 /synthetic/worker.py')
    durable=dict(request=dict(command=command,cwd=str(a.ROOT),schema_version=1,common_mutex_owned_by_target_command=True,
            automatic_retry=False,qualification_granted=False,created_at=at(-3)),
        launch=dict(command=command,cwd=str(a.ROOT),automatic_retry=False,qualification_granted=False,worker_identity=worker_identity),
        terminal=dict(status='command-exited-zero-awaiting-report-review',exit_code=0,actual_command_started=True,
            command_identity_observation_missing=False,stop_signals=[],command_identity=parent_identity,
            worker_identity=worker_identity,command_pid=parent,finished_at=at(2001),automatic_retry=False,qualification_granted=False))
    durable['worker-started']=dict(command=command,cwd=str(a.ROOT),qualification_granted=False,inherited_private_lease=True,
        detached_session=True,common_mutex_owned_by_target_command=True,worker_identity=worker_identity,started_at=at(-2))
    durable['command-started']=dict(command=command,cwd=str(a.ROOT),command_identity_observation_missing=False,
        command_identity=parent_identity,command_pid=parent,started_at=at(-1))
    report=dict(schema=a.PRODUCER_SCHEMA,status='complete',active=None,plan=str(a.PLAN),plan_sha256=a.PLAN_SHA,
        supervisor=dict(pid=parent,process_listing='Fri Jan 1 00:00:00 2027 '+' '.join(command)),
        pins_unchanged_at_end=True,common_mutex_held_continuously=True,full_timings_qualified=False,chart_admission=False,
        native_launch_unconfirmed_attempts=[],reused_samples=copy.deepcopy(plan['retained']['reused_samples']),
        benchmark_order=list(a.r.BENCHES),completed_benchmarks=list(a.r.BENCHES),shared_timing_lock=str(a.r.LOCK),
        no_automatic_retry=True,sample_count=3,source_work_profiles=20,canonical_loc_profiles=20,retained_qualified_samples=54,
        repeated_completed_samples=0,programs={},attempts=[],independent_supervisors=[],validated_attempt_artifacts={},
        isolated_failed_profiles=[],skipped_failed_profile_slots=[],descriptive_provenance=[],kernel_identity_observation_gaps=[],
        started_at=at(0),finished_at=at(2000))
    terminal=dict(schema='prolog-knucleotide-remaining36-terminal-v1',status='complete',report=plan['output']+'/report.json',
        report_sha256=SHA,integrity_errors=[],common_mutex_held_continuously=True,full_timings_qualified=False,chart_admission=False,
        native_launch_unconfirmed_attempts=[],common_mutex_held=True,common_mutex_inode=79859134,
        compiler_invocations=0,fixture_reexecutions=0,bounded_reexecutions=0,count_replays=0,repeated_completed_samples=0,
        original_files_mutated=False,retained_qualified_samples=54,prerequisite_pins=dict(plan['pins'],**{str(a.PLAN):a.PLAN_SHA}),
        available_evidence_pins={plan['output']+'/report.json':SHA})
    rows={row['key']:row for manifest in plan['manifests'].values() for row in manifest['profiles']}
    grouped={key:[] for key in rows}
    for x in old_attempts+prior['report']['attempts']+stopped['report']['attempts'][:14]:grouped[x['key']].append(x)
    failed=set();raw={};supervised={};outer={}
    for bench,round_,identity,key in plan['remaining_slots']:
        if key in failed:
            report['skipped_failed_profile_slots'].append(dict(benchmark=bench,round=round_,id=identity,key=key));continue
        index=len(report['attempts'])+1;row=rows[key];manifest=plan['manifests'][bench]
        command=[part.replace('{n}',str(manifest['size'])) for part in row['command']]
        reference=manifest['full_output_reference'] or dict(bytes=26,sha256=SHA)
        validation=dict(reference,reference_match=True)
        if bench=='nbody':validation.update(tolerance=1e-8,energies=[-0.169075164,-0.169059907])
        path=plan['output']+'/attempts/'+f'{index:03d}-{identity}'
        native=dict(type='native-group-started',pid=1000+index,pgid=1000+index,command=command,inherited_common_mutex=True)
        x=dict(key=key,id=identity,benchmark=bench,language=row['language'],source_sha256=row['source_sha256'],command=command,
            cwd=row['cwd'],runtime_environment=row['runtime_environment'],
            execution_fingerprint=json.dumps(dict(source_sha256=row['source_sha256'],binary_sha256=row['binary_sha256'],
                command=[part.replace(row['source'],'{source}') for part in row['command']],cwd=row['cwd'],
                environment=row['runtime_environment'],support=support(row))),
            started_at=at(index*20),finished_at=at(index*20+round_),seconds=float(round_),exit_status=0,
            workload_n=manifest['size'],full_workload=True,timeout_seconds=21600,maximum_rss_mib=10240,
            power_at_start=a.r.POWER,power_at_end=a.r.POWER,valid_environment=True,pins_unchanged_at_end=True,
            peak_process_group_rss_kib=100,resource_violation=None,stderr='',stdout_bytes=reference['bytes'],
            stdout_sha256=reference['sha256'],validation=validation,round=round_,attempt=index,sampler_wait_status=0,
            result_path=path+'.json',supervisor_result_path=path+'.supervisor.json',qualified=True,
            supervised_native_group=native,qualification_checks={key:True for key in a.p.CHECKS},
            **{name:[] for name in a.p.EMPTY_LIST_FIELDS})
        if key==failure and round_==failure_round:
            x.update(qualified=False,error='synthetic wrong output',error_type='OutputValidationError')
            for gate in ('no_execution_error','complete_output_reference_match','complete_output_bytes_and_hash'):
                x['qualification_checks'][gate]=False
            x['validation']['reference_match']=False;failed.add(key);report['isolated_failed_profiles'].append(key)
        report['attempts'].append(x);grouped[key].append(x)
        raw[x['result_path']]={k:copy.deepcopy(v) for k,v in x.items() if k not in a.p.SUPERVISOR_FIELDS}
        supervised[x['supervisor_result_path']]=copy.deepcopy(x)
        out=plan['output']+'/outer-supervisor/'+f'{index:03d}-{identity}.json';child=2000+index
        child_identity=dict(pid=child,ppid=parent,pgid=parent,status=2,birth_seconds=100,birth_microseconds=123)
        outer[out]=dict(status='returned',deadline_seconds=22200,native_timeout_seconds=21600,common_mutex_fd=5,
            common_mutex_held_through_cleanup=True,native_execute_unchanged=True,native_validation_unchanged=True,
            deadline_expired=False,cleanup_errors=[],signals=[],native_registrations=[copy.deepcopy(native)],
            owned_sampler_children={str(child):dict(identity=child_identity,reaped=True)},
            owned_groups={str(child):child_identity,str(native['pid']):dict(pid=native['pid'],ppid=child,pgid=native['pid'],
                status=2,birth_seconds=101,birth_microseconds=456)})
        report['independent_supervisors'].append(dict(path=out,sha256=SHA,status='returned'))
        for name in (x['result_path'],x['supervisor_result_path'],out):
            report['validated_attempt_artifacts'][name]=terminal['available_evidence_pins'][name]=SHA
    for key,row in rows.items():
        observed=grouped[key];good=[x for x in observed if x['qualified']]
        retained=[s for s in plan['retained']['reused_samples'] if s['slot'][3]==key]
        dest=dict(copy.deepcopy(row),samples_seconds=[x['seconds'] for x in good],sample_validation=[x['validation'] for x in good],
            attempts=[x['attempt'] for x in report['attempts'] if x['key']==key],
            retained_attempts=[dict(cohort=s['cohort'],attempt=s['original_attempt'],report=s['original_report'],
                report_sha256=s['original_report_sha256']) for s in retained])
        if key in failed:dest.update(measurement_status='failed-full-workload',full_failure=copy.deepcopy(observed[-1]))
        else:
            median,sd=a.p.three_statistics(dest['samples_seconds'])
            dest.update(measurement_status='measured',median_seconds=median,sample_stdev_seconds=sd)
        report['programs'][key]=dest
    for key,row in report['programs'].items():
        control=report['programs'][row['benchmark']+':prolog-full-study:mech-control']
        row.update(matched_mech_control=control['key'],matched_mech_source_sha256=control['source_sha256'],
            time_x_mech=None if key in failed or control['key'] in failed else row['median_seconds']/control['median_seconds'])
    count=len(report['attempts']);qualified=sum(x['qualified'] for x in report['attempts'])+54
    for item in (report,terminal):
        item.update(status='complete-with-unqualified-profiles' if failed else 'complete',saved_attempts=count,
            full_performance_runs=count,qualified_samples=qualified,registered_native_attempts=list(range(1,count+1)))
    terminal.update(new_qualified_samples=qualified-54,skipped_failed_profile_slots=report['skipped_failed_profile_slots'])
    # The source metadata contains retained descriptive provenance that the
    # frozen receipt checks report even though it is not an executed dependency.
    physical=dict(plan['historical_pins']);physical.update(terminal['prerequisite_pins'])
    for x in report['attempts']:report['descriptive_provenance'].extend(a.p.check_fingerprint(x,rows[x['key']],physical))
    return dict(plan=plan,stopped=stopped,prior=prior,original=original,prior_artifacts={},stopped_artifacts={},report=report,terminal=terminal,durable=durable,raw=raw,supervised=supervised,
                outer=outer,old_raw=old_raw,old_supervised=old_supervised,old_outer=old_outer)


class SavedPrefix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.saved=lightweight_saved_fixture()
    def test_actual14_and_interrupted_attempt_preserved(self):
        result=a.stopped_prefix(**copy.deepcopy(self.saved))
        self.assertEqual(len(result['reused_samples']),54)
        self.assertEqual(sum(s['cohort']=='linear-remaining50' for s in result['reused_samples']),14)
        self.assertEqual(result['excluded_attempts'][0]['attempt'],15)
        self.assertNotIn('knucleotide',{s['slot'][0] for s in result['reused_samples']})
    def test_stopped_status_or_cancelled_attempt_cannot_be_promoted(self):
        for change in (lambda v:v['report'].update(status='complete'),
            lambda v:v['report']['attempts'][14].update(qualified=True),
            lambda v:v['durable']['terminal'].update(stop_signals=[]),
            lambda v:v['closure'].update(deadline_expired=True),
            lambda v:v['report'].update(qualified_samples=55)):
            value=copy.deepcopy(self.saved);change(value)
            with self.assertRaises((ValueError,AssertionError)):a.stopped_prefix(**value)
    def test_retained_raw_or_snapshot_mutation_rejected(self):
        for fault in ('raw','snapshot','missing'):
            value=copy.deepcopy(self.saved);path=next(iter(value['report']['validated_attempt_artifacts']))
            if fault=='raw':value['artifacts'][path]['source_sha256']='0'*64
            elif fault=='snapshot':value['closure']['completed_artifacts_unchanged'][path]='0'*64
            else:value['artifacts'].pop(path)
            with self.assertRaises((ValueError,AssertionError,KeyError)):a.stopped_prefix(**value)
    def test_cancelled_owner_cleanup_failure_not_a_sample(self):
        value=copy.deepcopy(self.saved);attempt=value['report']['attempts'][-1]
        path=str(a.attempt_paths(a.PREVIOUS/'run-v1',attempt)[2])
        value['artifacts'][path]['cleanup_errors']=['group survives']
        with self.assertRaises(ValueError):a.stopped_prefix(**value)


class FutureLedger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.saved=lightweight_saved_fixture()
    def check(self,value):
        # Older40 are validated by frozen independent helpers in the real path;
        # these future-ledger cases isolate the new36 checks after that boundary.
        grouped={}
        for cohort in ('original','prior','stopped'):
            attempts=value[cohort]['report']['attempts'][:14] if cohort=='stopped' else value[cohort]['report']['attempts']
            for attempt in attempts:grouped.setdefault(attempt['key'],[]).append(copy.deepcopy(attempt))
        profiles={row['key']:row for manifest in value['plan']['manifests'].values() for row in manifest['profiles']}
        context=(value['plan']['schedule'],profiles,grouped,[],[],a.p.timestamp(self.saved['report']['finished_at']))
        with patch.object(a,'retained_context',return_value=context):return a.reconcile(**value)
    def test_exact_four_cohorts_54plus36_and_corrected_knucleotide(self):
        result=self.check(future(self.saved))
        self.assertEqual((result['reused_qualified_samples'],result['new_full_native_processes'],result['qualified_samples']),(54,36,90))
        self.assertEqual(result['total_native_processes_including_cancelled'],92)
        origins=[s for row in result['profiles'].values() for s in row['sample_evidence']]
        self.assertEqual({name:sum(s['cohort']==name for s in origins) for name in
            ('original-full90','linear-full81','linear-remaining50','knucleotide-remaining36')},
            {'original-full90':9,'linear-full81':31,'linear-remaining50':14,'knucleotide-remaining36':36})
        self.assertEqual(len({s['raw'] for s in origins}),90)
        self.assertEqual(set(result['prior_producer_statuses'].values()),{'stopped-unqualified'})
        self.assertFalse(result['chart_admission']);self.assertFalse(result['file_integrity_verified'])
        for row in result['profiles'].values():
            if row['benchmark']=='knucleotide':self.assertEqual({s['cohort'] for s in row['sample_evidence']},{'knucleotide-remaining36'})
    def test_subject_failure_all_rounds_skips_only_its_future_slots(self):
        for round_ in (1,2,3):
            result=self.check(future(self.saved,'nbody:prolog-nbody-compact',round_))
            row=result['profiles']['nbody:prolog-nbody-compact']
            self.assertIsNone(row['median_seconds']);self.assertEqual(len(row['samples_seconds']),round_-1)
            self.assertEqual(result['new_full_native_processes'],33+round_)
            self.assertEqual(row['failed_cohort'],'knucleotide-remaining36')
    def test_control_failure_does_not_replace_successful_subject_values(self):
        result=self.check(future(self.saved,'knucleotide:prolog-full-study:mech-control',2))
        rows=[row for row in result['profiles'].values() if row['benchmark']=='knucleotide']
        self.assertTrue(all(row['time_x_mech'] is None for row in rows))
        self.assertTrue(all(len(row['samples_seconds'])==3 for row in rows if row['language']=='prolog'))
        self.assertEqual(result['qualified_samples'],88)
    def test_changed_order_source_receipt_or_skips_fail(self):
        mutations=[lambda v:v['report']['attempts'].reverse(),
            lambda v:v['report']['attempts'][0].update(source_sha256='0'*64),
            lambda v:v['report']['validated_attempt_artifacts'].clear(),
            lambda v:v['report']['skipped_failed_profile_slots'].append(dict(benchmark='nbody',round=1,id='bad',key='bad')),
            lambda v:v['terminal'].update(retained_qualified_samples=55),
            lambda v:v['durable']['request']['command'].insert(4,'-u')]
        for mutate in mutations:
            value=future(self.saved);mutate(value)
            with self.assertRaises((ValueError,AssertionError,KeyError)):self.check(value)
    def test_new_slots_cannot_overlap_old_cohort(self):
        value=future(self.saved);value['report']['started_at']='2020-01-01T00:00:00+00:00'
        with self.assertRaises(ValueError):self.check(value)


class Replacement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.saved=lightweight_saved_fixture()
    def test_three_file_bundle_and_unchanged_runtime_policy(self):
        value=replacement(self.saved['plan']);a.qualification_checks(value,self.saved['plan']['manifests']['knucleotide']['profiles'][:2])
        for mutation in (lambda v:v['profiles'][0].update(runtime_environment={}),
            lambda v:v['profiles'][0]['source_bundle'].pop(),lambda v:v.update(canonical_LOC_admitted=False),
            lambda v:v['profiles'][1].update(source_alias_of=None)):
            changed=copy.deepcopy(value);mutation(changed)
            with self.assertRaises((ValueError,AssertionError)):a.qualification_checks(changed,self.saved['plan']['manifests']['knucleotide']['profiles'][:2])

    def scheduled(self):
        previous=copy.deepcopy(self.saved['plan']);previous.update(linear_qualification={},timing_policy={'boundary':'synthetic-full-process'})
        plan=future(self.saved)['plan']
        plan.update(schema=a.PRODUCER_SCHEMA,status='prepared-awaiting-independent-review',repository=str(a.ROOT),
            controller=str(a.CONTROLLER),controller_sha256=a.CONTROLLER_SHA,samples=3,full_processes=36,
            combined_sample_slots=90,retained_qualified_samples=54,new_prolog_processes=24,new_mech_processes=12,
            source_work_profiles=20,canonical_loc_profiles=20,compiler_invocations=0,fixture_reexecutions=0,
            bounded_reexecutions=0,count_replays=0,repeated_completed_samples=0,common_mutex_held_continuously=True,
            no_automatic_retry=True,original_files_mutated=False,full_timings_qualified=False,chart_admission=False,
            shared_timing_lock=str(a.r.LOCK),timing_policy=previous['timing_policy'])
        # The synthetic future output references are not part of this plan test;
        # every manifest field apart from the two source rows must remain exact.
        manifests=copy.deepcopy(previous['manifests'])
        manifests['knucleotide']['profiles'][:2]=copy.deepcopy(plan['knucleotide_qualification']['profiles'])
        plan['manifests']=manifests
        plan['pins'].update({str(a.PREVIOUS_PLAN):a.PREVIOUS_PLAN_SHA,str(a.CONTROLLER):a.CONTROLLER_SHA,
                            str(a.QUALIFICATION):a.QUALIFICATION_SHA,str(a.STOP/'closure.json'):a.CLOSURE_SHA})
        profiles={row['key']:row for manifest in previous['manifests'].values() for row in manifest['profiles']}
        return plan,previous,(previous['schedule'],profiles,{})

    def test_schedule_preserves54_and_replaces_only_two_qualified_rows(self):
        plan,previous,older=self.scheduled()
        with patch.object(a.q,'schedule',return_value=older):slots,profiles,_=a.schedule(plan,previous,{}, {})
        self.assertEqual(len(slots),90);self.assertEqual(len(profiles),30)
        self.assertEqual(plan['retained_slots'],slots[:54]);self.assertEqual(plan['remaining_slots'],slots[54:])
        self.assertEqual(sum(row['source_sha256']==a.SOURCE_SHA for row in profiles.values()),2)

    def test_schedule_rejects_unrelated_metadata_pin_or_partition_changes(self):
        mutations=[lambda v:v['manifests']['nbody']['profiles'][0].update(runtime_environment={}),
            lambda v:v['manifests']['knucleotide']['profiles'][2].update(source_sha256='0'*64),
            lambda v:v['qualification'].update(sha256='0'*64),
            lambda v:v['pins'].pop(str(a.PREVIOUS_PLAN)),lambda v:v['remaining_slots'].pop(),
            lambda v:v.update(new_prolog_processes=25)]
        for mutate in mutations:
            plan,previous,older=self.scheduled();mutate(plan)
            with patch.object(a.q,'schedule',return_value=older),self.assertRaises((ValueError,AssertionError)):
                a.schedule(plan,previous,{}, {})


class OutputClosure(unittest.TestCase):
    def context(self,fail=False,mutate=None):
        @contextmanager
        def review_context(*,on_exit_failure,final_consumer_check):
            yield dict(status='synthetic',chart_admission=False)
            try:
                if mutate:mutate()
                if fail:raise ValueError('late input drift')
                final_consumer_check()
            except BaseException:
                on_exit_failure();raise
        return review_context
    def test_late_input_failure_removes_only_owned_new_result(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'review.json'
            with patch.object(a,'review_context',self.context(fail=True)),self.assertRaises(ValueError):a.write_review(path)
            self.assertFalse(path.exists())
    def test_late_output_edit_fails_preserving_external_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'review.json'
            with patch.object(a,'review_context',self.context(mutate=lambda:path.write_bytes(b'external'))),self.assertRaises(BaseException):a.write_review(path)
            self.assertEqual(path.read_bytes(),b'external')
    def test_late_output_truncation_preserves_external_prefix(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'review.json'
            with patch.object(a,'review_context',self.context(mutate=lambda:path.write_bytes(b'{'))),self.assertRaises(BaseException):a.write_review(path)
            self.assertEqual(path.read_bytes(),b'{')
    def test_success_result_exact_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'review.json'
            with patch.object(a,'review_context',self.context()):result,digest=a.write_review(path)
            self.assertEqual(digest,hashlib.sha256(path.read_bytes()).hexdigest());self.assertEqual(result,read(path))


if __name__=='__main__':unittest.main()
