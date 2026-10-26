"""Fail-closed archive, executable, and exact test selection contracts."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("native_probe_runner", HERE / "run.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class ProbeRunnerTests(unittest.TestCase):
    def test_removed_probe_is_installed_once_with_local_imports(self):
        spec = json.loads((HERE / "probes.json").read_text())["probes"]["window-kernel"]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / spec["target_file"]
            target.parent.mkdir(parents=True)
            target.write_text("// Existing correctness support remains here.\n")
            report = runner.install_probe(root, "window-kernel", spec)
            self.assertEqual(report["mode"], "test-overlay")
            self.assertTrue(target.read_text().startswith("// Existing correctness support remains here."))
            self.assertIn("use std::{hint::black_box, time::Instant};", target.read_text())
            # A second install cannot silently accept a body different from the archive.
            with self.assertRaisesRegex(ValueError, "differs from the archived"):
                runner.install_probe(root, "window-kernel", spec)

    def test_original_is_preserved_and_changed_existing_probe_is_rejected(self):
        spec = json.loads((HERE / "probes.json").read_text())["probes"]["window-region"]
        original = (HERE / "probes/window-region.rs").read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / spec["target_file"]
            target.parent.mkdir(parents=True)
            target.write_bytes(original)
            report = runner.install_probe(root, "window-region", spec)
            self.assertEqual(report["mode"], "existing-identical")
            self.assertEqual(target.read_bytes(), original)
            target.write_bytes(original.replace(b"collections.len(), 1", b"collections.len(), 2"))
            with self.assertRaisesRegex(ValueError, "differs from the archived"):
                runner.install_probe(root, "window-region", spec)

    def test_exact_ignored_selection_rejects_zero_and_multiple_tests(self):
        runner.validate_selection("module::probe: test\n", "module::probe")
        for output in ("", "module::other: test\n", "module::probe: test\nmodule::other: test\n"):
            with self.assertRaises(ValueError):
                runner.validate_selection(output, "module::probe")

    def test_result_requires_one_named_pass(self):
        runner.validate_result("test module::probe ... ok\n\ntest result: ok. 1 passed; 0 failed; 0 ignored;\n", "module::probe")
        for output in ("test result: ok. 0 passed; 0 failed; 0 ignored;\n",
                       "test module::other ... ok\n\ntest result: ok. 1 passed; 0 failed; 0 ignored;\n"):
            with self.assertRaises(ValueError):
                runner.validate_result(output, "module::probe")

    def test_cargo_artifact_selection_rejects_wrong_target_and_ambiguity(self):
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "native-test"
            executable.touch()
            artifact = {"reason": "compiler-artifact", "profile": {"test": True},
                        "target": {"name": "mech_gpu", "kind": ["lib"]}, "executable": str(executable)}
            output = json.dumps(artifact)
            self.assertEqual(runner.selected_executable(output, "lib"), executable)
            with self.assertRaises(ValueError):
                runner.selected_executable(output, "canonical_artifact_program")
            artifact["executable"] += "-other"
            with self.assertRaises(ValueError):
                runner.selected_executable(output + "\n" + json.dumps(artifact), "lib")


if __name__ == "__main__":
    unittest.main()
