import tempfile
from contextlib import redirect_stdout
from copy import deepcopy
from io import StringIO
from itertools import permutations
from math import log
import subprocess
from types import SimpleNamespace
import unittest
from pathlib import Path
from unittest.mock import patch

from campaign_stats import paired_log, simultaneous
from compare_rebuilt import record_scoped_session, require_pair, run_scoped_campaign, write_new
from rebuild import HERE, PARENT, read, sha, write
from replay import fixture_campaign_controller, prepare_fixture_stage, suite81
from verify import (CONTINUATION_PARENT, CONTINUATION_PARENT_PATH, CONTINUATION_SOURCES, FIXTURE_ORACLE,
                    FIXTURE_WITNESSES, RUNTIME_CONTINUATION, SCOPED_BASELINE, SCOPED_POLICY, SCOPED_POLICY_PATH,
                    ScopedCampaign, combined_assessment, committed_blob, committed_tree, compilation_inputs,
                    compiler_gates, compiler_prerequisite, open_scope,
                    crossed_units, crossover_pair, crossover_plan, inventory, scoped_compiler_slots,
                    runtime_calibration_precision, runtime_precision_reference, scoped_assessment, scoped_calibration,
                    scoped_schedule, scoped_summary, scoped_tool_files,
                    validate_fixture_actor_pins, verify_fixture_execution, verify_fixture_stage, verify_inventory,
                    verify_compiler_parent, verify_leg_order, verify_runtime_continuation,
                    verify_scoped_assessment, verify_scoped_campaign, verify_session)


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

    def test_precision_uses_exact_log_width_and_the_eight_pinned_coordinates(self):
        root = HERE.parents[2]
        policy = read(SCOPED_POLICY)["runtime_calibration_precision"]
        reference = runtime_precision_reference(root, policy)
        self.assertEqual(len(reference), 8)
        self.assertIn(("previous", "fixtures/forward/suite-geomean"), reference)
        historical = read(root / policy["reference_path"])["controls"]
        control, coordinate = next(iter(reference))
        lo, hi = reference[control, coordinate]
        width = hi - lo
        for interval, expected in (([lo, hi], "pass"), ([-width / 4, width / 4], "pass"),
                                   ([-width, width], "unresolved")):
            with self.subTest(interval=interval):
                current = deepcopy(historical)
                current[control]["intervals"]["coordinates"][coordinate]["interval95"] = interval
                result = runtime_calibration_precision(current, root, policy)
                first = result["coordinates"][0]
                self.assertEqual(first["reference_log_width"], width)
                self.assertEqual(first["current_log_width"], interval[1] - interval[0])
                self.assertEqual(first["decision"], expected)
                self.assertEqual(result["decision"], expected)
        del current[control]["intervals"]["coordinates"][coordinate]
        with self.assertRaisesRegex(ValueError, "Missing calibration coordinate"):
            runtime_calibration_precision(current, root, policy)
        with self.assertRaisesRegex(ValueError, "expected"):
            runtime_precision_reference(root, {**policy, "reference_sha256": "0" * 64})
        with self.assertRaisesRegex(ValueError, "eight historically excluded"):
            runtime_precision_reference(root, {**policy, "coordinates": policy["coordinates"][:-1]})

    def test_precision_only_miss_refuses_candidate_timing_and_records(self):
        root = HERE.parents[2]
        policy = read(SCOPED_POLICY)
        declaration = policy["runtime_calibration_precision"]
        historical = read(root / declaration["reference_path"])["controls"]
        intervals = [deepcopy(historical[role]["intervals"]) for role in ("reviewed", "previous")]
        for family in intervals:
            for row in family["coordinates"].values():
                row["interval95"] = [0.0, 0.0]
        coordinate = declaration["coordinates"][0][1]
        lo, hi = historical["reviewed"]["intervals"]["coordinates"][coordinate]["interval95"]
        intervals[0]["coordinates"][coordinate]["interval95"] = [lo - hi, hi - lo]
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "runtime"
            output.mkdir()
            folder = Path(temporary)
            (folder / "record.json").write_text("{}")
            campaign = ScopedCampaign({"bench_root": str(root), "purpose": RUNTIME_CONTINUATION}, "manifest", output,
                                      policy, "runtime", {}, "parent-assessment", "unresolved")
            metrics = [{role: {"runtime": {"fixture": []}}} for role in ("reviewed", "previous")]
            with (patch("verify.scoped_sessions", return_value=[(folder, {}), (folder, {})]),
                  patch("verify.scoped_metrics", side_effect=metrics),
                  patch("verify.simultaneous", side_effect=intervals)):
                seal = scoped_calibration(campaign)
            self.assertTrue(all(row["decision"] == "pass" for row in seal["controls"].values()))
            self.assertEqual(seal["precision"]["decision"], "unresolved")
            self.assertEqual(seal["decision"], "unresolved")
            path = output / "calibration.json"
            write_new(path, seal)
            with (patch("verify.open_scope", return_value=campaign),
                  patch("verify.scoped_calibration", return_value=seal),
                  patch("compare_rebuilt.record_scoped_session") as record):
                for stage in ("qualify", "confirm"):
                    with self.subTest(stage=stage), self.assertRaisesRegex(ValueError, "Invalid runtime calibration"):
                        run_scoped_campaign(Path("campaign.json"), stage, path, "runtime")
                    self.assertFalse((output / stage).exists())
                record.assert_not_called()
                self.assertIsNone(verify_scoped_assessment(campaign))
                self.assertEqual(verify_runtime_continuation(campaign)["runtime_calibration"], "unresolved")
                self.assertEqual(verify_runtime_continuation(campaign)["runtime_assessment"], "not_run")
                (output / "qualify").mkdir()
                with self.assertRaisesRegex(ValueError, "Invalid runtime calibration"):
                    verify_scoped_assessment(campaign)


