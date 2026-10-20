"""Exact-scope, preservation and replay checks; no language/runtime execution."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from audit_owned_implementations import classify
from build_site import browser_data
from qualification import apply_futhark_knucleotide_eligibility as correction
from source_accounting import historical_catalog


class FutharkEligibilityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.published = correction.load(correction.ROOT / 'data/benchmarks.json')
        # This suite also remains useful after the guarded apply. Reconstruct
        # only the small additive eligibility transition, then require exact
        # reproduction against the published catalog in a dedicated test.
        cls.before = copy.deepcopy(cls.published)
        if correction.MARKER in cls.before:
            marker = cls.before.pop(correction.MARKER)
            bench = next(b for b in cls.before['benchmarks'] if b['key'] == 'knucleotide')
            old_groups = marker['removed_group']
            # Group order is source evidence too: restore at its saved index.
            bench['groups'].insert(marker['removed_group_index'], old_groups)
            for key in correction.KEYS:
                row = cls.before['program_inventory'].pop(key)
                for field in ('eligible_for_chart', 'exclusion_reason', 'eligibility_correction'):
                    row.pop(field)
                cls.before['programs'][key] = row
            cls.before['exclusions'] = [e for e in cls.before['exclusions'] if e['key'] not in correction.KEYS]
            language = next(l for l in cls.before['languages'] if l['key'] == 'futhark')
            language.clear()
            language.update(marker['previous_language'])
        cls.after = correction.append_catalog(cls.before)

    def test_exactly_two_profiles_become_ineligible_and_remain_retained(self):
        before, after = map(correction.catalog, (self.before, self.after))
        self.assertEqual(before.keys(), after.keys())
        changed = {key for key in before if before[key] != after[key]}
        self.assertEqual(changed, set(correction.KEYS))
        for key in correction.KEYS:
            self.assertNotIn(key, self.after['programs'])
            self.assertIn(key, self.after['program_inventory'])
            row = copy.deepcopy(after[key])
            self.assertIs(row.pop('eligible_for_chart'), False)
            self.assertEqual(row.pop('exclusion_reason'), correction.REASON)
            self.assertEqual(row.pop('eligibility_correction')['source_sha256'], before[key]['files'])
            self.assertEqual(row, before[key])
        new_excluded = {key for key in after if after[key].get('eligible_for_chart') is False
                        and before[key].get('eligible_for_chart') is not False}
        self.assertEqual(new_excluded, set(correction.KEYS))

    def test_all_351_protected_upstream_profiles_and_pool_memberships_unchanged(self):
        protected = {key for key, row in correction.catalog(self.before).items()
                     if classify(row)['preserve_upstream_source']}
        self.assertEqual(len(protected), 351)
        for pool in ('programs', 'program_inventory'):
            for key in protected:
                self.assertEqual(key in self.before[pool], key in self.after[pool])
                if key in self.before[pool]:
                    self.assertEqual(self.before[pool][key], self.after[pool][key], key)

    def test_all_source_records_roles_counts_and_observations_unchanged(self):
        self.assertEqual(self.before['files'], self.after['files'])
        self.assertEqual(self.before['archive_paths'], self.after['archive_paths'])
        for key, old in correction.catalog(self.before).items():
            new = correction.catalog(self.after)[key]
            for field in ('samples', 'seconds', 'timing_sd', 'files', 'loc', 'physical_loc', 'file_roles',
                          'source_accounting', 'authorship', 'algorithm', 'required_work_validated', 'x', 'y'):
                self.assertEqual(old.get(field), new.get(field), (key, field))

    def test_only_one_endpoint_group_removed_and_no_fallback_selected(self):
        for old, new in zip(self.before['benchmarks'], self.after['benchmarks']):
            expected = copy.deepcopy(old)
            if old['key'] == 'knucleotide':
                expected['groups'] = [g for g in old['groups'] if g['language'] != 'futhark']
            self.assertEqual(new, expected)
        for bench in self.after['benchmarks']:
            for group in bench['groups']:
                self.assertTrue(group['programs'])
                self.assertTrue(all(key in self.after['programs'] for key in group['programs']))
                self.assertFalse(set(group['programs']) & set(correction.KEYS))

    def test_coverage_eight_eligible_and_nine_historically_measured(self):
        language = next(l for l in self.after['languages'] if l['key'] == 'futhark')
        self.assertEqual(len(language['timed_benchmarks']), 8)
        self.assertEqual(len(language['source_benchmarks']), 8)
        self.assertEqual(len(language['historically_measured_benchmarks']), 9)
        self.assertEqual(language['unsupported_benchmarks'], ['binarytrees', 'knucleotide'])
        for old, new in zip(self.before['languages'], self.after['languages']):
            if old['key'] != 'futhark':
                self.assertEqual(old, new)

    def test_raw_profiles_and_sources_remain_inspectable_in_browser_data(self):
        projected = browser_data(self.after)
        for key in correction.KEYS:
            row = projected['program_inventory'][key]
            self.assertEqual(row['samples'], self.before['programs'][key]['samples'])
            self.assertIs(row['eligible_for_chart'], False)
            self.assertEqual(row['exclusion_reason'], correction.REASON)
            for source in row['files']:
                self.assertEqual(projected['files'][source]['code'], self.before['files'][source]['code'])

    def test_exact_historical_replay_including_eligibility_override(self):
        self.assertEqual(historical_catalog(correction.ROOT, self.after),
                         historical_catalog(correction.ROOT, self.before))
        if correction.MARKER in self.published:
            self.assertEqual(self.after, self.published)

    def test_repeat_application_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'already applied'):
            correction.append_catalog(self.after)

    def test_profile_config_or_source_drift_is_rejected(self):
        for field, value in [('loc', 38), ('seconds', 0.1), ('runtime_policy', 'other runtime'),
                             ('required_work_validated', False)]:
            changed = copy.deepcopy(self.before)
            changed['programs'][correction.KEYS[0]][field] = value
            with self.assertRaisesRegex(ValueError, 'Exact retained profile differs'):
                correction.append_catalog(changed)
        changed = copy.deepcopy(self.before)
        changed['files'][correction.SUPPORT[-1]]['code'] += '\n'
        with self.assertRaisesRegex(ValueError, 'Catalog source bytes differ'):
            correction.append_catalog(changed)

    def test_new_fallback_or_conflicting_inventory_identity_is_rejected(self):
        changed = copy.deepcopy(self.before)
        bench = next(b for b in changed['benchmarks'] if b['key'] == 'knucleotide')
        next(g for g in bench['groups'] if g['language'] == 'futhark')['programs'].append('unreviewed-fallback')
        with self.assertRaisesRegex(ValueError, 'endpoint group differs'):
            correction.append_catalog(changed)
        changed = copy.deepcopy(self.before)
        changed['program_inventory'][correction.KEYS[0]] = dict(changed['programs'][correction.KEYS[0]], loc=1)
        with self.assertRaisesRegex(ValueError, 'Conflicting profile'):
            correction.append_catalog(changed)

    def test_evidence_snapshot_tamper_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / correction.REVIEW
            target.parent.mkdir(parents=True)
            target.write_text('{}\n')
            with self.assertRaisesRegex(ValueError, 'Policy review identity differs'):
                correction.append_catalog(self.before, root)


if __name__ == '__main__':
    unittest.main()
