"""Pure tests for Scala owner adaptation and capture failure closure; no JVM runs."""
from contextlib import ExitStack
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

PATH = Path(__file__).with_name('scala_single_entry.py')
SPEC = importlib.util.spec_from_file_location('tested_scala_single_entry', PATH)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class ScalaSingleEntry(unittest.TestCase):
    def test_exact_two_original_mains_and_full_input_flags(self):
        plan = {'compiled': {'java': '/synthetic/jdk/bin/java'}}
        for bench, n in [('binarytrees', 21), ('pidigits', 10000)]:
            profile = dict(benchmark=bench, runtime_classpath='/classes:/scala3.jar:/scala.jar')
            command, env = m.command_for(plan, profile, Path('/synthetic/case'))
            self.assertEqual(command[-4:], ['-cp', profile['runtime_classpath'], 'Main', str(n)])
            self.assertEqual(command[1:5], ['-XX:ActiveProcessorCount=8', '-Xms64m', '-Xmx8g', '-XX:+UseG1GC'])
            self.assertEqual(env['JAVA_HOME'], '/synthetic/jdk')
            self.assertNotIn('JAVA_TOOL_OPTIONS', env)
            self.assertFalse(any('compileonly' in a.lower() or 'threshold' in a.lower() for a in command))
        self.assertEqual(m.kb.RSS_LIMIT, 10*1024**3)
        self.assertEqual(m.b.kb.RSS_LIMIT, 2*1024**3)
        self.assertEqual(m.receipt_reader.kb.RSS_LIMIT, m.kb.RSS_LIMIT)

    def test_scala_dollar_owners_are_literal_argv_and_kotlin_is_not_targeted(self):
        argv = m.options('pidigits', Path('/synthetic/pi'))
        self.assertIn('-XX:CompileCommand=print,scala.math.BigInt::$div', argv)
        self.assertTrue(m.targeted('Main$ main ([Ljava/lang/String;)V', 'pidigits'))
        self.assertTrue(m.targeted('scala.math.BigInt $div (Lscala/math/BigInt;)Lscala/math/BigInt;', 'pidigits'))
        self.assertTrue(m.targeted('Main$Node check ()I', 'binarytrees'))
        self.assertTrue(m.targeted('Main$$anon$1 call ()Ljava/lang/String;', 'binarytrees'))
        self.assertFalse(m.targeted('clbg.pidigits.MainKt main ([Ljava/lang/String;)V', 'pidigits'))
        self.assertFalse(m.targeted('Main$Node check ()I', 'pidigits'))
        self.assertFalse(m.targeted('scala.math.BigInt $times (Lscala/math/BigInt;)Lscala/math/BigInt;', 'pidigits'))

    def test_full_oracles_are_not_reduced_bounded_outputs(self):
        for bench, expected in m.OUTPUTS.items():
            raw = m.expected_output(bench)
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()), expected)
        with self.assertRaises(AssertionError):
            m.expected_output('nbody')

    def class_fixture(self):
        profile = dict(classes='/synthetic/classes', artifacts=[{'relative_path': n} for n in ('Main.class', 'Main$.class', 'Main$Node.class')])
        plan = dict(runtime_class_owners={'scala.math.BigInt': '/synthetic/scala.jar'})
        text = ('[0.1s][class,load] java.lang.Object source: shared objects file\n'
                '[0.1s][class,load] Main source: file:/synthetic/classes/\n'
                '[0.1s][class,load] Main$ source: file:/synthetic/classes/\n'
                '[0.1s][class,load] Main$$$Lambda/0x1234 source: Main$\n'
                '[0.1s][class,load] scala.math.BigInt source: file:/synthetic/scala.jar\n')
        return profile, plan, text

    def test_actual_owner_inventory_admits_only_bound_subject_and_runtime_origins(self):
        profile, plan, text = self.class_fixture()
        got = m.validate_classes(text, profile, plan)
        self.assertEqual(got['Main$'], 'file:/synthetic/classes/')
        self.assertIn('scala.math.BigInt', got)
        for bad in (text.replace('/synthetic/scala.jar', '/different/scala.jar'),
                    text+'[0.1s][class,load] Helper source: file:/synthetic/classes/\n',
                    text.replace('Main$ source: file:/synthetic/classes/', 'Main$ source: shared objects file'),
                    text.replace('source: Main$', 'source: UnboundHost')):
            with self.subTest(bad=bad), self.assertRaises(AssertionError):
                m.validate_classes(bad, profile, plan)

    def code_fixture(self, method='Main$ main ([Ljava/lang/String;)V'):
        owner, name, descriptor = method.split(' ')
        root = ET.Element('hotspot_log')
        ET.SubElement(root, 'hotspot_log_done')
        attrs = dict(compile_id='1', compiler='c2', level='4', entry='0x100', method=method)
        ET.SubElement(root, 'nmethod', attrs)
        printed = ET.SubElement(root, 'print_nmethod', {k: v for k, v in attrs.items() if k in ('compile_id', 'compiler', 'level')})
        printed.text = (f"# {{method}} {{0x55}} '{name}' '{descriptor}' in '{owner.replace('.', '/')}'\n"
                        'main code [0x100,0x110] = 16\n[MachCode]\n'
                        '  0x100: 1f20 03d5 | e953 40d1 \n'
                        '  0x108: ; ImmutableOopMap {[0]=Oop}\n'
                        '  0x108: 3f01 00f9 | ff03 02d1 \n[/MachCode]\n')
        return root

    def test_scala_native_identity_and_complete_machine_bytes(self):
        value = m.capture_index(self.code_fixture(), 'pidigits')
        self.assertEqual(value['native_methods'][0]['instruction_coverage']['bytes'], 16)
        self.assertEqual(len(value['native_methods'][0]['oopmaps']), 1)
        self.assertFalse(value['both_pi_divisions_proved'])
        self.assertFalse(value['source_work_qualified'])

    def test_missing_wrong_owner_or_incomplete_target_print_rejected(self):
        for fault in ('missing', 'owner', 'bytes', 'identity', 'duplicate'):
            with self.subTest(fault=fault):
                root = self.code_fixture()
                printed = root.find('print_nmethod')
                if fault == 'missing':
                    root.remove(printed)
                elif fault == 'owner':
                    printed.text = printed.text.replace("in 'Main$'", "in 'Other'")
                elif fault == 'bytes':
                    printed.text = printed.text.replace('  0x108: 3f01 00f9 | ff03 02d1 \n', '')
                elif fault == 'identity':
                    printed.set('compiler', 'c1')
                else:
                    ET.SubElement(root, 'print_nmethod', dict(printed.attrib))
                with self.assertRaises(AssertionError):
                    m.capture_index(root, 'pidigits')

    def test_uncompiled_main_is_retained_as_unqualified_evidence(self):
        root = ET.Element('hotspot_log')
        ET.SubElement(root, 'hotspot_log_done')
        value = m.capture_index(root, 'pidigits')
        self.assertEqual(value['native_methods'], [])
        self.assertFalse(value['both_pi_divisions_proved'])

    def test_node_elimination_and_inlined_main_references_are_not_discarded(self):
        root = self.code_fixture('Main$ tree (I)LMain$Node;')
        task = ET.SubElement(root, 'task', compile_id='1', method='Main$ tree (I)LMain$Node;')
        ET.SubElement(task, 'klass', id='2', name='Main$Node')
        ET.SubElement(task, 'klass', id='3', name='Main$')
        ET.SubElement(task, 'method', id='4', holder='3', name='main')
        ET.SubElement(task, 'eliminate_allocation', type='2')
        value = m.capture_index(root, 'binarytrees')
        self.assertTrue(value['node_allocation_eliminations'][0]['installed_nmethod'])
        self.assertEqual(value['main_method_references'][0]['holder'], 'Main$')
        self.assertFalse(value['allocation_and_lifetime_proved'])

    def final_fixture(self, directory):
        output = directory/'run'
        output.mkdir()
        compiled = directory/'compiled'
        compiled.mkdir()
        bounded = directory/'bounded'
        bounded.mkdir()
        pin = directory/'input'
        pin.write_text('pinned')
        stage = output/'binarytrees'
        stage.mkdir()
        receipt = dict(pid=42, pgid=42, native_process_started=True, direct_child_reaped=True,
                       remaining_process_group=[], cleanup_errors=[], status='failed')
        (stage/'process.json').write_text(json.dumps(receipt))
        report = dict(status='failed', active=None, profiles=[], native_processes_started=1,
                      registered_commands=[dict(benchmark='binarytrees', pid=42)],
                      validated_artifacts={'binarytrees': m.b.inventory(stage)})
        plan = dict(profiles=[dict(benchmark=x) for x in m.INPUTS],
                    compiled=dict(report=str(compiled/'report.json'), artifacts={}),
                    bounded_prerequisite=dict(report=str(bounded/'report.json'), artifacts={}))
        return report, plan, output, {str(pin): m.sha(pin)}

    def test_failure_closure_retains_partial_process_and_original_receipt(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(m.b, 'execution_inputs'), patch.object(m.kb.kh, 'verify_lock'):
            report, plan, output, pins = self.final_fixture(Path(temp))
            original = (output/'binarytrees/process.json').read_bytes()
            m.finish(report, plan, output, pins, object())
            terminal = json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'], 'failed')
            self.assertEqual(terminal['integrity_errors'], [])
            self.assertEqual((output/'binarytrees/process.json').read_bytes(), original)
            self.assertIn('binarytrees/process.json', terminal['available_evidence'])
            self.assertFalse(terminal['source_work_qualified'])

    def test_unreaped_unknown_pid_or_fabricated_success_fail_closed(self):
        for fault in ('unreaped', 'pid', 'success'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp, patch.object(m.b, 'execution_inputs'), patch.object(m.kb.kh, 'verify_lock'):
                report, plan, output, pins = self.final_fixture(Path(temp))
                path = output/'binarytrees/process.json'
                if fault == 'unreaped':
                    receipt = json.loads(path.read_bytes()); receipt['direct_child_reaped'] = False; path.write_text(json.dumps(receipt))
                elif fault == 'pid':
                    report['registered_commands'][0]['pid'] = 43
                else:
                    report['status'] = m.SUCCESS
                m.finish(report, plan, output, pins, object())
                terminal = json.loads((output/'terminal.json').read_bytes())
                self.assertEqual(terminal['status'], 'failed-integrity')
                self.assertTrue(terminal['integrity_errors'])

    def test_changed_validated_bytes_and_last_inventory_pin_mutation_rejected(self):
        for fault in ('artifact', 'pin-during-final-inventory'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as temp, patch.object(m.b, 'execution_inputs'), patch.object(m.kb.kh, 'verify_lock'):
                report, plan, output, pins = self.final_fixture(Path(temp))
                if fault == 'artifact':
                    (output/'binarytrees/late.txt').write_text('changed')
                original = m.b.inventory
                def inventory(path, exclude=()):
                    result = original(path, exclude)
                    if fault != 'artifact' and exclude == ('terminal.json',):
                        Path(next(iter(pins))).write_text('changed')
                    return result
                with patch.object(m.b, 'inventory', side_effect=inventory):
                    m.finish(report, plan, output, pins, object())
                self.assertEqual(json.loads((output/'terminal.json').read_bytes())['status'], 'failed-integrity')

    def test_changed_common_mutex_is_recorded_as_unheld(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(m.b, 'execution_inputs'), patch.object(m.kb.kh, 'verify_lock', side_effect=AssertionError('changed mutex')):
            report, plan, output, pins = self.final_fixture(Path(temp))
            m.finish(report, plan, output, pins, object())
            terminal = json.loads((output/'terminal.json').read_bytes())
            self.assertFalse(terminal['common_mutex_held'])
            self.assertEqual(terminal['status'], 'failed-integrity')

    def test_signal_handlers_transfer_to_owned_cleanup(self):
        handlers = {}
        def run(args):
            self.assertEqual(set(handlers), m.kb.kh.SIGNALS)
            for sig, handler in handlers.items():
                with self.assertRaises(KeyboardInterrupt):
                    handler(sig, None)
            return 19
        with patch.object(m.sys, 'argv', ['stage', 'run', '--plan', '/synthetic/plan', '--plan-sha256', '0'*64]), \
             patch.object(m.signal, 'signal', side_effect=lambda sig, handler: handlers.__setitem__(sig, handler)), \
             patch.object(m, 'run', side_effect=run):
            self.assertEqual(m.main(), 19)


if __name__ == '__main__':
    unittest.main()
