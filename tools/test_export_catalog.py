"""Check shared-observation exports without reading the recorded catalog."""
import contextlib
import copy
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('export_catalog', Path(__file__).with_name('export_catalog.py'))
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)
verify_spec = importlib.util.spec_from_file_location('verify_repository', Path(__file__).with_name('verify_repository.py'))
verifier = importlib.util.module_from_spec(verify_spec)
verify_spec.loader.exec_module(verifier)


def fixture():
    source = 'print(1)\n'
    owner = dict(key='b:owner', id='owner', benchmark='b', language='test',
                 samples=[1, 1, 1], seconds=1, loc=1, physical_loc=1,
                 files=['source'], native_observations=3, report='observed.json')
    alias = dict(owner, key='b:alias', id='alias', timing_alias_of='b:owner',
                 source_alias_of='b:owner', native_observations=0)
    independent = dict(owner, key='b:independent', id='independent', source_alias_of='b:owner')
    return dict(languages=[dict(key='test', label='Test')],
                benchmarks=[dict(key='b', title='B', workload='Print one', baseline_loc=1, baseline_seconds=1)],
                programs={p['key']: p for p in (owner, alias, independent)},
                files={'source': dict(code=source, sha256=hashlib.sha256(source.encode()).hexdigest(),
                                      name='main.test', path='source/main.test')})


def make_export(root):
    data = fixture()
    alias = data['programs'].pop('b:alias')
    alias.update(aliased_sample_source='b:owner', distinct_optimization_claimed=False,
                 source_alias_note='Same source and recorded runs.', separate_fresh_samples_required=False)
    data['program_inventory'] = {'b:alias': alias}
    (root/'data').mkdir()
    (root/'data/benchmarks.json').write_text(json.dumps(data))
    with contextlib.redirect_stdout(io.StringIO()):
        exporter.export(root)
    return data


def verify_export(root):
    # These three unrelated archive/admission checks require the full historic
    # repository. All manifest, source, CSV and summary checks run unchanged.
    with patch.object(verifier, 'check_migration', return_value=[]) as migration, \
         patch.object(verifier, 'check_previous', return_value=0) as previous, \
         patch.object(verifier, 'check_v', return_value={}) as v:
        result = verifier.verify(root)
        migration.assert_called_once_with(root.resolve(), False)
        previous.assert_called_once()
        v.assert_called_once()
        return result


class AliasExports(unittest.TestCase):
    def test_exporter_verifier_roundtrip_with_inventory_alias(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            make_export(root)
            raw = (root/'data/benchmarks.json').read_bytes()
            result = verify_export(root)
            self.assertEqual(result['status'], 'passed')
            self.assertEqual((result['programs'], result['samples'], result['exported_source_copies']), (3, 9, 3))
            summary = json.loads((root/'results/current/summary.json').read_bytes())
            self.assertEqual(summary['recorded_samples_selected_for_chart'], 6)
            self.assertEqual(summary['unique_recorded_samples_in_catalog'], 6)
            self.assertEqual(summary['unique_recorded_samples_selected_for_chart'], 6)
            self.assertEqual((root/'data/benchmarks.json').read_bytes(), raw)

    def test_verifier_rejects_changed_exported_owner_and_preserved_values(self):
        for mutation in ('sample_owner', 'sample_seconds', 'manifest_alias', 'unique_count', 'source'):
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                make_export(root)
                if mutation.startswith('sample_'):
                    path = root/'results/current/samples.csv'
                    with path.open(newline='') as stream:
                        reader = csv.DictReader(stream)
                        columns, rows = reader.fieldnames, list(reader)
                    row = next(row for row in rows if row['program'] == 'alias')
                    row['timing_owner' if mutation == 'sample_owner' else 'seconds'] = \
                        'b:independent' if mutation == 'sample_owner' else '2'
                    with path.open('w', newline='') as stream:
                        writer = csv.DictWriter(stream, fieldnames=columns)
                        writer.writeheader(); writer.writerows(rows)
                elif mutation == 'manifest_alias':
                    path = root/'programs/test/b/alias/program.json'
                    value = json.loads(path.read_bytes()); value['timing_alias_of'] = 'b:independent'
                    path.write_text(json.dumps(value))
                elif mutation == 'unique_count':
                    path = root/'results/current/summary.json'
                    value = json.loads(path.read_bytes()); value['unique_recorded_samples_in_catalog'] = 9
                    path.write_text(json.dumps(value))
                else:
                    (root/'programs/test/b/alias/main.test').write_text('print(2)\n')
                with self.assertRaisesRegex(ValueError, 'Recorded values|manifest changed|summary totals|Exported source changed'):
                    verify_export(root)

    def test_verifier_independently_rejects_invalid_canonical_alias(self):
        changes = [('timing_alias_of', 'missing'), ('timing_alias_of', 'b:alias'),
                   ('native_observations', False), ('aliased_sample_source', 'b:independent'),
                   ('samples', [True, True, True])]
        for field, value in changes:
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                data = make_export(root)
                data['program_inventory']['b:alias'][field] = value
                (root/'data/benchmarks.json').write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, 'Invalid canonical timing alias'):
                    verify_export(root)

    def test_saved_rows_keep_values_and_identify_shared_observations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/'data').mkdir()
            raw = json.dumps(fixture()).encode()
            (root/'data/benchmarks.json').write_bytes(raw)
            with contextlib.redirect_stdout(io.StringIO()):
                exporter.export(root)
            self.assertEqual((root/'data/benchmarks.json').read_bytes(), raw)
            with (root/'results/current/samples.csv').open(newline='') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 9)
            self.assertEqual({row['seconds'] for row in rows}, {'1'})
            self.assertEqual(len({(row['timing_owner'], row['run']) for row in rows}), 6)
            for row in rows:
                expected = 'b:independent' if row['program'] == 'independent' else 'b:owner'
                self.assertEqual(row['timing_owner'], expected)
                self.assertEqual(row['timing_alias_of'], 'b:owner' if row['program'] == 'alias' else '')
            summary = json.loads((root/'results/current/summary.json').read_bytes())
            self.assertEqual(summary['recorded_samples_in_catalog'], 9)
            self.assertEqual(summary['unique_recorded_samples_in_catalog'], 6)
            self.assertEqual(summary['unique_recorded_samples_selected_for_chart'], 6)
            self.assertEqual(summary['timing_alias_programs'], 1)
            record = json.loads((root/'programs/test/b/alias/program.json').read_bytes())
            self.assertEqual(record['timing_alias_of'], 'b:owner')
            self.assertEqual(record['native_observations'], 0)
            separate = json.loads((root/'programs/test/b/independent/program.json').read_bytes())
            self.assertEqual(separate['source_alias_of'], 'b:owner')
            self.assertNotIn('timing_alias_of', separate)

    def test_invalid_alias_fails_before_any_export(self):
        for field, value in [('timing_alias_of', 'missing'), ('timing_alias_of', 'b:alias'),
                             ('samples', [1, 2, 3]), ('samples', [True, True, True]),
                             ('aliased_sample_source', 'b:independent'), ('native_observations', 3),
                             ('native_observations', False), ('language', 'other')]:
            with self.subTest(field=field, value=value), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root/'data').mkdir()
                data = copy.deepcopy(fixture())
                data['programs']['b:alias'][field] = value
                (root/'data/benchmarks.json').write_text(json.dumps(data))
                with self.assertRaisesRegex(ValueError, 'Invalid timing alias'):
                    exporter.export(root)
                self.assertEqual({p.name for p in root.iterdir()}, {'data'})


if __name__ == '__main__':
    unittest.main()
