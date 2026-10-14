"""Pure saved-capture and lifecycle tests; no Node or runtime hashing."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
P=Path(__file__).with_name('typescript_single_entry_remaining.py')
S=importlib.util.spec_from_file_location('remaining_ts',P);m=importlib.util.module_from_spec(S);S.loader.exec_module(m)
T=importlib.util.spec_from_file_location('original_ts_tests',P.with_name('test_typescript_single_entry.py'))
t=importlib.util.module_from_spec(T);T.loader.exec_module(t)


class RemainingTests(unittest.TestCase):
    def test_saved_original_raw_closure_and_capabilities(self):
        pins={};result=m.closed_prior(pins)
        self.assertEqual(result['preserved_native_processes'],2)
        self.assertFalse(result['tree_required_work_qualified'])
        self.assertFalse(result['tree_application_output_qualified'])
        self.assertEqual(pins[str(m.PACKET/'run-v1/report.json')],m.PRIOR_PINS['run-v1/report.json'])

    def test_only_missing_pi_and_diagnostic_narrowing(self):
        plan={'compiled':{'node':'/node','profiles':[{'benchmark':'pidigits','javascript':{'path':'/pi.js'}}]}}
        self.assertEqual(m.command(plan),['/node']+m.s.diagnostic_options('pidigits')+
            ['--maglev-print-filter=calculatePi','--no-maglev-print-feedback','/pi.js','10000'])
        self.assertNotIn('--no-logfile-per-isolate',m.options())
        self.assertEqual(m.SLOT['benchmark'],'pidigits')

    def fixture(self,directory):
        cmd,env,parent=t.CaptureTests().fixture(directory)
        return cmd,env,parent

    def test_raw_unknown_diagnostics_do_not_imply_output_admission(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);cmd,env,parent=self.fixture(p)
            stdout=b'unparsed native diagnostic\n12345\n';stderr=b'unknown diagnostic\n'
            record=json.loads((p/'process.json').read_bytes())
            for n,data in [('stdout',stdout),('stderr',stderr)]:
                (p/(n+'.bin')).write_bytes(data);record[n+'_bytes']=len(data);record[n+'_sha256']=hashlib.sha256(data).hexdigest()
            (p/'process.json').write_text(json.dumps(record))
            with patch.object(m,'command',return_value=cmd),patch.object(m.b,'environment',return_value=env):
                result=m.checked_capture({},p,parent)
            self.assertFalse(result['application_output_qualified']);self.assertFalse(result['runtime_work_semantics_qualified'])
            self.assertEqual(result['stdout_bytes'],len(stdout));self.assertEqual(result['stderr_bytes'],len(stderr))
            self.assertEqual(result['code_trace_files'],[])

    def test_raw_mutation_and_unowned_logs_rejected(self):
        for mode in ['raw','log']:
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp);cmd,env,parent=self.fixture(p)
                if mode=='raw':(p/'stdout.bin').write_bytes(b'mutated')
                else:(p/'code-999-0.asm').write_bytes(b'wrong owner')
                with patch.object(m,'command',return_value=cmd),patch.object(m.b,'environment',return_value=env):
                    with self.assertRaises(AssertionError):m.checked_capture({},p,parent)

    def test_failed_native_not_raw_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);cmd,env,parent=self.fixture(p);v=json.loads((p/'process.json').read_bytes());v['exit_status']=1
            (p/'process.json').write_text(json.dumps(v))
            with patch.object(m,'command',return_value=cmd),patch.object(m.b,'environment',return_value=env):
                with self.assertRaises(AssertionError):m.checked_capture({},p,parent)

    def test_success_requires_one_native(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);r=dict(status=m.SUCCESS,native_processes_started=0,registered_commands=[],captures=[],validated_artifacts={})
            with patch.object(m.b,'verify'),patch.object(m.kb.kh,'verify_lock'):m.finish(r,{},p,{},object())
            self.assertEqual(r['status'],'failed-integrity')
            self.assertIn('Missing pi capture',r['integrity_errors'])

    def test_failed_closed_attempt_retained_without_admission(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);r=dict(status='failed',native_processes_started=0,registered_commands=[],captures=[],validated_artifacts={})
            with patch.object(m.b,'verify'),patch.object(m.kb.kh,'verify_lock'):m.finish(r,{},p,{},object())
            terminal=json.loads((p/'terminal.json').read_bytes())
            self.assertEqual(terminal['integrity_errors'],[]);self.assertEqual(terminal['status'],'failed')
            for k in ['application_output_qualified','required_work_qualified','full_timings_qualified','chart_admission']:
                self.assertFalse(terminal[k])

    def test_changed_snapshot_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);d=p/m.SLOT['directory'];d.mkdir();(d/'x').write_bytes(b'old');snap=m.s.inventory(d);(d/'x').write_bytes(b'new')
            r=dict(status='failed',native_processes_started=0,registered_commands=[],captures=[],validated_artifacts={m.SLOT['directory']:snap})
            with patch.object(m.b,'verify'),patch.object(m.kb.kh,'verify_lock'):m.finish(r,{},p,{},object())
            self.assertEqual(r['status'],'failed-integrity');self.assertIn('Validated raw artifact changed',r['integrity_errors'])

    def test_original_stage_unchanged(self):
        self.assertEqual(m.sha(m.BASE),m.BASE_SHA)
        self.assertEqual(m.s.INPUTS,{'binarytrees':21,'pidigits':10000})
        self.assertEqual((m.kb.TIMEOUT,m.kb.FILE_LIMIT,m.kb.RSS_LIMIT),(180,128*1024**2,10*1024**3))
        self.assertEqual((m.b.kb.TIMEOUT,m.b.kb.FILE_LIMIT,m.b.kb.RSS_LIMIT),(30,8*1024**2,2*1024**3))


if __name__=='__main__':unittest.main()
