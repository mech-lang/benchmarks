"""Pure positive/negative tests; no Scala, Node or benchmark process starts."""
import hashlib
import importlib.util
import pathlib
import unittest

PATH = pathlib.Path(__file__).with_name('scala_typescript_outputs.py')
SPEC = importlib.util.spec_from_file_location('bounded_output_adapters', PATH)
OUTPUTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(OUTPUTS)


def success(benchmark, expected, method='exact-complete-bytes'):
    return dict(benchmark=benchmark, case='fixture', validation=method, expected_exit=0,
                expected=dict(bytes=len(expected), sha256=hashlib.sha256(expected).hexdigest()))


def rejection(code):
    return dict(benchmark='revcomp', case='extended-invalid', expected_exit='nonzero',
                validation='language-specific-invalid-iupac', expected_invalid_byte=code)


def scala_error(code):
    return (f'Exception in thread "main" java.lang.IllegalArgumentException: '
            f'requirement failed: Invalid IUPAC byte: {code}\n'
            '\tat scala.Predef$.require(Predef.scala:337)\n'
            '\tat Main$.emit$1(Main.scala:31)\n'
            '\tat Main$.main(Main.scala:56)\n'
            '\tat Main.main(Main.scala)\n').encode('ascii')


class OutputContracts(unittest.TestCase):
    def test_complete_binary_output_and_no_admission(self):
        expected = b'P4\n9 1\n\xff\x80'
        for language in OUTPUTS.LANGUAGES:
            result = OUTPUTS.validate(success('mandelbrot', expected), language, expected, b'', 0, expected)
            self.assertTrue(result['output_contract_satisfied'])
            self.assertFalse(result['chart_admission'])
            self.assertFalse(result['native_process_verified'])
            self.assertFalse(result['source_work_qualified'])

    def test_truncation_padding_and_extra_newline_fail(self):
        expected = b'P4\n9 1\n\xff\x80'
        for actual in [expected[:-1], expected[:-1]+b'\x81', expected+b'\n']:
            with self.assertRaises(ValueError):
                OUTPUTS.validate(success('mandelbrot', expected), 'scala', actual, b'', 0, expected)

    def test_failed_process_or_stderr_cannot_pass_good_stdout(self):
        expected = b'correct\n'
        for status, stderr in [(1,b''),(-9,b''),(0,b'warning\n'),(False,b'')]:
            with self.assertRaises(ValueError):
                OUTPUTS.validate(success('fasta', expected), 'typescript', expected, stderr, status, expected)

    def test_changed_expected_bytes_cannot_validate_themselves(self):
        case = success('fasta', b'old\n')
        with self.assertRaises(ValueError):
            OUTPUTS.validate(case, 'scala', b'new\n', b'', 0, b'new\n')

    def test_nbody_retains_both_energies_and_tolerance(self):
        expected = b'-0.169075164\n-0.169087605\n'
        case = success('nbody', expected, 'finite-two-energy-lines-within-1e-8')
        actual = b'-0.169075160\n-0.169087600\n'
        self.assertTrue(OUTPUTS.validate(case, 'scala', actual, b'', 0, expected)['output_contract_satisfied'])
        for bad in [b'-0.169075164\n', expected+b'0.000000000\n',
                    b'nan\n-0.169087605\n', b'-0.169075164\n-0.169087500\n',
                    b'-0.16907516\n-0.16908760\n']:
            with self.assertRaises(ValueError):
                OUTPUTS.validate(case, 'typescript', bad, b'', 0, expected)

    def test_method_cannot_be_substituted(self):
        expected = b'1.000000000\n2.000000000\n'
        for benchmark, method in [('fasta','finite-two-energy-lines-within-1e-8'),
                                  ('nbody','exact-complete-bytes'),('fasta','unknown')]:
            with self.assertRaises(ValueError):
                OUTPUTS.validate(success(benchmark,expected,method), 'scala', expected, b'', 0, expected)

    def test_exact_decimal_tolerance_boundary(self):
        for reference, boundary, outside in [
                (b'-0.169016441',b'-0.169016451',b'-0.169016452'),
                (b'-0.169073022',b'-0.169073032',b'-0.169073033')]:
            expected = b'-0.169075164\n' + reference + b'\n'
            case = success('nbody',expected,'finite-two-energy-lines-within-1e-8')
            for language in OUTPUTS.LANGUAGES:
                result = OUTPUTS.validate(case,language,b'-0.169075164\n'+boundary+b'\n',b'',0,expected)
                self.assertEqual(result['differences_nanounits'],[0,10])
                with self.assertRaises(ValueError):
                    OUTPUTS.validate(case,language,b'-0.169075164\n'+outside+b'\n',b'',0,expected)

    def test_typescript_rejections_require_byte_and_partial_header(self):
        for code in [32,9,0,255,62,59,63]:
            case = rejection(code); message = f'Invalid IUPAC byte: {code}\n'.encode('ascii')
            self.assertTrue(OUTPUTS.validate(case,'typescript',b'>r\n',message,1,None)['output_contract_satisfied'])
            for stdout, stderr, status in [(b'',message,1),(b'>r\nA',message,1),
                                           (b'>r\n',message,0),(b'>r\n',message,-9),
                                           (b'>r\n',b'Invalid IUPAC byte: 33\n',1)]:
                with self.assertRaises(ValueError):
                    OUTPUTS.validate(case,'typescript',stdout,stderr,status,None)

    def test_scala_requires_exception_main_stack_and_empty_output(self):
        for code in [32,9,0,255,62,59,63]:
            message = scala_error(code); case = rejection(code)
            self.assertTrue(OUTPUTS.validate(case,'scala',b'',message,1,None)['output_contract_satisfied'])
            for stdout, stderr in [(b'>r\n',message),(b'',scala_error(33)),
                                   (b'',message+b'unrelated failure\n'),
                                   (b'',message.replace(b'Main.scala:56)\n',b'Main.scala:56)\r\n')),
                                   (b'',message.replace(b'Main.scala:56)',b'Main.scala:\x0056)')),
                                   (b'',message.replace(b'\tat Main.main(Main.scala)\n',b''))]:
                with self.assertRaises(ValueError):
                    OUTPUTS.validate(case,'scala',stdout,stderr,1,None)

    def test_unknown_language_and_incomplete_rejection_fail(self):
        case = rejection(32)
        for language in ['prolog','javascript','']:
            with self.assertRaises(ValueError):
                OUTPUTS.validate(case,language,b'',b'',1,None)
        case['expected_invalid_byte'] = True
        with self.assertRaises(ValueError):
            OUTPUTS.validate(case,'scala',b'',b'',1,None)


if __name__ == '__main__':
    unittest.main()
