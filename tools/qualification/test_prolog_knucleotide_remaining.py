"""Small retained-receipt and synthetic plan faults; no runtime/pin replay."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('remaining36_subject', HERE/'prolog_knucleotide_remaining.py')
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)


def read(path): return json.loads(path.read_bytes())


def lightweight_saved_fixture():
    """Replay actual small receipts with a reduced, explicitly synthetic pin map.

    No original multi-megabyte plan/terminal or runtime closure is read. The
    native verifier receives exact saved source/fingerprint bindings instead.
    Actual full prerequisite closure remains prepare/run work under leases.
    """
    report = read(c.PREVIOUS/'run-v1/report.json')
    before = read(c.STOP/'before-report.json'); request = read(c.STOP/'request.json')
    closure = read(c.STOP/'closure.json')
    durable = {name: read(c.JOB/(name+'.json')) for name in
               ('request', 'launch', 'worker-started', 'command-started', 'terminal')}
    aggregates = c.r.AGGREGATE | {'retained_attempts'}
    manifests, pins = {}, {}
    for bench in c.f.BENCHES:
        rows = [{k: copy.deepcopy(v) for k, v in row.items() if k not in aggregates}
                for row in report['programs'].values() if row['benchmark'] == bench]
        rows.sort(key=lambda row: 2 if row['language'] == 'mech' else 0 if row['variant'] == 'compact' else 1)
        ids = [row['id'] for row in rows]
        saved = next((a for a in report['attempts'][:14] if a['benchmark'] == bench), None)
        reference = dict(bytes=saved['stdout_bytes'], sha256=saved['stdout_sha256']) if saved else None
        manifests[bench] = dict(profiles=rows, orders=[dict(round=i+1, profiles=ids[i:]+ids[:i]) for i in range(3)],
            size=c.r.SIZES[bench], full_output_reference=reference)
    for attempt in report['attempts'][:14]:
        row = next(row for row in manifests[attempt['benchmark']]['profiles'] if row['key'] == attempt['key'])
        pins[row['source']] = row['source_sha256']; pins[row['binary']] = row['binary_sha256']
        for path, digest in json.loads(attempt['execution_fingerprint'])['support'].items():
            path = str(Path(path) if Path(path).is_absolute() else c.p.HOST_CLBG/Path(path))
            pins[os.path.normpath(path)] = digest
    slots = c.l.schedule_for(manifests)
    retained = dict(reused_samples=copy.deepcopy(report['reused_samples']), completed_benchmarks=c.f.BENCHES[:4])
    plan = dict(manifests=manifests, schedule=slots, retained_slots=slots[:40], remaining_slots=slots[40:],
        full_processes=50, retained_qualified_samples=40, new_prolog_processes=33, new_mech_processes=17,
        retained=retained, pins=pins, historical_pins={})
    artifacts = {path: read(Path(path)) for path in report['validated_attempt_artifacts']}
    cancelled = report['attempts'][-1]
    raw, _, outer = c.attempt_paths(c.PREVIOUS/'run-v1', cancelled)
    for path in (raw, raw.with_suffix('.wrapper.json'), outer): artifacts[str(path)] = read(path)
    inventory = dict(closure['completed_artifacts_unchanged'])
    for path in (raw, raw.with_suffix('.wrapper.json'), outer, c.PREVIOUS/'run-v1/error.log', c.PREVIOUS/'run-v1/report.json'):
        inventory[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    terminal = {name: copy.deepcopy(report[name]) for name in ('status', 'qualified_samples', 'retained_qualified_samples',
        'saved_attempts', 'full_performance_runs', 'common_mutex_held_continuously', 'full_timings_qualified',
        'chart_admission', 'registered_native_attempts', 'native_launch_unconfirmed_attempts', 'skipped_failed_profile_slots')}
    terminal.update(schema='prolog-linear-remaining50-terminal-v1', integrity_errors=[],
        report=str(c.PREVIOUS/'run-v1/report.json'), report_sha256=closure['controller_report_sha256'],
        prerequisite_pins=c.merge(pins, {str(c.PREVIOUS/'plan-v1.json'): c.PREVIOUS_PLAN_SHA}),
        common_mutex_held=True, common_mutex_inode=79859134, original_files_mutated=False,
        new_qualified_samples=14, available_evidence_pins=inventory)
    closure['prerequisite_pins_verified'] = len(terminal['prerequisite_pins'])
    return dict(plan=plan, before=before, report=report, terminal=terminal, durable=durable,
                request=request, closure=closure, artifacts=artifacts)


class SavedPrefix(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data = lightweight_saved_fixture()

    def check(self, mutate=None):
        values = copy.deepcopy(self.data)
        if mutate: mutate(values)
        return c.stopped_prefix(**values)

    def test_actual_small_receipts_preserve54_and_exclude_cancelled(self):
        result = self.check()
        self.assertEqual(len(result['reused_samples']), 54)
        self.assertEqual(result['completed_benchmarks'], c.f.BENCHES[:6])
        self.assertEqual(sum(s['cohort'] == 'linear-remaining50' for s in result['reused_samples']), 14)
        self.assertNotIn('knucleotide', {s['slot'][0] for s in result['reused_samples']})

    def test_cancellation_cannot_be_success_timeout_or_cleanup_failure(self):
        for field, value in [('status', 'complete'), ('error_type', 'TimeoutError'), ('active', {'attempt': 15}),
                             ('pins_unchanged_at_end', False), ('qualified_samples', 55)]:
            with self.subTest(field=field), self.assertRaises((ValueError, AssertionError)):
                self.check(lambda v: v['report'].__setitem__(field, value))
        with self.assertRaises(ValueError):
            self.check(lambda v: v['terminal'].__setitem__('integrity_errors', ['changed']))

    def test_prior_sample_or_source_fingerprint_mutation_fails(self):
        for where in ('report', 'before'):
            with self.subTest(where=where), self.assertRaises(ValueError):
                self.check(lambda v: v[where]['attempts'][0].__setitem__('seconds', 999))
        path = str(c.attempt_paths(c.PREVIOUS/'run-v1', self.data['report']['attempts'][0])[0])
        with self.assertRaises(ValueError):
            self.check(lambda v: v['artifacts'][path].__setitem__('source_sha256', '0'*64))

    def test_durable_argv_birth_parent_signal_or_retry_changed(self):
        mutations = [lambda v: v['durable']['request']['command'].insert(4, '-u'),
            lambda v: v['durable']['terminal'].__setitem__('stop_signals', []),
            lambda v: v['durable']['terminal'].__setitem__('exit_code', 0),
            lambda v: v['durable']['launch'].__setitem__('automatic_retry', True),
            lambda v: v['durable']['command-started']['command_identity'].__setitem__('listing',
                v['durable']['command-started']['command_identity']['listing'].replace('2953  2948', '2953  1'))]
        for mutate in mutations:
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): self.check(mutate)

    def test_interrupted_owned_sampler_or_native_cannot_disappear(self):
        path = str(c.attempt_paths(c.PREVIOUS/'run-v1', self.data['report']['attempts'][-1])[2])
        mutations = [lambda v: v['artifacts'][path]['owned_sampler_children']['15240'].__setitem__('reaped', False),
            lambda v: v['artifacts'][path].__setitem__('cleanup_errors', ['remaining']),
            lambda v: v['artifacts'][path].__setitem__('deadline_expired', True),
            lambda v: v['artifacts'][path]['owned_groups']['15261'].__setitem__('ppid', 1),
            lambda v: v['artifacts'][path].__setitem__('native_registrations', []),
            lambda v: v['closure'].__setitem__('owned_groups_empty', [2948])]
        for mutate in mutations:
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): self.check(mutate)

    def test_missing_extra_or_changed_completed_receipt(self):
        path = next(iter(self.data['report']['validated_attempt_artifacts']))
        for mutate in (lambda v: v['artifacts'].pop(path),
                       lambda v: v['artifacts'].__setitem__('/extra', {}),
                       lambda v: v['closure']['completed_artifacts_unchanged'].__setitem__(path, '0'*64)):
            with self.subTest(mutate=mutate), self.assertRaises((ValueError, KeyError)): self.check(mutate)


def replacement(plan):
    old = plan['manifests']['knucleotide']['profiles'][:2]
    q = dict(schema='prolog-knucleotide-linear-qualified-v1',
        status='qualified-source-work-and-canonical-counts-awaiting-full-timing', bounded_outputs_qualified=True,
        compiled_inputs_qualified=True, source_work_qualified=True, canonical_LOC_admitted=True,
        full_timings_qualified=False, chart_admission=False, pins=dict(c.SOURCES), evidence={},
        artifact_inventories={}, profiles=[])
    # These are synthetic bindings; no successful qualification file is written.
    for name in ('compilation', 'bounded', 'source_counts', 'required_work'):
        path = str(c.SOURCE/'synthetic'/f'{name}.json'); q['pins'][path] = 'a'*64
        q['evidence'][name] = dict(path=path, sha256='a'*64)
    q['artifact_inventories'][str(c.SOURCE/'synthetic')] = {name+'.json': 'a'*64 for name in q['evidence']}
    for index, original in enumerate(old):
        row = copy.deepcopy(original); origin = str(c.SOURCE/'sources/knucleotide'/('compact.pl' if not index else 'optimized.pl'))
        base = c.SOURCE/'synthetic/input'
        bundle = [dict(path=str(base/'sources/knucleotide/compact.pl'), origin=origin, sha256=c.SOURCE_SHA,
                       normalized_loc=101, physical_loc=81)]
        for name in ('clbg_io.pl', 'clbg_records.pl'):
            source = str(c.SOURCE/'support'/name)
            bundle.append(dict(path=str(base/'support'/name), origin=source, sha256=c.SOURCES[source],
                               normalized_loc=21, physical_loc=11))
        for entry in bundle:
            q['pins'][entry['path']] = entry['sha256']; q['pins'][str(Path(entry['path']).with_suffix('.qlf'))] = 'b'*64
        qlf = str(base/'sources/knucleotide/compact.qlf')
        extra = dict(path=str(c.SOURCE/'synthetic/loaded.json'), sha256='c'*64)
        q['pins'][extra['path']] = extra['sha256']; q['pins'][row['binary']] = row['binary_sha256']
        row.update(source=origin, source_sha256=c.SOURCE_SHA, measured_source=bundle[0]['path'], source_bundle=bundle,
            command=[row['binary'], '-q', '-O', '-f', 'none', '--stack-limit=8g', '-l', str(base/'support/clbg_io.qlf'),
                     '-l', str(base/'support/clbg_records.qlf'), '-s', qlf, '-g', 'clbg_io:run(clbg_knucleotide:main)'],
            cwd=str(base), compiled_artifact=dict(path=qlf, sha256='b'*64, bytes=123),
            compiler_bound_input_inventory=dict(extra, status='qualified-exact-authored-compiler-inputs'),
            required_work_review=dict(q['evidence']['required_work'], status='passed'),
            source_count_review=copy.deepcopy(q['evidence']['source_counts']), canonical_source_projection=extra,
            loc=143, canonical_loc=143, physical_loc=103, formatted_loc=None,
            source_alias_of=old[0]['id'] if index else None,
            optimization_claim='explicit equivalent-source alias; no distinct optimization admitted' if index else 'one conversion')
        q['profiles'].append(row)
    return q


class Planning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = lightweight_saved_fixture()
        cls.retained = c.stopped_prefix(**cls.saved)
        cls.q = replacement(cls.saved['plan'])

    def old_profiles(self): return self.saved['plan']['manifests']['knucleotide']['profiles'][:2]

    def plan(self):
        plan = copy.deepcopy(self.saved['plan']); plan['manifests']['knucleotide']['profiles'][:2] = copy.deepcopy(self.q['profiles'])
        plan.update(retained=self.retained, retained_slots=plan['schedule'][:54], remaining_slots=plan['schedule'][54:],
            samples=3, full_processes=36, retained_qualified_samples=54, new_prolog_processes=24,
            new_mech_processes=12, combined_sample_slots=90)
        return plan

    def test_future_qualification_contract_and_unchanged18profiles(self):
        c.qualification_checks(self.q, self.old_profiles())
        plan = self.plan(); c.validate_partition(plan)
        self.assertEqual(plan['remaining_slots'][0][:3], ['knucleotide', 1, 'prolog-knucleotide-compact'])
        self.assertEqual(len(plan['remaining_slots']), 36)
        self.assertEqual(sum(slot[2] == 'mech-aot-control' for slot in plan['remaining_slots']), 12)
        self.assertEqual(sum(len(row['samples_seconds']) for row in c.initial_rows(plan).values()), 54)
        for bench in c.f.BENCHES:
            if bench != 'knucleotide': self.assertEqual(plan['manifests'][bench], self.saved['plan']['manifests'][bench])

    def test_no_runnable_preparation_without_actual_qualification(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp).resolve()
            with patch.object(c, 'SOURCE', root), self.assertRaises(FileNotFoundError):
                c.qualification_prerequisite(root/'missing.json', '0'*64, self.old_profiles(), {})
            with patch.object(c, 'SOURCE', root), patch.object(c, 'retained_prerequisite') as previous:
                with self.assertRaises(FileNotFoundError): c.build_plan(root/'run', root/'missing.json', '0'*64)
                previous.assert_not_called()
        for flag in ('bounded_outputs_qualified', 'compiled_inputs_qualified', 'source_work_qualified', 'canonical_LOC_admitted'):
            value = copy.deepcopy(self.q); value[flag] = False
            with self.subTest(flag=flag), self.assertRaises(ValueError): c.qualification_checks(value, self.old_profiles())

    def test_missing_helpers_counts_wrong_runtime_or_changed_source_rejected(self):
        mutations = [lambda q: q['profiles'][0]['source_bundle'].pop(),
            lambda q: q['profiles'][0].__setitem__('canonical_loc', 1),
            lambda q: q['profiles'][0].__setitem__('formatted_loc', 143),
            lambda q: q['profiles'][0].__setitem__('maximum_workers', 2),
            lambda q: q['profiles'][0].__setitem__('source_sha256', 'a'*64),
            lambda q: q['profiles'][0]['runtime_environment'].__setitem__('NEW', 'value'),
            lambda q: q['profiles'][0]['command'].append('--new-option'),
            lambda q: q['profiles'][1].__setitem__('optimization_claim', 'optimized'),
            lambda q: q['evidence'].pop('bounded')]
        for mutate in mutations:
            value = copy.deepcopy(self.q); mutate(value)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): c.qualification_checks(value, self.old_profiles())

    def test_unpinned_compiled_or_native_artifact_and_path_escape_rejected(self):
        mutations = [lambda q: q['pins'].pop(q['profiles'][0]['compiled_artifact']['path']),
            lambda q: q['profiles'][0]['compiler_bound_input_inventory'].__setitem__('sha256', 'd'*64),
            lambda q: q['artifact_inventories'].__setitem__('/outside', {'x': 'b'*64}),
            lambda q: next(iter(q['artifact_inventories'].values())).__setitem__('../escape', 'b'*64)]
        for mutate in mutations:
            value = copy.deepcopy(self.q); mutate(value)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): c.qualification_checks(value, self.old_profiles())

    def test_schedule_cannot_repeat_54_or_include_interrupted_observation(self):
        for mutate in (lambda p: p['remaining_slots'].insert(0, p['retained_slots'][0]),
                       lambda p: p['remaining_slots'].reverse(),
                       lambda p: p['retained']['reused_samples'].append({'slot': p['remaining_slots'][0]})):
            plan = copy.deepcopy(self.plan()); mutate(plan)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): c.validate_partition(plan)

    def report(self, fail_key=None):
        plan = self.plan(); rows = c.initial_rows(plan); attempts = []; skipped = []; failed = []
        for slot in plan['remaining_slots']:
            bench, round_, identifier, key = slot; row = rows[key]
            if row.get('full_failure'):
                skipped.append(dict(benchmark=bench, round=round_, id=identifier, key=key)); continue
            number = len(attempts)+1
            attempt = dict(benchmark=bench, round=round_, id=identifier, key=key, attempt=number,
                           qualified=key != fail_key, seconds=float(number), validation={'reference_match': True})
            attempts.append(attempt); row['attempts'].append(number)
            if attempt['qualified']:
                row['samples_seconds'].append(attempt['seconds']); row['sample_validation'].append(attempt['validation'])
                row['measurement_status'] = 'measured' if len(row['samples_seconds']) == 3 else 'partial'
            else:
                row['full_failure'] = attempt; row['measurement_status'] = 'failed-full-workload'; failed.append(key)
        for manifest in plan['manifests'].values(): c.summarize(rows, manifest)
        report = dict(programs=rows, attempts=attempts, isolated_failed_profiles=failed,
            skipped_failed_profile_slots=skipped, active=None, completed_benchmarks=c.f.BENCHES,
            native_launch_unconfirmed_attempts=[], full_performance_runs=len(attempts),
            qualified_samples=sum(len(row['samples_seconds']) for row in rows.values()), retained_qualified_samples=54,
            repeated_completed_samples=0, registered_native_attempts=list(range(1, len(attempts)+1)))
        return plan, report

    def test_success_and_isolated_subject_or_control_failure_ledger(self):
        for key in (None, 'knucleotide:prolog-knucleotide-compact', 'knucleotide:prolog-full-study:mech-control'):
            plan, report = self.report(key); c.check_success_ledger(plan, report)
            self.assertEqual(report['qualified_samples'], 90 if key is None else 87)
            if key:
                self.assertEqual(len(report['skipped_failed_profile_slots']), 2)
                self.assertNotIn('median_seconds', report['programs'][key])

    def test_ledger_rejects_missing_duplicate_retry_or_altered_summary(self):
        mutations = [lambda r: r['attempts'].pop(), lambda r: r['attempts'].append(r['attempts'][0]),
            lambda r: r['attempts'][0].__setitem__('attempt', 2),
            lambda r: r['programs']['knucleotide:prolog-knucleotide-compact']['samples_seconds'].__setitem__(0, 999),
            lambda r: r.__setitem__('native_launch_unconfirmed_attempts', [1])]
        for mutate in mutations:
            plan, report = self.report(); mutate(report)
            with self.subTest(mutate=mutate), self.assertRaises(ValueError): c.check_success_ledger(plan, report)


class Closure(unittest.TestCase):
    def finish_fixture(self, fault):
        with tempfile.TemporaryDirectory() as directory:
            out = Path(directory); lock_path = out/'lock'; lock_path.touch()
            target = out/'output'; target.mkdir(); path = target/'report.json'
            report = dict(status='stopped-unqualified', active=None, attempts=[], programs={},
                skipped_failed_profile_slots=[], qualified_samples=54)
            def save(path, value): path.write_text(json.dumps(value, indent=2)+'\n')
            guard = types.SimpleNamespace(OUT=target, REPORT=path, save=save)
            original_inventory = c.l.file_inventory; called = 0
            def inventory(root):
                nonlocal called
                called += 1
                if fault == 'initial-report' and called == 1: path.write_text('{}\n')
                if fault == 'late-report' and called == 2: path.write_text('{}\n')
                return original_inventory(root)
            def verify(pins):
                if fault == 'pin': raise ValueError('changed pin')
            with lock_path.open('rb') as lock, patch.object(c, 'verify_lease') as lease, \
                 patch.object(c.l, 'file_inventory', side_effect=inventory), patch.object(c.f, 'verify', side_effect=verify):
                if fault == 'lease': lease.side_effect = ValueError('lock replaced')
                plan = dict(retained_artifact_inventories={}, knucleotide_qualification={'artifact_inventories': {}})
                if fault:
                    with self.assertRaises(ValueError): c.finish(plan, report, {}, {}, guard, lock)
                else: c.finish(plan, report, {}, {}, guard, lock)
            return read(target/'terminal.json')

    def test_final_report_pin_and_lock_mutations_cannot_claim_clean_closure(self):
        for fault in ('initial-report', 'late-report', 'pin', 'lease'):
            with self.subTest(fault=fault):
                terminal = self.finish_fixture(fault)
                self.assertEqual(terminal['status'], 'failed-terminal-integrity')
                self.assertTrue(terminal['integrity_errors'])

    def test_fresh_paths_no_implicit_resume_or_symlink_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory); old = root/'run'; old.mkdir(); link = root/'alias'; link.symlink_to(old)
            with patch.object(c, 'PACKET', root), self.assertRaises(ValueError): c.fresh_paths(root/'plan', old)
            with self.assertRaises(ValueError): c.regular(link)
            fifo = root/'fifo'; os.mkfifo(fifo)
            with self.assertRaises(ValueError): c.regular(fifo)

    def test_new_file_in_either_preserved_or_qualified_input_inventory_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve(); old = root/'old'; new = root/'new'; old.mkdir(); new.mkdir()
            (old/'x').write_bytes(b'old'); (new/'x').write_bytes(b'new')
            plan = dict(retained_artifact_inventories={str(old): c.l.file_inventory(old)},
                knucleotide_qualification=dict(artifact_inventories={str(new):
                    {'x': hashlib.sha256(b'new').hexdigest()}}))
            c.verify_input_inventories(plan)
            for target in (old, new):
                (target/'extra').write_bytes(b'late')
                with self.assertRaises(ValueError): c.verify_input_inventories(plan)
                (target/'extra').unlink()


if __name__ == '__main__': unittest.main()
