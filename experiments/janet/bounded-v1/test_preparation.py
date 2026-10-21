"""Corruption and boundary tests for preparation; no Janet/native child starts."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('janet_bounded_outputs', HERE / 'outputs.py')
OUTPUTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OUTPUTS)


def case(expected, benchmark='mandelbrot', method='exact-complete-bytes'):
    return dict(benchmark=benchmark, case='fixture', validation=method, expected_exit=0,
                expected=dict(bytes=len(expected), sha256=hashlib.sha256(expected).hexdigest()))


class Contracts(unittest.TestCase):
    def test_binary_padding_truncation_and_extra_output(self):
        expected = b'P4\n9 1\n\xff\x80'
        row = case(expected)
        result = OUTPUTS.validate_success(row, expected, b'', 0, expected)
        self.assertTrue(result['output_contract_satisfied'])
        for key in ('chart_admission', 'native_process_verified', 'source_work_qualified'):
            self.assertFalse(result[key])
        for actual in (expected[:-1], expected[:-1] + b'\x81', expected + b'\n'):
            with self.assertRaises(ValueError):
                OUTPUTS.validate_success(row, actual, b'', 0, expected)

    def test_exit_signal_diagnostics_or_boolean_status_cannot_pass(self):
        expected = b'correct\n'
        for status, stderr in ((1, b''), (-9, b''), (False, b''), (0, b'diagnostic\n')):
            with self.assertRaises(ValueError):
                OUTPUTS.validate_success(case(expected), expected, stderr, status, expected)

    def test_corrupt_expected_pin_cannot_validate_itself(self):
        expected = b'old\n'
        with self.assertRaises(ValueError):
            OUTPUTS.validate_success(case(expected), b'new\n', b'', 0, b'new\n')
        row = case(expected)
        row['expected']['bytes'] += 1
        with self.assertRaises(ValueError):
            OUTPUTS.validate_success(row, expected, b'', 0, expected)

    def test_exact_nbody_decimal_boundary_and_both_lines(self):
        expected = b'-0.169075164\n-0.169016441\n'
        row = case(expected, 'nbody', 'finite-two-energy-lines-within-1e-8')
        boundary = b'-0.169075154\n-0.169016451\n'
        self.assertEqual(OUTPUTS.validate_success(row, boundary, b'', 0, expected)
                         ['differences_nanounits'], [10, 10])
        for actual in (boundary.replace(b'451', b'452'), b'-0.169075164\n',
                       expected + b'0.000000000\n', b'nan\n-0.169016441\n',
                       b'-0.16907516\n-0.16901644\n'):
            with self.assertRaises(ValueError):
                OUTPUTS.validate_success(row, actual, b'', 0, expected)

    def test_wrong_method_and_language_rejections_fail_closed(self):
        expected = b'1.000000000\n2.000000000\n'
        for bench, method in (('fasta', 'finite-two-energy-lines-within-1e-8'),
                              ('nbody', 'exact-complete-bytes'), ('fasta', 'unknown')):
            with self.assertRaises(ValueError):
                OUTPUTS.validate_success(case(expected, bench, method), expected, b'', 0, expected)
        row = dict(benchmark='revcomp', case='bad', expected_exit='nonzero',
                   validation='language-specific-invalid-iupac', expected_invalid_byte=32)
        for status in (0, 1, -9):
            with self.assertRaises(ValueError):
                OUTPUTS.validate_success(row, b'>r\n', b'Invalid IUPAC nucleotide\n', status, None)

    def test_every_shared_success_reference_and_nbody_mutation(self):
        import json
        corpus = HERE.parents[1] / 'shared/bounded-corpus-v1/cases/manifest.json'
        manifest = json.loads(corpus.read_bytes())
        successes = 0
        for row in manifest['cases']:
            if type(row['expected_exit']) is not int:
                continue
            expected = (corpus.parent / row['expected']['path']).read_bytes()
            self.assertTrue(OUTPUTS.validate_success(row, expected, b'', 0, expected)
                            ['output_contract_satisfied'])
            successes += 1
            if row['benchmark'] == 'nbody':
                mutated = copy.deepcopy(row)
                mutated['validation'] = 'exact-complete-bytes'
                with self.assertRaises(ValueError):
                    OUTPUTS.validate_success(mutated, expected, b'', 0, expected)
        self.assertEqual(successes, 142)


if __name__ == '__main__':
    unittest.main()
