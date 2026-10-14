"""Pure metadata/pin checks; no mutex, runtime closure, native command or output."""
import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch


PATH = Path(__file__).with_name('elixir_loc_qualify.py')
SPEC = importlib.util.spec_from_file_location('elixir_loc_qualification_tests', PATH)
q = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(q)


class QualificationChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = q.read(q.PLAN)
        cls.replay = q.read(q.REPLAY)

    def inputs(self):
        return copy.deepcopy(self.plan), copy.deepcopy(self.replay)

    def test_reviewed_twenty_bundles_and_sixty_inputs(self):
        files, profiles, aliases = q.reviewed_counts(self.plan, self.replay)
        self.assertEqual((len(files), len(profiles), len(aliases)), (60, 20, 10))
        for profile in profiles:
            self.assertEqual(profile['canonical_loc'], q.EXPECTED[profile['benchmark']][1])
            self.assertIs(profile['canonical_loc_qualified'], True)
            self.assertIs(profile['formatted_loc_qualified'], True)
            for name in ('source_work_qualified', 'full_timings_qualified', 'chart_admission'):
                self.assertIs(profile[name], False)

    def test_failed_native_fixture_rejects(self):
        plan, replay = self.inputs()
        replay['fixture_checks'][0]['passed'] = False
        with self.assertRaisesRegex(AssertionError, 'fixture expectations'):
            q.reviewed_counts(plan, replay)

    def test_duplicate_native_fixture_rejects(self):
        plan, replay = self.inputs()
        replay['fixture_checks'][0]['id'] = replay['fixture_checks'][1]['id']
        with self.assertRaisesRegex(AssertionError, 'fixture identities'):
            q.reviewed_counts(plan, replay)

    def test_wrong_manual_canonical_total_rejects(self):
        plan, replay = self.inputs()
        first = replay['profiles'][0]
        replay['files'][first['inputs'][0]]['original']['normalized_loc'] += 1
        first['candidate_canonical_loc'] += 1
        with self.assertRaisesRegex(AssertionError, 'independent original-source review'):
            q.reviewed_counts(plan, replay)

    def test_wrong_formatted_total_rejects(self):
        plan, replay = self.inputs()
        first = replay['files'][replay['profiles'][0]['inputs'][0]]
        first['formatted']['physical_loc'] += 1
        first['candidate_formatted_loc'] += 1
        with self.assertRaisesRegex(AssertionError, 'independent original-source review'):
            q.reviewed_counts(plan, replay)

    def test_source_identity_mismatch_rejects(self):
        plan, replay = self.inputs()
        replay['files'][replay['profiles'][0]['inputs'][0]]['source_sha256'] = '0'*64
        with self.assertRaisesRegex(AssertionError, 'Source-count identity'):
            q.reviewed_counts(plan, replay)

    def test_missing_counted_role_rejects(self):
        plan, replay = self.inputs()
        plan['inputs'][0]['role'] = 'application-helper'
        with self.assertRaisesRegex(AssertionError, 'counted source role'):
            q.reviewed_counts(plan, replay)

    def test_repeated_profile_input_rejects(self):
        plan, replay = self.inputs()
        plan['profiles'][0]['inputs'][0] = plan['profiles'][0]['inputs'][1]
        with self.assertRaisesRegex(AssertionError, 'input membership'):
            q.reviewed_counts(plan, replay)

    def test_missing_form_rejects(self):
        plan, replay = self.inputs()
        replay['profiles'].pop()
        with self.assertRaisesRegex(AssertionError, 'twenty retained forms'):
            q.reviewed_counts(plan, replay)

    def test_equivalent_source_pair_mismatch_rejects(self):
        plan, replay = self.inputs()
        item = plan['inputs'][0]
        item['sha256'] = '0'*64
        replay['files'][item['id']]['source_sha256'] = item['sha256']
        with self.assertRaisesRegex(AssertionError, 'equivalent-source pair'):
            q.reviewed_counts(plan, replay)

    def test_ownership_diagnostic_rejects(self):
        plan, replay = self.inputs()
        replay['files'][replay['profiles'][0]['inputs'][0]]['original']['diagnostics'] = [{'kind': 'ambiguous'}]
        with self.assertRaisesRegex(AssertionError, 'ambiguous or invalid'):
            q.reviewed_counts(plan, replay)

    def test_reviewed_module_is_bound_before_execution(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)/'reviewed.py'
            raw = b'VALUE = 7\n'
            path.write_bytes(raw)
            digest = hashlib.sha256(raw).hexdigest()
            self.assertEqual(q.module(path, digest).VALUE, 7)
            path.write_text("raise RuntimeError('Changed helper executed')\n")
            with self.assertRaisesRegex(AssertionError, 'Reviewed helper changed'):
                q.module(path, digest)

    def test_replaced_common_lock_path_rejects(self):
        lock = Mock()
        opened = SimpleNamespace(st_dev=1, st_ino=q.LOCK_INODE)
        changed = SimpleNamespace(st_dev=1, st_ino=q.LOCK_INODE+1)
        with patch.object(q.os, 'fstat', return_value=opened), patch.object(q, 'LOCK') as path:
            path.stat.return_value = opened
            q.verify_lock(lock)
            path.stat.return_value = changed
            with self.assertRaisesRegex(AssertionError, 'Common mutex changed'):
                q.verify_lock(lock)


if __name__ == '__main__':
    unittest.main()
