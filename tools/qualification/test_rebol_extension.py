"""Pure draft fault checks; no compiler, interpreter, SDK or native process runs."""
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

spec=importlib.util.spec_from_file_location('rebol_extension_under_test',Path(__file__).with_name('rebol_extension.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)


def intake():
    return dict(target='arm64-apple-macos11.0',tools={k:dict(path='/fixed/'+k,sha256='a'*64)
        for k in ('clang','linker','runtime')},include_roots={k:'/headers/'+k
        for k in ('rebol','clang_resource','macos_sdk','gmp','pcre2')},
        libraries={k:dict(path='/libs/'+k+'.dylib',sha256='b'*64,runtime_version='1') for k in ('gmp','pcre2')})


def failed_report():
    return dict(status='stopped-unqualified',attempts=[],registered=[],active=None,captures=[],
                validated_artifacts={},validated_build_artifacts={})


class Contracts(unittest.TestCase):
    def test_second_native_failure_preserves_first_capture_and_never_retries(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve()/'fresh';meta=intake();slots=r.schedule(meta,out);calls=[];saved=[]
            def observe(command,environment,directory,payload,lock,launched,**kwargs):
                calls.append(command);launched(100+len(calls))
                if len(calls)==2:raise RuntimeError('owned failed compiler retained')
                (directory/'stdout.bin').write_bytes(b'')
            kb=SimpleNamespace(atomic=nullcontext,save=lambda p,v:p.write_bytes(r.encoded(v)),observe=observe)
            plan=dict(output=str(out),schedule=slots,unavailable_inputs=[],prerequisite_artifact_closures=[])
            capture=dict(id=slots[0]['id'],pid=101,started_at='2026-10-14T00:00:00+00:00',finished_at='2026-10-14T00:00:01+00:00')
            with patch.object(r,'pin'),patch.object(r,'verify'),patch.object(r,'check_leases'), \
                 patch.object(r,'checked_capture',return_value=(capture,{})), \
                 patch.object(r,'validate_compile_inputs',return_value=[]), \
                 patch.object(r,'built_image_closure',return_value={}),patch.object(r,'build_inventory',return_value={}), \
                 patch.object(r,'finish',side_effect=lambda report,*args:saved.append(copy.deepcopy(report))):
                with self.assertRaisesRegex(RuntimeError,'owned failed compiler'):
                    r.run(plan,Path('/plan'),'a'*64,meta,{},{},SimpleNamespace(kb=kb),None,[])
            self.assertEqual(len(calls),2)
            self.assertEqual(saved[0]['attempts'],r.IDS[:2]);self.assertEqual(len(saved[0]['captures']),1)
            self.assertEqual(len(saved[0]['registered']),2);self.assertIsNone(saved[0]['active'])
            self.assertEqual(saved[0]['status'],'stopped-unqualified')

    def test_four_processes_not_nine_native_processes(self):
        out=Path('/fresh/output');slots=r.schedule(intake(),out)
        self.assertEqual([s['id'] for s in slots],r.IDS)
        self.assertEqual([s['timeout_seconds'] for s in slots],[300,300,30,30])
        self.assertEqual(len(r.COMMANDS),9)
        self.assertEqual(bytes.fromhex(slots[-1]['stdin_hex']),b'\0\x80\xff')
        self.assertEqual(slots[-1]['command'],['/fixed/runtime','--quiet','--no-color',str(r.PACKET/'load-smoke.reb')])
        self.assertNotIn('DYLD_INSERT_LIBRARIES',slots[-1]['environment'])
        for slot in slots[:2]:
            self.assertEqual(slot['command'].count('--no-default-config'),1)
            self.assertIn('-fuse-ld=/fixed/linker',slot['command'])
            self.assertIn('-nostdinc',slot['command'])
            self.assertIn('-DREBOL_OPTIONS_FILE="gen-config.h"',slot['command'])
            self.assertIn('-MD',slot['command'])
        self.assertFalse(any('main.reb' in arg for slot in slots for arg in slot['command']))

    def test_pending_or_generic_intake_cannot_prepare(self):
        for value in ({},dict(schema='rebol-extension-concrete-toolchain-intake-v1',status='draft')):
            with self.assertRaises((KeyError,AssertionError)):
                r.validate_intake(value,{},dict(path='/missing/review',sha256='a'*64),{},{})

    def test_dependency_parser_handles_escaped_spaces_but_no_expansion(self):
        self.assertEqual(r.dependencies(b'dependencies: /a/source.c \\\n /SDK/Some\\ Header.h\n'),
                         {'/a/source.c','/SDK/Some Header.h'})
        for raw in (b'dependencies: $(dynamic)\n',b'other: /a\n',b'dependencies: relative.h\n',b'dependencies: /a\\'):
            with self.assertRaises(AssertionError):r.dependencies(raw)

    def test_unreviewed_compiler_header_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();(out/'build').mkdir()
            (out/'build/extension.d').write_bytes(b'dependencies: /reviewed/source.c /unreviewed/shadow.h\n')
            with self.assertRaisesRegex(AssertionError,'unreviewed header'):
                r.validate_compile_inputs(out,'extension',Path('/reviewed/source.c'),{'/reviewed/source.c':'a'*64},{})

    def test_named_alias_drift_rejected_even_with_same_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp).resolve();a=base/'a';b=base/'b';name=base/'link'
            a.write_bytes(b'same');b.write_bytes(b'same');name.symlink_to(a)
            pins,resolutions={},{};r.pin(pins,resolutions,name)
            name.unlink();name.symlink_to(b)
            with self.assertRaisesRegex(AssertionError,'named resolution'):r.verify(pins,resolutions)

    def test_fifo_never_opened_and_readable_failure_evidence_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp).resolve();(base/'good').write_bytes(b'receipt');os.mkfifo(base/'bad')
            with patch.object(r.os,'open',side_effect=AssertionError('must not open special file')):
                with self.assertRaisesRegex(AssertionError,'Regular file required'):r.read_bytes(base/'bad')
            found,errors=r.inventory(base,tolerant=True)
            self.assertEqual(set(found),{'good'});self.assertEqual([e['path'] for e in errors],['bad'])

    def test_unexpected_or_deleted_build_output_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();(out/'build').mkdir()
            names=('extension.d','extension.map','clbg_primitives.dylib')
            for name in names:(out/'build'/name).write_bytes(b'value')
            self.assertEqual(len(r.build_inventory(out,0)),3)
            (out/'build/extra').write_bytes(b'not declared')
            with self.assertRaises(AssertionError):r.build_inventory(out,0)
            (out/'build/extra').unlink();(out/'build/extension.d').unlink()
            with self.assertRaises(AssertionError):r.build_inventory(out,0)

    def test_missing_non_os_image_cannot_be_admitted(self):
        inspector=SimpleNamespace(tool_closure=lambda paths,pins:dict(images={'/new/image':{}}))
        with self.assertRaisesRegex(AssertionError,'unreviewed dependency'):
            r.built_image_closure([Path('/fresh/ext.dylib')],dict(declared_image_closure=dict(images={})),inspector,{})

    def test_owned_report_edit_during_first_inventory_is_not_adopted(self):
        for point in ('save-return','input-replay'):
            with self.subTest(point=point),tempfile.TemporaryDirectory() as temp:
                out=Path(temp).resolve();report=failed_report();calls=[]
                def save(path,value):
                    path.write_bytes(r.encoded(value))
                    if point=='save-return':path.write_bytes(b'{}\n')
                def verify(*args):
                    calls.append(True)
                    if len(calls)==2 and point=='input-replay':(out/'report.json').write_bytes(b'{}\n')
                plan=dict(schedule=[],unavailable_inputs=[],prerequisite_artifact_closures=[])
                with patch.object(r,'verify',side_effect=verify):
                    with self.assertRaisesRegex(AssertionError,'Final integrity failed'):
                        r.finish(report,plan,out,{},{},SimpleNamespace(save=save),lambda:None)
                terminal=json.loads((out/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed-integrity');self.assertEqual(terminal['available_evidence'],{})
                self.assertFalse(terminal['common_mutex_held'])
                self.assertEqual((out/'report.json').read_bytes(),b'{}\n')

    def test_final_named_lease_loss_rejects_success_claim(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();checks=[]
            def check():
                checks.append(True)
                if len(checks)==3:raise AssertionError('final named lock changed')
            kb=SimpleNamespace(save=lambda path,value:path.write_bytes(r.encoded(value)))
            plan=dict(schedule=[],unavailable_inputs=[],prerequisite_artifact_closures=[])
            with patch.object(r,'verify'):
                with self.assertRaisesRegex(AssertionError,'Final integrity failed'):
                    r.finish(failed_report(),plan,out,{},{},kb,check)
            terminal=json.loads((out/'terminal.json').read_bytes())
            self.assertFalse(terminal['common_mutex_held']);self.assertEqual(terminal['status'],'failed-integrity')

    def test_last_report_digest_cannot_adopt_different_bytes(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();kb=SimpleNamespace(save=lambda p,v:p.write_bytes(r.encoded(v)))
            plan=dict(schedule=[],unavailable_inputs=[],prerequisite_artifact_closures=[])
            original=r.sha;report_reads=[]
            def sha(path):
                if Path(path)==out/'report.json':
                    report_reads.append(True)
                    # Two inventories have already compared the exact report.
                    if len(report_reads)==3:(out/'report.json').write_bytes(b'{}\n')
                return original(path)
            with patch.object(r,'verify'),patch.object(r,'sha',side_effect=sha):
                with self.assertRaisesRegex(AssertionError,'Final integrity failed'):
                    r.finish(failed_report(),plan,out,{},{},kb,lambda:None)
            terminal=json.loads((out/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed-integrity');self.assertFalse(terminal['common_mutex_held'])
            self.assertEqual(terminal['available_evidence'],{})

    def test_partial_prefix_is_preserved_without_becoming_four_command_success(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp).resolve();report=failed_report();report['status']=r.SUCCESS
            kb=SimpleNamespace(save=lambda path,value:path.write_bytes(r.encoded(value)))
            with patch.object(r,'verify'):
                with self.assertRaisesRegex(AssertionError,'Final integrity failed'):
                    r.finish(report,dict(schedule=[],unavailable_inputs=[],prerequisite_artifact_closures=[]),out,{},{},kb,lambda:None)
            terminal=json.loads((out/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed-integrity');self.assertEqual(terminal['native_processes_started'],0)


if __name__=='__main__':unittest.main()
