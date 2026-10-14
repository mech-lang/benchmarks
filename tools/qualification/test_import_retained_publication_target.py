"""Synthetic target transactions using the frozen journal and owned-file writer."""
import copy
from contextlib import contextmanager
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import patch


spec = importlib.util.spec_from_file_location('retained_target_tested', Path(__file__).with_name('import_retained_publication_target.py'))
a = importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
OLD, DEPS = a.load_original(SimpleNamespace(cohort='uiua-fann'), a.EVIDENCE_ROOT)


class Transactions(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir='/private/tmp'); self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.evidence = self.base/'evidence'; self.publication = self.base/'publication'
        self.evidence.mkdir(); self.publication.mkdir()
        self.events = []; self.late = None; self.fail_final = False; self.history_root_reads = []
        self.count = 0
        self.before = {'reference_summary': [], 'programs': {}, 'program_inventory': {}, 'clean_note': 'Public policy.'}
        self.languages = {'languages': {}, 'clean_note': 'Public classifications.'}
        for name, value in zip(OLD.CATALOGS, (self.before, self.languages)):
            path = self.publication/name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(OLD.encoded(value))
        self.put(a.DRIVER, (a.EVIDENCE_ROOT/a.DRIVER).read_bytes())
        self.adapter, self.adapter_sha = self.put(a.ADAPTER, b'synthetic target adapter')
        self.tool, self.tool_sha = self.put('tools/qualification/synthetic_consumer.py', b'synthetic frozen consumer')
        self.source, self.source_sha = self.put('sources/retained/example.txt', b'authored source\n')
        self.report, self.report_sha = self.put('experiments/retained/report.json', b'{"observations":3}')
        self.root_patch = patch.object(a, 'EVIDENCE_ROOT', self.evidence); self.root_patch.start(); self.addCleanup(self.root_patch.stop)
        self.file_patch = patch.object(a, '__file__', str(self.adapter)); self.file_patch.start(); self.addCleanup(self.file_patch.stop)

    def put(self, relative, raw):
        for root in (self.evidence, self.publication):
            path = root/relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        return self.evidence/relative, a.sha(raw)

    def setup_scope(self, cohort='r'):
        self.count += 1
        spec = dict(OLD.COHORTS[cohort]); key = spec['audit_key']; language = spec['language']
        source = dict(sha256=self.source_sha, path=self.source.relative_to(self.evidence).as_posix(), code=self.source.read_text())
        candidate = dict(files={self.source_sha: source}, program_inventory={cohort+':one': {'language': language}},
                         report=dict(path=self.report.relative_to(self.evidence).as_posix(), sha256=self.report_sha))
        path, pin = self.put(spec['packet']+'/export/candidate.json', OLD.encoded(candidate))
        packet = self.publication/spec['packet']
        args = SimpleNamespace(evidence_root=self.evidence, publication_root=self.publication, cohort=cohort,
            mode='preview', candidate=path, candidate_sha256=pin, adapter_sha256=self.adapter_sha,
            output=packet/f'preview-{self.count}', apply_output=packet/f'apply-{self.count}')

        class Files:
            def verify(self, path, expected):
                if a.sha(Path(path).read_bytes()) != expected:
                    raise ValueError('synthetic original evidence pin changed')

        @contextmanager
        def context(*args, on_exit_failure, final_consumer_check):
            self.events.append('held')
            try:
                yield ({'synthetic': True}, Files()) if cohort != 'lua' else ({'synthetic': True}, Files(), {})
            except BaseException:
                on_exit_failure(); raise
            finally:
                try:
                    self.events.append('final-evidence')
                    if self.late:
                        self.late()
                    if self.fail_final:
                        raise ValueError('synthetic late evidence failure')
                    final_consumer_check()
                except BaseException:
                    on_exit_failure(); self.events.append('restored'); raise
                finally:
                    self.events.append('released')

        def reproduce(actual_args, deps, review, read):
            self.assertEqual(actual_args.candidate, path)
            read(self.source, self.source_sha)
            return json.loads(read(path, pin))

        def build(before, metadata, actual_candidate, candidate_ref, **options):
            self.assertEqual(actual_candidate, candidate)
            data, meta = copy.deepcopy(before), copy.deepcopy(metadata)
            identity = cohort+':one'
            data['programs'][identity] = candidate['program_inventory'][identity]
            data['program_inventory'][identity] = candidate['program_inventory'][identity]
            data['reference_summary'].append({'lang': language})
            audit = dict(endpoints={'work': {'programs': [identity]}}, candidate=candidate_ref)
            data[key] = audit
            meta['languages'][cohort] = {'count': 1}
            return data, meta, audit

        def history(root, data):
            self.history_root_reads.append(root)
            self.assertEqual(root, self.publication)
            current = root/OLD.HISTORY
            if current.exists():
                registry = json.loads(current.read_bytes())
                for entry in registry['admissions']:
                    success = root/entry['success']['path']; raw = success.read_bytes()
                    if a.sha(raw) != entry['success']['sha256']:
                        raise ValueError('synthetic target SUCCESS changed')
                    saved = json.loads(raw)
                    for phase, field in (('before', 'originals'), ('after', 'prepared')):
                        for name, expected in saved[field].items():
                            if a.sha((success.parent/phase/name).read_bytes()) != expected:
                                raise ValueError('synthetic target history snapshot changed')
                    if data[entry['audit_key']] != saved['audit']:
                        raise ValueError('synthetic target history audit changed')
            return data

        def scope(root, audit, before, after):
            self.assertEqual(root, self.publication)
            self.assertEqual(json.loads((root/audit['candidate']['path']).read_bytes()), candidate)
            refs = set() if any(row['lang'] == language for row in before['reference_summary']) else {language}
            return {'programs': {cohort+':one'}, 'program_inventory': {cohort+':one'}}, refs

        normalization = SimpleNamespace(strict_json=json.loads, historical_view=history,
            validate_registry=lambda value: value, validate_transition=lambda *args: None,
            additions_by_pool=DEPS['normalization'].additions_by_pool, ADAPTERS={key: scope})
        reconciler = SimpleNamespace(review_context=context, review_files=context)
        deps = dict(spec=spec, reconciler=reconciler, normalization=normalization,
                    writer=DEPS['writer'], publication=SimpleNamespace(build_publication=build),
                    pins={self.evidence/a.DRIVER: a.DRIVER_SHA, self.tool: self.tool_sha})
        old = SimpleNamespace(CATALOGS=OLD.CATALOGS, TARGETS=OLD.TARGETS, HISTORY=OLD.HISTORY,
            snapshot=OLD.snapshot, check_state=OLD.check_state, encoded=OLD.encoded, Journal=OLD.Journal,
            reproduce=reproduce, validate_apl_runtime=lambda *args: None)
        self.loader = patch.object(a, 'load_original', return_value=(old, deps)); self.loader.start(); self.addCleanup(self.loader.stop)
        self.old, self.deps, self.args = old, deps, args
        return args

    def apply_args(self):
        preview = a.publish(self.args)
        args = copy.copy(self.args); args.mode = 'apply'; args.output = args.apply_output; args.apply_output = None
        for name, suffix in zip(OLD.TARGETS, ('catalog', 'languages', 'history')):
            setattr(args, 'expected_'+suffix+'_sha256', preview['originals'][name])
            setattr(args, 'expected_prepared_'+suffix+'_sha256', preview['prepared'][name])
        self.args = args
        return preview

    def test_preview_preserves_current_metadata_and_creates_only_target_artifacts(self):
        self.setup_scope(); result = a.publish(self.args)
        self.assertFalse(result['catalog_changed'])
        self.assertEqual(json.loads((self.publication/OLD.CATALOGS[0]).read_bytes()), self.before)
        prepared = json.loads((self.args.output/'after'/OLD.CATALOGS[0]).read_bytes())
        self.assertEqual(prepared['clean_note'], self.before['clean_note'])
        self.assertFalse((self.evidence/self.args.output.relative_to(self.publication)).exists())
        self.assertFalse((self.publication/OLD.HISTORY).exists())

    def test_successful_apply_binds_registry_and_keeps_evidence_catalog_absent(self):
        self.setup_scope(); preview = self.apply_args(); result = a.publish(self.args)
        self.assertTrue(result['catalog_changed'])
        self.assertEqual(a.sha((self.args.output/'SUCCESS.json').read_bytes()), preview['proposed_apply']['sha256'])
        self.assertTrue((self.publication/OLD.HISTORY).exists())
        self.assertTrue(all(not (self.evidence/name).exists() for name in OLD.TARGETS))

    def test_second_admission_uses_target_only_prior_history(self):
        self.setup_scope('uiua-fann'); self.apply_args(); first = a.publish(self.args)
        first_path = self.publication/first['receipt_path']
        self.loader.stop(); self.setup_scope('r'); self.apply_args(); a.publish(self.args)
        self.assertFalse((self.evidence/first_path.relative_to(self.publication)).exists())
        history = json.loads((self.publication/OLD.HISTORY).read_bytes())
        self.assertEqual(len(history['admissions']), 2)
        self.assertTrue(all(root == self.publication for root in self.history_root_reads))

    def test_wrong_or_overlapping_roots_rejected(self):
        self.setup_scope(); self.args.evidence_root = self.publication
        with self.assertRaisesRegex(ValueError, 'Original measurement'):
            a.publish(self.args)
        self.args.evidence_root = self.evidence; self.args.publication_root = self.evidence
        with self.assertRaisesRegex(ValueError, 'disjoint'):
            a.publish(self.args)

    def test_original_consumer_pin_drift_rejected(self):
        self.setup_scope(); self.tool.write_bytes(b'altered consumer')
        with self.assertRaisesRegex(ValueError, 'pin changed'):
            a.publish(self.args)
        self.assertFalse(self.args.output.exists())

    def test_changed_copied_source_receipt_or_consumer_rejected(self):
        self.setup_scope()
        for original in (self.source, self.report, self.tool):
            target = self.publication/original.relative_to(self.evidence); raw = target.read_bytes()
            with self.subTest(target=str(target)):
                target.write_bytes(b'changed target copy')
                with self.assertRaisesRegex(ValueError, 'Pinned bytes differ'):
                    a.publish(self.args)
                target.write_bytes(raw)
                self.assertFalse(self.args.output.exists())

    def test_candidate_must_be_original_packet_file(self):
        self.setup_scope(); self.args.candidate = self.publication/self.args.candidate.relative_to(self.evidence)
        with self.assertRaisesRegex(ValueError, 'escaped repository'):
            a.publish(self.args)

    def test_six_apply_digests_are_required_and_enforced(self):
        self.setup_scope(); self.apply_args(); self.args.expected_prepared_history_sha256 = ''
        with self.assertRaisesRegex(ValueError, 'six exact'):
            a.publish(self.args)
        self.args.expected_prepared_history_sha256 = '0'*64
        with self.assertRaisesRegex(ValueError, 'Prepared bytes differ'):
            a.publish(self.args)
        self.assertFalse(self.args.output.exists())

    def test_target_edit_after_preview_rejected(self):
        self.setup_scope(); self.apply_args()
        (self.publication/OLD.CATALOGS[1]).write_bytes(b'{"external":true}')
        with self.assertRaisesRegex(ValueError, 'Original differs'):
            a.publish(self.args)

    def test_late_failure_restores_absent_registry_before_release(self):
        self.setup_scope(); self.apply_args(); self.fail_final = True
        with self.assertRaisesRegex(ValueError, 'late evidence'):
            a.publish(self.args)
        self.assertEqual(json.loads((self.publication/OLD.CATALOGS[0]).read_bytes()), self.before)
        self.assertFalse((self.publication/OLD.HISTORY).exists())
        self.assertFalse((self.args.output/'SUCCESS.json').exists())
        self.assertEqual(self.events[-2:], ['restored', 'released'])

    def test_late_success_edit_is_preserved_but_targets_restore(self):
        self.setup_scope(); self.apply_args()
        self.late = lambda: (self.args.output/'SUCCESS.json').write_bytes(b'{}')
        with self.assertRaises(BaseExceptionGroup):
            a.publish(self.args)
        self.assertFalse((self.publication/OLD.HISTORY).exists())
        self.assertEqual(json.loads((self.publication/OLD.CATALOGS[0]).read_bytes()), self.before)
        self.assertEqual((self.args.output/'SUCCESS.json').read_bytes(), b'{}')

    def test_late_history_edit_preserves_external_bytes_and_restores_other_targets(self):
        self.setup_scope(); self.apply_args()
        self.late = lambda: (self.publication/OLD.HISTORY).write_bytes(b'{"external":true}')
        with self.assertRaises(BaseExceptionGroup):
            a.publish(self.args)
        self.assertEqual((self.publication/OLD.HISTORY).read_bytes(), b'{"external":true}')
        self.assertEqual(json.loads((self.publication/OLD.CATALOGS[0]).read_bytes()), self.before)
        self.assertFalse((self.args.output/'SUCCESS.json').exists())

    def test_apply_return_gap_uses_persistent_journal(self):
        self.setup_scope(); self.apply_args()
        class InterruptJournal(OLD.Journal):
            def apply(inner):
                super().apply(); raise KeyboardInterrupt('synthetic return gap')
        self.old.Journal = InterruptJournal
        with self.assertRaises(KeyboardInterrupt):
            a.publish(self.args)
        self.assertFalse((self.publication/OLD.HISTORY).exists())
        self.assertEqual(json.loads((self.publication/OLD.CATALOGS[0]).read_bytes()), self.before)

    def test_existing_output_and_symlink_target_rejected(self):
        self.setup_scope(); self.args.output.mkdir()
        with self.assertRaisesRegex(ValueError, 'Fresh target'):
            a.publish(self.args)
        self.args.output.rmdir()
        target = self.publication/OLD.CATALOGS[0]; raw = target.read_bytes(); target.unlink()
        alternate = self.base/'catalog.json'; alternate.write_bytes(raw); target.symlink_to(alternate)
        with self.assertRaisesRegex(ValueError, 'Nonphysical'):
            a.publish(self.args)

    def test_special_input_and_catalog_rejected_without_open(self):
        self.setup_scope()
        for path in (self.publication/self.source.relative_to(self.evidence), self.publication/OLD.CATALOGS[0]):
            with self.subTest(path=str(path)):
                raw = path.read_bytes(); path.unlink(); os.mkfifo(path)
                original_snapshot = self.old.snapshot
                def guarded(candidate, optional=False):
                    self.assertNotEqual(Path(candidate), path, 'FIFO reached snapshot/open')
                    return original_snapshot(candidate, optional)
                with patch.object(self.old, 'snapshot', guarded):
                    with self.assertRaisesRegex(ValueError, 'Regular file'):
                        a.publish(self.args)
                path.unlink(); path.write_bytes(raw)
                self.assertFalse(self.args.output.exists())

    def test_late_fifo_target_preserved_while_other_targets_restore(self):
        self.setup_scope(); self.apply_args()
        target = self.publication/OLD.CATALOGS[1]
        def replace():
            target.unlink(); os.mkfifo(target)
        self.late = replace
        with self.assertRaises(BaseExceptionGroup):
            a.publish(self.args)
        self.assertTrue(target.exists())
        self.assertEqual(json.loads((self.publication/OLD.CATALOGS[0]).read_bytes()), self.before)
        self.assertFalse((self.publication/OLD.HISTORY).exists())
        self.assertFalse((self.args.output/'SUCCESS.json').exists())

    def test_late_fifo_success_does_not_block_owned_cleanup(self):
        self.setup_scope(); self.apply_args()
        target = self.args.output/'SUCCESS.json'
        def replace():
            target.unlink(); os.mkfifo(target)
        self.late = replace
        with self.assertRaises(BaseExceptionGroup):
            a.publish(self.args)
        self.assertTrue(target.exists())
        self.assertFalse((self.publication/OLD.HISTORY).exists())
        self.assertEqual(json.loads((self.publication/OLD.CATALOGS[0]).read_bytes()), self.before)


