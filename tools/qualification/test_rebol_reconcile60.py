"""Focused synthetic full60 ledger faults; no actual plan, lease or native run.

The frozen full90 test module supplies invented receipt shapes only. This file
builds its own two-row schedule and reindexes those synthetic receipts. The
producer is imported only for a parity assertion, never by the reader.
"""
import copy
from datetime import datetime, timedelta, timezone
import importlib.util
import json
import os
from pathlib import Path
import statistics
import tempfile
import unittest
from unittest.mock import patch


def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


HERE=Path(__file__).parent
m=load('rebol60_independent_test_subject',HERE/'rebol_reconcile60.py')
old=load('rebol60_synthetic_receipt_shapes',HERE/'test_rebol_reconcile.py')
producer=load('rebol60_schedule_parity_only',HERE/'rebol_full60.py')
SHA='1'*64
PLAN=str(m.PACKET/'synthetic-plan.json')
OUTPUT=str(m.PACKET/'synthetic-run')


def fixture(failure=None, failure_round=1):
    value=old.fixture(failure,failure_round)
    def relocate(v):
        if type(v) is str:return v.replace(str(old.m.PACKET),str(m.PACKET))
        if type(v) is list:return [relocate(x) for x in v]
        if type(v) is dict:return {relocate(k):relocate(x) for k,x in v.items()}
        return v
    value=relocate(value);plan=value['plan'];report=value['report'];terminal=value['terminal']
    pins=plan['pins']
    for before,after in ((old.m.CONTROLLER,m.CONTROLLER),(old.m.QUALIFIER,m.QUALIFIER)):
        pins.pop(str(before));pins[str(after)]=SHA
    policy=dict(path=str(m.PACKET/'POLICY.md'),sha256=SHA);pins[policy['path']]=SHA
    plan.update(schema='rebol-qualified-full60-v1',controller=str(m.CONTROLLER),
        source_work_profiles=10,canonical_loc_profiles=10,rebol_samples=30,full_processes=60,
        cohort_policy_file=policy,subject_policy=dict(authored_source_forms_per_workload=1,
        publication_forms=['compact'],duplicate_program_records=0,distinct_optimization_claim=False))
    for base in plan['qualification']['bases']:base['alias_policy']['publication_forms']=['compact']
    slots=[];originals={}
    for bench in m.BENCHES:
        manifest=plan['manifests'][bench]
        base=next(b for b in plan['qualification']['bases'] if b['benchmark']==bench)
        rows=[m.expected_subject(base,'compact',plan['qualification'],OUTPUT,pins),manifest['profiles'][2]]
        manifest['profiles']=rows;subject,control=[row['id'] for row in rows]
        manifest['orders']=[dict(round=1,profiles=[subject,control]),
                            dict(round=2,profiles=[control,subject]),
                            dict(round=3,profiles=[subject,control])]
        originals.update({row['key']:row for row in rows});keys={row['id']:row['key'] for row in rows}
        slots.extend([bench,order['round'],identity,keys[identity]]
                     for order in manifest['orders'] for identity in order['profiles'])
    plan['schedule']=slots;plan['resolutions']={k:k for k in pins}
    prior={(a['benchmark'],a['round'],a['id'],a['key']):a for a in report['attempts']}
    prior_outer=value['outer'];attempts=[];outer={};raw={};supervised={};skips=[];failed=[]
    start=datetime(2026,10,14,tzinfo=timezone.utc)
    def at(seconds):return (start+timedelta(seconds=seconds)).isoformat()
    for slot in slots:
        bench,round_number,identifier,key=slot
        if key in failed:
            skips.append(dict(benchmark=bench,round=round_number,id=identifier,key=key));continue
        a=copy.deepcopy(prior[tuple(slot)]);previous=a['attempt'];index=len(attempts)+1
        stem=OUTPUT+'/attempts/'+f'{index:03d}-{identifier}'
        a.update(attempt=index,result_path=stem+'.json',supervisor_result_path=stem+'.supervisor.json',
                 started_at=at(index*20),finished_at=at(index*20+round_number))
        a['execution_fingerprint']=old.fingerprint(originals[key])
        outer_path=OUTPUT+'/outer-supervisor/'+f'{index:03d}-{identifier}.json'
        outer[outer_path]=copy.deepcopy(prior_outer[OUTPUT+'/outer-supervisor/'+f'{previous:03d}-{identifier}.json'])
        raw[a['result_path']]={k:copy.deepcopy(v) for k,v in a.items() if k not in m.p.SUPERVISOR_FIELDS}
        supervised[a['supervisor_result_path']]=copy.deepcopy(a);attempts.append(a)
        if not a['qualified']:failed.append(key)
    rows={}
    for key,original in originals.items():
        selected=[a for a in attempts if a['key']==key];good=[a for a in selected if a['qualified']]
        values=[a['seconds'] for a in good]
        row=dict(copy.deepcopy(original),attempts=[a['attempt'] for a in selected],samples_seconds=values,
            sample_validation=[copy.deepcopy(a['validation']) for a in good],
            measurement_status='failed-full-workload' if key in failed else 'measured')
        if key in failed:row['full_failure']=copy.deepcopy(next(a for a in selected if not a['qualified']))
        else:row.update(median_seconds=statistics.median(values),sample_stdev_seconds=statistics.stdev(values))
        rows[key]=row
    for key,row in rows.items():
        control=row['benchmark']+':rebol-full-study:mech-control'
        row.update(matched_mech_control=control,matched_mech_source_sha256=rows[control]['source_sha256'],
            time_x_mech=None if key in failed or control in failed else row['median_seconds']/rows[control]['median_seconds'])
    snapshots={path:SHA for group in (raw,supervised,outer) for path in group}
    report.update(schema='rebol-full60-results-v1',source_work_profiles=10,canonical_loc_profiles=10,
        planned_rebol_samples=30,attempts=attempts,programs=rows,isolated_failed_profiles=failed,
        independent_supervisors=[dict(path=path,sha256=SHA,status='returned') for path in outer],
        validated_attempt_artifacts=dict(snapshots))
    terminal.update(schema='rebol-full60-terminal-v1',prerequisite_pins=dict(pins,**{PLAN:SHA}),
        prerequisite_resolutions=dict(plan['resolutions'],**{PLAN:PLAN}),validated_attempt_artifacts=dict(snapshots),
        available_evidence_pins=dict(snapshots,**{OUTPUT+'/report.json':SHA}))
    for item in (report,terminal):
        item.update(status='complete-with-unqualified-profiles' if failed else 'complete',
            skipped_failed_profile_slots=copy.deepcopy(skips),saved_attempts=len(attempts),full_performance_runs=len(attempts),
            qualified_samples=sum(a['qualified'] for a in attempts),registered_native_attempts=list(range(1,len(attempts)+1)))
    command=[m.p.PYTHON,'-I','-S','-B',str(m.CONTROLLER),'run','--plan',PLAN,'--plan-sha256',SHA]
    for name in ('request','launch','worker-started','command-started'):value['durable'][name]['command']=command[:]
    listing='Wed Oct 14 00:00:01 2026 '+' '.join(command);report['supervisor']['process_listing']=listing
    for name in ('command-started','terminal'):value['durable'][name]['command_identity']['listing']='99 98 '+listing
    value.update(raw=raw,supervised=supervised,outer=outer,plan_path=PLAN)
    return value


