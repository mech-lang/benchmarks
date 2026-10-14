"""Saved-receipt and synthetic continuation tests; no native/runtime hashing."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('remaining50_subject',HERE/'prolog_remaining_full.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def read(path):
    return c.p.strict_json(path.read_bytes())


class Remaining(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.prior = read(c.PRIOR/'plan-v1.json')
        cls.previous = read(c.l.OLD/'plan.json')
        cls.report = read(c.PRIOR/'run-v1/report.json')
        cls.terminal = read(c.PRIOR/'run-v1/terminal.json')
        cls.durable = {n:read(c.JOB/(n+'.json')) for n in
                       ('request','launch','worker-started','command-started','terminal')}
        cls.request = read(c.PRIOR/'priority-interpreter-stop-v1/request.json')
        cls.closure = read(c.PRIOR/'priority-interpreter-stop-v1/closure.json')
        cls.artifacts = {path:read(Path(path)) for path in cls.report['validated_attempt_artifacts']}

    def check_stopped(self, **changes):
        values = dict(plan=self.prior,previous=self.previous,report=self.report,terminal=self.terminal,
            durable=self.durable,request=self.request,closure=self.closure,artifacts=self.artifacts)
        values.update(changes)
        return c.stopped_checks(**values)

    def continuation(self):
        retained = self.check_stopped()
        return dict(manifests=self.prior['manifests'],schedule=self.prior['schedule'],
            retained_slots=self.prior['schedule'][:40],remaining_slots=self.prior['schedule'][40:],
            full_processes=50,retained_qualified_samples=40,new_prolog_processes=33,new_mech_processes=17,
            retained=retained)

    def test_actual_31_closure_replays_all40(self):
        retained = self.check_stopped()
        self.assertEqual(len(retained['reused_samples']),40)
        self.assertEqual(retained['completed_benchmarks'],['regexredux','revcomp','pidigits','spectralnorm'])
        self.assertEqual([s['cohort'] for s in retained['reused_samples']],['original-full90']*9+['linear-full81']*31)
        self.assertEqual(retained['kernel_identity_observation_gaps'],[])

    def test_exact_remaining50_no_repeat(self):
        plan=self.continuation();c.validate_partition(plan)
        self.assertEqual(plan['remaining_slots'][0],['mandelbrot',2,'mech-aot-control','mandelbrot:prolog-full-study:mech-control'])
        self.assertEqual(len({tuple(s) for s in plan['schedule']}),90)
        self.assertFalse(set(map(tuple,plan['retained_slots'])) & set(map(tuple,plan['remaining_slots'])))
        rows=c.initial_rows(plan)
        self.assertEqual(sum(len(r['samples_seconds']) for r in rows.values()),40)
        self.assertTrue(all(not r['attempts'] for r in rows.values()))
        self.assertEqual(sum(len(r['retained_attempts']) for r in rows.values()),40)
        self.assertEqual(sum(s[2].startswith('prolog-') for s in plan['remaining_slots']),33)

    def test_reorder_duplicate_omission_or_extra_slot_rejected(self):
        original=self.continuation()
        for mutation in ('reverse','repeat','omit','extra','retained'):
            plan=copy.deepcopy(original)
            if mutation=='reverse':plan['remaining_slots'].reverse()
            if mutation=='repeat':plan['remaining_slots'][1]=plan['remaining_slots'][0]
            if mutation=='omit':plan['remaining_slots'].pop()
            if mutation=='extra':plan['remaining_slots'].append(plan['retained_slots'][0])
            if mutation=='retained':plan['retained']['reused_samples'][0]['slot']=plan['remaining_slots'][0]
            with self.subTest(mutation=mutation),self.assertRaises((ValueError,AssertionError)):
                c.validate_partition(plan)

    def test_native_failure_or_interrupted_attempt_not_retained(self):
        for field,value in [('qualified',False),('attempt',32),('sampler_wait_status',2)]:
            report=copy.deepcopy(self.report);report['attempts'][-1][field]=value
            with self.subTest(field=field),self.assertRaises((ValueError,AssertionError)):
                self.check_stopped(report=report)
        closure=dict(self.closure,interrupted_native_attempts=1)
        with self.assertRaises(ValueError):self.check_stopped(closure=closure)

    def test_stopped_status_never_normalized_success(self):
        report=dict(self.report,status='complete')
        with self.assertRaises(ValueError):self.check_stopped(report=report)
        terminal=dict(self.terminal,integrity_errors=[dict(error='changed')])
        with self.assertRaises(ValueError):self.check_stopped(terminal=terminal)
        report=dict(self.report,error='timeout')
        with self.assertRaises(ValueError):self.check_stopped(report=report)

    def test_exact_argv_cwd_birth_parent_and_signal(self):
        for mutation in ('added-u','missing-B','cwd','birth','parent','signal','exit','retry'):
            d=copy.deepcopy(self.durable)
            if mutation=='added-u':d['request']['command'].insert(4,'-u')
            if mutation=='missing-B':d['launch']['command'].remove('-B')
            if mutation=='cwd':d['command-started']['cwd']='/tmp'
            if mutation=='birth':d['terminal']['command_identity']['listing']=d['terminal']['command_identity']['listing'].replace('07:51:51','07:51:52')
            if mutation=='parent':d['command-started']['command_identity']['listing']=d['command-started']['command_identity']['listing'].replace('66708 66704','66708 1')
            if mutation=='signal':d['terminal']['stop_signals']=[2]
            if mutation=='exit':d['terminal']['exit_code']=0
            if mutation=='retry':d['request']['automatic_retry']=True
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.check_stopped(durable=d)

    def test_missing_native_outer_or_extra_receipt(self):
        for mutation in ('missing','extra','unowned','remaining'):
            artifacts=copy.deepcopy(self.artifacts)
            outer=str(c.attempt_paths(c.PRIOR/'run-v1',self.report['attempts'][0])[2])
            if mutation=='missing':del artifacts[outer]
            if mutation=='extra':artifacts['/unexpected.json']={}
            if mutation=='unowned':
                child=next(iter(artifacts[outer]['owned_sampler_children']))
                artifacts[outer]['owned_sampler_children'][child]['identity']['ppid']=1
                artifacts[outer]['owned_groups'][child]['ppid']=1
            if mutation=='remaining':artifacts[outer]['cleanup_errors']=['unreaped']
            with self.subTest(mutation=mutation),self.assertRaises((KeyError,ValueError)):
                self.check_stopped(artifacts=artifacts)

    def test_modified_summary_or_snapshot_rejected(self):
        key=self.report['attempts'][0]['key']
        for mutation in ('seconds','validation','source','snapshot','unconfirmed'):
            report=copy.deepcopy(self.report)
            if mutation=='seconds':report['programs'][key]['samples_seconds'][0]+=1
            if mutation=='validation':report['programs'][key]['sample_validation'][0]={}
            if mutation=='source':report['programs'][key]['source_sha256']='0'*64
            if mutation=='snapshot':report['validated_attempt_artifacts'][next(iter(report['validated_attempt_artifacts']))]='0'*64
            if mutation=='unconfirmed':report['native_launch_unconfirmed_attempts']=[31]
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):self.check_stopped(report=report)

    def test_nonfinite_and_boolean_samples_rejected(self):
        for value in (float('nan'),float('inf'),True,-1):
            report=copy.deepcopy(self.report);report['attempts'][0]['seconds']=value
            with self.subTest(value=value),self.assertRaises(ValueError):self.check_stopped(report=report)

    def successful(self,plan,failed_key=None):
        rows=c.initial_rows(plan)
        report=dict(programs=rows,attempts=[],skipped_failed_profile_slots=[],isolated_failed_profiles=[],
            active=None,completed_benchmarks=list(c.f.BENCHES),native_launch_unconfirmed_attempts=[],
            retained_qualified_samples=40,repeated_completed_samples=0)
        for slot in plan['remaining_slots']:
            bench,round_,identifier,key=slot
            if rows[key].get('full_failure'):
                report['skipped_failed_profile_slots'].append(dict(benchmark=bench,round=round_,id=identifier,key=key))
                continue
            i=len(report['attempts'])+1
            a=dict(benchmark=bench,round=round_,id=identifier,key=key,attempt=i,qualified=True,
                   seconds=float(i+1),validation={'test':'synthetic'},
                   supervised_native_group=dict(pid=1000+i,pgid=1000+i,inherited_common_mutex=True,command=['subject']))
            report['attempts'].append(a);row=rows[key];row['attempts'].append(i)
            if key==failed_key:
                a['qualified']=False
                row['full_failure']=copy.deepcopy(a);row['measurement_status']='failed-full-workload'
                report['isolated_failed_profiles'].append(key)
                continue
            row['samples_seconds'].append(a['seconds']);row['sample_validation'].append(a['validation'])
            row['measurement_status']='measured' if len(row['samples_seconds'])==3 else 'partial'
        for manifest in plan['manifests'].values():self.assertTrue(c.summarize(rows,manifest))
        c.f.refresh_attempt_accounting(report)
        return report

    def test_complete90_replays40plus50(self):
        plan=self.continuation();report=self.successful(plan);c.check_success_ledger(plan,report)
        self.assertEqual(report['qualified_samples'],90)
        self.assertEqual(report['full_performance_runs'],50)
        self.assertEqual(len(report['programs']),30)
        self.assertTrue(all(len(r['samples_seconds'])==3 for r in report['programs'].values()))

    def test_isolated_failure_keeps_completed_samples_and_skips_only_its_later_slot(self):
        plan=self.continuation();key=plan['remaining_slots'][0][3]
        report=self.successful(plan,failed_key=key);c.check_success_ledger(plan,report)
        self.assertEqual(len(report['attempts']),49)
        self.assertEqual(report['qualified_samples'],88)
        self.assertEqual(len(report['programs'][key]['samples_seconds']),1)
        self.assertNotIn('median_seconds',report['programs'][key])
        self.assertEqual(report['programs'][key]['time_x_mech'],None)
        self.assertEqual([s['key'] for s in report['skipped_failed_profile_slots']],[key])
        self.assertEqual(sum(len(r['retained_attempts']) for r in report['programs'].values()),40)

    def test_completed_snapshot_cannot_change_during_finalization(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory=Path(tmp);artifact=directory/'sample.json';artifact.write_text('{}')
            lockpath=directory/'lock';lockpath.touch()
            report=dict(status='stopped-unqualified',attempts=[],active=None,programs={},
                skipped_failed_profile_slots=[])
            guard=SimpleNamespace(OUT=directory,REPORT=directory/'report.json',
                save=lambda path,value:path.write_text(json.dumps(value)))
            identity=SimpleNamespace(st_dev=lockpath.stat().st_dev,st_ino=79859134)
            with lockpath.open('rb') as lock, patch.object(c.f,'LOCK',SimpleNamespace(stat=lambda:identity)), \
                    patch.object(c.os,'fstat',return_value=identity):
                with self.assertRaises((ValueError,AssertionError)):
                    c.finish({},report,{}, {str(artifact):'0'*64},guard,lock)
            self.assertEqual(report['status'],'failed-terminal-integrity')
            self.assertFalse(report['pins_unchanged_at_end'])

    def test_future_reordered_or_repeated_attempt_rejected(self):
        plan=self.continuation();report=self.successful(plan)
        report['attempts'][0],report['attempts'][1]=report['attempts'][1],report['attempts'][0]
        for i,a in enumerate(report['attempts'],1):a['attempt']=i
        with self.assertRaises(ValueError):c.check_success_ledger(plan,report)
        report=self.successful(plan);report['attempts'][0].update(zip(('benchmark','round','id','key'),plan['retained_slots'][-1]))
        with self.assertRaises(ValueError):c.check_success_ledger(plan,report)

    def test_skip_without_prior_failure_rejected(self):
        plan=self.continuation();report=self.successful(plan)
        a=report['attempts'].pop();report['skipped_failed_profile_slots'].append({k:a[k] for k in ('benchmark','round','id','key')})
        c.f.refresh_attempt_accounting(report)
        with self.assertRaises(ValueError):c.check_success_ledger(plan,report)

    def test_no_success_report_can_drop_retained_or_validation(self):
        plan=self.continuation();report=self.successful(plan)
        report['programs'][plan['retained_slots'][0][3]]['retained_attempts']=[]
        with self.assertRaises(ValueError):c.check_success_ledger(plan,report)

    def test_fresh_paths_refuse_existing_plan_or_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            packet=Path(tmp);plan=packet/'plan.json';out=packet/'run-v1'
            with patch.object(c,'PACKET',packet):
                c.fresh_paths(plan,out);out.mkdir()
                with self.assertRaises(ValueError):c.fresh_paths(plan,out)
                out.rmdir();plan.write_text('{}')
                with self.assertRaises(ValueError):c.fresh_paths(plan,out)


if __name__=='__main__':unittest.main()
