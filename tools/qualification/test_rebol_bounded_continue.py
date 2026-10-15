"""Focused continuation tests; no native children or runtime pin replay."""
import copy
from contextlib import nullcontext
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

HERE=Path(__file__).resolve().parent
a=load('remaining126_adapter',HERE/'rebol_bounded_continue.py')
b=load('remaining126_base',a.BASE)
oldtests=load('remaining126_synthetic_native',HERE/'test_rebol_bounded.py')
e=oldtests.e;checker=oldtests.checker;OWN=a.digest(Path(a.__file__).read_bytes())

def controller():return a.load_controller(OWN)
def save(path,value):path.write_bytes(oldtests.r.encoded(value))
def plan(output):
    value=oldtests.draft_plan(output,oldtests.slots(output)[23:])
    value.update(continuation_adapter=dict(path=str(Path(a.__file__)),sha256=OWN),
                 prior_bounded_stage=dict(report_finished_at='2026-10-13T00:00:00+00:00'))
    return value

class ContinuationTests(unittest.TestCase):
    def test_frozen_observer_checker_and_original_identity_are_preserved(self):
        r=controller();base=b.load_controller(a.BASE_SHA,a.PRIMITIVE_SHA)
        self.assertEqual(r.__file__,base.__file__)
        for name in ('native_capture','checked_case','verify_inputs','corpus','primitive_inputs','bootstrap'):
            chosen,frozen=getattr(r,name),getattr(base,name)
            self.assertEqual(chosen.__code__.co_code,frozen.__code__.co_code)
            self.assertEqual(chosen.__code__.co_filename,frozen.__code__.co_filename)
        self.assertEqual(r.SUCCESS,a.SUCCESS)
        with self.assertRaisesRegex(AssertionError,'adapter changed'):a.load_controller('0'*64)

    def test_loader_rejects_fifo_before_open(self):
        with tempfile.TemporaryDirectory() as temp:
            fifo=Path(temp).resolve()/'base.py';os.mkfifo(fifo)
            with patch.object(a,'BASE',fifo),patch.object(a.os,'open',side_effect=AssertionError('must not open')):
                with self.assertRaisesRegex(AssertionError,'Physical regular bounded'):a.load_controller(OWN)

    def test_remaining_schedule_is_exact_original_suffix_and_limits(self):
        original=oldtests.slots(Path('/fresh/run'));snapshot=copy.deepcopy(original)
        actual=a.remaining_schedule(lambda:original)
        self.assertEqual(actual,original[23:]);self.assertEqual(original,snapshot)
        self.assertEqual(len(actual),126);self.assertEqual(sum(s['expected_exit']==0 for s in actual),119)
        self.assertEqual(sum(s['expected_exit']==1 for s in actual),7)
        self.assertEqual(actual[0]['id'],'binarytrees:n-0')
        self.assertEqual(actual[0]['directory'],'023-binarytrees-n-0')
        self.assertTrue(all((s['timeout_seconds'],s['rss_limit_bytes'],s['stream_limit_bytes'])==(180,536870912,1048576) for s in actual))
        for changed in (original[1:],original[:23]+original[24:]):
            with self.assertRaisesRegex(AssertionError,'prefix'):a.remaining_schedule(lambda:changed)
        changed=copy.deepcopy(original);changed[0]['expected_exit']=1
        with self.assertRaisesRegex(AssertionError,'prefix'):a.remaining_schedule(lambda:changed)

    def selection(self):
        base=b.load_controller(a.BASE_SHA,a.PRIMITIVE_SHA)
        pins={str(a.ROOT/name):value for name,value in oldtests.SPEC['immutable_source_pins'].items()}
        pins[str(base.FANN)]=a.digest(base.FANN.read_bytes())
        return base,pins

    def test_only_tree_selection_changes_and_old_main_pin_survives(self):
        base,pins=self.selection();before=base.source_selection(e,oldtests.SPEC,oldtests.MAPPING,oldtests.CASES,dict(pins),{})
        r=controller();actual=r.source_selection(e,oldtests.SPEC,oldtests.MAPPING,oldtests.CASES,pins,{})
        for bench in before:
            if bench!='binarytrees':self.assertEqual(actual[bench],before[bench])
        changed=actual['binarytrees'];old=before['binarytrees']
        self.assertEqual({k:changed[k] for k in ('path','sha256')},a.TREE)
        self.assertEqual((changed['historical_path'],changed['historical_sha256']),(old['path'],old['sha256']))
        self.assertEqual(pins[old['path']],old['sha256']);self.assertEqual(pins[a.TREE['path']],a.TREE['sha256'])
        self.assertEqual(actual['regexredux']['path'],b.REGEX_MAIN['path'])

    def test_tree_review_cannot_change_failure_helper_or_claimed_scope(self):
        base,pins=self.selection();review=json.loads(Path(a.TREE_REVIEW['path']).read_bytes())
        original=e.document
        for mutation in ('failure','main','helper','scope'):
            changed=copy.deepcopy(review)
            if mutation=='failure':changed['retained_failure']['review']['sha256']='0'*64
            elif mutation=='main':changed['files']['main.reb']['sha256']='0'*64
            elif mutation=='helper':changed['relative_helper_paths']=[]
            else:changed['canonical_source_count_qualified']=True
            def document(ref,*args):return changed if ref==a.TREE_REVIEW else original(ref,*args)
            helper=SimpleNamespace(document=document,pin=e.pin)
            with self.subTest(mutation=mutation),self.assertRaises(AssertionError):
                a.select_tree(base,base.source_selection,helper,oldtests.SPEC,oldtests.MAPPING,oldtests.CASES,dict(pins),{})

    def test_source_approval_requires_exact_base_and_all_five_new_files(self):
        r=controller();adapter_ref=dict(path=str(Path(a.__file__)),sha256=OWN)
        value=dict(schema='rebol126-continuation-source-review-v1',status='independent-source-review-complete-native-cases-pending',
            independent_review=True,files={name:a.digest((a.ROOT/name).read_bytes()) for name in a.SOURCE_FILES},
            dependencies={str(a.BASE.relative_to(a.ROOT)):a.BASE_SHA},base_source_review=a.BASE_REVIEW,
            prior_stage_review=a.PRIOR,tree_source_review=a.TREE_REVIEW,**{k:False for k in r.GATES})
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp).resolve()/'source-review.json'
            def check(v):
                raw=r.encoded(v);path.write_bytes(raw)
                return a.checked_source_review(r,dict(path=str(path),sha256=a.digest(raw)),adapter_ref)
            self.assertEqual(check(value),value)
            for key,new in (('base_source_review',{}),('prior_stage_review',{}),('chart_admission',True),('files',{})):
                with self.subTest(key=key),self.assertRaises(AssertionError):check(dict(value,**{key:new}))

    def test_prior_ledger_requires_honest_failed_prefix(self):
        r=controller();review=json.loads(Path(a.PRIOR['path']).read_bytes())
        p,report,terminal=[json.loads(Path(a.PRIOR_REFS[n]['path']).read_bytes()) for n in ('plan','report','terminal')]
        a.prior_ledger(r,review,p,report,terminal,p['primitive_review'])
        for key,value in (('attempted_cases',23),('successful_output_contracts',24),('failed_cases',False),('benchmark_correctness_qualified',True)):
            with self.subTest(key=key),self.assertRaises(AssertionError):
                a.prior_ledger(r,dict(review,**{key:value}),p,report,terminal,p['primitive_review'])
        for key,value in (('status','all149-output-contracts-retained-awaiting-independent-review'),('captures',report['captures'][:-1]),
                          ('attempts',report['attempts'][:-1]),('pins',{})):
            with self.subTest(key=key),self.assertRaises(AssertionError):
                a.prior_ledger(r,review,p,dict(report,**{key:value}),terminal,p['primitive_review'])

    def test_prior_durable_argv_birth_and_failed_exit_are_exact(self):
        with tempfile.TemporaryDirectory() as temp:
            job=Path(temp).resolve();identity=dict(pid=9182,listing='same retained birth')
            argv=[str(e.PYTHON),'-I','-S','-B',str(a.BASE),'--adapter-sha256',a.BASE_SHA,
                '--primitive-adapter-sha256',a.PRIMITIVE_SHA,'run','--plan',a.PRIOR_REFS['plan']['path'],'--plan-sha256',a.PRIOR_REFS['plan']['sha256']]
            launch=dict(command=argv,cwd=str(a.ROOT));started=dict(launch,command_pid=9182,command_identity=identity,command_identity_observation_missing=False)
            ended=dict(status='command-failed',exit_code=1,actual_command_started=True,automatic_retry=False,stop_signals=[],
                command_pid=9182,command_identity=identity,command_identity_observation_missing=False)
            for name in ('request.json','worker-started.json','command.stdout','command.stderr','worker.log'):(job/name).write_bytes(b'')
            def write(l,s,t):
                for name,value in (('launch',l),('command-started',s),('terminal',t)):save(job/(name+'.json'),value)
                return dict(durable=dict(directory=str(job),artifacts=e.inventory(job)[0],lease=dict(path=str(job/'owner.lock'))))
            with patch.object(a,'PRIOR_JOB',job):
                self.assertEqual(a.durable_inputs(e,write(launch,started,ended),{},{} )[0],9182)
                for l,s,t in ((dict(launch,command=argv+['-u']),started,ended),
                    (launch,started,dict(ended,exit_code=True)),(launch,started,dict(ended,status='command-exited-zero-awaiting-report-review')),
                    (launch,started,dict(ended,command_identity=dict(identity,listing='different birth')))):
                    with self.assertRaisesRegex(AssertionError,'durable identity'):
                        a.durable_inputs(e,write(l,s,t),{},{})

    def test_extra_lease_keeps_inherited_list_open_and_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            job=Path(temp).resolve();lease=job/'owner.lock';lease.write_bytes(b'');s=lease.stat()
            common=job/'common';common.write_bytes(b'')
            review=dict(durable=dict(directory=str(job),lease=dict(path=str(lease),device=s.st_dev,inode=s.st_ino)))
            with common.open('rb') as handle:
                old=[(common,handle,(0,0))]
                def check(rows):self.assertTrue(all(not row[1].closed for row in rows))
                with patch.object(a,'PRIOR_JOB',job),patch.object(e,'check_leases',side_effect=check):
                    with a.extra_lease(e,old,review) as combined:
                        self.assertEqual(len(old),1);self.assertEqual(len(combined),2)
                    self.assertEqual(len(old),1);self.assertFalse(handle.closed);self.assertTrue(combined[-1][1].closed)

    def test_complete126_finalizer_counts_only_new_observations(self):
        r=controller()
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();p=plan(out);report=oldtests.failed_report();report['status']=a.SUCCESS
            for index,slot in enumerate(p['schedule']):
                directory=out/slot['directory'];directory.mkdir();oldtests.native_files(directory,slot,pid=9182+index)
                report['attempts'].append(slot['id']);report['registered'].append(dict(id=slot['id'],pid=9182+index))
                report['captures'].append(dict(id=slot['id'],expected_rejection=bool(slot['expected_exit'])))
                report['validated_files'].update({str(Path(slot['directory'])/n):v for n,v in e.inventory(directory)[0].items()})
            with patch.object(r,'verify_inputs'),patch.object(e,'check_leases'):
                r.finish(e,SimpleNamespace(save=save),report,p,out,{},{},[])
            terminal=json.loads((out/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],a.SUCCESS)
            self.assertEqual((terminal['native_processes_started'],terminal['validated_cases'],terminal['preserved_successful_cases']),(126,126,23))
            self.assertEqual(terminal['schema'],'rebol126-bounded-terminal-v1')
            self.assertTrue(all(terminal[k] is False for k in r.GATES))

    def test_late_report_mutations_and_pin_failures_are_preserved(self):
        for phase in ('save','replay','digest','pin','lease'):
            with self.subTest(phase=phase),tempfile.TemporaryDirectory() as temp:
                r=controller();out=Path(temp).resolve();calls=[];original_sha=e.sha
                def writer(path,value):
                    save(path,value)
                    if phase=='save':path.write_bytes(b'{}\n')
                def verify(*args):
                    calls.append(True)
                    if phase=='pin':raise AssertionError('input changed')
                    if phase=='replay' and len(calls)==2:(out/'report.json').write_bytes(b'{}\n')
                def sha(path):
                    if phase=='digest':Path(path).write_bytes(b'{}\n')
                    return original_sha(path)
                def leases(*args):
                    if phase=='lease':raise AssertionError('named lease changed')
                with patch.object(r,'verify_inputs',side_effect=verify),patch.object(e,'sha',side_effect=sha),patch.object(e,'check_leases',side_effect=leases):
                    with self.assertRaisesRegex(AssertionError,'Final integrity failed'):
                        r.finish(e,SimpleNamespace(save=writer),oldtests.failed_report(),plan(out),out,{},{},[])
                terminal=json.loads((out/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed-integrity');self.assertFalse(terminal['common_mutex_held'])

    def test_expected_rejection_continues_and_next_failure_stops_without_retry(self):
        r=controller()
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp).resolve();out=base/'run';corpus=base/'corpus';corpus.mkdir()
            case=copy.deepcopy(oldtests.negative());case['stdin']=dict(path='input',bytes=0,sha256=r.digest(b''));(corpus/'input').write_bytes(b'')
            selected=oldtests.slots(out,[case,dict(case,case='second')]);p=plan(out);p['schedule']=selected
            calls=[];closed=[]
            def observe(command,environment,directory,payload,common,launched,**kwargs):
                slot=selected[len(calls)];calls.append(command);launched(9182+len(calls))
                oldtests.native_files(directory,slot,pid=9182+len(calls))
                if len(calls)==2:raise KeyboardInterrupt('stop after owned closure')
                raise AssertionError('Native command exited unsuccessfully')
            kb=SimpleNamespace(atomic=nullcontext,save=save,observe=observe,PIPE_CHUNK=65536)
            with patch.object(r,'CORPUS',corpus/'manifest.json'),patch.object(r,'verify_inputs'),patch.object(e,'pin'), \
                 patch.object(r,'finish',side_effect=lambda helper,kernel,report,*args:closed.append(copy.deepcopy(report))):
                with self.assertRaises(KeyboardInterrupt):r.run(e,kb,checker,p,base/'plan','a'*64,{},{},None,[])
            self.assertEqual(len(calls),2);self.assertEqual(len(closed[0]['captures']),1)
            self.assertEqual(closed[0]['captures'][0]['observer_status'],'failed')
            self.assertEqual(closed[0]['status'],'stopped-unqualified');self.assertEqual(closed[0]['preserved_successful_cases'],23)
            self.assertEqual(closed[0]['schema'],'rebol126-bounded-results-v1')

if __name__=='__main__':unittest.main()
