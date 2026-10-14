"""Exact six-source ownership faults; no R, lexer, native work or timing reads."""
import importlib.util
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('r_six_source_owners',Path(__file__).with_name('r_retained_source_units.py'))
r=importlib.util.module_from_spec(spec);spec.loader.exec_module(r)
EXPECTED={
 'nbody:nbody-r-compact':(19,19),'nbody:nbody-r-optimized':(24,24),
 'binarytrees:binarytrees-r-compact':(15,15),'binarytrees:binarytrees-r-optimized':(21,20),
 'fannkuchredux:fannkuchredux-r-array-compact':(31,30),
 'fannkuchredux:fannkuchredux-r-array-batched':(38,37),
}


class Owners(unittest.TestCase):
    def result(self,key):return r.count_source((ROOT/r.SOURCES[key]['path']).read_bytes(),key)

    def test_all_six_exact_source_identities_and_complete_significant_coverage(self):
        for key,(canonical,physical) in EXPECTED.items():
            with self.subTest(key=key):
                result=self.result(key)
                self.assertEqual((result['canonical_loc'],result['physical_loc']),(canonical,physical))
                self.assertEqual(result['unowned_significant_characters'],[])
                self.assertFalse(result['generic_language_certificate']);self.assertFalse(result['native_execution'])
                self.assertIsNone(result['formatted_loc']);self.assertFalse(result['chart_admission'])

    def test_only_three_proven_packed_control_rows_expand(self):
        expanded={key:self.result(key)['packed_owner_lines'] for key in EXPECTED}
        self.assertEqual({k:v for k,v in expanded.items() if v},{
            'binarytrees:binarytrees-r-optimized':[{'line':7,'canonical_units':2}],
            'fannkuchredux:fannkuchredux-r-array-compact':[{'line':10,'canonical_units':2}],
            'fannkuchredux:fannkuchredux-r-array-batched':[{'line':14,'canonical_units':2}]})
        for key in EXPECTED:
            result=self.result(key)
            self.assertTrue(all(o['canonical_units']==0 for o in result['source_owners'] if o['kind']=='written-open'))
            self.assertTrue(all(o['canonical_units']==1 for o in result['source_owners'] if o['kind']=='written-close'))

    def test_expression_functions_and_named_arguments_are_not_extra_statements(self):
        for key in EXPECTED:
            result=self.result(key)
            self.assertTrue(all(not x['independent_binding'] for x in result['named_arguments']))
            expected=2 if key.startswith('binarytrees:') else 1 if key.startswith('nbody:') else 0
            self.assertEqual(sum(o['kind']=='expression-function-binding' for o in result['source_owners']),expected)
        names={x['name'] for x in self.result('fannkuchredux:fannkuchredux-r-array-batched')['named_arguments']}
        self.assertTrue({'by','each','mc.cores','mc.preschedule'}<=names)

    def test_any_source_mutation_or_wrong_profile_rejected(self):
        for key in EXPECTED:
            source=(ROOT/r.SOURCES[key]['path']).read_bytes()
            for changed in (source+b'\n',source.replace(b' <- ',b' = ',1),source.replace(b'#',b'# changed',1)):
                with self.assertRaises(ValueError):r.count_source(changed,key)
            other=next(x for x in EXPECTED if x!=key)
            with self.assertRaises(ValueError):r.count_source(source,other)
        with self.assertRaises(ValueError):r.count_source(b'x <- 1\n','new-source')


if __name__=='__main__':unittest.main()
