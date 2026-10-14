"""Pure receipt, byte-output and finalizer tests; no native or closure hashing."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name('kotlin_single_entry_remaining.py')
SPEC = importlib.util.spec_from_file_location('tested_remaining_capture',PATH)
m = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(m)


class RemainingTests(unittest.TestCase):
    def test_only_remaining_original_ids(self):
        self.assertEqual(m.IDS,m.base.IDS[1:])
        self.assertNotIn(m.FIRST_ID,m.IDS)
        self.assertEqual(m.base.INPUTS,{'binarytrees':21,'pidigits':10000})

    def test_only_option_change_routes_os_warnings(self):
        directory = Path('/tmp/case')
        for benchmark in m.base.INPUTS:
            flags = m.options(benchmark,directory)
            self.assertEqual(flags[:-2],m.base.options(benchmark,directory))
            self.assertEqual(flags[-2],'-Xlog:all=warning,os=off:stdout:uptime,level,tags')
            self.assertEqual(flags[-1],'-Xlog:os=warning:file=/tmp/case/os.log:uptime,level,tags')
        self.assertEqual(m.kb.RSS_LIMIT,10*1024**3)

    def test_exact_recorded_warning_and_subject_bytes(self):
        expected = m.base.expected_output('binarytrees')
        self.assertEqual((len(m.FIRST_WARNING),len(expected)),(51,455))
        self.assertEqual(m.validate_first_stdout(m.FIRST_WARNING+expected,expected),expected)

    def test_no_generic_stdout_filter(self):
        expected = b'benchmark\n'
        for raw in (expected,b'warning\n'+expected,m.FIRST_WARNING+expected+b'junk',
                    m.FIRST_WARNING.replace(b'0.023',b'0.024')+expected,m.FIRST_WARNING+expected[:-1]):
            with self.subTest(raw=raw),self.assertRaisesRegex(AssertionError,'exact recorded'):
                m.validate_first_stdout(raw,expected)

    def test_os_log_allows_only_known_single_warning_or_empty(self):
        self.assertEqual(m.validate_os_log(b'')['lines'],[])
        self.assertEqual(m.validate_os_log(m.FIRST_WARNING)['lines'],[m.FIRST_WARNING.decode().strip()])
        self.assertEqual(len(m.validate_os_log(m.FIRST_WARNING.replace(b'0.023',b'1.102'))['lines']),1)
        for raw in (m.FIRST_WARNING*2,b'unknown\n',b'\n',b'[0.023s][warning][os] other failure\n'):
            with self.subTest(raw=raw),self.assertRaisesRegex(AssertionError,'Unexpected OS diagnostic'):
                m.validate_os_log(raw)

    def actual_receipt(self):
        directory = m.ORIGINAL/'run-v1'/m.FIRST_ID
        if not directory.exists(): self.skipTest('Saved first receipt unavailable')
        return directory,json.loads((directory/'process.json').read_bytes())

    def test_actual_first_receipt_validates_recorded_parent(self):
        directory,receipt = self.actual_receipt()
        m.validate_saved_receipt(receipt,directory,receipt['command'],receipt['environment'],23659)
        with self.assertRaisesRegex(AssertionError,'birth/parent'):
            m.validate_saved_receipt(receipt,directory,receipt['command'],receipt['environment'],os.getpid())

    def test_saved_first_metadata_replay_without_pin_verification(self):
        self.actual_receipt()
        # Pin/closure verification is reserved for prepare under the mutex.
        # This regression exercises only the already saved JSON/XML shapes.
        def metadata_only(path,expected,pins):
            return json.loads(Path(path).read_bytes())
        with patch.object(m,'read',side_effect=metadata_only),patch.object(m.base,'closed_artifacts') as closure:
            prior,proof = m.reconcile_first({},False)
        closure.assert_not_called()
        self.assertEqual(prior['ids'],[m.FIRST_ID]+m.IDS)
        self.assertEqual(proof['original_status'],'failed')
        self.assertEqual(proof['native_commands_reexecuted'],0)
        self.assertEqual(proof['complete_subject_output_bytes'],455)
        self.assertEqual(len(proof['native_capture']['native_methods']),9)
        self.assertIs(proof['source_work_qualified'],False)

    def test_changed_birth_and_nonempty_cleanup_fail(self):
        directory,receipt = self.actual_receipt()
        receipt['leader_identity_before_reap']['birth_microseconds'] += 1
        with self.assertRaisesRegex(AssertionError,'birth/parent'):
            m.validate_saved_receipt(receipt,directory,receipt['command'],receipt['environment'],23659)
        directory,receipt = self.actual_receipt(); receipt['remaining_process_group'] = [{'pid':23661}]
        with self.assertRaisesRegex(AssertionError,'cleanup'):
            m.validate_saved_receipt(receipt,directory,receipt['command'],receipt['environment'],23659)

    def successful(self,output):
        proof = {'original_status':'failed','native_commands_reexecuted':0}
        report = dict(status=m.COMPLETE,profiles=[],active=None,native_processes_started=3,
            registered_native_commands=[],commands={},validated_command_artifacts={},first_capture_reconciliation=proof)
        m.save(output/'first-capture-reconciliation.json',proof)
        for i,identity in enumerate(m.IDS,100):
            directory = output/identity; directory.mkdir()
            row = {'id':identity,'source_work_qualified':False}; report['profiles'].append(row)
            report['commands'][identity] = {'argv':['java',identity],'environment':{}}
            report['registered_native_commands'].append(dict(id=identity,pid=i,pgid=i))
            m.save(directory/'process.json',dict(kind='single-entry-work',native_process_started=True,
                pid=i,pgid=i,direct_child_reaped=True,cleanup_errors=[],remaining_process_group=[]))
            m.save(directory/'validated.json',row)
            report['validated_command_artifacts'][identity] = m.base.snapshot(directory)
        return report,{'first_capture_reconciliation':proof}

    def close(self,output,report,plan):
        with patch.object(m,'validate_saved_receipt'),patch.object(m.kb.kh,'verify_lock'):
            m.finish(report,plan,{},output,None)

    def test_successful_three_closes_with_no_qualification(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp); report,plan = self.successful(output); self.close(output,report,plan)
            terminal = json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],m.COMPLETE)
            self.assertEqual(terminal['native_processes_started'],3)
            self.assertEqual(terminal['registered_native_commands'],report['registered_native_commands'])
            self.assertEqual(report['remaining_receipt_errors'],[])
            for key in ('source_work_qualified','full_timings_qualified','chart_admission'):
                self.assertIs(terminal[key],False)

    def test_missing_profile_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp); report,plan = self.successful(output); report['profiles'].pop()
            with self.assertRaisesRegex(AssertionError,'Remaining native reconciliation'): self.close(output,report,plan)
            self.assertEqual(json.loads((output/'terminal.json').read_bytes())['status'],'failed-remaining-native-reconciliation')

    def test_changed_additive_proof_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp); report,plan = self.successful(output)
            m.save(output/'first-capture-reconciliation.json',{'original_status':'passed'})
            with self.assertRaisesRegex(AssertionError,'Remaining native reconciliation'): self.close(output,report,plan)
            self.assertTrue(report['remaining_receipt_errors'])

    def test_unregistered_native_receipt_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp); report,plan = self.successful(output)
            extra = output/'unexpected'; extra.mkdir(); m.save(extra/'process.json',{})
            with self.assertRaisesRegex(AssertionError,'Remaining native reconciliation'): self.close(output,report,plan)
            self.assertEqual(report['remaining_receipt_errors'],['Unexpected or omitted remaining native receipt'])

    def test_registered_but_missing_native_receipt_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp); report,plan = self.successful(output)
            (output/m.IDS[0]/'process.json').unlink()
            with self.assertRaisesRegex(AssertionError,'artifact or native closure'): self.close(output,report,plan)
            terminal = json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed-integrity-or-closure')
            self.assertTrue(terminal['process_receipt_errors'])


if __name__ == '__main__': unittest.main()
