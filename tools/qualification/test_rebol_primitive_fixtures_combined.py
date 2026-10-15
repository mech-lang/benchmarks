"""Focused synthetic checks for combined extension intake; no native commands."""
from contextlib import contextmanager,ExitStack
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

SOURCE=Path(__file__).with_name('rebol_primitive_fixtures_combined.py')
m=types.ModuleType('combined_under_test');m.__file__=str(SOURCE)
exec(compile(SOURCE.read_bytes(),str(SOURCE),'exec'),m.__dict__)
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def original():
    value=types.ModuleType('original_fixture_reference');value.__file__=str(m.ORIGINAL)
    exec(compile(m.ORIGINAL.read_bytes(),str(m.ORIGINAL),'exec'),value.__dict__);return value
def disposition():return json.loads(m.COMBINED.read_bytes())

class CombinedTests(unittest.TestCase):
    def test_actual_six_attempt_scope_rejects_fabricated_four_success(self):
        value=disposition();m.check_disposition(value)
        for key,replacement in (('native_attempts',4),('native_processes',4),('failed_loads',0),('extension_abi_qualified',False),('full_primitive_fixtures_qualified',True)):
            bad=deepcopy(value);bad[key]=replacement
            with self.assertRaises(AssertionError):m.check_disposition(bad)
        bad=deepcopy(value);bad['durables'][0]['exit_code']=0
        with self.assertRaises(AssertionError):m.check_disposition(bad)

    def test_alias_must_preserve_original_exact_image(self):
        for change in ('sha','copy','rebuild'):
            value=disposition()
            if change=='sha':value['built_image']['sha256']='0'*64
            elif change=='copy':value['image_copy']['byte_identical']=False
            else:value['image_copy']['binary_rebuilt']=True
            with self.assertRaises(AssertionError):m.check_disposition(value)

    def test_reusable_loader_keeps_original_runner_and_identity(self):
        fixed=original();loaded=m.load_controller(sha(SOURCE))
        self.assertEqual(loaded.__file__,str(m.ORIGINAL));self.assertEqual(loaded.ROOT,m.ROOT)
        for name in ('schedule','observe_case','checked_capture','run','finish','expected_files','check_durable_controller'):
            self.assertEqual(getattr(loaded,name).__code__.co_code,getattr(fixed,name).__code__.co_code)
            self.assertEqual(getattr(loaded,name).__code__.co_consts,getattr(fixed,name).__code__.co_consts)
        with self.assertRaises(AssertionError):m.load_controller('0'*64)

    def test_only_interposer_slot_gains_official_include_root(self):
        fixed=original();loaded=m.load_controller(sha(SOURCE))
        helper=types.SimpleNamespace(RUNTIME=Path('/runtime'),SUPPORT=Path('/support'),environment=lambda p:dict(PATH='/bin',HOME=str(p/'home')))
        intake=dict(tools=dict(clang=dict(path='/clang'),linker=dict(path='/ld'),runtime=dict(path='/runtime')),target='arm64-apple-macos',include_roots=dict(macos_sdk='/sdk',clang_resource='/resource/include'))
        transport=types.ModuleType('original_transport');transport.__file__=str(fixed.ADAPTER)
        exec(compile(fixed.ADAPTER.read_bytes(),str(fixed.ADAPTER),'exec'),transport.__dict__)
        spec=json.loads((fixed.ORIGINAL/'spec.json').read_bytes());output=Path('/fresh');image=dict(path='/image.rebx',sha256='1'*64)
        before=fixed.schedule(helper,transport,spec,intake,image,output);after=loaded.schedule(helper,transport,spec,intake,image,output)
        self.assertEqual(len(after),19);self.assertEqual(after[1:],before[1:])
        expected=deepcopy(before[0]);index=expected['command'].index('-MD');expected['command'][index:index]=['-isystem',str(m.HEADER_ROOT)]
        self.assertEqual(after[0],expected)
        self.assertTrue(all(x['command'][1:3]==['-q','-s'] and x['environment']['MECH_CLBG_REBOL_PRIMITIVES']=='/image.rebx' for x in after[1:]))

    def test_all_three_durable_inventories_replayed(self):
        loaded=m.load_controller(sha(SOURCE));seen=[];snapshots={f'/job{i}':{'terminal.json':dict(bytes=1,sha256=str(i)*64)} for i in range(3)}
        helper=types.SimpleNamespace(verify=lambda *args:seen.append('pins'),inventory=lambda p,ignored=(): (snapshots[str(p)],[]),check_leases=lambda x:seen.append('leases'))
        plan=dict(unavailable_inputs=[],prerequisite_artifact_closures=[],extension_durables=[dict(stage=stage,directory=f'/job{i}',artifacts=deepcopy(snapshots[f'/job{i}'])) for i,stage in enumerate(m.STAGES)])
        loaded.verify_inputs(helper,plan,{}, {},[]);self.assertEqual(seen,['pins','leases'])
        snapshots['/job1']={}
        with self.assertRaises(AssertionError):loaded.verify_inputs(helper,plan,{}, {},[])
        plan['extension_durables'].pop()
        with self.assertRaises(AssertionError):loaded.verify_inputs(helper,plan,{}, {},[])

    def test_combined_lease_list_does_not_mutate_outer_owner(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp).resolve();value=disposition();paths=[]
            for i in range(8):
                p=base/f'lease{i}';p.write_bytes(b'');paths.append(p)
            for i,item in enumerate(value['durables'],5):
                # The real API requires owner.lock beneath each distinct job.
                job=base/f'job{i}';job.mkdir();p=job/'owner.lock';p.write_bytes(b'');paths[i]=p;s=p.stat()
                item.update(directory=str(job),lease=dict(path=str(p),device=s.st_dev,inode=s.st_ino))
            combined=base/'combined.json';combined.write_text(json.dumps(value))
            review=base/'review.json';review.write_text(json.dumps(dict(schema='rebol-combined-primitive-controller-source-review-v1',status='independent-source-review-complete-native-fixtures-pending',independent_review=True,files={n:sha(m.ROOT/n) for n in m.SOURCE_FILES},dependencies=m.DEPENDENCIES,**{k:False for k in m.GATES})))
            checked=[];outer=[]
            def check(leases):
                self.assertTrue(all(not s.closed and (os.fstat(s.fileno()).st_dev,os.fstat(s.fileno()).st_ino)==identity for p,s,identity in leases));checked.append(len(leases))
            @contextmanager
            def inherited(ref):
                with ExitStack() as stack:
                    for p in paths[:5]:
                        s=stack.enter_context(p.open('rb'));v=p.stat();outer.append((p,s,(v.st_dev,v.st_ino)))
                    try:yield outer[0][1],outer,{}, {},{}
                    finally:self.assertEqual(len(outer),5);check(outer)
            helper=types.SimpleNamespace(ROOT=m.ROOT,__file__=str(m.ROOT/'tools/qualification/rebol_extension.py'),held_inputs=inherited,document=lambda ref,*args:json.loads(Path(ref['path']).read_bytes()),pin=lambda *args:None,regular=lambda p:p.open('rb'),check_leases=check,read_bytes=lambda p:Path(p).read_bytes(),load_support=lambda *args:None)
            frozen=original();rebx=types.SimpleNamespace(load_controller=lambda expected:types.SimpleNamespace(load_helper=lambda:helper))
            with patch.object(m,'COMBINED',combined),patch.object(m,'COMBINED_SHA',sha(combined)):
                loaded=m.attach(frozen,dict(path=str(SOURCE),sha256=sha(SOURCE)),rebx)
                with loaded.held(dict(path=str(combined),sha256=sha(combined)),dict(path=str(review),sha256=sha(review))) as values:self.assertEqual(len(values[4]),8)
            self.assertEqual(checked,[8,8,5]);self.assertTrue(all(s.closed for p,s,identity in outer))

if __name__=='__main__':unittest.main()
