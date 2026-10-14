"""Lua target planning and inherited guarded-transaction failure checks."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch


HERE = Path(__file__).parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


a = load('lua_target_tested', HERE/'import_lua_retained_publication_target.py')
prior = load('lua_inherited_target_faults', HERE/'test_import_retained_publication_target.py')
prior.a = a


class Transactions(prior.Transactions):
    def setUp(self):
        super().setUp()
        self.before['archive_paths'] = {'retained': 'retained'}
        (self.publication/prior.OLD.CATALOGS[0]).write_bytes(prior.OLD.encoded(self.before))

    def setup_scope(self, cohort='lua'):
        return super().setup_scope(cohort)


class PublicationLinks(prior.PublicationLinks):
    pass


class LuaBindings(unittest.TestCase):
    def test_original_consumers_are_still_pinned_with_two_explicit_additions(self):
        old, deps = a.load_original(SimpleNamespace(cohort='lua'), a.EVIDENCE_ROOT)
        self.assertEqual(old.ROOT, a.EVIDENCE_ROOT)
        self.assertEqual(deps['pins'][a.EVIDENCE_ROOT/a.DRIVER], a.DRIVER_SHA)
        self.assertEqual(deps['pins'][a.EVIDENCE_ROOT/a.NORMALIZATION], a.NORMALIZATION_SHA)
        self.assertEqual(deps['pins'][a.EVIDENCE_ROOT/'tools/qualification/retained_catalog_publication.py'], old.SHARED_SHA)
        for name, file, digest in (
                ('publication', a.LUA_PUBLICATION, a.LUA_PUBLICATION_SHA),
                ('normalization', a.LUA_NORMALIZATION, a.LUA_NORMALIZATION_SHA)):
            self.assertEqual(Path(deps[name].__file__), a.EVIDENCE_ROOT/file)
            self.assertEqual(deps['pins'][a.EVIDENCE_ROOT/file], digest)
        self.assertEqual(Path(deps['reconciler'].__file__), a.EVIDENCE_ROOT/'tools/qualification/lua_pidigits_reconcile.py')

    def test_wrong_additive_source_pins_and_other_cohort_fail_before_context(self):
        for constant in ('LUA_PUBLICATION_SHA', 'LUA_NORMALIZATION_SHA'):
            with self.subTest(constant=constant), patch.object(a, constant, '0'*64), self.assertRaises(ValueError):
                a.load_original(SimpleNamespace(cohort='lua'), a.EVIDENCE_ROOT)
        with self.assertRaisesRegex(ValueError, 'Only the retained Lua'):
            a.load_original(SimpleNamespace(cohort='r'), a.EVIDENCE_ROOT)

    def test_actual_leaves_plan_absent_aggregate_and_new_portable_history(self):
        old, deps = a.load_original(SimpleNamespace(cohort='lua'), a.EVIDENCE_ROOT)
        fixtures = load('lua_plan_history_fixture', HERE.parent/'test_normalization_history.py')
        candidate, before, _, old_audit = fixtures.Normalization().lua_fixture()
        before['reference_summary'] = [r for r in before['reference_summary'] if r['lang'] != 'lua']
        catalogs = load('lua_plan_catalog_fixture', HERE/'test_retained_catalog_publication.py')
        _, metadata = catalogs.catalog(candidate)
        raw = old.encoded(candidate)
        args = SimpleNamespace(cohort='lua', candidate=a.EVIDENCE_ROOT/old_audit['candidate']['path'],
                               candidate_sha256=a.sha(raw))
        originals = {old.CATALOGS[0]: old.encoded(before), old.CATALOGS[1]: old.encoded(metadata), old.HISTORY: None}
        snapshot = copy.deepcopy(originals)
        n = deps['normalization']; original_checked = n.checked
        reference = dict(path=old_audit['candidate']['path'], sha256=args.candidate_sha256)
        def evidence(root, ref):
            return raw if ref == reference else original_checked(a.EVIDENCE_ROOT, ref)
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory, patch.object(n, 'checked', side_effect=evidence):
            publication = Path(directory)
            data, audit, prepared, applied, success_raw, entry = a.plan_publication(
                old, deps, args, candidate, originals, publication/'fresh-apply', publication, {}, None)
        self.assertEqual(originals, snapshot)
        self.assertIsNone(audit['aggregate_change']['before'])
        self.assertEqual(len(audit['aggregate_change']['after']['measured_benchmarks']), 10)
        self.assertEqual(len([r for r in data['reference_summary'] if r['lang']=='lua']), 1)
        self.assertEqual(json.loads(prepared[old.HISTORY])['admissions'], [entry])
        self.assertEqual(a.sha(success_raw), entry['success']['sha256'])
        self.assertEqual(applied['prior_normalization_history_sha256'], 'absent')
        self.assertFalse((a.EVIDENCE_ROOT/'fresh-apply').exists())


if __name__ == '__main__':
    unittest.main()
