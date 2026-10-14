"""Synthetic prerequisite and adversarial policy tests; no native execution."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name('kotlin_full.py')
SPEC = importlib.util.spec_from_file_location('kotlin_full_test_subject', PATH)
full = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(full)
SHA = '1'*64


def ref(name):
    return dict(path='/synthetic-only/'+name, sha256=SHA)


def cohort():
    runtime = dict(java='/synthetic-only/jdk/bin/java', stdlib='/synthetic-only/kotlin-stdlib.jar',
                   runtime_expected={'version': 'synthetic-only'})
    rows, counted, files = {}, {}, {}
    pins = {runtime['java']: SHA, runtime['stdlib']: SHA}
    for bench in full.BENCHES:
        for variant in ('compact', 'optimized'):
            identity = 'kotlin-'+bench+'-'+variant
            base = '/synthetic-only/'+identity
            sources = [dict(path=base+'/'+name, sha256=SHA, role=role, counted=True)
                       for name, role in [('Main.kt', 'application'), ('Support.kt', 'application-helper')]]
            artifacts = [dict(path=base+'/classes/clbg/'+bench+'/MainKt.class', sha256=SHA, bytes=1,
                              relative_path='clbg/'+bench+'/MainKt.class')]
            env = dict(HOME=base+'/home', TMPDIR=base+'/tmp/', XDG_CONFIG_HOME=base+'/config',
                       JAVACMD=runtime['java'], JAVA_HOME='/synthetic-only/jdk',
                       PATH='/synthetic-only/jdk/bin:/usr/bin:/bin:/usr/sbin:/sbin',
                       CLASSPATH='', KOTLIN_RUNNER='', KOTLIN_COMPILER='', KOTLIN_TOOL='')
            options = full.FLAGS+['-Duser.home='+env['HOME'], '-Djava.io.tmpdir='+env['TMPDIR'].rstrip('/')]
            env['JAVA_OPTS'] = ' '.join(options)
            command = [runtime['java']]+options+['-cp', base+'/classes:'+runtime['stdlib'],
                                                'clbg.'+bench+'.MainKt', '{n}']
            rows[identity] = dict(id=identity, benchmark=bench, variant=variant, physical_inputs=sources,
                class_artifacts=artifacts, runtime_environment=env, classes=base+'/classes',
                retained_runtime_command=command, main_owner=command[-2], class_owner_names=[command[-2]],
                alias_of='kotlin-'+bench+'-baseline-v1')
            keys = [identity+'--'+s['role'] for s in sources]
            for key, item in zip(keys, sources):
                files[key] = dict(source=item['path'], source_sha256=SHA, role=item['role'],
                                  original_physical_loc=3, canonical_loc=4)
            counted[identity] = dict(id=identity, inputs=keys, original_physical_loc=6, canonical_loc=8,
                                    canonical_loc_qualified=True, formatted_loc_qualified=False, formatted_loc=None)
            pins.update({a['path']: SHA for a in sources+artifacts})
    return rows, counted, files, runtime, pins


def qualification_fixture():
    rows, counted, files, runtime, pins = cohort()
    plan = dict(runtime, profiles=list(rows.values()), schema='kotlin-retained-compiled-work-plan-v1',
                controller_sha256=full.WORK_CONTROLLER_SHA, planned_native_commands=21)
    refs = dict(plan=ref('remaining/plan.json'), report=ref('remaining/output/report.json'),
                terminal=ref('remaining/output/terminal.json'),
                first_capture_reconciliation=ref('remaining/output/first-capture-reconciliation.json'))
    first = dict(schema='kotlin-first-single-entry-additive-reconciliation-v1', id=full.FIRST_ID,
                 original_status='failed', original_error='Prescribed complete stdout differs',
                 original_plan_sha256=full.FIRST_REFS['plan']['sha256'],
                 original_report_sha256=full.FIRST_REFS['report']['sha256'],
                 original_terminal_sha256=full.FIRST_REFS['terminal']['sha256'],
                 complete_subject_output_match=True, native_commands_reexecuted=0,
                 retained_vm_diagnostic='[0.023s][warning][os] Loading hsdis library failed\n',
                 source_work_qualified=False, benchmark_samples=0)
    remaining = dict(schema='kotlin-single-entry-remaining-plan-v1', controller_sha256=full.REMAINING_CONTROLLER_SHA,
                     capture_sha256=full.CAPTURE_SHA, ids=full.REMAINING_IDS[:], excluded_id=full.FIRST_ID,
                     output=str(Path(refs['terminal']['path']).parent),
                     profiles=[copy.deepcopy(rows[i]) for i in full.REMAINING_IDS], planned_native_commands=3,
                     prior_native_commands_reused=1, automatic_retries=0,
                     prescribed_inputs={'binarytrees': 21, 'pidigits': 10000},
                     first_capture_reconciliation=first, source_work_qualified=False, benchmark_samples=0)
    report = dict(schema='kotlin-single-entry-remaining-results-v1', status=full.REMAINING_COMPLETE,
                  plan=refs['plan']['path'], plan_sha256=SHA, active=None,
                  profiles=[dict(id=i, complete_output_match=True) for i in full.REMAINING_IDS],
                  native_processes_started=3, prior_native_commands_reused=1,
                  remaining_receipt_errors=[], process_receipt_errors=[], integrity_errors=[],
                  registered_native_commands=[dict(id=i, pid=n+100, pgid=n+100) for n,i in enumerate(full.REMAINING_IDS)],
                  commands={i:{} for i in full.REMAINING_IDS}, validated_command_artifacts={i:{} for i in full.REMAINING_IDS},
                  first_capture_reconciliation=first, source_work_qualified=False, benchmark_samples=0)
    terminal = dict(status=full.REMAINING_COMPLETE, report_sha256=SHA, native_processes_started=3,
                    common_mutex_held=True, common_mutex_inode=79859134, integrity_errors=[], artifact_errors=[],
                    process_receipt_errors=[], registered_native_commands=report['registered_native_commands'],
                    source_work_qualified=False, benchmark_samples=0)
    receipt = dict(schema='kotlin-retained-compiled-work-qualified-v1', status='all20-retained-required-work-qualified',
                   source_work_qualified=True, compiled_work_profiles=20, compiled_work=copy.deepcopy(full.WORK_REFS),
                   single_entry_remaining=refs, decisions=ref('independent-decisions.json'),
                   profiles=[dict(id=i, decision_id=i, source_work_qualified=True) for i in rows],
                   subject_recompilations=0, benchmark_samples=0, full_timings_qualified=False, chart_admission=False)
    decisions = dict(schema='kotlin-independent-required-work-decisions-v1',
                     status='all20-retained-required-work-reviewed', compiled_work=copy.deepcopy(full.WORK_REFS),
                     single_entry_remaining=refs, profiles=[])
    for identity, original in rows.items():
        paths = [str(full.WORK/'run-v2'/identity/n) for n in ('validated.json','process.json','hotspot.xml')]
        if identity in [full.FIRST_ID]+full.REMAINING_IDS:
            directory = (full.FIRST/'run-v1'/identity if identity == full.FIRST_ID
                         else Path(refs['terminal']['path']).parent/identity)
            paths += [str(directory/n) for n in ('process.json','hotspot.xml')]
            paths += [refs['first_capture_reconciliation']['path'] if identity == full.FIRST_ID else str(directory/'capture-index.json')]
        evidence = {p:SHA for p in paths};pins.update(evidence)
        decisions['profiles'].append(dict(id=identity, source_work_qualified=True,
            physical_inputs=copy.deepcopy(original['physical_inputs']), class_artifacts=copy.deepcopy(original['class_artifacts']),
            retained_runtime_command=copy.deepcopy(original['retained_runtime_command']),
            runtime_environment=copy.deepcopy(original['runtime_environment']), runtime_binding=copy.deepcopy(runtime),
            checks={k:True for k in full.COMMON_CHECKS | full.SPECIAL_CHECKS.get(original['benchmark'],set())},
            rationale='Synthetic unit-test record only; no native qualification.', evidence_pins=evidence))
    return rows, counted, files, plan, pins, refs, first, remaining, report, terminal, receipt, decisions


class KotlinFullPolicy(unittest.TestCase):
    def setUp(self):
        (self.rows,self.counted,self.files,self.plan,self.pins,self.refs,self.first,self.remaining,
         self.report,self.terminal,self.receipt,self.decisions) = qualification_fixture()

    def candidate(self, identity='kotlin-nbody-compact'):
        return full.candidate(self.rows[identity],self.counted[identity],self.files,self.plan,self.pins)

    def validate_decisions(self):
        return full.validate_decisions(self.receipt,self.decisions,self.plan,self.remaining,self.pins,self.refs)

    def validate_remaining(self):
        return full.validate_remaining(self.refs,self.remaining,self.report,self.terminal,self.first)

    def test_clean_twenty_one_command_producer_keeps_its_open_gate(self):
        status='all20-bounded-work-witnesses-recorded-with-separate-open-gates'
        flags=dict(required_work_witnesses_qualified=True,subject_JIT_method_evidence_qualified=True,
                   actual_subject_runtime_dependency_closure_qualified=True,specified_case_coverage_qualified=True)
        counts=dict(native_processes_started=21,diagnostic_compiler_processes_started=1,
                    work_jvm_processes_started=20,observed_main_invocations=200000,observed_main_returns=200000)
        report=dict(flags,**counts,schema='kotlin-retained-compiled-work-results-v1',status=status,
                    plan=full.WORK_REFS['plan']['path'],plan_sha256=full.WORK_REFS['plan']['sha256'],
                    active=None,profiles=[dict(id=i) for i in self.rows],integrity_errors=[],
                    process_receipt_errors=[],missing_main_observations=[],source_work_qualified=False,
                    subject_recompilations=0,benchmark_samples=0)
        terminal=dict(flags,**counts,status=status,report_sha256=full.WORK_REFS['report']['sha256'],
                      common_mutex_held=True,common_mutex_inode=79859134,integrity_errors=[],artifact_errors=[],
                      process_receipt_errors=[],missing_main_observations=[],source_work_qualified=False)
        full.validate_work_producer(self.plan,report,terminal)
        for change in [lambda:report.update(observed_main_returns=199999),
                       lambda:terminal.update(diagnostic_compiler_processes_started=True),
                       lambda:report.update(source_work_qualified=True),
                       lambda:terminal.update(common_mutex_held=False),
                       lambda:terminal['process_receipt_errors'].append('unreaped'),
                       lambda:report['profiles'].pop()]:
            saved=copy.deepcopy((report,terminal));change()
            with self.assertRaises(AssertionError):full.validate_work_producer(self.plan,report,terminal)
            report,terminal=saved

    def test_unqualified_producer_cannot_replace_independent_receipt(self):
        self.assertEqual(len(self.validate_decisions()),20)
        self.receipt['source_work_qualified']=False
        with self.assertRaises(AssertionError):self.validate_decisions()

    def test_missing_duplicate_and_unqualified_work_decisions_fail(self):
        for mutation in [lambda d:d['profiles'].pop(),lambda d:d['profiles'].append(d['profiles'][0]),
                         lambda d:d['profiles'][0]['checks'].update(long_lived_graph_gc_roots=False),
                         lambda d:d['profiles'][0].update(rationale='')]:
            original=copy.deepcopy(self.decisions);mutation(self.decisions)
            with self.assertRaises(AssertionError):self.validate_decisions()
            self.decisions=original

    def test_source_class_runtime_and_native_evidence_substitution_fail(self):
        for mutate in [lambda r:r['physical_inputs'][0].update(sha256='0'*64),
                       lambda r:r['class_artifacts'][0].update(sha256='0'*64),
                       lambda r:r['runtime_binding'].update(java='/wrong/java'),
                       lambda r:r['retained_runtime_command'].append('-Xint'),
                       lambda r:r['evidence_pins'].clear(),
                       lambda r:r['evidence_pins'].update({'/unretained/hotspot.xml':SHA})]:
            original=copy.deepcopy(self.decisions);mutate(self.decisions['profiles'][0])
            with self.assertRaises(AssertionError):self.validate_decisions()
            self.decisions=original

    def test_pi_general_division_decision_and_capture_index_are_required(self):
        row=next(r for r in self.decisions['profiles'] if r['id']=='kotlin-pidigits-optimized')
        row['checks'].pop('both_general_divisions_before_every_comparison')
        with self.assertRaises(AssertionError):self.validate_decisions()
        row['checks']['both_general_divisions_before_every_comparison']=True
        row['evidence_pins'].pop(str(Path(self.refs['terminal']['path']).parent/row['id']/'capture-index.json'))
        with self.assertRaises(AssertionError):self.validate_decisions()

    def test_successful_remaining_three_and_first_reuse_are_mandatory(self):
        self.validate_remaining()
        for mutation in [lambda:self.report.update(status='failed'),lambda:self.report.update(active={'pid':42}),
                         lambda:self.report.update(native_processes_started=2),
                         lambda:self.report['registered_native_commands'][1].update(pid=100,pgid=100),
                         lambda:self.report['remaining_receipt_errors'].append('unreaped'),
                         lambda:self.terminal['artifact_errors'].append('missing'),
                         lambda:self.first.update(native_commands_reexecuted=1),
                         lambda:self.first.update(original_status='passed'),
                         lambda:self.remaining.update(ids=[full.FIRST_ID]+full.REMAINING_IDS),
                         lambda:self.first.update(retained_vm_diagnostic='')]:
            saved=copy.deepcopy((self.report,self.terminal,self.first,self.remaining));mutation()
            with self.assertRaises(AssertionError):self.validate_remaining()
            self.report,self.terminal,self.first,self.remaining=saved

    def test_canonical_loc_and_no_fabricated_formatted_loc(self):
        row=self.candidate()
        self.assertEqual(row['loc'],8);self.assertTrue(row['canonical_loc_qualified'])
        self.assertIsNone(row['formatted_loc']);self.assertFalse(row['formatted_loc_qualified'])
        self.counted['kotlin-nbody-compact']['formatted_loc']=6
        with self.assertRaises(AssertionError):self.candidate()

    def test_changed_command_heap_gc_processor_or_diagnostic_flags_fail(self):
        key='kotlin-nbody-compact'
        for flag in ['-Xmx1g','-XX:+UseSerialGC','-XX:ActiveProcessorCount=1','-XX:+LogCompilation']:
            saved=copy.deepcopy(self.rows[key]);self.rows[key]['retained_runtime_command'].insert(1,flag)
            with self.assertRaises(AssertionError):self.candidate()
            self.rows[key]=saved
        self.rows[key]['runtime_environment']['JAVA_TOOL_OPTIONS']=''
        with self.assertRaises(AssertionError):self.candidate()

    def test_unpinned_class_and_loc_source_omission_fail(self):
        key='kotlin-nbody-compact';artifact=self.rows[key]['class_artifacts'][0]
        digest=self.pins.pop(artifact['path'])
        with self.assertRaises(AssertionError):self.candidate()
        self.pins[artifact['path']]=digest
        self.counted[key]['inputs'].pop()
        with self.assertRaises(AssertionError):self.candidate()

    def test_exact_ninety_slots_rotation_and_full_sizes(self):
        controls={b:dict(id='mech-aot-control',key=b+':control',benchmark=b,language='mech') for b in full.BENCHES}
        prerequisite=(self.rows,self.counted,self.files,self.plan,self.pins,[])
        with patch.object(full,'prerequisites',return_value=prerequisite),patch.object(full,'controls',return_value=controls):
            plan=full.build_draft('/synthetic-only/future-output',ref('qualification.json'))
        self.assertEqual(len(plan['schedule']),90)
        self.assertEqual(sum(slot[2].startswith('kotlin-') for slot in plan['schedule']),60)
        self.assertEqual(plan['formatted_loc_profiles'],0)
        self.assertFalse(plan['pins_verified']);self.assertFalse(plan['full_timings_qualified'])
        for bench,manifest in plan['manifests'].items():
            self.assertEqual(manifest['size'],full.FULL[bench][0])
            for position in range(3):self.assertEqual(len({o['profiles'][position] for o in manifest['orders']}),3)
        for mutate in [lambda p:p['manifests'].pop('nbody'),
                       lambda p:p['manifests']['nbody']['orders'][0]['profiles'].reverse(),
                       lambda p:p['manifests']['nbody']['profiles'].pop()]:
            changed=copy.deepcopy(plan);mutate(changed)
            with self.assertRaises(AssertionError):full.schedule_for(changed['manifests'])
        with patch.object(full,'build_draft',return_value=copy.deepcopy(plan)):
            with self.assertRaises(AssertionError):full.validate_plan(plan,prepared=True)
            prepared=copy.deepcopy(plan);prepared.update(status='prepared-awaiting-independent-review',pins_verified=True)
            full.validate_plan(prepared,prepared=True)
            for mutate in [lambda p:p['manifests']['nbody'].update(size=100),
                           lambda p:p['manifests']['nbody'].update(maximum_rss_mib=99999),
                           lambda p:p['manifests']['nbody'].update(timeout_seconds=99999),
                           lambda p:p.update(no_automatic_retry=False),lambda p:p.update(chart_admission=True),
                           lambda p:p['pins'].pop(str(full.HELPERS))]:
                changed=copy.deepcopy(prepared);mutate(changed)
                with self.assertRaises(AssertionError):full.validate_plan(changed,prepared=True)

    def test_missing_qualification_has_no_fallback_or_plan(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'absent.json'
            with self.assertRaises(FileNotFoundError):full.prerequisites(dict(path=str(path),sha256=SHA))
            self.assertEqual(list(Path(directory).iterdir()),[])

    def test_busy_common_mutex_prevents_even_runtime_hash_preparation(self):
        with tempfile.TemporaryDirectory() as directory:
            args=types.SimpleNamespace(plan=Path(directory)/'new-plan.json')
            with patch.object(full,'common_lock',side_effect=BlockingIOError('busy')), \
                 patch.object(full,'checked_runtime') as check:
                with self.assertRaises(BlockingIOError):full.prepare(args)
                check.assert_not_called()
            self.assertEqual(list(Path(directory).iterdir()),[])

    def test_metadata_change_and_nested_terminal_inventory_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);sub=root/'command';sub.mkdir();nested=sub/'terminal.json';nested.write_text('{}\n')
            terminal=root/'terminal.json';terminal.write_text('{}\n')
            meta=root/'report.json';meta.write_text('{}\n')
            pins={};reference=dict(path=str(meta),sha256=full.sha(meta));full.read_ref(reference,pins)
            artifacts={'command/terminal.json':dict(bytes=nested.stat().st_size,sha256=full.sha(nested)),
                       'report.json':dict(bytes=meta.stat().st_size,sha256=full.sha(meta))}
            closure=dict(directory=str(root),terminal=dict(path=str(terminal),sha256=full.sha(terminal)),artifacts=artifacts)
            full.verify_artifact_inventories([closure])
            omitted=copy.deepcopy(closure);omitted['artifacts'].pop('command/terminal.json')
            with self.assertRaises(AssertionError):full.verify_artifact_inventories([omitted])
            meta.write_text('[]\n')
            with self.assertRaises(AssertionError):full.read_ref(reference,{})
            with self.assertRaises(AssertionError):full.verify(pins)
            (root/'late.txt').write_text('late')
            with self.assertRaises(AssertionError):full.verify_artifact_inventories([closure])

    def test_complete_output_cannot_override_nonempty_stderr(self):
        with patch.object(full.shared,'qualified_sample'):
            full.qualified_sample({'stderr':''},{},{},'fingerprint')
            with self.assertRaises(AssertionError):full.qualified_sample({'stderr':'JVM warning'},{},{},'fingerprint')


if __name__ == '__main__':
    unittest.main()
