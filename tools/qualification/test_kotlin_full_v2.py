"""Saved-evidence and adversarial admission tests; no native/runtime hashing."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

PATH = Path(__file__).with_name('kotlin_full_v2.py')
SPEC = importlib.util.spec_from_file_location('tested_kotlin_full_v2', PATH)
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class AdditiveKotlinFull(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        packet = m.ROOT/'experiments/kotlin/required-work-qualification-v2'
        cls.receipt = json.loads((packet/'qualified-work.json').read_bytes())
        cls.decisions = json.loads((packet/'decisions.json').read_bytes())
        cls.reference = m.ref(packet/'qualified-work.json', m.full.sha(packet/'qualified-work.json'))
        cls.original, cls.counted, cls.files, cls.work, cls.pins, cls.closures = m.prerequisites(cls.reference)
        cls.last = {kind: json.loads(Path(reference['path']).read_bytes())
                    for kind, reference in m.CAPTURES['final'].items()}
        cls.durable = {name: json.loads((m.LAST_JOB/name).read_bytes()) for name in
                       ('request.json', 'launch.json', 'worker-started.json', 'command-started.json', 'terminal.json')}

    def check(self, receipt=None, decisions=None, pins=None):
        return m.validate_decisions(receipt or self.receipt, decisions or self.decisions,
                                    self.work, pins or self.pins)

    def test_actual_twenty_independent_decisions(self):
        self.assertEqual(set(self.check()), set(self.original))
        self.assertEqual(len(self.original), 20)
        self.assertEqual(len(self.closures), 8)  # work, three captures, three durable owners, LOC
        self.assertEqual(self.pins[str(m.FROZEN)], m.FROZEN_SHA)

    def test_both_failed_producers_are_preserved(self):
        for group in ('first', 'remaining'):
            report = json.loads(Path(m.CAPTURES[group]['report']['path']).read_bytes())
            self.assertEqual(report['status'], 'failed')
        self.assertEqual(self.last['report']['native_processes_started'], 1)
        self.assertEqual(self.last['report']['prior_native_commands_reused'], 3)

    def test_pi_uses_observed_interpreter_path_without_numeric_count_claim(self):
        for d in self.decisions['profiles']:
            if d['id'].startswith('kotlin-pidigits-'):
                self.assertTrue(d['checks']['single_entry_execution_path'])
                self.assertNotIn('single_entry_compiled_versions', d['checks'])
                self.assertEqual(d['single_entry_execution_path'], 'interpreted-main')
                self.assertIs(d['numeric_runtime_division_count_proved'], False)

    def test_missing_form_or_duplicate_form_fails(self):
        for duplicate in (False, True):
            decisions = copy.deepcopy(self.decisions)
            decisions['profiles'].pop()
            if duplicate: decisions['profiles'].append(copy.deepcopy(decisions['profiles'][0]))
            with self.assertRaises(AssertionError): self.check(decisions=decisions)

    def test_source_class_runtime_and_environment_changes_fail(self):
        changes = [lambda d: d['physical_inputs'][0].update(sha256='0'*64),
                   lambda d: d['class_artifacts'][0].update(sha256='0'*64),
                   lambda d: d['runtime_binding'].update(java='/different/java'),
                   lambda d: d['runtime_environment'].update(JAVA_TOOL_OPTIONS='-Xint'),
                   lambda d: d['retained_runtime_command'].append('-Xint')]
        for change in changes:
            decisions = copy.deepcopy(self.decisions); change(decisions['profiles'][0])
            with self.subTest(change=change), self.assertRaises(AssertionError): self.check(decisions=decisions)

    def test_missing_native_source_or_independent_review_evidence_fails(self):
        for suffix in ('hotspot.xml', 'process.json', 'summary.json', 'Main.kt', 'review.json'):
            decisions = copy.deepcopy(self.decisions); evidence = decisions['profiles'][0]['evidence_pins']
            path = next(path for path in evidence if path.endswith('/'+suffix)); del evidence[path]
            with self.subTest(suffix=suffix), self.assertRaises(AssertionError): self.check(decisions=decisions)

    def test_changed_evidence_pin_fails(self):
        decisions = copy.deepcopy(self.decisions)
        path = next(iter(decisions['profiles'][0]['evidence_pins']))
        decisions['profiles'][0]['evidence_pins'][path] = '0'*64
        with self.assertRaises(AssertionError): self.check(decisions=decisions)

    def test_old_compiled_main_gate_cannot_replace_execution_path(self):
        decisions = copy.deepcopy(self.decisions)
        pi = next(d for d in decisions['profiles'] if d['id'] == 'kotlin-pidigits-compact')
        del pi['checks']['single_entry_execution_path']; pi['checks']['single_entry_compiled_versions'] = True
        with self.assertRaises(AssertionError): self.check(decisions=decisions)

    def test_unqualified_checks_and_invented_numeric_counts_fail(self):
        for field in ('single_entry_execution_path', 'numeric_runtime_division_count_proved'):
            decisions = copy.deepcopy(self.decisions)
            pi = next(d for d in decisions['profiles'] if d['id'] == 'kotlin-pidigits-optimized')
            pi[field] = 'compiled-main' if field == 'single_entry_execution_path' else True
            with self.subTest(field=field), self.assertRaises(AssertionError): self.check(decisions=decisions)
        decisions = copy.deepcopy(self.decisions)
        decisions['profiles'][0]['checks']['long_lived_graph_gc_roots'] = False
        with self.assertRaises(AssertionError): self.check(decisions=decisions)

    def test_native_and_review_chain_cannot_be_substituted(self):
        for field in ('single_entry_captures', 'independent_reviews', 'compiled_work'):
            receipt = copy.deepcopy(self.receipt); receipt[field] = {}
            with self.subTest(field=field), self.assertRaises(AssertionError): self.check(receipt=receipt)

    def test_timing_feasibility_and_chart_promotion_fail(self):
        for field in ('full_timings_qualified', 'full_size_feasibility_qualified', 'chart_admission'):
            receipt = copy.deepcopy(self.receipt); receipt[field] = True
            with self.subTest(field=field), self.assertRaises(AssertionError): self.check(receipt=receipt)
        receipt = copy.deepcopy(self.receipt); receipt['benchmark_samples'] = False
        with self.assertRaises(AssertionError): self.check(receipt=receipt)

    def test_final_plan_cannot_repeat_a_prior_capture(self):
        plan = copy.deepcopy(self.last['plan'])
        plan['profiles'].append(self.work['profiles'][0]); plan['planned_native_commands'] = 2
        with self.assertRaises(AssertionError):
            m.validate_final_metadata(plan, self.last['report'], self.last['terminal'], self.work)

    def test_final_incomplete_or_unowned_terminal_fails(self):
        changes = [lambda p,r,t: r.update(active={'pid': 62778}),
                   lambda p,r,t: t.update(common_mutex_held=False),
                   lambda p,r,t: t['process_receipt_errors'].append('unreaped'),
                   lambda p,r,t: r.update(prior_native_commands_reused=2),
                   lambda p,r,t: r.update(native_processes_started=True),
                   lambda p,r,t: t.update(report_sha256='0'*64),
                   lambda p,r,t: r.update(source_work_qualified=True)]
        for change in changes:
            p,r,t = (copy.deepcopy(self.last[k]) for k in ('plan','report','terminal')); change(p,r,t)
            with self.subTest(change=change), self.assertRaises(AssertionError): m.validate_final_metadata(p,r,t,self.work)

    def test_final_durable_exact_argv_and_identity(self):
        m.check_final_durable(self.durable)
        for option in ('-u', '-I', '-S', '-B'):
            documents = copy.deepcopy(self.durable); documents['request.json']['command'].remove(option)
            with self.subTest(option=option), self.assertRaises(AssertionError): m.check_final_durable(documents)
        for change in (lambda d: d['request.json']['command'].insert(1, '-O'),
                       lambda d: d['request.json'].update(cwd='/tmp'),
                       lambda d: d['terminal.json'].update(command_pid=62777),
                       lambda d: d['terminal.json']['worker_identity'].update(pid=1),
                       lambda d: d['terminal.json'].update(exit_code=1),
                       lambda d: d['worker-started.json'].update(inherited_private_lease=False)):
            documents = copy.deepcopy(self.durable); change(documents)
            with self.subTest(change=change), self.assertRaises(AssertionError): m.check_final_durable(documents)

    def test_changed_qualification_file_fails_before_capture_replay(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'qualified.json'; path.write_text(json.dumps(self.receipt))
            reference = m.ref(path, m.full.sha(path)); path.write_text('{}')
            with self.assertRaises(AssertionError): m.prerequisites(reference)

    def test_late_nested_artifact_and_symlink_are_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp); (directory/'terminal.json').write_text('{}')
            data = directory/'receipt.json'; data.write_text('{}')
            closure = dict(directory=str(directory), terminal=m.ref(directory/'terminal.json', m.full.sha(directory/'terminal.json')),
                           artifacts={'receipt.json':dict(bytes=2, sha256=m.full.sha(data))})
            m.full.verify_artifact_inventories([closure])
            nested = directory/'nested'; nested.mkdir(); (nested/'terminal.json').write_text('{}')
            with self.assertRaises(AssertionError): m.full.verify_artifact_inventories([closure])
            (nested/'terminal.json').unlink(); nested.rmdir(); (directory/'alias').symlink_to(data)
            with self.assertRaises(AssertionError): m.full.verify_artifact_inventories([closure])

    def test_actual_canonical_counts_keep_formatted_unqualified(self):
        for identity in self.original:
            row = m.full.candidate(self.original[identity], self.counted[identity], self.files, self.work, self.pins)
            self.assertTrue(row['canonical_loc_qualified'])
            self.assertIs(row['formatted_loc_qualified'], False)
            self.assertIsNone(row['formatted_loc'])
            self.assertFalse(row['optimization_claim'])

    def test_metadata_draft_retains_full90_and_frozen_runtime_policy(self):
        # Keep this in memory: no prepared or runnable plan is created.
        values = (self.original, self.counted, self.files, self.work, self.pins, self.closures)
        with patch.object(m.full, 'prerequisites', return_value=copy.deepcopy(values)):
            draft = m.full.build_draft('/synthetic-only/uncreated-full90', self.reference)
        self.assertFalse(draft['pins_verified'])
        self.assertEqual(draft['full_processes'], 90)
        self.assertEqual(draft['controller'], str(PATH.resolve()))
        self.assertEqual(draft['pins'][str(m.FROZEN)], m.FROZEN_SHA)
        self.assertEqual(len(draft['schedule']), 90)
        for manifest in draft['manifests'].values():
            self.assertEqual(manifest['samples'], 3)
            self.assertTrue(manifest['canonical_full_workload'])
            self.assertEqual(manifest['maximum_rss_mib'], 10240)
            for row in manifest['profiles'][:2]:
                self.assertEqual(row['command'][1:5], m.full.FLAGS)
        self.assertEqual(m.full.run_locked.__code__.co_filename, str(m.FROZEN))
        self.assertEqual(m.full.schedule_for.__code__.co_filename, str(m.FROZEN))


if __name__ == '__main__': unittest.main()
