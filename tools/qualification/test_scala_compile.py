"""Pure negative checks; never load the observer or invoke a compiler/JVM."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('scala_compile_tested', HERE/'scala_compile.py')
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)


class SourceContracts(unittest.TestCase):
    def setUp(self):
        self.sources = json.loads(subject.SOURCES.read_bytes())

    def test_actual_ten_sources(self):
        rows = subject.source_rows(self.sources)
        self.assertEqual(len(rows), 10)

    def test_duplicate_workload(self):
        self.sources['programs'][-1] = copy.deepcopy(self.sources['programs'][0])
        with self.assertRaises(AssertionError):
            subject.source_rows(self.sources)

    def test_redirected_application(self):
        self.sources['programs'][0]['sources'][0]['path'] = '/tmp/borrowed/Main.scala'
        with self.assertRaises(AssertionError):
            subject.source_rows(self.sources)

    def test_omitted_source_helper(self):
        self.sources['programs'][0]['sources'].append(copy.deepcopy(self.sources['programs'][0]['sources'][0]))
        with self.assertRaises(AssertionError):
            subject.source_rows(self.sources)

    def test_runtime_does_not_include_compiler(self):
        toolchain = json.loads(subject.TOOLCHAIN.read_bytes())
        jars = subject.runtime_jars(toolchain['compiler_dependencies'])
        self.assertEqual({p.name for p in jars}, {'scala3-library_3-3.10.0.jar', 'scala-library-3.10.0.jar'})

    def test_ambiguous_runtime(self):
        paths = ['/a/scala3-library_3-3.10.0.jar', '/a/scala-library-3.10.0.jar',
                 '/b/scala-library-3.10.0.jar']
        with self.assertRaises(AssertionError):
            subject.runtime_jars(paths)


class OutputInventory(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        for name in ('Main.class', 'Main$.class'):
            (self.directory/name).write_bytes(b'\xca\xfe\xba\xbe'+b'\x00'*6)
        (self.directory/'Main.tasty').write_bytes(b'fixture')

    def test_complete_inventory(self):
        self.assertEqual(len(subject.class_inventory(self.directory)), 3)

    def test_missing_module(self):
        (self.directory/'Main$.class').unlink()
        with self.assertRaises(AssertionError):
            subject.class_inventory(self.directory)

    def test_linked_module(self):
        (self.directory/'Main$.class').unlink()
        (self.directory/'Main$.class').symlink_to(self.directory/'Main.class')
        with self.assertRaises(AssertionError):
            subject.class_inventory(self.directory)

    def test_unexpected_generated_source(self):
        (self.directory/'Other.scala').write_text('object Other')
        with self.assertRaises(AssertionError):
            subject.class_inventory(self.directory)

    def test_corrupt_class(self):
        (self.directory/'Main.class').write_bytes(b'not a JVM class')
        with self.assertRaises(AssertionError):
            subject.class_inventory(self.directory)

    def test_final_inventory_cannot_adopt_changed_receipt(self):
        receipt = self.directory/'receipt.json'
        receipt.write_text('{}')
        saved = {str(receipt): subject.sha(receipt)}
        receipt.write_text('{"changed":true}')
        with self.assertRaises(AssertionError):
            subject.close_artifact_inventory(self.directory, subject.artifact_inventory(self.directory),
                                             {}, saved, [])

    def test_final_inventory_rejects_added_class(self):
        profiles = [dict(source=str(self.directory/'Main.scala'), artifacts=subject.class_inventory(self.directory))]
        # The real packet places classes beneath each application directory.
        classes = self.directory/'classes'
        classes.mkdir()
        for item in profiles[0]['artifacts']:
            old = Path(item['path'])
            old.rename(classes/old.name)
        profiles[0]['artifacts'] = subject.class_inventory(classes)
        (classes/'Added.class').write_bytes(b'\xca\xfe\xba\xbe'+b'\x00'*6)
        with self.assertRaises(AssertionError):
            subject.close_artifact_inventory(self.directory, subject.artifact_inventory(self.directory),
                                             {}, {}, profiles)

    def test_final_inventory_rejects_symlink(self):
        (self.directory/'linked').symlink_to(self.directory/'Main.class')
        with self.assertRaises(AssertionError):
            subject.artifact_inventory(self.directory)


class NativeClosure(unittest.TestCase):
    def setUp(self):
        self.path = subject.BASE/'toolchain-v1/native-v1/compile-frozen/process.json'
        self.record = json.loads(self.path.read_bytes())
        self.command = self.record['command']
        self.environment = self.record['environment']
        self.directory = Path(self.record['cwd'])

    def check(self):
        subject.closed_process(self.record, self.command, self.environment, self.directory)

    def test_saved_actual_native_closure(self):
        self.check()

    def test_unreaped_child(self):
        self.record['direct_child_reaped'] = False
        with self.assertRaises(AssertionError): self.check()

    def test_remaining_descendant(self):
        self.record['remaining_process_group'] = [dict(pid=123)]
        with self.assertRaises(AssertionError): self.check()

    def test_wrong_executable(self):
        self.command = ['unexpected']+self.command[1:]
        with self.assertRaises(AssertionError): self.check()

    def test_changed_common_mutex(self):
        self.record['common_mutex_inode'] += 1
        with self.assertRaises(AssertionError): self.check()

    def test_failed_exit(self):
        self.record['exit_status'] = 1
        with self.assertRaises(AssertionError): self.check()


if __name__ == '__main__':
    unittest.main()