class Ledger(unittest.TestCase):
    def test_sixty_actual_slots_twenty_rows_and_no_copied_form(self):
        value=fixture();result=m.reconcile(**value)
        self.assertEqual((result['actual_full_native_processes'],result['qualified_samples']),(60,60))
        self.assertEqual((result['actual_rebol_processes'],result['actual_matched_mech_processes']),(30,30))
        self.assertEqual(len(result['profiles']),20)
        self.assertEqual(len({v['path'] for b in result['qualification']['bases'] for v in b['physical_inputs']}),15)
        self.assertFalse(any('optimized' in key for key in result['profiles']))
        self.assertTrue(all(row['endpoint_eligible'] and row['median_seconds']==2.0 and
                            row['sample_stdev_seconds']==1.0 for row in result['profiles'].values()))
        self.assertTrue(all(result[name] is False for name in ('file_integrity_verified','chart_admission',
                            'runtime_publication_metadata_qualified','full_timings_qualified','runtime_source_equivalence_proven')))

    def test_independent_schedule_and_aggregates_match_producer_contract(self):
        for failure in (None,'rebol-regexredux-compact','regexredux:rebol-full-study:mech-control'):
            value=fixture(failure,2);plan=value['plan']
            slots,rows=m.schedule(plan)
            self.assertEqual([tuple(v) for v in slots],producer.schedule_for(plan['manifests']))
            self.assertEqual(list(rows),list(value['report']['programs']))
            # Test-only cross-check; the independent reader never invokes this producer validator.
            producer.check_success_ledger(plan,value['report'])
            self.assertEqual(m.reconcile(**value)['failed_profiles'],[] if failure is None else [failure])

    def test_subject_failure_each_round_retains_partial_samples_without_median(self):
        for round_number in (1,2,3):
            with self.subTest(round=round_number):
                result=m.reconcile(**fixture('rebol-revcomp-compact',round_number));row=result['profiles']['rebol-revcomp-compact']
                self.assertEqual((result['actual_full_native_processes'],result['qualified_samples']),
                                 (57+round_number,56+round_number))
                self.assertEqual(len(row['samples_seconds']),round_number-1)
                self.assertEqual(len(row['sample_evidence']),round_number)
                self.assertIsNone(row['median_seconds']);self.assertFalse(row['endpoint_eligible'])
                self.assertEqual(len(result['skipped_slots']),3-round_number)

    def test_failed_control_excludes_subject_but_keeps_descriptive_samples(self):
        for round_number in (1,2,3):
            result=m.reconcile(**fixture('regexredux:rebol-full-study:mech-control',round_number))
            row=result['profiles']['rebol-regexredux-compact']
            self.assertTrue(row['full_workload_qualified']);self.assertEqual(row['samples_seconds'],[1.,2.,3.])
            self.assertEqual(row['median_seconds'],2.);self.assertFalse(row['endpoint_eligible']);self.assertIsNone(row['time_x_mech'])

    def test_schema_policy_counts_rotation_and_alias_substitutions_reject(self):
        def alter(plan,kind):
            if kind=='schema':plan['schema']='rebol-qualified-full90-v1'
            elif kind=='count':plan['rebol_samples']=60
            elif kind=='policy':plan['subject_policy']['publication_forms'].append('optimized')
            elif kind=='policy_path':plan['cohort_policy_file']['path']=str(m.PACKET/'README.md')
            elif kind=='forms':plan['qualification']['bases'][0]['alias_policy']['publication_forms'].append('optimized')
            elif kind=='rotation':plan['manifests']['regexredux']['orders'][2]['profiles'].reverse()
            elif kind=='extra':plan['manifests']['regexredux']['profiles'].append(copy.deepcopy(plan['manifests']['regexredux']['profiles'][0]))
            else:plan['manifests']['regexredux']['profiles'][0]['timing_alias_of']='other'
        for kind in ('schema','count','policy','policy_path','forms','rotation','extra','alias'):
            value=fixture();alter(value['plan'],kind)
            with self.subTest(kind=kind),self.assertRaises(ValueError):m.reconcile(**value)

    def test_independent_raw_ownership_and_no_retry_checks(self):
        for kind in ('raw','supervisor','outer_parent','cleanup','missing','repeat','terminal'):
            value=fixture();a=value['report']['attempts'][0];outer=next(iter(value['outer'].values()))
            if kind=='raw':value['raw'][a['result_path']]['seconds']=100.
            elif kind=='supervisor':value['supervised'][a['supervisor_result_path']]['seconds']=100.
            elif kind=='outer_parent':next(iter(outer['owned_sampler_children'].values()))['identity']['ppid']=999
            elif kind=='cleanup':outer['cleanup_errors']=['synthetic live descendant']
            elif kind=='missing':value['report']['attempts'].pop()
            elif kind=='repeat':value['report']['attempts'].append(copy.deepcopy(a))
            else:value['terminal']['status']='failed-terminal-integrity'
            with self.subTest(kind=kind),self.assertRaises(ValueError):m.reconcile(**value)

    def test_statistics_partial_failure_and_control_ratios_reject(self):
        for field,bad in (('median_seconds',2.1),('sample_stdev_seconds',0.),('time_x_mech',True)):
            value=fixture();value['report']['programs']['rebol-fasta-compact'][field]=bad
            with self.subTest(field=field),self.assertRaises(ValueError):m.reconcile(**value)
        value=fixture('rebol-fasta-compact',2);value['report']['programs']['rebol-fasta-compact']['median_seconds']=1.
        with self.assertRaisesRegex(ValueError,'Partial failure promoted'):m.reconcile(**value)

    def test_exact_durable_status_argv_and_controller_birth(self):
        for kind in ('status','argv','birth','worker','stop'):
            value=fixture();durable=value['durable']
            if kind=='status':durable['terminal']['status']='command-succeeded'
            elif kind=='argv':durable['request']['command'].insert(4,'-u')
            elif kind=='birth':value['report']['supervisor']['process_listing']=value['report']['supervisor']['process_listing'].replace('00:00:01','00:00:02')
            elif kind=='worker':durable['terminal']['worker_identity']['pid']=700
            else:durable['terminal']['stop_signals']=['TERM']
            with self.subTest(kind=kind),self.assertRaises(ValueError):m.reconcile(**value)


