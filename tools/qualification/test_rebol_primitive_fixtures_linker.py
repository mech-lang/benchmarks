"""Focused linker-option and retained-failure regression checks; no native work."""
from copy import deepcopy
from pathlib import Path
import hashlib,json,types,unittest

SOURCE=Path(__file__).with_name('rebol_primitive_fixtures_linker.py')
m=types.ModuleType('linker_under_test');m.__file__=str(SOURCE);exec(compile(SOURCE.read_bytes(),str(SOURCE),'exec'),m.__dict__)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def base():
    b=types.ModuleType('combined_reference');b.__file__=str(m.BASE);exec(compile(m.BASE.read_bytes(),str(m.BASE),'exec'),b.__dict__)
    return b.load_controller(m.BASE_SHA)

class LinkerTests(unittest.TestCase):
    def test_only_exact_linker_token_changes_in_nineteen_slots(self):
        before=base();after=m.load_controller(sha(SOURCE))
        helper=types.SimpleNamespace(RUNTIME=Path('/runtime'),SUPPORT=Path('/support'),environment=lambda p:dict(PATH='/bin',HOME=str(p/'home')))
        intake=dict(tools=dict(clang=dict(path='/clang'),linker=dict(path='/ld'),runtime=dict(path='/runtime')),target='arm64-apple-macos',include_roots=dict(macos_sdk='/sdk',clang_resource='/resource/include'))
        transport=types.ModuleType('transport');transport.__file__=str(before.ADAPTER);exec(compile(before.ADAPTER.read_bytes(),str(before.ADAPTER),'exec'),transport.__dict__)
        spec=json.loads((before.ORIGINAL/'spec.json').read_bytes());output=Path('/fresh');image=dict(path='/image.rebx',sha256='1'*64)
        original=before.schedule(helper,transport,spec,intake,image,output);actual=after.schedule(helper,transport,spec,intake,image,output)
        self.assertEqual(len(actual),19);self.assertEqual(actual[1:],original[1:]);expected=deepcopy(original[0]);i=expected['command'].index('-fuse-ld=/ld');expected['command'][i]='--ld-path=/ld';self.assertEqual(actual[0],expected)
        self.assertEqual(after.__file__,before.__file__);self.assertEqual(after.intake_adapter,m.BASE_INTAKE_ADAPTER)
        for name in ('schedule','observe_case','checked_capture','run','finish'):
            self.assertEqual(getattr(before,name).__code__.co_code,getattr(after,name).__code__.co_code)
        self.assertIs(after.validate_prior_failure,m.validate_prior_failure)
        with self.assertRaises(AssertionError):m.load_controller('0'*64)

    def test_ambiguous_or_different_linker_option_is_rejected(self):
        for argv in (['-fuse-ld=/other'],['-fuse-ld=/ld','-fuse-ld=/ld'],['-fuse-ld=/ld','--ld-path=/ld']):
            f=types.SimpleNamespace(bootstrap=lambda *x:None,held=lambda *x:None,compile_slot=lambda *x:dict(command=list(argv)),build_plan=lambda *x:None,verify_inputs=lambda *x:None)
            adapted=m.attach(f,dict(path=str(SOURCE),sha256=sha(SOURCE)))
            with self.assertRaises(AssertionError):adapted.compile_slot(None,dict(tools=dict(linker=dict(path='/ld'))),Path('/output'))

    def test_prior_failure_outputs_and_inventory_cannot_be_promoted(self):
        planref=dict(path='/prior/plan',sha256='1'*64);reportref=dict(path='/prior/report',sha256='2'*64);terminalref=dict(path='/prior/terminal',sha256='3'*64)
        inventory={'process.json':dict(bytes=1,sha256='4'*64)};jobinventory={'terminal.json':dict(bytes=2,sha256='5'*64)}
        review=dict(schema='rebol-fixed19-independent-failed-closure-v1',status='diagnostic-compiler-failure-preserved-owned-stage-closed',native_attempts=1,validated_captures=0,rebol_fixture_processes=0,compiler_exit_status=1,compiler_outputs=[],plan=planref,report=reportref,terminal=terminalref,artifacts=inventory,durable=dict(directory='/prior/job',artifacts=jobinventory,lease=dict(path='/prior/job/owner.lock',device=1,inode=2)))
        plan=dict(intake_adapter=m.BASE_INTAKE_ADAPTER,source_review=m.BASE_REVIEW,output='/prior/output')
        report=dict(status='stopped-unqualified',captures=[],attempts=['compile-io-interposer'],active=None,integrity_errors=[],artifact_errors=[],pins={},input_resolutions={})
        terminal=dict(status='stopped-unqualified',integrity_errors=[],artifact_errors=[],common_mutex_held=True,native_processes_started=1,validated_captures=0,report_sha256='2'*64,expected_report_sha256='2'*64)
        documents={m.FAILURE['path']:review,'/prior/plan':plan,'/prior/report':report,'/prior/terminal':terminal};snapshots={'/prior/output':deepcopy(inventory),'/prior/job':deepcopy(jobinventory)};pins=[]
        helper=types.SimpleNamespace(document=lambda ref,*x:deepcopy(documents[ref['path']]),inventory=lambda p,*x:(deepcopy(snapshots[str(p)]),[]),pin=lambda *x:pins.append(x))
        failure,closure=m.validate_prior_failure(helper,{},{});self.assertEqual(failure['durable'],review['durable']);self.assertEqual(closure,dict(directory='/prior/output',artifacts=inventory));self.assertEqual(len(pins),2)
        report['status']='complete'
        with self.assertRaises(AssertionError):m.validate_prior_failure(helper,{},{})
        report['status']='stopped-unqualified';snapshots['/prior/job']={}
        with self.assertRaises(AssertionError):m.validate_prior_failure(helper,{},{})

if __name__=='__main__':unittest.main()
