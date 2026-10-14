"""Pure saved-evidence and fail-closed continuation tests; no native work."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

PATH = Path(__file__).with_name('kotlin_single_entry_final.py')
SPEC = importlib.util.spec_from_file_location('tested_final_kotlin_capture', PATH)
m = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(m)


class FinalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((m.SECOND/'plan-v1.json').read_bytes())
        cls.row = cls.plan['profiles'][1]
        cls.xml_path = m.SECOND/'run-v1'/cls.row['id']/'hotspot.xml'
        cls.xml = cls.xml_path.read_bytes()

    def test_exact_final_cohort_and_unchanged_options(self):
        self.assertEqual(m.FINAL_ID, m.base.IDS[-1])
        self.assertEqual(m.REUSED_IDS, m.base.IDS[:-1])
        self.assertNotIn(m.FINAL_ID, m.REUSED_IDS)
        self.assertEqual(m.base.INPUTS['pidigits'], 10000)
        self.assertEqual(m.kb.FLAGS, ['-XX:ActiveProcessorCount=8', '-Xms64m', '-Xmx8g', '-XX:+UseG1GC'])

    def test_both_actual_pi_bytecode_rows(self):
        for row in self.plan['profiles'][1:]:
            with self.subTest(identity=row['id']):
                proof = m.pi_bytecode(row)
                self.assertEqual(proof['divide_bcis'], [122, 201])
                self.assertEqual(proof['comparison_bci'], 216)
                self.assertEqual(proof['backedges'], [[381, 48], [388, 48], [539, 48]])
                self.assertTrue(proof['ordered_divides_dominate_each_comparison'])
                self.assertIs(proof['numeric_runtime_division_count_proved'], False)

    def changed_bytecode(self, old, new):
        row = deepcopy(self.row)
        raw = Path(row['retained_disassembly']['path']).read_text()
        before, method = raw.split('  public static final void main(java.lang.String[]);', 1)
        self.assertIn(old, method)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'javap.stdout'
            path.write_text(before+'  public static final void main(java.lang.String[]);'+method.replace(old, new, 1))
            row['retained_disassembly'] = dict(path=str(path), sha256=m.sha(path))
            m.pi_bytecode(row)

    def test_missing_or_specialized_divide_fails(self):
        for replacement in ('java/math/BigInteger.divideAndRemainder:', 'java/math/BigInteger.divideKnuth:'):
            with self.subTest(replacement=replacement), self.assertRaisesRegex(AssertionError, 'divides/comparison'):
                self.changed_bytecode('java/math/BigInteger.divide:', replacement)

    def test_bypass_first_divide_fails_dominance(self):
        with self.assertRaises(AssertionError):
            self.changed_bytecode('54: aload_2', '54: goto          133')

    def test_backedge_entering_comparison_fails(self):
        with self.assertRaisesRegex(AssertionError, 'loop boundary/backedges'):
            self.changed_bytecode('539: goto          48', '539: goto          212')

    def test_exception_edge_fails(self):
        with self.assertRaisesRegex(AssertionError, 'exception edges'):
            self.changed_bytecode('      stack=4, locals=15, args_size=1',
                                  '      stack=4, locals=15, args_size=1\n      Exception table:')

    def test_current_class_bytes_must_match(self):
        original = m.sha
        artifact = next(p['path'] for p in self.row['class_artifacts'] if p['relative_path'].endswith('MainKt.class'))
        with patch.object(m, 'sha', side_effect=lambda path: '0'*64 if str(path) == artifact else original(path)):
            with self.assertRaisesRegex(AssertionError, 'class binding'): m.pi_bytecode(self.row)

    def test_actual_interpreted_main_and_all_division_versions(self):
        result = m.pi_index(self.xml_path, self.row)
        self.assertEqual(result['main_execution_path'], 'interpreted-main')
        self.assertEqual(result['main_compilation_events'], {'task_queued': 0, 'task': 0, 'nmethod': 0})
        self.assertEqual(len(result['native_methods']), 8)
        self.assertEqual(result['compilation_log_closure'], dict(queued_tasks=220, completed_tasks=220,
            installed_compiler_methods=220, installed_native_wrappers=32))
        self.assertIs(result['source_work_qualified'], False)
        self.assertIs(result['runtime_pi_division_counts_proved'], False)

    def changed_xml(self, change):
        root = ET.fromstring(self.xml); change(root)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'hotspot.xml'; ET.ElementTree(root).write(path, encoding='utf-8')
            return m.pi_index(path, self.row)

    @staticmethod
    def remove(root, tag):
        for parent in root.iter():
            for node in parent:
                if node.tag == tag:
                    parent.remove(node); return
        raise AssertionError('Missing test fixture tag '+tag)

    def test_missing_footer_or_compiler_records_fail(self):
        for tag in ('hotspot_log_done', 'task_done', 'task_queued', 'task', 'nmethod'):
            with self.subTest(tag=tag), self.assertRaises(AssertionError):
                # The first nmethod is a native wrapper; remove a compiler entry instead.
                if tag == 'nmethod':
                    def change(root):
                        for parent in root.iter():
                            for node in parent:
                                if node.tag == 'nmethod' and node.get('compiler') in ('c1', 'c2'):
                                    parent.remove(node); return
                else:
                    change = lambda root: self.remove(root, tag)
                self.changed_xml(change)

    def test_duplicate_task_and_failed_task_fail(self):
        def duplicate(root): root.append(deepcopy(next(root.iter('task'))))
        def failed(root): next(root.iter('task_done')).set('success', '0')
        for change in (duplicate, failed):
            with self.subTest(change=change.__name__), self.assertRaises(AssertionError): self.changed_xml(change)

    def test_logging_or_compiler_failure_fails(self):
        for tag in ('failure', 'log_error', 'code_cache_full', 'make_not_compilable'):
            with self.subTest(tag=tag), self.assertRaisesRegex(AssertionError, 'Compiler or logging'):
                self.changed_xml(lambda root: ET.SubElement(root, tag))

    def test_unfinished_main_queue_fails(self):
        with self.assertRaisesRegex(AssertionError, 'inventory incomplete'):
            self.changed_xml(lambda root: ET.SubElement(root, 'task_queued', compile_id='999', method=m.PI_MAIN))

    def test_main_method_reference_prevents_interpreted_inference(self):
        def change(root):
            task = next(root.iter('task'))
            ET.SubElement(task, 'klass', id='99990', name='clbg.pidigits.MainKt')
            ET.SubElement(task, 'method', id='99991', holder='99990', name='main')
        with self.assertRaisesRegex(AssertionError, 'inline compilation evidence'): self.changed_xml(change)

    def test_every_installed_division_version_needs_complete_print(self):
        with self.assertRaisesRegex(AssertionError, 'Missing/duplicate emitted'):
            self.changed_xml(lambda root: self.remove(root, 'print_nmethod'))
        def truncated(root):
            printed = next(root.iter('print_nmethod'))
            printed.text = ''.join(printed.itertext()).replace('[/MachCode]', '', 1)
        with self.assertRaisesRegex(AssertionError, 'MachCode boundaries'): self.changed_xml(truncated)

    @staticmethod
    def add_compiled_main(root):
        native = deepcopy(next(n for n in root.iter('nmethod') if n.get('compile_id') == '153'))
        native.set('compile_id', '999'); native.set('method', m.PI_MAIN); native.set('bytes', '560'); root.append(native)
        printed = deepcopy(next(n for n in root.iter('print_nmethod') if n.get('compile_id') == '153'))
        printed.set('compile_id', '999')
        text = ''.join(printed.itertext())
        text = re.sub(r'(Compiled method \(c1\)\s+\d+\s+)153(\s)', r'\g<1>999\2', text)
        text = text.replace('java.math.BigInteger::divide (', 'clbg.pidigits.MainKt::main (')
        text = text.replace('clbg.pidigits.MainKt::main (38 bytes)', 'clbg.pidigits.MainKt::main (560 bytes)')
        text = text.replace("'divide' '(Ljava/math/BigInteger;)Ljava/math/BigInteger;' in 'java/math/BigInteger'",
                            "'main' '([Ljava/lang/String;)V' in 'clbg/pidigits/MainKt'")
        printed.text = text; root.append(printed)
        for tag in ('task_queued', 'task'):
            node = ET.SubElement(root, tag, compile_id='999', method=m.PI_MAIN, bytes='560')
            if tag == 'task': ET.SubElement(node, 'task_done', success='1')

    def test_compiled_main_captured_without_semantic_qualification(self):
        result = self.changed_xml(self.add_compiled_main)
        self.assertEqual(result['main_execution_path'], 'compiled-main-versions-captured')
        self.assertEqual(len(result['native_methods']), 9)
        self.assertIs(result['source_work_qualified'], False)

    @classmethod
    def add_osr_main(cls, root):
        cls.add_compiled_main(root)
        for tag in ('task_queued', 'task', 'nmethod', 'print_nmethod'):
            node = next(n for n in root.iter(tag) if n.get('compile_id') == '999')
            node.set('compile_kind', 'osr')
            if tag in ('task_queued', 'task'): node.set('osr_bci', '48')
            if tag == 'print_nmethod':
                node.text = ''.join(node.itertext()).replace('::main (', '::main @ 48 (')

    def test_osr_main_and_entry_bci_match(self):
        result = self.changed_xml(self.add_osr_main)
        self.assertEqual(result['main_execution_path'], 'compiled-main-versions-captured')
        self.assertEqual(result['native_methods'][-1]['compile_kind'], 'osr')
        def wrong_entry(root):
            self.add_osr_main(root)
            node = next(n for n in root.iter('print_nmethod') if n.get('compile_id') == '999')
            node.text = ''.join(node.itertext()).replace('::main @ 48 (', '::main @ 49 (')
        with self.assertRaisesRegex(AssertionError, 'OSR entry'): self.changed_xml(wrong_entry)

    def test_compiled_main_without_oopmaps_fails(self):
        def change(root):
            self.add_compiled_main(root)
            node = next(n for n in root.iter('print_nmethod') if n.get('compile_id') == '999')
            node.text = ''.join(node.itertext()).replace('ImmutableOopMap', 'RemovedOopMap')
        with self.assertRaisesRegex(AssertionError, 'lacks OopMap'): self.changed_xml(change)

    def test_swapped_print_body_and_changed_compiler_fail(self):
        def swapped(root):
            first, second = list(root.iter('print_nmethod'))[:2]
            first.text, second.text = second.text, first.text
        with self.assertRaisesRegex(AssertionError, 'method owner/name/descriptor'): self.changed_xml(swapped)
        with self.assertRaisesRegex(AssertionError, 'compiler/level/entry'):
            self.changed_xml(lambda root: next(root.iter('print_nmethod')).set('compiler', 'c2'))

    def test_wrong_print_version_header_fails(self):
        def change(root):
            printed = next(root.iter('print_nmethod'))
            printed.text = ''.join(printed.itertext()).replace('  146 ', '  999 ', 1)
        with self.assertRaisesRegex(AssertionError, 'version header'): self.changed_xml(change)

    def test_compiled_main_bytecode_length_must_match_retained_class(self):
        def change(root):
            self.add_compiled_main(root)
            for tag in ('task_queued', 'task', 'nmethod'):
                next(n for n in root.iter(tag) if n.get('compile_id') == '999').set('bytes', '38')
            printed = next(n for n in root.iter('print_nmethod') if n.get('compile_id') == '999')
            printed.text = ''.join(printed.itertext()).replace('::main (560 bytes)', '::main (38 bytes)')
        with self.assertRaisesRegex(AssertionError, 'bytecode length'): self.changed_xml(change)

    def durable(self):
        return {name: json.loads((m.SECOND_JOB/name).read_bytes()) for name in
                ('request.json', 'launch.json', 'worker-started.json', 'command-started.json', 'terminal.json')}

    def test_actual_durable_and_exact_u_flag(self):
        docs = self.durable(); m.validate_durable(docs)
        docs['request.json']['command'].remove('-u')
        with self.assertRaisesRegex(AssertionError, 'command/cwd'): m.validate_durable(docs)

    def test_actual_first_durable_without_u_flag(self):
        docs = {name: json.loads((m.previous.DURABLE.parent/name).read_bytes()) for name in self.durable()}
        m.validate_durable(docs, first=True)
        docs['request.json']['command'].insert(4, '-u')
        with self.assertRaisesRegex(AssertionError, 'command/cwd'): m.validate_durable(docs, first=True)

    def test_pure_environment_matches_fresh_retained_helper(self):
        saved = self.row['runtime_environment']
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            expected = m.expected_environment(saved, directory)
            self.assertEqual(list(directory.iterdir()), [])
            self.assertEqual(m.kb.kh.environment(saved, directory), expected)
            self.assertEqual({p.name for p in directory.iterdir()}, {'home', 'tmp', 'config'})
            for key in ('PATH', 'JAVA_HOME', 'CLASSPATH'):
                self.assertEqual(expected[key], saved[key])

    def test_injected_jvm_environment_fails(self):
        saved = dict(self.row['runtime_environment'], JAVA_TOOL_OPTIONS='-Xint')
        with self.assertRaisesRegex(AssertionError, 'Injected JVM'):
            m.expected_environment(saved, Path('/tmp/case'))

    def test_changed_durable_parent_or_birth_fails(self):
        for old, new in (('57903 57899', '57903 57898'), ('07:03:31', '07:03:30')):
            docs = self.durable()
            for name in ('command-started.json', 'terminal.json'):
                docs[name]['command_identity']['listing'] = docs[name]['command_identity']['listing'].replace(old, new)
            with self.subTest(change=new), self.assertRaisesRegex(AssertionError, 'observed command identity'):
                m.validate_durable(docs)

    def saved_pins(self):
        # Values come from saved receipts. Only small retained evidence is read or
        # hashed here; runtime/library/source closures are not scanned or verified.
        report = json.loads((m.SECOND/'run-v1/report.json').read_bytes())
        terminal = json.loads((m.SECOND/'run-v1/terminal.json').read_bytes())
        pins = dict(report['pins'])
        pins.update({str((m.SECOND/'run-v1'/name).resolve()): item['sha256']
                     for name, item in terminal['available_evidence'].items()})
        pins.update({str(p.resolve()): m.sha(p) for p in m.SECOND_JOB.iterdir() if p.is_file()})
        pins.update({str(p.resolve()): m.sha(p) for p in m.previous.DURABLE.parent.iterdir() if p.is_file()})
        return pins

    def test_actual_prior_metadata_reconciliation_without_closure_scan(self):
        with patch.object(m.base, 'closed_artifacts') as closure:
            plan, proof = m.reconcile_prior(self.saved_pins(), False)
        closure.assert_not_called()
        self.assertEqual(plan['profiles'][-1]['id'], m.FINAL_ID)
        self.assertEqual(proof['reused_ids'], m.REUSED_IDS)
        self.assertEqual(proof['second_original_status'], 'failed')
        self.assertEqual(proof['native_commands_reexecuted'], 0)
        self.assertIs(proof['source_work_qualified'], False)
        self.assertEqual(proof['second_captures'][1]['capture']['main_execution_path'], 'interpreted-main')

    def test_missing_inherited_or_artifact_pin_fails(self):
        for path in (self.plan['java'], str(m.SECOND/'run-v1/kotlin-pidigits-compact/hotspot.xml')):
            pins = self.saved_pins(); del pins[path]
            with self.subTest(path=path), self.assertRaisesRegex(AssertionError, 'pin'):
                m.reconcile_prior(pins, False)

    def test_closed_inventory_includes_nested_terminal_and_rejects_extras(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp); nested = directory/'nested'; nested.mkdir()
            (directory/'terminal.json').write_text('{}'); (nested/'terminal.json').write_text('evidence')
            digest = m.sha(nested/'terminal.json')
            terminal = dict(available_evidence={'nested/terminal.json': dict(bytes=8, sha256=digest)})
            pins = {str((nested/'terminal.json').resolve()): digest}
            m.closed_inventory(directory, terminal, pins, False)
            (directory/'unexpected').write_text('extra')
            with self.assertRaisesRegex(AssertionError, 'inventory changed'):
                m.closed_inventory(directory, terminal, pins, False)

    def successful(self, output):
        proof = {'second_original_status': 'failed', 'native_commands_reexecuted': 0}
        row = {'id': m.FINAL_ID, 'source_work_qualified': False}
        directory = output/m.FINAL_ID; directory.mkdir()
        m.save(directory/'process.json', dict(kind='single-entry-work', native_process_started=True,
            pid=123, pgid=123, direct_child_reaped=True, cleanup_errors=[], remaining_process_group=[]))
        m.save(directory/'validated.json', row); m.save(output/'prior-capture-reconciliation.json', proof)
        report = dict(status=m.COMPLETE, profiles=[row], active=None, native_processes_started=1,
            registered_native_commands=[dict(id=m.FINAL_ID, pid=123, pgid=123)],
            commands={m.FINAL_ID: dict(argv=['java', 'main', '10000'], environment={})},
            validated_command_artifacts={m.FINAL_ID: m.base.snapshot(directory)}, prior_capture_reconciliation=proof)
        return report, {'prior_capture_reconciliation': proof}

    def close(self, output, report, plan, pins=None):
        with patch.object(m.previous, 'validate_saved_receipt'), patch.object(m.kb.kh, 'verify_lock'):
            m.finish(report, plan, pins or {}, output, None)

    def test_one_success_closes_with_all_gates_false(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp); report, plan = self.successful(output); self.close(output, report, plan)
            terminal = json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'], m.COMPLETE)
            self.assertEqual(terminal['native_processes_started'], 1)
            self.assertEqual(terminal['registered_native_commands'], report['registered_native_commands'])
            for key in ('source_work_qualified', 'full_timings_qualified', 'chart_admission'):
                self.assertIs(terminal[key], False)

    def test_missing_profile_and_altered_reused_proof_fail(self):
        for mutation in ('profile', 'proof'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                output = Path(tmp); report, plan = self.successful(output)
                if mutation == 'profile': report['profiles'] = []
                else: m.save(output/'prior-capture-reconciliation.json', {'second_original_status': 'passed'})
                with self.assertRaisesRegex(AssertionError, 'Final native reconciliation'): self.close(output, report, plan)
                self.assertEqual(json.loads((output/'terminal.json').read_bytes())['status'], 'failed-final-native-reconciliation')

    def test_unregistered_native_receipt_fails_even_on_failed_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp); report, plan = self.successful(output); report['status'] = 'failed'
            extra = output/'unexpected'; extra.mkdir(); m.save(extra/'process.json', {})
            with self.assertRaisesRegex(AssertionError, 'Final native reconciliation'): self.close(output, report, plan)
            self.assertEqual(report['final_receipt_errors'], ['Unexpected final native receipt'])

    def test_early_terminal_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp); report, plan = self.successful(output)
            m.save(output/'terminal.json', {'unexpected': True})
            with self.assertRaisesRegex(AssertionError, 'Unexpected terminal'): self.close(output, report, plan)
            self.assertEqual(json.loads((output/'terminal.json').read_bytes()), {'unexpected': True})

    def test_post_snapshot_pin_mutation_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp)/'output'; output.mkdir(); pin = Path(tmp)/'input'; pin.write_text('before')
            report, plan = self.successful(output); digest = m.sha(pin); original = m.base.finish
            def changed_after_snapshot(*args):
                original(*args); pin.write_text('after')
            with patch.object(m.base, 'finish', side_effect=changed_after_snapshot):
                with self.assertRaisesRegex(AssertionError, 'post-snapshot pin'): self.close(output, report, plan, {str(pin): digest})
            terminal = json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'], 'failed-integrity-or-closure')
            self.assertEqual(terminal['report_sha256'], m.sha(output/'report.json'))
            self.assertEqual(terminal['available_evidence']['report.json']['sha256'], terminal['report_sha256'])


if __name__ == '__main__': unittest.main()
