"""Authored synthetic tests for the Rebol149 controller; no native children.

Execution is deferred until the continuous timing cohort releases the lane.
Temporary files and mock observers exercise ownership and evidence closure;
no actual prerequisite plan or full runtime closure is replayed.
"""
import copy
from contextlib import contextmanager, nullcontext
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
r=load('rebol149_test_subject',HERE/'rebol_bounded.py')
e=load('rebol149_test_extension_helpers',HERE/'rebol_extension.py')
checker=load('rebol149_test_outputs',HERE/'rebol_outputs.py')
SPEC=json.loads((r.ORIGINAL/'spec.json').read_bytes())
MAPPING=json.loads((r.ORIGINAL/'bounded-corpus-map.json').read_bytes())
CASES=json.loads(r.CORPUS.read_bytes())['cases']


def save(path,value):path.write_bytes(r.encoded(value))


def sources():
    return {row['benchmark']:dict(path=str(r.FANN if row['benchmark']=='fannkuchredux' else r.ROOT/row['source']))
            for row in MAPPING['rows']}


def slots(output,cases=CASES):
    return r.schedule(e,checker,cases,sources(),dict(path='/fixed/approved-extension.dylib'),output,SPEC['limits'])


def negative():return next(c for c in CASES if c['expected_exit']=='nonzero')


def native_files(directory,slot,pid=9182,exit_code=None):
    code=slot['expected_exit'] if exit_code is None else exit_code
    identity=dict(pid=pid,ppid=os.getpid(),pgid=pid,birth_seconds=100,birth_microseconds=200,status=1)
    common=dict(command=slot['command'],environment=slot['environment'],cwd=str(directory),kind=r.KIND,
        started_at='2026-10-14T00:00:00+00:00',process_timeout_seconds=slot['timeout_seconds'],cleanup_timeout_seconds=5,
        maximum_process_group_rss_bytes=slot['rss_limit_bytes'],native_file_limit_bytes=slot['stream_limit_bytes'],
        stdout_capture_limit_bytes=slot['stream_limit_bytes']+65536,stdout_transport='OS pipe, retained as received',
        stderr_transport='exclusive artifact',stdin_bytes=slot['stdin_bytes'],stdin_sha256=slot['stdin_sha256'],
        inherited_common_mutex=True,common_mutex_inode=79859134,benchmark_samples=0,source_work_qualified=False,chart_admission=False)
    start=dict(common,status='starting',native_process_started=False)
    active=dict(common,status='running',native_process_started=True,pid=pid,pgid=pid,identity=identity)
    stdout=b'';stderr=b'\n** User error: Unsupported revcomp sequence byte\n\n' if code else b''
    final=dict(active,status='failed' if code else 'native-passed',finished_at='2026-10-14T00:00:01+00:00',
        leader_identity_before_reap=dict(identity,status=5),direct_child_reaped=True,remaining_process_group=[],
        stop_signals=[],cleanup_errors=[],exit_status=code,kernel_monitor_samples=2,observed_peak_process_group_rss_bytes=4096,
        stdout_bytes=len(stdout),stdout_sha256=r.digest(stdout),stderr_bytes=len(stderr),stderr_sha256=r.digest(stderr))
    if code:final.update(error_type='AssertionError',error='Native command exited unsuccessfully',remaining_after_cleanup=[])
    for name,value in (('start',start),('active',active),('process',final)):save(directory/(name+'.json'),value)
    (directory/'stdout.bin').write_bytes(stdout);(directory/'stderr.bin').write_bytes(stderr)
    return start,active,final


def draft_plan(output,case_slots=None):
    return dict(output=str(output),schedule=case_slots or slots(output),primitive_review={},
        unavailable_inputs=[],prerequisite_artifact_closures=[],prior_durable_jobs=[])


def failed_report():
    return dict(status='stopped-unqualified',attempts=[],registered=[],captures=[],active=None,validated_files={})


