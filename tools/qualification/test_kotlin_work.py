"""Pure compiled-work evidence fixtures; never launches JVMs or reads full pins."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('kotlin_work',Path(__file__).with_name('kotlin_work.py'))
work = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(work)


class WorkEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.root = Path(self.temp.name).resolve()
    def tearDown(self): self.temp.cleanup()

    def test_prerequisite_requires_completed_156_case_native_and_observed_counts(self):
        shared = dict(status='all20-bounded-output-passed-awaiting-work-JIT-and-LOC',qualified_bounded_cases=156,
            native_processes_started=157,diagnostic_compiler_processes_started=1,bounded_jvm_processes_started=156,
            observed_subject_main_invocations=156,observed_subject_main_returns=156,integrity_errors=[],process_receipt_errors=[])
        report = dict(shared,schema='kotlin-retained-classes-bounded-results-v1',bounded_outputs_qualified=True,
            profiles=[str(i) for i in range(20)],cases=[{} for _ in range(156)],active=None,
            subject_recompilations=0,benchmark_samples=0,chart_admission=False)
        terminal = dict(shared,report_sha256='known',artifact_errors=[],common_mutex_held=True,common_mutex_inode=79859134)
        work.validate_prerequisite(report,terminal,'known')
        for changed in [dict(qualified_bounded_cases=155),dict(observed_subject_main_returns=0),
                        dict(native_processes_started=156),dict(active={'pid':123}),dict(bounded_outputs_qualified=False)]:
            with self.subTest(changed=changed),self.assertRaisesRegex(AssertionError,'prerequisite'):
                work.validate_prerequisite(dict(report,**changed),terminal,'known')

    def test_jit_requires_actual_scored_method_nmethod_record(self):
        path = self.root/'hotspot.xml'
        target = dict(owner='clbg.nbody.MainKt',name='advance',descriptor='([[D)V')
        path.write_text("<hotspot_log><nmethod method='java.lang.String equals (Ljava/lang/Object;)Z' compiler='c2' compile_id='7' address='0x123'/></hotspot_log>")
        self.assertFalse(work.jit_records(path,[target])['subject_JIT_method_evidence_qualified'])
        path.write_text("<hotspot_log><nmethod method='clbg.nbody.MainKt advance ([[D)V' compiler='c1' compile_id='8' address='0x234' level='3'/></hotspot_log>")
        result = work.jit_records(path,[target]); self.assertTrue(result['subject_JIT_method_evidence_qualified'])
        self.assertEqual(result['subject_native_methods'][0]['compiler'],'c1')
        path.write_text("<hotspot_log><nmethod method='clbg.nbody.MainKt advance ([[D)V' compiler='none' compile_id='8' address='0x234'/></hotspot_log>")
        with self.assertRaisesRegex(AssertionError,'Malformed subject native'): work.jit_records(path,[target])

    def test_work_rejects_incomplete_or_foreign_specified_case_prerequisite(self):
        shared = dict(status='specified-30-cases-passed-awaiting-work-JIT-and-LOC',bounded_report_sha256='bounded',
            specified_case_coverage_qualified=True,qualified_supplemental_cases=30,native_processes_started=31,
            diagnostic_compiler_processes_started=1,supplemental_jvm_processes_started=30,
            observed_subject_main_invocations=30,observed_subject_main_returns=30,combined_qualified_form_cases=186,
            integrity_errors=[],process_receipt_errors=[])
        report = dict(shared,schema='kotlin-specified-cases-results-v1',profiles=[str(i) for i in range(20)],cases=[{}]*30,
            active=None,subject_recompilations=0,benchmark_samples=0,chart_admission=False)
        terminal = dict(shared,report_sha256='supplement',common_mutex_held=True,common_mutex_inode=79859134,artifact_errors=[])
        args = SimpleNamespace(supplement_report=self.root/'report.json',supplement_report_sha256='supplement',
            supplement_terminal_sha256='terminal',bounded_report_sha256='bounded')
        for changed in (dict(specified_case_coverage_qualified=False),dict(qualified_supplemental_cases=29),
                        dict(bounded_report_sha256='another-bounded-run')):
            with self.subTest(changed=changed),patch.object(work,'bind',side_effect=lambda path,digest,pins:Path(path)),\
                 patch.object(work,'read',side_effect=[dict(report,**changed),terminal]),\
                 self.assertRaisesRegex(AssertionError,'specified-case prerequisite'):
                work.supplemental_prerequisite(args,{}, {},{}, {})

    def test_incomplete_jit_xml_is_not_accepted(self):
        path = self.root/'hotspot.xml'; path.write_text('<hotspot_log><nmethod')
        with self.assertRaises(work.ET.ParseError): work.jit_records(path,[])

    def test_actual_native_images_are_bound_and_unknown_nonplatform_stays_open(self):
        java_home = self.root/'jdk'; (java_home/'lib').mkdir(parents=True)
        pins = {}
        for name in ('libjvm.dylib','libjava.dylib'):
            path = java_home/'lib'/name; path.write_bytes(name.encode()); pins[str(path)] = work.sha(path)
        text = 'Dynamic libraries:\n0x123 '+str(java_home/'lib/libjvm.dylib')+'\n0x234 '+str(java_home/'lib/libjava.dylib')+'\n0x345 /usr/lib/libSystem.B.dylib\n'
        result = work.native_libraries(text,pins,java_home)
        self.assertTrue(result['native_non_platform_images_qualified'])
        self.assertEqual(result['images'][-1]['scope'],'operating-system-image-install-name-not-file-pinned')
        result = work.native_libraries(text+'0x456 /unexpected/libforeign.dylib\n',pins,java_home)
        self.assertFalse(result['native_non_platform_images_qualified'])
        with self.assertRaisesRegex(AssertionError,'Unrecognized actual'):
            work.native_libraries(text+'Error: Cannot print dynamic libraries.\n',pins,java_home)

    def test_work_probe_class_log_preserves_names_and_rejects_wrong_origin(self):
        classes = self.root/'subject'; stdlib = self.root/'stdlib.jar'; probe = self.root/'probe'
        rows = [('boundedqualification.WorkProbe',probe.as_uri()),('boundedqualification.BoundedProbe',probe.as_uri()),
                ('clbg.Support',classes.as_uri()),('clbg.nbody.MainKt',classes.as_uri())]
        text = '\n'.join('[0.1s][class,load] '+name+' source: '+source for name,source in rows)
        result = work.validate_log(text,classes,stdlib,probe,{'clbg.Support','clbg.nbody.MainKt'})
        self.assertIn('boundedqualification.WorkProbe',result)
        with self.assertRaisesRegex(AssertionError,'Wrong work probe'):
            work.validate_log(text.replace('WorkProbe source: '+probe.as_uri(),'WorkProbe source: '+classes.as_uri()),
                classes,stdlib,probe,{'clbg.Support','clbg.nbody.MainKt'})

    def witness_base(self,bench):
        classes = self.root/'subject'; stdlib = self.root/'stdlib.jar'; probe = self.root/'probe'
        main = 'clbg.'+bench+'.MainKt'; owners = ['clbg.Support',main]
        baseline = {k:None for k in work.kb.RUNTIME_KEYS}
        runtime = dict(baseline,flags=['original'],CLASS_PATH=str(probe),USER_HOME=str(self.root/'home'),
            JAVA_TMPDIR=str(self.root/'tmp'),JVM_MAIN='boundedqualification.WorkProbe')
        summary = dict(status='work-witnesses-recorded',benchmark=bench,main_owner=main,subject_owner_names=owners,
            denied_owner_canary=True,denied_owners=['clbg.UnexpectedOwner'],main_invocations=1,main_returns=1,main_output_checks=1,
            maximum_main_invocations=10000,warmup_deadline_milliseconds=20000,main_argument='0',runtime=runtime,
            probe_code_source=probe.as_uri(),main_code_source=classes.as_uri(),
            non_platform_class_origins={owner:classes.as_uri() for owner in owners},
            non_platform_class_resources={owner:(classes/(owner.replace('.','/')+'.class')).as_uri() for owner in owners})
        row = dict(benchmark=bench,main_owner=main,class_owner_names=owners,classes=str(classes),diagnostic_case={'n':0})
        plan = dict(runtime_expected=baseline,stdlib=str(stdlib))
        return summary,row,plan,probe

    def test_no_natural_collection_leaves_tree_gc_witness_open(self):
        summary,row,plan,probe = self.witness_base('binarytrees')
        summary['tree_witness'] = dict(fresh_identity_cases=[dict(depth=d,repetition=r,nodes=2**(d+1)-1)
            for d in (0,1,4,6,8) for r in (0,1)],all_graphs_disjoint=True,retained_root_depth=8,retained_descendants=511,
            only_root_strong_during_pressure=True,descendant_identity_preserved=True,pressure_allocated_bytes=256*1024*1024,
            pressure_retained_bound_bytes=32*1024*1024,tree_root_requests=11,check_root_requests=11,
            normal_gc_observed=False,gc_count_before=2,gc_count_after=2,optimized_main_allocation_and_lifetime_proved=False)
        result = work.validate_witness(summary,row,plan,self.root,probe,['original'])
        self.assertTrue(result['tree_identity_qualified']); self.assertFalse(result['constructor_or_container_witness_qualified'])
        self.assertFalse(result['optimized_main_allocation_and_lifetime_proved'])

    def test_full_maps_are_checked_independently_including_nonquery_entries(self):
        summary,row,plan,probe = self.witness_base('knucleotide')
        seed = 'GGTATTTTAATTTATAGTACGTACGTTGCA'
        sequences = [seed[:n] for n in (0,1,2,17,18,19)]+[seed+'AAAAACCCCCGGGGGTTTTT'+seed+'ACGTACGT']
        cases = []
        for sequence in sequences:
            maps = []
            for k in (1,2,3,4,6,12,18):
                expected = {}
                for index in range(max(0,len(sequence)-k+1)):
                    word = sequence[index:index+k]; expected[word] = expected.get(word,0)+1
                maps.append(dict(k=k,entries=expected,count_sum=max(0,len(sequence)-k+1)))
            cases.append(dict(sequence=sequence,length=len(sequence),maps=maps,seven_distinct_simultaneously_retained=True,
                repeat_is_fresh=True,earlier_maps_unchanged=True,table_invocations=8))
        summary['map_witness'] = cases
        self.assertTrue(work.validate_witness(summary,row,plan,self.root,probe,['original'])['constructor_or_container_witness_qualified'])
        del summary['map_witness'][-1]['maps'][0]['entries']['A']
        with self.assertRaisesRegex(AssertionError,'Independent complete map mismatch'):
            work.validate_witness(summary,row,plan,self.root,probe,['original'])

    def clean_receipt(self,directory,pid,kind):
        identity = dict(pid=pid,ppid=42,pgid=pid,birth_seconds=100,birth_microseconds=20,status=2)
        return dict(kind=kind,status='native-passed',native_process_started=True,pid=pid,pgid=pid,exit_status=0,
            direct_child_reaped=True,remaining_process_group=[],inherited_common_mutex=True,common_mutex_inode=79859134,
            cwd=str(directory),stdin_bytes=0,stdin_sha256=hashlib.sha256(b'').hexdigest(),
            process_timeout_seconds=30,cleanup_timeout_seconds=5,maximum_process_group_rss_bytes=work.kb.RSS_LIMIT,
            native_file_limit_bytes=work.kb.FILE_LIMIT,stdout_capture_limit_bytes=work.kb.FILE_LIMIT+work.kb.PIPE_CHUNK,
            kernel_monitor_samples=1,observed_peak_process_group_rss_bytes=1024,identity=identity,
            leader_identity_before_reap=dict(identity,status=5),stdout_bytes=0,stderr_bytes=0,
            stdout_sha256=hashlib.sha256(b'').hexdigest(),stderr_sha256=hashlib.sha256(b'').hexdigest())

    def complete_native_evidence(self):
        ids = ['kotlin-'+b+'-'+v for b in work.kb.CASE_NAMES for v in ('compact','optimized')]
        profiles = [dict(id=i,main_invocations=2,main_returns=2,
            witness={'constructor_or_container_witness_qualified':True},jit={'subject_JIT_method_evidence_qualified':True},
            actual_subject_runtime_dependency_closure_qualified=True) for i in ids]
        report = dict(status='all20-bounded-work-witnesses-recorded-with-separate-open-gates',profiles=profiles,active=None,
            native_processes_started=21,diagnostic_compiler_processes_started=1,work_jvm_processes_started=20,
            native_process_ids=[],validated_command_artifacts={},required_work_witnesses_qualified=True,
            subject_JIT_method_evidence_qualified=True,actual_subject_runtime_dependency_closure_qualified=True,
            supplemental_output_prerequisite={'qualified_cases':30},specified_case_coverage_qualified=True)
        for index,identity in enumerate([None]+ids):
            kind = 'diagnostic-compile' if identity is None else 'compiled-work'
            directory = self.root/('diagnostic-compile' if identity is None else identity); directory.mkdir()
            files = {'stdout.bin','stderr.bin','start.json','active.json'}
            files |= ({'WorkProbe.java','BoundedProbe.java'} if identity is None else
                {'stdin.bin','expected.stdout','owners.txt','first.stdout','last.stdout','native-libraries.txt','classes.log','gc.log','hotspot.xml'})
            for name in files: (directory/name).write_bytes(b'')
            if identity is not None:
                (directory/'summary.json').write_text(json.dumps(dict(status='work-witnesses-recorded',main_invocations=2,main_returns=2,main_output_checks=2)))
                (directory/'validated.json').write_text(json.dumps(profiles[index-1]))
            receipt = self.clean_receipt(directory,1000+index,kind)
            (directory/'process.json').write_text(json.dumps(receipt))
            report['native_process_ids'].append(dict(kind=kind,id=identity,pid=1000+index,pgid=1000+index))
            report['validated_command_artifacts'][directory.name] = work.snapshot_command(directory)
        return report,dict(profiles=[{'id':i} for i in ids])

    def test_complete_native_inventory_reconciles_all_twenty_summaries_and_21_starts(self):
        report,plan = self.complete_native_evidence()
        self.assertEqual(work.reconcile_native(report,self.root,plan),[])
        self.assertEqual(report['observed_main_invocations'],40)
        self.assertEqual(report['observed_main_returns'],40)

    def test_missing_summary_and_mismatched_pid_fail_reconciliation(self):
        report,plan = self.complete_native_evidence()
        (self.root/plan['profiles'][0]['id']/'summary.json').unlink()
        report['native_process_ids'][0]['pid'] = 99999
        errors = work.reconcile_native(report,self.root,plan)
        self.assertTrue(any('PID/PGID' in item['error'] for item in errors))
        self.assertTrue(report['missing_main_observations'])
        self.assertTrue(any('incomplete' in item['error'] for item in errors))

    def test_native_clean_exit_and_resource_receipts_are_required(self):
        directory=self.root/'one';directory.mkdir()
        for name in ('stdout.bin','stderr.bin'): (directory/name).write_bytes(b'')
        receipt=self.clean_receipt(directory,123,'compiled-work')
        work.validate_native_receipt(receipt,'compiled-work',directory)
        for changed in (dict(exit_status=9),dict(cleanup_errors=['failed']),dict(pgid=124),
                        dict(exit_status=False),dict(stdout_bytes=False),
                        dict(kernel_monitor_samples=0),dict(observed_peak_process_group_rss_bytes=work.kb.RSS_LIMIT+1),
                        dict(native_file_limit_bytes=work.kb.FILE_LIMIT*2)):
            with self.subTest(changed=changed),self.assertRaises(AssertionError):
                work.validate_native_receipt(dict(receipt,**changed),'compiled-work',directory)

    def test_changed_or_missing_validated_artifact_cannot_acquire_fresh_terminal_qualification(self):
        report,plan = self.complete_native_evidence(); directory=self.root/plan['profiles'][0]['id']
        (directory/'native-libraries.txt').write_text('changed')
        (directory/'hotspot.xml').unlink()
        with patch.object(work.kb.kh,'verify_lock'),self.assertRaisesRegex(AssertionError,'evidence incomplete'):
            work.finalize(report,{},self.root,None,plan)
        saved=json.loads((self.root/'report.json').read_bytes());terminal=json.loads((self.root/'terminal.json').read_bytes())
        self.assertEqual(saved['status'],terminal['status'])
        for key in ('required_work_witnesses_qualified','subject_JIT_method_evidence_qualified','actual_subject_runtime_dependency_closure_qualified'):
            self.assertFalse(saved[key]);self.assertFalse(terminal[key])
        self.assertTrue(terminal['artifact_errors'])
        self.assertEqual(terminal['report_sha256'],work.sha(self.root/'report.json'))

    def test_profile_count_or_aggregate_flag_discrepancy_fails(self):
        report,plan=self.complete_native_evidence()
        report['profiles'][0]['main_invocations']=3
        report['subject_JIT_method_evidence_qualified']=False
        errors=work.reconcile_native(report,self.root,plan)
        self.assertTrue(any('counts differ' in item['error'] for item in errors))
        self.assertTrue(any('flags differ' in item['error'] for item in errors))

    def test_directory_symlink_and_traversal_error_are_explicit(self):
        (self.root/'outside').symlink_to(self.root/'missing',target_is_directory=True)
        errors=[];self.assertEqual(work.inventory_files(self.root,errors),[]);self.assertTrue(errors)
        with patch.object(work.os,'scandir',side_effect=PermissionError(13,'fixture denied',str(self.root))):
            errors=[];self.assertEqual(work.inventory_files(self.root,errors),[]);self.assertTrue(errors)

    def test_supplement_case_reference_must_match_terminal_inventory(self):
        path=self.root/'kotlin-nbody-compact/n-10/validated.json';path.parent.mkdir(parents=True);path.write_text('{}')
        terminal={'available_evidence':{}}
        with self.assertRaisesRegex(AssertionError,'terminal inventory'):
            work.terminal_reference(path,work.sha(path),self.root,terminal)
        terminal['available_evidence'][str(path.relative_to(self.root))]={'sha256':work.sha(path),'bytes':2}
        work.terminal_reference(path,work.sha(path),self.root,terminal)
        terminal['available_evidence'][str(path.relative_to(self.root))]['sha256']='changed'
        with self.assertRaisesRegex(AssertionError,'terminal inventory'):
            work.terminal_reference(path,work.sha(path),self.root,terminal)


if __name__ == '__main__': unittest.main()
