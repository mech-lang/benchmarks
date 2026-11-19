import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from benchmark_suite import load_catalog
from run_rust_suite import rust_response, task_report, NOTE
from suite_oracle import outputs


class RustQualification(unittest.TestCase):
    def test_resident_reports_do_not_compare_different_runtime_semantics(self):
        for group, backend, metric in [('resident', 'source', 'resident_turn_seconds'), ('concurrent', 'process-workers', 'worker_group_process_seconds')]:
            measured = {'case_id': 'ekf', 'backend': backend, 'lane': 'candidate',
                        'measurement': {'primary_metric': metric}, 'summary': {metric: {'median': 1.31e-6}}}
            control = {**measured, 'backend': 'rust', 'lane': 'control', 'summary': {metric: {'median': 110.7e-9}}}
            report = task_report({'results': [measured, control]}, group, NOTE)
            self.assertIn('1.31e-06', report)
            self.assertIn('rollback', report)
            self.assertNotIn('110.7', report)
            self.assertNotIn('Rust seconds', report)
            self.assertNotIn('| Mech / Rust |', report)

    def setUp(self):
        self.case = next(c for c in load_catalog()['cases'] if c['id'] == 'retained-snapshots')
        self.expected = outputs(self.case, 10)
        self.response = {'outcome': 'ok', 'iterations': 10, 'output_name': 'result', 'final_output': self.expected[-1],
                         'outputs': self.expected, 'before_execution': self.expected[:-1], 'retained_outputs': self.expected,
                         'owned_outputs_released': True, 'metrics': {'resident_turn_seconds': 1e-7, 'execution_block_seconds': 1e-6}}

    def test_requires_complete_trajectory_publication_and_retention(self):
        rust_response(self.response, self.expected, self.case, 10, True)
        for field, value in [('outputs', self.expected[:1]), ('before_execution', self.expected[1:]),
                             ('retained_outputs', [self.expected[-1]] * 10), ('final_output', {'kind': 'scalar', 'value': -999.0}),
                             ('output_name', 'different'), ('iterations', 9), ('owned_outputs_released', False)]:
            with self.subTest(field=field), self.assertRaises(ValueError):
                rust_response({**self.response, field: value}, self.expected, self.case, 10, True)

    def test_no_fabricated_mech_artifact_or_managed_budget_required(self):
        rust_response(self.response, self.expected, self.case, 10)
        self.assertNotIn('artifact_bytes', self.response['metrics'])
        self.assertNotIn('managed_after_drop_bytes', self.response['metrics'])

    def test_measurements_still_require_correct_endpoint_and_ownership(self):
        response = {**self.response, 'outputs': [], 'before_execution': [], 'retained_outputs': []}
        rust_response(response, self.expected, self.case, 10)
        for number in [float('nan'), float('inf'), -1, 0, True]:
            broken = copy.deepcopy(response); broken['metrics']['resident_turn_seconds'] = number
            with self.subTest(number=number), self.assertRaises(ValueError):
                rust_response(broken, self.expected, self.case, 10)

    def test_string_selectors_publish_integer_results(self):
        case=next(c for c in load_catalog()['cases'] if c['id']=='strings')
        count=len(case['measurement']['schedule']); expected=outputs(case,count)
        response={**self.response,'iterations':count,'final_output':copy.deepcopy(expected[-1]),
                  'metrics':{'resident_turn_seconds':1e-7,'execution_block_seconds':count*1e-7}}
        rust_response(response,expected,case,count)
        response['final_output']['value']=float(response['final_output']['value'])
        with self.assertRaisesRegex(ValueError,'unsigned integer'):rust_response(response,expected,case,count)


if __name__ == '__main__': unittest.main()
