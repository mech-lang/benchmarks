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
import source_metrics

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


def alias_fixture():
    catalog = fixture()
    owner = catalog['programs']['b:first']
    owner['native_observations'] = 3
    catalog['program_inventory']['b:first'] = copy.deepcopy(owner)
    alias = copy.deepcopy(owner)
    alias.update(key='b:alias', id='alias', timing_alias_of='b:first',
                 source_alias_of='b:first', aliased_sample_source='b:first',
                 native_observations=0, distinct_optimization_claimed=False,
                 source_alias_note='Same source and observations; second label only.',
                 separate_fresh_samples_required=False)
    catalog['program_inventory']['b:alias'] = alias
    return catalog


def bound_fixture():
    catalog = fixture()
    source = catalog['files'].pop('source')
    digest = hashlib.sha256(source['code'].encode()).hexdigest()
    source['sha256'] = digest
    catalog['files'][digest] = source
    for pool in ('programs', 'program_inventory'):
        for row in catalog[pool].values():
            row['files'] = [digest]
            row['file_roles'][digest] = row['file_roles'].pop('source')
    return catalog


def measured_fixture(catalog, raw=None):
    raw = raw if raw is not None else json.dumps(catalog).encode()
    return raw, source_metrics.build_report(catalog, raw, include_audit=False)


