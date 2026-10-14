"""Independent receipt-shape regressions; no native work or full-file review."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location(
    'prolog_reconciliation_review_subject', Path(__file__).with_name('prolog_reconcile.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def receipt():
    """Small synthetic full-workload receipt, independent of a live report."""
    row = dict(id='prolog-regexredux-compact', key='regexredux:prolog-regexredux-compact',
        benchmark='regexredux', language='prolog', source='/example/program.pl',
        source_sha256='a'*64, binary_sha256='b'*64, command=['/example/swipl', '{n}'],
        cwd='/example', runtime_environment={})
    command = ['/example/swipl', '5000000']
    fingerprint = dict(source_sha256=row['source_sha256'], binary_sha256=row['binary_sha256'],
        command=row['command'], cwd=row['cwd'], environment={}, support={})
    attempt = dict(benchmark='regexredux', round=1, id=row['id'], key=row['key'],
        attempt=1, sampler_wait_status=0, full_workload=True, workload_n=5000000,
        timeout_seconds=21600, maximum_rss_mib=10240, valid_environment=True,
        pins_unchanged_at_end=True, qualified=True,
        qualification_checks={name: True for name in m.p.CHECKS}, command=command,
        supervised_native_group=dict(type='native-group-started', pid=301, pgid=301,
            command=command, inherited_common_mutex=True),
        power_at_start=dict(m.POWER), power_at_end=dict(m.POWER),
        cwd=row['cwd'], runtime_environment={}, source_sha256=row['source_sha256'],
        language='prolog', execution_fingerprint=json.dumps(fingerprint),
        started_at='2026-10-14T01:00:00+00:00', finished_at='2026-10-14T01:00:02+00:00',
        exit_status=0, stderr='', seconds=1.0, peak_process_group_rss_kib=100,
        stdout_bytes=100, stdout_sha256='c'*64,
        validation=dict(bytes=100, sha256='c'*64, reference_match=True))
    attempt.update({name: [] for name in m.p.EMPTY_LIST_FIELDS})
    manifest = dict(size=5000000, full_output_reference=dict(bytes=100, sha256='c'*64))
    pins = {row['source']: row['source_sha256'], row['command'][0]: row['binary_sha256']}
    return attempt, row, manifest, pins


def validate(attempt, row, manifest, pins):
    raw = {k: copy.deepcopy(v) for k, v in attempt.items() if k not in m.p.SUPERVISOR_FIELDS}
    slot = ['regexredux', 1, row['id'], row['key']]
    return m.check_attempt(attempt, raw, copy.deepcopy(attempt), slot, row, manifest, pins, [])


def timed_out():
    attempt, row, manifest, pins = receipt()
    # Frozen execute records the normal remaining-group observation only after
    # proc.wait() returns. A timeout during wait cleans/reaps the native process,
    # then persists the execution error without that optional observation.
    attempt.pop('remaining_group_members')
    attempt.pop('validation')
    attempt.update(qualified=False, error='Full process reached the recorded wall-clock timeout',
        error_type='TimeoutError', exit_status=-9, seconds=21600.02,
        finished_at='2026-10-14T07:00:02+00:00', stdout_bytes=0, stdout_sha256='d'*64,
        stdout_prefix='')
    for name in m.FAILURE_GATES:
        attempt['qualification_checks'][name] = name == 'no_resource_violation'
    return attempt, row, manifest, pins


class FrozenFailureShape(unittest.TestCase):
    def test_successful_receipt_is_accepted(self):
        validate(*receipt())

    def test_timeout_without_normal_exit_group_observation_is_preserved(self):
        validate(*timed_out())

    def test_timeout_with_explicit_empty_exit_group_is_preserved(self):
        attempt, row, manifest, pins = timed_out()
        attempt['remaining_group_members'] = []
        validate(attempt, row, manifest, pins)

    def test_timeout_does_not_hide_surviving_group_members(self):
        attempt, row, manifest, pins = timed_out()
        attempt['remaining_group_members'] = [dict(pid=302, pgid=301)]
        with self.assertRaises(ValueError):
            validate(attempt, row, manifest, pins)

    def test_success_requires_actual_normal_exit_group_observation(self):
        attempt, row, manifest, pins = receipt()
        attempt.pop('remaining_group_members')
        with self.assertRaises((ValueError, KeyError)):
            validate(attempt, row, manifest, pins)

    def test_timeout_does_not_hide_monitor_errors(self):
        for name in ('monitor_errors', 'resource_monitor_errors', 'supervisor_remaining_members'):
            with self.subTest(field=name):
                attempt, row, manifest, pins = timed_out()
                attempt['remaining_group_members'] = []
                attempt[name] = ['failure']
                with self.assertRaises(ValueError):
                    validate(attempt, row, manifest, pins)

    def test_timeout_does_not_permit_missing_resource_monitor_receipt(self):
        attempt, row, manifest, pins = timed_out()
        attempt['remaining_group_members'] = []
        attempt.pop('resource_monitor_errors')
        with self.assertRaises((ValueError, KeyError)):
            validate(attempt, row, manifest, pins)


if __name__ == '__main__':
    unittest.main()
