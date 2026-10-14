#!/usr/bin/env python3
"""Pure regression checks using the retained report and archived dataset rows."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import statistics
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('mech_timing_boundary', ROOT / 'tools/mech_timing_boundary.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class TimingBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = m.load_retained_report(ROOT)
        legacy = json.loads((ROOT / 'archive/site/explorer/dist/data.json').read_text())
        # Preserve real rows and metadata, but avoid copying the entire 55 MB
        # multilingual source catalog for each adversarial case.
        rows = {k: p for k, p in legacy['programs'].items() if p['language'] == m.LANGUAGE}
        other_key, other = next((k, p) for k, p in legacy['programs'].items() if p['language'] == 'mech')
        rows[other_key] = other
        cls.other_key = other_key
        file_keys = {r['source_sha256'] for r in cls.report['programs'].values()}
        file_keys.update(other['files'])
        cls.original = {
            'programs': rows, 'program_inventory': {},
            'files': {k: legacy['files'][k] for k in file_keys},
            'benchmarks': legacy['benchmarks'], 'reference_summary': legacy['reference_summary'],
            'formatted_reference_summary': legacy['formatted_reference_summary'],
            'interpreter_integration_audit': legacy['interpreter_integration_audit'],
            'opaque_historical_metadata': {'keep': ['all', 'values']},
        }
        cls.key = 'revcomp:mech-revcomp-optimized:resident'
        cls.corrected, cls.review = m.correct_dataset(cls.original, cls.report)

    def test_real_45_samples_and_14_selected_rows(self):
        self.assertEqual(self.review['retained_forms_validated'], 15)
        self.assertEqual(self.review['retained_wall_samples_validated'], 45)
        self.assertEqual(self.review['selected_wall_samples'], 42)
        self.assertEqual(len(m.verify_previous_correction(self.original, self.corrected, self.report)), 14)
        for key, row in self.corrected['programs'].items():
            if row['language'] != m.LANGUAGE:
                continue
            retained = self.report['programs'][key.removesuffix(':resident') + ':after']
            expected = [d['wall_seconds'] for d in retained['sample_details']]
            self.assertEqual(row['samples'], expected)
            self.assertEqual(row['seconds'], statistics.median(expected))
            self.assertEqual(row['timing_sd'], statistics.stdev(expected))
            self.assertEqual(row['sample_details'], retained['sample_details'])

    def test_independent_process_wall_is_not_phase_sum(self):
        row = self.corrected['programs'][self.key]
        phases = [d['prepare_seconds'] + d['kernel_seconds'] for d in row['sample_details']]
        self.assertNotEqual(row['samples'], phases)
        self.assertGreater(row['samples'][0] - phases[0], 0.55)
        bad = deepcopy(self.corrected)
        bad['programs'][self.key]['samples'] = phases
        bad['programs'][self.key]['seconds'] = statistics.median(phases)
        with self.assertRaises(ValueError):
            m.verify_previous_correction(self.original, bad, self.report)

    def test_reverse_complement_outlier_is_retained(self):
        row = self.corrected['programs'][self.key]
        self.assertEqual(row['samples'], [0.839388917, 0.259461291, 0.257213666])
        self.assertEqual(row['seconds'], 0.259461291)
        self.assertEqual(row['timing_sd'], 0.3354720867904038)
        bad = deepcopy(self.corrected)
        bad['programs'][self.key]['samples'].pop(0)
        with self.assertRaises(ValueError):
            m.verify_correction(self.original, bad, self.report)

    def test_kernel_only_reversion_rejected(self):
        bad = deepcopy(self.corrected)
        for field in ('samples', 'seconds', 'timing_sd', 'y'):
            bad['programs'][self.key][field] = deepcopy(self.original['programs'][self.key][field])
        with self.assertRaises(ValueError):
            m.verify_previous_correction(self.original, bad, self.report)

    def test_missing_wall_in_unselected_form_rejected(self):
        report = deepcopy(self.report)
        row = report['programs']['fannkuchredux:mech-fannkuch-even:after']
        del row['sample_details'][2]['wall_seconds']
        with self.assertRaises(ValueError):
            m.correct_dataset(self.original, report)

    def test_forged_wall_or_report_identity_rejected(self):
        for field in ('wall_seconds', 'kernel_seconds'):
            with self.subTest(field=field):
                report = deepcopy(self.report)
                report['programs']['revcomp:mech-revcomp-optimized:after']['sample_details'][0][field] += 1
                with self.assertRaises(ValueError):
                    m.correct_dataset(self.original, report)

    def test_source_mismatch_rejected_in_selected_and_unselected_forms(self):
        for key in (self.key, 'fannkuchredux:mech-fannkuch-even:resident'):
            with self.subTest(key=key):
                data = deepcopy(self.original)
                source = self.report['programs'][key.removesuffix(':resident') + ':after']['source_sha256']
                data['files'][source]['code'] += '\n'
                with self.assertRaises(ValueError):
                    m.correct_dataset(data, self.report)

    def test_unrelated_profile_mutation_rejected(self):
        bad = deepcopy(self.corrected)
        bad['programs'][self.other_key]['seconds'] += 1
        with self.assertRaises(ValueError):
            m.verify_correction(self.original, bad, self.report)
        with self.assertRaises(ValueError):
            m.verify_previous_correction(self.original, bad, self.report)

    def test_baselines_and_other_groups_are_preserved(self):
        self.assertEqual(self.corrected['programs'][self.other_key], self.original['programs'][self.other_key])
        for before, after in zip(self.original['benchmarks'], self.corrected['benchmarks']):
            self.assertEqual(before, after)  # the recomputed resident endpoints happen to be unchanged
        for before, after in zip(self.original['reference_summary'], self.corrected['reference_summary']):
            if before['lang'] != m.LANGUAGE:
                self.assertEqual(before, after)
            else:
                for kind in ('fast', 'small'):
                    self.assertEqual(before[kind]['x'], after[kind]['x'])
                    self.assertNotEqual(before[kind]['y'], after[kind]['y'])
        bad = deepcopy(self.corrected)
        bad['benchmarks'][0]['baseline_seconds'] *= 2
        with self.assertRaises(ValueError):
            m.verify_previous_correction(self.original, bad, self.report)

    def test_no_historical_audit_or_raw_detail_reinterpretation(self):
        for key, before in self.original['programs'].items():
            if before['language'] != m.LANGUAGE:
                continue
            after = self.corrected['programs'][key]
            for field in ('sample_details', 'previous_measurement', 'integration_comparison',
                          'full_output_validation', 'environment_scope', 'prior_runtime_metadata'):
                self.assertEqual(after[field], before[field])
            evidence = after['measured_backend']['evidence']
            original_evidence = before['measured_backend']['evidence']
            saved = evidence['original_audit_timing_selection']
            self.assertEqual(saved['actual_sample_array'], original_evidence['actual_sample_array'])
            self.assertEqual(saved['original_timing_boundary'], original_evidence['original_timing_boundary'])
            self.assertEqual(evidence['original_timing_boundary'], original_evidence['original_timing_boundary'])
            self.assertEqual(evidence['actual_sample_array'], after['samples'])
            self.assertEqual(evidence['selected_sample_field'], 'sample_details[].wall_seconds')
            for field in ('confidence', 'verified', 'missing_evidence', 'missing_evidence_details'):
                self.assertEqual(after['measured_backend'].get(field), before['measured_backend'].get(field))
        self.assertEqual(self.corrected['interpreter_integration_audit'], self.original['interpreter_integration_audit'])
        self.assertEqual(self.corrected['formatted_reference_summary'], self.original['formatted_reference_summary'])

    def test_all_15_forms_considered_for_endpoints(self):
        even = 'fannkuchredux:mech-fannkuch-even:resident'
        self.assertIn(even, self.review['forms'])
        self.assertFalse(self.review['forms'][even]['selected_for_chart'])
        self.assertEqual(self.review['forms'][even]['wall_median_seconds'], 79.817310959)
        self.assertEqual(self.review['endpoint_selection']['fannkuchredux']['fast'],
                         'fannkuchredux:mech-fannkuch-default:resident')
        bad = deepcopy(self.original)
        group = next(g for g in bad['benchmarks'][0]['groups'] if g['language'] == m.LANGUAGE)
        group['fast'] = group['small']
        with self.assertRaises(ValueError):
            m.correct_dataset(bad, self.report)

    def test_later_additions_allowed_but_old_fields_not(self):
        later = deepcopy(self.corrected)
        later['programs']['new:profile'] = {'language': 'new', 'samples': [1]}
        later['programs'][self.other_key]['new_annotation'] = 'additive'
        self.assertEqual(len(m.verify_previous_correction(self.original, later, self.report)), 14)
        later['programs'][self.key]['algorithm'] = {'strict': False}
        with self.assertRaises(ValueError):
            m.verify_previous_correction(self.original, later, self.report)

    def test_backend_wall_array_cannot_keep_kernel_selection(self):
        bad = deepcopy(self.corrected)
        evidence = bad['programs'][self.key]['measured_backend']['evidence']
        evidence['actual_sample_array'] = deepcopy(self.original['programs'][self.key]['samples'])
        with self.assertRaises(ValueError):
            m.verify_previous_correction(self.original, bad, self.report)

    def test_inputs_are_immutable_and_correction_is_one_shot(self):
        before = deepcopy(self.original)
        report = deepcopy(self.report)
        result, review = m.correct_dataset(before, report)
        self.assertEqual(before, self.original)
        self.assertEqual(report, self.report)
        result['programs'][self.key]['sample_details'][0]['wall_seconds'] = -1
        review['forms'][self.key]['wall_samples_seconds'][0] = -1
        self.assertEqual(before, self.original)
        self.assertEqual(report, self.report)
        with self.assertRaises(ValueError):
            m.correct_dataset(self.corrected, self.report)


if __name__ == '__main__':
    unittest.main()
