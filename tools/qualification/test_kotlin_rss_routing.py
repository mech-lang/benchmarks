"""Pure dependency/prerequisite regressions for the RSS observer revision.

Only small controller sources and synthetic metadata are read. No native
process, runtime closure, prepared plan or execution receipt is modified.
"""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
V2_SHA = 'c525b0dd6784a52a4cfa583e687abf3b12454a9304d222f18cf4e9005693d0bc'
OLD_SHA = '916a94f68e191cce8d074121859121351517c8ab2132bb5953ebc62621ba710e'


def load(name):
    path = HERE/(name+'.py')
    spec = importlib.util.spec_from_file_location('rss_routing_'+name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module


class RoutingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with patch.object(subprocess, 'Popen', side_effect=AssertionError('Native launch forbidden')):
            cls.supplement = load('kotlin_supplement')
            cls.work = load('kotlin_work')
            cls.reader = load('kotlin_loc')
            cls.elixir = load('elixir_work')
            cls.units = load('kotlin_source_units')

    def test_all_native_consumers_load_the_exact_repaired_observer(self):
        with patch.object(subprocess, 'Popen', side_effect=AssertionError('Native launch forbidden')):
            observers = [self.supplement.kb, self.work.kb,
                         self.reader.module(), self.elixir.load_supervisor()]
        for observer in observers:
            with self.subTest(module=observer.__name__):
                self.assertEqual(Path(observer.__file__), HERE/'kotlin_bounded_v2.py')
                self.assertEqual(hashlib.sha256(Path(observer.__file__).read_bytes()).hexdigest(), V2_SHA)
                self.assertEqual((observer.TIMEOUT, observer.CLEANUP_TIMEOUT), (30, 5))
                self.assertEqual((observer.RSS_LIMIT, observer.FILE_LIMIT), (2*1024**3, 8*1024**2))
        self.assertEqual(hashlib.sha256((HERE/'kotlin_bounded.py').read_bytes()).hexdigest(), OLD_SHA)

    def test_observer_loaders_reject_wrong_source_pins(self):
        with self.assertRaisesRegex(AssertionError, 'Reviewed module changed'):
            self.supplement.module(HERE/'kotlin_bounded_v2.py', OLD_SHA, 'wrong_observer')
        for module, name, loader in ((self.work, 'BOUNDED_CONTROLLER_SHA', self.work.load_bounded),
                                    (self.reader, 'SUPERVISOR_SHA', self.reader.module),
                                    (self.elixir, 'SUPERVISOR_SHA', self.elixir.load_supervisor)):
            with self.subTest(module=module.__name__), patch.object(module, name, OLD_SHA):
                with self.assertRaises((AssertionError, ValueError)):
                    loader()

    def test_both_output_consumers_require_a_v2_bounded_plan(self):
        class PassedControllerGate(Exception):
            pass

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = SimpleNamespace(plan=root/'plan.json', output=root/'output',
                bounded_report=root/'report.json', bounded_report_sha256='report',
                bounded_terminal_sha256='terminal')
            report = dict(plan='bounded-plan', plan_sha256='plan', profiles=[])
            for module, validator in ((self.supplement, 'validate_bounded'),
                                      (self.work, 'validate_prerequisite')):
                for digest in (OLD_SHA, V2_SHA):
                    bounded = dict(schema='kotlin-retained-classes-bounded-plan-v1',
                                   controller_sha256=digest, profiles=[])
                    with self.subTest(module=module.__name__, digest=digest), \
                         patch.object(module, 'read', side_effect=[report, {}, bounded]), \
                         patch.object(module, validator), \
                         patch.object(module.kb, 'bounded_schedule', side_effect=PassedControllerGate):
                        if digest == OLD_SHA:
                            with self.assertRaisesRegex(AssertionError, 'Wrong completed bounded plan'):
                                module.prepare(args)
                        else:
                            with self.assertRaises(PassedControllerGate):
                                module.prepare(args)
            self.assertEqual(list(root.iterdir()), [])

    def test_failed_monitor_attempt_cannot_satisfy_output_prerequisites(self):
        report = dict(schema='kotlin-retained-classes-bounded-results-v1', status='failed')
        for validator in (self.supplement.validate_bounded, self.work.validate_prerequisite):
            with self.subTest(validator=validator.__name__), self.assertRaisesRegex(AssertionError, 'prerequisite'):
                validator(report, dict(status='failed'), 'failed-report')

    def test_transitive_pins_bind_the_updated_supplement_and_pure_psi_validator(self):
        self.assertEqual(hashlib.sha256((HERE/'kotlin_supplement.py').read_bytes()).hexdigest(),
                         self.work.SUPPLEMENT_CONTROLLER_SHA)
        self.assertEqual(hashlib.sha256((HERE/'kotlin_loc_v3.py').read_bytes()).hexdigest(),
                         self.units.READER_VALIDATOR_SHA256)
        self.units.reader_validator.cache_clear()
        with patch.object(subprocess, 'Popen', side_effect=AssertionError('Native launch forbidden')):
            validator = self.units.reader_validator()
        self.assertEqual(validator.__name__, 'validate_psi')
        self.assertEqual(Path(validator.__code__.co_filename), HERE/'kotlin_loc_v3.py')

    def test_source_units_reject_a_changed_reader_before_loading_definitions(self):
        self.units.reader_validator.cache_clear()
        with patch.object(self.units, 'READER_VALIDATOR_SHA256', '0'*64):
            with self.assertRaisesRegex(self.units.CountError, 'validator bytes differ'):
                self.units.reader_validator()
        self.units.reader_validator.cache_clear()


if __name__ == '__main__':
    unittest.main()
