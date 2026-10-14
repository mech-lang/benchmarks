"""Pure source-reader stage fault checks; no Prolog or full closure hashes."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

PATH=Path(__file__).with_name('prolog_revcomp_loc.py')
SPEC=importlib.util.spec_from_file_location('tested_linear_loc',PATH)
m=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(m)


def digest(raw):return hashlib.sha256(raw).hexdigest()


class SourceReaderStageTests(unittest.TestCase):
    def receipt(self,directory,command=None,pid=50001,parent=None):
        command=['retained-swipl','-g','read-only'] if command is None else command
        parent=os.getpid() if parent is None else parent
        env={'SWI_HOME_DIR':'/retained/swipl'}
        common=dict(kind='prolog-revcomp-bounded',command=command,environment=env,cwd=str(directory),
            stdin_bytes=0,stdin_sha256=digest(b''),inherited_common_mutex=True,common_mutex_inode=m.kb.LOCK_INODE,
            process_timeout_seconds=m.kb.TIMEOUT,cleanup_timeout_seconds=m.kb.CLEANUP_TIMEOUT,
            maximum_process_group_rss_bytes=m.kb.RSS_LIMIT,native_file_limit_bytes=m.kb.FILE_LIMIT,
            stdout_capture_limit_bytes=m.kb.FILE_LIMIT+m.kb.PIPE_CHUNK)
        identity=dict(pid=pid,pgid=pid,ppid=parent,birth_seconds=100,birth_microseconds=111,status=2)
        start=dict(common,status='starting',native_process_started=False)
        active=dict(common,status='running',native_process_started=True,pid=pid,pgid=pid,identity=identity)
        final=dict(active,status='native-passed',exit_status=0,direct_child_reaped=True,remaining_process_group=[],
            stop_signals=[],cleanup_errors=[],kernel_monitor_samples=2,observed_peak_process_group_rss_bytes=1024,
            leader_identity_before_reap=dict(identity,status=5),stdout_bytes=3,stdout_sha256=digest(b'{}\n'),
            stderr_bytes=0,stderr_sha256=digest(b''))
        for name,row in [('start',start),('active',active),('process',final)]:m.save(directory/(name+'.json'),row)
        (directory/'stdout.bin').write_bytes(b'{}\n');(directory/'stderr.bin').write_bytes(b'')
        return command,env

    def test_historical_parent_replay_does_not_mutate_frozen_validator(self):
        function=m.b.check_receipt;original_getpid=m.b.os.getpid
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary);parent=os.getpid()+90000
            command,env=self.receipt(directory,parent=parent)
            self.assertEqual(m.saved_receipt(directory,command,env,b'',50001,parent)['exit_status'],0)
            with self.assertRaises(AssertionError):m.saved_receipt(directory,command,env,b'',50001,os.getpid())
            with self.assertRaises(AssertionError):function(directory,command,env,b'',50001)
        self.assertIs(m.b.check_receipt,function);self.assertIs(m.b.os.getpid,original_getpid)

    def test_wrong_pid_birth_and_unreaped_receipts_fail(self):
        changes=[lambda r:r.update(direct_child_reaped=False),lambda r:r.update(remaining_process_group=[{'pid':99}]),
                 lambda r:r['leader_identity_before_reap'].update(birth_seconds=101),
                 lambda r:r.update(pid=50002),lambda r:r.update(exit_status=1)]
        for change in changes:
            with tempfile.TemporaryDirectory() as temporary:
                directory=Path(temporary);command,env=self.receipt(directory)
                record=json.loads((directory/'process.json').read_bytes());change(record);m.save(directory/'process.json',record)
                with self.assertRaises(AssertionError):m.saved_receipt(directory,command,env,b'',50001,os.getpid())

    def test_closed_prerequisite_artifact_omission_and_changes_fail(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory=Path(temporary);(directory/'one.bin').write_bytes(b'one')
            terminal={'available_evidence':m.b.inventory(directory)};m.save(directory/'terminal.json',terminal)
            pins={};m.closed_artifacts(directory,terminal,pins)
            self.assertEqual(pins[str((directory/'one.bin').resolve())],digest(b'one'))
            (directory/'one.bin').write_bytes(b'two')
            with self.assertRaises(AssertionError):m.closed_artifacts(directory,terminal,{})
            (directory/'one.bin').write_bytes(b'one');(directory/'extra.bin').write_bytes(b'extra')
            with self.assertRaises(AssertionError):m.closed_artifacts(directory,terminal,{})

    def test_partial_or_unqualified_bounded_cohort_stops_before_deep_replay(self):
        for key,value,message in [('native_processes_started',541,'Incomplete bounded prerequisite'),
                                  ('qualified_cases',539,'Incomplete bounded prerequisite'),
                                  ('successful_cases',469,'Incomplete bounded prerequisite'),
                                  ('rejected_cases',69,'Incomplete bounded prerequisite'),
                                  ('bounded_conformance_qualified',False,'Incomplete bounded prerequisite'),
                                  ('source_work_qualified',True,'Wrong bounded closure or scope'),
                                  ('integrity_errors',[{'error':'changed'}],'Wrong bounded closure or scope')]:
            with self.subTest(key=key),tempfile.TemporaryDirectory() as temporary:
                directory=Path(temporary).resolve();report_path=directory/'report.json'
                status='bounded-conformance-passed-awaiting-work-and-source-count-review'
                report=dict(schema='prolog-revcomp-linear-bounded-report-v1',status=status,active=None,
                    commands=[{} for _ in range(542)],native_processes_started=542,qualified_cases=540,
                    successful_cases=470,rejected_cases=70,bounded_conformance_qualified=True,
                    integrity_errors=[],artifact_errors=[],benchmark_samples=0,canonical_loc=None,formatted_loc=None,
                    source_work_qualified=False,full_timings_qualified=False,chart_admission=False)
                report[key]=value;m.save(report_path,report)
                terminal=dict(status=status,report_sha256=m.sha(report_path),native_processes_started=542,
                    qualified_cases=540,bounded_conformance_qualified=True,integrity_errors=[],artifact_errors=[],
                    common_mutex_held=True,common_mutex_inode=m.kb.LOCK_INODE,source_work_qualified=False,
                    full_timings_qualified=False,chart_admission=False)
                m.save(directory/'terminal.json',terminal);m.save(directory/'durable.json',{})
                args=SimpleNamespace(bounded_report=report_path,bounded_report_sha256=m.sha(report_path),
                    bounded_terminal_sha256=m.sha(directory/'terminal.json'),bounded_durable=directory/'durable.json',
                    bounded_durable_sha256=m.sha(directory/'durable.json'))
                with patch.object(m.b,'validate_plan') as replay,self.assertRaisesRegex(AssertionError,message):
                    m.bounded_prerequisite(args,{})
                replay.assert_not_called()

    def legacy(self):
        ids=['test'+str(i) for i in range(31)]
        report=dict(status='passed-awaiting-original-source-review',tests_run=31,expected_ids=ids,
            started_ids=list(reversed(ids)),discovered_ids=ids,failures=0,errors=0,skipped=0,expected_failures=0,
            unexpected_successes=0,pin_reconciliation_passed=True,terminal_artifact_errors=[],
            available_bytes_not_fully_pinned=False,shared_timing_mutex_held=True,mutex_inode=m.kb.LOCK_INODE,
            input_pins={'/historical/prolog-proposal-v5/foreign_prolog.py':m.units.COUNTER_SHA,
                        '/historical/prolog-proposal-v5/scan_source.pl':m.units.READER_SHA})
        terminal=dict(status=report['status'],receipt_sha256=m.LEGACY_REPORT_SHA,integrity_errors=[],
                      available_bytes_not_fully_pinned=False)
        pins={str(m.LEGACY_REPORT):m.LEGACY_REPORT_SHA,str(m.LEGACY_TERMINAL):m.LEGACY_TERMINAL_SHA}
        return report,terminal,pins

    def test_legacy_fixture_count_failures_and_grammar_are_enforced(self):
        report,terminal,pins=self.legacy();m.validate_legacy_reader(report,terminal,pins)
        changes=[lambda r:r.update(tests_run=30),lambda r:r['started_ids'].pop(),lambda r:r.update(skipped=1),
                 lambda r:r.update(failures=1),lambda r:r.update(pin_reconciliation_passed=False),
                 lambda r:r['input_pins'].update({'/historical/prolog-proposal-v5/scan_source.pl':'0'*64})]
        for change in changes:
            report,terminal,pins=self.legacy();change(report)
            with self.assertRaises(AssertionError):m.validate_legacy_reader(report,terminal,pins)

    def test_actual_retained31_metadata_matches_frozen_contract(self):
        # Metadata shapes only; no pin closure verification or native replay.
        report=json.loads(m.LEGACY_REPORT.read_bytes());terminal=json.loads(m.LEGACY_TERMINAL.read_bytes())
        pins={str(m.LEGACY_REPORT):m.LEGACY_REPORT_SHA,str(m.LEGACY_TERMINAL):m.LEGACY_TERMINAL_SHA}
        m.validate_legacy_reader(report,terminal,pins)

    def test_schedule_contains_exact_nine_readonly_commands(self):
        pins={};rows=m.source_schedule('/retained/swipl',pins)
        self.assertEqual(len(rows),9)
        self.assertEqual([row['kind'] for row in rows],['metadata']+['fixture']*7+['candidate'])
        self.assertEqual(len({row['id'] for row in rows}),9)
        for row in rows:
            self.assertNotIn('-s',row['argv'])
            self.assertNotIn('clbg_revcomp_linear:run',row['argv'])
        self.assertEqual(rows[-1]['source_sha256'],m.units.CANDIDATE_SHA)
        self.assertEqual(len(pins),9)

    def plan(self):
        pins=m.own_pins();rows=m.source_schedule('/retained/swipl',pins)
        return dict(schema='prolog-linear-source-count-plan-v1',controller_sha256=m.sha(PATH),
            status='prepared-awaiting-nine-native-readers',pins=pins,prerequisite={'binary':'/retained/swipl'},
            schedule=rows,output=str(m.PACKET/'pure-test-unused-output'),process_timeout_seconds=m.kb.TIMEOUT,
            cleanup_timeout_seconds=m.kb.CLEANUP_TIMEOUT,maximum_process_group_rss_bytes=m.kb.RSS_LIMIT,
            native_file_limit_bytes=m.kb.FILE_LIMIT,planned_native_processes=9,subject_main_executions=0,
            subject_compilations=0,automatic_retries=0,benchmark_samples=0,canonical_LOC_admitted=False,
            source_work_qualified=False,chart_admission=False)

    def test_plan_rejects_changed_policy_schedule_and_own_pins(self):
        plan=self.plan();m.validate_plan(plan)
        changes=[lambda p:p.update(planned_native_processes=8),lambda p:p.update(subject_main_executions=1),
                 lambda p:p.update(subject_compilations=1),lambda p:p.update(automatic_retries=1),
                 lambda p:p.update(canonical_LOC_admitted=True),lambda p:p['schedule'].pop(),
                 lambda p:p['schedule'][1]['argv'].append('clbg_revcomp_linear:run'),
                 lambda p:p['pins'].pop(str(m.PACKET/'inspect_targets.pl')),
                 lambda p:p.update(output='/outside/packet/output')]
        for change in changes:
            changed=copy.deepcopy(plan);change(changed)
            with self.assertRaises(AssertionError):m.validate_plan(changed)

    def test_projection_rejects_wrong_source_before_counter(self):
        row=m.source_schedule('/retained/swipl',{})[1]
        with patch.object(m.units,'project') as project:
            with self.assertRaises(AssertionError):m.validate_projection(row,dict(source='wrong',source_text=''),{}, {})
        project.assert_not_called()

    def test_fixture_projection_requires_exact_count_and_diagnostic_contract(self):
        row=m.source_schedule('/retained/swipl',{})[1]
        raw=Path(row['source']).read_bytes();packet=dict(source=row['source'],source_text=raw.decode())
        prior={'environment':{'SWI_HOME_DIR':'/retained/swipl'}}
        result=dict(projection={'normalized_loc':4,'diagnostics':[]},canonical_LOC_admitted=False,
                    source_work_qualified=False,chart_admission=False)
        with patch.object(m.units,'project',return_value=result):
            self.assertEqual(m.validate_projection(row,packet,{},prior),result)
        for key,value in [('normalized_loc',5),('diagnostics',[{'kind':'prolog-unproved-call-target'}])]:
            changed=copy.deepcopy(result);changed['projection'][key]=value
            with patch.object(m.units,'project',return_value=changed),self.assertRaises(AssertionError):
                m.validate_projection(row,packet,{},prior)
        changed=copy.deepcopy(result);changed['canonical_LOC_admitted']=True
        with patch.object(m.units,'project',return_value=changed),self.assertRaises(AssertionError):
            m.validate_projection(row,packet,{},prior)

    def successful(self,output):
        rows=m.source_schedule('/retained/swipl',{})
        plan={'schedule':rows,'prerequisite':{'environment':{'SWI_HOME_DIR':'/retained/swipl'}}}
        report=dict(status=m.COMPLETE,commands=[],native_processes_started=9,projections=[],active=None,
            canonical_LOC_admitted=False,source_work_qualified=False,chart_admission=False)
        snapshots={}
        for index,row in enumerate(rows):
            directory=output/row['id'];directory.mkdir();pid=50001+index
            self.receipt(directory,row['argv'],pid)
            report['commands'].append(dict(id=row['id'],argv=row['argv'],pid=pid,status='reader-validated',
                process_sha256=m.sha(directory/'process.json')))
            if index:
                m.save(directory/'projection.json',{'canonical_LOC_admitted':False})
                report['projections'].append(dict(id=row['id'],projection_sha256=m.sha(directory/'projection.json')))
            snapshots[row['id']]=m.b.inventory(directory)
        return report,plan,snapshots

    def close(self,report,plan,output,snapshots,pins=None):
        with patch.object(m.kb.kh,'verify_lock'):
            m.finish(report,plan,{} if pins is None else pins,output,snapshots,None)

    def test_nine_reader_closure_keeps_all_admission_flags_false(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);report,plan,snapshots=self.successful(output)
            self.close(report,plan,output,snapshots)
            terminal=json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],m.COMPLETE)
            self.assertEqual(terminal['native_processes_started'],9)
            for key in ('canonical_LOC_admitted','source_work_qualified','chart_admission'):
                self.assertIs(terminal[key],False)

    def test_missing_receipt_wrong_pid_and_incomplete_projection_fail_closed(self):
        for fault in ('missing','pid','projection'):
            with self.subTest(fault=fault),tempfile.TemporaryDirectory() as temporary:
                output=Path(temporary);report,plan,snapshots=self.successful(output)
                if fault=='missing':(output/report['commands'][0]['id']/'process.json').unlink()
                elif fault=='pid':report['commands'][0]['pid']+=100
                else:report['projections'].pop()
                with self.assertRaisesRegex(AssertionError,'Reader artifact or native closure failed'):
                    self.close(report,plan,output,snapshots)
                terminal=json.loads((output/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'],'failed-reader-integrity-or-closure')
                self.assertIs(terminal['canonical_LOC_admitted'],False)

    def test_late_projection_artifact_change_fails_closure(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);report,plan,snapshots=self.successful(output)
            path=output/report['projections'][0]['id']/'projection.json';path.write_bytes(b'changed')
            with self.assertRaises(AssertionError):self.close(report,plan,output,snapshots)
            self.assertTrue(any('Projection report/artifact linkage changed' in r['error'] for r in report['native_receipt_errors']))

    def test_late_pinned_input_change_fails_closure(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);report,plan,snapshots=self.successful(output)
            pin=output/'input.txt';pin.write_bytes(b'old');pins={str(pin):m.sha(pin)};pin.write_bytes(b'new')
            with self.assertRaises(AssertionError):self.close(report,plan,output,snapshots,pins)
            self.assertEqual([r['path'] for r in report['integrity_errors']],[str(pin)])

    def test_unregistered_process_receipt_fails_closure(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);report,plan,snapshots=self.successful(output)
            extra=output/'unexpected';extra.mkdir();self.receipt(extra,pid=60000)
            with self.assertRaises(AssertionError):self.close(report,plan,output,snapshots)
            self.assertTrue(any('Unexpected or missing reader process receipt' in r['error'] for r in report['native_receipt_errors']))

    def test_native_artifact_inventory_failure_retains_failed_terminal(self):
        with tempfile.TemporaryDirectory() as temporary:
            output=Path(temporary);report,plan,snapshots=self.successful(output)
            (output/'unretained-link').symlink_to(output/report['commands'][0]['id']/'stdout.bin')
            with self.assertRaises(AssertionError):self.close(report,plan,output,snapshots)
            terminal=json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed-reader-artifact-retention')
            self.assertIs(terminal['canonical_LOC_admitted'],False)
            self.assertTrue(terminal['artifact_errors'])


if __name__=='__main__':unittest.main()
