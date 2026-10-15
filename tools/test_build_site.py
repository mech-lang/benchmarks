"""Small browser-projection/build fixtures; never read the recorded catalog."""
import copy
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('site_builder', Path(__file__).with_name('build_site.py'))
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


def fixture():
    row = dict(key='b:first', id='first', benchmark='b', language='test',
               samples=[0.2, 0.3, 0.4], seconds=0.3, timing_sd=0.1,
               loc=2, physical_loc=1, x=1, y=1, formatted_loc=None,
               formatted_loc_status='unavailable', formatted_loc_complete=False,
               formatted_loc_evidence={'reasons': ['No formatter observation.']},
               formatted_x=None, eligible_for_chart=True, files=['source'],
               report='archive/report.json.gz', report_sha256='a'*64,
               measured_backend={'execution': 'interpreted', 'evidence': {'report': 'archive/runtime.json'}},
               file_roles={'source': {'role': 'application-helper', 'source_path': 'archive/helper.reb'}},
               loc_expansions=[{'line': 1, 'units': ['a: 1', 'b: 2']}],
               sample_details=[{'receipt': 'archive/sample.json', 'wall_seconds': value}
                               for value in (0.2, 0.3, 0.4)],
               source_url='https://example.test/source', runtime_policy='Whole process',
               exclusion_reason=None)
    row['publication_record'] = copy.deepcopy(row)
    second = copy.deepcopy(row)
    second.update(key='b:second', id='second', seconds=None, samples=[0.5],
                  eligible_for_chart=False, exclusion_reason='Failed matched control.')
    return dict(languages=[{'key': 'test', 'label': 'λ', 'release_year': 1997}],
                benchmarks=[dict(key='b', baseline_loc=2, baseline_seconds=0.3,
                    groups=[dict(language='test', programs=['b:first'], fast='b:first', small='b:first')])],
                programs={'b:first': row},
                program_inventory={'b:second': second, 'b:first': copy.deepcopy(row)},
                files={'source': {'code': 'a: 1 b: 2\n', 'sha256': 'b'*64,
                                  'name': 'helper.reb', 'path': 'archive/helper.reb'}},
                repository={'url': 'https://example.test/repository'},
                archive_paths={'archive/report.json': 'archive/report.json.gz'},
                protocol={'boundary': 'whole process'}, reference_summary=[],
                saved_publication_audit={'physical_pins': {'/original/receipt': 'c'*64}})


