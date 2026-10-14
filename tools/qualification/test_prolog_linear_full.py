"""Pure/source and saved-receipt tests; no native launches or runtime pin hashes."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('linear_full_test_subject', HERE/'prolog_linear_full.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def read(path):
    return json.loads(path.read_bytes())


class Continuation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = read(c.OLD/'plan.json')
        cls.old_report = read(c.OLD/'results/report.json')
        cls.old_terminal = read(c.OLD/'results/terminal.json')
        cls.durable = read(c.OLD/'owned-jobs/full90/terminal.json')
        cls.cancel = read(c.OLD/'cancellation-v1.json')
        cls.closure = read(c.OLD/'cancellation-review-v1.json')
        source_plan = read(c.LINEAR/'source-counts-v1/plan-v1.json')
        cls.linear = dict(bounded=source_plan['prerequisite'],
            required_work_review=dict(path=str(c.LINEAR/'compiled-work-review.md'),sha256=c.WORK_SHA,status='passed'),
            source_count_review=dict(path=str(c.LINEAR/'source-counts-v1/source-count-review.json'),sha256=c.COUNT_SHA),
            projection=dict(path=str(c.LINEAR/'source-counts-v1/run-v1/candidate-original-source/projection.json'),
                sha256=c.FIXED[c.LINEAR/'source-counts-v1/run-v1/candidate-original-source/projection.json']))
        manifests = c.manifests_for(cls.old, cls.linear)
        slots = c.schedule_for(manifests)
        cls.plan = dict(manifests=manifests, remaining_slots=slots[9:], retained=dict(reused_samples=[
            dict(slot=cls.old['schedule'][i], original_attempt=i+1, seconds=a['seconds'],validation=a['validation'])
            for i,a in enumerate(cls.old_report['attempts'][:9])]))

    def test_exact_81_rotation_and_language_counts(self):
        slots = c.schedule_for(self.plan['manifests'])
        self.assertEqual(slots[:9], self.old['schedule'][:9])
        self.assertEqual(len(slots[9:]),81)
        by_key = {r['key']:r for m in self.plan['manifests'].values() for r in m['profiles']}
        self.assertEqual(sum(by_key[s[3]]['language']=='prolog' for s in slots[9:]),54)
        self.assertEqual(sum(by_key[s[3]]['language']=='mech' for s in slots[9:]),27)
        self.assertFalse(any(s[0]=='regexredux' for s in slots[9:]))

    def test_only_two_revcomp_rows_change(self):
        for bench,manifest in self.old['manifests'].items():
            actual = self.plan['manifests'][bench]
            if bench != 'revcomp':
                self.assertEqual(actual,manifest)
            else:
                self.assertEqual(actual['profiles'][2],manifest['profiles'][2])
                self.assertEqual({k:v for k,v in actual.items() if k not in ('orders','profiles')},
                                 {k:v for k,v in manifest.items() if k not in ('orders','profiles')})

    def test_alias_same_compiled_work_not_independent_optimization(self):
        a,b = self.plan['manifests']['revcomp']['profiles'][:2]
        for key in ('source','source_sha256','command','compiled_artifact','source_bundle','runtime_environment','cwd'):
            self.assertEqual(a[key],b[key])
        self.assertEqual(b['source_alias_of'],a['id'])
        self.assertIn('no distinct optimization admitted',b['optimization_claim'])
        self.assertEqual((a['loc'],a['physical_loc']),(242,146))
        self.assertEqual(a['command'][-2:],['-g','clbg_revcomp_linear:run'])
        self.assertEqual(a['command'].count('-s'),1)
        self.assertNotIn('-l',a['command'])

    def test_runtime_change_rejected(self):
        linear = copy.deepcopy(self.linear);linear['bounded']['environment'] = {}
        with self.assertRaisesRegex(AssertionError,'retained runtime'):
            c.manifests_for(self.old,linear)

    def test_rotation_and_duplicate_rejected(self):
        manifests = copy.deepcopy(self.plan['manifests'])
        manifests['revcomp']['orders'][0]['profiles'].reverse()
        with self.assertRaises(AssertionError):c.schedule_for(manifests)
        manifests = copy.deepcopy(self.plan['manifests'])
        manifests['revcomp']['profiles'][1]['id'] = manifests['revcomp']['profiles'][0]['id']
        with self.assertRaises(AssertionError):c.schedule_for(manifests)

    def test_actual_cancelled_boundary(self):
        slots,_ = c.retained_checks(self.old,self.old_report,self.old_terminal,self.durable,self.cancel,self.closure)
        self.assertEqual(slots,self.old['schedule'])

    def test_cancelled_attempt_cannot_be_reused_or_relabelled(self):
        report = copy.deepcopy(self.old_report);report['attempts'][9]['qualified']=True
        with self.assertRaises(AssertionError):
            c.retained_checks(self.old,report,self.old_terminal,self.durable,self.cancel,self.closure)
        cancel = dict(self.cancel,cancellation_is_timeout=True)
        with self.assertRaises(AssertionError):
            c.retained_checks(self.old,self.old_report,self.old_terminal,self.durable,cancel,self.closure)
        closure = dict(self.closure,remaining_owned_processes_or_groups=[83209])
        with self.assertRaises(AssertionError):
            c.retained_checks(self.old,self.old_report,self.old_terminal,self.durable,self.cancel,closure)

    def test_actual_nine_receipt_semantics_and_environment(self):
        # Saved small JSON only: no hashing of runtime, inputs, or old closure.
        profiles = {r['key']:r for m in self.old['manifests'].values() for r in m['profiles']}
        for slot,attempt in zip(self.old['schedule'][:9],self.old_report['attempts'][:9]):
            raw,supervised,outer = [read(p) for p in c.attempt_paths(c.OLD/'results',attempt)]
            c.r.check_attempt(attempt,raw,supervised,slot,profiles[slot[3]],self.old['manifests'][slot[0]],
                              c.fingerprint_pins(self.old,self.old_terminal['prerequisite_pins']),[])
            c.r.check_outer(outer,attempt,83209)
            self.assertTrue(attempt['valid_environment'])
            damaged = copy.deepcopy(attempt);damaged['valid_environment']=False
            with self.assertRaises(ValueError):
                c.r.check_attempt(damaged,raw,damaged,slot,profiles[slot[3]],self.old['manifests'][slot[0]],
                                  c.fingerprint_pins(self.old,self.old_terminal['prerequisite_pins']),[])

    def test_actual_count_owner_review_and_unchanged_producer_scope(self):
        review = read(c.LINEAR/'source-counts-v1/source-count-review.json')
        projection = read(c.LINEAR/'source-counts-v1/run-v1/candidate-original-source/projection.json')
        c.count_review_checks(review,projection)
        bad = dict(review,canonical_loc=241)
        with self.assertRaises(AssertionError):c.count_review_checks(bad,projection)
        bad = dict(projection,canonical_LOC_admitted=True)
        with self.assertRaises(AssertionError):c.count_review_checks(review,bad)

    def test_initial_rows_have_exact_reused_samples_and_separate_attempt_namespace(self):
        rows = c.initial_rows(self.plan)
        self.assertEqual(sum(len(r['samples_seconds']) for r in rows.values()),9)
        for key,seconds in self.cancel['preserved_completed_samples'].items():
            self.assertEqual(rows[key]['samples_seconds'],seconds)
            self.assertEqual(rows[key]['attempts'],[])
            self.assertEqual(len(rows[key]['retained_attempts']),3)
        self.assertEqual(rows['regexredux:prolog-regexredux-compact']['median_seconds'],19.334585)

    def report(self, fail=None):
        rows=c.initial_rows(self.plan)
        report=dict(programs=rows,attempts=[],skipped_failed_profile_slots=[],isolated_failed_profiles=[],active=None,
                    retained_qualified_samples=9,repeated_completed_samples=0,completed_benchmarks=['regexredux'])
        for slot in self.plan['remaining_slots']:
            bench,round_,identifier,key=slot;row=rows[key]
            if row.get('full_failure'):
                report['skipped_failed_profile_slots'].append(dict(benchmark=bench,round=round_,id=identifier,key=key))
                continue
            index=len(report['attempts'])+1
            a=dict(benchmark=bench,round=round_,id=identifier,key=key,attempt=index,
                   qualified=key!=fail,seconds=index/10,validation={'reference_match':True},
                   supervised_native_group=dict(pid=1000+index,pgid=1000+index,inherited_common_mutex=True,command=['subject']))
            report['attempts'].append(a);row['attempts'].append(index)
            if a['qualified']:
                row['samples_seconds'].append(a['seconds']);row['sample_validation'].append(a['validation'])
                row['measurement_status']='measured' if len(row['samples_seconds'])==3 else 'partial'
            else:
                row['full_failure']=a;row['measurement_status']='failed-full-workload';report['isolated_failed_profiles'].append(key)
            if c.summarize(rows,self.plan['manifests'][bench]) and bench not in report['completed_benchmarks']:
                report['completed_benchmarks'].append(bench)
        c.f.refresh_attempt_accounting(report)
        return report

    def test_full81_summary_replays_to_combined90(self):
        report=self.report();c.check_success_ledger(self.plan,report)
        self.assertEqual(report['full_performance_runs'],81)
        self.assertEqual(report['qualified_samples'],90)

    def test_isolated_failure_skips_only_later_same_profile(self):
        key=self.plan['remaining_slots'][0][3]
        report=self.report(fail=key);c.check_success_ledger(self.plan,report)
        self.assertEqual(len(report['skipped_failed_profile_slots']),2)
        self.assertEqual(report['full_performance_runs'],79)
        self.assertEqual(report['qualified_samples'],87)
        self.assertIsNone(report['programs'][key]['time_x_mech'])
        wrong=copy.deepcopy(report);wrong['skipped_failed_profile_slots'][0]['key']='unrelated'
        with self.assertRaises(AssertionError):c.check_success_ledger(self.plan,wrong)

    def test_missing_duplicate_or_modified_summary_rejected(self):
        report=self.report();report['attempts'].pop()
        with self.assertRaises(AssertionError):c.check_success_ledger(self.plan,report)
        report=self.report();report['attempts'].append(copy.deepcopy(report['attempts'][0]))
        with self.assertRaises(AssertionError):c.check_success_ledger(self.plan,report)
        report=self.report();report['programs'][self.plan['remaining_slots'][0][3]]['median_seconds']=0
        with self.assertRaises(AssertionError):c.check_success_ledger(self.plan,report)

    def test_changed_validated_bytes_fail_terminal_without_success(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp);artifact=directory/'receipt.json';artifact.write_text('before')
            snapshot={str(artifact):c.sha(artifact)};artifact.write_text('after')
            report=self.report();report.update(status='stopped-unqualified',active=None)
            guard=SimpleNamespace(OUT=directory,REPORT=directory/'report.json',save=lambda p,v:p.write_text(json.dumps(v)))
            # Simulate the recorded common-lock identity without acquiring any lock.
            stat=c.f.LOCK.stat()
            with patch.object(c.os,'fstat',return_value=stat):
                with self.assertRaisesRegex(AssertionError,'Terminal integrity'):
                    c.finish(self.plan,report,{},snapshot,guard,SimpleNamespace(fileno=lambda:0))
            terminal=read(directory/'terminal.json')
            self.assertEqual(terminal['status'],'failed-terminal-integrity')
            self.assertTrue(terminal['integrity_errors'])
            self.assertFalse(terminal['chart_admission'])
            self.assertFalse(terminal['full_timings_qualified'])

    def test_closure_excludes_only_top_level_terminal(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp);(directory/'terminal.json').write_text('{}')
            (directory/'nested').mkdir();(directory/'nested/terminal.json').write_text('{}')
            found=c.file_inventory(directory,exclude=('terminal.json',))
            self.assertNotIn(str(directory/'terminal.json'),found)
            self.assertIn(str(directory/'nested/terminal.json'),found)

    def test_edit_during_terminal_inventory_is_not_adopted_as_validated_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            directory=Path(temp);artifact=directory/'receipt.json';artifact.write_text('validated')
            snapshot={str(artifact):c.sha(artifact)}
            report=self.report();report.update(status='stopped-unqualified',active=None)
            guard=SimpleNamespace(OUT=directory,REPORT=directory/'report.json',save=lambda p,v:p.write_text(json.dumps(v)))
            inventory=c.file_inventory
            def changed_inventory(path):
                artifact.write_text('changed during inventory')
                return inventory(path)
            with patch.object(c.os,'fstat',return_value=c.f.LOCK.stat()), \
                    patch.object(c,'file_inventory',side_effect=changed_inventory):
                with self.assertRaisesRegex(AssertionError,'Terminal integrity'):
                    c.finish(self.plan,report,{},snapshot,guard,SimpleNamespace(fileno=lambda:0))
            terminal=read(directory/'terminal.json')
            self.assertEqual(terminal['status'],'failed-terminal-integrity')
            self.assertTrue(any('during terminal inventory' in e['error'] for e in terminal['integrity_errors']))
            self.assertEqual(terminal['available_evidence_pins'][str(guard.REPORT)],c.sha(guard.REPORT))

    def test_fingerprint_physical_pin_overrides_historical_alias(self):
        self.assertEqual(c.fingerprint_pins({'historical_pins':{'a':'old','b':'sealed'}},{'a':'current'}),
                         {'a':'current','b':'sealed'})

    def test_frozen_supervisor_cleanup_context_exists(self):
        source=(HERE/'prolog_supervisor.py').read_text()
        self.assertIn('def lifecycle_atomic():',source)
        self.assertIn('with supervisor.lifecycle_atomic():',(HERE/'prolog_linear_full.py').read_text())


if __name__=='__main__':unittest.main()
