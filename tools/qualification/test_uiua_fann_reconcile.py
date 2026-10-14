"""Saved small-document replays and failure closure; no native subject runs."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('uiua_reconcile_test', HERE/'uiua_fann_reconcile.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)


def fixture():
    def read(relative):
        return json.loads((r.ARCHIVE/relative).read_text())
    manifest, report, candidate = (read(x) for x in ('full-study/manifest.json','full-study/report.json','manifest.json'))
    return dict(manifest=manifest, report=report, candidate=candidate,
        source_audit=read('results/source-audit.json'),
        runner_qualification=read('runner-qualification/report.json'),
        prior_review=json.loads(r.PRIOR_REVIEW.read_text()),
        source_bytes={v:(r.ARCHIVE/'sources'/(v+'.ua')).read_bytes() for v in ('compact','fast')},
        raw_records={a['attempt']:read('full-study/attempts/'+Path(a['result_path']).name) for a in report['attempts']})


class RetainedStudy(unittest.TestCase):
    def check(self, values):
        with r.helper_modules() as modules:
            return r.reconcile(**values, modules=modules)

    def test_actual_nine_saved_observations_replay_without_native_execution(self):
        result = self.check(fixture())
        self.assertEqual(result['native_observations'], 9)
        self.assertEqual(result['retained_subject_samples'], 6)
        self.assertEqual(result['retained_control_samples'], 3)
        self.assertEqual(result['source_counts']['compact']['canonical_loc'], 20)
        self.assertEqual(result['source_counts']['fast']['canonical_loc'], 21)
        self.assertFalse(result['chart_admission'])
        self.assertEqual(result['native_processes_started'], 0)

    def test_raw_receipt_cannot_be_replaced_by_report_summary(self):
        values = fixture()
        values['raw_records'][2]['seconds'] += 1
        with self.assertRaisesRegex(ValueError, 'sampler receipt'):
            self.check(values)

    def test_supervisor_fields_cannot_be_retrofilled_into_raw_record(self):
        values = fixture()
        values['raw_records'][2]['qualified'] = True
        with self.assertRaisesRegex(ValueError, 'schema'):
            self.check(values)

    def test_partial_prior_cohort_cannot_supply_three_samples(self):
        values = fixture()
        values['prior_review']['fann']['profiles']['uiua-compact']['samples'].pop()
        with self.assertRaisesRegex(ValueError, 'prior independent'):
            self.check(values)

    def test_changed_source_or_native_helper_claim_is_rejected(self):
        for mutation in ('source', 'helper'):
            values = fixture()
            if mutation == 'source':
                values['source_bytes']['compact'] += b'Extra\n'
            else:
                values['source_audit']['native_benchmark_kernel'] = True
            with self.assertRaises(ValueError):
                self.check(values)

    def test_output_workload_environment_and_missing_record_fail(self):
        for mutation in ('output', 'workload', 'environment', 'missing'):
            values = fixture()
            if mutation == 'output':
                values['report']['attempts'][1]['stdout_bytes'] = 0
            elif mutation == 'workload':
                values['report']['attempts'][1]['workload_n'] = 11
            elif mutation == 'environment':
                values['report']['attempts'][1]['competing_compilers'] = [{'executable':'compiler'}]
            else:
                values['report']['attempts'].pop()
            with self.assertRaises((ValueError, AssertionError)):
                self.check(values)

    def test_json_duplicate_and_nonfinite_values_rejected(self):
        for raw in (b'{"x":1,"x":2}', b'{"x":NaN}'):
            with self.assertRaises(ValueError):
                r.strict_json(raw)

    def test_retained_candidate_allows_documentation_change_only(self):
        original=fixture()['candidate']
        retained=copy.deepcopy(original)
        retained['migration_policy']='Public documentation sentence'
        r.check_retained_candidate(original,retained)
        retained['programs'][0]['source_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'beyond its documentation'):
            r.check_retained_candidate(original,retained)

    def test_deleting_original_pin_does_not_weaken_final_check(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory)/'source'
            source.write_bytes(b'original')
            files = r.Files()
            files.verify(source,r.sha(b'original'))
            original = tuple(files.pins.items())
            files.pins.clear()
            source.write_bytes(b'changed')
            with self.assertRaisesRegex(ValueError,'Pinned file changed'):
                files.final_check(original)

    def test_final_pin_failure_calls_consumer_cleanup_under_lease(self):
        calls = []
        class FakeFiles:
            def __init__(self): self.pins = {}
            def verify(self, path, digest): self.pins[str(path)] = digest
            def read(self, path, digest):
                self.verify(path,digest)
                return Path(path).read_bytes()
            def final_check(self, original_pins=()):
                calls.append('final-check')
                raise ValueError('changed final pin')
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory)/'lock'
            lock.touch()
            def cleanup():
                calls.append('cleanup')
                with lock.open('r+') as other:
                    with self.assertRaises(BlockingIOError):
                        r.fcntl.flock(other,r.fcntl.LOCK_EX|r.fcntl.LOCK_NB)
            with patch.object(r,'LOCK',lock), patch.object(r,'LOCK_INODE',lock.stat().st_ino), patch.object(r,'Files',FakeFiles):
                with self.assertRaisesRegex(ValueError,'changed final pin'):
                    with r.review_context('0'*64, on_exit_failure=cleanup):
                        calls.append('consumer')
            self.assertEqual(calls,['consumer','final-check','cleanup'])

    def test_consumer_check_runs_after_pins_and_failure_cleans_under_lease(self):
        calls = []
        class FakeFiles:
            def __init__(self): self.pins = {}
            def verify(self, path, digest): self.pins[str(path)] = digest
            def read(self, path, digest):
                self.verify(path,digest)
                return Path(path).read_bytes()
            def final_check(self, original_pins=()):
                self.assert_original = bool(original_pins)
                calls.append('pin-replay')
        with tempfile.TemporaryDirectory() as directory:
            lock = Path(directory)/'lock'
            lock.touch()
            def assert_held():
                with lock.open('r+') as other:
                    with self.assertRaises(BlockingIOError):
                        r.fcntl.flock(other,r.fcntl.LOCK_EX|r.fcntl.LOCK_NB)
            def consumer_check():
                assert_held()
                calls.append('final-consumer')
                raise ValueError('late output mutation')
            def cleanup():
                assert_held()
                calls.append('cleanup')
            with patch.object(r,'LOCK',lock), patch.object(r,'LOCK_INODE',lock.stat().st_ino), patch.object(r,'Files',FakeFiles):
                with self.assertRaisesRegex(ValueError,'late output mutation'):
                    with r.review_context('0'*64,on_exit_failure=cleanup,final_consumer_check=consumer_check):
                        calls.append('consumer')
            self.assertEqual(calls,['consumer','pin-replay','final-consumer','cleanup'])


if __name__ == '__main__':
    unittest.main()
