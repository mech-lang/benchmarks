"""Pure metadata/retained-text tests. No VM, compiler, supervisor or full pins."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET
from types import SimpleNamespace

PATH = Path(__file__).with_name('kotlin_single_entry.py')
SPEC = importlib.util.spec_from_file_location('tested_single_entry', PATH)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class CaptureTests(unittest.TestCase):
    def fixture(self, benchmark='binarytrees'):
        root = ET.Element('hotspot_log')
        ET.SubElement(root, 'vm_arguments')
        ET.SubElement(root, 'hotspot_log_done')
        methods = [('main','([Ljava/lang/String;)V')]
        if benchmark == 'binarytrees':
            methods += [('tree','(I)Lclbg/binarytrees/Node;'),('check','(Lclbg/binarytrees/Node;)J')]
        for i,(name,desc) in enumerate(methods,1):
            ET.SubElement(root,'nmethod',compile_id=str(i),compiler='c2',entry='0x100',
                method='clbg.'+benchmark+'.MainKt '+name+' '+desc)
            printed = ET.SubElement(root,'print_nmethod',compile_id=str(i))
            printed.text = '\nmain code [0x100,0x108] = 8\n[MachCode]\n  0x00000100: aabbccdd 01020304\n ; ImmutableOopMap {r0=Oop off=8/0x8}\n[/MachCode]\n'
        return root

    def capture(self, root, benchmark='binarytrees'):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'hotspot.xml'; ET.ElementTree(root).write(path)
            return m.capture_index(path, benchmark)

    def test_tree_capture_is_not_work_qualification(self):
        value = self.capture(self.fixture())
        self.assertEqual(len(value['native_methods']),3)
        self.assertFalse(value['source_work_qualified'])
        self.assertFalse(value['optimized_main_allocation_and_lifetime_proved'])

    def test_pi_capture_is_not_division_count(self):
        value = self.capture(self.fixture('pidigits'),'pidigits')
        self.assertFalse(value['runtime_pi_division_counts_proved'])

    def test_missing_bytes_rejected(self):
        root = self.fixture(); root.find('print_nmethod').text = 'main code [0x100,0x108] = 8\n[MachCode]\nImmutableOopMap {}\n[/MachCode]'
        with self.assertRaisesRegex(AssertionError,'instruction bytes'): self.capture(root)

    def test_missing_oopmap_rejected(self):
        root = self.fixture(); node = root.find('print_nmethod')
        node.text = node.text.replace('ImmutableOopMap','unrelated-map')
        with self.assertRaisesRegex(AssertionError,'OopMap'): self.capture(root)

    def test_missing_print_rejected(self):
        root = self.fixture(); root.remove(root.find('print_nmethod'))
        with self.assertRaisesRegex(AssertionError,'emitted native code'): self.capture(root)

    def test_partial_machine_range_rejected(self):
        root = self.fixture(); node = root.find('print_nmethod')
        node.text = node.text.replace(' aabbccdd 01020304',' aabbccdd')
        with self.assertRaisesRegex(AssertionError,'cover the main-code range'): self.capture(root)

    def test_overlapping_machine_bytes_rejected(self):
        root = self.fixture(); node = root.find('print_nmethod')
        node.text = node.text.replace('[/MachCode]','0x104: aabbccdd\n[/MachCode]')
        with self.assertRaisesRegex(AssertionError,'Overlapping'): self.capture(root)

    def test_missing_machine_end_rejected(self):
        root = self.fixture(); node = root.find('print_nmethod')
        node.text = node.text.replace('[/MachCode]','')
        with self.assertRaisesRegex(AssertionError,'boundaries'): self.capture(root)

    def test_duplicate_print_identity_rejected(self):
        root = self.fixture(); ET.SubElement(root,'print_nmethod',compile_id='1')
        with self.assertRaisesRegex(AssertionError,'duplicate'): self.capture(root)

    def test_wrong_main_descriptor_rejected(self):
        root = self.fixture(); root.find('nmethod').set('method','clbg.binarytrees.MainKt main ()V')
        with self.assertRaisesRegex(AssertionError,'JIT methods'): self.capture(root)

    def test_truncated_terminal_rejected(self):
        root = self.fixture(); root.remove(root.find('hotspot_log_done'))
        with self.assertRaisesRegex(AssertionError,'Incomplete'): self.capture(root)

    def test_nested_node_id_resolution_and_installation(self):
        root = self.fixture()
        for identity in ('1','999'):
            task = ET.SubElement(root,'task',compile_id=identity,method='clbg.binarytrees.MainKt main ([Ljava/lang/String;)V')
            parse = ET.SubElement(task,'parse')
            ET.SubElement(parse,'klass',id='90',name='clbg.binarytrees.Node')
            ET.SubElement(parse,'method',id='91',name='tree')
            node = ET.SubElement(task,'eliminate_allocation',type='90')
            ET.SubElement(node,'jvms',method='91',bci='16')
        values = self.capture(root)['node_allocation_eliminations']
        self.assertEqual([r['installed_nmethod'] for r in values],[True,False])
        self.assertEqual(values[0]['locations'],[{'method':'tree','bci':'16'}])

    def test_instruction_xml_escaping_preserved(self):
        root = self.fixture(); root.find('print_nmethod').text += '\n; <allocation> & literal\n'
        self.assertEqual(len(self.capture(root)['native_methods']),3)

    def test_exact_prescribed_outputs(self):
        self.assertEqual(len(m.expected_output('binarytrees')),455)
        self.assertEqual(len(m.expected_output('pidigits')),16893)

    def test_printing_only_preserves_original_policy(self):
        flags = m.options('pidigits',Path('/tmp/capture'))
        self.assertEqual(flags[:len(m.kb.FLAGS)],m.kb.FLAGS)
        self.assertIn('-XX:-DisplayVMOutput',flags)
        self.assertIn('-XX:CompileCommand=quiet',flags)
        self.assertFalse(any('Threshold' in x or 'dontinline' in x or 'compileonly' in x or 'EscapeAnalysis' in x for x in flags))
        self.assertNotIn('-XX:+PrintAssembly',flags)

    def test_unknown_class_owner_rejected(self):
        row = {'classes':'/tmp/classes','class_owner_names':['clbg.Support','clbg.binarytrees.MainKt'],
               'main_owner':'clbg.binarytrees.MainKt'}
        with self.assertRaisesRegex(AssertionError,'Unexpected subject owner'):
            m.validate_classes('[class,load] clbg.Uncounted source: file:/tmp/classes/',row,'/tmp/stdlib.jar')

    def test_direct_class_origins(self):
        row = {'classes':'/tmp/classes','class_owner_names':['clbg.Support','clbg.binarytrees.MainKt'],
               'main_owner':'clbg.binarytrees.MainKt'}
        text = '\n'.join('[class,load] '+n+' source: file:/tmp/classes/' for n in row['class_owner_names'])
        self.assertEqual(set(m.validate_classes(text,row,'/tmp/stdlib.jar')),set(row['class_owner_names']))

    def test_retained_warmup_log_has_no_machine_capture(self):
        path = m.WORK/'run-v2/kotlin-binarytrees-optimized/hotspot.xml'
        if not path.exists(): self.skipTest('Retained actual XML unavailable')
        with self.assertRaisesRegex(AssertionError,'emitted native code'):
            m.capture_index(path,'binarytrees')

    def test_rss_revision_is_isolated_and_only_policy_changes(self):
        self.assertEqual(m.kw.kb.RSS_LIMIT,2*1024**3)
        self.assertEqual(m.kb.RSS_LIMIT,10*1024**3)
        self.assertIsNot(m.kb,m.kw.kb)
        self.assertEqual(m.kb.observe.__code__.co_code,m.kw.kb.observe.__code__.co_code)
        for key in ('FLAGS','TIMEOUT','CLEANUP_TIMEOUT','FILE_LIMIT','PIPE_CHUNK','LOCK_INODE'):
            self.assertEqual(getattr(m.kb,key),getattr(m.kw.kb,key))

    def test_full_rss_bound_accepts_three_gib_and_rejects_excess(self):
        identity = dict(pid=123,pgid=123,ppid=1,birth_seconds=1,birth_microseconds=2,status=2)
        def monitor(module,rss,directory):
            kernel = SimpleNamespace(identity=lambda pid:identity,group=lambda pid:[identity],resident_bytes=lambda row:rss)
            record = dict(identity=identity,observed_peak_process_group_rss_bytes=0,kernel_monitor_samples=0)
            module.monitor(kernel,SimpleNamespace(pid=123),record,directory)
            return record
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            self.assertEqual(monitor(m.kb,3*1024**3,directory)['observed_peak_process_group_rss_bytes'],3*1024**3)
            self.assertEqual(monitor(m.kb,10*1024**3,directory)['kernel_monitor_samples'],1)
            with self.assertRaisesRegex(AssertionError,'RSS limit'): monitor(m.kb,10*1024**3+1,directory)
            with self.assertRaisesRegex(AssertionError,'RSS limit'): monitor(m.kw.kb,3*1024**3,directory)

    def failed_report(self):
        return dict(status='failed',active={'id':m.IDS[0]},profiles=[],commands={},
            native_processes_started=0,registered_native_commands=[],validated_command_artifacts={})

    def test_launch_failure_without_child_has_closed_terminal(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.kb.kh,'verify_lock'):
            output = Path(tmp); directory = output/m.IDS[0]; directory.mkdir()
            m.save(directory/'process.json',dict(kind='single-entry-work',native_process_started=False,
                direct_child_reaped=False,status='failed',cleanup_errors=[]))
            report = self.failed_report(); m.finish(report,{}, {},output,None)
            import json
            terminal = json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed')
            self.assertEqual(terminal['process_receipt_errors'],[])
            self.assertFalse(terminal['source_work_qualified'])

    def test_registered_child_without_saved_receipt_cannot_pass(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.kb.kh,'verify_lock'):
            output = Path(tmp); report = self.failed_report()
            report['native_processes_started'] = 1
            report['registered_native_commands'] = [dict(id=m.IDS[0],pid=123,pgid=123)]
            with self.assertRaisesRegex(AssertionError,'closure failed'): m.finish(report,{}, {},output,None)
            import json
            terminal = json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed-integrity-or-closure')
            self.assertTrue(terminal['process_receipt_errors'])

    def test_artifact_error_still_has_failed_terminal(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(m.kb.kh,'verify_lock'):
            output = Path(tmp); (output/'bad-link').symlink_to(output/'missing')
            with self.assertRaisesRegex(AssertionError,'closure failed'):
                m.finish(self.failed_report(),{}, {},output,None)
            import json
            terminal = json.loads((output/'terminal.json').read_bytes())
            self.assertEqual(terminal['status'],'failed-artifact-retention')
            self.assertTrue(terminal['artifact_errors'])


if __name__ == '__main__': unittest.main()
