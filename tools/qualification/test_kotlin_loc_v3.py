"""Pure PSI/artifact and newline-input regressions; no native parser execution."""
import importlib.util
from pathlib import Path
import unittest


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(filename))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


original = load('original_kotlin_reader_tests_v3', 'test_kotlin_loc.py')
original.loc = load('kotlin_reader_v3', 'kotlin_loc_v3.py')
PsiTests = original.PsiTests
ArtifactTests = original.ArtifactTests


class ParserInputTests(unittest.TestCase):
    def test_normalized_parser_input_preserves_unicode_and_written_escape_characters(self):
        # Check the Java call's input wiring without compiling the diagnostic.
        java = (original.loc.PACKET/'SourceReader.java').read_text()
        normalization = r'''String normalized = source.replace("\r\n", "\n").replace('\r', '\n');'''
        call = 'factory.createFile(sourcePath.getFileName().toString(), normalized)'
        self.assertLess(java.index(normalization), java.index(call))
        self.assertIn('require(parsed.equals(normalized),', java)
        self.assertIn('Files.write(directory.resolve("source.kt"), raw,', java)
        # This is a pure fixture for the specified Java String replacements,
        # not an assertion that the native parser has accepted the source.
        literal = r'val value = "λ😀\r\n" // comment'
        source = literal + '\r\nfun f() = value\r'
        expected = literal + '\nfun f() = value\n'
        parser_input = source.replace('\r\n', '\n').replace('\r', '\n')
        self.assertEqual(parser_input, expected)
        self.assertIn('λ😀\\r\\n', parser_input)
        self.assertNotIn('\r', parser_input)
        expected_row, psi, unchanged_source, parsed = original.fixture(source, parser_input)
        original.loc.validate_psi(psi, unchanged_source, parsed, expected_row)
        self.assertEqual(unchanged_source.encode(), source.encode())
        self.assertTrue(psi['newline_normalization_observed'])
        self.assertEqual(psi['source_utf16_length'], len(parser_input.encode('utf-16-le'))//2)


if __name__ == '__main__':
    unittest.main()
