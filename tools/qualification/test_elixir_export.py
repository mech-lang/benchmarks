"""Pure private-export tests using saved source metadata and synthetic timings.

The completed reconciliation status, file-verification flags, report binding,
times, PIDs, and output observations in these fixtures are explicitly invented.
No actual full-run result is read or qualified. The reader below permits only
the small saved metadata, source, formatter, and probe files used by this API;
it cannot hash runtime images or traverse a prerequisite closure.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest


HERE = Path(__file__).parent


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


export = load('tested_elixir_private_export', HERE/'elixir_export.py')
synthetic = load('elixir_export_synthetic_ledger', HERE/'test_elixir_reconcile.py')
ROOT = synthetic.audit.ROOT


def document(path):
    return json.loads(Path(path).read_bytes())


class Candidate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        plan = synthetic.SAVED_PLAN
        cls.work = document(plan['qualified_work']['path'])
        cls.counts = document(plan['qualified_source_counts']['path'])
        cls.compiled_report = document(cls.work['report'])
        cls.compiled_plan = document(cls.compiled_report['plan'])
        cls.allowed = {
            str(Path(plan['qualified_work']['path']).resolve()),
            str(Path(plan['qualified_source_counts']['path']).resolve()),
            str(Path(cls.work['report']).resolve()),
            str(Path(cls.compiled_report['plan']).resolve()),
            str((ROOT/'experiments/elixir/compiled-work-v1/probe-v2.exs').resolve()),
        }
        for item in cls.counts['files'].values():
            for field in ('source', 'retained_source', 'formatted_source'):
                cls.allowed.add(str(Path(item[field]).resolve()))

    def fixture(self, failure=None, failure_round=1):
        ledger = synthetic.fixture(failure, failure_round)
        review = synthetic.audit.reconcile(**ledger)
        self.synthetic_bytes = {}
        for group in ('raw', 'supervised', 'outer'):
            for path, value in ledger[group].items():
                self.synthetic_bytes[path] = (json.dumps(value, sort_keys=True)+'\n').encode()
        invented_pins = {path: hashlib.sha256(raw).hexdigest()
                         for path, raw in self.synthetic_bytes.items()}
        # These attestations stand in for the file phase only inside this test.
        # Their synthetic report path is deliberately outside the real run.
        review.update(
            status='full90-reconciled-awaiting-runtime-and-publication-review',
            file_integrity_verified=True, common_mutex_held=True,
            common_mutex_inode=synthetic.audit.p.LOCK_INODE,
            plan=dict(path=synthetic.PLAN, sha256=synthetic.audit.PLAN_SHA),
            report=dict(path='/synthetic/elixir-export/report.json', sha256='f'*64),
            terminal=dict(path='/synthetic/elixir-export/terminal.json', sha256='e'*64),
            verified_file_pins=dict(ledger['plan']['pins'], **{synthetic.PLAN:synthetic.audit.PLAN_SHA},
                                   **invented_pins),
            source_evidence=dict(work=ledger['plan']['qualified_work'],
                                 counts=ledger['plan']['qualified_source_counts'],
                                 bounded=ledger['plan']['original_bounded_plan']))
        self.reads = []
        return dict(plan=ledger['plan'], review=review, work=copy.deepcopy(self.work),
                    counts=copy.deepcopy(self.counts), compiled_report=copy.deepcopy(self.compiled_report),
                    compiled_plan=copy.deepcopy(self.compiled_plan), read_raw=self.read_raw)

    def read_raw(self, path, digest):
        if path in self.synthetic_bytes:
            raw = self.synthetic_bytes[path]
            if hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError('Synthetic sample binding changed')
            self.reads.append((path, digest))
            return raw
        name = str(Path(path).resolve())
        if name not in self.allowed:
            raise ValueError('Test reader refuses runtime/closure or unexpected file: '+name)
        raw = Path(name).read_bytes()
        if len(raw) > 4*1024*1024:
            raise ValueError('Test reader refuses an unexpectedly large artifact')
        if hashlib.sha256(raw).hexdigest() != digest:
            raise ValueError('Saved source/metadata binding changed: '+name)
        self.reads.append((name, digest))
        return raw

    def build(self, **kwargs):
        return export.build_candidate(**self.fixture(**kwargs))

    def test_complete_candidate_keeps_twenty_separate_actual_receipt_keys(self):
        result = self.build()
        self.assertEqual(result['schema'], 'elixir-private-publication-candidate-v1')
        self.assertEqual(result['status'], 'validated-evidence-candidate-awaiting-explicit-publication-review')
        self.assertEqual(len(result['program_inventory']), 20)
        self.assertEqual(set(result['matched_mech_controls']), set(synthetic.audit.BENCHES))
        self.assertEqual(result['excluded_profiles'], [])
        for key, row in result['program_inventory'].items():
            self.assertEqual(key, row['benchmark']+':'+row['receipt_key'])
            self.assertTrue(row['receipt_key'].startswith('elixir-'+row['benchmark']+'-'))
            self.assertEqual(len(row['samples']), 3)
            self.assertEqual(row['seconds'], sorted(row['samples'])[1])
            self.assertTrue(row['full_workload_qualified'])
            self.assertTrue(row['matched_control_qualified'])
            self.assertTrue(row['eligible_for_publication_review'])
            self.assertEqual(len(row['sample_execution_metadata']), 3)

    def test_all_three_authored_roles_and_formatted_counts_are_included(self):
        result = self.build()
        for row in result['program_inventory'].values():
            counted = next(p for p in self.counts['profiles'] if p['id'] == row['receipt_key'])
            files = [self.counts['files'][name] for name in counted['inputs']]
            self.assertEqual(len(row['files']), 3)
            self.assertEqual(set(row['files']), set(row['file_roles']))
            self.assertEqual({v['role'] for v in row['file_roles'].values()},
                             {'application', 'application-helper', 'application-launcher'})
            self.assertEqual(row['canonical_loc'], sum(f['canonical_loc'] for f in files))
            self.assertEqual(row['formatted_loc'], sum(f['formatted_loc'] for f in files))
            self.assertEqual(row['physical_loc'], sum(f['original_physical_loc'] for f in files))
            self.assertTrue(row['source_work_qualified'])

    def test_source_aliases_keep_both_forms_without_reusing_samples(self):
        result = self.build()
        for bench in synthetic.audit.BENCHES:
            a = result['program_inventory'][bench+':elixir-'+bench+'-compact']
            b = result['program_inventory'][bench+':elixir-'+bench+'-optimized']
            self.assertEqual(a['files'], b['files'])
            self.assertEqual(a['canonical_loc'], b['canonical_loc'])
            self.assertEqual(a['formatted_loc'], b['formatted_loc'])
            self.assertNotEqual(a['receipt_key'], b['receipt_key'])
            self.assertNotEqual(a['sample_execution_metadata'], b['sample_execution_metadata'])

    def test_frozen_raw_receipts_remain_without_supervisor_owned_fields(self):
        value = self.fixture()
        raw_path = next(path for path in self.synthetic_bytes
                        if '/attempts/' in path and not path.endswith('.supervisor.json'))
        raw = json.loads(self.synthetic_bytes[raw_path])
        self.assertTrue({'attempt', 'round', 'qualified'}.isdisjoint(raw))
        before = dict(self.synthetic_bytes)
        result = export.build_candidate(**value)
        self.assertEqual(self.synthetic_bytes, before)
        records = [sample for row in result['program_inventory'].values()
                   for sample in row['sample_execution_metadata']]
        sample = next(item for item in records if item['raw_evidence']['path'] == raw_path)
        self.assertEqual(sample['raw_evidence']['sha256'], hashlib.sha256(before[raw_path]).hexdigest())
        self.assertTrue(sample['supervisor_evidence']['path'].endswith('.supervisor.json'))

    def test_rebound_supervisor_cannot_change_form_or_qualification(self):
        for field, replacement in [('id', 'elixir-unrelated-compact'), ('qualified', False)]:
            value = self.fixture()
            path = next(name for name in self.synthetic_bytes if name.endswith('.supervisor.json'))
            item = json.loads(self.synthetic_bytes[path]); item[field] = replacement
            raw = (json.dumps(item, sort_keys=True)+'\n').encode()
            self.synthetic_bytes[path] = raw
            value['review']['verified_file_pins'][path] = hashlib.sha256(raw).hexdigest()
            with self.subTest(field=field), self.assertRaises(ValueError):
                export.build_candidate(**value)

    def test_candidate_never_changes_dataset_or_grants_chart_admission(self):
        value = self.fixture()
        before = copy.deepcopy({k:v for k,v in value.items() if k != 'read_raw'})
        result = export.build_candidate(**value)
        self.assertFalse(result['chart_admission'])
        self.assertFalse(result['dataset_files_changed'])
        self.assertTrue(all(row['chart_admission'] is False for row in result['program_inventory'].values()))
        self.assertEqual({k:v for k,v in value.items() if k != 'read_raw'}, before)

    def test_runtime_metadata_does_not_invent_gc_or_regex_observations(self):
        meta = self.build()['language_metadata']
        self.assertEqual(meta['normal_schedulers_online'], 8)
        self.assertFalse(meta['runtime_gc_configuration_observed'])
        self.assertFalse(meta['gc_numeric_defaults_claimed'])
        self.assertFalse(meta['regex_jit_observed'])
        self.assertIsNone(meta['exact_regex_engine_version'])
        self.assertIn('1.20.4', meta['runtime_policy'])
        self.assertIn('17.1', meta['runtime_policy'])
        self.assertIn('BEAM', meta['runtime_policy'])

    def test_unfinished_unverified_or_wrong_plan_review_is_rejected(self):
        changes = [lambda r:r.update(status='ledger-reconciled-awaiting-file-runtime-and-publication-review'),
                   lambda r:r.update(file_integrity_verified=False),
                   lambda r:r.update(common_mutex_held=False),
                   lambda r:r.update(common_mutex_inode=123),
                   lambda r:r['plan'].update(sha256='0'*64),
                   lambda r:r.update(chart_admission=True),
                   lambda r:r.update(runtime_publication_metadata_qualified=True)]
        for change in changes:
            with self.subTest(change=change):
                value = self.fixture(); change(value['review'])
                with self.assertRaises((ValueError, AssertionError, KeyError)):
                    export.build_candidate(**value)

    def test_review_must_bind_work_counts_and_runtime_evidence(self):
        for which in ('qualified_work', 'qualified_source_counts'):
            value = self.fixture()
            value['review']['verified_file_pins'].pop(value['plan'][which]['path'])
            with self.assertRaises((ValueError, AssertionError, KeyError)):
                export.build_candidate(**value)
        value = self.fixture()
        probe = str(ROOT/'experiments/elixir/compiled-work-v1/probe-v2.exs')
        value['review']['verified_file_pins'].pop(probe)
        with self.assertRaises((ValueError, AssertionError, KeyError)):
            export.build_candidate(**value)

    def test_work_or_count_qualification_cannot_be_substituted(self):
        changes = [lambda v:v['work'].update(source_work_qualified=False),
                   lambda v:v['work'].update(report_sha256='0'*64),
                   lambda v:v['counts'].update(canonical_loc_qualified=False),
                   lambda v:v['counts'].update(formatted_loc_qualified=False)]
        for change in changes:
            value = self.fixture(); change(value)
            with self.assertRaises((ValueError, AssertionError, KeyError)):
                export.build_candidate(**value)

    def test_compiled_source_beam_command_and_runtime_bindings_are_exact(self):
        for kind in ('beam', 'source', 'command', 'environment'):
            value = self.fixture(); row = value['compiled_plan']['profiles'][0]
            if kind == 'beam': row['beams'][0]['sha256'] = '0'*64
            elif kind == 'source': row['physical_inputs'][0]['sha256'] = '0'*64
            elif kind == 'command': row['retained_command'].insert(1, '--no-halt')
            else: row['runtime_environment']['ERL_FLAGS'] = '+JPperf true'
            with self.subTest(kind=kind), self.assertRaises((ValueError, AssertionError, KeyError)):
                export.build_candidate(**value)

    def test_missing_launcher_or_changed_source_role_is_rejected(self):
        for kind in ('missing', 'role'):
            value = self.fixture(); row = value['counts']['profiles'][0]
            if kind == 'missing': row['inputs'].pop()
            else: value['counts']['files'][row['inputs'][-1]]['role'] = 'application-helper'
            with self.assertRaises((ValueError, AssertionError, KeyError)):
                export.build_candidate(**value)

    def test_count_and_formatter_mutations_are_rejected(self):
        for kind in ('canonical', 'formatted', 'formatted_binding', 'formatter'):
            value = self.fixture(); row = value['counts']['profiles'][0]
            if kind == 'canonical': row['canonical_loc'] += 1
            elif kind == 'formatted': row['formatted_loc'] += 1
            elif kind == 'formatted_binding':
                value['counts']['files'][row['inputs'][0]]['artifact_bindings']['formatted_source']['sha256'] = '0'*64
            else: value['counts']['formatter']['line_length'] = 80
            with self.subTest(kind=kind), self.assertRaises((ValueError, AssertionError, KeyError)):
                export.build_candidate(**value)

    def test_failed_form_keeps_prior_samples_without_median_ratio_or_endpoint(self):
        receipt = 'elixir-revcomp-compact'
        key = 'revcomp:'+receipt
        for round_number in (1, 2, 3):
            result = self.build(failure=receipt, failure_round=round_number)
            row = result['program_inventory'][key]
            self.assertEqual(len(row['samples']), round_number-1)
            self.assertIsNone(row['seconds'])
            self.assertIsNone(row['time_ratio_to_matched_mech'])
            self.assertFalse(row['full_workload_qualified'])
            self.assertFalse(row['eligible_for_publication_review'])
            self.assertIn(receipt, result['excluded_profiles'])
            self.assertNotIn(key, result['endpoint_proposals']['revcomp']['programs'])

    def test_failed_control_preserves_elixir_samples_but_disables_ratio_and_endpoints(self):
        result = self.build(failure='revcomp:elixir-full-study:mech-control')
        for form in ('compact', 'optimized'):
            row = result['program_inventory']['revcomp:elixir-revcomp-'+form]
            self.assertEqual(len(row['samples']), 3)
            self.assertGreater(row['seconds'], 0)
            self.assertTrue(row['full_workload_qualified'])
            self.assertFalse(row['matched_control_qualified'])
            self.assertFalse(row['eligible_for_publication_review'])
            self.assertIsNone(row['time_ratio_to_matched_mech'])
        endpoints = result['endpoint_proposals']['revcomp']
        self.assertIsNone(endpoints['fast'])
        self.assertIsNone(endpoints['small'])
        self.assertEqual(endpoints['programs'], [])


if __name__ == '__main__':
    unittest.main()
