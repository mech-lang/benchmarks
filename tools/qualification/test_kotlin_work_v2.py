"""Pure proxy-origin fixtures plus the unchanged compiled-work fixture suite.

No JVM, host kernel observation, runtime hashing, or saved-run mutation.
"""
import ast
import hashlib
import importlib.util
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE/filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


work = load('kotlin_work_v2_review', 'kotlin_work_v2.py')
original_tests = load('kotlin_work_original_tests', 'test_kotlin_work.py')
original_tests.work = work


class ProxyOriginTests(unittest.TestCase):
    factories = ('java.lang.reflect.Proxy', 'java.lang.reflect.Proxy$ProxyBuilder',
                 'java.lang.reflect.ProxyGenerator')

    def setUp(self):
        self.classes = Path('/tmp/kotlin-proxy-fixture/subject').resolve()
        self.stdlib = Path('/tmp/kotlin-proxy-fixture/stdlib.jar').resolve()
        self.probe = Path('/tmp/kotlin-proxy-fixture/probe').resolve()
        self.owners = {'clbg.Support', 'clbg.binarytrees.MainKt'}
        self.base = [('boundedqualification.WorkProbe', self.probe.as_uri()),
                     ('boundedqualification.BoundedProbe', self.probe.as_uri()),
                     ('clbg.Support', self.classes.as_uri()),
                     ('clbg.binarytrees.MainKt', self.classes.as_uri())]

    def rows(self, origin='jrt:/java.base'):
        return self.base + [(name, origin) for name in self.factories]

    def validate(self, rows):
        text = '\n'.join('[0.1s][class,load] '+owner+' source: '+source
                         for owner, source in rows)
        return work.validate_log(text, self.classes, self.stdlib, self.probe, self.owners)

    def test_exact_generated_proxies_preserve_their_observed_marker(self):
        proxies = [('jdk.proxy1.$Proxy0', '__dynamic_proxy__'),
                   ('jdk.proxy12.$Proxy37', '__dynamic_proxy__')]
        result = self.validate(self.rows()+proxies)
        self.assertEqual({name: result[name] for name, _ in proxies}, dict(proxies))
        self.assertEqual(result['boundedqualification.WorkProbe'], self.probe.as_uri())

    def test_factories_from_existing_shared_archive_origin_are_accepted(self):
        for origin in ('shared objects file', 'shared objects file (top)'):
            with self.subTest(origin=origin):
                self.validate(self.rows(origin)+[('jdk.proxy1.$Proxy0', '__dynamic_proxy__')])

    def test_wrong_namespace_or_generated_name_is_rejected(self):
        for owner in ('clbg.binarytrees.MainKt', 'kotlin.Proxy', 'boundedqualification.WorkProbe',
                      'jdk.proxy0.$Proxy0', 'jdk.proxy01.$Proxy0', 'jdk.proxy1.$Proxy00',
                      'jdk.proxy1.Proxy0', 'jdk.proxy1.$Proxy0$Extra', 'jdk.other.$Proxy0',
                      'com.sun.proxy.jdk.proxy1.$Proxy0'):
            with self.subTest(owner=owner), self.assertRaisesRegex(AssertionError, 'Unexpected generated proxy owner'):
                self.validate(self.rows()+[(owner, '__dynamic_proxy__')])

    def test_wrong_generation_marker_is_not_exempted(self):
        for marker in ('__dynamic_proxy__extra', '__unknown_generated__'):
            with self.subTest(marker=marker), self.assertRaisesRegex(AssertionError, 'Unknown class origin'):
                self.validate(self.rows()+[('jdk.proxy1.$Proxy0', marker)])

    def test_each_factory_must_have_been_observed(self):
        for absent in self.factories:
            rows = [row for row in self.rows() if row[0] != absent]
            with self.subTest(absent=absent), self.assertRaisesRegex(AssertionError, 'prior trusted java.base factories'):
                self.validate(rows+[('jdk.proxy1.$Proxy0', '__dynamic_proxy__')])

    def test_factory_records_after_proxy_do_not_supply_prior_evidence(self):
        with self.assertRaisesRegex(AssertionError, 'prior trusted java.base factories'):
            self.validate(self.base+[('jdk.proxy1.$Proxy0', '__dynamic_proxy__')]+
                          [(name, 'jrt:/java.base') for name in self.factories])

    def test_factory_from_another_origin_is_rejected(self):
        for origin in ('jrt:/java.management', 'file:/tmp/foreign.jar', '__dynamic_proxy__'):
            rows = self.rows()
            rows[-1] = (self.factories[-1], origin)
            with self.subTest(origin=origin), self.assertRaises(AssertionError):
                self.validate(rows+[('jdk.proxy1.$Proxy0', '__dynamic_proxy__')])

    def test_other_unknown_origins_remain_rejected(self):
        with self.assertRaisesRegex(AssertionError, 'Unknown class origin'):
            self.validate(self.rows()+[('jdk.proxy1.$Proxy0', '__dynamic_proxy__'),
                                       ('jdk.unexpected.Owner', '__unknown_generated__')])

    def test_subject_file_origin_is_still_checked(self):
        rows = self.rows()+[('jdk.proxy1.$Proxy0', '__dynamic_proxy__'),
                            ('clbg.binarytrees.MainKt', self.probe.as_uri())]
        with self.assertRaisesRegex(AssertionError, 'Unexpected non-platform class origin'):
            self.validate(rows)

    def test_only_class_log_validator_changed_and_original_is_frozen(self):
        original = (HERE/'kotlin_work.py').read_bytes()
        self.assertEqual(hashlib.sha256(original).hexdigest(),
                         'c7f801c2b658262bf522f7bde1370cab607863a4c9b8ca8ddbdd1e8d95f03e3e')
        trees = [ast.parse(raw) for raw in (original, (HERE/'kotlin_work_v2.py').read_bytes())]
        for tree in trees:
            method = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'validate_log')
            method.body = [ast.Pass()]
        self.assertEqual(ast.dump(trees[0]), ast.dump(trees[1]))


if __name__ == '__main__':
    suite = unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromModule(original_tests),
                              unittest.defaultTestLoader.loadTestsFromTestCase(ProxyOriginTests)])
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    raise SystemExit(not result.wasSuccessful())
