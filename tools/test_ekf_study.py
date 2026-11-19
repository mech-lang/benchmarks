import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from ekf_study import ekf_study

ROOT = Path(__file__).resolve().parents[1]


class EkfStudyTest(unittest.TestCase):
    def test_every_retained_sample_and_separate_scope_is_preserved(self):
        data = ekf_study(ROOT)
        self.assertEqual([len(s['rows']) for s in data['studies']], [10, 18, 12, 3, 1, 1])
        self.assertEqual(sum(r['n'] for s in data['studies'] for r in s['rows']), 431)
        studies = {s['id']: s for s in data['studies']}
        self.assertEqual(studies['backends']['rows'][0]['n'], 10)
        self.assertEqual(studies['backends']['instances'], 500000)
        backend = next(r for r in studies['backends']['rows'] if r['backend'] == 'metal' and r['mode'] == 'checked')
        cross = next(r for r in studies['metal']['rows'] if r['label'] == 'Mech generated MSL' and r['mode'] == 'checked')
        self.assertAlmostEqual(backend['median'], 420.89616624669395)
        self.assertAlmostEqual(cross['median'], 409.7645)
        self.assertNotEqual(backend['median'], cross['median'])

    def test_export_retains_original_bytes_and_source_identities(self):
        with tempfile.TemporaryDirectory() as directory:
            data = ekf_study(ROOT, directory)
            output = Path(directory)
            manifest = json.loads((ROOT/'studies/ekf/provenance.json').read_text())
            for item in manifest['evidence']:
                path = output/'ekf-evidence'/item['file'] if item.get('publish', True) else ROOT/item['repository_file']
                self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), item['sha256'])
            for study in data['studies']:
                for row in study['rows']:
                    self.assertTrue((output/row['source_url'].removeprefix('/benchmarks/')).is_file())
                    self.assertEqual(row['n'], len(row['samples_seconds_per_filter_turn']))
            measured = next(r for r in data['studies'][0]['rows'] if r['backend'] == 'simd-aot')
            self.assertEqual(hashlib.sha256((output/measured['source_url'].removeprefix('/benchmarks/')).read_bytes()).hexdigest(), 'da531cddcb25d002d49f1a77800122e84b573e2685e191c1955908ef6fccd625')

    def test_execution_categories_follow_measured_implementations(self):
        data = ekf_study(ROOT)
        backends, cpu, metal = data['studies'][:3]
        self.assertTrue(all(r['is_mech'] for r in backends['rows']))
        categories = {r['label']: r['category'] for r in cpu['rows']}
        self.assertEqual({name for name, kind in categories.items() if kind == 'cpu-jit'},
                         {'Mech fused SIMD/JIT', 'Mech per-turn SIMD/JIT', 'Julia SIMD.jl',
                          'NumPy/Numba', 'Taichi LLVM CPU', 'Halide native CPU'})
        self.assertEqual({name for name, kind in categories.items() if kind == 'cpu-aot'},
                         {'Rust packed SIMD', 'Futhark ISPC AOT', 'Mojo SIMD-4'})
        self.assertTrue(all(r['category'] == 'metal' for r in metal['rows']))
        self.assertTrue(all(r['is_mech'] == r['label'].startswith('Mech')
                            for study in [cpu, metal] for r in study['rows']))

    def test_modified_evidence_is_not_silently_projected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(ROOT/'studies/ekf', root/'studies/ekf')
            evidence = root/'studies/ekf/evidence/apple-m1-mech-backend-pairs-n10-2026-09-25.json'
            data = json.loads(evidence.read_text())
            data['summary']['metal']['checked']['median_million_filter_turns_per_second'] *= 2
            evidence.write_text(json.dumps(data))
            with self.assertRaises(AssertionError):
                ekf_study(root)


if __name__ == '__main__':
    unittest.main()
