"""Offline Nim admission regressions using sealed, relocated evidence."""
import copy
import gzip
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from qualification import import_nim_knucleotide as admission


def write(root, path, value):
    destination = root/path; destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(admission.encoded(value))


def copy_file(root, path):
    destination = root/path; destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(admission.ROOT/path, destination)


class NimExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        folder = admission.BASE+'additional-full-v1'
        shutil.copytree(admission.ROOT/folder, self.root/folder)
        for path in [admission.REFS['matched_build'], admission.REFS['additional_build'], admission.REFS['restoration'], admission.CORPUS]:
            copy_file(self.root, path)
        self.report_path = admission.REFS['full']; self.report = admission.load(self.root/self.report_path)
        self.recorded = admission.recorded_root(self.report)
        matched = admission.load(self.root/admission.REFS['matched_build'])
        additional = admission.load(self.root/admission.REFS['additional_build'])
        copy_file(self.root, matched['historical_build'])
        self.builds = {r['id']: r for r in matched['commands']+additional['commands']}
        evidence = {name: admission.pin(self.root, path) for name, path in [
            ('full', self.report_path), ('corpus', admission.CORPUS), ('matched_build', admission.REFS['matched_build']),
            ('additional_build', admission.REFS['additional_build']), ('restoration', admission.REFS['restoration']),
            ('additional_builder', admission.REFS['additional_builder'])] if (self.root/path).is_file()}
        copy_file(self.root, admission.REFS['additional_builder'])
        evidence['additional_builder'] = admission.pin(self.root, admission.REFS['additional_builder'])
        for name in ['controller.py', 'process_controller.py', 'build-plan.json']:
            evidence['full_'+name] = admission.pin(self.root, folder+'/'+name)
        for identity in admission.IDENTITIES:
            evidence['full_build_'+identity] = admission.pin(self.root, folder+'/builds/'+identity+'/build.json')
        self.plan = dict(recorded_execution_root=self.recorded, evidence=evidence)

    def check(self):
        write(self.root, self.report_path, self.report)
        self.plan['evidence']['full'] = admission.pin(self.root, self.report_path)
        return admission.check_execution(admission.shared.Evidence(self.root), self.plan, 'full', self.builds)

    def test_full_18_process_evidence_replays_in_new_checkout_without_binaries(self):
        self.assertFalse((self.root/admission.stage('preencoded')/'knucleotide').exists())
        self.assertFalse((self.root/admission.shared.INPUT['path']).exists())
        self.assertEqual(self.check()['medians']['preencoded'], 2.606080417)

    def test_incomplete_full_or_running_reports_reject(self):
        original = copy.deepcopy(self.report)
        for field, value in [('status', 'RUNNING'), ('full_workload', False), ('chart_admission', True), ('active', {})]:
            with self.subTest(field=field):
                self.report = copy.deepcopy(original); self.report[field] = value
                with self.assertRaises(ValueError): self.check()

    def test_source_binary_controller_and_round_binding(self):
        original = copy.deepcopy(self.report)
        for field in ['source', 'binary', 'controller', 'round']:
            with self.subTest(field=field):
                self.report = copy.deepcopy(original)
                if field in ['source', 'binary']:
                    suffix = '/knucleotide.nim' if field == 'source' else '/knucleotide'
                    self.report['pins'][admission.stage('preencoded')+suffix] = '0'*64
                elif field == 'controller': self.report['controller_sha256'] = '0'*64
                else: self.report['orders'].pop()
                with self.assertRaises(ValueError): self.check()

    def test_mixed_prefix_and_raw_receipt_change_reject(self):
        original = copy.deepcopy(self.report)
        self.report['cases'][0]['stdin'] = str(self.root/admission.shared.INPUT['path'])
        with self.assertRaisesRegex(ValueError, 'recorded repository'): self.check()
        self.report = original; self.report['cases'][0]['pid'] += 1
        with self.assertRaisesRegex(ValueError, 'receipt'): self.check()

    def test_median_and_complete_output_are_recomputed(self):
        self.report['medians']['preencoded'] *= 0.1
        with self.assertRaisesRegex(ValueError, 'median'): self.check()
        self.report['medians']['preencoded'] /= 0.1
        self.report['cases'][0]['stdout']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'Changed evidence'): self.check()

    def test_unreviewed_flags_reject_even_when_source_unchanged(self):
        result = admission.check_build_plans(admission.shared.Evidence(self.root), self.plan, {}, False)
        self.assertEqual(set(result), set(admission.IDENTITIES))
        path = admission.REFS['additional_build']; document = admission.load(self.root/path)
        document['commands'][2]['command'].insert(-1, '--passC:-ffast-math')
        write(self.root, path, document); self.plan['evidence']['additional_build'] = admission.pin(self.root, path)
        with self.assertRaisesRegex(ValueError, 'flag'): admission.check_build_plans(admission.shared.Evidence(self.root), self.plan, {}, False)

    def test_build_source_snapshot_tamper_rejects(self):
        path = self.root/(admission.BASE+'additional-full-v1/builds/preencoded/knucleotide.nim')
        path.write_text(path.read_text()+'\necho 0\n')
        with self.assertRaisesRegex(ValueError, 'Changed evidence'): self.check()


class NimSourceOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        copy_file(self.root, admission.SOURCE)
        self.receipt = admission.load(admission.ROOT/admission.REFS['ownership'])
        self.receipt.update(independent_review_approved=True, application_loc=72)
        refs = self.receipt['policy_evidence']+self.receipt['vendor_snapshot']+self.receipt['generated_source_evidence']['artifacts']+[self.receipt['runtime_restoration']]
        for ref in refs: copy_file(self.root, ref['path'])
        copy_file(self.root, self.receipt['baseline_comparison']['source'])

    def check(self):
        path = admission.REFS['ownership']; write(self.root, path, self.receipt)
        return admission.check_ownership(admission.shared.Evidence(self.root), admission.pin(self.root, path))

    def test_source_bound_review_accepts(self):
        self.assertEqual(self.check()['source_sha256'], admission.SOURCE_SHA)

    def test_unapproved_wrong_source_or_missing_work_cannot_admit(self):
        original = copy.deepcopy(self.receipt)
        for field in ['approval', 'source', 'work']:
            self.receipt = copy.deepcopy(original)
            if field == 'approval': self.receipt['independent_review_approved'] = False
            elif field == 'source': self.receipt['source_sha256'] = '0'*64
            else: self.receipt['required_work']['expected_updates'] -= 1
            with self.subTest(field=field), self.assertRaises(ValueError): self.check()

    def test_source_owners_cannot_drift(self):
        self.receipt['line_ledger'][0]['source_text'] += ' drift'
        with self.assertRaisesRegex(ValueError, 'Stale'): self.check()

    def test_vendor_snapshot_cannot_be_reclassified_or_replaced(self):
        self.receipt['vendor_snapshot'][1]['included_in_application_loc'] = True
        with self.assertRaisesRegex(ValueError, 'Vendor'): self.check()

    def test_source_delta_and_generated_work_receipt_are_bound(self):
        original = copy.deepcopy(self.receipt)
        self.receipt['source_delta']['unified_diff'] += 'drift'
        with self.assertRaisesRegex(ValueError, 'delta'): self.check()
        self.receipt = original
        self.receipt['generated_source_evidence']['parent_build_source_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'Generated source'): self.check()


class NimCatalogExtensionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve(); copy_file(self.root, admission.SOURCE)
        write(self.root, admission.PLAN, {'fixture': 'review'})
        write(self.root, admission.REFS['ownership'], {'fixture': 'review'})
        self.results = dict(schema='nim-knucleotide-admission-results.v1', status='RECONCILED',
            plan=admission.pin(self.root, admission.PLAN), author_context=copy.deepcopy(admission.shared.AUTHOR_CONTEXT),
            evidence=dict(ownership=admission.pin(self.root, admission.REFS['ownership']),
                full=dict(path='full.json', sha256='1'*64)),
            recorded_at='2026-10-20T00:00:00+00:00', recorded_execution_root='/original/sealed/checkout',
            timing_boundary='Fresh complete process', runtime_environment=dict(LC_ALL='C'), artifacts=[],
            toolchains=dict(nim=dict(version='Nim 2.2.12')),
            programs=[dict(key=admission.KEY, id=admission.KEY.split(':')[1], source_sha256=admission.SOURCE_SHA,
                loc=72, physical_loc=64, median_seconds=2.6, samples_seconds=[2.6, 2.5, 2.7], sample_sd_seconds=0.1,
                command=['recorded/knucleotide'], build_command=['recorded/nim', 'c'], build_cwd='recorded/build',
                binary_sha256=admission.BINARY_HASHES['preencoded'], sample_execution_metadata=[])])
        write(self.root, admission.RESULTS, self.results)
        parent = dict(key=admission.PARENT, id=admission.PARENT.split(':')[1], benchmark='knucleotide', language='nim',
            files=[admission.PARENT_SHA], loc=72, physical_loc=64, seconds=3.5, samples=[3.4, 3.5, 3.6], x=72/17, y=7.,
            measurement_status='measured', formatted_loc=66, formatted_loc_complete=True, formatted_x=66/34,
            authorship=dict(kind='local-origin-unverified', origin_gaps=['Original source unresolved'],
                retained_sources=[], sources=[], license=dict(status='partial', unresolved=['Inherited terms unknown'], licenses=[])))
        self.before = dict(programs={admission.PARENT: parent}, program_inventory={admission.PARENT: copy.deepcopy(parent)},
            files={admission.PARENT_SHA: dict(code='retained', path='old.nim')}, archive_paths={'old': 'old'},
            benchmarks=[dict(key='knucleotide', baseline_loc=17, baseline_seconds=0.5, groups=[dict(language='nim',
                programs=[admission.PARENT], fast=admission.PARENT, small=admission.PARENT,
                formatted_fast=admission.PARENT, formatted_small=admission.PARENT)])],
            reference_summary=[dict(lang='nim', fast=dict(x=72/17, y=7.), small=dict(x=72/17, y=7.))],
            formatted_reference_summary=[dict(lang='nim', fast=dict(x=66/34, y=7.), small=dict(x=66/34, y=7.))])

    def append(self):
        with mock.patch.object(admission, 'reconcile', return_value=self.results):
            return admission.append_catalog(self.before, self.root)

    def test_append_preserves_old_sources_profiles_and_samples(self):
        original = copy.deepcopy(self.before); result = self.append()
        self.assertEqual(self.before, original)
        for pool in ['programs', 'program_inventory', 'files', 'archive_paths']:
            for key, value in original[pool].items(): self.assertEqual(result[pool][key], value)
        row = result['programs'][admission.KEY]
        self.assertEqual(row['samples'], [2.6, 2.5, 2.7]); self.assertFalse(row['formatted_loc_complete'])
        group = result['benchmarks'][0]['groups'][0]
        self.assertEqual(group['fast'], admission.KEY)
        self.assertEqual(group['small'], admission.KEY)
        self.assertEqual(group['formatted_fast'], admission.PARENT)
        self.assertEqual(result['benchmarks'][0]['baseline_seconds'], 0.5)
        self.assertAlmostEqual(result['reference_summary'][0]['fast']['y'], 5.2)
        self.assertEqual(row['authorship']['ai']['models'], [])
        self.assertEqual(row['authorship']['license'], original['programs'][admission.PARENT]['authorship']['license'])

    def test_stale_results_and_global_minimum_reject(self):
        changed = copy.deepcopy(self.results); changed['programs'][0]['loc'] += 1
        with mock.patch.object(admission, 'reconcile', return_value=changed), self.assertRaisesRegex(ValueError, 'Stale'):
            admission.append_catalog(self.before, self.root)
        self.results['programs'][0]['median_seconds'] = 0.1; write(self.root, admission.RESULTS, self.results)
        with self.assertRaisesRegex(ValueError, 'normalization'): self.append()

    def test_authorship_hook_binds_exact_new_source_and_admission(self):
        result = self.append(); row = result['programs'][admission.KEY]
        self.assertEqual(admission.bound_authorship(result, row, self.root), row['authorship'])
        row['source_provenance_record']['admission']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'admission'): admission.bound_authorship(result, row, self.root)


