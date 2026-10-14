"""Pure Pony reconciliation fixtures; no native commands or bulk pin hashing.

These consume the retained completed study as metadata fixtures. Run only after
the timing coordinator releases the lane. No saved evidence is modified.
"""
import copy
import importlib.util
import json
import math
from pathlib import Path
import unittest


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SPEC = importlib.util.spec_from_file_location('pony_reconcile_test_subject', HERE/'pony_reconcile.py')
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)
PLAN = ROOT/'experiments/pony/migration-resume-v1/plan.json'
PLAN_SHA = '710530db6445292bd6506c97a9e6c91fd7aeba4523f077cf72be25cbebf7a3ee'


def read(path):
    return audit.strict_json(Path(path).read_bytes())


class PureHelpers(unittest.TestCase):
    def test_nonfinite_and_duplicate_json_are_rejected(self):
        for raw in ('{"x": 1, "x": 2}', '{"x": NaN}', '{"x": Infinity}', '{"x": -Infinity}'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                audit.strict_json(raw)

    def test_true_is_not_one(self):
        with self.assertRaises(ValueError):
            audit.same({'ok': True}, {'ok': 1}, 'type differs')

    def test_three_sample_statistics(self):
        self.assertEqual(audit.three_statistics([3.0, 1.0, 2.0]), (2.0, 1.0))
        self.assertEqual(audit.three_statistics([2.0, 2.0, 2.0]), (2.0, 0.0))
        for samples in ([1, 2], [1, 2, 3, 4], [True, 2, 3], [0, 2, 3], [math.nan, 2, 3], [1, 2, math.inf]):
            with self.subTest(samples=samples), self.assertRaises(ValueError):
                audit.three_statistics(samples)

    def test_detached_parent_change_preserves_process_identity(self):
        a = dict(pid=123, listing='123 98 Tue Oct 13 23:23:44 2026 /p/python -B /p/worker.py')
        b = dict(pid=123, listing='123 1 Tue Oct 13 23:23:44 2026 /p/python -B /p/worker.py')
        self.assertEqual(audit.process_identity(a), audit.process_identity(b))
        b['listing'] = b['listing'].replace('23:23:44', '23:23:45')
        self.assertNotEqual(audit.process_identity(a), audit.process_identity(b))


class CompletedLedger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = read(PLAN)
        cls.report = read(Path(cls.plan['output'])/'report.json')
        cls.terminal = read(Path(cls.plan['output'])/'terminal.json')
        cls.retained = read(cls.plan['original_report'])
        cls.raw, cls.supervised = {}, {}
        for attempt in cls.report['attempts']:
            for name, dest in (('result_path', cls.raw), ('supervisor_result_path', cls.supervised)):
                logical = attempt[name]
                path = cls.plan['path_reconciliation'].get(logical, {}).get('path', logical)
                dest[logical] = read(path)
        job = PLAN.parent/'owned-jobs/remaining36'
        cls.durable = {name: read(job/(name+'.json')) for name in
                       ('request', 'launch', 'worker-started', 'command-started', 'terminal')}
        cls.slots, cls.profiles = audit.schedule(cls.plan)
        cls.pins = dict(cls.plan['historical_pins']); cls.pins.update(cls.plan['pins'])

    def reconcile(self, report=None, terminal=None, durable=None):
        return audit.reconcile(self.plan, self.retained, self.report if report is None else report,
            self.terminal if terminal is None else terminal, self.raw, self.supervised,
            self.durable if durable is None else durable, str(PLAN), PLAN_SHA)

    def attempt(self, index=0, mutation=None):
        actual = copy.deepcopy(self.report['attempts'][index])
        if mutation:
            mutation(actual)
        # Keep all three supplied documents mutually consistent: acceptance must
        # still independently reject false raw facts and stale all-true gates.
        raw = {k: v for k, v in actual.items() if k not in audit.SUPERVISOR_FIELDS}
        return audit.check_attempt(actual, raw, copy.deepcopy(actual), self.slots[index],
            self.profiles[actual['key']], self.plan['manifests'][actual['benchmark']], self.pins)

    def test_full90_ledger_only_reconciliation_does_not_admit(self):
        result = self.reconcile()
        self.assertEqual((result['pony_samples'], result['matched_mech_samples']), (60, 30))
        self.assertEqual(len(result['profiles']), 30)
        self.assertIs(result['file_integrity_verified'], False)
        self.assertIs(result['runtime_publication_metadata_qualified'], False)
        self.assertIs(result['chart_admission'], False)

    def test_retained_prefix_is_immutable(self):
        report = copy.deepcopy(self.report)
        report['attempts'][0]['seconds'] += 0.1
        with self.assertRaisesRegex(ValueError, 'Preserved 54'):
            self.reconcile(report=report)

    def test_partial_or_failed_full90_cannot_reconcile(self):
        for status in ('running', 'stopped', 'complete-with-failures'):
            report = copy.deepcopy(self.report); report['status'] = status
            with self.subTest(status=status), self.assertRaises(ValueError):
                self.reconcile(report=report)
        report = copy.deepcopy(self.report); report['attempts'].pop()
        with self.assertRaises(ValueError):
            self.reconcile(report=report)

    def test_changed_median_or_sd_is_rejected(self):
        for field in ('median_seconds', 'sample_stdev_seconds'):
            report = copy.deepcopy(self.report)
            next(iter(report['programs'].values()))[field] += 0.1
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.reconcile(report=report)

    def test_changed_control_binary_is_rejected(self):
        report = copy.deepcopy(self.report)
        control = next(r for r in report['programs'].values() if r['language'] == 'mech')
        control['binary_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'metadata/source binding'):
            self.reconcile(report=report)

    def test_omitted_check_and_truthy_gate_are_rejected(self):
        def remove(a):
            del a['qualification_checks']['native_exited_normally']
        def truthy(a):
            a['qualification_checks']['pins_unchanged'] = 1
        for mutate in (remove, truthy):
            with self.assertRaises(ValueError):
                self.attempt(mutation=mutate)

    def test_raw_failures_cannot_hide_behind_stale_all_true_checks(self):
        changes = [('exit_status', False), ('sampler_wait_status', False), ('valid_environment', 1),
            ('stderr', 'diagnostic'), ('resource_monitor_errors', ['lost sampler']),
            ('supervisor_remaining_members', [123]), ('monitor_finish_error', 'failure'),
            ('seconds', math.inf), ('seconds', 0), ('seconds', True),
            ('peak_process_group_rss_kib', 10240*1024+1), ('full_workload', 1)]
        for field, value in changes:
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                self.attempt(mutation=lambda a, k=field, v=value: a.__setitem__(k, v))

    def test_native_registration_and_command_are_required(self):
        def change_pid(a):
            a['supervised_native_group']['pgid'] += 1
        def change_command(a):
            a['command'][0] += '-replacement'
            a['supervised_native_group']['command'] = a['command']
        for mutate in (change_pid, change_command):
            with self.assertRaises(ValueError):
                self.attempt(mutation=mutate)

    def test_output_hash_cannot_change_in_all_receipts(self):
        def change(a):
            a['stdout_sha256'] = '0'*64; a['validation']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'full reference'):
            self.attempt(mutation=change)

    def test_nbody_tolerance_is_checked_independently(self):
        index = next(i for i, a in enumerate(self.report['attempts']) if a['benchmark'] == 'nbody')
        def change(a):
            a['validation']['energies'][1] += 0.01
        with self.assertRaisesRegex(ValueError, 'N-body energies'):
            self.attempt(index, mutation=change)

    def test_supervisor_cannot_drop_raw_fact(self):
        a = self.report['attempts'][0]
        raw = copy.deepcopy(self.raw[a['result_path']]); raw['unreported_failure'] = 'evidence'
        with self.assertRaisesRegex(ValueError, 'raw sampler fields'):
            audit.check_attempt(a, raw, self.supervised[a['supervisor_result_path']], self.slots[0],
                self.profiles[a['key']], self.plan['manifests'][a['benchmark']], self.pins)

    def test_unsafe_durable_terminal_is_rejected(self):
        for field, value in [('exit_code', False), ('stop_signals', [15]), ('automatic_retry', True),
                             ('command_identity_observation_missing', True)]:
            durable = copy.deepcopy(self.durable); durable['terminal'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.reconcile(durable=durable)

    def test_duplicate_or_changed_rotation_is_rejected(self):
        plan = copy.deepcopy(self.plan)
        plan['remaining_slots'][0] = plan['remaining_slots'][1]
        with self.assertRaisesRegex(ValueError, 'Remaining rotation'):
            audit.schedule(plan)

    def test_exact_revised_sources_are_required(self):
        self.assertEqual(audit.PONY_IDS['knucleotide'],
            ('pony-knucleotide-compact-precedence-v4', 'pony-knucleotide-optimized-shift-types-v5'))
        self.assertEqual(audit.PONY_IDS['binarytrees'],
            ('pony-binarytrees-compact-precedence-v4', 'pony-binarytrees-optimized-precedence-v4'))
        for bench in ('knucleotide', 'binarytrees'):
            plan = copy.deepcopy(self.plan)
            plan['manifests'][bench]['profiles'][0]['id'] = 'pony-'+bench+'-compact'
            with self.subTest(bench=bench), self.assertRaisesRegex(ValueError, 'Wrong measured cohort'):
                audit.schedule(plan)

    def test_scored_source_and_runtime_support_mismatch_cannot_be_provenance(self):
        a = self.report['attempts'][0]
        row = self.profiles[a['key']]
        for path in (row['source'], row['command'][0]):
            pins = dict(self.pins); pins[path] = '0'*64
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'Scored source/binary'):
                audit.check_fingerprint(a, row, pins)
        # Even an added runtime pin that matches the declared fingerprint cannot
        # inherit the narrowly named compiler-provenance exception.
        changed_row = copy.deepcopy(row)
        changed_row['libraries'] = {'/unreviewed/runtime.dylib': '1'*64}
        changed_attempt = copy.deepcopy(a)
        fp = json.loads(a['execution_fingerprint']); fp['support']['/unreviewed/runtime.dylib'] = '1'*64
        changed_attempt['execution_fingerprint'] = json.dumps(fp, sort_keys=True)
        with self.assertRaisesRegex(ValueError, 'Unpinned measured support'):
            audit.check_fingerprint(changed_attempt, changed_row, self.pins)

    def test_descriptive_algorithm_references_preserve_frozen_values(self):
        a = next(a for a in self.report['attempts'] if a['language'] == 'mech' and a['benchmark'] == 'pidigits')
        row = self.profiles[a['key']]
        refs = audit.check_fingerprint(a, row, self.pins)
        prior = next(r for r in refs if r['path'] == 'pidigits/pidigits.mec')
        self.assertIs(prior['descriptive_provenance_only'], True)
        self.assertIs(prior['claimed_source_of_scored_binary'], False)
        self.assertIsNone(prior['current_plan_sha256'])
        changed = copy.deepcopy(a)
        fp = json.loads(a['execution_fingerprint'])
        fp['support']['pidigits/pidigits.mec'] = '0'*64
        changed['execution_fingerprint'] = json.dumps(fp)
        with self.assertRaisesRegex(ValueError, 'Frozen fingerprint support'):
            audit.check_fingerprint(changed, row, self.pins)

    def test_algorithm_reference_alias_of_active_source_stays_strict(self):
        a = next(a for a in self.report['attempts'] if a['language'] == 'mech' and a['benchmark'] == 'pidigits')
        row = copy.deepcopy(self.profiles[a['key']])
        path = 'pidigits/pidigits-advance.mec'
        for ref in row['algorithm']['evidence']:
            if ref['path'] == path:
                ref['sha256'] = '0'*64
        changed = copy.deepcopy(a)
        fp = json.loads(a['execution_fingerprint']); fp['support'][path] = '0'*64
        changed['execution_fingerprint'] = json.dumps(fp)
        with self.assertRaisesRegex(ValueError, 'changed active input'):
            audit.check_fingerprint(changed, row, self.pins)

    def test_nested_or_runtime_support_is_never_descriptive(self):
        a = next(a for a in self.report['attempts'] if a['language'] == 'mech')
        for placement in ('runtime', 'nested_algorithm'):
            row = copy.deepcopy(self.profiles[a['key']])
            ref = dict(path='/unreviewed/runtime.dylib', sha256='1'*64)
            if placement == 'runtime':
                row['runtime_support'] = ref
            else:
                row['algorithm']['other'] = dict(evidence=[ref])
            changed = copy.deepcopy(a)
            fp = json.loads(a['execution_fingerprint']); fp['support'][ref['path']] = ref['sha256']
            changed['execution_fingerprint'] = json.dumps(fp)
            with self.subTest(placement=placement), self.assertRaisesRegex(ValueError, 'Unpinned measured support'):
                audit.check_fingerprint(changed, row, self.pins)


if __name__ == '__main__':
    unittest.main()
