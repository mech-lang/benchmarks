"""Pure full-ledger faults and retained durable-launch regression checks.

Full-ledger times, PIDs, output observations and statuses are synthetic. The
durable-only tests read the five small saved launch receipts, never measured
sample reports. No runtime launches, file phase or runtime closure hashes.
"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HERE = Path(__file__).parent
audit = load('elixir_reconciliation_tests', HERE/'elixir_reconcile.py')
base = load('elixir_shared_synthetic_receipts', HERE/'test_prolog_reconcile.py')
SAVED_PLAN = json.loads((audit.ROOT/'experiments/elixir/full90-v1/plan-v1.json').read_bytes())
PLAN = str(audit.ROOT/'experiments/elixir/full90-v1/plan-v1.json')


def fingerprint(row):
    support = {}
    def collect(value):
        if isinstance(value, dict):
            if value.get('path') and audit.p.digest(value.get('sha256')):
                support[value['path']] = value['sha256']
            for child in value.values():
                collect(child)
        elif isinstance(value, list):
            for child in value:
                collect(child)
    collect(row)
    return json.dumps(dict(source_sha256=row['source_sha256'], binary_sha256=row['binary_sha256'],
        command=[v.replace(row['source'], '{source}') for v in row['command']], cwd=row['cwd'],
        environment=row['runtime_environment'], support=support), sort_keys=True)


def fixture(failure=None, failure_round=1):
    old_failure = None
    if failure:
        old_failure = (failure.replace(':elixir-full-study:', ':prolog-full-study:') if ':mech-control' in failure
                       else failure.split('-')[1]+':'+failure.replace('elixir-', 'prolog-'))
    value = base.fixture(old_failure, failure_round)
    def convert(text):
        if type(text) is str:
            if text.startswith('/fixture/results'):
                text = SAVED_PLAN['output'] + text[len('/fixture/results'):]
            if text == base.audit.PLAN_SHA:
                return audit.PLAN_SHA
            for bench in audit.BENCHES:
                text = text.replace(bench+':prolog-'+bench+'-', 'elixir-'+bench+'-')
            return text.replace('prolog-', 'elixir-').replace(':prolog-full-study:', ':elixir-full-study:')
        if type(text) is dict:
            return {convert(k): convert(v) for k,v in text.items()}
        if type(text) is list:
            return [convert(v) for v in text]
        return text
    value = convert(value)
    plan = value['plan'] = copy.deepcopy(SAVED_PLAN)
    value.update(plan_path=PLAN, plan_sha=audit.PLAN_SHA)
    report, terminal = value['report'], value['terminal']
    report.update(plan=PLAN, plan_sha256=audit.PLAN_SHA, formatted_loc_profiles=20,
                  planned_elixir_samples=60, planned_matched_mech_samples=30, full_timings_qualified=False)
    terminal.update(full_timings_qualified=False, prerequisite_pins=dict(plan['pins'], **{PLAN:audit.PLAN_SHA}))
    originals = {row['key']: row for m in plan['manifests'].values() for row in m['profiles']}
    for key, row in list(report['programs'].items()):
        report['programs'][key] = dict(copy.deepcopy(originals[key]),
            **{k:v for k,v in row.items() if k in audit.AGGREGATE})
    for attempt in report['attempts']:
        row = originals[attempt['key']]
        for field in ('language', 'source_sha256', 'cwd', 'runtime_environment'):
            attempt[field] = copy.deepcopy(row[field])
        attempt['command'] = [v.replace('{n}', str(audit.SIZES[row['benchmark']])) for v in row['command']]
        attempt['supervised_native_group']['command'] = attempt['command'][:]
        attempt['execution_fingerprint'] = fingerprint(row)
        ref = plan['manifests'][row['benchmark']]['full_output_reference'] or dict(bytes=44, sha256='1'*64)
        attempt.update(stdout_bytes=ref['bytes'], stdout_sha256=ref['sha256'])
        attempt['validation'].update(ref)
        value['raw'][attempt['result_path']] = {k:copy.deepcopy(v) for k,v in attempt.items()
                                               if k not in audit.p.SUPERVISOR_FIELDS}
        value['supervised'][attempt['supervisor_result_path']] = copy.deepcopy(attempt)
        outer_path = plan['output']+'/outer-supervisor/'+f'{attempt["attempt"]:03d}-{attempt["id"]}.json'
        value['outer'][outer_path]['native_registrations'] = [copy.deepcopy(attempt['supervised_native_group'])]
    for key, row in report['programs'].items():
        attempts = [a for a in report['attempts'] if a['key'] == key]
        row['sample_validation'] = [copy.deepcopy(a['validation']) for a in attempts if a['qualified']]
        row['matched_mech_source_sha256'] = originals[row['matched_mech_control']]['source_sha256']
        if row.get('full_failure'):
            row['full_failure'] = copy.deepcopy(next(a for a in attempts if not a['qualified']))
    command = [audit.p.PYTHON, '-I', '-S', '-B', plan['controller'], 'run',
               '--plan', PLAN, '--plan-sha256', audit.PLAN_SHA]
    for name in ('request', 'launch', 'worker-started', 'command-started'):
        value['durable'][name].update(command=command, cwd=plan['repository'])
    listing = 'Wed Oct 14 00:00:01 2026 '+' '.join(command)
    report['supervisor']['process_listing'] = listing
    for name in ('command-started', 'terminal'):
        value['durable'][name]['command_identity']['listing'] = '99 98 '+listing
    return value


class DurableLaunch(unittest.TestCase):
    def saved(self):
        directory = audit.ROOT/'experiments/elixir/full90-v1/owned-jobs/full90-v1'
        return {name: json.loads((directory/(name+'.json')).read_bytes()) for name in
                ('request', 'launch', 'worker-started', 'command-started', 'terminal')}

    def check(self, durable):
        audit.check_durable(durable, PLAN, audit.PLAN_SHA, SAVED_PLAN)

    def test_retained_no_u_launch_and_all_four_argv_records_are_accepted(self):
        durable = self.saved()
        self.assertNotIn('-u', durable['request']['command'])
        self.check(durable)

    def test_consistently_added_removed_reordered_or_replaced_options_reject(self):
        original = self.saved()['request']['command']
        commands = [original[:4]+['-u']+original[4:],
                    original[:1]+original[2:], original[:2]+original[3:], original[:3]+original[4:],
                    original[:1]+['-S', '-I']+original[3:],
                    ['/other/python']+original[1:], original[:-1]+['0'*64], original+['extra']]
        for command in commands:
            with self.subTest(command=command):
                durable = self.saved()
                for name in ('request', 'launch', 'worker-started', 'command-started'):
                    durable[name]['command'] = command[:]
                for name in ('command-started', 'terminal'):
                    prefix = durable[name]['command_identity']['listing'].split(None, 7)[:7]
                    durable[name]['command_identity']['listing'] = ' '.join(prefix+[' '.join(command)])
                with self.assertRaisesRegex(ValueError, 'exact prepared Elixir run'):
                    self.check(durable)

    def test_each_argv_and_cwd_record_must_agree(self):
        for name in ('request', 'launch', 'worker-started', 'command-started'):
            for field in ('command', 'cwd'):
                with self.subTest(name=name, field=field):
                    durable = self.saved()
                    if field == 'command': durable[name][field] = durable[name][field]+['-u']
                    else: durable[name][field] = '/other/checkout'
                    with self.assertRaises(ValueError): self.check(durable)

    def test_controller_and_worker_pid_birth_command_and_parent_mismatches_reject(self):
        mutations = [
            lambda d:d['command-started'].update(command_pid=99999),
            lambda d:d['terminal'].update(command_pid=99999),
            lambda d:d['command-started']['command_identity'].update(pid=99999),
            lambda d:d['terminal']['command_identity'].update(pid=99999),
            lambda d:d['terminal']['command_identity'].update(listing=d['terminal']['command_identity']['listing'].replace('04:13:40', '04:13:41', 1)),
            lambda d:d['terminal']['worker_identity'].update(pid=99999),
            lambda d:d['launch']['worker_identity'].update(listing=d['launch']['worker_identity']['listing']+' extra'),
        ]
        for mutate in mutations:
            durable = self.saved(); mutate(durable)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError): self.check(durable)
        for field in ('command', 'parent'):
            durable = self.saved()
            for name in ('command-started', 'terminal'):
                fields = durable[name]['command_identity']['listing'].split(None, 7)
                if field == 'command': fields[7] += ' -u'
                else: fields[1] = '99999'
                durable[name]['command_identity']['listing'] = ' '.join(fields)
            with self.subTest(consistent_mismatch=field), self.assertRaises(ValueError): self.check(durable)

    def test_durable_failure_policy_and_missing_interpreter_pin_reject(self):
        for mutate in [lambda d:d['terminal'].update(exit_code=1),
                       lambda d:d['terminal'].update(stop_signals=[15]),
                       lambda d:d['terminal'].update(exception_cleanup={'pid':24394}),
                       lambda d:d['terminal'].update(command_identity_observation_missing=True),
                       lambda d:d['request'].update(automatic_retry=True),
                       lambda d:d['worker-started'].update(inherited_private_lease=False)]:
            durable = self.saved(); mutate(durable)
            with self.assertRaises(ValueError): self.check(durable)
        plan = copy.deepcopy(SAVED_PLAN); del plan['pins'][audit.p.PYTHON]
        with self.assertRaisesRegex(ValueError, 'Unpinned Elixir interpreter'):
            audit.check_durable(self.saved(), PLAN, audit.PLAN_SHA, plan)


class Ledger(unittest.TestCase):
    def test_full90_uses_exact_saved_plan_without_publication(self):
        result = audit.reconcile(**fixture())
        self.assertEqual((result['actual_full_native_processes'], result['actual_elixir_processes'],
                          result['actual_matched_mech_processes'], result['qualified_samples']), (90,60,30,90))
        self.assertFalse(result['chart_admission'])
        self.assertFalse(result['file_integrity_verified'])
        self.assertFalse(result['full_timings_qualified'])

    def test_failure_in_each_round_retains_prior_samples_but_no_median(self):
        key = 'elixir-revcomp-compact'
        for round_number in (1,2,3):
            result = audit.reconcile(**fixture(key, round_number))
            self.assertEqual(result['actual_full_native_processes'], 87+round_number)
            self.assertEqual(len(result['profiles'][key]['samples_seconds']), round_number-1)
            self.assertIsNone(result['profiles'][key]['median_seconds'])
            self.assertIsNone(result['profiles'][key]['time_x_mech'])

    def test_failed_mech_retains_elixir_samples_but_no_ratio(self):
        result = audit.reconcile(**fixture('revcomp:elixir-full-study:mech-control'))
        rows = [r for r in result['profiles'].values() if r['benchmark'] == 'revcomp']
        self.assertEqual(sum(r['full_workload_qualified'] for r in rows), 2)
        self.assertTrue(all(r['time_x_mech'] is None for r in rows))

    def test_partial_failure_cannot_publish_median(self):
        value = fixture('elixir-revcomp-compact', 2)
        value['report']['programs']['elixir-revcomp-compact']['median_seconds'] = 1.0
        with self.assertRaisesRegex(ValueError, 'partial timings'):
            audit.reconcile(**value)

    def test_plan_rejects_draft_changed_runtime_and_unbound_source(self):
        for change in [lambda p:p.update(pins_verified=False),
                       lambda p:p['manifests']['nbody']['profiles'][0]['runtime_environment'].update(ERL_FLAGS='+JPperf true'),
                       lambda p:p['pins'].pop(p['manifests']['nbody']['profiles'][0]['source'])]:
            value = fixture(); change(value['plan'])
            with self.assertRaises((ValueError, KeyError)):
                audit.reconcile(**value)

    def test_owner_fingerprint_alias_requires_exact_retained_pin(self):
        value = fixture(); row = value['plan']['manifests']['nbody']['profiles'][0]
        row['retained_owner_evidence'][0]['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'owner'):
            audit.reconcile(**value)

    def test_unexplained_skips_duplicate_attempts_and_orphan_artifacts_reject(self):
        mutations = [lambda v:v['report']['attempts'].pop(),
                     lambda v:v['report']['attempts'][1].update(attempt=1),
                     lambda v:v['terminal']['available_evidence_pins'].update({'/fixture/orphan':'1'*64})]
        for mutate in mutations:
            value = fixture(); mutate(value)
            with self.assertRaises(ValueError):
                audit.reconcile(**value)

    def test_changed_output_or_overlap_reject_even_consistent_receipts(self):
        for kind in ('output', 'overlap', 'stderr'):
            value = fixture(); attempt = value['report']['attempts'][1]
            if kind == 'output':
                attempt['stdout_sha256'] = attempt['validation']['sha256'] = '0'*64
            elif kind == 'overlap':
                attempt['started_at'] = value['report']['attempts'][0]['started_at']
            else:
                attempt['stderr'] = 'warning'
            value['raw'][attempt['result_path']] = {k:copy.deepcopy(v) for k,v in attempt.items()
                                                   if k not in audit.p.SUPERVISOR_FIELDS}
            value['supervised'][attempt['supervisor_result_path']] = copy.deepcopy(attempt)
            with self.assertRaises(ValueError):
                audit.reconcile(**value)

    def test_cleanup_and_process_ownership_failures_reject(self):
        for kind in ('cleanup', 'parent'):
            value = fixture(); outer = next(iter(value['outer'].values()))
            if kind == 'cleanup':
                outer['cleanup_errors'] = ['owned child remains']
            else:
                outer['owned_groups']['1001']['ppid'] = 99999
            with self.assertRaises(ValueError):
                audit.reconcile(**value)

    def test_wrong_statistics_control_or_boolean_counts_reject(self):
        mutations = [lambda v:v['report']['programs']['elixir-nbody-compact'].update(sample_stdev_seconds=-1e-13),
                     lambda v:v['report']['programs']['elixir-nbody-compact'].update(time_x_mech=True),
                     lambda v:v['report']['programs']['elixir-nbody-compact'].update(matched_mech_source_sha256='0'*64),
                     lambda v:v['terminal'].update(compiler_invocations=False)]
        for mutate in mutations:
            value = fixture(); mutate(value)
            with self.assertRaises(ValueError):
                audit.reconcile(**value)

    def test_live_durable_or_active_native_reject(self):
        for mutate in [lambda v:v['report'].update(active={'pid':123}),
                       lambda v:v['durable']['terminal'].update(actual_command_started=False)]:
            value = fixture(); mutate(value)
            with self.assertRaises(ValueError):
                audit.reconcile(**value)

    def test_nbody_tolerance_recomputed_from_finite_values(self):
        value = fixture(); attempt = next(a for a in value['report']['attempts'] if a['benchmark'] == 'nbody')
        attempt['validation']['energies'][1] = 0.0
        value['raw'][attempt['result_path']] = {k:copy.deepcopy(v) for k,v in attempt.items()
                                               if k not in audit.p.SUPERVISOR_FIELDS}
        value['supervised'][attempt['supervisor_result_path']] = copy.deepcopy(attempt)
        with self.assertRaisesRegex(ValueError, 'N-body'):
            audit.reconcile(**value)


if __name__ == '__main__':
    unittest.main()
