"""Pure temporary-file tests; no Julia, LLVM, preparation or runtime hashing."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('adapter',Path(__file__).with_name('julia_native_inspection_metadata.py'))
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)


class MetadataTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name).resolve();self.old=self.root/'old';self.old.mkdir()
        self.patch=patch.object(m,'OLD_ROOT',self.old);self.patch.start();self.addCleanup(self.patch.stop)
        self.target=self.root/'archive/result.json';self.target.parent.mkdir();self.target.write_bytes(b'{"saved":true}\n')
        self.row=dict(original_path=str(self.old/'result.json'),archived_path='archive/result.json',
                      sha256=hashlib.sha256(self.target.read_bytes()).hexdigest(),bytes=self.target.stat().st_size)
        self.resolver=m.ExactMetadata(self.root,[self.row])

    def pin(self,pins,path,expected=None):
        path=m.regular(path);digest=m.digest(path)
        if expected is not None:m.require(digest==expected,'pin differs')
        pins[str(path)]=digest;return path

    def test_exact_mapping_retains_historical_digest(self):
        pins={};result=self.resolver.pin(self.pin,pins,self.row['original_path'],self.row['sha256'])
        self.assertEqual(result,self.target);self.assertEqual(pins,{str(self.target):self.row['sha256']})
        self.assertEqual(self.resolver.used,{self.row['original_path']});self.resolver.check()

    def test_wrong_historical_digest_rejected(self):
        with self.assertRaisesRegex(AssertionError,'pin differs'):
            self.resolver.pin(self.pin,{},self.row['original_path'],'0'*64)

    def test_unmapped_missing_path_has_no_fallback(self):
        with self.assertRaises(FileNotFoundError):
            self.resolver.pin(self.pin,{},self.old/'other.json','0'*64)

    def test_changed_target_rejected(self):
        self.target.write_bytes(b'bad')
        with self.assertRaisesRegex(AssertionError,'Archived evidence changed'):self.resolver.check()

    def test_reappeared_old_path_rejected_even_exact_bytes(self):
        Path(self.row['original_path']).write_bytes(self.target.read_bytes())
        with self.assertRaisesRegex(AssertionError,'reappeared'):self.resolver.check()
        with self.assertRaisesRegex(AssertionError,'reappeared'):
            self.resolver.pin(self.pin,{},self.row['original_path'],self.row['sha256'])

    def test_target_symlink_and_fifo_rejected_without_read(self):
        other=self.root/'other';other.write_bytes(self.target.read_bytes());self.target.unlink();self.target.symlink_to(other)
        with self.assertRaisesRegex(AssertionError,'Physical absolute'):self.resolver.check()
        self.target.unlink();m.os.mkfifo(self.target)
        with self.assertRaisesRegex(AssertionError,'Regular metadata'):self.resolver.check()

    def test_binary_kinds_and_duplicate_names_rejected(self):
        for suffix in ('.bc','.a','.o','.dylib',''):
            row=dict(self.row,archived_path='archive/image'+suffix)
            with self.assertRaises(AssertionError):m.ExactMetadata(self.root,[row])
        with self.assertRaisesRegex(AssertionError,'Duplicate'):
            m.ExactMetadata(self.root,[self.row,self.row])

    def fake(self):
        module=types.SimpleNamespace();module.pin=self.pin
        def verify(pins,resolutions,unavailable=()):
            for p,h in pins.items():self.assertEqual(m.digest(p),h);self.assertEqual(str(Path(p).resolve()),resolutions[p])
        module.verify=verify
        def build(output):
            pins={};module.pin(pins,self.row['original_path'],self.row['sha256'])
            return dict(pins=pins,input_resolutions={},commands=[{'argv':['llvm-dis','physical.bc','-o','-']}],
                        native_commands=11,benchmark_samples=0,chart_admission=False)
        module.build_plan=build;module.finish=lambda report,plan,*args:report
        module.main=lambda:'unchanged main';return module

    def bindings(self):
        files={}
        for name in ('ORIGINAL','ADAPTER','MANIFEST','LINK_RESULT'):
            path=self.root/(name+'.json');path.write_text(name);files[name]=path
        index=self.root/'index.tsv';index.write_text('exact row')
        self.stack=[]
        for name,value in files.items():
            p=patch.object(m,name,value);p.start();self.stack.append(p)
            if name!='ADAPTER':
                p=patch.object(m,name+'_SHA',m.digest(value));p.start();self.stack.append(p)
        p=patch.object(m,'reviewed_mapping',return_value=(self.resolver,index));p.start();self.stack.append(p)
        self.addCleanup(lambda:[p.stop() for p in reversed(self.stack)])
        return files,index

    def test_plan_binds_adapter_manifest_original_and_exact_mappings(self):
        files,index=self.bindings();original=self.fake();main=original.main
        m.install(original);plan=original.build_plan(self.root/'run')
        self.assertIs(original.main,main)
        self.assertEqual(plan['commands'],[{'argv':['llvm-dis','physical.bc','-o','-']}])
        self.assertEqual(plan['native_commands'],11);self.assertFalse(plan['chart_admission'])
        for p in (*files.values(),index,self.target):self.assertEqual(plan['pins'][str(p)],m.digest(p))
        self.assertEqual(plan['controller'],str(files['ADAPTER']))
        self.assertEqual(plan['historical_evidence_mappings'][0]['original_path'],self.row['original_path'])
        original.verify(plan['pins'],plan['input_resolutions'])
        report=original.finish({},plan)
        self.assertEqual(report['entry_adapter']['sha256'],m.digest(files['ADAPTER']))

    def test_verify_rejects_change_during_original_verification(self):
        self.bindings();original=self.fake()
        original.verify=lambda *args:self.target.write_bytes(b'changed during replay')
        m.install(original);plan=original.build_plan(self.root/'run')
        with self.assertRaisesRegex(AssertionError,'Archived evidence changed'):
            original.verify(plan['pins'],plan['input_resolutions'])

    def test_verify_rejects_old_path_appearing_during_replay(self):
        self.bindings();original=self.fake()
        original.verify=lambda *args:Path(self.row['original_path']).write_bytes(b'late')
        m.install(original);plan=original.build_plan(self.root/'run')
        with self.assertRaisesRegex(AssertionError,'reappeared'):
            original.verify(plan['pins'],plan['input_resolutions'])

    def test_manifest_change_after_plan_rejected(self):
        files,_=self.bindings();original=m.install(self.fake());plan=original.build_plan(self.root/'run')
        files['MANIFEST'].write_bytes(b'new mapping')
        with self.assertRaisesRegex(AssertionError,'manifest changed'):
            original.verify(plan['pins'],plan['input_resolutions'])


if __name__=='__main__':unittest.main()
