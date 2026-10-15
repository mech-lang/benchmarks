"""Focused complete-map policy tests; no native observations or reruns."""
import ast
import importlib.util
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('rebol_complete_map_contract',HERE/'map_contract.py')
m = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(m)
INPUT = b'>ONE\nignored\n>THREE known\n' + b'A'*20 + b'\n>FOUR\nignored\n'
EXPECTED = b'exact caller-pinned bounded output\n'


def sidecar():
    rows = ['rebol-knucleotide-map-observation-v1\t7\t20']
    for width in (1,2,3,4,6,12,18):
        # A-only words have base-four key zero, with exactly 21-width windows.
        rows.extend([f'map\t{width}\t1\t{21-width}',f'entry\t{width}\t0\t{21-width}',f'end\t{width}'])
    return ('\n'.join(rows)+'\n').encode()


class CompleteMaps(unittest.TestCase):
    def check(self,**changes):
        args=dict(stdin=INPUT,stdout=EXPECTED,stderr=b'',exit_status=0,sidecar=sidecar(),expected_stdout=EXPECTED)
        args.update(changes)
        return m.validate(**args)

    def test_exact_seven_maps_without_capacity_or_identity_claims(self):
        result=self.check()
        self.assertEqual(result['complete_maps'],[dict(width=w,entries=1,total_windows=21-w) for w in m.WIDTHS])
        self.assertEqual(result['dump_calls_source_bound'],0)
        self.assertEqual(result['capacity_scope'],'not observed')
        self.assertEqual(result['selected_sequence_bytes'],20)
        for name in ('backing_series_capacity_observed','backing_series_identity_observed',
                     'full_pointer_identity_observed','hash_bucket_capacities_observed',
                     'capacity_growth_trajectory_observed','native_process_verified',
                     'runtime_source_equivalence_proven','full_size_work_qualified',
                     'source_work_qualified','full_timing_qualified','chart_admission'):
            self.assertIs(result[name],False)
        self.assertFalse(any(key.startswith('backing_') for row in result['complete_maps'] for key in row))

    def test_normal_zero_and_complete_empty_stderr_are_required(self):
        for value in (1,-9,False,None):
            with self.subTest(exit_status=value),self.assertRaises(ValueError):self.check(exit_status=value)
        for stderr in (b'warning\n',b'Dump Series #00000001: wide: 32\n',b'\n',''):
            with self.subTest(stderr=stderr),self.assertRaises(ValueError):self.check(stderr=stderr)
        with self.assertRaises(ValueError):self.check(stdout=EXPECTED+b'\n')

    def test_incomplete_changed_extra_or_noncanonical_sidecar_rejects(self):
        raw=sidecar()
        for bad in (raw[:-1],raw+b'extra\n',raw.replace(b'entry\t18\t0\t3\n',b''),
                    raw.replace(b'entry\t1\t0\t20',b'entry\t1\t0\t19'),
                    raw.replace(b'entry\t1\t0\t20',b'entry\t1\t00\t20'),
                    raw.replace(b'entry\t1\t0\t20\n',b'entry\t1\t0\t20\n'*2)):
            with self.subTest(sidecar=bad[:80]),self.assertRaises(ValueError):self.check(sidecar=bad)

    def test_input_selection_and_existing_bounds_stay_strict(self):
        self.assertEqual(m.selected_sequence(INPUT),b'A'*20)
        for changes in ({'stdin':b'>THREEISH\nAAAA'}, {'stdin':b'>THREE\nAAAN'},
                        {'sidecar':b'x'*(m.SIDECAR_LIMIT+1)}, {'stdout':b'x'*(m.STDOUT_LIMIT+1)}):
            with self.subTest(fields=list(changes)),self.assertRaises(ValueError):self.check(**changes)

    def test_independent_selection_and_histogram_functions_are_exact_originals(self):
        old=ast.parse((HERE.parent/'map_contract.py').read_text())
        new=ast.parse((HERE/'map_contract.py').read_text())
        for name in ('require','number','selected_sequence','independent_maps','sidecar_maps'):
            before=next(x for x in old.body if isinstance(x,ast.FunctionDef) and x.name==name)
            after=next(x for x in new.body if isinstance(x,ast.FunctionDef) and x.name==name)
            self.assertEqual(ast.dump(before,include_attributes=False),ast.dump(after,include_attributes=False),name)

    def test_wrapper_only_removes_dump_and_relocates_the_same_main(self):
        expected=(HERE.parent/'knucleotide.reb').read_text()
        expected=expected.replace('Unchanged knucleotide complete-map and final-capacity observation',
                                  'Unchanged knucleotide complete-map observation')
        expected=expected.replace('%../../../archive/languages/rebol/','%../../../../archive/languages/rebol/')
        expected=expected.replace('Preserve actual map iteration order for exact backing-series matching.',
                                  'Preserve actual map iteration order in the complete sidecar.')
        expected=expected.replace('    ; This single generic runtime dump precedes every diagnostic pair copy.\n'
                                  '    ; It writes the retained native format to stderr, not benchmark stdout.\n'
                                  '    stats/dump-series -1\n',
                                  '    ; Observe only the seven actual maps. Runtime capacity is not measured.\n')
        actual=(HERE/'knucleotide.reb').read_text()
        self.assertEqual(actual,expected)
        self.assertNotIn('stats/dump-series',actual)
        old_main=(HERE.parent/'../../../archive/languages/rebol/20261013/drafts/private-v1/sources/knucleotide/main.reb').resolve()
        new_main=(HERE/'../../../../archive/languages/rebol/20261013/drafts/private-v1/sources/knucleotide/main.reb').resolve()
        self.assertEqual(old_main,new_main)
        self.assertTrue(old_main.is_file())


if __name__=='__main__':unittest.main()
