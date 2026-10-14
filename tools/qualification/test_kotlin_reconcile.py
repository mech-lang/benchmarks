"""Pure full-ledger faults and retained durable-launch regression checks.

All times, PIDs, outputs and statuses are synthetic, joined to the exact
prepared Kotlin plan. No live report, runtime launch, file phase or runtime
closure hashing is used. The fixture generator is shared with Prolog tests.
"""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HERE = Path(__file__).parent
audit = load('kotlin_reconciliation_tests', HERE/'kotlin_reconcile.py')
base = load('kotlin_shared_synthetic_receipts', HERE/'test_prolog_reconcile.py')
SAVED_PLAN = json.loads((audit.ROOT/'experiments/kotlin/full90-v2/plan-v1.json').read_bytes())
PLAN = str(audit.ROOT/'experiments/kotlin/full90-v2/plan-v1.json')


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
        old_failure = (failure.replace(':kotlin-full-study:', ':prolog-full-study:') if ':mech-control' in failure
                       else failure.split('-')[1]+':'+failure.replace('kotlin-', 'prolog-'))
    value = base.fixture(old_failure, failure_round)
    def convert(text):
        if type(text) is str:
            if text.startswith('/fixture/results'):
                text = SAVED_PLAN['output'] + text[len('/fixture/results'):]
            if text == base.audit.PLAN_SHA:
                return audit.PLAN_SHA
            for bench in audit.BENCHES:
                text = text.replace(bench+':prolog-'+bench+'-', 'kotlin-'+bench+'-')
            return text.replace('prolog-', 'kotlin-').replace(':prolog-full-study:', ':kotlin-full-study:')
        if type(text) is dict:
            return {convert(k): convert(v) for k,v in text.items()}
        if type(text) is list:
            return [convert(v) for v in text]
        return text
    value = convert(value)
    plan = value['plan'] = copy.deepcopy(SAVED_PLAN)
    value.update(plan_path=PLAN, plan_sha=audit.PLAN_SHA)
    report, terminal = value['report'], value['terminal']
    report.update(plan=PLAN, plan_sha256=audit.PLAN_SHA, formatted_loc_profiles=0,
                  planned_kotlin_samples=60, planned_matched_mech_samples=30, full_timings_qualified=False)
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
    command = [audit.p.PYTHON, '-I', '-S', '-B', '-u', plan['controller'], 'run',
               '--plan', PLAN, '--plan-sha256', audit.PLAN_SHA]
    for name in ('request', 'launch', 'worker-started', 'command-started'):
        value['durable'][name].update(command=command, cwd=plan['repository'])
    listing = 'Wed Oct 14 00:00:01 2026 '+' '.join(command)
    report['supervisor']['process_listing'] = listing
    for name in ('command-started', 'terminal'):
        value['durable'][name]['command_identity']['listing'] = '99 98 '+listing
    return value


class DurableLaunch(unittest.TestCase):
    def test_exact_isolated_unbuffered_command(self):
        value = fixture()
        command = value['durable']['request']['command']
        self.assertEqual(command[1:5], ['-I', '-S', '-B', '-u'])
        audit.check_durable(value['durable'], PLAN, audit.PLAN_SHA, SAVED_PLAN)
        mutations = [command[:4]+command[5:], command[:1]+command[2:], command+['extra'],
                     command[:1]+['-S','-I']+command[3:]]
        for replacement in mutations:
            durable = copy.deepcopy(value['durable'])
            for name in ('request','launch','worker-started','command-started'):
                durable[name]['command'] = replacement[:]
            with self.subTest(command=replacement), self.assertRaises(ValueError):
                audit.check_durable(durable, PLAN, audit.PLAN_SHA, SAVED_PLAN)

    def test_parent_birth_cwd_and_exit_mismatches_reject(self):
        value = fixture()
        mutations = [lambda d:d['command-started'].update(command_pid=999),
            lambda d:d['terminal'].update(exit_code=1),
            lambda d:d['terminal'].update(stop_signals=[15]),
            lambda d:d['worker-started'].update(cwd='/elsewhere'),
            lambda d:d['terminal']['command_identity'].update(listing='99 999 '+d['terminal']['command_identity']['listing'].split(None,2)[2]),
            lambda d:d['terminal']['command_identity'].update(listing=d['terminal']['command_identity']['listing'].replace('00:00:01','00:00:02'))]
        for mutate in mutations:
            durable = copy.deepcopy(value['durable']);mutate(durable)
            with self.assertRaises(ValueError):
                audit.check_durable(durable, PLAN, audit.PLAN_SHA, SAVED_PLAN)