class RuntimeContinuationTests(unittest.TestCase):
    def test_combined_assessment_order_and_invalid_statuses(self):
        cases = (
            ("unresolved", "not_run", "not_run", "unresolved"),
            ("unresolved", "unresolved", "not_run", "unresolved"),
            ("unresolved", "pass", "incomplete", "unresolved"),
            ("unresolved", "pass", "pass", "unresolved"),
            ("unresolved", "pass", "fail", "fail"),
            ("pass", "not_run", "not_run", "incomplete"),
            ("pass", "unresolved", "not_run", "unresolved"),
            ("pass", "pass", "pass", "pass"),
            ("fail", "pass", "pass", "fail"),
        )
        for compiler, calibration, runtime, result in cases:
            with self.subTest(compiler=compiler, calibration=calibration, runtime=runtime):
                self.assertEqual(combined_assessment(compiler, calibration, runtime), result)
        for invalid in ((None, "pass", "pass"), ("pass", "fail", "pass"), ("pass", "pass", "unknown")):
            with self.subTest(invalid=invalid), self.assertRaisesRegex(ValueError, "Invalid"):
                combined_assessment(*invalid)

    def test_unresolved_parent_allows_runtime_calibration_and_prepared_verification(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary).resolve()
            policy = read(SCOPED_POLICY)
            bindings = {role: {"build_directory": role, "configuration_sha256": "same"}
                        for role in ("reviewed", "previous", "candidate")}
            path = output / "prepared-bindings.json"
            write_new(path, bindings)
            manifest = {"purpose": RUNTIME_CONTINUATION, "compiler_parent": {**CONTINUATION_PARENT, "manifest_sha256": "parent"},
                        "source_commits": CONTINUATION_SOURCES, "actors": {"candidate": {"source": str(output)}},
                        "tooling_commit": "continuation", "host": {}, "prepared_bindings_sha256": sha(path)}
            with (patch("verify.load_campaign", return_value=(manifest, "manifest", output, policy)),
                  patch("verify.pinned_bindings", return_value=bindings),
                  patch("verify.subprocess.run", return_value=SimpleNamespace(returncode=0)),
                  patch("verify.verify_compiler_parent", return_value=("unresolved", "parent-assessment", 252)),
                  patch("compare_rebuilt.campaign_host", return_value={}),
                  patch("compare_rebuilt.ordinary_compiler_inputs") as compiler_inputs,
                  patch("compare_rebuilt.record_scoped_session") as record,
                  patch("verify.scoped_calibration", return_value={"decision": "unresolved"})):
                prepared = verify_scoped_campaign(output / "campaign.json", output, "runtime")
                self.assertEqual(prepared["runtime_calibration"], "not_run")
                self.assertEqual(prepared["runtime_assessment"], "not_run")
                self.assertEqual(prepared["overall_assessment"], "unresolved")
                self.assertFalse((output / "runtime").exists())
                run_scoped_campaign(output / "campaign.json", "calibrate", None, "runtime")
                self.assertEqual(record.call_count, 6)
                for call in record.call_args_list:
                    self.assertEqual(call.args[0].compiler_assessment, "parent-assessment")
                    self.assertEqual(call.args[0].parent_compiler_decision, "unresolved")
                compiler_inputs.assert_not_called()
                self.assertFalse((output / "compiler").exists())
            self.assertEqual(read(output / "parent-verification.json")["verified_compiler_invocations"], 252)

    def test_continuation_rejects_compiler_collection(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "campaign.json"
            write_new(path, {"schema": "mech.native-route-campaign.v2", "purpose": RUNTIME_CONTINUATION})
            with (patch("compare_rebuilt.record_scoped_session") as record,
                  self.assertRaisesRegex(ValueError, "forbids compiler collection")):
                run_scoped_campaign(path, "calibrate", None, "compiler")
            record.assert_not_called()

    def test_passing_runtime_does_not_replace_the_compiler_result(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary)
            (output / "calibration.json").touch()
            campaign = ScopedCampaign({}, "manifest", output, {}, "runtime", {}, "parent", "unresolved")
            seal = {"decision": "pass", "sessions": dict.fromkeys(range(6))}
            result = {"decision": "pass", "sessions": {stage: dict.fromkeys(range(3))
                                                       for stage in ("qualify", "confirm")}}
            with (patch("verify.scoped_calibration_seal", return_value=(seal, "calibration")),
                  patch("verify.verify_scoped_result", return_value=result)):
                verified = verify_runtime_continuation(campaign)
            self.assertEqual(verified["runtime_assessment"], "pass")
            self.assertEqual(verified["overall_assessment"], "unresolved")
            self.assertEqual(verified["runtime_sessions"], {"calibrate": 6, "qualify": 3, "confirm": 3})


class CompilerParentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(temp.cleanup)
        cls.root = Path(temp.name).resolve()
        cls.record = cls.root / CONTINUATION_PARENT_PATH
        cls.policy = read(SCOPED_POLICY)
        cls.tool = str(Path(SCOPED_POLICY_PATH).parents[2] / "verify.py")
        (cls.root / SCOPED_POLICY_PATH).parent.mkdir(parents=True)
        write(cls.root / SCOPED_POLICY_PATH, cls.policy)
        (cls.root / cls.tool).write_text("historical tooling\n")
        cls.git("init", "-q")
        cls.git("add", "--", cls.tool, SCOPED_POLICY_PATH)
        cls.git("commit", "-qm", "Synthetic historical tooling")
        tooling = cls.git("rev-parse", "HEAD")

        cls.record.mkdir(parents=True)
        cls.bindings = {role: {"build_directory": str(cls.root / role), "codec_source": str(cls.root / "source"),
                               "compiler_sha256": role, "configuration_sha256": "configuration", "artifacts": {}}
                        for role in ("reviewed", "previous", "candidate")}
        write_new(cls.record / "prepared-bindings.json", cls.bindings)
        for name in ("candidate-recipe.json", "fixture-stage.json"):
            write_new(cls.record / name, {})
        cls.manifest = {**cls.policy, "schema": "mech.native-route-campaign.v2", "purpose": "final-qualification",
                        "source_commits": CONTINUATION_SOURCES, "campaign_id": CONTINUATION_PARENT["campaign_id"],
                        "tooling_commit": tooling, "bench_root": str(cls.root), "output_directory": str(cls.record),
                        "host": {}, "baseline_benchmark_commit": SCOPED_BASELINE, "fixture_stage": {},
                        "actors": {"candidate": {"recipe": str(cls.record / "candidate-recipe.json")}},
                        "qualification_root": str(cls.root), "corpus": str(cls.root / "corpus"), "corpus_manifest_sha256": "",
                        "prepared_bindings_sha256": sha(cls.record / "prepared-bindings.json"),
                        "tooling_files_sha256": {name: sha(cls.root / name) for name in scoped_tool_files(cls.root)}}
        manifest_path = cls.record / "campaign.json"
        write_new(manifest_path, cls.manifest)
        scope = ScopedCampaign(cls.manifest, sha(manifest_path), cls.record / "compiler", cls.policy,
                               "compiler", cls.bindings)
        calibration_hash = None
        with (patch("compare_rebuilt.measure_ordinary_compiler", side_effect=cls.fake_sample),
              patch("compare_rebuilt.campaign_host", return_value={}), redirect_stdout(StringIO())):
            for stage, seal_name in (("calibrate", "calibration"), ("qualify", "qualification"),
                                     ("confirm", "confirmation")):
                (scope.output / stage).mkdir(parents=True)
                for name, ordinal, controls in scoped_schedule(cls.policy, stage):
                    inputs = {role: (row, ordinal) for role, row in cls.bindings.items()}
                    record_scoped_session(scope, scope.output / stage / name, stage, calibration_hash,
                                          ordinal, controls, inputs)
                seal_path = scope.output / (seal_name + ".json")
                if stage == "calibrate":
                    calibration = scoped_calibration(scope)
                    write_new(seal_path, calibration)
                    calibration_hash = sha(seal_path)
                else:
                    write_new(seal_path, scoped_summary(scope, stage, calibration_hash))
        assessment = scoped_assessment(scope, calibration, calibration_hash)
        if assessment["decision"] != "unresolved":
            raise AssertionError("Expected a synthetic unresolved compiler parent.")
        write_new(scope.output / "assessment.json", assessment)
        write_new(cls.record / "compiler-verification.json", {
            "manifest_sha256": scope.digest, "scope": "compiler", "scope_assessment": "unresolved",
            "assessment": "unresolved",
        })
        names = ["campaign.json", "prepared-bindings.json", "candidate-recipe.json", "fixture-stage.json",
                 "compiler-verification.json", "compiler/calibration.json", "compiler/qualification.json",
                 "compiler/confirmation.json", "compiler/assessment.json"]
        cls.git("add", "--", *(str(CONTINUATION_PARENT_PATH / name) for name in names))
        cls.git("commit", "-qm", "Synthetic sealed compiler evidence")
        cls.pins = {**CONTINUATION_PARENT, "tooling_commit": tooling, "evidence_commit": cls.git("rev-parse", "HEAD")}
        cls.reference = {**cls.pins, "manifest_path": str(manifest_path), "record_directory": str(cls.record),
                         "manifest_sha256": scope.digest, "prepared_bindings_sha256": cls.manifest["prepared_bindings_sha256"],
                         "compiler_assessment_sha256": sha(scope.output / "assessment.json")}
        cls.continuation = {**cls.manifest, "purpose": RUNTIME_CONTINUATION}
        (cls.root / cls.tool).write_text("different checkout contents\n")

    @classmethod
    def git(cls, *args):
        return subprocess.check_output(["git", "-c", "user.name=Test", "-c", "user.email=test@example.invalid",
                                        "-c", "commit.gpgsign=false",
                                        "-C", str(cls.root), *args], text=True).strip()

    @staticmethod
    def fake_sample(folder, inputs):
        binding, ordinal = inputs
        is_candidate = binding["compiler_sha256"] == "candidate"
        elapsed = (98 if ordinal % 2 else 102) if is_candidate else 100
        rss = 90 if is_candidate else 100
        folder.mkdir(parents=True)
        (folder / "process.log").write_text(f"{rss} maximum resident set size\n")
        return {**{key: binding[key] for key in ("compiler_sha256", "configuration_sha256", "artifacts")},
                "elapsed_ns": elapsed, "maximum_resident_bytes": rss,
                "command": ["/usr/bin/time", "-l", binding["build_directory"] + "/compile_profile", binding["codec_source"],
                            str(folder / "frontend"), "compact"]}

    def verify_parent(self, reference=None, continuation=None):
        with (patch("verify.CONTINUATION_PARENT", self.pins),
              patch("verify.verify_fixture_stage"), patch("verify.runtime_precision_reference"),
              patch("verify.pinned_bindings", return_value=self.bindings),
              patch("compare_rebuilt.measure_ordinary_compiler") as measure):
            try:
                return verify_compiler_parent(reference or self.reference, continuation or self.continuation, self.bindings)
            finally:
                measure.assert_not_called()

    def test_reconstructs_all_252_invocations_from_the_original_identity(self):
        before = self.git("rev-parse", "HEAD")
        self.assertNotEqual(before, self.pins["tooling_commit"])
        identity = read(self.record / "compiler/calibrate/reviewed-1/started.json")
        self.assertEqual(set(identity), {"manifest_sha256", "calibration_sha256", "stage", "scope",
                                         "compiler_assessment_sha256", "session", "start_utc"})
        self.assertIsNone(identity["compiler_assessment_sha256"])
        self.assertEqual(self.verify_parent(), ("unresolved", self.reference["compiler_assessment_sha256"], 252))
        self.assertEqual(self.git("rev-parse", "HEAD"), before)
        self.assertEqual((self.root / self.tool).read_text(), "different checkout contents\n")

    def test_missing_partial_changed_and_mismatched_parent_evidence_is_rejected(self):
        for name, data, error in (
            ("compiler/qualification.json", None, "Missing or noncanonical"),
            ("compiler/calibrate/reviewed-1/record.json", None, "Incomplete session"),
            ("compiler/assessment.json", b"{}", "committed file"),
            ("compiler/calibrate/reviewed-1/processes/observations.json", b"{}", "Raw evidence changed"),
        ):
            path = self.record / name
            contents = path.read_bytes()
            with self.subTest(name=name):
                try:
                    if data is None:
                        path.unlink()
                    else:
                        path.write_bytes(data)
                    with self.assertRaisesRegex(ValueError, error):
                        self.verify_parent()
                finally:
                    path.write_bytes(contents)
        with self.assertRaisesRegex(ValueError, "changes compiler parent host"):
            self.verify_parent(continuation={**self.continuation, "host": {"machine": "different"}})
        with self.assertRaisesRegex(ValueError, "pinned latest"):
            self.verify_parent(reference={**self.reference, "campaign_id": "F-m1-20261126T181433Z"})
        with (patch("verify.verify_scoped_assessment", return_value={"decision": "fail"}),
              self.assertRaisesRegex(ValueError, "complete pass or unresolved")):
            self.verify_parent()

    def test_rejects_changed_historical_blobs_and_wrong_policy(self):
        tree = committed_tree(self.root, self.pins["tooling_commit"], (SCOPED_POLICY_PATH,))
        self.assertEqual(committed_blob(self.root, tree, SCOPED_POLICY_PATH), (self.root / SCOPED_POLICY_PATH).read_bytes())
        with self.assertRaisesRegex(ValueError, "ordinary committed file"):
            committed_blob(self.root, {SCOPED_POLICY_PATH: ("120000", "blob", tree[SCOPED_POLICY_PATH][2])},
                           SCOPED_POLICY_PATH)
        def wrong_tool(root, tree, name):
            return b"wrong tooling" if name == self.tool else committed_blob(root, tree, name)
        with patch("verify.committed_blob", side_effect=wrong_tool):
            with self.assertRaisesRegex(ValueError, "historical tooling contents differ"):
                self.verify_parent()
        changed = {**self.continuation, "sessions": {**self.policy["sessions"], "confirm": 4}}
        with self.assertRaisesRegex(ValueError, "fixed sessions policy"):
            self.verify_parent(continuation=changed)

    def test_rejects_recursive_parent_and_saved_pass_even_with_matching_blobs(self):
        for name, field, replacement, digest_key, error in (
            ("campaign.json", "purpose", RUNTIME_CONTINUATION, "manifest_sha256", "ordinary final qualification"),
            ("compiler/assessment.json", "decision", "pass", "compiler_assessment_sha256", "assessment does not reproduce"),
        ):
            with self.subTest(name=name):
                path = self.record / name
                original = path.read_bytes()
                try:
                    write(path, {**read(path), field: replacement})
                    relative = (CONTINUATION_PARENT_PATH / name).as_posix()
                    def substitute(root, tree, requested):
                        return path.read_bytes() if requested == relative else committed_blob(root, tree, requested)
                    with patch("verify.committed_blob", side_effect=substitute), self.assertRaisesRegex(ValueError, error):
                        self.verify_parent(reference={**self.reference, digest_key: sha(path)})
                finally:
                    path.write_bytes(original)


class SharedFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        temporary = tempfile.TemporaryDirectory()
        cls.output = Path(temporary.name).resolve(strict=True)
        cls.root = cls.output / "fixture-stage"

        def cleanup():
            if cls.root.is_dir():
                cls.root.chmod(0o755)
                for item in cls.root.rglob("*"):
                    if item.is_dir():
                        item.chmod(0o755)
            temporary.cleanup()

        cls.addClassCleanup(cleanup)
        with patch("replay.subprocess.run") as launch:
            cls.binding = prepare_fixture_stage(cls.root, PARENT)
            launch.assert_not_called()
        cls.stage = verify_fixture_stage(cls.binding, cls.output)

    def test_preparation_creates_a_read_only_stage_once(self):
        with patch("replay.prepare_fixture_inputs") as prepare:
            with self.assertRaises(FileExistsError):
                prepare_fixture_stage(self.root, PARENT)
            prepare.assert_not_called()
        self.assertEqual(verify_fixture_stage(self.binding, self.output), self.stage)
        self.assertEqual(self.root.stat().st_mode & 0o777, 0o555)
        self.assertEqual((self.root / "fixtures.json").stat().st_mode & 0o777, 0o444)
        self.assertEqual((self.root / "peers/libdeflate-worker").stat().st_mode & 0o777, 0o555)
        baseline = (self.root / "controller.py").read_text()
        active = (self.root / "campaign-controller.py").read_text()
        self.assertEqual(fixture_campaign_controller(baseline, 2), active)
        anchor = "orders = list(permutations(commands)) * 4"
        for variant in (baseline.replace(anchor, ""), baseline + anchor):
            with self.assertRaisesRegex(ValueError, "crossover anchor"):
                fixture_campaign_controller(variant, 2)

    def test_stage_rejects_changed_or_additional_inputs(self):
        for name in ("fixtures/0/input", "campaign-controller.py", FIXTURE_ORACLE, "peers/reference-metadata.json"):
            with self.subTest(name=name):
                path = self.root / name
                original = path.read_bytes()
                mode = path.stat().st_mode & 0o777
                path.chmod(0o644)
                try:
                    path.write_bytes(original + b"changed")
                    with self.assertRaisesRegex(ValueError, "stage inventory changed"):
                        verify_fixture_stage(self.binding, self.output)
                finally:
                    path.write_bytes(original)
                    path.chmod(mode)
        extra = self.root / "extra.json"
        self.root.chmod(0o755)
        try:
            extra.touch()
            with self.assertRaisesRegex(ValueError, "stage inventory changed"):
                verify_fixture_stage(self.binding, self.output)
            extra.unlink()
            extra.symlink_to(self.root / "fixtures.json")
            with self.assertRaisesRegex(ValueError, "symbolic link"):
                verify_fixture_stage(self.binding, self.output)
        finally:
            extra.unlink(missing_ok=True)
            self.root.chmod(0o555)

    def test_legs_share_execution_inputs_and_keep_separate_results(self):
        worker = self.root / "actors/control/bound/mech-worker"
        metadata = worker.with_name("metadata.json")
        binary = {"81": {"path": str(worker), "sha256": sha(worker)},
                  "artifacts": {"metadata.json": sha(metadata)}}
        pair = dict.fromkeys(("control", "candidate"), binary)
        shared_cases = str(self.root / "fixtures.json")
        prefixes = []

        def fake_run(command, **options):
            if Path(command[2]).name != "campaign-controller.py":
                self.assertEqual(Path(command[2]).name, "verify_timings.py")
                return
            self.assertNotIn("cwd", options)
            self.assertEqual(command[2], str(self.root / "campaign-controller.py"))
            prefix = Path(command[3])
            prefixes.append(prefix)
            prefix.mkdir()
            write(prefix / "complete.json", {"cases": 81, "balanced_blocks_per_case": 48, "timed_calls": 491328})
            write(prefix / "summary.json", [])
            pin = {"command": [str(worker), str(metadata), shared_cases],
                   "binary_sha256": sha(worker), "metadata_sha256": sha(metadata)}
            pins = read(self.root / "pinned-peers/pins.json")
            pins["actors"].update(dict.fromkeys(("mech-control", "mech-experiment"), pin))
            write(prefix / "pins.json", pins)

        with (patch("replay.actor", return_value=worker),
              patch("replay.prepare_fixture_inputs") as prepare,
              patch("replay.subprocess.run", side_effect=fake_run)):
            for step in tuple(crossover_plan(("reviewed",), 1, True))[:2]:
                leg = self.output / f"leg-{step['leg']}" / "suite81"
                leg.mkdir(parents=True)
                suite81(leg, PARENT, self.output, self.output, "fixture", "fixture", orders=("forward",),
                        retain_warmups=True, cycles=2, fixture_stage=self.binding)
                verify_fixture_execution(leg, pair, "forward", self.stage)
                validate_fixture_actor_pins(leg / "cranelift-forward", pair, self.stage)
                self.assertEqual(read(leg / "fixture-execution.json")["cwd"], str(Path.cwd()))
            prepare.assert_not_called()
        self.assertEqual(prefixes, [self.output / f"leg-{name}/suite81/cranelift-forward" for name in "AB"])

        prefix = prefixes[0]
        leg = prefix.parent
        path = prefix / "pins.json"
        original_pins = read(path)
        for name in original_pins["actors"]:
            with self.subTest(actor=name):
                copied = deepcopy(original_pins)
                copied["actors"][name]["command"][-1] = str(leg / "fixtures.json")
                write(path, copied)
                with self.assertRaisesRegex(ValueError, "shared case JSON"):
                    validate_fixture_actor_pins(prefix, pair, self.stage)
        write(path, original_pins)
        receipt_path = leg / "fixture-execution.json"
        original_receipt = read(receipt_path)
        for field, offset, alternate in (("controller", 2, leg / "controller.py"),
                                         ("output_prefix", 3, self.root / "results")):
            with self.subTest(field=field):
                receipt = deepcopy(original_receipt)
                receipt[field] = receipt["command"][offset] = str(alternate)
                write(receipt_path, receipt)
                with self.assertRaisesRegex(ValueError, "Recorded fixture execution differs"):
                    verify_fixture_execution(leg, pair, "forward", self.stage)
        write(receipt_path, original_receipt)
        for witness in FIXTURE_WITNESSES:
            self.assertEqual(sha(leg / witness), sha(self.root / FIXTURE_WITNESSES[witness]))

    def test_standalone_replay_prepares_its_own_inputs(self):
        out = self.output / "standalone"
        out.mkdir()
        folder = out / "cranelift-forward"

        def prepare(path, packets):
            (path / "controller.py").touch()
            return self.stage["reference_actor"]

        def fake_run(command, **options):
            if Path(command[2]).name == "controller.py":
                self.assertEqual(command[2:4], [str(out / "controller.py"), str(folder)])
                folder.mkdir()
                write(folder / "complete.json", {"cases": 81, "balanced_blocks_per_case": 96, "timed_calls": 982656})
                write(folder / "summary.json", [])

        with (patch("replay.prepare_fixture_inputs", side_effect=prepare) as prepare_inputs,
              patch("replay.actor", return_value=out / "worker"),
              patch("replay.subprocess.run", side_effect=fake_run)):
            suite81(out, PARENT, out, out, "fixture", "fixture", orders=("forward",))
        prepare_inputs.assert_called_once_with(out, PARENT)
        self.assertFalse((out / "fixture-execution.json").exists())