class NimRestorationAndReplayTests(unittest.TestCase):
    def test_all_6770_distribution_pins_replay_and_missing_pin_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); path = admission.REFS['restoration']
            copy_file(root, path); receipt = admission.load(root/path)
            copy_file(root, receipt['historical_proposal'])
            recorded = receipt['compiler'].split('/'+admission.BASE, 1)[0]
            actual, _ = admission.check_restoration(admission.shared.Evidence(root), admission.pin(root, path), recorded, False)
            self.assertEqual(len(actual['checked_distribution_pins']), 6770)
            receipt['checked_distribution_pins'].pop('lib/pure/collections/tables.nim')
            write(root, path, receipt)
            with self.assertRaisesRegex(ValueError, 'pin set'):
                admission.check_restoration(admission.shared.Evidence(root), admission.pin(root, path), recorded, False)

    def test_historical_replay_applies_nim_after_ruby_then_bqn(self):
        import source_accounting as accounting
        from qualification import import_ruby_zjit as ruby
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); before = {'historical': 'untouched'}
            corrected = dict(source_accounting=True, stage='loc')
            after_ruby = dict(**corrected, ruby_zjit_audit={}); after_ruby['stage'] = 'ruby'
            after_bqn = dict(**after_ruby, bqn_knucleotide_audit={}); after_bqn['stage'] = 'bqn'
            after_nim = dict(**after_bqn, nim_knucleotide_audit={}); after_nim['stage'] = 'nim'
            raw = admission.encoded(before); empty = admission.encoded({}); report = {'transformation': 'fixture'}
            packet = root/accounting.PACKET; packet.mkdir(parents=True)
            (packet/'before.json.gz').write_bytes(gzip.compress(raw, mtime=0))
            write(root, 'data/source-size-review.json', {}); write(root, accounting.PACKET+'/partitions.json', {})
            write(root, accounting.PACKET+'/receipt.json', dict(before_catalog_sha256=hashlib.sha256(raw).hexdigest(),
                review_sha256=hashlib.sha256(empty).hexdigest(), partitions_sha256=hashlib.sha256(empty).hexdigest(), transformation=report))
            def checked(expected, output):
                def append(value, _):
                    self.assertEqual(value, expected); return copy.deepcopy(output)
                return append
            with mock.patch.object(accounting, 'transform', return_value=(corrected, report)), \
                 mock.patch.object(ruby, 'append_catalog', side_effect=checked(corrected, after_ruby)), \
                 mock.patch.object(admission.shared, 'append_catalog', side_effect=checked(after_ruby, after_bqn)), \
                 mock.patch.object(admission, 'append_catalog', side_effect=checked(after_bqn, after_nim)):
                self.assertEqual(accounting.historical_catalog(root, after_nim), before)
                with self.assertRaisesRegex(AssertionError, 'validated source-accounting'):
                    accounting.historical_catalog(root, {**after_nim, 'stage': 'tampered'})


if __name__ == '__main__': unittest.main()
