import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmark_suite import (campaign_lock, comparison, digest, equal, file_digest, invoke,
    load_catalog, measurement_response, summarize, verify_response, worker_provenance)
from suite_oracle import outputs


class Contracts(unittest.TestCase):
    def setUp(self):
        self.case = load_catalog()['cases'][0]
        self.expected = outputs(self.case, len(self.case['measurement']['schedule']))

    def response(self):
        return {'protocol': 1, 'outcome': 'ok', 'output_name': 'result', 'outputs': self.expected,
                'before_execution': self.expected[:-1], 'metrics': {'managed_after_drop_bytes': 0}}

    def test_complete_trajectory_and_negative_control(self):
        self.assertEqual(verify_response(self.response(), self.expected, self.case), ('ok', None))
        broken = self.response()
        broken['before_execution'] = self.expected[1:]
        self.assertEqual(verify_response(broken, self.expected, self.case)[0], 'incorrect')

    def test_noop_and_partial_answers_rejected(self):
        for values in ([self.expected[0]] * len(self.expected), self.expected[:1]):
            response = self.response()
            response['outputs'] = values
            self.assertEqual(verify_response(response, self.expected, self.case)[0], 'incorrect')

    def test_output_identity_and_leaked_ownership_rejected(self):
        for key, value in [('output_name', 'last-node'), ('metrics', {'managed_after_drop_bytes': 1})]:
            response = self.response()
            response[key] = value
            self.assertEqual(verify_response(response, self.expected, self.case)[0], 'incorrect')

    def test_retained_snapshots_checked_after_later_turns(self):
        case = copy.deepcopy(self.case)
        case['measurement']['retain_snapshots'] = True
        response = self.response()
        response['retained_outputs'] = [self.expected[-1]] * len(self.expected)
        self.assertEqual(verify_response(response, self.expected, case)[0], 'incorrect')

    def test_shapes_and_nonfinite_numbers_are_not_tolerated(self):
        task = self.case['task']
        self.assertFalse(equal(float('nan'), 1.0, task))
        self.assertFalse(equal(True, 1, task))
        self.assertFalse(equal({'kind':'matrix','shape':[1,2],'values':[1,2]},
                               {'kind':'matrix','shape':[2,1],'values':[1,2]}, task))

    def test_tolerance_does_not_hide_missing_values(self):
        task = self.case['task']
        self.assertTrue(equal(2.0 + 1e-11, 2.0, task))
        self.assertFalse(equal([2.0], [2.0, 3.0], task))

    def test_measured_endpoint_and_numeric_metrics_required(self):
        response = {'outcome':'ok','iterations':6,'output_name':'result','final_output':self.expected[-1],
                    'metrics':{'resident_turn_seconds':1e-5,'source_to_artifact_seconds':1e-3,
                               'artifact_bytes':100,'managed_after_drop_bytes':0}}
        self.assertEqual(measurement_response(response,self.expected[-1],self.case,6)[0],'ok')
        response['metrics']['resident_turn_seconds'] = float('nan')
        self.assertEqual(measurement_response(response,self.expected[-1],self.case,6)[0],'error')
        response['metrics']['resident_turn_seconds'] = 1e-5
        response['final_output'] = self.expected[0]
        self.assertEqual(measurement_response(response,self.expected[-1],self.case,6)[0],'incorrect')

    def test_every_implemented_case_has_an_independent_oracle(self):
        for case in load_catalog()['cases']:
            if case['progress'] != 'planned':
                count = len(case['measurement']['schedule']) * 2
                self.assertEqual(len(outputs(case,count)),count,case['id'])

    def test_planned_coverage_is_separate_from_capability(self):
        for case in load_catalog()['cases']:
            if case['progress'] == 'planned':
                self.assertNotIn('capability',case)
                self.assertEqual(case['backends'],[])