class BrowserProjection(unittest.TestCase):
    def test_bound_metrics_preserve_source_partition_counts_and_catalog(self):
        catalog = bound_fixture()
        before = copy.deepcopy(catalog)
        raw, metrics = measured_fixture(catalog)
        projected = builder.browser_data(catalog, source_metrics=metrics, catalog_raw=raw)
        self.assertEqual(catalog, before)
        self.assertEqual(projected['programs']['b:first']['source_metrics'], metrics['profiles']['b:first'])
        self.assertEqual(projected['source_metrics']['catalog_sha256'], hashlib.sha256(raw).hexdigest())
        self.assertEqual(projected['source_metrics']['uniform_logical_loc']['status'], 'unavailable')
        self.assertIsNone(projected['programs']['b:first']['source_metrics']['application']['cl100k_base_tokens'])

    def test_bound_metrics_fail_closed_on_catalog_tool_profile_and_partition_changes(self):
        catalog = bound_fixture()
        raw, metrics = measured_fixture(catalog)
        mutations = [
            lambda m: m.update(catalog_sha256='0'*64),
            lambda m: m.update(tool_sha256='0'*64),
            lambda m: m['profiles'].pop('b:second'),
            lambda m: m['profiles']['b:first']['files'][0].update(application_line_ranges=[]),
            lambda m: m['profiles']['b:first']['application'].update(utf8_bytes=999),
            lambda m: m['profiles']['b:first']['retained_application_loc'].update(status='uniform-logical-loc'),
            lambda m: m['profiles']['b:first']['canonical_formatted_loc'].update(value=2),
            lambda m: m['profiles']['b:first']['files'][0]['application'].update(cl100k_base_tokens=42),
        ]
        for mutate in mutations:
            changed = copy.deepcopy(metrics); mutate(changed)
            with self.assertRaisesRegex(ValueError, 'Invalid source metrics'):
                builder.browser_data(catalog, source_metrics=changed, catalog_raw=raw)
        with self.assertRaisesRegex(ValueError, 'Exact catalog bytes'):
            builder.browser_data(catalog, source_metrics=metrics)

    def test_rebound_catalog_cannot_hide_changed_source_bytes_or_support_roles(self):
        for change in ('code', 'role', 'range', 'displayed-code', 'displayed-sha'):
            catalog = bound_fixture()
            raw, metrics = measured_fixture(catalog)
            digest = catalog['programs']['b:first']['files'][0]
            if change == 'code': catalog['files'][digest]['code'] += 'changed\n'
            if change == 'role': catalog['programs']['b:first']['file_roles'][digest]['role'] = 'runtime-support'
            if change == 'range': catalog['programs']['b:first']['file_roles'][digest]['support_line_ranges'] = [{'start': 1, 'end': 1}]
            if change == 'displayed-code': catalog['programs']['b:first']['file_roles'][digest]['code'] = 'different displayed bytes\n'
            if change == 'displayed-sha': catalog['programs']['b:first']['file_roles'][digest]['sha256'] = '0'*64
            raw = json.dumps(catalog).encode()
            metrics['catalog_sha256'] = hashlib.sha256(raw).hexdigest()
            with self.assertRaisesRegex(ValueError, 'Invalid source metrics'):
                builder.browser_data(catalog, source_metrics=metrics, catalog_raw=raw)

    def test_explicit_timing_alias_fields_and_order_are_preserved(self):
        catalog = alias_fixture()
        before = copy.deepcopy(catalog)
        projected = builder.browser_data(catalog)
        self.assertEqual(catalog, before)
        self.assertEqual(list(projected['program_inventory']), list(catalog['program_inventory']))
        for field in ('timing_alias_of', 'source_alias_of', 'aliased_sample_source',
                      'native_observations', 'distinct_optimization_claimed', 'source_alias_note',
                      'separate_fresh_samples_required'):
            self.assertEqual(projected['program_inventory']['b:alias'][field],
                             catalog['program_inventory']['b:alias'][field])

    def test_timing_alias_requires_direct_same_scope_owner(self):
        for field, value in (('timing_alias_of', 'missing'), ('timing_alias_of', 'b:alias'),
                             ('timing_alias_of', ''), ('language', 'other'), ('benchmark', 'other')):
            with self.subTest(field=field, value=value):
                catalog = alias_fixture(); catalog['program_inventory']['b:alias'][field] = value
                with self.assertRaisesRegex(ValueError, 'Invalid timing alias'):
                    builder.browser_data(catalog)
        catalog = alias_fixture()
        catalog['programs']['b:first']['timing_alias_of'] = 'b:alias'
        with self.assertRaisesRegex(ValueError, 'directly own'):
            builder.browser_data(catalog)

    def test_timing_alias_rejects_changed_samples_coordinates_and_missing_nulls(self):
        for field, value in (('samples', [0.2, 0.3, 0.5]), ('seconds', 0.4), ('x', 2),
                             ('y', True), ('files', ['other']), ('loc', 3), ('formatted_x', 1)):
            with self.subTest(field=field):
                catalog = alias_fixture(); catalog['program_inventory']['b:alias'][field] = value
                with self.assertRaisesRegex(ValueError, 'differs from owner'):
                    builder.browser_data(catalog)
        catalog = alias_fixture(); del catalog['program_inventory']['b:alias']['formatted_x']
        with self.assertRaisesRegex(ValueError, 'presence differs'):
            builder.browser_data(catalog)
        for pool in ('programs', 'program_inventory'):
            for row in catalog[pool].values():row.pop('formatted_x', None)
        builder.browser_data(catalog)  # Optional field absent from both owner and alias.

    def test_timing_alias_rejects_new_native_observations_and_wrong_sample_owner(self):
        for field, value in (('native_observations', 3), ('native_observations', False),
                             ('aliased_sample_source', 'b:second')):
            with self.subTest(field=field, value=value):
                catalog = alias_fixture(); catalog['program_inventory']['b:alias'][field] = value
                with self.assertRaisesRegex(ValueError, 'Invalid timing alias'):
                    builder.browser_data(catalog)

    def test_source_only_aliases_keep_separately_recorded_samples(self):
        catalog = fixture()
        row = catalog['program_inventory']['b:second']
        row.update(source_alias_of='b:first', separate_fresh_samples_required=True,
                   native_observations=3, samples=[0.7, 0.8, 0.9], seconds=0.8,
                   source_alias_note='Same source with separately measured fresh processes.')
        projected = builder.browser_data(catalog)['program_inventory']['b:second']
        self.assertNotIn('timing_alias_of', projected)
        for field in ('source_alias_of', 'separate_fresh_samples_required', 'native_observations',
                      'samples', 'seconds', 'source_alias_note'):
            self.assertEqual(projected[field], row[field])

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
            for name in ('site/src', 'site/reports', 'data', 'tools', 'experiments/source-metrics/v1'):
                (root/name).mkdir(parents=True)
            (root/'site/src/index.html').write_text('<script src="./app.mjs"></script>')
            (root/'site/src/app.mjs').write_text("import './math.mjs';\n")
            (root/'site/src/math.mjs').write_text('export const identity=1;\n')
            (root/'site/reports/method.txt').write_text('retained report\n')
            (root/'tools/source_metrics.py').write_bytes(Path(source_metrics.__file__).read_bytes())
            original = json.dumps(bound_fixture(), indent=2).encode()
            (root/'data/benchmarks.json').write_bytes(original)
            _, metrics = measured_fixture(json.loads(original), original)
            (root/builder.SOURCE_METRICS_PATH).write_text(json.dumps(metrics))
            implementation = root/'builder.py'
            implementation.write_text('reviewed transformation revision 1\n')
            with patch.object(builder, 'ROOT', root), patch.object(builder, '__file__', str(implementation)):
                builder.build()
                first = json.loads((root/'site/public/build.json').read_bytes())
                payload = (root/'site/public/data.json').read_bytes()
                compressed = (root/'site/public/data.json.gz').read_bytes()
                self.assertEqual(payload, builder.browser_payload(json.loads(original), catalog_raw=original,
                    source_metrics=metrics, metrics_raw=(root/builder.SOURCE_METRICS_PATH).read_bytes()))
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
                changed = bound_fixture()
                changed['programs']['b:first']['samples'][0] = 0.25
                (root/'data/benchmarks.json').write_text(json.dumps(changed))
                with self.assertRaisesRegex(ValueError, 'catalog SHA-256 differs'):
                    builder.build()
                _, metrics = measured_fixture(changed, (root/'data/benchmarks.json').read_bytes())
                (root/builder.SOURCE_METRICS_PATH).write_text(json.dumps(metrics))
                builder.build()
                third = json.loads((root/'site/public/build.json').read_bytes())
                self.assertNotEqual(second['version'], third['version'])


if __name__ == '__main__':
    unittest.main()
