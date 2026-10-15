"""Focused remaining-fixture schedule, preservation and finalization checks."""
from contextlib import nullcontext
from copy import deepcopy
from pathlib import Path
import hashlib,json,tempfile,types,unittest

SOURCE=Path(__file__).with_name('rebol_primitive_remaining.py')
m=types.ModuleType('remaining_test');m.__file__=str(SOURCE);exec(compile(SOURCE.read_bytes(),str(SOURCE),'exec'),m.__dict__)
sha=lambda raw:hashlib.sha256(raw).hexdigest()
def base():
    b=types.ModuleType('linker_reference');b.__file__=str(m.BASE);exec(compile(m.BASE.read_bytes(),str(m.BASE),'exec'),b.__dict__)
    return b.load_controller(m.BASE_SHA)

class Files:
    def __init__(self):self.inventory_hook=None;self.sha_hook=None
    def inventory(self,path,excluded=(),tolerant=False):
        if self.inventory_hook:self.inventory_hook(Path(path),excluded)
        return {str(p.relative_to(path)):dict(bytes=len(p.read_bytes()),sha256=sha(p.read_bytes()))
            for p in sorted(Path(path).rglob('*')) if p.is_file() and str(p.relative_to(path)) not in excluded},[]
    def read_bytes(self,path):return Path(path).read_bytes()
    def sha(self,path):
        if self.sha_hook:self.sha_hook(Path(path))
        return sha(Path(path).read_bytes())
    def pin(self,*args):pass
    def check_leases(self,leases):pass
    def now(self):return '2026-10-15T00:00:00+00:00'

def harness(root,fail=False):
    e=Files();f=types.SimpleNamespace(GATES=('chart_admission','full_primitive_fixtures_qualified'),
        CAPTURE_FILES={'start.json','active.json','process.json','stdout.bin','stderr.bin'},verify_inputs=lambda *args:None)
    kb=types.SimpleNamespace(atomic=lambda:nullcontext(),save=lambda p,v:Path(p).write_bytes(m.encoded(v)))
    output=root/'run';slots=[]
    for index,name in enumerate(('regex','gc-ownership')):
        slots.append(dict(id=name,directory=str(index)+'-'+name,case=dict(id=name),input_path=str(output/'inputs'/(name+'.bin')),
            stdin_bytes=0,stdin_sha256=sha(b''),timeout_seconds=180,rss_limit_bytes=536870912,stream_limit_bytes=1048576,sidecars={}))
    plan=dict(output=str(output),schedule=slots,extension_review={},remaining_adapter={},prior_linker_stage={})
    calls=[]
    def observe(e,adapter,kb,slot,output,common,launched):
        calls.append(slot['id']);directory=output/slot['directory'];launched(100+len(calls))
        record=dict(pid=100+len(calls),cleanup_errors=[],direct_child_reaped=True,remaining_process_group=[])
        for name in f.CAPTURE_FILES|{'transport.json'}:
            (directory/name).write_bytes(m.encoded(record) if name=='process.json' else b'')
        if fail:raise AssertionError('synthetic native fixture failure')
        return dict(id=slot['id']),{}
    f.observe_case=observe
    f.exact_snapshot=lambda e,p:(p.read_bytes(),dict(bytes=len(p.read_bytes()),sha256=sha(p.read_bytes())))
    f.checked_capture=lambda e,slot,directory,parent,kb,extra:(dict(id=slot['id'],pid=100+len(calls),started_at=e.now(),finished_at=e.now()),e.inventory(directory)[0])
    f.finish=lambda *args:m.finish(f,*args)
    adapter=types.SimpleNamespace(case_bytes=lambda case:(b'',b''))
    return f,e,kb,plan,adapter,calls