class PublicationLinks(unittest.TestCase):
    def test_retained_control_algorithm_paths_keep_their_original_context(self):
        legacy = [dict(path='fannkuchredux/fannkuchredux.mec', sha256='1'*64),
                  dict(path='../../hosts/gpu/src/control/runtime.rs', sha256='2'*64)]
        direct = dict(path='experiments/example/reconciliation.json', sha256='3'*64)
        control = dict(algorithm=dict(evidence=legacy),
                       original_profile=dict(algorithm=dict(evidence=legacy)),
                       reconciliation=direct)
        candidate = dict(files={}, program_inventory={'example': dict(matched_mech_control=control)},
                         report=dict(path='archive/example/report.json', sha256='4'*64))
        original = copy.deepcopy(candidate)
        links = a.publication_links(candidate, {}, {}, a.EVIDENCE_ROOT)
        self.assertEqual(links, {direct['path']: '3'*64, 'archive/example/report.json': '4'*64})
        self.assertEqual(candidate, original)

    def test_escaped_direct_reference_still_rejected(self):
        candidate = dict(files={}, report=dict(path='../../outside.json', sha256='1'*64))
        with self.assertRaisesRegex(ValueError, 'Nonportable'):
            a.publication_links(candidate, {}, {}, a.EVIDENCE_ROOT)

    def test_subject_algorithm_is_not_a_historical_control_exception(self):
        candidate = dict(files={}, program_inventory={'example': dict(
            algorithm=dict(evidence=[dict(path='../../outside.json', sha256='1'*64)]))})
        with self.assertRaisesRegex(ValueError, 'Nonportable'):
            a.publication_links(candidate, {}, {}, a.EVIDENCE_ROOT)

    def test_subject_algorithm_proof_requires_an_exact_target_copy(self):
        with tempfile.TemporaryDirectory(dir='/private/tmp') as directory:
            evidence, publication = Path(directory)/'evidence', Path(directory)/'publication'
            evidence.mkdir(); publication.mkdir()
            raw = b'{"work":"verified"}'
            (evidence/'proof.json').write_bytes(raw)
            candidate = dict(files={}, program_inventory={'example': dict(
                algorithm=dict(evidence=[dict(path='proof.json', sha256=a.sha(raw))]))})
            links = a.publication_links(candidate, {}, {}, evidence)
            with self.assertRaisesRegex(ValueError, 'Required file'):
                a.verify_links(OLD, links, evidence, publication)
            (publication/'proof.json').write_bytes(raw)
            a.verify_links(OLD, links, evidence, publication)
            (publication/'proof.json').write_bytes(b'changed proof')
            with self.assertRaisesRegex(ValueError, 'Pinned bytes differ'):
                a.verify_links(OLD, links, evidence, publication)


class OriginalSource(unittest.TestCase):
    def test_each_real_dependency_load_keeps_original_locations_and_pins(self):
        for cohort in OLD.COHORTS:
            with self.subTest(cohort=cohort):
                old, deps = a.load_original(SimpleNamespace(cohort=cohort), a.EVIDENCE_ROOT)
                self.assertEqual(old.ROOT, a.EVIDENCE_ROOT)
                self.assertEqual(deps['pins'][a.EVIDENCE_ROOT/a.DRIVER], a.DRIVER_SHA)
                self.assertEqual(deps['pins'][a.EVIDENCE_ROOT/a.NORMALIZATION], a.NORMALIZATION_SHA)
                for name in ('reconciler', 'exporter', 'publication', 'normalization', 'writer'):
                    self.assertTrue(Path(deps[name].__file__).is_relative_to(a.EVIDENCE_ROOT))


if __name__ == '__main__':
    unittest.main()
