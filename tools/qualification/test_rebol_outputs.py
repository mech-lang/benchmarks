"""Pure proposed output-contract regressions; no Rebol process is launched."""
import hashlib
import importlib.util
import pathlib
import unittest

PATH = pathlib.Path(__file__).with_name('rebol_outputs.py')
SPEC = importlib.util.spec_from_file_location('rebol_output_adapter', PATH)
OUTPUTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OUTPUTS)


def success(benchmark, expected, method='exact-complete-bytes'):
    return dict(benchmark=benchmark, case='fixture', validation=method, expected_exit=0,
                expected=dict(bytes=len(expected), sha256=hashlib.sha256(expected).hexdigest()))


def rejection(name='extended-invalid-space', code=32):
    return dict(benchmark='revcomp', case=name, expected_exit='nonzero',
                validation='language-specific-invalid-iupac', expected_invalid_byte=code)


REJECTION_STDERR = b'\n** User error: Unsupported revcomp sequence byte\n\n'


class RebolOutputContracts(unittest.TestCase):
    def test_rebol_identity_complete_binary_bytes_and_no_admission(self):
        expected = b'P4\n9 1\n\xff\x80\x00'
        result = OUTPUTS.validate(success('mandelbrot', expected), expected, b'', 0, expected)
        self.assertEqual(result['language'], 'rebol')
        self.assertTrue(result['output_contract_satisfied'])
        for field in ('chart_admission', 'native_process_verified', 'source_work_qualified'):
            self.assertIs(result[field], False)
        self.assertEqual(result['stdout_sha256'], hashlib.sha256(expected).hexdigest())
        self.assertEqual(result['stdout_bytes'], len(expected))

    def test_complete_byte_contract_rejects_truncation_padding_and_newline(self):
        expected = b'P4\n9 1\n\xff\x80'
        for actual in (expected[:-1], expected[:-1] + b'\x81', expected + b'\n'):
            with self.subTest(actual=actual), self.assertRaises(ValueError):
                OUTPUTS.validate(success('mandelbrot', expected), actual, b'', 0, expected)

    def test_good_stdout_cannot_hide_stderr_exit_or_signal(self):
        expected = b'correct\n'
        for status, stderr in ((1, b''), (-9, b''), (0, b'warning\n'), (False, b'')):
            with self.subTest(status=status, stderr=stderr), self.assertRaises(ValueError):
                OUTPUTS.validate(success('fasta', expected), expected, stderr, status, expected)
        for stdout, stderr in (('correct\n', b''), (expected, '')):
            with self.assertRaises(ValueError):
                OUTPUTS.validate(success('fasta', expected), stdout, stderr, 0, expected)

    def test_altered_expected_cannot_validate_itself(self):
        case = success('fasta', b'old\n')
        with self.assertRaises(ValueError):
            OUTPUTS.validate(case, b'new\n', b'', 0, b'new\n')
        case['expected']['bytes'] = True
        with self.assertRaises(ValueError):
            OUTPUTS.validate(case, b'x', b'', 0, b'x')
        case = success('fasta', b'old\n')
        case['expected_exit'] = False
        with self.assertRaises(ValueError):
            OUTPUTS.validate(case, b'old\n', b'', 0, b'old\n')

    def test_nbody_both_lines_and_signed_nanounits(self):
        expected = b'-0.169075164\n-0.169087605\n'
        case = success('nbody', expected, 'finite-two-energy-lines-within-1e-8')
        result = OUTPUTS.validate(case, b'-0.169075160\n-0.169087600\n', b'', 0, expected)
        self.assertEqual(result['comparison'], 'signed-integer-nanounits')
        self.assertEqual(result['differences_nanounits'], [4, 5])
        self.assertEqual(result['maximum_difference_nanounits'], 10)
        for bad in (b'-0.169075164\n', expected + b'0.000000000\n',
                    b'nan\n-0.169087605\n', b'-0.169075164\n-0.169087500\n',
                    b'-0.16907516\n-0.16908760\n', expected.replace(b'\n', b'\r\n')):
            with self.subTest(actual=bad), self.assertRaises(ValueError):
                OUTPUTS.validate(case, bad, b'', 0, expected)

    def test_decimal_boundary_on_both_sides_and_across_zero(self):
        for reference, boundary, outside in (
                (b'-0.169016441', b'-0.169016451', b'-0.169016452'),
                (b'-0.169073022', b'-0.169073012', b'-0.169073011'),
                (b'-0.000000005', b'0.000000005', b'0.000000006'),
                (b'0.000000005', b'-0.000000005', b'-0.000000006')):
            expected = b'-0.169075164\n' + reference + b'\n'
            case = success('nbody', expected, 'finite-two-energy-lines-within-1e-8')
            result = OUTPUTS.validate(case, b'-0.169075164\n' + boundary + b'\n', b'', 0, expected)
            self.assertEqual(result['differences_nanounits'], [0, 10])
            with self.assertRaises(ValueError):
                OUTPUTS.validate(case, b'-0.169075164\n' + outside + b'\n', b'', 0, expected)

    def test_nonfinite_decimal_and_malformed_reference_rejected(self):
        for expected in (b'1.0\n2.0\n', b'9' * 400 + b'.000000000\n0.000000000\n'):
            case = success('nbody', expected, 'finite-two-energy-lines-within-1e-8')
            with self.assertRaises(ValueError):
                OUTPUTS.validate(case, expected, b'', 0, expected)

    def test_validation_method_cannot_be_substituted(self):
        expected = b'1.000000000\n2.000000000\n'
        for benchmark, method in (('fasta', 'finite-two-energy-lines-within-1e-8'),
                                  ('nbody', 'exact-complete-bytes'), ('fasta', 'unknown')):
            with self.subTest(benchmark=benchmark, method=method), self.assertRaises(ValueError):
                OUTPUTS.validate(success(benchmark, expected, method), expected, b'', 0, expected)

    def test_all_seven_source_defined_rejections_and_oracle_metadata(self):
        for name, code in (('extended-invalid-space', 32), ('extended-invalid-tab', 9),
                           ('extended-invalid-nul', 0), ('extended-invalid-high-byte', 255),
                           ('extended-inline-header-marker', 62),
                           ('extended-inline-comment-marker', 59),
                           ('extended-invalid-reverse-order', 63)):
            result = OUTPUTS.validate(rejection(name, code), b'', REJECTION_STDERR, 1, None)
            self.assertEqual(result['language'], 'rebol')
            self.assertEqual(result['expected_invalid_byte'], code)
            self.assertIs(result['invalid_byte_emitted'], False)
            self.assertIs(result['native_rejection_prequalified'], False)
            self.assertEqual(result['rejection_policy_basis'], 'retained-source')
            self.assertTrue(result['output_contract_satisfied'])
            for field in ('chart_admission', 'native_process_verified', 'source_work_qualified'):
                self.assertIs(result[field], False)

    def test_rejection_requires_native_exit_one_and_no_partial_stdout(self):
        for status, stdout in ((0, b''), (-9, b''), (2, b''), (True, b''),
                               (1, b'>r\n'), (1, b'\n')):
            with self.subTest(status=status, stdout=stdout), self.assertRaises(ValueError):
                OUTPUTS.validate(rejection(), stdout, REJECTION_STDERR, status, None)

    def test_generic_failures_and_diagnostic_suffixes_do_not_pass(self):
        for stderr in (b'', b'Unsupported revcomp sequence byte\n',
                       b'Invalid IUPAC byte: 32\n',
                       REJECTION_STDERR.replace(b'User', b'user'),
                       REJECTION_STDERR.replace(b'Unsupported revcomp sequence byte', b'Unknown command'),
                       REJECTION_STDERR.replace(b'\n', b'\r\n'),
                       REJECTION_STDERR[:-1], REJECTION_STDERR + b'\n',
                       b'warning\n' + REJECTION_STDERR,
                       REJECTION_STDERR[:-1] + b'** Where: fail emit-record\n\n',
                       REJECTION_STDERR[:-1] + b'** Near: do make error! message\n\n',
                       REJECTION_STDERR + b'Closing in 3s!\n'):
            with self.subTest(stderr=stderr), self.assertRaises(ValueError):
                OUTPUTS.validate(rejection(), b'', stderr, 1, None)

    def test_malformed_rejection_contract_rejected(self):
        for update in ({'benchmark': 'fasta'}, {'expected_exit': 1},
                       {'expected_invalid_byte': True}, {'expected_invalid_byte': -1},
                       {'expected_invalid_byte': 256}, {'expected': {}}):
            case = rejection()
            case.update(update)
            with self.subTest(update=update), self.assertRaises(ValueError):
                OUTPUTS.validate(case, b'', REJECTION_STDERR, 1, None)
        with self.assertRaises(ValueError):
            OUTPUTS.validate(rejection(), b'', REJECTION_STDERR, 1, b'')


if __name__ == '__main__':
    unittest.main()
