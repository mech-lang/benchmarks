"""Final8 boundary checks using synthetic files and retained metadata only."""
import copy
from contextlib import nullcontext
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module
a=load('final8_source',HERE/'rebol_bounded_final.py')
base=load('final8_base',a.BASE)
t=load('final8_synthetic',HERE/'test_rebol_bounded.py')
e=t.e
OWN=a.digest(Path(a.__file__).read_bytes())
def controller():return a.load_controller(OWN)
def document(ref):return json.loads(Path(ref['path']).read_bytes())
def save(path,value):path.write_bytes(t.r.encoded(value))
def draft(output):
    plan=t.draft_plan(output,t.slots(output)[141:])
    plan.update(final_adapter=dict(path=str(Path(a.__file__)),sha256=OWN),
        prior_continuation_stage=dict(report_finished_at='2026-10-13T00:00:00+00:00'))
    return plan

class FinalEight(unittest.TestCase):
    def test_loader_preserves_current_schedule_and_observer(self):
        r=controller();old=base.load_controller(a.BASE_SHA)
        self.assertEqual(r.__file__,old.__file__)
        for name in ('schedule','source_selection','native_capture','checked_case','verify_inputs'):
            self.assertEqual(getattr(r,name).__code__,getattr(old,name).__code__,name)
        self.assertTrue(a.PACKET.is_relative_to(base.PACKET))
        with self.assertRaises(AssertionError):a.load_controller('0'*64)

    def test_suffix_is_only_eight_unstarted_cases(self):
        slots=t.slots(Path('/fresh'))[23:];before=copy.deepcopy(slots)
        final=a.final_schedule(slots)
        self.assertEqual(final,slots[118:]);self.assertEqual(slots,before)
        self.assertEqual([s['expected_exit'] for s in final],[1]*6+[0,0])
        self.assertEqual([s['directory'][:3] for s in final],[str(i) for i in range(141,149)])
        for fault in ('repeat-accepted','remove','success-as-rejection'):
            bad=copy.deepcopy(slots)
            if fault=='repeat-accepted':bad[117],bad[118]=bad[118],bad[117]
            elif fault=='remove':bad.pop()
            else:bad[-1]['expected_exit']=1
            with self.subTest(fault=fault),self.assertRaises(AssertionError):a.final_schedule(bad)

    def test_actual_failed_ledger_stays_failed_and_counts_are_exact(self):
        r=controller();review=document(a.PRIOR)
        plan,report,terminal=[document(a.PRIOR_REFS[name]) for name in ('plan','report','terminal')]
        a.prior_ledger(r,review,plan,report,terminal,plan['primitive_review'])
        for key,value in (('successful_output_contracts',118),('failed_cases',0),('benchmark_correctness_qualified',True)):
            with self.subTest(key=key),self.assertRaises(AssertionError):
                a.prior_ledger(r,dict(review,**{key:value}),plan,report,terminal,plan['primitive_review'])
        for key,value in (('status',a.SUCCESS),('captures',report['captures'][:-1]),('pins',{}),('error','different failure')):
            with self.subTest(key=key),self.assertRaises(AssertionError):
                a.prior_ledger(r,review,plan,dict(report,**{key:value}),terminal,plan['primitive_review'])

    def test_retained_acceptance_is_exact_and_does_not_promote_observer(self):
        r=controller();approval=document(a.ACCEPTANCE);review=document(a.PRIOR)
        capture=approval['capture'];snapshot=approval['capture_files'];slot=approval['slot']
        a.acceptance(r,e,None,approval,slot,capture,snapshot,review)
        for key,value in (('observer_status','native-passed'),('producer_status',a.SUCCESS),('case_id','other'),
                          ('rejection_qualified',False),('chart_admission',True),('capture_files',{})):
            with self.subTest(key=key),self.assertRaises(AssertionError):
                a.acceptance(r,e,None,dict(approval,**{key:value}),slot,capture,snapshot,review)
        changed=copy.deepcopy(approval);changed['references']['checker']['sha256']='0'*64
        with self.assertRaises(AssertionError):a.acceptance(r,e,None,changed,slot,capture,snapshot,review)

    def test_additional_leases_leave_inherited_ownership_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();jobs=[root/'current',root/'prelaunch']
            review={}
            for key,job in zip(('durable','failed_prelaunch'),jobs):
                job.mkdir();path=job/'owner.lock';path.touch();s=path.stat()
                review[key]=dict(directory=str(job),lease=dict(path=str(path),device=s.st_dev,inode=s.st_ino))
            common=root/'common';common.touch()
            with common.open('rb') as stream:
                inherited=[(common,stream,(0,0))]
                def check(rows):self.assertTrue(all(not x[1].closed for x in rows))
                with patch.object(a,'PRIOR_JOB',jobs[0]),patch.object(a,'PRELAUNCH_JOB',jobs[1]),patch.object(e,'check_leases',side_effect=check):
                    with a.extra_leases(e,inherited,review) as held:
                        self.assertEqual(len(held),3);self.assertEqual(len(inherited),1)
                    self.assertFalse(stream.closed);self.assertTrue(all(x[1].closed for x in held[1:]))

    def test_build_keeps_126_constructor_then_slices_result(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();output=root/'run';r=base.load_controller(a.BASE_SHA)
            calls=[];schedule=t.slots(output)[23:]
            old_plan=dict(sources={'tree':'unchanged'},extension_image={'image':'same'},prerequisite_artifact_closures=[],
                prior_durable_jobs=[],prior_bounded_stage={'prior23':'same'})
            def old_build(*args):
                calls.append(args);self.assertEqual(args[7],a.BASE_REVIEW)
                self.assertEqual(len(schedule),126)
                return dict(copy.deepcopy(old_plan),schedule=copy.deepcopy(schedule))
            r.build_plan=old_build;r=a.attach(r,dict(path=str(Path(a.__file__)),sha256=OWN))
            prior=dict(durable=dict(directory='/prior',artifacts={}),preserved_successful_cases=141)
            helper=SimpleNamespace();inspector=SimpleNamespace(kb=object());source_ref={'new':'source'};pins={};resolutions={}
            with patch.object(a,'PACKET',root),patch.object(r,'validate_prior_continuation',return_value=(prior,[{'closure':'current'}],old_plan)):
                result=r.build_plan(object(),helper,object(),object(),inspector,output,{'primitive':'ref'},source_ref,{}, {}, {},pins,resolutions)
            self.assertEqual(len(calls),1);self.assertEqual(result['schedule'],schedule[118:])
            self.assertEqual(result['source_review'],source_ref);self.assertEqual(result['continuation_source_review'],a.BASE_REVIEW)
            self.assertEqual((result['native_processes'],result['success_cases'],result['rejection_cases'],result['preserved_successful_cases']),(8,2,6,141))
            self.assertEqual(result['prior_durable_jobs'],[dict(directory='/prior',artifacts={})])

    def test_finalizer_counts_only_eight_and_rejects_late_artifact_changes(self):
        for fault in (None,'digest'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as directory:
                r=controller();out=Path(directory).resolve();plan=draft(out);report=t.failed_report();report['status']=a.SUCCESS
                for index,slot in enumerate(plan['schedule']):
                    d=out/slot['directory'];d.mkdir();t.native_files(d,slot,pid=9182+index)
                    report['attempts'].append(slot['id']);report['registered'].append(dict(id=slot['id'],pid=9182+index))
                    report['captures'].append(dict(id=slot['id'],expected_rejection=bool(slot['expected_exit'])))
                    report['validated_files'].update({str(Path(slot['directory'])/n):v for n,v in e.inventory(d)[0].items()})
                original_sha=e.sha
                def writer(path,value):
                    save(path,value)
                    if fault=='save':path.write_bytes(b'{}\n')
                def sha(path):
                    if fault=='digest':Path(path).write_bytes(b'{}\n')
                    return original_sha(path)
                def leases(*args):
                    if fault=='lease':raise AssertionError('changed named lease')
                with patch.object(r,'verify_inputs'),patch.object(e,'sha',side_effect=sha),patch.object(e,'check_leases',side_effect=leases):
                    if fault:
                        with self.assertRaises(AssertionError):r.finish(e,SimpleNamespace(save=writer),report,plan,out,{},{},[])
                    else:r.finish(e,SimpleNamespace(save=writer),report,plan,out,{},{},[])
                terminal=json.loads((out/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed-integrity' if fault else a.SUCCESS)
                self.assertEqual((terminal['native_processes_started'],terminal['validated_cases'],terminal['preserved_successful_cases']),(8,8,141))
                self.assertEqual(terminal['common_mutex_held'],fault is None)

    def test_run_retains_expected_failed_observer_and_stops_next_failure(self):
        r=controller();checker=load('final8_corrected_checker',Path(a.CHECKER['path']))
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory).resolve();out=root/'run';corpus=root/'corpus';corpus.mkdir();(corpus/'input').write_bytes(b'')
            case=copy.deepcopy(t.negative());case['stdin']=dict(path='input',bytes=0,sha256=r.digest(b''))
            slots=t.slots(out,[case,dict(case,case='second')]);plan=draft(out);plan['schedule']=slots
            calls=[];closed=[]
            def observe(command,environment,d,payload,common,launched,**kwargs):
                slot=slots[len(calls)];calls.append(command);launched(9182+len(calls))
                _,_,final=t.native_files(d,slot,pid=9182+len(calls))
                (d/'stderr.bin').write_bytes(checker.NEGATIVE_STDERR)
                final.update(stderr_bytes=len(checker.NEGATIVE_STDERR),stderr_sha256=r.digest(checker.NEGATIVE_STDERR))
                save(d/'process.json',final)
                if len(calls)==2:raise KeyboardInterrupt('owned stopped case')
                raise AssertionError('Native command exited unsuccessfully')
            kb=SimpleNamespace(atomic=nullcontext,save=save,observe=observe,PIPE_CHUNK=65536)
            with patch.object(r,'CORPUS',corpus/'manifest.json'),patch.object(r,'verify_inputs'),patch.object(e,'pin'), \
                 patch.object(r,'finish',side_effect=lambda helper,kernel,report,*args:closed.append(copy.deepcopy(report))):
                with self.assertRaises(KeyboardInterrupt):r.run(e,kb,checker,plan,root/'plan','a'*64,{},{},None,[])
            self.assertEqual(len(calls),2);self.assertEqual(len(closed[0]['captures']),1)
            self.assertEqual(closed[0]['captures'][0]['observer_status'],'failed')
            self.assertEqual(closed[0]['preserved_successful_cases'],141);self.assertEqual(closed[0]['status'],'stopped-unqualified')

if __name__=='__main__':unittest.main()
