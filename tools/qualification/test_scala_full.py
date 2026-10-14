"""Saved-metadata and synthetic policy faults; no native execution/full hashing."""
import copy
from contextlib import contextmanager
from datetime import datetime,timezone,timedelta
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PATH=Path(__file__).with_name('scala_full.py')
SPEC=importlib.util.spec_from_file_location('scala_full_test_subject',PATH)
full=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(full)


class ScalaFull(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs={name:json.loads((full.ROOT/path).read_bytes()) for name,(path,_) in full.REFS.items()}
        cls.rows,cls.counted,cls.runtime,cls.pins,cls.closures=full.prerequisites()

    def evidence(self,mutation=None):
        docs=copy.deepcopy(self.docs)
        if mutation:mutation(docs)
        return full.validate_evidence(docs)

    def candidate(self,identity='scala-nbody-jvm-v1',row=None,counted=None,runtime=None,pins=None):
        return full.candidate(row or self.rows[identity],counted or self.counted[identity],
                              runtime or self.runtime,self.pins if pins is None else pins)

    def manifests(self):
        return {b:dict(benchmark=b,samples=3,orders=full.orders_for(b),profiles=[
            dict(id='scala-'+b+'-jvm-v1',key='scala-'+b+'-jvm-v1',benchmark=b,language='scala'),
            dict(id='mech-aot-control',key=b+':scala-full-study:mech-control',benchmark=b,language='mech')])
            for b in full.BENCHES}

    def test_actual_ten_source_class_count_and_work_links(self):
        original,counted,runtime=self.evidence()
        self.assertEqual(set(original),set(counted));self.assertEqual(len(original),10)
        self.assertEqual(len(self.closures),5)
        for identity in original:
            row=self.candidate(identity)
            self.assertTrue(row['source_work_qualified']);self.assertIsNone(row['source_alias_of'])
            self.assertEqual(len(row['physical_inputs']),1)
            self.assertEqual(row['source_sha256'],counted[identity]['source_sha256'])

    def test_unqualified_or_incomplete_admission_rejected(self):
        mutations=[lambda d:d['work'].update(source_work_qualified=False),
            lambda d:d['work']['qualified_profiles'].pop(),lambda d:d['loc'].update(canonical_LOC_admitted=False),
            lambda d:d['work'].update(chart_admission=True),lambda d:d['work'].update(producer_artifacts_unchanged=False)]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                with self.assertRaises(AssertionError):self.evidence(mutate)

    def test_pi_tree_and_bounded_decisions_required(self):
        for mutate in [lambda d:d['pi_peer'].update(both_division_calls_dominate_comparison=False),
                lambda d:d['pi_peer'].update(complete_hotspot_log=False),
                lambda d:d['tree_peer'].update(status='pending'),
                lambda d:d['bounded_review'].update(all_native_children_reaped=False),
                lambda d:d['bounded_report'].update(rejected_cases=6),
                lambda d:d['bounded_terminal']['integrity_errors'].append('changed')]:
            with self.assertRaises(AssertionError):self.evidence(mutate)

    def test_wrong_source_class_or_native_reference_rejected(self):
        for mutate in [lambda d:d['compiled_report']['profiles'][0].update(source_sha256='0'*64),
                lambda d:d['static']['profiles'][0]['class_artifacts'][0].update(sha256='0'*64),
                lambda d:d['work']['producer_report'].update(sha256='0'*64),
                lambda d:d['capture_plan']['profiles'][0].update(main_owner='AnotherMain'),
                lambda d:d['capture_report'].update(active={'pid':1}),
                lambda d:d['compiled_terminal'].update(report_sha256='0'*64)]:
            with self.assertRaises(AssertionError):self.evidence(mutate)

    def test_fixed_heap_workers_gc_and_no_timed_diagnostics(self):
        for identity in self.rows:
            row=self.candidate(identity);command=row['command']
            self.assertEqual(command[1:5],full.FLAGS)
            self.assertNotIn('dotty.tools.dotc.Main',command);self.assertEqual(row['diagnostic_flags'],[])
            self.assertEqual(row['runtime_environment']['CLASSPATH'],'')
            self.assertFalse(any(x in row['runtime_environment'] for x in full.INJECTION_ENV))
            self.assertEqual(command[-1], 'Main' if row['benchmark'] in ('revcomp','regexredux','knucleotide') else '{n}')
        for flag in ('-Xmx1g','-Xint','-XX:+UseSerialGC','-XX:ActiveProcessorCount=1'):
            with self.assertRaises(AssertionError):self.evidence(lambda d:d['capture_plan']['runtime_flags'].append(flag))

    def test_counted_source_and_class_pins_cannot_be_dropped(self):
        identity='scala-nbody-jvm-v1'
        for name in [self.rows[identity]['source'],self.rows[identity]['compiled_source'],
                     self.rows[identity]['artifacts'][0]['path'],self.runtime['java'],self.runtime['runtime_libraries'][0]]:
            pins=dict(self.pins);pins.pop(name)
            with self.assertRaises(AssertionError):self.candidate(pins=pins)
        row=copy.deepcopy(self.rows[identity]);row['artifacts'][0]['relative_path']='../escape.class'
        with self.assertRaises(AssertionError):self.candidate(row=row)

    def test_no_fabricated_formatted_counts_or_library_substitution(self):
        for field,value in [('formatted_loc',12),('formatted_loc_qualified',True),('canonical_loc',False),('physical_loc',0)]:
            counted=copy.deepcopy(self.counted['scala-nbody-jvm-v1']);counted[field]=value
            with self.assertRaises(AssertionError):self.candidate(counted=counted)
        runtime=copy.deepcopy(self.runtime);runtime['runtime_libraries'].append('/compiler.jar')
        with self.assertRaises(AssertionError):self.candidate(runtime=runtime)

    def test_exact_sixty_slots_one_real_source_and_balanced_leading_positions(self):
        manifests=self.manifests();slots=full.schedule_for(manifests)
        self.assertEqual(len(slots),60);self.assertEqual(len(set(x[3] for x in slots)),20)
        self.assertEqual(sum(x[2].startswith('scala-') for x in slots),30)
        self.assertEqual(sum(o['profiles'][0].startswith('scala-') for m in manifests.values() for o in m['orders']),15)
        for key in {x[3] for x in slots}:self.assertEqual(sum(x[3]==key for x in slots),3)
        for mutate in [lambda m:m.pop('nbody'),lambda m:m['nbody']['orders'][0]['profiles'].reverse(),
                lambda m:m['nbody']['profiles'].append(m['nbody']['profiles'][0]),
                lambda m:m['nbody'].update(samples=True)]:
            altered=copy.deepcopy(manifests);mutate(altered)
            with self.assertRaises(AssertionError):full.schedule_for(altered)

    def test_prepared_plan_mutations_fail_without_reading_runtime(self):
        base=dict(output='/synthetic-only/not-written',status='draft-metadata-only-not-executable',pins_verified=False,
                  policies=dict(samples=3,rss=10240,retries=False),pins={'synthetic':'1'*64})
        with patch.object(full,'build_draft',return_value=copy.deepcopy(base)):
            full.validate_plan(base)
            with self.assertRaises(AssertionError):full.validate_plan(base,prepared=True)
            prepared=dict(base,status='prepared-awaiting-independent-review',pins_verified=True)
            full.validate_plan(prepared,prepared=True)
            for mutate in [lambda p:p['policies'].update(samples=4),lambda p:p['pins'].clear(),
                           lambda p:p['policies'].update(retries=True),lambda p:p.update(chart_admission=True)]:
                changed=copy.deepcopy(prepared);mutate(changed)
                with self.assertRaises(AssertionError):full.validate_plan(changed,prepared=True)

    def test_ambient_jvm_injection_rejected_without_native_probe(self):
        for name in full.INJECTION_ENV:
            with patch.object(full.helpers,'checked_runtime'),patch.dict(full.os.environ,{name:''},clear=True):
                with self.assertRaises(AssertionError):full.checked_runtime()

    def test_qualified_sample_rejects_stderr(self):
        with patch.object(full.shared,'qualified_sample'):
            full.qualified_sample({'stderr':''},{},{},{})
            with self.assertRaises(AssertionError):full.qualified_sample({'stderr':'VM warning'},{},{},{})

    def test_missing_changed_nested_or_linked_artifact_rejected(self):
        with tempfile.TemporaryDirectory() as where:
            directory=Path(where);(directory/'nested').mkdir();path=directory/'nested/input';path.write_bytes(b'x')
            closure=[dict(directory=where,artifacts={'nested/input':dict(bytes=1,sha256='1'*64)})]
            full.verify_artifact_inventories(closure)
            path.write_bytes(b'xx')
            with self.assertRaises(AssertionError):full.verify_artifact_inventories(closure)
            path.write_bytes(b'x');(directory/'nested/terminal.json').write_text('{}')
            with self.assertRaises(AssertionError):full.verify_artifact_inventories(closure)
            (directory/'nested/terminal.json').unlink();path.unlink();path.symlink_to('/dev/null')
            with self.assertRaises(AssertionError):full.verify_artifact_inventories(closure)

    def test_metadata_change_rejected_without_plan_fallback(self):
        with tempfile.TemporaryDirectory() as where:
            path=Path(where)/'metadata.json';path.write_text('{}')
            with self.assertRaises(AssertionError):full.read_ref(dict(path=str(path),sha256='0'*64),{})
            self.assertEqual([p.name for p in Path(where).iterdir()],['metadata.json'])


def synthetic_run(directory,failure=None):
    manifests={}
    for bench in full.BENCHES:
        manifests[bench]=dict(benchmark=bench,samples=3,orders=full.orders_for(bench),profiles=[
            dict(id='scala-'+bench+'-jvm-v1',key='scala-'+bench+'-jvm-v1',benchmark=bench,language='scala',source_sha256='1'*64),
            dict(id='mech-aot-control',key=bench+':scala-full-study:mech-control',benchmark=bench,language='mech',source_sha256='2'*64)])
    plan=dict(manifests=manifests,prerequisite_artifact_closures=[]);rows=full.initial_rows(plan)
    report=dict(status='complete',programs=rows,attempts=[],active=None,skipped_failed_profile_slots=[],
        isolated_failed_profiles=[],completed_benchmarks=[],independent_supervisors=[],validated_attempt_artifacts={},
        descriptive_provenance=[],kernel_identity_observation_gaps=[])
    snapshots={};base=datetime(2027,1,1,tzinfo=timezone.utc)
    for bench,round_index,identity,key in full.schedule_for(manifests):
        row=rows[key]
        if row.get('full_failure'):
            report['skipped_failed_profile_slots'].append(dict(benchmark=bench,round=round_index,id=identity,key=key));continue
        number=len(report['attempts'])+1
        attempt=dict(attempt=number,benchmark=bench,round=round_index,id=identity,key=key,qualified=key!=failure,
            seconds=1.0+number/100,validation=dict(reference_match=True),
            started_at=(base+timedelta(seconds=number*2)).isoformat(),finished_at=(base+timedelta(seconds=number*2+1)).isoformat(),
            supervised_native_group=dict(pid=number+100,pgid=number+100,inherited_common_mutex=True,command=['/synthetic-only']))
        paths=full.attempt_paths(directory,attempt);attempt.update(result_path=str(paths[0]),supervisor_result_path=str(paths[1]))
        for path in paths:
            path.parent.mkdir(exist_ok=True);path.write_text(json.dumps(attempt));snapshots[str(path)]=full.sha(path)
        report['independent_supervisors'].append(dict(path=str(paths[2]),sha256=snapshots[str(paths[2])],status='returned'))
        report['attempts'].append(attempt);row['attempts'].append(number)
        if attempt['qualified']:
            row['samples_seconds'].append(attempt['seconds']);row['sample_validation'].append(attempt['validation'])
            row['measurement_status']='measured' if len(row['samples_seconds'])==3 else 'partial'
        else:
            row.update(full_failure=attempt,measurement_status='failed-full-workload');report['isolated_failed_profiles'].append(key)
        if full.summarize(rows,manifests[bench]) and bench not in report['completed_benchmarks']:report['completed_benchmarks'].append(bench)
    if failure:report['status']='complete-with-unqualified-profiles'
    report['validated_attempt_artifacts']=dict(snapshots);full.refresh_attempt_accounting(report)
    def save(path,value):path.write_text(json.dumps(value))
    guard=SimpleNamespace(OUT=directory,REPORT=directory/'report.json',save=save);save(guard.REPORT,report)
    return plan,report,snapshots,guard


class ClosureFaults(unittest.TestCase):
    def test_complete_and_isolated_failure_ledgers(self):
        with tempfile.TemporaryDirectory() as where:
            for index,failure in enumerate((None,'fasta:scala-full-study:mech-control','scala-nbody-jvm-v1')):
                directory=Path(where)/str(index);directory.mkdir()
                plan,report,_,_=synthetic_run(directory,failure);full.check_success_ledger(plan,report)
                self.assertEqual(len(report['attempts'])+len(report['skipped_failed_profile_slots']),60)
                if failure:
                    self.assertNotIn('median_seconds',report['programs'][failure])
                    self.assertEqual(len(report['skipped_failed_profile_slots']),2)
                for mutate in [lambda d:d['attempts'].reverse(),lambda d:d['programs'][next(iter(d['programs']))]['samples_seconds'].append(999),
                               lambda d:d.update(active={'pid':10}),lambda d:d['independent_supervisors'].clear()]:
                    changed=copy.deepcopy(report);mutate(changed)
                    if not changed['independent_supervisors']:continue  # Covered by the terminal closure below.
                    with self.assertRaises(AssertionError):full.check_success_ledger(plan,changed)

    def test_returned_attempt_is_committed_with_masked_ledger_and_snapshot(self):
        with tempfile.TemporaryDirectory() as where:
            directory=Path(where);plan,old,snapshots,guard=synthetic_run(directory)
            attempt=old['attempts'][0];manifest=plan['manifests'][attempt['benchmark']]
            rows=full.initial_rows(plan);row=rows[attempt['key']];events=[];held=[False]
            report=dict(programs=rows,attempts=[],active={'pid':101},isolated_failed_profiles=[],completed_benchmarks=[],
                descriptive_provenance=[],kernel_identity_observation_gaps=[])
            @contextmanager
            def atomic():
                self.assertFalse(held[0]);held[0]=True;events.append('blocked')
                try:yield
                finally:held[0]=False;events.append('restored')
            def save(path,value):
                self.assertTrue(held[0]);events.append('saved');path.write_text(json.dumps(value))
            def checked(*args):
                self.assertTrue(held[0]);events.append('validated')
                return {str(p):snapshots[str(p)] for p in full.attempt_paths(directory,attempt)},[],[]
            guard.save=save;harness=SimpleNamespace(execution_fingerprint=lambda row:{})
            with patch.object(full,'check_attempt',checked),patch.object(full,'qualified_sample'):
                full.record_attempt(SimpleNamespace(lifecycle_atomic=atomic),guard,harness,report,row,manifest,
                    (attempt['benchmark'],attempt['round'],attempt['id'],attempt['key']),{}, {},attempt)
            self.assertEqual(events,['blocked','saved','validated','saved','restored'])
            saved=json.loads(guard.REPORT.read_bytes());self.assertIsNone(saved['active'])
            self.assertEqual(saved['qualified_samples'],1);self.assertEqual(len(saved['validated_attempt_artifacts']),3)

    def test_invalid_receipt_retains_raw_attempt_before_validation_failure(self):
        with tempfile.TemporaryDirectory() as where:
            directory=Path(where);plan,old,_,guard=synthetic_run(directory);attempt=old['attempts'][0]
            rows=full.initial_rows(plan);report=dict(programs=rows,attempts=[],active={'pid':101},isolated_failed_profiles=[],
                completed_benchmarks=[],descriptive_provenance=[],kernel_identity_observation_gaps=[])
            @contextmanager
            def atomic():yield
            with patch.object(full,'check_attempt',side_effect=AssertionError('unowned native')):
                with self.assertRaisesRegex(AssertionError,'unowned native'):
                    full.record_attempt(SimpleNamespace(lifecycle_atomic=atomic),guard,None,report,rows[attempt['key']],
                        plan['manifests'][attempt['benchmark']],None,{}, {},attempt)
            saved=json.loads(guard.REPORT.read_bytes())
            self.assertEqual(saved['attempts'],[attempt]);self.assertEqual(saved['registered_native_attempts'],[1])
            self.assertEqual(saved['qualified_samples'],0)

    def finish(self,plan,report,snapshots,guard,late_change=None):
        def checked(output,attempt,*args):return {str(p):snapshots[str(p)] for p in full.attempt_paths(output,attempt)},[],[]
        calls=[0];original_inventory=full.r.inventory
        def inventory(directory):
            calls[0]+=1
            # Successful first call checks the exact native/report inventory.
            # The second starts terminal hashing after independent receipt replay.
            if calls[0]==2 and late_change:late_change()
            return original_inventory(directory)
        with patch.object(full,'check_attempt',checked),patch.object(full,'check_execution_inputs'), \
             patch.object(full,'verify_lock'),patch.object(full.r,'inventory',inventory):
            full.finish(plan,report,{},snapshots,guard,None,None)

    def test_final_closure_replays_every_snapshot_and_supervisor(self):
        with tempfile.TemporaryDirectory() as where:
            plan,report,snapshots,guard=synthetic_run(Path(where));self.finish(plan,report,snapshots,guard)
            terminal=json.loads((guard.OUT/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'complete');self.assertEqual(terminal['validated_attempt_artifacts'],snapshots)
            self.assertEqual(terminal['saved_attempts'],60);self.assertFalse(terminal['full_timings_qualified'])

    def test_missing_outer_membership_fails_closed(self):
        with tempfile.TemporaryDirectory() as where:
            plan,report,snapshots,guard=synthetic_run(Path(where));report['independent_supervisors'].pop()
            with self.assertRaises(AssertionError):self.finish(plan,report,snapshots,guard)
            terminal=json.loads((guard.OUT/'terminal.json').read_bytes());self.assertEqual(terminal['status'],'failed-terminal-integrity')

    def test_late_receipt_change_cannot_become_new_accepted_digest(self):
        with tempfile.TemporaryDirectory() as where:
            plan,report,snapshots,guard=synthetic_run(Path(where));target=Path(next(iter(snapshots)))
            with self.assertRaises(AssertionError):
                self.finish(plan,report,snapshots,guard,lambda:target.write_text('{}'))
            terminal=json.loads((guard.OUT/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed-terminal-integrity')
            self.assertEqual(terminal['validated_attempt_artifacts'][str(target)],snapshots[str(target)])
            self.assertTrue(terminal['integrity_errors'])

    def test_extra_nested_artifact_and_overlapping_intervals_rejected(self):
        with tempfile.TemporaryDirectory() as where:
            for index,kind in enumerate(('extra','overlap')):
                directory=Path(where)/str(index);directory.mkdir();plan,report,snapshots,guard=synthetic_run(directory)
                if kind=='extra':(directory/'outer-supervisor/terminal.json').write_text('{}')
                else:report['attempts'][1]['started_at']=report['attempts'][0]['started_at']
                with self.assertRaises(AssertionError):self.finish(plan,report,snapshots,guard)
                self.assertEqual(json.loads((directory/'terminal.json').read_bytes())['status'],'failed-terminal-integrity')


if __name__=='__main__':unittest.main()
