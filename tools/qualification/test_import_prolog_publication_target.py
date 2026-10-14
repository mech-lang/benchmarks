"""Small synthetic publication transactions; no native or full evidence replay."""
import copy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location('prolog_target_tested', Path(__file__).with_name('import_prolog_publication_target.py'))
a = importlib.util.module_from_spec(spec)
spec.loader.exec_module(a)
ORIGINAL = a.load_original(a.EVIDENCE_ROOT)


class TargetPublication(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir='/private/tmp')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.evidence, self.publication = self.base/'evidence', self.base/'publication'
        self.evidence.mkdir(); self.publication.mkdir()
        self.events = []; self.fail_final = False; self.final_mutation = None

        def put(relative, raw, copy_to_target=True):
            path = self.evidence/relative
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
            if copy_to_target:
                target = self.publication/relative
                target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
            return path, a.digest(raw)
        self.put = put
        source, source_sha = put('sources/prolog/example.pl', b'main :- write(ok).\n')
        receipt, receipt_sha = put('experiments/prolog/prior/process.json', b'{"exit":0}\n')
        self.source = source; self.source_sha = source_sha
        self.candidate = dict(files={source_sha: dict(code=source.read_text(), sha256=source_sha,
                                                   archive_path='sources/prolog/example.pl')},
                              receipt=dict(path=str(receipt), sha256=receipt_sha))
        self.fresh = dict(verified_file_pins={str(source): source_sha}, scope='synthetic-future-only')
        self.paths = {}
        for name, document in (('candidate', self.candidate), ('metadata', self.fresh), ('reconciliation', {'qualified': True})):
            self.paths[name] = put(a.PACKET_REL+'/'+name+'.json', json.dumps(document).encode())
        plan, plan_sha = put(a.PACKET_REL+'/plan.json', b'{}')
        prior, prior_sha = put('experiments/prolog/prior/plan-v1.json', b'{}')
        previous, previous_sha = put('experiments/prolog/old/plan-v1.json', b'{}')
        exporter, exporter_sha = put('tools/qualification/prolog_remaining_export.py', b'synthetic exporter')
        release, release_sha = put('experiments/prolog/release.json', b'{}')
        traits, traits_sha = put('site/src/traits.mjs', b'synthetic traits')
        put(a.IMPORTER_REL, (a.EVIDENCE_ROOT/a.IMPORTER_REL).read_bytes())
        adapter, adapter_sha = put(a.ADAPTER_REL, b'synthetic adapter')
        self.before = {name: ('original '+name).encode() for name in a.TARGETS}
        self.after = {name: ('prepared '+name).encode() for name in a.TARGETS}
        for name, raw in self.before.items():
            target = self.publication/name
            target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(raw)
        l = SimpleNamespace(PLAN=plan, PLAN_SHA=plan_sha, PRIOR=prior.parent, PRIOR_PLAN_SHA=prior_sha,
                            l=SimpleNamespace(OLD_REFS={'plan': (previous, previous_sha)}),
                            JOB=self.evidence/'job', PRIOR_JOB=self.evidence/'priorjob', OLD=self.evidence/'old')
        lock = self.evidence/'common.lock'
        for path in (l.JOB/'owner.lock', l.PRIOR_JOB/'owner.lock', l.OLD/'owned-jobs/full90/owner.lock',
                     self.evidence/'experiments/prolog/prolog-full90.owner.lock', lock):
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(b'')

        @contextmanager
        def context(path, expected, *, on_exit_failure, final_consumer_check):
            self.events.append('leases-held')
            try:
                yield copy.deepcopy(self.fresh)
                self.events.append('final-evidence-replay')
                try:
                    if self.final_mutation:
                        self.final_mutation()
                    if self.fail_final:
                        raise ValueError('synthetic final evidence drift')
                    final_consumer_check()
                except BaseException:
                    on_exit_failure()
                    self.events.append('restored-before-release')
                    raise
            finally:
                self.events.append('leases-released')

        def reproduce(plan, prior, previous, review, fresh, read_raw, *refs):
            read_raw(str(source), source_sha)
            return copy.deepcopy(self.candidate)

        def build(originals, candidate, release, refs, plan, *, root):
            self.assertEqual(root, self.evidence)
            self.assertEqual(originals, self.before)
            self.assertEqual(candidate, self.candidate)
            self.assertEqual(refs['import_controller']['path'], a.ADAPTER_REL)
            return dict(self.after), dict(status='synthetic-preview', baseline_changed=False)

        self.old = SimpleNamespace(
            e=SimpleNamespace(checked=ORIGINAL.e.checked, ref=ORIGINAL.e.ref, reproduced_candidate=reproduce),
            m=SimpleNamespace(review_context=context), l=l, r=SimpleNamespace(LOCK=lock), p=ORIGINAL.p,
            EXPORTER=exporter, EXPORTER_SHA=exporter_sha, RELEASE=release, RELEASE_SHA=release_sha,
            TRAITS=traits, TRAITS_SHA=traits_sha, public_ref=ORIGINAL.public_ref, same=ORIGINAL.same,
            build_publication=build, atomic_publication=ORIGINAL.atomic_publication,
            verify_written=ORIGINAL.verify_written, restore_prepared=ORIGINAL.restore_prepared,
            apply_prepared=ORIGINAL.apply_prepared)
        self.args = SimpleNamespace(evidence_root=self.evidence, publication_root=self.publication,
            adapter_sha256=adapter_sha, output=self.base/'private-preview', apply=False,
            benchmarks_sha256=a.digest(self.before[a.TARGETS[0]]),
            languages_sha256=a.digest(self.before[a.TARGETS[1]]), module_sha256=a.digest(self.before[a.TARGETS[2]]))
        for name, (path, expected) in self.paths.items():
            setattr(self.args, name, path); setattr(self.args, name+'_sha256', expected)
        self.patches = [patch.object(a, 'EVIDENCE_ROOT', self.evidence), patch.object(a, '__file__', str(adapter)),
                        patch.object(a, 'load_original', return_value=self.old)]
        for item in self.patches:
            item.start(); self.addCleanup(item.stop)

    def assert_original_targets(self):
        for name, raw in self.before.items():
            self.assertEqual((self.publication/name).read_bytes(), raw)

    def test_preview_only_changes_private_output(self):
        result = a.publish(self.args)
        self.assertFalse(result['applied']); self.assert_original_targets()
        self.assertEqual(result['evidence_root'], str(self.evidence))
        self.assertEqual(result['publication_root'], str(self.publication))
        for name in a.TARGETS:
            self.assertEqual((self.args.output/name).read_bytes(), self.after[name])
            self.assertEqual((self.args.output/'originals'/name).read_bytes(), self.before[name])
        self.assertEqual(self.events[-2:], ['final-evidence-replay', 'leases-released'])

    def test_apply_uses_only_publication_targets(self):
        self.args.apply = True
        result = a.publish(self.args)
        self.assertTrue(result['applied'])
        for name, raw in self.after.items():
            self.assertEqual((self.publication/name).read_bytes(), raw)
            self.assertFalse((self.evidence/name).exists())

    def test_wrong_evidence_root_or_overlap_rejected(self):
        self.args.evidence_root = self.publication
        with self.assertRaisesRegex(ValueError, 'Original measurement'):
            a.publish(self.args)
        self.args.evidence_root = self.evidence; self.args.publication_root = self.evidence
        with self.assertRaisesRegex(ValueError, 'disjoint'):
            a.publish(self.args)

    def test_candidate_from_publication_checkout_rejected(self):
        self.args.candidate = self.publication/self.args.candidate.relative_to(self.evidence)
        with self.assertRaisesRegex(ValueError, 'original additive packet'):
            a.publish(self.args)

    def test_original_importer_pin_drift_rejected_before_outputs(self):
        (self.evidence/a.IMPORTER_REL).write_bytes(b'changed original importer')
        with self.assertRaisesRegex(ValueError, 'Pinned bytes differ'):
            a.publish(self.args)
        self.assertFalse(self.args.output.exists()); self.assert_original_targets()

    def test_missing_inherited_source_pin_rejected(self):
        self.fresh['verified_file_pins'].clear()
        raw = json.dumps(self.fresh).encode(); self.args.metadata.write_bytes(raw)
        self.args.metadata_sha256 = a.digest(raw)
        with self.assertRaisesRegex(ValueError, 'Unverified publication input'):
            a.publish(self.args)

    def test_copied_source_or_receipt_mismatch_rejected(self):
        for relative in ('sources/prolog/example.pl', 'experiments/prolog/prior/process.json', 'site/src/traits.mjs'):
            with self.subTest(relative=relative):
                copied = self.publication/relative; original = copied.read_bytes()
                copied.write_bytes(b'editorially changed')
                with self.assertRaisesRegex(ValueError, 'Pinned bytes differ'):
                    a.publish(self.args)
                copied.write_bytes(original)
                self.assertFalse(self.args.output.exists())

    def test_changed_or_symlinked_target_rejected(self):
        target = self.publication/a.TARGETS[0]
        target.write_bytes(b'changed catalog')
        with self.assertRaisesRegex(ValueError, 'Pinned bytes differ'):
            a.publish(self.args)
        alternate = self.base/'same-catalog'; alternate.write_bytes(self.before[a.TARGETS[0]])
        target.unlink(); target.symlink_to(alternate)
        with self.assertRaisesRegex(ValueError, 'Symlinked'):
            a.publish(self.args)

    def test_late_context_failure_restores_before_lease_release(self):
        self.args.apply = True; self.fail_final = True
        with self.assertRaisesRegex(ValueError, 'final evidence drift'):
            a.publish(self.args)
        self.assert_original_targets(); self.assertFalse(self.args.output.exists())
        self.assertEqual(self.events[-2:], ['restored-before-release', 'leases-released'])

    def test_late_copied_link_change_restores_targets(self):
        self.args.apply = True
        copied = self.publication/'sources/prolog/example.pl'
        self.final_mutation = lambda: copied.write_bytes(b'external edit')
        with self.assertRaisesRegex(ValueError, 'Pinned bytes differ'):
            a.publish(self.args)
        self.assert_original_targets(); self.assertEqual(copied.read_bytes(), b'external edit')
        self.assertFalse(self.args.output.exists())

    def test_late_receipt_mutation_cannot_claim_success(self):
        self.args.apply = True
        self.final_mutation = lambda: (self.args.output/'import-receipt.json').write_bytes(b'{}')
        with self.assertRaises(BaseExceptionGroup):
            a.publish(self.args)
        self.assert_original_targets()
        self.assertEqual((self.args.output/'import-receipt.json').read_bytes(), b'{}')

    def test_missing_target_does_not_prevent_other_restoration(self):
        self.args.apply = True
        missing = self.publication/a.TARGETS[1]
        self.final_mutation = missing.unlink
        with self.assertRaises(BaseExceptionGroup):
            a.publish(self.args)
        self.assertFalse(missing.exists())
        for name in (a.TARGETS[0], a.TARGETS[2]):
            self.assertEqual((self.publication/name).read_bytes(), self.before[name])
        self.assertFalse(self.args.output.exists())

    def test_apply_return_gap_preserves_persistent_journal(self):
        self.args.apply = True
        def interrupted(*args):
            ORIGINAL.apply_prepared(*args)
            raise KeyboardInterrupt('synthetic apply return gap')
        self.old.apply_prepared = interrupted
        with self.assertRaises(KeyboardInterrupt):
            a.publish(self.args)
        self.assert_original_targets(); self.assertFalse(self.args.output.exists())


class OriginalBindings(unittest.TestCase):
    def test_real_source_import_keeps_all_original_roots(self):
        for module in (ORIGINAL, ORIGINAL.e, ORIGINAL.m, ORIGINAL.l, ORIGINAL.r):
            self.assertEqual(getattr(module, 'ROOT', a.EVIDENCE_ROOT), a.EVIDENCE_ROOT)
            self.assertEqual(Path(module.__file__).resolve().parents[2], a.EVIDENCE_ROOT)
        self.assertEqual(Path(ORIGINAL.__file__), a.EVIDENCE_ROOT/a.IMPORTER_REL)

    def test_importer_rejects_an_alternative_evidence_root(self):
        with self.assertRaisesRegex(ValueError, 'Original measurement'):
            a.load_original(Path('/private/tmp/other-checkout'))


if __name__ == '__main__':
    unittest.main()
