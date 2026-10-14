"""Lua nine-to-ten admission with real retained forms and synthetic catalogs."""
import copy
import importlib.util
from pathlib import Path
import unittest


HERE = Path(__file__).parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE/filename)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


p = load('lua_publication_test', 'lua_retained_publication.py')
fixtures = load('lua_catalog_fixtures', 'test_retained_catalog_publication.py')


class Admission(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.candidate = fixtures.candidates()['lua']

    def before(self, aggregate=False):
        return fixtures.catalog(self.candidate, expanded_reference=aggregate)

    def apply(self, before, languages, candidate=None):
        return p.build_publication(before, languages, self.candidate if candidate is None else candidate,
                                   dict(path='experiments/lua/retained-pidigits-v1/export/candidate.json', sha256='a'*64))

    def test_absent_prior_aggregate_stays_absent_in_history_and_adds_full_reference(self):
        before, languages = self.before()
        snapshot = copy.deepcopy((before, languages, self.candidate))
        after, new_languages, audit = self.apply(before, languages)
        self.assertEqual((before, languages, self.candidate), snapshot)
        self.assertIsNone(audit['aggregate_change']['before'])
        refs = [row for row in after['reference_summary'] if row['lang'] == 'lua']
        self.assertEqual(len(refs), 1)
        self.assertEqual(refs[0]['label'], 'Lua (interpreted)')
        self.assertEqual(refs[0]['measured_benchmarks'], [b['key'] for b in before['benchmarks']])
        for kind in ('fast', 'small'):
            for axis in ('x', 'y'):
                self.assertEqual(refs[0][kind][axis], p.p.aggregate(after, refs[0], kind, axis))
        for pool in ('programs', 'program_inventory', 'files'):
            for key, value in before[pool].items():
                self.assertEqual(after[pool][key], value)
        self.assertEqual(audit['normalizations'], [])
        self.assertEqual(new_languages['languages']['c'], languages['languages']['c'])
        self.assertEqual((audit['subject_native_observations'], audit['control_native_observations']), (12, 6))
        for key, row in self.candidate['program_inventory'].items():
            for field in ('samples', 'matched_mech_control', 'additional_matched_mech_control', 'file_roles'):
                self.assertEqual(after['program_inventory'][key][field], row[field])

    def test_present_aggregate_matches_frozen_transform_without_new_semantics(self):
        before, languages = self.before(True)
        original = next(row for row in before['reference_summary'] if row['lang'] == 'lua')
        original['label'] = 'Existing public label'
        expected = p.p.build_publication(before, languages, self.candidate,
            dict(path='experiments/lua/retained-pidigits-v1/export/candidate.json', sha256='a'*64))
        actual = self.apply(before, languages)
        self.assertEqual(actual, expected)
        self.assertEqual(actual[2]['aggregate_change']['before'], original)

    def test_missing_duplicate_or_inconsistent_coverage_is_rejected(self):
        mutations = [
            lambda data: data['languages'][1]['timed_benchmarks'].pop(),
            lambda data: data['languages'][1]['timed_benchmarks'].__setitem__(0, 'pidigits'),
            lambda data: data['benchmarks'][0]['groups'].pop(),
            lambda data: data['benchmarks'][0]['groups'].append(copy.deepcopy(data['benchmarks'][0]['groups'][-1])),
            lambda data: data['reference_summary'].append(copy.deepcopy(data['reference_summary'][-1])),
            lambda data: data['reference_summary'][-1]['measured_benchmarks'].pop(),
        ]
        for mutate in mutations:
            before, languages = self.before(True); mutate(before)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                self.apply(before, languages)

    def test_luajit_rows_metadata_and_aggregate_are_untouched(self):
        before, languages = self.before()
        row = copy.deepcopy(before['programs']['pidigits:old-c'])
        row.update(key='pidigits:existing-luajit', language='luajit')
        row['publication_record'] = {k: copy.deepcopy(v) for k,v in row.items() if k != 'publication_record'}
        for pool in ('programs', 'program_inventory'):
            before[pool][row['key']] = copy.deepcopy(row)
        before['languages'].append(dict(key='luajit', timed_benchmarks=['pidigits'], source_benchmarks=['pidigits']))
        before['reference_summary'].append(dict(lang='luajit', fast=dict(x=1,y=2), small=dict(x=1,y=2)))
        languages['languages']['luajit'] = {'displayed_program_count': 1, 'runtime': 'unchanged'}
        after, metadata, _ = self.apply(before, languages)
        for pool in ('programs', 'program_inventory'):
            self.assertEqual(after[pool][row['key']], before[pool][row['key']])
        self.assertEqual(after['languages'][-1], before['languages'][-1])
        self.assertEqual(next(x for x in after['reference_summary'] if x['lang']=='luajit'), before['reference_summary'][-1])
        self.assertEqual(metadata['languages']['luajit'], languages['languages']['luajit'])

    def test_new_minima_and_wrong_cohort_are_rejected(self):
        for axis in ('baseline_seconds', 'baseline_loc'):
            before, languages = self.before()
            bench = next(b for b in before['benchmarks'] if b['key']=='pidigits')
            bench[axis] = 1e9
            with self.subTest(axis=axis), self.assertRaises(ValueError):
                self.apply(before, languages)
        before, languages = self.before()
        with self.assertRaisesRegex(ValueError, 'Only the retained Lua'):
            self.apply(before, languages, fixtures.candidates()['r'])


if __name__ == '__main__':
    unittest.main()
