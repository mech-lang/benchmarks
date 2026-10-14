"""Pure saved-metadata and adversarial gate tests; no native process launches."""
import copy
import importlib.util
import json
from pathlib import Path
import types
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).with_name('elixir_full.py')
spec = importlib.util.spec_from_file_location('elixir_full_test_subject', SOURCE)
full = importlib.util.module_from_spec(spec)
spec.loader.exec_module(full)


class FullPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original, cls.compiled, cls.counted, cls.files, cls.pins = full.prerequisites()
        cls.plan = full.build_draft(full.HERE / 'run-v1')

    def candidate(self, original=None, compiled=None, counted=None, files=None, pins=None):
        identifier = 'elixir-nbody-compact'
        return full.candidate(original or self.original[identifier], compiled or self.compiled[identifier],
            counted or self.counted[identifier], files or self.files, self.pins if pins is None else pins)

    def test_saved_cohort_is_sixty_elixir_and_thirty_matched_controls(self):
        slots = self.plan['schedule']
        self.assertEqual(len(slots), 90)
        self.assertEqual(sum(s[2].startswith('elixir-') for s in slots), 60)
        self.assertEqual(sum(s[2] == 'mech-aot-control' for s in slots), 30)
        self.assertEqual({slots.count(s) for s in slots}, {1})
        self.assertFalse(self.plan['pins_verified'])
        self.assertFalse(self.plan['full_timings_qualified'])
        self.assertFalse(self.plan['chart_admission'])

    def test_rotation_balances_each_position(self):
        for manifest in self.plan['manifests'].values():
            for position in range(3):
                self.assertEqual(len({o['profiles'][position] for o in manifest['orders']}), 3)

    def test_reject_missing_or_duplicate_cohort(self):
        rows = list(self.original.values())
        for invalid in [rows[:-1], rows[:-1] + [rows[0]]]:
            with self.assertRaises(AssertionError):
                full.keyed(invalid)

    def test_reject_missing_benchmark_or_changed_rotation(self):
        manifests = copy.deepcopy(self.plan['manifests'])
        manifests.pop('nbody')
        with self.assertRaises(AssertionError):
            full.schedule_for(manifests)
        manifests = copy.deepcopy(self.plan['manifests'])
        manifests['nbody']['orders'][1]['profiles'].reverse()
        with self.assertRaises(AssertionError):
            full.schedule_for(manifests)

    def test_retains_first_compile_nbody_ebin(self):
        row = self.candidate()
        self.assertIn('/first-compiler-stdio-owner-v1/ebin', row['command'][2])
        self.assertEqual(row['command'], self.original[row['id']]['command'])
        self.assertEqual(row['cwd'], str(Path(row['source']).parent))

    def test_reject_diagnostic_even_if_both_source_commands_changed(self):
        original = copy.deepcopy(self.original['elixir-nbody-compact'])
        compiled = copy.deepcopy(self.compiled['elixir-nbody-compact'])
        original['command'].insert(1, '--no-halt')
        compiled['retained_command'] = original['command'][:]
        with self.assertRaises(AssertionError):
            self.candidate(original=original, compiled=compiled)

    def test_reject_runtime_policy_change(self):
        for field, value in [('ELIXIR_ERL_OPTIONS', '+S 1:1'), ('ERL_FLAGS', '+JPperf true')]:
            original = copy.deepcopy(self.original['elixir-nbody-compact'])
            compiled = copy.deepcopy(self.compiled['elixir-nbody-compact'])
            original['runtime_environment'][field] = value
            compiled['runtime_environment'][field] = value
            with self.assertRaises(AssertionError):
                self.candidate(original=original, compiled=compiled)

    def test_reject_loc_role_omission_and_source_substitution(self):
        counted = copy.deepcopy(self.counted['elixir-nbody-compact'])
        counted['inputs'].pop()
        with self.assertRaises(AssertionError):
            self.candidate(counted=counted)
        files = copy.deepcopy(self.files)
        files['elixir-nbody-compact--application']['source_sha256'] = '0' * 64
        with self.assertRaises(AssertionError):
            self.candidate(files=files)

    def test_reject_loc_aggregate_or_qualification_change(self):
        for field, value in [('canonical_loc', 1), ('formatted_loc', 1), ('canonical_loc_qualified', False)]:
            counted = copy.deepcopy(self.counted['elixir-nbody-compact'])
            counted[field] = value
            with self.assertRaises(AssertionError):
                self.candidate(counted=counted)

    def test_reject_changed_beam_and_unpinned_launcher(self):
        compiled = copy.deepcopy(self.compiled['elixir-nbody-compact'])
        compiled['beams'][0]['sha256'] = '0' * 64
        with self.assertRaises(AssertionError):
            self.candidate(compiled=compiled)
        pins = dict(self.pins)
        pins.pop(self.original['elixir-nbody-compact']['command'][0])
        with self.assertRaises(AssertionError):
            self.candidate(pins=pins)

    def test_archived_owner_bound_to_unique_existing_pin(self):
        row = self.candidate()
        self.assertEqual(len(row['retained_owner_evidence']), 2)
        self.assertTrue(all('/archive/languages/elixir/' in p['path'] for p in row['retained_owner_evidence']))
        pins = dict(self.pins)
        pins[row['retained_owner_evidence'][0]['path'] + '/Elixir.Clbg.Main.ownership.etf'] = row['owners'][0]['sha256']
        with self.assertRaises(AssertionError):
            self.candidate(pins=pins)

    def test_controls_preserve_distinct_reviewed_command_shapes(self):
        controls = {b: m['profiles'][2] for b, m in self.plan['manifests'].items()}
        self.assertEqual(len(controls['regexredux']['command']), 1)
        self.assertEqual(controls['mandelbrot']['command'][1:], ['{n}', '8'])
        self.assertEqual(controls['pidigits']['command'][1:], ['{n}'])
        self.assertIn('five16-rows-loop-fma', controls['mandelbrot']['binary'])

    def test_source_aliases_remain_twenty_independent_forms(self):
        for manifest in self.plan['manifests'].values():
            a, b = manifest['profiles'][:2]
            self.assertEqual(a['source_sha256'], b['source_sha256'])
            self.assertNotEqual(a['source'], b['source'])
            self.assertNotEqual(a['key'], b['key'])
            self.assertFalse(a['optimization_claim'])
            self.assertFalse(b['optimization_claim'])

    def test_draft_cannot_execute(self):
        with self.assertRaises(AssertionError):
            full.validate_plan(self.plan, prepared=True)

    def test_exact_prepared_plan_and_tampered_command_closure_reference(self):
        prepared = copy.deepcopy(self.plan)
        prepared.update(status='prepared-awaiting-independent-review', pins_verified=True)
        with patch.object(full, 'build_draft', return_value=self.plan.copy()):
            full.validate_plan(prepared, prepared=True)
        mutations = [lambda p: p['manifests']['nbody']['profiles'][0]['command'].append('--trace'),
                     lambda p: p['pins'].pop(str(full.WORK)),
                     lambda p: p['manifests']['pidigits']['full_output_reference'].update(bytes=1),
                     lambda p: p.update(chart_admission=True)]
        for mutate in mutations:
            changed = copy.deepcopy(prepared)
            mutate(changed)
            with patch.object(full, 'build_draft', return_value=copy.deepcopy(self.plan)):
                with self.assertRaises(AssertionError):
                    full.validate_plan(changed, prepared=True)

    def test_full_workloads_and_retained_input_pins(self):
        self.assertEqual({b: m['size'] for b, m in self.plan['manifests'].items()},
            dict(regexredux=5000000, revcomp=25000000, pidigits=10000, spectralnorm=5500,
                 mandelbrot=16000, fasta=25000000, knucleotide=25000000, binarytrees=21,
                 nbody=50000000, fannkuchredux=12))
        for relative in ['knucleotide/.build/knucleotide-input25000000.txt', 'regexredux/.build/input5000000.txt']:
            self.assertIn(str(full.CLBG / relative), self.plan['pins'])

    def test_artifact_escape_and_conflicting_pins_fail(self):
        for path in ['../outside', '/tmp/outside']:
            with self.assertRaises(AssertionError):
                full.artifact_pins(Path('/tmp/artifacts'), {path: dict(bytes=1, sha256='0' * 64)})
        with self.assertRaises(AssertionError):
            full.merge({'a': '0' * 64}, {'a': '1' * 64})

    def test_lock_replacement_is_rejected(self):
        held = types.SimpleNamespace(st_dev=1, st_ino=79859134)
        named = types.SimpleNamespace(st_dev=1, st_ino=123)
        lock = types.SimpleNamespace(fileno=lambda: 2)
        with patch.object(full.os, 'fstat', return_value=held), patch.object(Path, 'stat', return_value=named):
            with self.assertRaises(AssertionError):
                full.verify_lock(lock)


if __name__ == '__main__':
    unittest.main()
