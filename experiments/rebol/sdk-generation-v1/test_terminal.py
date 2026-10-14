"""Temporary-file closure faults only; no runtime, SDK intake or native process."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('sdk_terminal_fixture',ROOT/'tools/qualification/rebol_sdk.py')
C=importlib.util.module_from_spec(spec);spec.loader.exec_module(C)


class Terminal(unittest.TestCase):
    def setUp(self):
        temporary=tempfile.TemporaryDirectory();self.addCleanup(temporary.cleanup)
        self.root=Path(temporary.name).resolve();self.output=self.root/'output';self.copy=self.root/'copy'
        self.output.mkdir();self.copy.mkdir()
        self.input=self.root/'input';self.input.write_bytes(b'fixed input')
        self.header=self.copy/'src/include/gen-funcs.h';self.header.parent.mkdir(parents=True)
        self.header.write_bytes(b'validated header')
        (self.output/'header-generation.json').write_text('{"pid":4321}')
        (self.output/'header-generation.stdout').write_bytes(b'complete output')
        self.validated,errors=C.artifact_pins((self.output,self.copy));self.assertEqual(errors,[])
        self.pins={str(self.input):C.sha(self.input)}
        self.result=dict(status='vendor-SDK-generated-awaiting-header-and-extension-ABI-review',
            native_commands_started=0,chart_admission=False,generated_files={'src/include/gen-funcs.h':C.sha(self.header)})

    def finish(self,check_leases=lambda:None):
        return C.retain_terminal(self.output,self.copy,self.result,self.pins,
                                 validated=self.validated,check_leases=check_leases)

    def terminal(self):return json.loads((self.output/'terminal.json').read_bytes())

    def test_complete_closure_binds_exact_report_and_validated_artifacts(self):
        events=[]
        errors,artifacts=self.finish(lambda:events.append('leases'))
        self.assertEqual((errors,artifacts),([],[]));self.assertGreaterEqual(len(events),3)
        terminal=self.terminal();report=self.output/'report.json'
        self.assertEqual(terminal['report_sha256'],C.sha(report))
        self.assertEqual(terminal['available_evidence_pins'],dict(self.validated,**{str(report):C.sha(report)}))
        self.assertTrue(terminal['common_mutex_held']);self.assertFalse(terminal['chart_admission'])

    def test_generated_header_change_cannot_be_adopted_as_success(self):
        self.header.write_bytes(b'changed after validation')
        errors,_=self.finish()
        self.assertTrue(errors);self.assertEqual(self.terminal()['status'],'failed-terminal-integrity')
        self.assertEqual(self.header.read_bytes(),b'changed after validation')

    def test_new_file_before_terminal_inventory_cannot_extend_validated_success(self):
        (self.copy/'unexpected.c').write_bytes(b'new vendor source')
        errors,_=self.finish()
        self.assertTrue(errors);self.assertEqual(self.terminal()['status'],'failed-terminal-integrity')

    def test_deleted_file_before_terminal_inventory_is_rejected(self):
        self.header.unlink()
        errors,_=self.finish()
        self.assertTrue(errors);self.assertEqual(self.terminal()['status'],'failed-terminal-integrity')

    def test_prerequisite_change_after_report_write_fails(self):
        original=C.new_json
        def write(path,value):
            result=original(path,value)
            if path.name=='report.json':self.input.write_bytes(b'late changed input')
            return result
        with patch.object(C,'new_json',side_effect=write):errors,_=self.finish()
        self.assertTrue(errors);self.assertEqual(self.terminal()['status'],'failed-terminal-integrity')

    def test_late_stream_change_or_added_artifact_fails(self):
        for extra in (False,True):
            with self.subTest(extra=extra):
                # A separate test instance keeps each output directory exclusive.
                other=Terminal();other.setUp()
                self.addCleanup(other.doCleanups);original=C.new_json
                def write(path,value):
                    result=original(path,value)
                    if path.name=='report.json':
                        (other.output/('extra' if extra else 'header-generation.stdout')).write_bytes(b'late')
                    return result
                with patch.object(C,'new_json',side_effect=write):errors,_=other.finish()
                self.assertTrue(errors);self.assertEqual(other.terminal()['status'],'failed-terminal-integrity')

    def test_external_report_mutation_is_preserved_and_rejected(self):
        original=C.new_json
        def write(path,value):
            result=original(path,value)
            if path.name=='report.json':path.write_bytes(b'external report edit')
            return result
        with patch.object(C,'new_json',side_effect=write):errors,_=self.finish()
        self.assertTrue(errors);self.assertEqual((self.output/'report.json').read_bytes(),b'external report edit')
        self.assertEqual(self.terminal()['status'],'failed-terminal-integrity')
        self.assertEqual(self.terminal()['available_evidence_pins'],{})

    def test_last_named_lease_check_failure_cannot_claim_held(self):
        calls=0
        def check():
            nonlocal calls
            calls+=1
            if calls==3:raise AssertionError('named lease changed')
        errors,_=self.finish(check)
        self.assertTrue(errors);self.assertFalse(self.terminal()['common_mutex_held'])
        self.assertEqual(self.terminal()['status'],'failed-terminal-integrity')

    def test_unreadable_special_artifact_retains_readable_siblings(self):
        fifo=self.copy/'pipe';os.mkfifo(fifo)
        errors,artifacts=self.finish()
        self.assertTrue(artifacts)
        report=json.loads((self.output/'report.json').read_bytes())
        self.assertEqual(report['artifact_pins'][str(self.header)],self.validated[str(self.header)])
        self.assertNotIn(str(fifo),report['artifact_pins'])
        self.assertEqual(self.terminal()['status'],'failed-terminal-integrity')


class FileKindsAndMembership(unittest.TestCase):
    def test_fifo_is_rejected_without_opening_or_hashing(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fifo';os.mkfifo(path)
            with patch.object(C.os,'open') as opened,self.assertRaises(AssertionError):C.sha(path)
            opened.assert_not_called()

    def test_replacement_with_fifo_after_lstat_uses_nonblocking_regular_guard(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'file';path.write_bytes(b'old');original=os.open
            def opened(name,flags,*args):
                self.assertTrue(flags&os.O_NONBLOCK);path.unlink();os.mkfifo(path)
                return original(name,flags,*args)
            with patch.object(C.os,'open',side_effect=opened),self.assertRaises(AssertionError):C.sha(path)

    def test_replaced_named_lease_rejected_with_original_fd_still_open(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'lease';path.write_bytes(b'')
            with path.open('rb') as handle:
                opened=os.fstat(handle.fileno());identity=(opened.st_dev,opened.st_ino)
                C.verify_leases([(path,handle,identity)])
                path.rename(path.with_suffix('.old'));path.write_bytes(b'')
                with self.assertRaises(AssertionError):C.verify_leases([(path,handle,identity)])

    def test_deleted_original_or_unexpected_new_source_copy_file_rejected(self):
        for missing in (False,True):
            with self.subTest(missing=missing),tempfile.TemporaryDirectory() as directory:
                root=Path(directory);output=root/'output';copy=root/'copy';output.mkdir();copy.mkdir()
                original=copy/'original.c';original.write_bytes(b'original')
                raw_spec=root/'spec';raw_spec.write_bytes(b'/vendor/')
                for name,raw in [('native-original-spec.reb',b'/vendor/'),('generation-spec.reb',(str(copy)+'/').encode()),
                                 ('generator-completed.reb',b'done'),('os-query-events.reb',b'events')]:
                    (output/name).write_bytes(raw)
                (copy/'generated.h').write_bytes(b'generated')
                plan=dict(output=str(output),source_copy=str(copy),raw_spec=str(raw_spec),
                    raw_spec_sha256=C.sha(raw_spec),initial_copy_pins={str(original):C.sha(original)})
                if missing:original.unlink()
                else:(copy/'extra.c').write_bytes(b'not allowed')
                validated,errors=C.artifact_pins((output,copy));self.assertEqual(errors,[])
                parser=SimpleNamespace(SOURCE_ROOT='/vendor/',parse=lambda raw:{'root':raw.decode()},canonical=lambda v:v)
                with patch.object(C,'GENERATED',{'generated.h'}),self.assertRaisesRegex(AssertionError,'membership'):
                    C.verify_generated(plan,parser,validated)


if __name__=='__main__':unittest.main(verbosity=2)