class BoundedTests(unittest.TestCase):
    def test_actual_durable_status_and_invented_success_rejection(self):
        with tempfile.TemporaryDirectory() as temp:
            job=Path(temp).resolve();plan_ref=dict(path='/exact/plan.json',sha256='a'*64)
            argv=[str(e.PYTHON),'-I','-S','-B',str(r.HELPER),'run','--plan',plan_ref['path'],
                  '--plan-sha256',plan_ref['sha256']]
            identity=dict(pid=9182,listing='retained birth identity')
            save(job/'launch.json',dict(command=argv,cwd=str(r.ROOT)))
            save(job/'command-started.json',dict(command=argv,cwd=str(r.ROOT),command_pid=9182,
                command_identity=identity,command_identity_observation_missing=False))
            terminal=dict(status='command-exited-zero-awaiting-report-review',exit_code=0,
                actual_command_started=True,automatic_retry=False,stop_signals=[],
                command_pid=9182,command_identity=identity,command_identity_observation_missing=False)
            save(job/'terminal.json',terminal)
            review=dict(durable=dict(directory=str(job),artifacts=e.inventory(job)[0]))
            self.assertEqual(r.durable_inputs(e,review,plan_ref,{},{})[0],9182)
            terminal['status']='command-succeeded';save(job/'terminal.json',terminal)
            review['durable']['artifacts']=e.inventory(job)[0]
            with self.assertRaisesRegex(AssertionError,'Primitive durable ownership'):
                r.durable_inputs(e,review,plan_ref,{},{})

    def test_exact149_schedule_and_existing_policy(self):
        result=slots(Path('/fresh/run'))
        self.assertEqual(len(result),149);self.assertEqual(sum(bool(s['expected_exit']) for s in result),7)
        self.assertEqual(len({s['id'] for s in result}),149)
        self.assertEqual({b:sum(s['case']['benchmark']==b for s in result) for b in r.BENCHES},
            dict(binarytrees=4,fannkuchredux=9,fasta=16,knucleotide=14,mandelbrot=15,nbody=6,pidigits=10,regexredux=7,revcomp=61,spectralnorm=7))
        self.assertTrue(all((s['timeout_seconds'],s['rss_limit_bytes'],s['stream_limit_bytes'])==(180,536870912,1048576) for s in result))
        for s in result:
            self.assertEqual(s['command'][:3],[str(e.RUNTIME),'-q','-s'])
            self.assertEqual(len(s['command']),5 if s['case']['input_kind']=='integer-argument' else 4)
            for key in SPEC['absent_environment_for_ordinary_cases']:self.assertNotIn(key,s['environment'])
        self.assertFalse(any('clang' in s['command'][0] for s in result))

    def test_only_fann_main_is_substituted_and_old_pin_is_preserved(self):
        pins={str(r.ROOT/name):value for name,value in SPEC['immutable_source_pins'].items()}
        pins[str(r.FANN)]='a'*64;seen=[]
        helper=SimpleNamespace(pin=lambda pins,resolutions,path,sha:seen.append((str(path),sha)))
        selected=r.source_selection(helper,SPEC,MAPPING,CASES,pins,{})
        self.assertEqual(selected['fannkuchredux']['path'],str(r.FANN))
        self.assertEqual(selected['fannkuchredux']['sha256'],'a'*64)
        self.assertEqual(sum(v['substitution'] is not None for v in selected.values()),1)
        self.assertEqual(len(seen),10)
        changed=copy.deepcopy(MAPPING);changed['rows'][1]['case_ids'].remove('n-0')
        with self.assertRaisesRegex(AssertionError,'source/case mapping'):
            r.source_selection(helper,SPEC,changed,CASES,pins,{})
        del pins[str(r.FANN)]
        with self.assertRaisesRegex(AssertionError,'independent source-review pin'):
            r.source_selection(helper,SPEC,MAPPING,CASES,pins,{})

    def test_draft_or_overqualified_primitive_review_is_rejected(self):
        value=dict(schema='rebol19-independent-primitive-review-v1',status='exact-eighteen-primitive-contracts-qualified',
            independent_review=True,full_primitive_fixtures_qualified=True,native_processes=19,fixture_processes=18,
            benchmark_samples=0,**{k:False for k in r.GATES})
        for change in (dict(status='source-only'),dict(full_primitive_fixtures_qualified=False),
                       dict(native_processes=18),dict(native_processes=19.0),dict(source_work_qualified=True)):
            with self.subTest(change=change),self.assertRaisesRegex(AssertionError,'Actual independent'):
                r.check_primitive_review(dict(value,**change))

    def test_extra_primitive_lease_does_not_mutate_inherited_list(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp).resolve();lease=base/'owner.lock';lease.write_bytes(b'');common=base/'common';common.write_bytes(b'')
            st=lease.stat();prior_lists=[];events=[]
            primitive_ref=dict(path='/primitive-review',sha256='a'*64);source_ref=dict(path='/source-review',sha256='b'*64)
            review=dict(references=dict(extension_review={},source_review={}),durable=dict(lease=dict(path=str(lease),device=st.st_dev,inode=st.st_ino)))
            source=dict(files={str(r.CHECKER.relative_to(r.ROOT)):r.digest(r.CHECKER.read_bytes())},dependencies={})
            @contextmanager
            def inherited(*args):
                with common.open('rb') as handle:
                    owned=[(common,handle,(0,0))];prior_lists.append(owned)
                    try:yield e,None,None,handle,owned,{},None,{},{}
                    finally:
                        self.assertEqual(len(owned),1);self.assertTrue(all(not row[1].closed for row in owned));events.append('outer-closed')
            def check(rows):self.assertTrue(all(not row[1].closed for row in rows))
            with patch.object(r,'bootstrap',return_value=(SimpleNamespace(held=inherited),review,source)), \
                 patch.object(e,'document',side_effect=lambda ref,*args:review if ref==primitive_ref else source), \
                 patch.object(e,'pin'),patch.object(e,'check_leases',side_effect=check):
                with r.held(primitive_ref,source_ref) as result:
                    self.assertEqual(len(result[6]),2);self.assertEqual(len(prior_lists[0]),1)
            self.assertEqual(events,['outer-closed'])

    def test_expected_rejection_keeps_original_failed_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();slot=slots(out,[negative()])[0];directory=out/slot['directory'];directory.mkdir()
            native_files(directory,slot);before=(directory/'process.json').read_bytes()
            record,_=r.checked_case(e,SimpleNamespace(PIPE_CHUNK=65536),checker,slot,directory,os.getpid())
            self.assertEqual(record['observer_status'],'failed');self.assertTrue(record['expected_rejection'])
            self.assertEqual((directory/'process.json').read_bytes(),before)
            self.assertFalse(record['output_validation']['native_process_verified'])

    def test_unrelated_failure_cannot_be_an_expected_rejection(self):
        for change in (dict(error='Unexpected stderr; raw bytes retained'),dict(error_type='TimeoutExpired'),
                       dict(exit_status=-9),dict(exit_status=False),dict(direct_child_reaped=False),
                       dict(remaining_process_group=[123]),dict(stop_signals=[9])):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as temp:
                out=Path(temp).resolve();slot=slots(out,[negative()])[0];directory=out/slot['directory'];directory.mkdir()
                _,_,final=native_files(directory,slot);final.update(change);save(directory/'process.json',final)
                with self.assertRaises(AssertionError):r.native_capture(e,SimpleNamespace(PIPE_CHUNK=65536),slot,directory,os.getpid())

    def test_success_requires_exact_zero_exit_and_owned_birth(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();slot=slots(out,[CASES[0]])[0];directory=out/slot['directory'];directory.mkdir()
            _,_,final=native_files(directory,slot)
            r.native_capture(e,SimpleNamespace(PIPE_CHUNK=65536),slot,directory,os.getpid())
            final['leader_identity_before_reap']['birth_microseconds']+=1;save(directory/'process.json',final)
            with self.assertRaisesRegex(AssertionError,'owned native closure'):
                r.native_capture(e,SimpleNamespace(PIPE_CHUNK=65536),slot,directory,os.getpid())

    def test_zero_rss_requires_initial_owned_zombie_and_stays_unavailable(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();slot=slots(out,[negative()])[0];directory=out/slot['directory'];directory.mkdir()
            _,active,final=native_files(directory,slot);final['observed_peak_process_group_rss_bytes']=0;save(directory/'process.json',final)
            with self.assertRaisesRegex(AssertionError,'initial owned zombie'):
                r.native_capture(e,SimpleNamespace(PIPE_CHUNK=65536),slot,directory,os.getpid())
            active['identity']['status']=final['identity']['status']=5
            save(directory/'active.json',active);save(directory/'process.json',final)
            record,_=r.checked_case(e,SimpleNamespace(PIPE_CHUNK=65536),checker,slot,directory,os.getpid())
            self.assertIsNone(record['observed_peak_process_group_rss_bytes']);self.assertFalse(record['memory_usage_qualified'])

    def test_wrong_rebol_diagnostic_is_rejected_after_clean_native_exit(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();slot=slots(out,[negative()])[0];directory=out/slot['directory'];directory.mkdir()
            _,_,final=native_files(directory,slot);raw=b'other user error\n'
            (directory/'stderr.bin').write_bytes(raw);final.update(stderr_bytes=len(raw),stderr_sha256=r.digest(raw));save(directory/'process.json',final)
            with self.assertRaises(ValueError):r.checked_case(e,SimpleNamespace(PIPE_CHUNK=65536),checker,slot,directory,os.getpid())

    def test_late_stream_change_cannot_enter_validated_snapshot(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();slot=slots(out,[negative()])[0];directory=out/slot['directory'];directory.mkdir();native_files(directory,slot)
            def changed(*args):
                result=checker.validate(*args);(directory/'stderr.bin').write_bytes(b'changed');return result
            with self.assertRaisesRegex(AssertionError,'changed before adoption'):
                r.checked_case(e,SimpleNamespace(PIPE_CHUNK=65536),SimpleNamespace(validate=changed),slot,directory,os.getpid())

    def test_expected_negative_continues_but_next_unexpected_failure_stops(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp).resolve();out=base/'run';corpus=base/'corpus';corpus.mkdir();case=copy.deepcopy(negative())
            case['stdin']=dict(path='input',bytes=0,sha256=r.digest(b''));(corpus/'input').write_bytes(b'')
            result=slots(out,[case,dict(case,case='second')]);document=draft_plan(out,result);calls=[];closed=[]
            def observe(command,environment,directory,payload,common,launched,**kwargs):
                slot=result[len(calls)];calls.append(command);launched(9182+len(calls))
                native_files(directory,slot,pid=9182+len(calls))
                if len(calls)==2:raise KeyboardInterrupt('stop after owned closure')
                raise AssertionError('Native command exited unsuccessfully')
            kb=SimpleNamespace(atomic=nullcontext,save=save,observe=observe,PIPE_CHUNK=65536)
            with patch.object(r,'CORPUS',corpus/'manifest.json'),patch.object(r,'verify_inputs'),patch.object(e,'pin'), \
                 patch.object(r,'finish',side_effect=lambda helper,kernel,report,*args:closed.append(copy.deepcopy(report))):
                with self.assertRaises(KeyboardInterrupt):r.run(e,kb,checker,document,base/'plan','a'*64,{},{},None,[])
            self.assertEqual(len(calls),2);self.assertEqual(len(closed[0]['captures']),1)
            self.assertEqual(closed[0]['captures'][0]['observer_status'],'failed')
            self.assertEqual(closed[0]['status'],'stopped-unqualified');self.assertEqual(len(closed[0]['registered']),2)

    def test_final_report_mutation_is_not_adopted(self):
        for phase in ('save','replay'):
            with self.subTest(phase=phase),tempfile.TemporaryDirectory() as temp:
                out=Path(temp).resolve();calls=[]
                def writer(path,value):
                    save(path,value)
                    if phase=='save':path.write_bytes(b'{}\n')
                def verify(*args):
                    calls.append(True)
                    if phase=='replay' and len(calls)==2:(out/'report.json').write_bytes(b'{}\n')
                with patch.object(r,'verify_inputs',side_effect=verify),patch.object(e,'check_leases'):
                    with self.assertRaisesRegex(AssertionError,'Final integrity failed'):
                        r.finish(e,SimpleNamespace(save=writer),failed_report(),draft_plan(out),out,{},{},[])
                terminal=json.loads((out/'terminal.json').read_bytes());self.assertEqual(terminal['status'],'failed-integrity')
                self.assertFalse(terminal['common_mutex_held']);self.assertEqual((out/'report.json').read_bytes(),b'{}\n')

    def test_final_snapshot_and_named_lease_failures_are_retained(self):
        for phase in ('snapshot','lease'):
            with self.subTest(phase=phase),tempfile.TemporaryDirectory() as temp:
                out=Path(temp).resolve();report=failed_report()
                if phase=='snapshot':
                    (out/'raw').write_bytes(b'changed');report['validated_files']['raw']=dict(bytes=3,sha256=r.digest(b'old'))
                def check(*args):
                    if phase=='lease':raise AssertionError('lease replaced')
                with patch.object(r,'verify_inputs'),patch.object(e,'check_leases',side_effect=check):
                    with self.assertRaisesRegex(AssertionError,'Final integrity failed'):
                        r.finish(e,SimpleNamespace(save=save),report,draft_plan(out),out,{},{},[])
                terminal=json.loads((out/'terminal.json').read_bytes());self.assertEqual(terminal['status'],'failed-integrity')
                if phase=='snapshot':self.assertEqual((out/'raw').read_bytes(),b'changed')


if __name__=='__main__':unittest.main()
