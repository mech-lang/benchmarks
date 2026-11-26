import tempfile
from itertools import permutations
from math import log
import unittest
from pathlib import Path
from unittest.mock import patch

from campaign_stats import paired_log, simultaneous
from compare_rebuilt import require_pair, run_scoped_campaign, write_new
from rebuild import read
from verify import (SCOPED_POLICY, ScopedCampaign, compilation_inputs, compiler_gates, compiler_prerequisite,
                    crossed_units, crossover_pair, crossover_plan, inventory, scoped_compiler_slots,
                    scoped_schedule, verify_inventory, verify_leg_order, verify_session)


class CampaignRunnerTests(unittest.TestCase):
    def test_identical_roles_are_allowed_only_for_calibration(self):
        binding = {"label": "control", "build_directory": "/build",
                   "source_commit": "reviewed", "compiler_sha256": "pinned",
                   "81": {"sha256": "worker"}, "silesia": {"sha256": "encoder"}}
        alias = {**binding, "label": "candidate"}
        require_pair(binding, alias, calibration=True)
        with self.assertRaises(ValueError):
            require_pair(binding, alias, calibration=False)
        with self.assertRaises(ValueError):
            require_pair(binding, {**alias, "compiler_sha256": "changed"}, calibration=True)
        require_pair(binding, {**alias, "source_commit": "candidate", "build_directory": "/new"},
                     calibration=False)

    def test_seals_reject_missing_changed_or_additional_raw_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            raw = folder / "raw.json"
            raw.write_bytes(b"expected")
            sealed = inventory(folder)
            verify_inventory(folder, sealed)
            raw.write_bytes(b"tampered")
            with self.assertRaises(ValueError):
                verify_inventory(folder, sealed)
            raw.unlink()
            with self.assertRaises(ValueError):
                verify_inventory(folder, sealed)
            raw.write_bytes(b"expected")
            (folder / "added.json").touch()
            with self.assertRaises(ValueError):
                verify_inventory(folder, sealed)

    def test_session_must_be_complete_and_at_the_same_inputs_to_resume(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            with self.assertRaises(ValueError):
                verify_session(folder, "manifest", "qualify", "calibration")
            info = {"manifest_sha256": "manifest", "calibration_sha256": "calibration",
                    "stage": "qualify", "session": folder.name,
                    "start_utc": "00", "end_utc": "01", "raw_files": {}}
            path = folder / "record.json"
            write_new(path, info)
            self.assertEqual(verify_session(folder, "manifest", "qualify", "calibration"), info)
            with self.assertRaises(ValueError):
                verify_session(folder, "manifest", "qualify", "changed")
            with self.assertRaises(FileExistsError):
                write_new(path, info)


    def test_crossover_orients_the_compiler_effect_and_cancels_fixed_slot_bias(self):
        timings = {"reviewed": 10, "candidate": 8}
        slot_bias = {"control": 1.0, "candidate": 1.25}
        plans = list(crossover_plan(("reviewed",), 1, False))

        def cycle(step):
            slot_values = {slot: timings[label] * slot_bias[slot] for slot, label in step["slots"].items()}
            return {"file": paired_log(slot_values["candidate"], slot_values["control"])}

        first, swapped = [cycle(step) for step in plans[:2]]
        self.assertAlmostEqual(first["file"], 0)
        self.assertAlmostEqual(crossed_units([first] * 2, [swapped] * 2, 2)[0]["file"], log(0.8))
        bindings = {name: {"label": name, "build_directory": name, "source_commit": name}
                    for name in timings}
        self.assertEqual(crossover_pair(bindings, plans[1], False)["control"]["source_commit"], "candidate")
        aa = next(crossover_plan(("reviewed",), 2, True))
        self.assertEqual(aa["slots"], {"control": "reviewed", "candidate": "reviewed"})

    def test_ordinals_interleave_controls_and_reverse_leg_startups(self):
        policy = read(SCOPED_POLICY)
        self.assertEqual([row[0] for row in scoped_schedule(policy, "calibrate")],
                         ["reviewed-1", "previous-1", "reviewed-2", "previous-2", "reviewed-3", "previous-3"])
        self.assertEqual([row[1] for row in scoped_schedule(policy, "qualify")], [1, 2, 3])
        self.assertEqual([row[1] for row in scoped_schedule(policy, "confirm")], [4, 5, 6])
        for _, ordinal, controls in scoped_schedule(policy, "qualify") + scoped_schedule(policy, "confirm"):
            plan = list(crossover_plan(controls, ordinal, False))
            expected = ["A", "B", "B", "A"] if ordinal % 2 else ["B", "A", "A", "B"]
            self.assertEqual([step["leg"] for step in plan], expected * 2)
            self.assertEqual(plan[0]["comparison"], "reviewed" if ordinal % 2 else "previous")

    def test_compiler_slots_balance_absolute_launch_positions_in_each_batch(self):
        policy = read(SCOPED_POLICY)

        def positions(stage, control=None):
            orders = []
            for _, ordinal, controls in scoped_schedule(policy, stage):
                if control is not None and controls != (control,):
                    continue
                slots = scoped_compiler_slots(policy, stage, controls, ordinal)
                if control is not None:
                    self.assertEqual(set(slots.values()), {control})
                measured = [slot for sequence in permutations(slots) for slot in sequence]
                orders.append([*slots, *measured])
            return orders

        for schedules in (positions("calibrate", "reviewed"), positions("calibrate", "previous"),
                          positions("qualify"), positions("confirm")):
            self.assertEqual(len(schedules), 3)
            for column in zip(*schedules, strict=True):
                self.assertEqual(len(set(column)), 3)

    def test_scoped_compiler_verifier_rejects_valid_permutations_in_the_wrong_launch_order(self):
        policy = read(SCOPED_POLICY)
        slots = scoped_compiler_slots(policy, "calibrate", ("reviewed",), 2)
        blocks = [{"order": list(order), "samples": dict.fromkeys(order)}
                  for order in permutations(slots)]
        wrong = {"slots": slots, "warmup": dict.fromkeys(slots), "blocks": blocks[::-1]}
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            write_new(folder / "observations.json", wrong)
            with self.assertRaisesRegex(ValueError, "launch order"):
                compilation_inputs(folder, slots, {}, "candidate", "control", ordered=True)

    def test_leg_verification_refuses_missing_duplicate_wrong_mapping_and_wrong_order(self):
        expected = list(crossover_plan(("reviewed",), 1, False))
        observed = [{**step, "start_utc": f"{i}", "end_utc": f"{i}"} for i, step in enumerate(expected)]
        verify_leg_order(expected, observed, "0", "4")
        swapped = {**observed[0], "slots": observed[1]["slots"]}
        malformed = [observed[1:], [observed[0], *observed[:-1]],
                     [swapped, *observed[1:]], [observed[1], observed[0], *observed[2:]]]
        for legs in malformed:
            with self.assertRaises(ValueError):
                verify_leg_order(expected, legs, "0", "4")

    def test_resampling_uses_whole_crossed_cycle_pairs(self):
        first = [{"one": 12, "two": -2}, {"one": 52, "two": 38}]
        swapped = [{"one": 10, "two": -6}, {"one": 50, "two": 34}]
        units = crossed_units(first, swapped, 2)
        self.assertEqual(units, [{"one": 1.0, "two": 2.0}] * 2)
        result = simultaneous({"fixtures/forward": [units] * 3}, replicates=20)
        self.assertEqual(result["cycles_per_session"], {"fixtures/forward": 2})
        self.assertEqual(result["coordinates"]["one"]["interval95"], [1.0, 1.0])
        self.assertEqual(result["coordinates"]["two"]["interval95"], [2.0, 2.0])
        with self.assertRaises(ValueError):
            crossed_units(first, swapped[:1], 2)

    def test_runtime_requires_a_recomputed_passing_compiler_scope(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            compiler = ScopedCampaign({}, "manifest", root, {}, "compiler", {})
            with self.assertRaisesRegex(ValueError, "passing compiler assessment"):
                compiler_prerequisite(compiler)
            (root / "assessment.json").write_text("{}")
            with patch("verify.verify_scoped_assessment", return_value={"decision": "unresolved"}) as verify:
                with self.assertRaisesRegex(ValueError, "passing compiler assessment"):
                    compiler_prerequisite(compiler)
                verify.assert_called_once_with(compiler)
            with patch("verify.verify_scoped_assessment", return_value={"decision": "pass"}):
                self.assertEqual(len(compiler_prerequisite(compiler)), 64)

    def test_invalid_runtime_calibration_refuses_candidate_timing(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "runtime"
            campaign = ScopedCampaign({}, "manifest", output, {}, "runtime", {}, "compiler-assessment")
            with (patch("verify.open_scope", return_value=campaign),
                  patch("verify.scoped_calibration_seal", return_value=({"decision": "unresolved"}, "seal")),
                  patch("compare_rebuilt.record_scoped_session") as record):
                with self.assertRaisesRegex(ValueError, "Invalid runtime calibration"):
                    run_scoped_campaign(Path("campaign.json"), "qualify", Path("calibration.json"), "runtime")
                record.assert_not_called()
                self.assertFalse(output.exists())

    def test_previous_compiler_rss_requires_a_strictly_negative_upper_bound(self):
        coordinates = {"elapsed_ns": {"interval95": [-0.01, 0.01]},
                       "maximum_resident_bytes": {"interval95": [-0.01, 0.0]}}
        intervals = {"coordinates": coordinates}
        seal = {"decision": "pass", "epsilon": {"elapsed_ns": 0.02, "maximum_resident_bytes": 0.02}}
        self.assertEqual(compiler_gates(intervals, seal, "reviewed")["decision"], "pass")
        self.assertEqual(compiler_gates(intervals, seal, "previous")["decision"], "unresolved")
        coordinates["maximum_resident_bytes"]["interval95"][1] = -0.001
        self.assertEqual(compiler_gates(intervals, seal, "previous")["decision"], "pass")
