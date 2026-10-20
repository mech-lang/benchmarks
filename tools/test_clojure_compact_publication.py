"""Compact Clojure intake checks; never run a JVM, compiler or benchmark."""
import copy
import math
from pathlib import Path
import shutil
import tempfile
import unittest

from qualification import import_clojure_compact as admission


def put(root, path, value):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(admission.encoded(value) if isinstance(value, (dict, list)) else value)


class CompactAdmissionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = admission.load(admission.ROOT / admission.RESULTS)
        cls.catalog = admission.load(admission.ROOT / 'data/benchmarks.json')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        paths = {ref['path'] for ref in self.results['artifacts']} | {admission.PLAN, admission.RESULTS, admission.SOURCE}
        for path in paths:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(admission.ROOT / path, target)
        self.foundation = admission.load(self.root / admission.FROZEN['foundation'][0])
        self.full = admission.load(self.root / admission.FROZEN['full'][0])
        self.runtime = admission.load(self.root / admission.FROZEN['runtime'][0])
        parent = copy.deepcopy(self.catalog['programs'][admission.PARENT])
        control = copy.deepcopy(self.catalog['programs'][admission.CONTROL])
        bench = next(b for b in self.catalog['benchmarks'] if b['key'] == 'nbody')
        programs = {admission.PARENT: parent, admission.CONTROL: control}
        self.before = dict(programs=programs, program_inventory=copy.deepcopy(programs),
            files={key: copy.deepcopy(self.catalog['files'][key]) for row in programs.values() for key in row['files']},
            archive_paths={'sentinel': 'sentinel'}, sentinel={'preserved': [1, 2, 3]},
            benchmarks=[dict(key='nbody', baseline_loc=bench['baseline_loc'], baseline_seconds=bench['baseline_seconds'],
                groups=[dict(language='clojure', programs=list(programs), fast=admission.CONTROL, small=admission.PARENT)])],
            reference_summary=[dict(lang='clojure', fast={}, small={})])

    def check(self, report=None, label='full'):
        admission.check_processes(admission.shared.Evidence(self.root), report or self.full, label,
                                  self.foundation, self.results['recorded_execution_root'])

    def test_real_archived_evidence_relocates_without_runtime_or_classes(self):
        self.assertFalse((self.root / self.foundation['java']['path']).exists())
        self.assertEqual(admission.reconcile(self.root, local_artifacts=False), self.results)
        self.assertEqual(self.results['programs'][0]['median_seconds'], 22.217027958)
        self.assertEqual(self.results['matched_candidate_medians']['primitive-control'], 2.689588458)
        self.assertGreater(self.results['candidate_time_over_matched_control'], 8)

    def test_all_30_bounded_two_pilot_and_six_full_rows_validate(self):
        for label, count in [('bounded', 30), ('pilot', 2), ('full', 6)]:
            report = admission.load(self.root / admission.FROZEN[label][0])
            self.assertEqual(len(report['cases']), count)
            self.check(report, label)

    def test_incomplete_active_diagnostic_or_wrong_cohort_rejects(self):
        for field, value in [('status', 'RUNNING'), ('active', {}), ('pins_unchanged', False),
                             ('diagnostic_profile', True), ('full_workload', False), ('chart_admission', True),
                             ('sources', ['compact-hot-aset'])]:
            report = copy.deepcopy(self.full); report[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): self.check(report)
        report = copy.deepcopy(self.full); report['cases'].pop()
        with self.assertRaises(ValueError): self.check(report)

    def test_source_workload_command_environment_or_process_drift_rejects(self):
        for field, value in [('n', 1000000), ('command', ['java', 'other']), ('environment', {}),
                             ('source_sha256', '0' * 64), ('output_valid', False), ('common_mutex_inherited', False),
                             ('timed_out', True), ('remaining_process_group', [123])]:
            report = copy.deepcopy(self.full); report['cases'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): self.check(report)

    def test_raw_receipt_power_and_mutex_evidence_cannot_be_rewritten(self):
        report = copy.deepcopy(self.full); report['cases'][0]['pid'] += 1
        with self.assertRaisesRegex(ValueError, 'Raw process'): self.check(report)
        report = copy.deepcopy(self.full); report['cases'][0]['power_after']['settings'] = 'lowpowermode 1'
        with self.assertRaisesRegex(ValueError, 'power'): self.check(report)
        report = copy.deepcopy(self.full); report['cases'][0]['common_mutex_inode'] += 1
        with self.assertRaises(ValueError): self.check(report)

    def test_exact_full_output_and_recorded_stream_root_are_required(self):
        row = self.full['cases'][0]
        path = admission.relative(self.root, row['stdout']['path'], self.results['recorded_execution_root'])
        put(self.root, path, b'wrong\n')
        with self.assertRaisesRegex(ValueError, 'Changed evidence'): self.check()
        shutil.copyfile(admission.ROOT / path, self.root / path)
        row['exact_reference_bytes'] = False
        with self.assertRaisesRegex(ValueError, 'exact 26-byte'): self.check()
        row['exact_reference_bytes'] = True
        row['stdout']['path'] = str(self.root / path)
        process = str(Path(path).with_name('process.json'))
        raw = admission.load(self.root / process)
        raw['stdout']['path'] = row['stdout']['path']
        put(self.root, process, raw)
        with self.assertRaisesRegex(ValueError, 'recorded repository'): self.check()

    def test_strict_recorded_runtime_cwd_and_classpath_roots(self):
        foundation = copy.deepcopy(self.foundation)
        foundation['programs']['compact-hot-aset']['classes'] = str(self.root / 'classes')
        with self.assertRaisesRegex(ValueError, 'classpath'):
            admission.recorded_root(foundation, self.full, self.runtime)
        report = copy.deepcopy(self.full); report['cases'][0]['cwd'] = str(self.root)
        with self.assertRaisesRegex(ValueError, 'roots differ'):
            admission.recorded_root(self.foundation, report, self.runtime)

    def test_schedule_or_median_dispersion_changes_reject(self):
        report = copy.deepcopy(self.full); report['orders'][0]['sources'].reverse()
        with self.assertRaisesRegex(ValueError, 'observations'): self.check(report)
        for field in ('medians', 'sample_sd_seconds'):
            report = copy.deepcopy(self.full); report[field]['compact-hot-aset'] = 1.0
            with self.assertRaisesRegex(ValueError, 'aggregates|dispersion'): self.check(report)

    def test_sd_rounding_is_portable_but_samples_and_saved_output_stay_exact(self):
        # Python 3.9 and 3.12 differ by one ULP for this sealed sample cohort.
        # Permit only a tight recomputation tolerance, never different samples.
        report = copy.deepcopy(self.full)
        saved = report['sample_sd_seconds']['compact-hot-aset']
        report['sample_sd_seconds']['compact-hot-aset'] = math.nextafter(saved, math.inf)
        self.check(report)
        self.assertEqual(self.results['programs'][0]['sample_sd_seconds'], saved)
        report['sample_sd_seconds']['compact-hot-aset'] = saved * (1 + 1e-10)
        with self.assertRaisesRegex(ValueError, 'dispersion'): self.check(report)
        report = copy.deepcopy(self.full); report['samples']['compact-hot-aset'][0] += 1e-12
        with self.assertRaisesRegex(ValueError, 'aggregates'): self.check(report)

    def test_sealed_source_approved_ledger_or_producer_report_cannot_be_resealed(self):
        for path in [admission.SOURCE, admission.FROZEN['ownership'][0], admission.FROZEN['full'][0],
                     admission.QUAL + 'selected-full-v1/full-v1/controllers/run_selected_full.py']:
            with self.subTest(path=path):
                original = (self.root / path).read_bytes(); put(self.root, path, original + b'\n')
                put(self.root, admission.PLAN, admission.make_plan(self.root))
                with self.assertRaises(ValueError): admission.reconcile(self.root, local_artifacts=False)
                put(self.root, path, original)

    def test_fast_profile_and_all_legacy_samples_counts_sources_preserved(self):
        before = copy.deepcopy(self.before); after = admission.append_catalog(self.before, self.root)
        self.assertEqual(self.before, before)
        for pool in ('programs', 'program_inventory', 'files', 'archive_paths'):
            for key, value in before[pool].items(): self.assertEqual(after[pool][key], value)
        self.assertEqual(after['sentinel'], before['sentinel'])
        group = after['benchmarks'][0]['groups'][0]
        self.assertEqual(group['fast'], admission.CONTROL)
        self.assertEqual(group['small'], admission.KEY)
        self.assertEqual(after['programs'][admission.CONTROL]['samples'], before['programs'][admission.CONTROL]['samples'])

    def test_new_source_has_own_three_observations_and_exact_supported_counts(self):
        after = admission.append_catalog(self.before, self.root); row = after['programs'][admission.KEY]
        self.assertEqual(row['samples'], [22.092492166, 22.217027958, 22.303277375])
        self.assertEqual((row['loc'], row['physical_loc'], row['native_observations']), (109, 49, 3))
        self.assertIsNone(row['timing_alias_of'])
        self.assertEqual(row['files'], [admission.SOURCE_SHA, admission.SUPPORT_SHA])
        self.assertFalse(row['file_roles'][admission.SUPPORT_SHA]['included_in_application_loc'])
        self.assertNotIn('source_metrics', row)
        self.assertIn('needs-explicit-binder', self.results['logical_source_count_status'])
        self.assertNotIn('matched_control_speedup', self.results)

    def test_duplicate_parent_control_or_baseline_drift_rejects(self):
        after = admission.append_catalog(self.before, self.root)
        with self.assertRaisesRegex(ValueError, 'already admitted'): admission.append_catalog(after, self.root)
        for key in (admission.PARENT, admission.CONTROL):
            before = copy.deepcopy(self.before); before['programs'][key]['loc'] = 1
            with self.assertRaisesRegex(ValueError, 'parent changed|control source/count'): admission.append_catalog(before, self.root)
        before = copy.deepcopy(self.before); before['benchmarks'][0]['baseline_seconds'] = 30
        with self.assertRaisesRegex(ValueError, 'baseline'): admission.append_catalog(before, self.root)

    def test_exact_source_family_attribution_preserves_unknown_origin_and_support_urls(self):
        after = admission.append_catalog(self.before, self.root); row = after['programs'][admission.KEY]
        self.assertEqual(row['authorship'], admission.bound_authorship(after, row, self.root))
        self.assertEqual(row['authorship']['ai']['models'], [])
        self.assertIsNone(row['authorship']['ai']['exact_model'])
        self.assertEqual(row['authorship']['origin_status'], 'unresolved')
        support = [r for r in row['authorship']['retained_sources'] if r['source_sha256'] == admission.SUPPORT_SHA]
        old_support = [r for r in self.before['programs'][admission.PARENT]['authorship']['retained_sources']
                       if r['source_sha256'] == admission.SUPPORT_SHA]
        self.assertEqual(support, old_support)
        row['source_provenance_record']['source_sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'Unbound'): admission.bound_authorship(after, row, self.root)


if __name__ == '__main__': unittest.main()