class FinalClosure(unittest.TestCase):
    def test_cli_receipt_removed_on_exit_failure_before_lease_release(self):
        from contextlib import contextmanager
        events=[]
        @contextmanager
        def closed(*args,on_exit_failure):
            events.append('held')
            try:
                yield {'status':'synthetic-verified'}
                self.assertTrue(output.is_file())
                on_exit_failure()
                self.assertFalse(output.exists())
                events.append('removed')
                raise ValueError('late closure change')
            finally:events.append('released')
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'new.json'
            with mock.patch.object(audit,'review_files',closed), self.assertRaisesRegex(ValueError,'late closure'):
                audit.save_review_result(output,'plan','digest','job')
            self.assertFalse(output.exists())
        self.assertEqual(events,['held','removed','released'])

    def test_cli_preserves_replaced_receipt_and_keeps_success_after_exit(self):
        from contextlib import contextmanager
        @contextmanager
        def closed(*args,on_exit_failure):
            yield {'status':'synthetic-verified'}
            output.write_bytes(b'changed independently')
            on_exit_failure()
        with tempfile.TemporaryDirectory() as directory:
            output=Path(directory)/'new.json'
            with mock.patch.object(audit,'review_files',closed), self.assertRaisesRegex(ValueError,'altered result'):
                audit.save_review_result(output,'plan','digest','job')
            self.assertEqual(output.read_bytes(),b'changed independently')
            output.unlink()
            events=[]
            @contextmanager
            def success(*args,on_exit_failure):
                yield {'status':'synthetic-verified'}
                events.append('exit-verified')
            with mock.patch.object(audit,'review_files',success):
                result,digest=audit.save_review_result(output,'plan','digest','job')
            self.assertEqual(events,['exit-verified'])
            self.assertEqual(result['status'],'synthetic-verified')
            self.assertEqual(audit.hashlib.sha256(output.read_bytes()).hexdigest(),digest)

    def test_exit_recheck_and_restoration_run_before_outer_release(self):
        from contextlib import contextmanager
        events=[]
        @contextmanager
        def lease():
            events.append('held')
            try: yield
            finally: events.append('released')
        def check():
            self.assertEqual(events[0], 'held')
            self.assertNotIn('released', events)
            events.append('check')
            if 'body' in events: raise ValueError('late change')
        def restore():
            self.assertNotIn('released', events)
            events.append('restored')
        with self.assertRaisesRegex(ValueError, 'late change'), lease():
            with audit._yield_verified({},check,restore):events.append('body')
        self.assertEqual(events,['held','check','body','check','restored','released'])

    def test_body_failure_still_rechecks_and_both_closure_restore_errors_survive(self):
        checks=[]
        def check():checks.append('checked')
        with self.assertRaisesRegex(RuntimeError,'body'):
            with audit._yield_verified({},check,None):raise RuntimeError('body')
        self.assertEqual(len(checks),2)
        def late():
            checks.append('checked')
            if len(checks)>3:raise ValueError('closure')
        def restore():raise OSError('restoration')
        with self.assertRaises(BaseExceptionGroup) as caught:
            with audit._yield_verified({},late,restore):pass
        self.assertEqual([str(e) for e in caught.exception.exceptions],['closure','restoration'])

    def test_inventory_does_not_hide_nested_terminals_or_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'nested').mkdir();(root/'nested/terminal.json').write_text('{}')
            self.assertEqual(audit.inventory(root),{str(root/'nested/terminal.json')})
            (root/'alias').symlink_to(root/'nested')
            with self.assertRaisesRegex(ValueError,'Nonregular'):audit.inventory(root)


class Ledger(unittest.TestCase):
    def test_full90_uses_exact_saved_plan_without_publication(self):
        result = audit.reconcile(**fixture())
        self.assertEqual((result['actual_full_native_processes'], result['actual_kotlin_processes'],
                          result['actual_matched_mech_processes'], result['qualified_samples']), (90,60,30,90))
        self.assertFalse(result['chart_admission'])
        self.assertFalse(result['file_integrity_verified'])
        self.assertFalse(result['full_timings_qualified'])

    def test_failure_in_each_round_retains_prior_samples_but_no_median(self):
        key = 'kotlin-revcomp-compact'
        for round_number in (1,2,3):
            result = audit.reconcile(**fixture(key, round_number))
            self.assertEqual(result['actual_full_native_processes'], 87+round_number)
            self.assertEqual(len(result['profiles'][key]['samples_seconds']), round_number-1)
            self.assertIsNone(result['profiles'][key]['median_seconds'])
            self.assertIsNone(result['profiles'][key]['time_x_mech'])

    def test_failed_mech_retains_kotlin_samples_but_no_ratio(self):
        result = audit.reconcile(**fixture('revcomp:kotlin-full-study:mech-control'))
        rows = [r for r in result['profiles'].values() if r['benchmark'] == 'revcomp']
        self.assertEqual(sum(r['full_workload_qualified'] for r in rows), 2)
        self.assertTrue(all(r['time_x_mech'] is None for r in rows))

    def test_partial_failure_cannot_publish_median(self):
        value = fixture('kotlin-revcomp-compact', 2)
        value['report']['programs']['kotlin-revcomp-compact']['median_seconds'] = 1.0
        with self.assertRaisesRegex(ValueError, 'partial timings'):
            audit.reconcile(**value)

    def test_plan_rejects_draft_changed_runtime_and_unbound_source(self):
        for change in [lambda p:p.update(pins_verified=False),
                       lambda p:p['manifests']['nbody']['profiles'][0]['runtime_environment'].update(JAVA_TOOL_OPTIONS='-Xint'),
                       lambda p:p['pins'].pop(p['manifests']['nbody']['profiles'][0]['source'])]:
            value = fixture(); change(value['plan'])
            with self.assertRaises((ValueError, KeyError)):
                audit.reconcile(**value)

    def test_class_pin_role_count_and_formatted_promotion_reject(self):
        for mutate in [lambda p:p['pins'].pop(p['manifests']['nbody']['profiles'][0]['class_artifacts'][0]['path']),
                       lambda p:p['manifests']['nbody']['profiles'][0]['physical_inputs'][1].update(counted=False),
                       lambda p:p['manifests']['nbody']['profiles'][0].update(formatted_loc=20),
                       lambda p:p['manifests']['nbody']['profiles'][0].update(optimization_claim=True),
                       lambda p:p['prerequisite_artifact_closures'].pop()]:
            value=fixture();mutate(value['plan'])
            with self.assertRaises(ValueError):audit.reconcile(**value)

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
        mutations = [lambda v:v['report']['programs']['kotlin-nbody-compact'].update(sample_stdev_seconds=-1e-13),
                     lambda v:v['report']['programs']['kotlin-nbody-compact'].update(time_x_mech=True),
                     lambda v:v['report']['programs']['kotlin-nbody-compact'].update(matched_mech_source_sha256='0'*64),
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
