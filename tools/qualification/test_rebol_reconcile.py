"""Synthetic receipt/closure faults only; no producer or native invocation.

All times, paths, PIDs and hashes in fixtures are invented test data. These
tests neither read future measured reports nor stand in for their file review.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


HERE=Path(__file__).parent
m=load('test_rebol_independent_reconcile',HERE/'rebol_reconcile.py')
base=load('test_rebol_shared_synthetic_receipts',HERE/'test_prolog_reconcile.py')
SHA='1'*64
PLAN=str(m.PACKET/'synthetic-plan.json')
OUTPUT=str(m.PACKET/'synthetic-run')


def fingerprint(row):
    support={}
    def collect(value):
        if type(value) is dict:
            if value.get('path') and m.p.digest(value.get('sha256')):support[value['path']]=value['sha256']
            for child in value.values():collect(child)
        elif type(value) is list:
            for child in value:collect(child)
    collect(row)
    return json.dumps(dict(source_sha256=row['source_sha256'],binary_sha256=row['binary_sha256'],
        command=[v.replace(row['source'],'{source}') for v in row['command']],cwd=row['cwd'],
        environment=row['runtime_environment'],support=support),sort_keys=True)


def fixture(failure=None, failure_round=1):
    old_failure=None
    if failure:
        old_failure=(failure.replace(':rebol-full-study:',':prolog-full-study:') if ':mech-control' in failure
                     else failure.split('-')[1]+':'+failure.replace('rebol-','prolog-'))
    value=base.fixture(old_failure,failure_round)
    def convert(v):
        if type(v) is str:
            v=v.replace('/fixture/results',OUTPUT)
            for bench in m.BENCHES:v=v.replace(bench+':prolog-'+bench+'-','rebol-'+bench+'-')
            return v.replace('prolog-','rebol-').replace(':prolog-full-study:',':rebol-full-study:')
        if type(v) is list:return [convert(x) for x in v]
        if type(v) is dict:return {convert(k):convert(x) for k,x in v.items()}
        return v
    value=convert(value);old=value['plan'];report=value['report'];terminal=value['terminal']
    refs={name:dict(path=str(m.PACKET/(name+'.json')),sha256=SHA)
          for name in ('qualification_manifest','source_review','original_profiles')}
    runtime=dict(path='/fixture/rebol',sha256=SHA);image=dict(path='/fixture/primitives.dylib',sha256=SHA)
    pins={str(m.CONTROLLER):SHA,str(m.QUALIFIER):SHA,m.p.PYTHON:SHA,runtime['path']:SHA,image['path']:SHA,
          **{v['path']:v['sha256'] for v in refs.values()}}
    fixed=dict(PATH='/usr/bin:/bin:/usr/sbin:/sbin',LC_ALL='C',LANG='C',OMP_NUM_THREADS='1',
               OPENBLAS_NUM_THREADS='1',VECLIB_MAXIMUM_THREADS='1')
    bases=[]
    for bench in m.BENCHES:
        inputs=[dict(path='/fixture/sources/'+bench+'/main.reb',sha256=SHA,role='application',counted=True,canonical_loc=2,physical_loc=3)]
        owners=[('clbg_io.reb','application-helper'),('clbg_primitives.reb','application-launcher'),
                ('clbg_primitives.c','general-library-helper')]
        if bench in ('pidigits','regexredux'):
            owners.append(('clbg_big.reb' if bench=='pidigits' else 'clbg_regex.reb','application-helper'))
        inputs.extend(dict(path='/fixture/support/'+name,sha256=SHA,role=role,counted=True,canonical_loc=2,physical_loc=3)
                      for name,role in owners)
        pins.update({v['path']:v['sha256'] for v in inputs})
        main={k:inputs[0][k] for k in ('path','sha256')}
        bases.append(dict(benchmark=bench,language='rebol3',original_profile_id=f'rebol-{bench}-baseline-v1',
            main=main,command_prefix=[runtime['path'],'-q','-s',main['path']],
            input_kind='stdin' if bench in ('regexredux','revcomp','knucleotide') else 'integer-argument',
            cwd=str(m.ROOT),maximum_workers=1,physical_inputs=inputs,canonical_loc=len(inputs)*2,
            physical_loc=len(inputs)*3,formatted_loc=None,corrections={},
            alias_policy=dict(authored_source_forms=1,publication_forms=['compact','optimized'],
                              distinct_optimization_claim=False,copied_timing_allowed=False),
            runtime_environment_policy=dict(fixed=fixed,fresh_directories=dict(HOME='home',REBOL_HOME='home',TMPDIR='tmp'),
                extension_variable='MECH_CLBG_REBOL_PRIMITIVES',ambient_loader_overrides=False,diagnostic_flags=[])))
    admission=dict(schema='rebol-pre-timing-admission-v1',manifest=refs['qualification_manifest'],bases=bases,
        runtime=dict(binary=runtime),extension_image=image,scope=dict(required_work_qualified=True,
            canonical_source_count_qualified=True,bounded_output_qualified=True,extension_abi_qualified=True,
            full_primitive_fixtures_qualified=True,runtime_source_equivalence_proven=False,
            full_timing_qualified=False,chart_admission=False))
    manifests={}
    for b in bases:
        bench=b['benchmark'];control=copy.deepcopy(old['manifests'][bench]['profiles'][2])
        control.update(loc=None);pins.update({control[k]:control[k+'_sha256'] for k in ('source','binary')})
        rows=[m.expected_subject(b,form,admission,OUTPUT,pins) for form in ('compact','optimized')]+[control]
        ids=[v['id'] for v in rows];ref=m.FULL_REFERENCES[bench]
        manifests[bench]=dict(benchmark=bench,profiles=rows,size=m.SIZES[bench],samples=3,
            timeout_seconds=21600,supervisor_timeout_seconds=22200,maximum_rss_mib=10240,
            canonical_full_workload=True,compilation_outside_timer=True,
            runtime_source_helpers_extension_loading_inside_timer=True,no_automatic_retry=True,
            chart_admission=False,shared_timing_lock=str(m.LOCK),orders=[dict(round=i+1,profiles=ids[i:]+ids[:i]) for i in range(3)],
            full_output_reference=None if ref is None else dict(bytes=ref[0],sha256=ref[1]))
    plan=dict(schema='rebol-qualified-full90-v1',status='prepared-awaiting-independent-review',pins_verified=True,
        repository=str(m.ROOT),output=OUTPUT,controller=str(m.CONTROLLER),controller_sha256=SHA,**refs,
        qualification=admission,source_work_profiles=20,canonical_loc_profiles=20,formatted_loc_profiles=0,
        distinct_subject_bundles=10,counted_physical_sources=15,retained_bounded_cases=149,retained_primitive_cases=18,
        samples=3,rebol_samples=60,matched_mech_samples=30,full_processes=90,new_native_probes=0,
        compiler_invocations=0,fixture_reexecutions=0,bounded_reexecutions=0,original_files_mutated=False,
        chart_admission=False,full_timings_qualified=False,runtime_source_equivalence_proven=False,
        no_automatic_retry=True,continuous_common_mutex=True,shared_timing_lock=str(m.LOCK),
        common_mutex_inode=m.p.LOCK_INODE,timing_policy=m.TIMING_POLICY,pins=pins,
        resolutions={k:k for k in pins},manifests=manifests,schedule=old['schedule'])
    value.update(plan=plan,plan_path=PLAN,plan_sha=SHA)
    originals={v['key']:v for x in manifests.values() for v in x['profiles']}
    report.update(schema='rebol-full90-results-v1',plan=PLAN,plan_sha256=SHA,qualification_manifest=refs['qualification_manifest'],
        formatted_loc_profiles=0,planned_rebol_samples=60,planned_matched_mech_samples=30,
        full_timings_qualified=False,runtime_source_equivalence_proven=False,descriptive_provenance=[],kernel_identity_observation_gaps=[])
    terminal.update(schema='rebol-full90-terminal-v1',common_mutex_held_continuously=True,
        common_mutex_inode=m.p.LOCK_INODE,full_timings_qualified=False,runtime_source_equivalence_proven=False,
        prerequisite_pins=dict(pins,**{PLAN:SHA}),prerequisite_resolutions=dict(plan['resolutions'],**{PLAN:PLAN}),
        report=OUTPUT+'/report.json',report_sha256=SHA)
    terminal.pop('count_replays',None)
    for key,row in list(report['programs'].items()):
        report['programs'][key]=dict(copy.deepcopy(originals[key]),**{k:v for k,v in row.items() if k in m.AGGREGATE})
    for a in report['attempts']:
        row=originals[a['key']]
        for field in ('language','source_sha256','cwd','runtime_environment'):a[field]=copy.deepcopy(row[field])
        a['command']=[v.replace('{n}',str(m.SIZES[row['benchmark']])) for v in row['command']]
        a['supervised_native_group']['command']=a['command'][:];a['execution_fingerprint']=fingerprint(row)
        ref=manifests[row['benchmark']]['full_output_reference'] or dict(bytes=44,sha256=SHA)
        a.update(stdout_bytes=ref['bytes'],stdout_sha256=ref['sha256']);a['validation'].update(ref)
        value['raw'][a['result_path']]={k:copy.deepcopy(v) for k,v in a.items() if k not in m.p.SUPERVISOR_FIELDS}
        value['supervised'][a['supervisor_result_path']]=copy.deepcopy(a)
        outer=OUTPUT+'/outer-supervisor/'+f'{a["attempt"]:03d}-{a["id"]}.json'
        value['outer'][outer]['native_registrations']=[copy.deepcopy(a['supervised_native_group'])]
    for key,row in report['programs'].items():
        attempts=[a for a in report['attempts'] if a['key']==key]
        row['sample_validation']=[copy.deepcopy(a['validation']) for a in attempts if a['qualified']]
        row['matched_mech_source_sha256']=originals[row['matched_mech_control']]['source_sha256']
        if row.get('full_failure'):row['full_failure']=copy.deepcopy(next(a for a in attempts if not a['qualified']))
    snapshots={k:v for k,v in terminal['available_evidence_pins'].items() if k!=OUTPUT+'/report.json'}
    report['validated_attempt_artifacts']=copy.deepcopy(snapshots);terminal['validated_attempt_artifacts']=snapshots
    command=[m.p.PYTHON,'-I','-S','-B',str(m.CONTROLLER),'run','--plan',PLAN,'--plan-sha256',SHA]
    for name in ('request','launch','worker-started','command-started'):
        value['durable'][name].update(command=command,cwd=str(m.ROOT))
    listing='Wed Oct 14 00:00:01 2026 '+' '.join(command)
    report['supervisor']['process_listing']=listing
    for name in ('command-started','terminal'):value['durable'][name]['command_identity']['listing']='99 98 '+listing
    return value


class Ledger(unittest.TestCase):
    def test_ninety_distinct_actual_samples_and_fifteen_counted_sources(self):
        value=fixture();result=m.reconcile(**value)
        self.assertEqual((result['actual_full_native_processes'],result['qualified_samples']),(90,90))
        self.assertEqual((result['actual_rebol_processes'],result['actual_matched_mech_processes']),(60,30))
        self.assertTrue(all(v['endpoint_eligible'] for v in result['profiles'].values()))
        self.assertFalse(result['file_integrity_verified']);self.assertFalse(result['runtime_publication_metadata_qualified'])
        self.assertFalse(result['chart_admission'])
        one=result['profiles']['rebol-pidigits-compact'];two=result['profiles']['rebol-pidigits-optimized']
        self.assertEqual(one['original_profile']['physical_inputs'],two['original_profile']['physical_inputs'])
        self.assertTrue(set(one['attempts']).isdisjoint(two['attempts']))

    def test_failure_each_round_retains_partial_observations_without_median(self):
        for round_number in (1,2,3):
            key='rebol-revcomp-compact';result=m.reconcile(**fixture(key,round_number));row=result['profiles'][key]
            self.assertEqual(len(row['samples_seconds']),round_number-1)
            self.assertEqual(len(row['sample_evidence']),round_number)
            self.assertIsNone(row['median_seconds']);self.assertFalse(row['endpoint_eligible'])
            self.assertEqual(result['actual_full_native_processes'],87+round_number)

    def test_failed_control_excludes_both_successful_forms(self):
        result=m.reconcile(**fixture('regexredux:rebol-full-study:mech-control'))
        for form in ('compact','optimized'):
            row=result['profiles']['rebol-regexredux-'+form]
            self.assertTrue(row['full_workload_qualified']);self.assertIsNotNone(row['median_seconds'])
            self.assertFalse(row['endpoint_eligible']);self.assertIsNone(row['time_x_mech'])

    def test_raw_supervisor_and_outer_are_independently_checked(self):
        errors={'raw':'Supervisor changed raw sampler evidence','supervised':'Report differs from supervisor receipt',
                'outer':'Expected exactly one sampler child'}
        for kind in ('raw','supervised','outer'):
            value=fixture();path=next(iter(value[kind]))
            if kind=='outer':value[kind][path]['owned_sampler_children'].clear()
            else:value[kind][path]['stdout_sha256']='f'*64
            with self.subTest(kind=kind),self.assertRaisesRegex(ValueError,'^'+errors[kind]+'$'):m.reconcile(**value)

    def test_timing_alias_missing_rotation_and_extra_attempt_reject(self):
        errors={'alias':'Subject differs from qualification','rotation':'Rotation differs','extra':'Outer receipt count differs'}
        for fault in ('alias','rotation','extra'):
            value=fixture()
            if fault=='alias':value['plan']['manifests']['fasta']['profiles'][1]['timing_alias_of']='compact'
            elif fault=='rotation':value['plan']['manifests']['fasta']['orders'][1]['profiles'].reverse()
            else:value['report']['attempts'].append(copy.deepcopy(value['report']['attempts'][-1]))
            with self.subTest(fault=fault),self.assertRaisesRegex(ValueError,'^'+errors[fault]+'$'):m.reconcile(**value)

    def test_changed_general_c_count_or_environment_reject(self):
        errors={'count':'Subject differs from qualification','C':'Source bundle membership differs',
                'environment':'Subject differs from qualification'}
        for fault in ('count','C','environment'):
            value=fixture();row=value['plan']['manifests']['pidigits']['profiles'][0]
            if fault=='count':row['canonical_loc']-=1
            elif fault=='C':row['physical_inputs'].pop(3)
            else:row['runtime_environment']['DYLD_INSERT_LIBRARIES']='/diagnostic'
            with self.subTest(fault=fault),self.assertRaisesRegex(ValueError,'^'+errors[fault]+'$'):m.reconcile(**value)

    def test_late_failed_terminal_cannot_admit_complete_report(self):
        value=fixture();value['terminal']['status']='failed-terminal-integrity'
        value['terminal']['common_mutex_held']=False
        with self.assertRaisesRegex(ValueError,'^Not a completed full90 ledger$'):m.reconcile(**value)

    def test_actual_durable_status_and_exact_no_u_command(self):
        value=fixture();m.check_durable(value['durable'],PLAN,SHA,value['plan'])
        errors={'invented':'Durable execution failed','u':'Durable command differs','stop':'Durable execution failed'}
        for fault in ('invented','u','stop'):
            bad=copy.deepcopy(value['durable'])
            if fault=='invented':bad['terminal']['status']='command-succeeded'
            elif fault=='u':bad['request']['command'].insert(4,'-u')
            else:bad['terminal']['stop_signals']=[15]
            with self.subTest(fault=fault),self.assertRaisesRegex(ValueError,'^'+errors[fault]+'$'):m.check_durable(bad,PLAN,SHA,value['plan'])

    def test_serial_native_intervals_and_snapshot_membership(self):
        errors={'overlap':'Native timing intervals overlap','snapshot':'Terminal snapshots differ',
                'resolution':'Terminal named input resolutions differ'}
        for fault in ('overlap','snapshot','resolution'):
            value=fixture()
            if fault=='overlap':
                a=value['report']['attempts'][1];a['started_at']=value['report']['attempts'][0]['started_at']
                value['raw'][a['result_path']]['started_at']=a['started_at']
                value['supervised'][a['supervisor_result_path']]['started_at']=a['started_at']
            elif fault=='snapshot':value['terminal']['validated_attempt_artifacts'].pop(next(iter(value['raw'])))
            else:value['terminal']['prerequisite_resolutions'][PLAN]='/replacement'
            with self.subTest(fault=fault),self.assertRaisesRegex(ValueError,'^'+errors[fault]+'$'):m.reconcile(**value)

    def test_failed_partial_median_and_wrong_control_ratio_reject(self):
        value=fixture('rebol-fasta-compact',2);value['report']['programs']['rebol-fasta-compact']['median_seconds']=1.0
        with self.assertRaisesRegex(ValueError,'^Partial failure promoted to median$'):m.reconcile(**value)
        value=fixture();value['report']['programs']['rebol-fasta-optimized']['time_x_mech']=2.0
        with self.assertRaisesRegex(ValueError,'^Matched ratio differs$'):m.reconcile(**value)

    def test_control_source_audit_join_rejects_substituted_binary(self):
        plan=fixture()['plan'];documents=dict(audit=dict(status='reviewed',controls=[]),mandelbrot=dict(profiles=[]))
        for bench in m.BENCHES:
            original={k:copy.deepcopy(plan['manifests'][bench]['profiles'][2][k]) for k in m.EXECUTION_FIELDS}
            original['id']='row16-aot-control' if bench=='mandelbrot' else 'retained-'+bench
            documents['audit']['controls'].append(original)
            if bench=='mandelbrot':documents['mandelbrot']['profiles'].append(original)
            expected=copy.deepcopy(original);ref=m.CONTROL_REFS['mandelbrot' if bench=='mandelbrot' else 'audit']
            expected.update(id='mech-aot-control',key=bench+':rebol-full-study:mech-control',maximum_workers=8,
                loc=None,role='Fresh unchanged matched Mech AOT control',chart_admission=False,
                control_provenance=dict(ref,original_id=original['id']))
            plan['manifests'][bench]['profiles'][2]=expected
        m.check_controls(plan,documents)
        plan['manifests']['nbody']['profiles'][2]['binary']='/unreviewed/control'
        with self.assertRaisesRegex(ValueError,'^Matched control differs from retained source audit$'):m.check_controls(plan,documents)


class PhysicalClosure(unittest.TestCase):
    def test_immutable_pin_and_result_snapshots(self):
        errors={'delete':'Review-owned pin removed or rebound','rebind':'Review-owned pin removed or rebound',
                'result':'Yielded reconciliation changed'}
        for fault in ('delete','rebind','result'):
            pins={'/old':SHA};resolutions={'/old':'/old'};result={'status':'verified'};events=[]
            final=m.immutable_final_check(pins,resolutions,result,lambda a,b:events.append('replay'),lambda:events.append('consumer'))
            if fault=='delete':pins.clear()
            elif fault=='rebind':resolutions['/old']='/new'
            else:result['status']='altered'
            with self.subTest(fault=fault),self.assertRaisesRegex(ValueError,'^'+errors[fault]+'$'):final()
            self.assertEqual(events,[])

    def test_mutation_during_replay_rejects_before_consumer(self):
        pins={'/old':SHA};resolutions={'/old':'/old'};result={'status':'verified'};events=[]
        def replay(a,b):
            self.assertEqual(a,{'/old':SHA});pins.clear()
        final=m.immutable_final_check(pins,resolutions,result,replay,lambda:events.append('consumer'))
        with self.assertRaisesRegex(ValueError,'^Review-owned pin removed or rebound$'):final()
        self.assertEqual(events,[])

    def test_callback_order_and_added_pins_do_not_shrink_original(self):
        pins={'/old':SHA};resolutions={'/old':'/old'};result={'status':'verified'};events=[]
        final=m.immutable_final_check(pins,resolutions,result,lambda a,b:events.append(('replay',dict(a))),
                                     lambda:events.append('consumer'))
        pins['/new']='a'*64;resolutions['/new']='/new';final()
        self.assertEqual(events,[('replay',{'/old':SHA}),'consumer'])

    def test_fifo_and_symlink_reject_before_read(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp).resolve();fifo=root/'fifo';os.mkfifo(fifo)
            with self.assertRaisesRegex(ValueError,'^Regular evidence file required$'):m.read_regular(fifo)
            with self.assertRaisesRegex(ValueError,'^Regular original lease required$'):
                with m.regular_lease(fifo):pass
            target=root/'target';target.write_bytes(b'good');link=root/'link';link.symlink_to(target)
            with self.assertRaisesRegex(ValueError,'^Physical evidence path required$'):m.read_regular(link)
            self.assertEqual(m.read_regular(target),b'good')

    def test_named_lease_replacement_rejects_with_original_descriptor_open(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp).resolve()/'owner.lock';path.write_bytes(b'')
            with m.regular_lease(path) as stream:
                identity=os.fstat(stream.fileno());leases=[(path,stream,(identity.st_dev,identity.st_ino))]
                m.verify_leases(leases);path.rename(path.with_name('old'));path.write_bytes(b'')
                with self.assertRaisesRegex(ValueError,'^Review lease replaced$'):m.verify_leases(leases)
                self.assertFalse(stream.closed)


if __name__=='__main__':unittest.main()
