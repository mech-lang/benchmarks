"""Authored pure tree-sidecar checks; execution remains pending."""
import importlib.util
from pathlib import Path
import unittest

PATH = Path(__file__).with_name('tree_contract.py')
SPEC = importlib.util.spec_from_file_location('rebol_tree_contract', PATH)
t = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(t)


def observed():
    return dict(t.EXACT, **{'recycles-before': 10, 'recycles-after': 12})


class TreeContract(unittest.TestCase):
    def test_exact_observation_keeps_qualification_separate(self):
        result = t.validate(t.EXPECTED_STDOUT, b'', 0, observed())
        self.assertTrue(result['observation_contract_satisfied'])
        for key in ('native_process_verified', 'runtime_source_equivalence_proven',
                    'full_size_work_qualified', 'source_work_qualified',
                    'per_tree_frees_observed', 'full_timing_qualified', 'chart_admission'):
            self.assertIs(result[key], False)

    def test_all_graph_and_identity_counts_are_required(self):
        for key in ('nodes-before', 'nodes-after', 'leaves-before', 'leaves-after',
                    'internal-before', 'internal-after', 'identity-pairs-before',
                    'identity-pairs-after', 'check-before', 'check-after'):
            value = observed()
            value[key] -= 1
            with self.subTest(key=key), self.assertRaises(ValueError):
                t.validate(t.EXPECTED_STDOUT, b'', 0, value)

    def test_collection_must_actually_advance_without_policy_change(self):
        for before, after in ((10, 10), (10, 9), (-1, 2), (False, 2), (1, True)):
            value = observed()
            value.update({'recycles-before': before, 'recycles-after': after})
            with self.assertRaises(ValueError):
                t.validate(t.EXPECTED_STDOUT, b'', 0, value)
        for key in ('manual-gc', 'gc-policy-changed', 'per-tree-frees-observed',
                    'source-work-qualified', 'chart-admission'):
            value = observed()
            value[key] = True
            with self.assertRaises(ValueError):
                t.validate(t.EXPECTED_STDOUT, b'', 0, value)

    def test_root_alias_and_leaf_mutation_observations_cannot_be_invented(self):
        for key in ('fresh-leaves-distinct', 'fresh-leaf-mutation-isolated', 'long-root-same'):
            value = observed()
            value[key] = False
            with self.assertRaises(ValueError):
                t.validate(t.EXPECTED_STDOUT, b'', 0, value)
        for key in ('diagnostic-root-aliases', 'diagnostic-node-lists-during-churn'):
            value = observed()
            value[key] += 1
            with self.assertRaises(ValueError):
                t.validate(t.EXPECTED_STDOUT, b'', 0, value)

    def test_streams_exit_types_and_exact_sidecar_fields(self):
        for stdout, stderr, status in ((t.EXPECTED_STDOUT + b'\n', b'', 0),
                                       (t.EXPECTED_STDOUT, b'warning\n', 0),
                                       (t.EXPECTED_STDOUT, b'', 1),
                                       (t.EXPECTED_STDOUT, b'', False)):
            with self.assertRaises(ValueError):
                t.validate(stdout, stderr, status, observed())
        for kind in ('missing', 'extra', 'boolean-count'):
            value = observed()
            if kind == 'missing':
                del value['main-n']
            elif kind == 'extra':
                value['inferred-freed-trees'] = 80
            else:
                value['diagnostic-root-aliases'] = True
            with self.assertRaises(ValueError):
                t.validate(t.EXPECTED_STDOUT, b'', 0, value)


if __name__ == '__main__':
    unittest.main()