class BrowserProjection(unittest.TestCase):
    def test_samples_counts_sources_and_displayed_row_fields_are_exact(self):
        catalog = fixture()
        projected = builder.browser_data(catalog)
        for pool in ('programs', 'program_inventory'):
            self.assertEqual(list(projected[pool]), list(catalog[pool]))
            for key, row in catalog[pool].items():
                self.assertEqual(projected[pool][key],
                                 {name: value for name, value in row.items() if name != 'publication_record'})
        for field in ('files', 'languages', 'benchmarks', 'archive_paths', 'repository', 'protocol', 'reference_summary'):
            self.assertEqual(projected[field], catalog[field])

    def test_unrendered_proofs_are_omitted_but_format_reasons_and_source_overrides_remain(self):
        catalog = fixture()
        row = catalog['programs']['b:first']
        row['sample_execution_metadata'] = [{'pins': {'/runtime': 'c'*64}}]
        row['matched_mech_control'] = {'samples': [1, 2, 3], 'proof': 'retained in canonical'}
        row['formatted_loc_evidence']['owner_receipts'] = {'large': ['unused']*10}
        row['algorithm'] = {'reason': 'Same required recurrence.', 'proof': {'unused': True}}
        row['file_roles']['source'].update(code='exact override\n', loc_note='Counted helper',
                                          retained_source={'path': 'unused by source renderer'})
        projected = builder.browser_data(catalog)['programs']['b:first']
        self.assertNotIn('sample_execution_metadata', projected)
        self.assertNotIn('matched_mech_control', projected)
        self.assertEqual(projected['formatted_loc_evidence'], {'reasons': ['No formatter observation.']})
        self.assertEqual(projected['algorithm'], {'reason': 'Same required recurrence.'})
        self.assertEqual(projected['file_roles']['source']['code'], 'exact override\n')
        self.assertEqual(projected['file_roles']['source']['loc_note'], 'Counted helper')
        self.assertNotIn('retained_source', projected['file_roles']['source'])

    def test_all_three_loc_audit_forms_keep_rendered_owner_fields(self):
        packed = {'loc_expansions': [{'line': 2, 'extra_lines': 1, 'units': ['a', 'b'], 'proof': 'unused'}]}
        self.assertEqual(builder.browser_loc_audit(packed), [{'line': 2, 'extra_lines': 1, 'units': ['a', 'b']}])
        grouped = {'loc_expansions': [{'source': '/original/helper', 'expansions': [
            {'line': 3, 'units': 0, 'original': 'wrapped source', 'proof': 'unused'}]}]}
        self.assertEqual(builder.browser_loc_audit(grouped), [{'source': '/original/helper', 'expansions': [
            {'line': 3, 'units': 0, 'original': 'wrapped source'}]}])
        owned = dict(loc_expansion_format='source-bound-canonical-owner-audit-v1',loc_expansions=[
            dict(name='main',sha256='a'*64,source_language='other',physical_loc=1,normalized_loc=1,
                 canonical_events=[dict(start=2,kind='statement',units=1,original_source='x',proof='unused')]),
            dict(name='helper',sha256='b'*64,source_language='gleam',physical_loc=1,normalized_loc=1,
                 expansions=[dict(full_owner_start=4,kind='closer',units=0,original_source='}',proof='unused')])])
        result = builder.browser_loc_audit(owned)
        self.assertEqual(result[0]['canonical_events'], [dict(start=2,kind='statement',units=1,original_source='x')])
        self.assertEqual(result[1]['expansions'], [dict(full_owner_start=4,kind='closer',units=0,original_source='}')])

    def test_projection_does_not_mutate_canonical_catalog(self):
        catalog = fixture()
        before = copy.deepcopy(catalog)
        builder.browser_payload(catalog)
        self.assertEqual(catalog, before)
        self.assertNotIn('saved_publication_audit', builder.browser_data(catalog))

    def test_optional_inventory_remains_optional(self):
        catalog = fixture()
        del catalog['program_inventory']
        self.assertNotIn('program_inventory', builder.browser_data(catalog))
        for field in ('languages', 'benchmarks', 'programs', 'files'):
            broken = dict(catalog)
            del broken[field]
            with self.assertRaisesRegex(ValueError, 'Missing browser catalog field'):
                builder.browser_data(broken)

    def test_compact_utf8_payload_is_deterministic_and_preserves_null(self):
        catalog = fixture()
        raw = builder.browser_payload(catalog)
        self.assertEqual(raw, builder.browser_payload(catalog))
        self.assertIn('λ'.encode(), raw)
        self.assertEqual(json.loads(raw), builder.browser_data(catalog))
        self.assertIsNone(json.loads(raw)['program_inventory']['b:second']['seconds'])
        self.assertLess(len(raw), len(json.dumps(catalog, indent=2).encode()))

    def test_build_keeps_catalog_bytes_and_binds_actual_payload(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name in ('site/src', 'site/reports', 'data'):
                (root/name).mkdir(parents=True)
            (root/'site/src/index.html').write_text('<script src="./app.mjs"></script>')
            (root/'site/src/app.mjs').write_text("import './math.mjs';\n")
            (root/'site/src/math.mjs').write_text('export const identity=1;\n')
            (root/'site/reports/method.txt').write_text('retained report\n')
            original = json.dumps(fixture(), indent=2).encode()
            (root/'data/benchmarks.json').write_bytes(original)
            implementation = root/'builder.py'
            implementation.write_text('reviewed transformation revision 1\n')
            with patch.object(builder, 'ROOT', root), patch.object(builder, '__file__', str(implementation)):
                builder.build()
                first = json.loads((root/'site/public/build.json').read_bytes())
                payload = (root/'site/public/data.json').read_bytes()
                compressed = (root/'site/public/data.json.gz').read_bytes()
                self.assertEqual(payload, builder.browser_payload(json.loads(original)))
                self.assertEqual(gzip.decompress(compressed), payload)
                self.assertEqual(compressed, gzip.compress(payload, mtime=0))
                self.assertEqual(first['files']['data.json'], hashlib.sha256(payload).hexdigest())
                self.assertEqual(first['files']['data.json.gz'], hashlib.sha256(compressed).hexdigest())
                self.assertIn('?v='+first['version'], (root/'site/public/index.html').read_text())
                self.assertEqual((root/'data/benchmarks.json').read_bytes(), original)
                builder.build()
                self.assertEqual((root/'site/public/data.json.gz').read_bytes(), compressed)
                implementation.write_text('reviewed transformation revision 2\n')
                builder.build()
                second = json.loads((root/'site/public/build.json').read_bytes())
                self.assertNotEqual(first['version'], second['version'])
                changed = fixture()
                changed['programs']['b:first']['samples'][0] = 0.25
                (root/'data/benchmarks.json').write_text(json.dumps(changed))
                builder.build()
                third = json.loads((root/'site/public/build.json').read_bytes())
                self.assertNotEqual(second['version'], third['version'])


if __name__ == '__main__':
    unittest.main()
