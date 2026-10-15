"""Distinct-program full-cohort contracts; no native timing or qualification."""
import ast
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


HERE = Path(__file__).resolve().parent
m = load('rebol_full60_tested', HERE/'rebol_full60.py')
old_tests = load('rebol_full90_test_fixtures', HERE/'test_rebol_full.py')


def fixture():
    with patch.object(old_tests, 'm', m):
        return old_tests.fixture()


def completed(plan, failed_key=None):
    with patch.object(old_tests, 'm', m):
        return old_tests.completed(plan, failed_key)


def base_fixture(benchmark='pidigits'):
    base, admission, environment, pins = old_tests.base_fixture(benchmark)
    base['alias_policy']['publication_forms'] = ['compact']
    return base, admission, environment, pins


class Full60(unittest.TestCase):
    def test_all_ten_programs_have_three_fresh_samples_and_controls(self):
        plan = fixture()
        slots = m.schedule_for(plan['manifests'])
        self.assertEqual(len(slots), 60)
        self.assertEqual(len({slot[3] for slot in slots}), 20)
        self.assertEqual(sum(slot[2] == 'mech-aot-control' for slot in slots), 30)
        self.assertEqual(sum(slot[2].endswith('-compact') for slot in slots), 30)
        self.assertFalse(any('optimized' in slot[2] for slot in slots))
        for bench in m.BENCHES:
            actual = [(round_index, identity) for name, round_index, identity, _ in slots if name == bench]
            subject = f'rebol-{bench}-compact'
            self.assertEqual(actual, [(1, subject), (1, 'mech-aot-control'),
                                     (2, 'mech-aot-control'), (2, subject),
                                     (3, subject), (3, 'mech-aot-control')])

    def test_missing_duplicate_alias_and_wrong_order_reject(self):
        for mutation in ('missing-workload', 'missing-control', 'extra-form', 'copied-timing', 'order'):
            plan = fixture()
            row = plan['manifests'][m.BENCHES[0]]
            if mutation == 'missing-workload':
                plan['manifests'].pop(m.BENCHES[-1])
            elif mutation == 'missing-control':
                row['profiles'].pop()
            elif mutation == 'extra-form':
                row['profiles'].insert(1, dict(row['profiles'][0], id='rebol-regexredux-optimized'))
            elif mutation == 'copied-timing':
                row['profiles'][0]['timing_alias_of'] = 'another-program'
            else:
                row['orders'][1]['profiles'].reverse()
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                m.schedule_for(plan['manifests'])

    def test_full_ledger_accounts_for_every_actual_sample(self):
        plan = fixture()
        report = completed(plan)
        m.check_success_ledger(plan, report)
        self.assertEqual(report['full_performance_runs'], 60)
        self.assertEqual(report['qualified_samples'], 60)
        self.assertTrue(all(len(row['samples_seconds']) == 3 for row in report['programs'].values()))
        for mutation in ('duplicate', 'missing', 'reordered', 'changed-sample'):
            bad = copy.deepcopy(report)
            if mutation == 'duplicate':
                bad['attempts'][1] = copy.deepcopy(bad['attempts'][0])
            elif mutation == 'missing':
                bad['attempts'].pop()
            elif mutation == 'reordered':
                bad['attempts'][0], bad['attempts'][1] = bad['attempts'][1], bad['attempts'][0]
            else:
                bad['programs']['rebol-pidigits-compact']['samples_seconds'][0] += 1
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                m.check_success_ledger(plan, bad)

    def test_failed_subject_preserves_failure_and_skips_only_remaining_two(self):
        plan = fixture()
        key = 'rebol-regexredux-compact'
        report = completed(plan, key)
        m.check_success_ledger(plan, report)
        self.assertEqual(report['full_performance_runs'], 58)
        self.assertEqual(len(report['skipped_failed_profile_slots']), 2)
        self.assertEqual({row['key'] for row in report['skipped_failed_profile_slots']}, {key})
        self.assertNotIn('median_seconds', report['programs'][key])
        self.assertIsNone(report['programs'][key]['time_x_mech'])
        self.assertEqual(len(report['programs']['regexredux:rebol-full-study:mech-control']['samples_seconds']), 3)
        self.assertEqual(len(report['programs']['rebol-nbody-compact']['samples_seconds']), 3)
        report['skipped_failed_profile_slots'].pop()
        with self.assertRaises(AssertionError):
            m.check_success_ledger(plan, report)

    def test_failed_control_retains_subject_samples_without_comparison(self):
        plan = fixture()
        report = completed(plan, 'regexredux:rebol-full-study:mech-control')
        m.check_success_ledger(plan, report)
        subject = report['programs']['rebol-regexredux-compact']
        self.assertEqual(len(subject['samples_seconds']), 3)
        self.assertIn('median_seconds', subject)
        self.assertIsNone(subject['time_x_mech'])

    def test_only_one_canonical_direct_subject_with_complete_bundle(self):
        for benchmark in m.BENCHES:
            base, admission, environment, pins = base_fixture(benchmark)
            subject = m.subject(base, 'compact', admission, environment, pins)
            self.assertEqual(subject['command'], base['command_prefix'] + ([] if benchmark in m.STDIN_BENCHES else ['{n}']))
            self.assertEqual(subject['physical_inputs'], base['physical_inputs'])
            self.assertEqual(subject['alias_policy']['publication_forms'], ['compact'])
            self.assertFalse(subject['optimization_claim'])
            self.assertNotIn('timing_alias_of', subject)
            with self.assertRaises(AssertionError):
                m.subject(base, 'optimized', admission, environment, pins)
        base, admission, environment, pins = base_fixture()
        for mutation in ('old-policy', 'helper', 'image', 'trace'):
            b, a = copy.deepcopy(base), copy.deepcopy(admission)
            if mutation == 'old-policy':
                b['alias_policy']['publication_forms'].append('optimized')
            elif mutation == 'helper':
                b['physical_inputs'].pop()
            elif mutation == 'image':
                a['extension_image']['sha256'] = 'd'*64
            else:
                b['command_prefix'].append('--trace')
            with self.subTest(mutation=mutation), self.assertRaises(AssertionError):
                m.subject(b, 'compact', a, environment, pins)

    def test_plan_preserves_old_proposal_and_emits_ten_canonical_programs(self):
        bases, pins = [], {}
        for bench in m.BENCHES:
            base, admission, environment, values = base_fixture(bench)
            main = f'/source/{bench}/main.reb'
            base['main']['path'] = base['physical_inputs'][0]['path'] = main
            base['command_prefix'][-1] = main
            values[main] = values.pop('/source/main.reb')
            pins.update(values)
            bases.append(base)
        original = dict(language='rebol3', publication_forms_proposed=['compact', 'optimized'],
                        publication_alias_policy=m.ORIGINAL_ALIAS_POLICY,
                        profiles=[dict(id=base['original_profile_id']) for base in bases])
        qualification = dict(path='/qualified.json', sha256='a'*64)
        admission.update(schema='rebol-pre-timing-admission-v1', manifest=qualification, bases=bases,
            scope=dict(required_work_qualified=True, canonical_source_count_qualified=True,
                       bounded_output_qualified=True, extension_abi_qualified=True, full_primitive_fixtures_qualified=True,
                       runtime_source_equivalence_proven=False, full_timing_qualified=False, chart_admission=False))
        pins[str(m.PROFILES)] = 'a'*64
        def pin(pins, resolutions, path, sha):
            pins[str(path)] = sha
            resolutions[str(path)] = str(path)
        evidence = SimpleNamespace(pin=pin, document=lambda *args: original,
                                   environment=lambda output: dict(environment))
        held = SimpleNamespace(evidence=evidence, pins=pins, resolutions={})
        def controls(_):
            return {bench: dict(id='mech-aot-control', language='mech', benchmark=bench) for bench in m.BENCHES}
        helpers = SimpleNamespace(controls=controls, SAMPLER_PINS={}, SHARED=Path('/shared'), SHARED_SHA='a'*64,
            SUPERVISOR=Path('/supervisor'), SUPERVISOR_SHA='b'*64, PYTHON=Path('/python'), PYTHON_SHA='c'*64,
            LOCK=Path('/tmp/mech-clbg-timing.lock'), FULL={bench:(100, 10, 'd'*64) for bench in m.BENCHES})
        receipts = SimpleNamespace(HELPER=Path('/receipts'), HELPER_SHA='e'*64)
        sources = {str(Path(m.__file__)): 'f'*64, str(m.PACKET/'POLICY.md'): 'a'*64}
        result = m.build_plan(admission, held, helpers, receipts, m.PACKET/'run-v1', qualification, {}, sources)
        self.assertEqual((result['source_work_profiles'], result['canonical_loc_profiles']), (10, 10))
        self.assertEqual((result['rebol_samples'], result['matched_mech_samples'], result['full_processes']), (30, 30, 60))
        self.assertEqual(result['subject_policy']['publication_forms'], ['compact'])
        self.assertEqual(len(result['schedule']), 60)
        self.assertEqual(result['cohort_policy_file']['sha256'], 'a'*64)
        self.assertEqual(original['publication_forms_proposed'], ['compact', 'optimized'])
        self.assertTrue(all(len(manifest['profiles']) == 2 for manifest in result['manifests'].values()))
        self.assertTrue(all((manifest['timeout_seconds'], manifest['supervisor_timeout_seconds'], manifest['maximum_rss_mib'])
                           == (21600, 22200, 10240) for manifest in result['manifests'].values()))
        admission['scope']['required_work_qualified'] = False
        with self.assertRaises(AssertionError):
            m.build_plan(admission, held, helpers, receipts, m.PACKET/'run-v1', qualification, {}, sources)

    def test_frozen_measurement_receipt_and_cleanup_functions_remain_exact(self):
        before = ast.parse((HERE/'rebol_full.py').read_text())
        after = ast.parse(Path(m.__file__).read_text())
        old = {node.name: node for node in before.body if isinstance(node, ast.FunctionDef)}
        new = {node.name: node for node in after.body if isinstance(node, ast.FunctionDef)}
        names = ('regular', 'read_bytes', 'sha', 'merge', 'reference', 'load', 'initial_rows', 'summarize',
                 'attempt_paths', 'check_attempt', 'record_attempt', 'source_policy', 'write_new', 'verify_written',
                 'suite_lease', 'check_inputs', 'artifact_inventory', 'downgrade_terminal', 'finalize_once',
                 'final_failure_guard')
        for name in names:
            self.assertEqual(ast.dump(old[name], include_attributes=False), ast.dump(new[name], include_attributes=False), name)
        for name in ('HELPERS_SHA', 'RECEIPTS_SHA', 'POLICY', 'FORBIDDEN_ENV'):
            original = load('rebol_original_constant_'+name, HERE/'rebol_full.py')
            self.assertEqual(getattr(m, name), getattr(original, name))

    def test_reviewed_qualification_entry_is_resolved_before_use(self):
        files = {str(path.relative_to(m.ROOT)): 'a'*64 for path in m.SOURCE_FILES}
        dependencies = {str(path.relative_to(m.ROOT)): sha for path, sha in (
            (m.QUALIFIER, 'b'*64), (m.HELPERS, m.HELPERS_SHA),
            (m.RECEIPTS, m.RECEIPTS_SHA), (m.ORIGINAL, m.ORIGINAL_SHA))}
        review = dict(schema='rebol-full60-source-review-v1',
            status='independent-source-review-complete-native-timing-pending', independent_review=True,
            files=files, dependencies=dependencies, full_timing_qualified=False, chart_admission=False)
        raw = json.dumps(review).encode()
        reference = dict(path='/source-review.json', sha256=m.digest(raw))
        expected = {str(m.ROOT/name): sha for name, sha in {**files, **dependencies}.items()}
        qualified = SimpleNamespace(ROOT=m.ROOT, review_context=object())
        calls = []
        def controller(sha):
            calls.append(sha)
            return qualified
        with patch.object(m, 'read_bytes', return_value=raw), patch.object(m, 'sha', side_effect=lambda path: expected[str(path)]), \
             patch.object(m, 'load', return_value=SimpleNamespace(load_controller=controller)) as entry:
            actual, pins = m.source_intake(reference)
        self.assertIs(actual, qualified)
        self.assertEqual(calls, ['b'*64])
        self.assertEqual(pins[reference['path']], reference['sha256'])
        self.assertIn(str(m.PACKET/'POLICY.md'), pins)
        entry.assert_called_once_with(m.QUALIFIER, 'b'*64, 'rebol_full60_qualification_entry')


if __name__ == '__main__':
    unittest.main()
