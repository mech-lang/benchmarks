"""Offline negative work-replay fixtures; no Nim/compiler/native process."""
from pathlib import Path
import tempfile
import unittest

import instrument_sources_v2 as instrument
import reference_work as work


BEGIN = 'begin\t0\t2\t2\n'
ZERO = ('rank\t0\t-1\t-1\t0,1\nrotations\t0\t-1\t-1\t0,0\n'
    'done\t0\t0\t0\t0,1\nmaximum\t0\t0\t0\t0,1\n')
ONE = ('rank\t1\t-1\t-1\t1,0\nrotations\t1\t-1\t-1\t0,1\n'
    'copy\t1\t-1\t-1\t1,0\nflip\t1\t1\t0\t1,0\n'
    'swap\t1\t0\t1\t0,1\ndone\t1\t1\t-1\t1,0\n'
    'maximum\t1\t1\t0\t1,0\n')
END = 'end\t0\t2\t-1\t1\n'
OUTPUT = b'-1\nPfannkuchen(2) = 1\n'


class QualificationTests(unittest.TestCase):
    def fixture(self, text):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        directory = Path(temporary.name)
        (directory / '0-2.tsv').write_text(text)
        return directory

    def test_guarded_exact_work_and_copy_reduction(self):
        result = work.validate(self.fixture(BEGIN + ZERO + ONE + END), 2, False, True, OUTPUT)
        self.assertEqual(result['aggregate']['permutations'], 2)
        self.assertEqual(result['aggregate']['scratch_copies'], 1)
        self.assertEqual(result['aggregate']['actual_prefix_reversals'], 1)
        self.assertEqual(result['aggregate']['actual_endpoint_swaps'], 1)

    def test_parent_still_copies_zero_first_permutation(self):
        zero = ZERO.replace('done\t0', 'copy\t0\t-1\t-1\t0,1\ndone\t0')
        result = work.validate(self.fixture(BEGIN + zero + ONE + END), 2, False, False, OUTPUT)
        self.assertEqual(result['aggregate']['scratch_copies'], 2)

    def test_missing_actual_swap_rejects_even_with_correct_output(self):
        text = BEGIN + ZERO + ONE.replace('swap\t1\t0\t1\t0,1\n', '') + END
        with self.assertRaises(ValueError):
            work.validate(self.fixture(text), 2, False, True, OUTPUT)

    def test_wrong_global_parity_rejects(self):
        text = (BEGIN + ZERO + ONE + END).replace('done\t1\t1\t-1', 'done\t1\t1\t1')
        with self.assertRaises(ValueError):
            work.validate(self.fixture(text), 2, False, True, OUTPUT)

    def test_mutated_array_rejects(self):
        text = (BEGIN + ZERO + ONE + END).replace('swap\t1\t0\t1\t0,1', 'swap\t1\t0\t1\t0,0')
        with self.assertRaises(ValueError):
            work.validate(self.fixture(text), 2, False, True, OUTPUT)

    def test_additional_hidden_work_record_rejects(self):
        with self.assertRaises(ValueError):
            work.validate(self.fixture(BEGIN + ZERO + ONE + ONE + END), 2, False, True, OUTPUT)

    def test_actual_two_worker_creates_and_joins(self):
        directory = self.fixture(BEGIN + ZERO + ONE + END)
        (directory / '0-2.tsv').unlink()
        (directory / '0-1.tsv').write_text('begin\t0\t1\t2\n' + ZERO + 'end\t0\t1\t0\t0\n')
        (directory / '1-2.tsv').write_text('begin\t1\t2\t2\n' + ONE + 'end\t1\t2\t-1\t1\n')
        (directory / 'main.tsv').write_text('workers\t2\ncreated\t0\t0\t1\ncreated\t1\t1\t2\njoined\t0\njoined\t1\n')
        result = work.validate(directory, 2, True, True, OUTPUT)
        self.assertEqual(result['actual_created_threads'], 2)
        self.assertEqual(result['actual_joined_threads'], 2)
        (directory / 'main.tsv').write_text('workers\t2\ncreated\t0\t0\t1\ncreated\t1\t1\t2\njoined\t0\n')
        with self.assertRaises(ValueError):
            work.validate(directory, 2, True, True, OUTPUT)

    def test_library_delta_cannot_change_actual_swaps(self):
        source = (Path(__file__).resolve().parents[1] / 'vendor/nim-2.2.12/algorithm.nim').read_text()
        twin = instrument.library_twin(source)
        restored = twin.replace(instrument.TRACE_HELPERS, '', 1).replace('    when T is int or T is uint8:\n      if fannTraceFile != nil and a.len == 12:\n        fannEvent("swap", x, y, a)\n', '', 1)
        self.assertEqual(restored, source)
        with self.assertRaises(ValueError):
            instrument.library_twin(source.replace('swap(a[x], a[y])', 'discard'))

    def test_observer_excludes_unrelated_string_instantiations(self):
        source = (Path(__file__).resolve().parents[1] / 'vendor/nim-2.2.12/algorithm.nim').read_text()
        twin = instrument.library_twin(source)
        self.assertIn('when T is int or T is uint8:\n      if fannTraceFile != nil and a.len == 12:', twin)
        self.assertNotIn('cast(noSideEffect)', twin)

    def test_trace_oracle_refuses_unbounded_work(self):
        with self.assertRaises(ValueError):
            work.expected_work(7)


if __name__ == '__main__':
    unittest.main()
