"""Offline admission checks: no compiler, BQN process or timing is executed."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from qualification import import_bqn_knucleotide as admission


def put(root, path, value):
    target = root/path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(admission.encoded(value) if isinstance(value, (dict, list)) else value.encode())
    return target


class ExecutionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.source = 'candidate.bqn'
        put(self.root, admission.BASE+'sources/'+self.source, '1+1\n')
        self.report_path = admission.BASE+'fixture/report.json'
        put(self.root, admission.BASE+'fixture/sources/'+self.source, '1+1\n')
        input_path = 'input.fasta'; put(self.root, input_path, '>THREE\nA\n')
        self.input = dict(path=input_path, bytes=(self.root/input_path).stat().st_size, sha256=admission.sha(self.root/input_path))
        self.output = dict(bytes=2, sha256=hashlib.sha256(b'2\n').hexdigest())
        power = dict(battery="Now drawing from 'AC Power'", settings='AC Power:\n lowpowermode 0\n')
        directory = admission.BASE+'fixture/01-candidate/'
        put(self.root, directory+'stdout.bin', '2\n'); put(self.root, directory+'stderr.bin', '')
        process = dict(command=[str(self.root/admission.RUNTIME), str(self.root/(admission.BASE+'sources/'+self.source))],
            started_utc='2026-10-20T00:00:00+00:00', finished_utc='2026-10-20T00:00:01+00:00',
            stdin=str(self.root/input_path), pid=123, exit_code=0, elapsed_seconds=1.0,
            timed_out=False, stdout=dict(path=directory+'stdout.bin', **self.output),
            stderr=dict(path=directory+'stderr.bin', bytes=0, sha256=hashlib.sha256(b'').hexdigest()))
        put(self.root, directory+'process.json', process)
        row = dict(**process, source=self.source, sample=1, output_valid=True, power_before=power, power_after=power)
        self.report = dict(schema='bqn-knucleotide-execution.v1', status='PASSED', active=None,
            finished_utc='2026-10-20T00:00:02+00:00', controller_sha256=admission.CONTROLLER_SHA,
            pins={admission.BASE+'sources/'+self.source: admission.sha(self.root/(admission.BASE+'sources/'+self.source)),
                  admission.RUNTIME: admission.RUNTIME_SHA},
            full_workload=False, chart_admission=False, diagnostic_profile=False, diagnostic_work_witness=False,
            input=self.input, expected=self.output, orders=[[self.source]], cases=[row], medians={self.source: 1.0})

    def check(self):
        put(self.root, self.report_path, self.report)
        with mock.patch.dict(admission.SUPPORT, {}, clear=True):
            return admission.check_execution(admission.Evidence(self.root), admission.pin(self.root, self.report_path),
                [self.source], admission.RUNTIME, False, expected_input=self.input, expected_output=self.output)

    def test_complete_raw_process_reconciles(self):
        self.assertEqual(self.check()['medians'], {self.source: 1.0})

    def test_rejects_incomplete_diagnostic_or_failed_process(self):
        before = copy.deepcopy(self.report)
        mutations = [('active', {'source': self.source}), ('status', 'RUNNING'),
                     ('diagnostic_profile', True), ('diagnostic_work_witness', True), ('full_workload', True)]
        for field, value in mutations:
            with self.subTest(field=field):
                self.report = copy.deepcopy(before); self.report[field] = value
                with self.assertRaises(ValueError): self.check()
        self.report = before
        self.report['cases'][0]['elapsed_seconds'] = float('nan')
        with self.assertRaises(ValueError): self.check()

    def test_rejects_missing_round_and_stale_median(self):
        self.report['orders'] = []
        with self.assertRaisesRegex(ValueError, 'round'): self.check()
        self.report['orders'] = [[self.source]]; self.report['medians'][self.source] = 0.5
        with self.assertRaisesRegex(ValueError, 'median'): self.check()

    def test_rejects_source_runtime_or_stdout_tampering(self):
        for target in ['source', 'runtime', 'stdout']:
            with self.subTest(target=target):
                before = copy.deepcopy(self.report)
                if target == 'source':
                    self.report['pins'][admission.BASE+'sources/'+self.source] = '0'*64
                elif target == 'runtime':
                    self.report['pins'][admission.RUNTIME] = '0'*64
                else:
                    self.report['cases'][0]['stdout']['sha256'] = '0'*64
                with self.assertRaises(ValueError): self.check()
                self.report = before

    def test_rejects_raw_receipt_and_power_mismatch(self):
        self.report['cases'][0]['pid'] = 999
        with self.assertRaisesRegex(ValueError, 'receipt'): self.check()
        self.report['cases'][0]['pid'] = 123
        self.report['cases'][0]['power_before']['settings'] = 'lowpowermode 1'
        with self.assertRaisesRegex(ValueError, 'power'): self.check()

    def test_rejects_stale_source_snapshot(self):
        put(self.root, admission.BASE+'fixture/sources/'+self.source, '2+2\n')
        with self.assertRaisesRegex(ValueError, 'Changed evidence'): self.check()

    def test_sealed_absolute_commands_replay_in_relocated_checkout(self):
        recorded = '/original/sealed/checkout'
        row = self.report['cases'][0]
        row['command'] = [arg.replace(str(self.root), recorded) for arg in row['command']]
        row['stdin'] = row['stdin'].replace(str(self.root), recorded)
        self.report['input'] = {**self.input, 'path': recorded+'/'+self.input['path']}
        for stream in ['stdout', 'stderr']:
            row[stream]['path'] = recorded+'/'+row[stream]['path']
        raw = {k: v for k, v in row.items() if k not in {'source', 'sample', 'output_valid', 'power_before', 'power_after'}}
        directory = Path(admission.relative(self.root, row['stdout']['path'], recorded)).parent
        put(self.root, directory/'process.json', raw)
        self.assertEqual(self.check()['cases'][0]['command'], row['command'])
        old_input = row['stdin']; row['stdin'] = str(self.root/self.input['path'])
        with self.assertRaisesRegex(ValueError, 'recorded repository'): self.check()
        row['stdin'] = old_input
        row['command'][1] = row['command'][1].replace(recorded, '/other/checkout')
        with self.assertRaisesRegex(ValueError, 'command'): self.check()

    def test_recorded_root_mapping_cannot_escape(self):
        with self.assertRaises(ValueError):
            admission.relative(self.root, '/original/checkout/../outside', '/original/checkout')

    def test_native_build_receipt_replays_without_original_native_paths(self):
        path = admission.REFS['runtime_build']
        value = admission.load(admission.ROOT/path)
        recorded = '/original/sealed/checkout'
        for artifact in value['artifacts']:
            if artifact['path'].startswith(str(admission.ROOT)+'/'):
                artifact['path'] = recorded+'/'+artifact['path'][len(str(admission.ROOT))+1:]
        put(self.root, path, value)
        self.assertEqual(admission.check_build(admission.Evidence(self.root), admission.pin(self.root, path),
            local_artifacts=False, recorded_root=recorded)['commit'], admission.COMMIT)


class SourceOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in [admission.SOURCE, admission.REFS['ownership']]:
            target = self.root/path; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((admission.ROOT/path).read_bytes())
        self.receipt = admission.load(self.root/admission.REFS['ownership'])
        for field in ['source', 'saved_audit']:
            path = self.receipt['policies']['retained'][field]
            target = self.root/path; target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((admission.ROOT/path).read_bytes())

    def check(self):
        put(self.root, admission.REFS['ownership'], self.receipt)
        return admission.check_ownership(admission.Evidence(self.root), admission.pin(self.root, admission.REFS['ownership']))

    def test_exact_reviewed_ledger_accepts(self):
        self.assertEqual(self.check()['application_loc'], 48)

    def test_unapproved_or_wrong_source_count_rejects(self):
        for field, value in [('independent_review_approved', False), ('application_loc', None),
                             ('application_loc', 43), ('source_sha256', '0'*64)]:
            with self.subTest(field=field, value=value):
                original = self.receipt[field]; self.receipt[field] = value
                with self.assertRaises(ValueError): self.check()
                self.receipt[field] = original

    def test_owner_text_or_sum_cannot_drift(self):
        self.receipt['line_ledger'][0]['source_text'] += ' changed'
        with self.assertRaisesRegex(ValueError, 'stale'): self.check()


class CatalogExtensionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        put(self.root, admission.SOURCE, (admission.ROOT/admission.SOURCE).read_text())
        put(self.root, admission.PLAN, {'review': 'fixture'})
        put(self.root, admission.REFS['ownership'], {'review': 'fixture'})
        self.results = dict(schema='bqn-knucleotide-admission-results.v1', status='RECONCILED',
            plan=admission.pin(self.root, admission.PLAN), recorded_at='2026-10-20T00:00:00+00:00',
            evidence=dict(ownership=admission.pin(self.root, admission.REFS['ownership']),
                full=dict(path='full.json', sha256='1'*64), full_workload_validation=dict(path='validation.json', sha256='2'*64)),
            programs=[dict(key=admission.KEY, id=admission.KEY.split(':')[1], source_sha256=admission.SOURCE_SHA,
                loc=48, physical_loc=43, median_seconds=3.0, samples_seconds=[3.1, 3.0, 2.9], sample_sd_seconds=0.1,
                command=['BQN', 'candidate.bqn'], build_command=['make', 'o3'], sample_execution_metadata=[])],
            author_context=copy.deepcopy(admission.AUTHOR_CONTEXT),
            toolchains=dict(bqn=dict(version='CBQN commit '+admission.COMMIT)), timing_boundary='Fresh whole process', artifacts=[])
        self.results['recorded_execution_root'] = '/original/sealed/checkout'
        put(self.root, admission.RESULTS, self.results)
        support = ['a'*64, 'b'*64]
        parent = dict(key=admission.PARENT, id='array-bqn-faithful', benchmark='knucleotide', language='bqn',
            files=[admission.BASELINE_SHA]+support, loc=39, physical_loc=36, seconds=12.0, samples=[12., 11., 13.],
            x=39/17, y=24., formatted_loc=None, formatted_loc_complete=False, formatted_x=None,
            file_roles={support[0]: {'role': 'runtime-support'}}, source_accounting=dict(files=[]),
            authorship=dict(origin_gaps=['Predecessor origin unknown'], retained_sources=[], sources=[],
                license=dict(status='unverified', licenses=[], unresolved=['Inherited terms unknown'])))
        self.before = dict(programs={admission.PARENT: parent}, program_inventory={admission.PARENT: copy.deepcopy(parent)},
            files={admission.BASELINE_SHA: dict(code='retained baseline', path='baseline.bqn')}, archive_paths={'old': 'old'},
            benchmarks=[dict(key='knucleotide', baseline_loc=17, baseline_seconds=0.5,
                groups=[dict(language='bqn', programs=[admission.PARENT], fast=admission.PARENT, small=admission.PARENT,
                    formatted_fast=None, formatted_small=None)])],
            reference_summary=[dict(lang='bqn', fast=dict(x=39/17, y=24), small=dict(x=39/17, y=24))],
            formatted_reference_summary=[])

    def append(self):
        with mock.patch.object(admission, 'reconcile', return_value=self.results):
            return admission.append_catalog(self.before, self.root)

    def test_append_preserves_every_old_profile_source_sample_and_baseline(self):
        original = copy.deepcopy(self.before)
        after = self.append()
        self.assertEqual(self.before, original)
        for pool in ['programs', 'program_inventory', 'files', 'archive_paths']:
            for key, value in original[pool].items(): self.assertEqual(after[pool][key], value)
        self.assertEqual(after['programs'][admission.KEY]['samples'], [3.1, 3.0, 2.9])
        self.assertEqual(after['programs'][admission.KEY]['cwd'], '/original/sealed/checkout')
        self.assertEqual(after['benchmarks'][0]['baseline_seconds'], 0.5)
        group = after['benchmarks'][0]['groups'][0]
        self.assertEqual(group['fast'], admission.KEY)
        self.assertEqual(group['small'], admission.PARENT)
        self.assertEqual(after['reference_summary'][0]['fast'], dict(x=48/17, y=6.))
        for axis in ['x', 'y']:
            self.assertAlmostEqual(after['reference_summary'][0]['small'][axis], original['reference_summary'][0]['small'][axis])
        self.assertEqual(after['programs'][admission.KEY]['authorship']['ai']['models'], [])
        self.assertEqual(after['programs'][admission.KEY]['authorship']['license'], original['programs'][admission.PARENT]['authorship']['license'])

    def test_stale_results_cannot_append(self):
        changed = copy.deepcopy(self.results); changed['programs'][0]['median_seconds'] = 1.0
        with mock.patch.object(admission, 'reconcile', return_value=changed):
            with self.assertRaisesRegex(ValueError, 'Stale'): admission.append_catalog(self.before, self.root)

    def test_new_global_baseline_requires_separate_review(self):
        self.results['programs'][0]['median_seconds'] = 0.1
        put(self.root, admission.RESULTS, self.results)
        with self.assertRaisesRegex(ValueError, 'normalization'): self.append()

    def test_authorship_hook_requires_exact_source_and_admission(self):
        after = self.append(); row = after['programs'][admission.KEY]
        expected = admission.bound_authorship(after, row, self.root)
        self.assertEqual(expected, row['authorship'])
        row['source_provenance_record']['admission']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'binding'): admission.bound_authorship(after, row, self.root)


class HistoricalReplayTests(unittest.TestCase):
    def test_bqn_extension_replays_after_ruby_and_checks_final_identity(self):
        import source_accounting as accounting
        from qualification import import_ruby_zjit as ruby
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            before = {'old': 'untouched'}; transformed = {'source_accounting': True, 'stage': 'loc'}
            ruby_result = {**transformed, 'ruby_zjit_audit': {}, 'stage': 'ruby'}
            bqn_result = {**ruby_result, 'bqn_knucleotide_audit': {}, 'stage': 'bqn'}
            raw = admission.encoded(before); review = admission.encoded({}); partitions = admission.encoded({})
            packet = root/accounting.PACKET; packet.mkdir(parents=True)
            (packet/'before.json.gz').write_bytes(gzip.compress(raw, mtime=0))
            put(root, 'data/source-size-review.json', {})
            put(root, accounting.PACKET+'/partitions.json', {})
            report = {'transformation': 'fixture'}
            put(root, accounting.PACKET+'/receipt.json', dict(before_catalog_sha256=hashlib.sha256(raw).hexdigest(),
                review_sha256=hashlib.sha256(review).hexdigest(), partitions_sha256=hashlib.sha256(partitions).hexdigest(),
                transformation=report))
            def append_ruby(value, _):
                self.assertEqual(value, transformed); return copy.deepcopy(ruby_result)
            def append_bqn(value, _):
                self.assertEqual(value, ruby_result); return copy.deepcopy(bqn_result)
            with mock.patch.object(accounting, 'transform', return_value=(transformed, report)), \
                 mock.patch.object(ruby, 'append_catalog', side_effect=append_ruby), \
                 mock.patch.object(admission, 'append_catalog', side_effect=append_bqn):
                self.assertEqual(accounting.historical_catalog(root, bqn_result), before)
                with self.assertRaisesRegex(AssertionError, 'validated source-accounting'):
                    accounting.historical_catalog(root, {**bqn_result, 'stage': 'tampered'})


if __name__ == '__main__':
    unittest.main()