class IntakeAndClosure(unittest.TestCase):
    def test_exact_producer_source_review_and_policy_membership(self):
        plan=fixture()['plan']
        files=(m.CONTROLLER,m.CONTROLLER.with_name('test_rebol_full60.py'),m.PACKET/'README.md',m.PACKET/'POLICY.md')
        deps={str(m.QUALIFIER.relative_to(m.ROOT)):SHA,'tools/qualification/elixir_full.py':producer.HELPERS_SHA,
              str(m.HELPER.relative_to(m.ROOT)):m.HELPER_SHA,str(m.ORIGINAL.relative_to(m.ROOT)):m.ORIGINAL_SHA}
        review=dict(schema='rebol-full60-source-review-v1',status='independent-source-review-complete-native-timing-pending',
            independent_review=True,full_timing_qualified=False,chart_admission=False,
            files={str(path.relative_to(m.ROOT)):SHA for path in files},dependencies=deps)
        plan['pins'].update({str(m.ROOT/name):sha for name,sha in {**review['files'],**deps}.items()})
        m.source_review(plan,review)
        for kind in ('policy','original','helper'):
            changed=copy.deepcopy(review)
            if kind=='policy':changed['files'].pop(str((m.PACKET/'POLICY.md').relative_to(m.ROOT)))
            else:changed['dependencies'][str((m.ORIGINAL if kind=='original' else m.HELPER).relative_to(m.ROOT))]='0'*64
            with self.subTest(kind=kind),self.assertRaises(ValueError):m.source_review(plan,changed)

    def test_pinned_qualification_entry_api_uses_exact_verified_bytes(self):
        raw=("from pathlib import Path\nfrom types import SimpleNamespace\n"
             "def load_controller(expected):\n"
             "    return SimpleNamespace(ROOT=Path(__file__).resolve().parents[2], observed=expected)\n").encode()
        expected=m.digest(raw);plan=dict(pins={str(m.QUALIFIER):expected})
        with patch.object(m,'read_regular',return_value=raw) as read:
            q=m.load_qualification(plan);self.assertEqual(q.observed,expected);read.assert_called_once_with(m.QUALIFIER)
        with patch.object(m,'read_regular',return_value=raw+b'# changed'):
            with self.assertRaisesRegex(ValueError,'Qualification consumer changed'):m.load_qualification(plan)
        raw=raw.replace(b'Path(__file__).resolve().parents[2]',b"Path('/wrong')")
        with patch.object(m,'read_regular',return_value=raw):
            with self.assertRaisesRegex(ValueError,'Qualification root differs'):m.load_qualification(dict(pins={str(m.QUALIFIER):m.digest(raw)}))

    def test_yielded_pins_result_and_final_callback_remain_immutable(self):
        for fault in ('pin','resolution','result','during_replay','consumer'):
            pins={'/original':SHA};resolutions={'/original':'/original'};result={'rows':20};events=[]
            def replay(a,b):
                events.append('replay');self.assertEqual(a,{'/original':SHA})
                if fault=='during_replay':pins.clear()
            def consumer():
                events.append('consumer')
                if fault=='consumer':result['rows']=30
            final=m.immutable_final_check(pins,resolutions,result,replay,consumer)
            if fault=='pin':pins.clear()
            elif fault=='resolution':resolutions['/original']='/replacement'
            elif fault=='result':result['rows']=30
            with self.subTest(fault=fault),self.assertRaises(ValueError):final()
            self.assertEqual(events,[] if fault in ('pin','resolution','result') else
                             ['replay'] if fault=='during_replay' else ['replay','consumer'])

    def test_original_lease_identity_and_nonregular_file_rejection(self):
        self.assertEqual(m.JOB.name,'rebol-full60-v1');self.assertEqual(m.SUITE.parent,m.PACKET)
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp).resolve();fifo=directory/'fifo';os.mkfifo(fifo)
            with self.assertRaisesRegex(ValueError,'Regular evidence'):m.read_regular(fifo)
            path=directory/'owner.lock';path.write_bytes(b'')
            with m.regular_lease(path) as stream:
                held=os.fstat(stream.fileno());leases=[(path,stream,(held.st_dev,held.st_ino))]
                m.verify_leases(leases);path.rename(directory/'old');path.write_bytes(b'')
                with self.assertRaisesRegex(ValueError,'Review lease replaced'):m.verify_leases(leases)
                self.assertFalse(stream.closed)


if __name__=='__main__':unittest.main()
