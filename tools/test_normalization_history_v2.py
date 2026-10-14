"""Preserve prior admission replays and qualify Lua's first saved aggregate.

Only small saved evidence and synthetic catalog snapshots are read. No current
catalog, runtime closure, native subject or publication file phase is used.
"""
import copy
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


HERE = Path(__file__).resolve().parent


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE/filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


n = load('normalization_v2_under_test', 'normalization_history_v2.py')
prior = load('normalization_v1_regressions', 'test_normalization_history.py')
prior.n = n


class PriorAdmissions(prior.Normalization):
    """All earlier Uiua/R/APL/Lua checks run against the additive helper."""


class FirstLuaAggregate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = prior.Normalization().lua_fixture()

    def values(self):
        candidate, before, after, audit = copy.deepcopy(self.fixture)
        previous = next(ref for ref in before['reference_summary'] if ref['lang'] == 'lua')
        before['reference_summary'] = [ref for ref in before['reference_summary'] if ref['lang'] != 'lua']
        audit['aggregate_change']['before'] = None
        after['lua_retained_publication_audit'] = copy.deepcopy(audit)
        return candidate, before, after, audit, previous

    def check(self, candidate, before, after, audit):
        raw = prior.encode(candidate)
        real_checked = n.checked
        def evidence(root, reference):
            return raw if reference == audit['candidate'] else real_checked(HERE.parent, reference)
        with patch.object(n, 'checked', side_effect=evidence):
            added, refs = n.validate_lua(HERE.parent, audit, before, after)
            boundaries = n.validate_transition(before, after, audit, added, refs)
        return added, refs, boundaries

    def test_nine_measured_groups_without_saved_aggregate_add_only_lua_reference(self):
        candidate, before, after, audit, _ = self.values()
        original = copy.deepcopy(before)
        added, refs, boundaries = self.check(candidate, before, after, audit)
        self.assertEqual(refs, {'lua'})
        self.assertEqual((len(added['programs']), len(added['program_inventory'])), (2, 4))
        self.assertEqual(boundaries, [])
        self.assertIsNone(audit['aggregate_change']['before'])
        self.assertEqual(before, original, 'No historical aggregate may be invented.')
        self.assertEqual(len(audit['aggregate_change']['after']['measured_benchmarks']), 10)
        old_jit = [ref for ref in before['reference_summary'] if ref['lang'] == 'luajit']
        self.assertEqual(old_jit, [ref for ref in after['reference_summary'] if ref['lang'] == 'luajit'])

    def test_present_reference_stays_exact_and_duplicate_references_fail(self):
        candidate, before, after, audit = copy.deepcopy(self.fixture)
        _, refs, _ = self.check(candidate, before, after, audit)
        self.assertEqual(refs, set())
        previous = next(ref for ref in before['reference_summary'] if ref['lang'] == 'lua')
        before['reference_summary'].append(copy.deepcopy(previous))
        with self.assertRaises(ValueError):
            self.check(candidate, before, after, audit)

    def test_absent_reference_does_not_excuse_coverage_raw_or_aggregate_faults(self):
        faults = ('fake_prior', 'missing_coverage', 'duplicate_coverage', 'missing_group',
                  'wrong_label', 'aggregate_x', 'aggregate_y', 'duplicate_new_ref',
                  'new_unrelated_ref', 'luajit', 'raw_sample', 'minimum')
        for fault in faults:
            candidate, before, after, audit, previous = self.values()
            reference = next(ref for ref in after['reference_summary'] if ref['lang'] == 'lua')
            if fault == 'fake_prior':
                audit['aggregate_change']['before'] = previous
            elif fault in ('missing_coverage', 'duplicate_coverage'):
                entry = next(row for row in before['languages'] if row['key'] == 'lua')
                if fault == 'missing_coverage': entry['timed_benchmarks'].pop()
                else: entry['timed_benchmarks'][-1] = entry['timed_benchmarks'][0]
            elif fault == 'missing_group':
                before['benchmarks'][0]['groups'] = [g for g in before['benchmarks'][0]['groups'] if g['language'] != 'lua']
            elif fault == 'wrong_label':
                reference['label'] = 'Unreviewed label'
                audit['aggregate_change']['after'] = copy.deepcopy(reference)
            elif fault in ('aggregate_x', 'aggregate_y'):
                reference['fast'][fault[-1]] *= 2
                audit['aggregate_change']['after'] = copy.deepcopy(reference)
            elif fault == 'duplicate_new_ref':
                after['reference_summary'].append(copy.deepcopy(reference))
            elif fault == 'new_unrelated_ref':
                after['reference_summary'].append(dict(reference, lang='unrelated'))
            elif fault == 'luajit':
                next(ref for ref in after['reference_summary'] if ref['lang'] == 'luajit')['fast']['y'] *= 2
            elif fault == 'raw_sample':
                after['program_inventory']['pidigits:lua-interpreted-gmp-listed-1']['samples'][0] += 1
            else:
                before['benchmarks'][-1]['baseline_loc'] = 300
            after['lua_retained_publication_audit'] = copy.deepcopy(audit)
            with self.subTest(fault=fault), self.assertRaises(ValueError):
                self.check(candidate, before, after, audit)

    def test_saved_first_aggregate_replays_portably_and_checks_current_state(self):
        candidate, before, after, audit, _ = self.values()
        raw = prior.encode(candidate)
        real_checked = n.checked
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entry = prior.saved(root, before, after, audit,
                                key='lua_retained_publication_audit', folder='lua')
            prior.write(root, n.HISTORY,
                        dict(schema='canonical-loc-normalization-history-v1', admissions=[entry]))
            def evidence(target, reference):
                if reference == audit['candidate']: return raw
                if reference in [dict(path=p, sha256=d) for p, d in n.LUA_PINS.values()]:
                    return real_checked(HERE.parent, reference)
                return real_checked(target, reference)
            with patch.object(n, 'checked', side_effect=evidence):
                self.assertEqual(n.historical_view(root, after), after)
                for fault in ('aggregate', 'endpoint', 'source'):
                    changed = copy.deepcopy(after)
                    if fault == 'aggregate':
                        next(ref for ref in changed['reference_summary'] if ref['lang'] == 'lua')['small']['y'] *= 2
                    elif fault == 'endpoint':
                        group = next(g for g in changed['benchmarks'][-1]['groups'] if g['language'] == 'lua')
                        group['programs'].append(group['programs'][0])
                    else:
                        changed['files'][n.LUA_HELPER]['code'] += 'changed'
                    with self.subTest(fault=fault), self.assertRaises(ValueError):
                        n.historical_view(root, changed)

    def test_original_validator_bytes_remain_frozen(self):
        self.assertEqual(hashlib.sha256((HERE/'normalization_history.py').read_bytes()).hexdigest(),
                         'f22249bc06a18b84cf45f6e4de50061575fc6ae640fa0c380bf01ad0a4c9bfa0')


if __name__ == '__main__':
    unittest.main()
