"""Exact Lean4 policy-correction scope and historical preservation; no language execution."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from audit_owned_implementations import classify
from build_site import browser_data
from qualification import apply_lean4_knucleotide_eligibility as correction


class Lean4EligibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.published = correction.load(correction.ROOT / 'data/benchmarks.json')
        cls.before = copy.deepcopy(cls.published)
        if correction.MARKER in cls.before:
            marker = cls.before.pop(correction.MARKER)
            bench = next(b for b in cls.before['benchmarks'] if b['key'] == 'knucleotide')
            bench['groups'].insert(marker['removed_group_index'], marker['removed_group'])
            for key in correction.KEYS:
                row = cls.before['program_inventory'][key]
                for field in ('eligible_for_chart', 'exclusion_reason', 'eligibility_correction'):
                    row.pop(field)
                row.update(marker['previous_profile_eligibility'][key])
                cls.before['programs'][key] = copy.deepcopy(row)
            cls.before['exclusions'] = [e for e in cls.before['exclusions'] if e['key'] not in correction.KEYS]
            language = next(l for l in cls.before['languages'] if l['key'] == 'lean4')
            language.clear()
            language.update(marker['previous_language'])
            reference = next(r for r in cls.before['reference_summary'] if r['lang'] == 'lean4')
            reference.clear()
            reference.update(marker['previous_reference_summary'][0])
        cls.after = correction.append_catalog(cls.before)

    def changed_profile(self, key):
        value = dict(self.before, programs=dict(self.before['programs']),
                     program_inventory=dict(self.before['program_inventory']))
        row = copy.deepcopy(value['programs'][key])
        value['programs'][key] = value['program_inventory'][key] = row
        return value, row

    def test_only_two_exact_profiles_receive_additive_metadata(self):
        before, after = map(correction.catalog, (self.before, self.after))
        self.assertEqual(before.keys(), after.keys())
        self.assertEqual({key for key in before if before[key] != after[key]}, set(correction.KEYS))
        for key in correction.KEYS:
            self.assertNotIn(key, self.after['programs'])
            self.assertIn(key, self.after['program_inventory'])
            retained = copy.deepcopy(after[key])
            self.assertIs(retained.pop('eligible_for_chart'), False)
            self.assertEqual(retained.pop('exclusion_reason'), correction.REASON)
            meta = retained.pop('eligibility_correction')
            self.assertEqual(meta['source_sha256'], before[key]['files'])
            self.assertTrue(meta['historical_work_assertion_preserved'])
            retained.update({field: before[key][field]
                             for field in ('eligible_for_chart', 'exclusion_reason', 'eligibility_correction')
                             if field in before[key]})
            self.assertEqual(retained, before[key])

    def test_all_sources_roles_counts_samples_and_work_assertions_unchanged(self):
        self.assertEqual(self.before['files'], self.after['files'])
        self.assertEqual(self.before['archive_paths'], self.after['archive_paths'])
        before, after = map(correction.catalog, (self.before, self.after))
        for key, row in before.items():
            for field in ('samples', 'seconds', 'timing_sd', 'sample_execution_metadata', 'files', 'loc',
                          'physical_loc', 'file_roles', 'source_accounting', 'authorship', 'algorithm',
                          'required_work_validated', 'source_work_qualified', 'publication_record', 'x', 'y'):
                self.assertEqual(row.get(field), after[key].get(field), (key, field))

    def test_protected_upstream_profiles_and_pool_memberships_are_unchanged(self):
        protected = {key for key, row in correction.catalog(self.before).items()
                     if classify(row)['preserve_upstream_source']}
        self.assertEqual(len(protected), 351)
        for pool in ('programs', 'program_inventory'):
            for key in protected:
                self.assertEqual(key in self.before[pool], key in self.after[pool])
                if key in self.before[pool]:
                    self.assertEqual(self.before[pool][key], self.after[pool][key])

    def test_exactly_one_endpoint_group_removed_with_no_fallback(self):
        for old, new in zip(self.before['benchmarks'], self.after['benchmarks']):
            expected = copy.deepcopy(old)
            if old['key'] == 'knucleotide':
                expected['groups'] = [g for g in old['groups'] if g['language'] != 'lean4']
            self.assertEqual(new, expected)
            self.assertEqual(correction.minima(self.before, old), correction.minima(self.after, new))
        for bench in self.after['benchmarks']:
            for group in bench['groups']:
                self.assertTrue(group['programs'])
                self.assertFalse(set(group['programs']) & set(correction.KEYS))

    def test_only_lean4_coverage_and_reference_change_to_nine_workloads(self):
        language = next(l for l in self.after['languages'] if l['key'] == 'lean4')
        self.assertEqual(len(language['timed_benchmarks']), 9)
        self.assertEqual(len(language['source_benchmarks']), 9)
        self.assertEqual(len(language['historically_measured_benchmarks']), 10)
        self.assertEqual(language['unsupported_benchmarks'], ['knucleotide'])
        self.assertEqual(self.before['formatted_reference_summary'], self.after['formatted_reference_summary'])
        for old, new in zip(self.before['languages'], self.after['languages']):
            if old['key'] != 'lean4':
                self.assertEqual(old, new)
        aggregate = correction.language_aggregate(self.after)
        self.assertEqual(aggregate['count'], 9)
        for old, new in zip(self.before['reference_summary'], self.after['reference_summary']):
            if old['lang'] != 'lean4':
                self.assertEqual(old, new)
                continue
            self.assertEqual(len(new['measured_benchmarks']), 9)
            self.assertNotIn('knucleotide', new['measured_benchmarks'])
            for kind in ('fast', 'small'):
                self.assertEqual(new[kind], aggregate[kind])
        marker = self.after[correction.MARKER]
        self.assertEqual(marker['previous_reference_summary'],
                         [r for r in self.before['reference_summary'] if r['lang'] == 'lean4'])

    def test_raw_profiles_remain_inspectable_in_browser_data(self):
        projected = browser_data(self.after)
        for key in correction.KEYS:
            row = projected['program_inventory'][key]
            self.assertIs(row['eligible_for_chart'], False)
            self.assertEqual(row['samples'], self.before['programs'][key]['samples'])
            self.assertEqual(row['exclusion_reason'], correction.REASON)
            for source in row['files']:
                self.assertEqual(projected['files'][source]['code'], self.before['files'][source]['code'])

    def test_applied_catalog_exact_reproduction_and_repeat_rejection(self):
        if correction.MARKER in self.published:
            self.assertEqual(self.after, self.published)
        with self.assertRaisesRegex(ValueError, 'already applied'):
            correction.append_catalog(self.after)

    def test_profile_configuration_or_source_drift_is_rejected(self):
        for field, value in [('loc', 1), ('seconds', 0.1), ('runtime_policy', 'other'),
                             ('required_work_validated', False)]:
            changed, row = self.changed_profile(correction.KEYS[0])
            row[field] = value
            with self.assertRaisesRegex(ValueError, 'Exact retained profile differs'):
                correction.append_catalog(changed)
        changed = dict(self.before, files=dict(self.before['files']))
        changed['files'][correction.FORMAT] = dict(changed['files'][correction.FORMAT], code='changed support')
        with self.assertRaisesRegex(ValueError, 'Catalog source bytes differ'):
            correction.append_catalog(changed)

    def test_new_alias_or_conflicting_inventory_profile_is_rejected(self):
        changed = dict(self.before, program_inventory=dict(self.before['program_inventory']))
        new_key = 'knucleotide:unreviewed-lean4-fallback'
        changed['program_inventory'][new_key] = dict(self.before['programs'][correction.KEYS[0]], key=new_key)
        with self.assertRaisesRegex(ValueError, 'fallback'):
            correction.append_catalog(changed)
        changed = dict(self.before, program_inventory=dict(self.before['program_inventory']))
        changed['program_inventory'][correction.KEYS[0]] = dict(changed['program_inventory'][correction.KEYS[0]], loc=1)
        with self.assertRaisesRegex(ValueError, 'Conflicting profile'):
            correction.append_catalog(changed)

    def test_evidence_tamper_and_changed_endpoint_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / correction.REVIEW
            target.parent.mkdir(parents=True)
            target.write_text('{}\n')
            with self.assertRaisesRegex(ValueError, 'Policy review identity differs'):
                correction.append_catalog(self.before, root)
        changed = dict(self.before, benchmarks=copy.deepcopy(self.before['benchmarks']))
        bench = next(b for b in changed['benchmarks'] if b['key'] == 'knucleotide')
        next(g for g in bench['groups'] if g['language'] == 'lean4')['programs'].reverse()
        with self.assertRaisesRegex(ValueError, 'endpoint group differs'):
            correction.append_catalog(changed)

    def test_serialization_preserves_unrelated_dictionary_order(self):
        fixture = {'z': {'third': 3, 'first': 1}, 'a': 0}
        self.assertEqual(list(json.loads(correction.encoded(fixture))), ['z', 'a'])
        self.assertEqual(list(json.loads(correction.encoded(fixture))['z']), ['third', 'first'])


if __name__ == '__main__':
    unittest.main()
