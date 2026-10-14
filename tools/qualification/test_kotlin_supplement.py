"""Small pure fixture/evidence regressions; no JVM, full pins or numeric workloads."""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


def load(path,name):
    spec = importlib.util.spec_from_file_location(name,path)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value); return value


supp = load(Path(__file__).with_name('kotlin_supplement.py'),'kotlin_supplement_tested')
oracle = load(supp.PACKET/'oracles.py','specified_oracle_tested')
FIXTURES = json.loads((supp.PACKET/'fixtures.json').read_bytes())


class SupplementTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name).resolve()
    def tearDown(self): self.temp.cleanup()

    def profiles(self):
        return [dict(id='kotlin-'+bench+'-'+variant,benchmark=bench,variant=variant,bounded_cases=[
            dict(case=f['case'],n=f['n'],stdin={'path':'fixture'} if 'stdin_ascii' in f else None)
            for f in FIXTURES if f['benchmark']==bench]) for bench in supp.kb.CASE_NAMES for variant in ('compact','optimized')]

    def test_exact_specification_gaps_and_independent_forms(self):
        specification = json.loads(supp.SPEC.read_bytes())
        self.assertEqual(hashlib.sha256(supp.SPEC.read_bytes()).hexdigest(),supp.SPEC_SHA)
        for bench,missing in supp.NUMERIC.items():
            required = [0,1,9,10,11,27,100] if bench=='pidigits' else specification['work_stage']['other_bounded_workloads'][bench]['sizes']
            self.assertEqual(set(required)-set(supp.kb.NUMERIC[bench]),set(missing))
        rows = self.profiles(); self.assertEqual(len(supp.validate_coverage(rows,FIXTURES)),30)
        rows[0]['bounded_cases'] = rows[0]['bounded_cases'][:-1]
        with self.assertRaisesRegex(AssertionError,'schedule'): supp.validate_coverage(rows,FIXTURES)
        with self.assertRaisesRegex(AssertionError,'inventory'): supp.fixture_schedule(FIXTURES[:-1])

    def test_every_literal_alternative_is_unique_and_matches_only_its_declared_regex(self):
        words = [word for group in oracle.WORDS for word in group]
        self.assertEqual(len(words),50); self.assertEqual(len(set(words)),50)
        for index,group in enumerate(oracle.WORDS):
            self.assertEqual(len(group),2 if index==0 else 6)
            for word in group:
                self.assertEqual(len(word),8)
                self.assertEqual([i for i,p in enumerate(oracle.PATTERNS) if re.fullmatch(p,word)],[index])

    def test_declared_regex_counts_and_overlap_are_independently_cross_checked(self):
        references = oracle.legacy()
        for fixture in FIXTURES:
            if fixture['benchmark']!='regexredux': continue
            expected = oracle.regex_expectation(fixture)
            self.assertEqual(expected,references.regexredux(fixture['stdin_ascii'].encode('ascii')))
        overlap = next(f for f in FIXTURES if f['case']=='specified-overlapping-candidates')
        self.assertEqual(overlap['expected_counts'],[2]+[0]*8)
        self.assertEqual(overlap['overlapping_candidate_counts'],[4]+[0]*8)
        bad = dict(overlap,expected_counts=[4]+[0]*8)
        with self.assertRaisesRegex(AssertionError,'reviewed regex counts'): oracle.regex_expectation(bad)

    def test_reverse_complement_boundary_fixture_has_all_lengths_and_standalone_cr(self):
        fixture = next(f for f in FIXTURES if f['benchmark']=='revcomp'); raw = fixture['stdin_ascii'].encode('ascii')
        references = oracle.legacy(); records = references.records(raw)
        self.assertEqual([len(text) for _,text in records],[0,1,59,60,61,121])
        self.assertTrue(re.search(rb'\r(?!\n)',raw)); self.assertFalse(raw.endswith((b'\r',b'\n')))
        self.assertEqual([len(text) for _,text in references.records(references.revcomp(raw))],[0,1,59,60,61,121])
        self.assertTrue(set(b'ACGTUMRWSYKVHDBNacgtumrwsykvhdbn') <= set(raw))

    def test_both_composite_record_descriptions_select_the_same_complete_sequence(self):
        references = oracle.legacy()
        for fixture in FIXTURES:
            if fixture['benchmark']!='knucleotide': continue
            raw = fixture['stdin_ascii'].encode('ascii'); sequence,tables = references.nucleotide_maps(raw)
            self.assertEqual(sequence,'GGTATTTTAATTTATAGTACGT')
            self.assertIn(b'>THREEBAD',raw); self.assertIn(b';>THREE',raw); self.assertIn(b'>FOUR',raw)
            self.assertEqual([table[query] for table,query in zip(tables[2:],references.QUERIES)],[1]*5)
            self.assertEqual(tables[0],{'A':6,'C':1,'G':4,'T':11})

    def completed(self):
        shared = dict(status=supp.SUCCESS,bounded_report_sha256='bounded',specified_case_coverage_qualified=True,
            qualified_supplemental_cases=30,native_processes_started=31,diagnostic_compiler_processes_started=1,
            supplemental_jvm_processes_started=30,observed_subject_main_invocations=30,observed_subject_main_returns=30,
            combined_qualified_form_cases=186,
            integrity_errors=[],process_receipt_errors=[])
        report = dict(shared,schema='kotlin-specified-cases-results-v1',profiles=[str(i) for i in range(20)],cases=[{}]*30,
            active=None,subject_recompilations=0,benchmark_samples=0,chart_admission=False,validated_command_artifacts={},
            original_output_artifact_binding={'saved_output_and_receipt_artifacts_bound':True})
        terminal = dict(shared,report_sha256='supplement',common_mutex_held=True,common_mutex_inode=79859134,artifact_errors=[])
        return report,terminal

    def test_completed_supplement_requires_30_observed_cases_bound_to_same_156_report(self):
        report,terminal = self.completed(); supp.validate_completed(report,terminal,'supplement','bounded')
        for changed in (dict(qualified_supplemental_cases=29),dict(observed_subject_main_returns=0),
                        dict(native_processes_started=30),dict(specified_case_coverage_qualified=False),dict(bounded_report_sha256='foreign')):
            with self.subTest(changed=changed),self.assertRaisesRegex(AssertionError,'prerequisite'):
                supp.validate_completed(dict(report,**changed),terminal,'supplement','bounded')

    def test_failed_post_popen_identity_receipt_remains_one_actual_native_start(self):
        directory = self.root/'kotlin-nbody-compact/n-10'; directory.mkdir(parents=True)
        receipt = dict(kind='bounded-main',native_process_started=True,pid=123,pgid=123,status='failed',direct_child_reaped=True)
        (directory/'process.json').write_text(json.dumps(receipt))
        report = dict(specified_case_coverage_qualified=False,native_processes_started=1,
            validated_command_artifacts={},
            native_process_ids=[dict(kind='bounded-main',id='kotlin-nbody-compact',case='n-10',pid=123,pgid=123)])
        self.assertEqual(supp.reconcile_native(self.root,report),[])
        self.assertEqual(report['observed_subject_main_invocations'],0)
        self.assertEqual(len(report['unobserved_main_summaries']),1)
        report['native_processes_started']=0
        self.assertTrue(supp.reconcile_native(self.root,report))

    def test_clean_native_receipt_rejects_failed_or_unreaped_commands(self):
        for name in ('stdout.bin','stderr.bin','stdin.bin'): (self.root/name).write_bytes(b'')
        receipt = self.native_receipt(self.root,123,'bounded-main')
        supp.validate_receipt(receipt,'bounded-main',self.root)
        for changed in (dict(status='failed'),dict(direct_child_reaped=False),dict(cleanup_errors=['error']),dict(exit_status=False),
                        dict(observed_peak_process_group_rss_bytes=supp.kb.RSS_LIMIT+1),dict(kernel_monitor_samples=False),dict(stdout_bytes=False)):
            with self.assertRaises(AssertionError): supp.validate_receipt(dict(receipt,**changed),'bounded-main',self.root)

    def native_receipt(self,directory,pid,kind):
        identity=dict(pid=pid,ppid=42,pgid=pid,birth_seconds=100,birth_microseconds=20,status=2)
        return dict(kind=kind,status='native-passed',native_process_started=True,pid=pid,pgid=pid,exit_status=0,
            direct_child_reaped=True,remaining_process_group=[],inherited_common_mutex=True,common_mutex_inode=79859134,
            cwd=str(directory),process_timeout_seconds=30,cleanup_timeout_seconds=5,
            maximum_process_group_rss_bytes=supp.kb.RSS_LIMIT,native_file_limit_bytes=supp.kb.FILE_LIMIT,
            stdout_capture_limit_bytes=supp.kb.FILE_LIMIT+supp.kb.PIPE_CHUNK,kernel_monitor_samples=1,
            observed_peak_process_group_rss_bytes=1024,identity=identity,leader_identity_before_reap=dict(identity,status=5),
            stdin_bytes=0,stdin_sha256=hashlib.sha256(b'').hexdigest(),stdout_bytes=0,stderr_bytes=0,
            stdout_sha256=hashlib.sha256(b'').hexdigest(),stderr_sha256=hashlib.sha256(b'').hexdigest())

    def complete_saved_commands(self):
        report,_=self.completed();report.update(cases=[],native_process_ids=[])
        cases=[(row['id'],case['case']) for row in self.profiles() for case in row['bounded_cases']]
        for index,(identity,case) in enumerate([(None,None)]+cases):
            kind='diagnostic-compile' if identity is None else 'bounded-main'
            name='diagnostic-compile' if identity is None else identity+'/'+case
            directory=self.root/name;directory.mkdir(parents=True)
            files={'stdout.bin','stderr.bin','start.json','active.json'}
            files |= {'BoundedProbe.java'} if identity is None else {'stdin.bin','expected.stdout','owners.txt','classes.log','gc.log'}
            for filename in files:(directory/filename).write_bytes(b'')
            if identity is not None:
                (directory/'summary.json').write_text(json.dumps(dict(benchmark_main_invocations=1,benchmark_main_returns=1)))
                (directory/'validated.json').write_text(json.dumps(dict(id=identity,case=case)))
                report['cases'].append(dict(id=identity,case=case))
            (directory/'process.json').write_text(json.dumps(self.native_receipt(directory,1000+index,kind)))
            report['native_process_ids'].append(dict(kind=kind,id=identity,case=case,pid=1000+index,pgid=1000+index))
            report['validated_command_artifacts'][name]=supp.snapshot_command(directory,kind)
        return report

    def test_complete_31_command_artifact_snapshots_reconcile(self):
        report=self.complete_saved_commands()
        self.assertEqual(supp.reconcile_native(self.root,report),[])
        self.assertEqual(report['observed_subject_main_invocations'],30)

    def test_changed_validated_output_invalidates_report_and_terminal(self):
        report=self.complete_saved_commands()
        case=report['cases'][0];path=self.root/case['id']/case['case']/'validated.json'
        path.write_text('changed after validation')
        with patch.object(supp.kb.kh,'verify_lock'),self.assertRaisesRegex(AssertionError,'integrity failed'):
            supp.finalize(report,{},self.root,None)
        saved=json.loads((self.root/'report.json').read_bytes());terminal=json.loads((self.root/'terminal.json').read_bytes())
        self.assertEqual(saved['status'],terminal['status']);self.assertEqual(saved['status'],'failed-artifact-integrity')
        self.assertFalse(saved['specified_case_coverage_qualified']);self.assertFalse(terminal['specified_case_coverage_qualified'])
        self.assertTrue(terminal['artifact_errors']);self.assertEqual(terminal['report_sha256'],supp.sha(self.root/'report.json'))

    def test_artifact_failure_clears_report_and_terminal_coverage_flag(self):
        report,terminal = self.completed(); report.update(native_process_ids=[])
        def failed_inventory(root,errors): errors.append(dict(error='simulated artifact enumeration failure')); return []
        with patch.object(supp,'reconcile_native',return_value=[]),patch.object(supp,'inventory_files',side_effect=failed_inventory),\
             patch.object(supp.kb.kh,'verify_lock'),self.assertRaisesRegex(AssertionError,'integrity failed'):
            supp.finalize(report,{},self.root,None)
        saved=json.loads((self.root/'report.json').read_bytes()); end=json.loads((self.root/'terminal.json').read_bytes())
        self.assertEqual(saved['status'],'failed-artifact-integrity');self.assertEqual(saved['status'],end['status'])
        self.assertFalse(saved['specified_case_coverage_qualified']);self.assertFalse(end['specified_case_coverage_qualified'])
        self.assertEqual(end['report_sha256'],supp.sha(self.root/'report.json'))

    def test_inventory_surfaces_directory_read_failure(self):
        with patch.object(supp.os,'scandir',side_effect=PermissionError(13,'fixture denied',str(self.root))):
            errors=[];self.assertEqual(supp.inventory_files(self.root,errors),[]);self.assertEqual(len(errors),1)

    def original_artifact_fixture(self):
        digest=hashlib.sha256(b'x').hexdigest();objects={};report={'cases':[]};terminal={'available_evidence':{}}
        row=dict(id='kotlin-pidigits-compact',benchmark='pidigits',bounded_cases=[])
        for index in range(156):
            name='n-'+str(index);case=dict(case=name,n=0,stdin=None,expected={'path':'independent-reference','sha256':digest})
            row['bounded_cases'].append(case);directory=self.root/row['id']/name
            validation=supp.kb.eb.output_validation('pidigits',b'x',b'x')
            value=dict(status='bounded-output-passed',id=row['id'],case=name,n=0,reference_evidence=case,
                main_invocations=1,main_returns=1,validation=validation)
            receipt=dict(stdout_sha256=digest,stdout_bytes=1,stderr_sha256=digest,stdin_sha256=hashlib.sha256(b'').hexdigest())
            record=dict(id=row['id'],case=name,status='bounded-output-passed',validated=str(directory/'validated.json'),
                process=str(directory/'process.json'),validated_sha256=digest,process_sha256=digest)
            report['cases'].append(record);objects[record['validated']]=value;objects[record['process']]=receipt
            for filename,sha in [('validated.json',digest),('process.json',digest),('stdout.bin',digest),('expected.stdout',digest),
                                  ('stderr.bin',digest),('stdin.bin',receipt['stdin_sha256'])]:
                terminal['available_evidence'][row['id']+'/'+name+'/'+filename]=dict(sha256=sha,bytes=1)
        return report,terminal,{'profiles':[row]},objects

    def test_all_156_original_case_proofs_are_bound_without_new_runtime_work(self):
        report,terminal,bounded,objects=self.original_artifact_fixture()
        with patch.object(supp,'bind',side_effect=lambda path,digest,pins:Path(path)),\
             patch.object(supp,'read',side_effect=lambda path,digest,pins:objects[str(path)]),\
             patch.object(supp,'validate_receipt'),patch.object(Path,'stat',return_value=SimpleNamespace(st_size=1)),\
             patch.object(Path,'read_bytes',return_value=b'x'):
            proof=supp.original_case_bindings(report,terminal,bounded,self.root,{})
            self.assertEqual(proof['original_cases'],156);self.assertEqual(proof['new_native_executions'],0)
            self.assertFalse(proof['runtime_work_proved'])
            key=report['cases'][-1]['id']+'/'+report['cases'][-1]['case']+'/process.json'
            terminal['available_evidence'][key]['sha256']='changed-before-old-terminal-scan'
            with self.assertRaisesRegex(AssertionError,'report and terminal artifact hashes'):
                supp.original_case_bindings(report,terminal,bounded,self.root,{})


if __name__=='__main__': unittest.main()