class RemainingTests(unittest.TestCase):
    def test_exact_sixteen_slots_reuse_capture_helpers_and_old_interposer(self):
        before=base();after=m.load_controller(sha(SOURCE.read_bytes()))
        e=types.SimpleNamespace(RUNTIME=Path('/runtime'),SUPPORT=Path('/support'),environment=lambda p:dict(PATH='/bin',HOME=str(p/'home')))
        intake=dict(tools=dict(clang=dict(path='/clang'),linker=dict(path='/ld'),runtime=dict(path='/runtime')),target='arm64-apple-macos',include_roots=dict(macos_sdk='/sdk',clang_resource='/resource/include'))
        transport=types.ModuleType('transport');transport.__file__=str(before.ADAPTER);exec(compile(before.ADAPTER.read_bytes(),str(before.ADAPTER),'exec'),transport.__dict__)
        spec=json.loads((before.ORIGINAL/'spec.json').read_bytes());output=Path('/fresh');image=dict(path='/image.rebx',sha256='1'*64)
        original=before.schedule(e,transport,spec,intake,image,output);actual=after.schedule(e,transport,spec,intake,image,output)
        expected=deepcopy(original[3:]);expected[0]['command'][3]=m.REGEX['path'];expected[-1]['environment']['DYLD_INSERT_LIBRARIES']=m.INTERPOSER['path']
        self.assertEqual(actual,expected);self.assertEqual(len(actual),16)
        self.assertFalse(any(s['id'] in ('compile-io-interposer','arithmetic','formatting') for s in actual))
        self.assertEqual(after.__file__,before.__file__);self.assertEqual(after.SUCCESS,m.SUCCESS)
        for name in ('observe_case','checked_capture'):
            self.assertEqual(getattr(after,name).__code__.co_code,getattr(before,name).__code__.co_code)
        self.assertEqual(after.linker_adapter,before.linker_adapter);self.assertEqual(after.intake_adapter,before.intake_adapter)
        with self.assertRaises(AssertionError):m.load_controller('0'*64)

    def test_different_schedule_cannot_silently_skip_successes(self):
        with self.assertRaises(AssertionError):m.remaining_schedule(lambda *args:[],None,None,None,None,None,Path('/new'))

    def test_prior_success_or_missing_failed_capture_is_not_accepted(self):
        f=base();after=m.attach(f,dict(path=str(SOURCE),sha256=sha(SOURCE.read_bytes())))
        review=dict(schema='rebol-fixed19-linker-independent-failed-closure-v1',status='regex-fixture-failure-preserved-owned-stage-closed',native_attempts=4,validated_captures=3,successful_fixture_processes=2,unstarted_fixture_processes=15,plan=dict(path='/plan'),report=dict(path='/report',sha256='1'*64),terminal=dict(path='/terminal'))
        plan=dict(linker_adapter=dict(path=str(m.BASE),sha256=m.BASE_SHA),source_review=m.BASE_REVIEW,entrypoint=str(m.BASE))
        report=dict(plan='/plan',plan_sha256='2'*64,status='complete',attempts=['compile-io-interposer','arithmetic','formatting','regex'])
        docs={m.PRIOR['path']:review,'/plan':plan,'/report':report,'/terminal':dict(status='complete')}
        e=types.SimpleNamespace(document=lambda ref,*args:deepcopy(docs[ref['path']]))
        # A malformed record fails before any inventory or path is consumed.
        review['plan']['sha256']='2'*64
        with self.assertRaises(AssertionError):after.validate_prior_linker(e,None,None,{},{})
        review['native_attempts']=3
        with self.assertRaises(AssertionError):after.validate_prior_linker(e,None,None,{},{})

    def test_fixture_only_run_counts_schedule_not_hardcoded_nineteen(self):
        with tempfile.TemporaryDirectory() as name:
            f,e,kb,plan,adapter,calls=harness(Path(name));m.run(f,e,adapter,types.SimpleNamespace(kb=kb),plan,Path('/plan'),'0'*64,{}, {},{},None,[])
            out=Path(plan['output']);report=json.loads((out/'report.json').read_bytes());terminal=json.loads((out/'terminal.json').read_bytes())
            self.assertEqual(calls,['regex','gc-ownership']);self.assertFalse((out/'build').exists())
            self.assertEqual(report['schema'],'rebol-primitive-remaining-results-v1');self.assertEqual(terminal['schema'],'rebol-primitive-remaining-terminal-v1')
            self.assertEqual(report['status'],m.SUCCESS);self.assertEqual(terminal['status'],m.SUCCESS)
            self.assertEqual(terminal['native_processes_started'],2);self.assertEqual(terminal['diagnostic_compilations'],0)
            self.assertFalse(terminal['chart_admission']);self.assertEqual(terminal['report_sha256'],sha((out/'report.json').read_bytes()))

    def test_first_failure_is_retained_without_later_fixture_or_retry(self):
        with tempfile.TemporaryDirectory() as name:
            f,e,kb,plan,adapter,calls=harness(Path(name),True)
            with self.assertRaisesRegex(AssertionError,'synthetic native fixture failure'):
                m.run(f,e,adapter,types.SimpleNamespace(kb=kb),plan,Path('/plan'),'0'*64,{}, {},{},None,[])
            out=Path(plan['output']);terminal=json.loads((out/'terminal.json').read_bytes())
            self.assertEqual(calls,['regex']);self.assertFalse((out/plan['schedule'][1]['directory']).exists())
            self.assertEqual(terminal['status'],'stopped-unqualified');self.assertEqual(terminal['validated_captures'],0)
            self.assertTrue((out/plan['schedule'][0]['directory']/'process.json').is_file())
            self.assertTrue(Path(plan['schedule'][1]['input_path']).is_file())

    def test_final_report_mutation_cannot_produce_success_terminal(self):
        with tempfile.TemporaryDirectory() as name:
            f,e,kb,plan,adapter,calls=harness(Path(name))
            e.sha_hook=lambda p:p.write_bytes(p.read_bytes()+b' ')
            with self.assertRaisesRegex(AssertionError,'Final integrity failed'):
                m.run(f,e,adapter,types.SimpleNamespace(kb=kb),plan,Path('/plan'),'0'*64,{}, {},{},None,[])
            terminal=json.loads((Path(plan['output'])/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed-integrity');self.assertFalse(terminal['common_mutex_held'])
            self.assertIsNone(terminal['report_sha256']);self.assertIn('Final report digest differs',terminal['integrity_errors'])

if __name__=='__main__':unittest.main()