class Comparison(unittest.TestCase):
    def record(self,values):
        return {'task_hash':'task','measurement_hash':'measurement','source_sha256':'source',
                'backend':'source','environment_hash':'host','outcome':'ok',
                'samples':[{'fork':i,'metrics':{'resident_turn_seconds':value}} for i,value in enumerate(values)]}

    def test_boundary_source_environment_and_backend_must_match(self):
        for field in ('task_hash','measurement_hash','source_sha256','environment_hash','backend'):
            a,b=self.record([1]*5),self.record([2]*5)
            b[field]='changed'
            self.assertEqual(comparison(a,b)['status'],'incompatible',field)

    def test_implementation_allocation_changes_do_not_invalidate_task(self):
        a,b=self.record([1]*5),self.record([.5]*5)
        b['implementation']={'allocations':0,'algorithm':'improved'}
        self.assertEqual(comparison(a,b)['status'],'improvement')

    def test_three_forks_do_not_enable_regression_decisions(self):
        result=comparison(self.record([1]*3),self.record([2]*3))
        self.assertEqual(result['status'],'informational')
        self.assertFalse(result['performance_gate'])

    def test_screening_requires_confirmation_and_is_reproducible(self):
        a,b=self.record([1,1.01,.99,1.02,1]),self.record([2,2.01,1.99,2,2.02])
        first=comparison(a,b,seed=10)
        self.assertEqual(first,comparison(a,b,seed=10))
        self.assertEqual(first['status'],'suspected_regression')
        self.assertIn('confirmation',first['reason'])
        self.assertFalse(first['performance_gate'])

    def test_failure_cannot_create_a_ratio(self):
        a,b=self.record([1]*5),self.record([.5]*5)
        b['outcome']='incorrect'
        self.assertNotIn('ratio',comparison(a,b))

    def test_raw_samples_retained(self):
        samples=[{'metrics':{'seconds':n}} for n in [3,1,2]]
        result=summarize(samples)['seconds']
        self.assertEqual(result['median'],2)
        self.assertEqual(result['samples'],[3,1,2])


class Supervision(unittest.TestCase):
    def test_valid_malformed_crash_and_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            tests=[('ok','print(\'{"protocol":1,"outcome":"ok"}\')',1,'ok'),
                   ('bad','print("invalid")',1,'error'),('crash','raise SystemExit(3)',1,'crash'),
                   ('timeout','import time; time.sleep(10)',.1,'timeout')]
            for name,script,timeout,expected in tests:
                result=invoke([sys.executable,'-c',script],{},root/name,timeout)
                self.assertEqual(result['outcome'],expected)
                self.assertTrue((root/name/'request.json').is_file())
                self.assertTrue((root/name/'stdout.json').is_file())

    def test_process_descendants_are_stopped_even_after_leader_exits(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            marker=root/'escaped'
            child=f'import time; from pathlib import Path; time.sleep(.6); Path({str(marker)!r}).write_text("leaked")'
            parent=f'import subprocess,sys; subprocess.Popen([sys.executable,"-c",{child!r}]); print(\'{{"protocol":1,"outcome":"ok"}}\')'
            result=invoke([sys.executable,'-c',parent],{},root/'raw',2)
            self.assertEqual(result['outcome'],'ok')
            time.sleep(.8)
            self.assertFalse(marker.exists())

    def test_locks_prevent_competing_campaigns(self):
        with tempfile.TemporaryDirectory() as directory:
            with campaign_lock(directory):
                with self.assertRaises(ValueError):
                    with campaign_lock(directory): pass
            self.assertFalse((Path(directory)/'campaign.lock').exists())

    def test_worker_hash_is_checked(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            binary=root/'worker'
            binary.write_text('worker')
            manifest=root/'worker.json'
            manifest.write_text(json.dumps({'protocol':1,'binary':str(binary),'binary_sha256':file_digest(binary),
                'revision':'revision','adapter_sha256':'adapter','lock_sha256':'lock'}))
            worker_provenance(manifest)
            binary.write_text('changed')
            with self.assertRaises(ValueError):worker_provenance(manifest)


if __name__ == '__main__':
    unittest.main()
