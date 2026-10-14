"""Deterministic retained publication bytes and inherited transaction faults."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest


HERE = Path(__file__).parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE/filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


a = load('retained_target_v2_tested', 'import_retained_publication_target_v2.py')
prior = load('retained_target_transaction_tests', 'test_import_retained_publication_target.py')
prior.a = a


class Transactions(prior.Transactions):
    def setUp(self):
        super().setUp()
        self.before['archive_paths'] = {'existing-z': 'existing-z', 'existing-a': 'existing-a'}
        (self.publication/prior.OLD.CATALOGS[0]).write_bytes(prior.OLD.encoded(self.before))


class PublicationLinks(prior.PublicationLinks):
    pass


class OriginalSource(prior.OriginalSource):
    pass


class Ordering(unittest.TestCase):
    def test_only_new_key_order_changes(self):
        before = {'archive_paths': {'old-z': 'target-z', 'old-a': 'target-a'}}
        data = {'archive_paths': {'new-z': 'new-z', 'old-a': 'target-a',
                                 'new-a': 'new-a', 'old-z': 'target-z'},
                'programs': {'exact': {'samples': [1.0, 2.0, 3.0]}}}
        original_before, original_data = copy.deepcopy(before), copy.deepcopy(data)
        a.order_new_archive_paths(before, data)
        self.assertEqual(before, original_before)
        self.assertEqual(data, original_data)
        self.assertEqual(list(data['archive_paths']), ['old-z', 'old-a', 'new-a', 'new-z'])
        a.order_new_archive_paths(before, data)
        self.assertEqual(list(data['archive_paths']), ['old-z', 'old-a', 'new-a', 'new-z'])

    def test_existing_mapping_change_or_removal_is_rejected(self):
        before = {'archive_paths': {'old': 'target'}}
        for current in ({}, {'old': 'changed'}):
            with self.subTest(current=current), self.assertRaisesRegex(ValueError, 'Existing archive'):
                a.order_new_archive_paths(before, {'archive_paths': current})

    def test_actual_retained_r_transform_is_identical_across_process_hash_seeds(self):
        # Separate pure Python interpreters intentionally omit -I so each fixed
        # PYTHONHASHSEED exercises the original set iteration. No native subject,
        # runtime inventory, current catalog or evidence file phase is executed.
        script = r'''
import hashlib, importlib.util, json
from pathlib import Path
here = Path(HERE_LITERAL)
def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, here/filename)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
a = load('retained_target_v2', 'import_retained_publication_target_v2.py')
fixtures = load('retained_catalog_fixtures', 'test_retained_catalog_publication.py')
r = load('retained_r_fixture', 'test_r_retained_export.py')
r.Candidate.setUpClass()
candidate = r.e.build_candidate(r.Candidate.review, r.Candidate.sources, r.t.r)
before, metadata = fixtures.catalog(candidate)
before['archive_paths'] = {'existing-z': 'existing-z', 'existing-a': 'existing-a'}
after, metadata, audit = fixtures.p.build_publication(before, metadata, candidate,
    {'path': 'experiments/r/synthetic-candidate.json', 'sha256': 'a'*64})
encoded = lambda value: (json.dumps(value, indent=2, ensure_ascii=False)+'\n').encode()
original = encoded(after)
a.order_new_archive_paths(before, after)
assert json.loads(original) == after
assert list(after['archive_paths'])[:2] == ['existing-z', 'existing-a']
print(json.dumps({'original': hashlib.sha256(original).hexdigest(),
                  'stable': hashlib.sha256(encoded(after)).hexdigest(),
                  'metadata': hashlib.sha256(encoded(metadata)).hexdigest(),
                  'audit': hashlib.sha256(encoded(audit)).hexdigest()}))
'''.replace('HERE_LITERAL', repr(str(HERE.resolve())))
        results = []
        for seed in ('1', '2', '3'):
            result = subprocess.run([sys.executable, '-S', '-B', '-c', script],
                env={'PYTHONHASHSEED': seed}, cwd='/private/tmp', capture_output=True,
                check=True, timeout=10)
            self.assertEqual(result.stderr, b'')
            results.append(json.loads(result.stdout))
        self.assertGreater(len({row['original'] for row in results}), 1,
                           'Regression did not reproduce original set-order divergence')
        for field in ('stable', 'metadata', 'audit'):
            self.assertEqual(len({row[field] for row in results}), 1, field)


if __name__ == '__main__':
    unittest.main()
