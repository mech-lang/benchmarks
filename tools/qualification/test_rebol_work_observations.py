"""Authored synthetic three-observation tests; no native child is started."""
from contextlib import nullcontext
import copy
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


def load(name, path):
    spec = importlib.util.spec_from_file_location(name,path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HERE = Path(__file__).resolve().parent
w = load('rebol_work_test_subject',HERE/'rebol_work_observations.py')
r = load('rebol_work_test_shared149',HERE/'rebol_bounded.py')
e = load('rebol_work_test_extension',HERE/'rebol_extension.py')


def save(path, value): path.write_bytes(w.encoded(value))


def cases():
    return [dict(benchmark=benchmark,case=case,n=n,expected_exit=0,validation='exact-complete-bytes',
        stdin=dict(path=f'{index}.stdin',bytes=0,sha256=w.digest(b'')),
        expected=dict(path=f'{index}.expected',bytes=len(raw),sha256=w.digest(raw)))
        for index,((benchmark,case),n,raw) in enumerate(zip(w.CASES,(4,27,0),(b'tree',b'pi',b'map')))]


def plan(output):
    return dict(output=str(output),primitive_review={},schedule=w.schedule(e,cases(),dict(path='/approved/extension.dylib'),output),
        unavailable_inputs=[],prerequisite_artifact_closures=[],prior_durable_jobs=[])


def native_files(directory,slot,index=0):
    pid = 9200+index
    identity = dict(pid=pid,ppid=os.getpid(),pgid=pid,birth_seconds=100,birth_microseconds=200,status=1)
    common = dict(command=slot['command'],environment=slot['environment'],cwd=str(directory),kind=w.KIND,
        started_at=f'2026-10-14T00:00:{index*2:02d}+00:00',process_timeout_seconds=180,cleanup_timeout_seconds=5,
        maximum_process_group_rss_bytes=slot['rss_limit_bytes'],native_file_limit_bytes=slot['native_file_limit_bytes'],
        stdout_capture_limit_bytes=slot['native_file_limit_bytes']+65536,stdout_transport='OS pipe, retained as received',
        stderr_transport='exclusive artifact',stdin_bytes=slot['stdin_bytes'],stdin_sha256=slot['stdin_sha256'],
        inherited_common_mutex=True,common_mutex_inode=79859134,benchmark_samples=0,source_work_qualified=False,chart_admission=False)
    start = dict(common,status='starting',native_process_started=False)
    active = dict(common,status='running',native_process_started=True,pid=pid,pgid=pid,identity=identity)
    stdout = (b'tree',b'pi',b'map')[index]
    stderr = b'complete map dump' if slot['consumer'] == 'map' else b''
    final = dict(active,status='failed' if stderr else 'native-passed',finished_at=f'2026-10-14T00:00:{index*2+1:02d}+00:00',
        leader_identity_before_reap=dict(identity,status=5),direct_child_reaped=True,remaining_process_group=[],
        stop_signals=[],cleanup_errors=[],exit_status=0,kernel_monitor_samples=2,observed_peak_process_group_rss_bytes=4096,
        stdout_bytes=len(stdout),stdout_sha256=w.digest(stdout),stderr_bytes=len(stderr),stderr_sha256=w.digest(stderr))
    if stderr:
        final.update(error_type='AssertionError',error='Unexpected stderr; raw bytes retained')
    for name,value in (('start',start),('active',active),('process',final)):
        save(directory/(name+'.json'),value)
    (directory/'stdout.bin').write_bytes(stdout)
    (directory/'stderr.bin').write_bytes(stderr)
    Path(slot['sidecar']).write_bytes(b'observed facts')
    return start,active,final


def consumers():
    return {name:SimpleNamespace(validate=lambda *args:dict(contract=True,chart_admission=False))
            for name in ('tree','pi','map')}


def empty_report():
    return dict(status='stopped-unqualified',attempts=[],registered=[],captures=[],active=None,validated_files={})


class WorkObservationTests(unittest.TestCase):
    def test_exact_three_commands_and_separate_map_stream_policy(self):
        output = Path('/fresh/output')
        slots = plan(output)['schedule']
        self.assertEqual(tuple(slot['id'] for slot in slots),w.IDS)
        self.assertEqual(slots[0]['command'][-2:],['4',slots[0]['sidecar']])
        self.assertEqual(slots[1]['command'][-1],'27')
        self.assertEqual(len(slots[2]['command']),4)
        for index,slot in enumerate(slots):
            self.assertEqual(slot['command'][:3],[str(e.RUNTIME),'-q','-s'])
            self.assertEqual(slot['timeout_seconds'],180)
            self.assertEqual(slot['rss_limit_bytes'],512*1024**2)
            self.assertEqual(slot['stdout_limit_bytes'],1024**2)
            self.assertEqual(slot['sidecar_limit_bytes'],1024**2)
            self.assertEqual(slot['native_file_limit_bytes'],(16 if index == 2 else 1)*1024**2)
            self.assertEqual(slot['stderr_limit_bytes'],slot['native_file_limit_bytes'])
            self.assertEqual(slot['expected_observer_stderr_failure'],index == 2)
            for key in ('DYLD_INSERT_LIBRARIES','DYLD_LIBRARY_PATH','DYLD_FRAMEWORK_PATH','MECH_REBOL_IO_FAULT_REPORT'):
                self.assertNotIn(key,slot['environment'])

    def test_other_cases_and_draft_source_review_rejected(self):
        changed = cases()
        changed[0]['case'] = 'n-21'
        with self.assertRaisesRegex(AssertionError,'three existing'):
            w.schedule(e,changed,dict(path='/image'),Path('/fresh'))
        value = dict(schema='rebol-three-work-observations-source-review-v1',
            status='independent-source-review-complete-native-observations-pending',independent_review=True,
            files={name:'a'*64 for name in w.FILES},dependencies={str(w.HELPER.relative_to(w.ROOT)):'b'*64},
            **{key:False for key in w.GATES})
        w.source_review(value)
        for change in (dict(status='draft'),dict(independent_review=False),dict(chart_admission=True),dict(files={})):
            with self.assertRaises(AssertionError):
                w.source_review(dict(value,**change))

    def test_source_review_digest_checked_before_loading_dependency(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp).resolve()/'review.json'
            path.write_bytes(b'{}\n')
            with patch.object(w,'load',side_effect=AssertionError('must not load')) as loader:
                with self.assertRaisesRegex(AssertionError,'source review changed'):
                    with w.held({}, {}, dict(path=str(path),sha256='f'*64)):
                        self.fail('unreachable')
                loader.assert_not_called()

    def test_original_map_failure_receipt_remains_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp).resolve()
            slot = plan(output)['schedule'][2]
            directory = output/slot['directory']
            directory.mkdir()
            native_files(directory,slot,2)
            before = (directory/'process.json').read_bytes()
            final,streams,sidecar,_ = w.native_capture(r,e,SimpleNamespace(PIPE_CHUNK=65536),slot,directory,os.getpid())
            self.assertEqual(final['status'],'failed')
            self.assertEqual(final['exit_status'],0)
            self.assertTrue(streams[1])
            self.assertEqual(sidecar,b'observed facts')
            self.assertEqual((directory/'process.json').read_bytes(),before)

    def test_map_exception_cannot_hide_an_unrelated_failure(self):
        for change in (dict(error='Native command exited unsuccessfully'),dict(error_type='TimeoutExpired'),
                       dict(status='native-passed'),dict(exit_status=1),dict(exit_status=False),
                       dict(stop_signals=[9]),dict(cleanup_errors=['failed']),dict(remaining_process_group=[1])):
            with self.subTest(change=change),tempfile.TemporaryDirectory() as temp:
                output = Path(temp).resolve()
                slot = plan(output)['schedule'][2]
                directory = output/slot['directory']
                directory.mkdir()
                _,_,final = native_files(directory,slot,2)
                final.update(change)
                save(directory/'process.json',final)
                with self.assertRaises(AssertionError):
                    w.native_capture(r,e,SimpleNamespace(PIPE_CHUNK=65536),slot,directory,os.getpid())

    def test_tree_and_pi_do_not_inherit_map_failure_exception(self):
        for index in (0,1):
            with tempfile.TemporaryDirectory() as temp:
                output = Path(temp).resolve()
                slot = plan(output)['schedule'][index]
                directory = output/slot['directory']
                directory.mkdir()
                _,_,final = native_files(directory,slot,index)
                final.update(status='failed',error_type='AssertionError',error='Unexpected stderr; raw bytes retained')
                save(directory/'process.json',final)
                with self.assertRaisesRegex(AssertionError,'Tree/Pi observer'):
                    w.native_capture(r,e,SimpleNamespace(PIPE_CHUNK=65536),slot,directory,os.getpid())

    def test_owned_birth_and_zero_rss_identity_are_required(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp).resolve()
            slot = plan(output)['schedule'][0]
            directory = output/slot['directory']
            directory.mkdir()
            _,active,final = native_files(directory,slot)
            original = copy.deepcopy(final)
            final['leader_identity_before_reap']['birth_microseconds'] += 1
            save(directory/'process.json',final)
            with self.assertRaisesRegex(AssertionError,'owned zero-exit'):
                w.native_capture(r,e,SimpleNamespace(PIPE_CHUNK=65536),slot,directory,os.getpid())
            final = original
            final['observed_peak_process_group_rss_bytes'] = 0
            save(directory/'process.json',final)
            with self.assertRaisesRegex(AssertionError,'initial owned zombie'):
                w.native_capture(r,e,SimpleNamespace(PIPE_CHUNK=65536),slot,directory,os.getpid())
            active['identity']['status'] = final['identity']['status'] = 5
            save(directory/'active.json',active)
            save(directory/'process.json',final)
            w.native_capture(r,e,SimpleNamespace(PIPE_CHUNK=65536),slot,directory,os.getpid())

    def test_consumer_must_accept_map_and_cannot_change_raw_sidecar(self):
        for mode in ('reject','mutate'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as temp:
                output = Path(temp).resolve()
                slot = plan(output)['schedule'][2]
                directory = output/slot['directory']
                directory.mkdir()
                native_files(directory,slot,2)
                (output/'2.expected').write_bytes(b'map')
                (output/'2.stdin').write_bytes(b'')
                selected = consumers()
                def validate(*args):
                    if mode == 'reject':
                        raise AssertionError('invalid map grammar')
                    Path(slot['sidecar']).write_bytes(b'changed')
                    return dict(contract=True)
                selected['map'] = SimpleNamespace(validate=validate)
                with patch.object(r,'CORPUS',output/'manifest.json'),self.assertRaises(AssertionError):
                    w.checked_case(r,e,None,selected,SimpleNamespace(PIPE_CHUNK=65536),slot,directory,os.getpid())

    def test_nonregular_sidecar_rejected_before_read(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp).resolve()
            slot = plan(output)['schedule'][0]
            directory = output/slot['directory']
            directory.mkdir()
            native_files(directory,slot)
            sidecar = Path(slot['sidecar'])
            sidecar.unlink()
            os.mkfifo(sidecar)
            with self.assertRaisesRegex(AssertionError,'Nonregular artifact'):
                w.native_capture(r,e,SimpleNamespace(PIPE_CHUNK=65536),slot,directory,os.getpid())

    def test_three_slot_run_accepts_only_reviewed_map_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            output = base/'run'
            corpus = base/'corpus'
            corpus.mkdir()
            document = plan(output)
            for index,raw in enumerate((b'tree',b'pi',b'map')):
                (corpus/f'{index}.expected').write_bytes(raw)
                (corpus/f'{index}.stdin').write_bytes(b'')
            calls = []
            def observe(command,environment,directory,payload,common,launched,**kwargs):
                index = len(calls)
                slot = document['schedule'][index]
                calls.append(command)
                launched(9200+index)
                native_files(directory,slot,index)
                if index == 2:
                    raise AssertionError('Unexpected stderr; raw bytes retained')
            kb = SimpleNamespace(PIPE_CHUNK=65536,atomic=nullcontext,save=save,observe=observe)
            with patch.object(r,'CORPUS',corpus/'manifest.json'),patch.object(r,'verify_inputs'), \
                 patch.object(e,'pin'),patch.object(e,'check_leases'):
                w.run(r,e,SimpleNamespace(observation=lambda raw:{}),consumers(),kb,document,
                      base/'plan','a'*64,{},{},None,[])
            terminal = json.loads((output/'terminal.json').read_bytes())
            report = json.loads((output/'report.json').read_bytes())
            self.assertEqual(len(calls),3)
            self.assertEqual(terminal['status'],w.SUCCESS)
            self.assertEqual(terminal['validated_observations'],3)
            self.assertEqual(report['captures'][2]['observer_status'],'failed')
            for gate in w.GATES:
                self.assertIs(terminal[gate],False)

    def test_first_unexpected_failure_stops_without_retry_and_retains_sidecar(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            output = base/'run'
            corpus = base/'corpus'
            corpus.mkdir()
            (corpus/'0.stdin').write_bytes(b'')
            document = plan(output)
            calls = []
            def observe(command,environment,directory,payload,common,launched,**kwargs):
                calls.append(command)
                launched(9200)
                _,_,final = native_files(directory,document['schedule'][0])
                final.update(status='failed',error_type='AssertionError',error='Unexpected stderr; raw bytes retained')
                save(directory/'process.json',final)
                raise AssertionError('Unexpected stderr; raw bytes retained')
            kb = SimpleNamespace(PIPE_CHUNK=65536,atomic=nullcontext,save=save,observe=observe)
            with patch.object(r,'CORPUS',corpus/'manifest.json'),patch.object(r,'verify_inputs'), \
                 patch.object(e,'pin'),patch.object(e,'check_leases'):
                with self.assertRaisesRegex(AssertionError,'Unexpected stderr'):
                    w.run(r,e,None,consumers(),kb,document,base/'plan','a'*64,{},{},None,[])
            terminal = json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(len(calls),1)
            self.assertEqual(terminal['status'],'stopped-unqualified')
            self.assertEqual(terminal['validated_observations'],0)
            self.assertEqual(Path(document['schedule'][0]['sidecar']).read_bytes(),b'observed facts')

    def test_report_mutation_and_lost_final_lease_cannot_claim_success(self):
        for phase in ('save','replay','lease'):
            with self.subTest(phase=phase),tempfile.TemporaryDirectory() as temp:
                output = Path(temp).resolve()
                calls = []
                def writer(path,value):
                    save(path,value)
                    if phase == 'save':
                        path.write_bytes(b'{}\n')
                def verify(*args):
                    calls.append(True)
                    if phase == 'replay' and len(calls) == 2:
                        (output/'report.json').write_bytes(b'{}\n')
                def leases(*args):
                    if phase == 'lease':
                        raise AssertionError('named lease replaced')
                with patch.object(r,'verify_inputs',side_effect=verify),patch.object(e,'check_leases',side_effect=leases):
                    with self.assertRaisesRegex(AssertionError,'Final integrity failed'):
                        w.finish(r,e,SimpleNamespace(save=writer),empty_report(),plan(output),output,{},{},[])
                terminal = json.loads((output/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed-integrity')
                self.assertFalse(terminal['common_mutex_held'])


if __name__ == '__main__':
    unittest.main()
