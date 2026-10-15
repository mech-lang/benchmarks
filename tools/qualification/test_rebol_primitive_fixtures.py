"""Draft synthetic fixed-stage tests; no interpreter/compiler/native child.

These tests are authored but deliberately unexecuted while timing owns the lane.
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


def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


HERE=Path(__file__).resolve().parent
r=load('rebol_fixtures_test_subject',HERE/'rebol_primitive_fixtures.py')
e=load('rebol_fixtures_test_helper',HERE/'rebol_extension.py')
a=load('rebol_fixtures_test_transport',r.ADAPTER)
SPEC=json.loads((r.ORIGINAL/'spec.json').read_bytes())


def intake():
    return dict(target='arm64-apple-macos11.0',tools={k:dict(path=str(e.RUNTIME) if k=='runtime' else '/fixed/'+k)
        for k in ('clang','linker','runtime')},include_roots={k:'/fixed/include/'+k
        for k in ('clang_resource','macos_sdk','gmp','pcre2','rebol')})


def slots(output):return r.schedule(e,a,SPEC,intake(),dict(path='/fixed/approved-extension.dylib'),output)


def save(path,value):path.write_bytes(r.encoded(value))


def failure_report():
    return dict(status='stopped-unqualified',attempts=[],registered=[],captures=[],active=None,validated_files={})


def plan(output):
    return dict(output=str(output),schedule=slots(output),extension_review=dict(path='/not-executed/review',sha256='a'*64),
        unavailable_inputs=[],prerequisite_artifact_closures=[],extension_durable=dict(directory='/not-executed/job',artifacts={}))


def capture_files(directory,slot):
    identity=dict(pid=9123,ppid=os.getpid(),pgid=9123,birth_seconds=100,birth_microseconds=200,status=1)
    common=dict(command=slot['command'],environment=slot['environment'],cwd=str(directory),kind=r.KIND,
        started_at='2026-10-14T00:00:00+00:00',process_timeout_seconds=slot['timeout_seconds'],cleanup_timeout_seconds=5,
        maximum_process_group_rss_bytes=slot['rss_limit_bytes'],native_file_limit_bytes=slot['stream_limit_bytes'],
        stdout_capture_limit_bytes=slot['stream_limit_bytes']+65536,stdout_transport='OS pipe, retained as received',
        stderr_transport='exclusive artifact',stdin_bytes=slot['stdin_bytes'],stdin_sha256=slot['stdin_sha256'],
        inherited_common_mutex=True,common_mutex_inode=79859134,source_work_qualified=False,chart_admission=False)
    start=dict(common,status='starting',native_process_started=False)
    active=dict(common,status='running',native_process_started=True,pid=9123,pgid=9123,identity=identity)
    final=dict(active,status='native-passed',finished_at='2026-10-14T00:00:01+00:00',
        leader_identity_before_reap=dict(identity,status=5),direct_child_reaped=True,remaining_process_group=[],
        stop_signals=[],cleanup_errors=[],exit_status=0,kernel_monitor_samples=2,observed_peak_process_group_rss_bytes=4096,
        stdout_bytes=0,stdout_sha256=r.digest(b''),stderr_bytes=0,stderr_sha256=r.digest(b''))
    for name,value in (('start',start),('active',active),('process',final)):save(directory/(name+'.json'),value)
    (directory/'stdout.bin').write_bytes(b'');(directory/'stderr.bin').write_bytes(b'')
    return start,active,final


class FixedStageTests(unittest.TestCase):
    def test_actual_durable_zero_exit_status_is_preserved_not_promoted(self):
        argv=[str(e.PYTHON),'-I','-S','-B',str(r.HELPER),'run','--plan','/plan','--plan-sha256','a'*64]
        identity=dict(pid=51,birth_seconds=100,birth_microseconds=200)
        launch=dict(command=argv,cwd=str(r.ROOT))
        started=dict(launch,command_pid=51,command_identity=identity,command_identity_observation_missing=False)
        ended=dict(status='command-exited-zero-awaiting-report-review',exit_code=0,actual_command_started=True,
            automatic_retry=False,stop_signals=[],command_identity_observation_missing=False,
            command_pid=51,command_identity=copy.deepcopy(identity))
        original=copy.deepcopy((launch,started,ended))
        r.check_durable_controller(launch,started,ended,argv)
        self.assertEqual((launch,started,ended),original)
        for changes in (dict(status='command-succeeded'),dict(status='command-failed'),dict(exit_code=1),
                        dict(exit_code=False),dict(stop_signals=[15])):
            with self.subTest(changes=changes),self.assertRaisesRegex(AssertionError,'durable command'):
                r.check_durable_controller(launch,started,dict(ended,**changes),argv)

    def test_extra_lease_does_not_escape_into_outer_helpers_owned_list(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp).resolve();(base/'common').write_bytes(b'');(base/'extension').write_bytes(b'')
            metadata=(base/'extension').stat();outer_lists=[];checks=[]
            source_ref=dict(path='/source-review',sha256='a'*64);extension_ref=dict(path='/extension-review',sha256='b'*64)
            source=dict(files={str(r.ADAPTER.relative_to(r.ROOT)):r.digest(r.ADAPTER.read_bytes())},dependencies={})
            extension=dict(references=dict(toolchain_intake={}),durable=dict(lease=dict(path=str(base/'extension'),
                device=metadata.st_dev,inode=metadata.st_ino)))
            @contextmanager
            def inherited(unused):
                with (base/'common').open('rb') as stream:
                    owned=[(base/'common',stream,(0,0))];outer_lists.append(owned)
                    try:yield stream,owned,{},{},{}
                    finally:
                        self.assertEqual(len(owned),1)
                        self.assertTrue(all(not member[1].closed for member in owned))
                        checks.append('outer-close')
            def check(members):
                self.assertTrue(all(not member[1].closed for member in members));checks.append(len(members))
            with patch.object(r,'bootstrap',return_value=(e,extension,source)),patch.object(r,'check_disposition'), \
                 patch.object(e,'held_inputs',side_effect=inherited),patch.object(e,'pin'), \
                 patch.object(e,'document',side_effect=lambda ref,*args:source if ref==source_ref else extension), \
                 patch.object(e,'check_leases',side_effect=check),patch.object(e,'load_support',return_value=SimpleNamespace()):
                with r.held(extension_ref,source_ref) as context:
                    self.assertEqual(len(context[4]),2);self.assertEqual(len(outer_lists[0]),1)
            self.assertEqual(checks[-1],'outer-close')

    def test_exact_nineteen_order_limits_and_original_argv(self):
        result=slots(Path('/fresh/stage'))
        self.assertEqual([slot['id'] for slot in result],['compile-io-interposer',*a.CASE_IDS])
        self.assertEqual(len(result),19)
        self.assertEqual((result[0]['timeout_seconds'],result[0]['rss_limit_bytes'],result[0]['stream_limit_bytes']),
                         (300,2*1024**3,64*1024**2))
        self.assertTrue(all((s['timeout_seconds'],s['rss_limit_bytes'],s['stream_limit_bytes'])==(180,512*1024**2,1024**2)
                            for s in result[1:]))
        self.assertTrue(all(s['command'][:3]==[str(e.RUNTIME),'-q','-s'] for s in result[1:]))
        self.assertEqual(result[0]['command'].count('--no-default-config'),1)
        self.assertIn('-nostdinc',result[0]['command']);self.assertIn('-MD',result[0]['command'])
        self.assertIn('-D_DARWIN_C_SOURCE',result[0]['command'])
        self.assertIn('-fuse-ld=/fixed/linker',result[0]['command'])
        self.assertFalse(any('gmp' in arg or 'pcre2' in arg for arg in result[0]['command']))
        changed=copy.deepcopy(SPEC);changed['cases'].pop()
        with self.assertRaisesRegex(AssertionError,'eighteen-case'):
            r.schedule(e,a,changed,intake(),dict(path='/extension'),Path('/fresh'))

    def test_only_last_fixture_has_injection_and_all_inputs_are_retained(self):
        result=slots(Path('/fresh/stage'))
        for slot in result[:-1]:
            for key in SPEC['absent_environment_for_ordinary_cases']:self.assertNotIn(key,slot['environment'])
        self.assertEqual(result[-1]['environment']['DYLD_INSERT_LIBRARIES'],'/fresh/stage/build/io-faults.dylib')
        self.assertEqual(sum(s.get('case',{}).get('stdin',{}).get('transport')=='regular-file' for s in result),9)
        expected=r.expected_files(dict(output='/fresh/stage',schedule=result))
        self.assertEqual(sum(name.startswith('inputs/') for name in expected),18)
        self.assertEqual(sum(name.endswith('/transport.json') for name in expected),18)
        self.assertEqual(sum(name.endswith('.reb') for name in expected),15)
        self.assertIn('18-pipe-injected-short-io/io-faults.json',expected)

    def test_draft_or_prematurely_qualified_extension_disposition_is_rejected(self):
        value=dict(schema='rebol-extension-actual-build-layout-load-review-v1',
            status='qualified-exact-extension-build-layout-load',independent_review=True,extension_abi_qualified=True,
            failed_sdk_producer_preserved=True,native_processes=4,benchmark_samples=0,**{k:False for k in r.GATES})
        for changes in (dict(status='source-reviewed-awaiting-native-build-layout-load'),
                        dict(extension_abi_qualified=False),dict(full_primitive_fixtures_qualified=True),
                        dict(native_processes=0),dict(independent_review=False)):
            with self.subTest(changes=changes),self.assertRaisesRegex(AssertionError,'Actual independently'):
                r.check_disposition(dict(value,**changes))

    def test_transport_and_sidecar_survive_observer_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();slot=slots(out)[4];directory=out/slot['directory'];directory.mkdir()
            raw=b'schema "rebol-primitive-gc-observation-v1" before 1 after 2\n'
            def observe(*args,**kwargs):
                Path(slot['sidecars']['sidecar']).write_bytes(raw)
                raise RuntimeError('native observation failed after sidecar')
            kb=SimpleNamespace(atomic=nullcontext,save=save,observe=observe)
            with self.assertRaisesRegex(RuntimeError,'native observation failed'):
                r.observe_case(e,a,kb,slot,out,None,lambda pid:None)
            self.assertEqual(Path(slot['sidecars']['sidecar']).read_bytes(),raw)
            record=json.loads((directory/'transport.json').read_bytes())
            self.assertEqual(record['case'],'gc-ownership');self.assertFalse(record['transfer_completed'])

    def test_transport_save_failure_still_retains_sidecar_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();slot=slots(out)[4];directory=out/slot['directory'];directory.mkdir()
            sidecar=Path(slot['sidecars']['sidecar']);sidecar.write_bytes(b'actual raw sidecar')
            def broken_save(path,value):
                if path.name=='transport.json':raise OSError('transport write failed')
                save(path,value)
            kb=SimpleNamespace(atomic=nullcontext,save=broken_save,
                observe=lambda *args,**kwargs:(_ for _ in ()).throw(RuntimeError('primary native failure')))
            with self.assertRaisesRegex(RuntimeError,'primary native failure'):
                r.observe_case(e,a,kb,slot,out,None,lambda pid:None)
            self.assertEqual(sidecar.read_bytes(),b'actual raw sidecar')
            errors=json.loads((directory/'sidecar-retention-errors.json').read_bytes())
            self.assertIn('transport write failed',errors[0]['error'])

    def test_regular_input_context_surrounds_failed_observer_cleanup(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();slot=slots(out)[5];(out/slot['directory']).mkdir();events=[];handle=object()
            @contextmanager
            def regular(path,payload):
                events.append('file-open')
                try:yield handle
                finally:events.append('file-rechecked-closed')
            def observe(*args,**kwargs):
                self.assertIs(kwargs['launch'].__self__.regular,handle)
                events.extend(('observe','owned-cleanup'));raise RuntimeError('owned failure')
            kb=SimpleNamespace(atomic=nullcontext,save=save,observe=observe)
            with patch.object(a,'regular_input',side_effect=regular),self.assertRaisesRegex(RuntimeError,'owned failure'):
                r.observe_case(e,a,kb,slot,out,None,lambda pid:None)
            self.assertEqual(events,['file-open','observe','owned-cleanup','file-rechecked-closed'])
            self.assertTrue((out/slot['directory']/'transport.json').is_file())

    def test_capture_rejects_wrong_limits_transports_boolean_exit_and_identity(self):
        cases=(dict(maximum_process_group_rss_bytes=2*1024**3),dict(exit_status=False),
               dict(stdout_transport='guessed'),dict(cleanup_errors=['unreaped']))
        for delta in cases:
            with self.subTest(delta=delta),tempfile.TemporaryDirectory() as temp:
                out=Path(temp).resolve();slot=slots(out)[1];directory=out/slot['directory'];directory.mkdir()
                _,_,record=capture_files(directory,slot);record.update(delta);save(directory/'process.json',record)
                with self.assertRaises(AssertionError):r.checked_capture(e,slot,directory,os.getpid(),SimpleNamespace(PIPE_CHUNK=65536),{})

    def test_rss_zero_requires_same_owned_initial_zombie(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();slot=slots(out)[1];directory=out/slot['directory'];directory.mkdir()
            _,active,record=capture_files(directory,slot);record['observed_peak_process_group_rss_bytes']=0
            save(directory/'process.json',record)
            with self.assertRaisesRegex(AssertionError,'initial owned zombie'):
                r.checked_capture(e,slot,directory,os.getpid(),SimpleNamespace(PIPE_CHUNK=65536),{})
            active['identity']['status']=record['identity']['status']=5
            save(directory/'active.json',active);save(directory/'process.json',record)
            capture,_=r.checked_capture(e,slot,directory,os.getpid(),SimpleNamespace(PIPE_CHUNK=65536),{})
            self.assertIsNone(capture['observed_peak_process_group_rss_bytes']);self.assertFalse(capture['memory_usage_qualified'])

    def test_native_failure_stops_fixed_schedule_without_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve()/'run';document=plan(out);calls=[];retained=[]
            def observe(command,environment,directory,payload,common,launched,**kwargs):
                calls.append(command);launched(1000+len(calls))
                for name in r.CAPTURE_FILES:(directory/name).write_bytes(b'{}' if name.endswith('.json') else b'')
                if len(calls)==2:raise RuntimeError('first fixture failed')
                for name in r.BUILD_FILES:(out/'build'/name).write_bytes(b'compiler output')
            def checked(helper,slot,directory,parent,kb,extra):
                return dict(id=slot['id'],pid=1001,started_at='2026-10-14T00:00:00+00:00',
                    finished_at='2026-10-14T00:00:01+00:00'),e.inventory(directory)[0]
            kb=SimpleNamespace(atomic=nullcontext,save=save,observe=observe)
            with patch.object(r,'verify_inputs'),patch.object(e,'pin'),patch.object(r,'checked_capture',side_effect=checked), \
                 patch.object(e,'validate_compile_inputs',return_value=[]), \
                 patch.object(e,'built_image_closure',return_value=dict(images={str(out/'build/io-faults.dylib'): {}})), \
                 patch.object(r,'finish',side_effect=lambda helper,report,*args:retained.append(copy.deepcopy(report))):
                with self.assertRaisesRegex(RuntimeError,'first fixture failed'):
                    r.run(e,a,SimpleNamespace(kb=kb),document,Path('/unused/plan'),'a'*64,intake(),{},{},None,[])
            self.assertEqual(len(calls),2);self.assertEqual(retained[0]['attempts'],['compile-io-interposer','arithmetic'])
            self.assertEqual(len(retained[0]['captures']),1);self.assertEqual(len(retained[0]['registered']),2)
            self.assertEqual(retained[0]['status'],'stopped-unqualified');self.assertIsNone(retained[0]['active'])

    def test_late_report_mutation_is_not_adopted(self):
        for where in ('save','input-replay'):
            with self.subTest(where=where),tempfile.TemporaryDirectory() as temp:
                out=Path(temp).resolve();checks=[]
                def writer(path,value):
                    save(path,value)
                    if where=='save':path.write_bytes(b'{}\n')
                def verify(*args):
                    checks.append(True)
                    if len(checks)==2 and where=='input-replay':(out/'report.json').write_bytes(b'{}\n')
                with patch.object(r,'verify_inputs',side_effect=verify),patch.object(e,'check_leases'):
                    with self.assertRaisesRegex(AssertionError,'Final integrity failed'):
                        r.finish(e,failure_report(),plan(out),out,{},{},SimpleNamespace(save=writer),[])
                terminal=json.loads((out/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed-integrity');self.assertFalse(terminal['common_mutex_held'])
                self.assertEqual(terminal['available_evidence'],{});self.assertEqual((out/'report.json').read_bytes(),b'{}\n')

    def test_final_named_lease_failure_cannot_claim_closed_success(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve()
            with patch.object(r,'verify_inputs'),patch.object(e,'check_leases',side_effect=AssertionError('lease replaced')):
                with self.assertRaisesRegex(AssertionError,'Final integrity failed'):
                    r.finish(e,failure_report(),plan(out),out,{},{},SimpleNamespace(save=save),[])
            terminal=json.loads((out/'terminal.json').read_bytes())
            self.assertFalse(terminal['common_mutex_held']);self.assertEqual(terminal['status'],'failed-integrity')

    def test_changed_validated_input_and_special_artifact_remain_failed_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();(out/'input').write_bytes(b'changed');os.mkfifo(out/'unsafe')
            report=failure_report();report['validated_files']['input']=dict(bytes=3,sha256=r.digest(b'old'))
            with patch.object(r,'verify_inputs'),patch.object(e,'check_leases'):
                with self.assertRaisesRegex(AssertionError,'Final integrity failed'):
                    r.finish(e,report,plan(out),out,{},{},SimpleNamespace(save=save),[])
            terminal=json.loads((out/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed-integrity')
            self.assertTrue(any(item['path']=='unsafe' for item in terminal['artifact_errors']))
            self.assertEqual((out/'input').read_bytes(),b'changed')


if __name__=='__main__':unittest.main()
