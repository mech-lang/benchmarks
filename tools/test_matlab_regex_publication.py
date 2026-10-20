"""Small offline exact-source intake fixtures; no MATLAB, browser or catalog writes."""
import copy
import gzip
import hashlib
import json
from pathlib import Path
import statistics
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from qualification import import_matlab_regex as intake


class MatlabRegexIntake(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog_bytes = (intake.ROOT / "data/benchmarks.json").read_bytes()
        catalog = json.loads(cls.catalog_bytes)
        parents = {key: value for key, value in catalog["programs"].items() if key in {"regexredux:matlab-compact", "regexredux:matlab-optimized"}}
        benchmark = copy.deepcopy(next(b for b in catalog["benchmarks"] if b["key"] == "regexredux"))
        benchmark["groups"] = [g for g in benchmark["groups"] if g["language"] == "matlab"]
        files = {h for p in parents.values() for h in p["files"]}
        cls.before = {"programs": parents, "program_inventory": copy.deepcopy(parents),
                      "files": {h: catalog["files"][h] for h in files}, "benchmarks": [benchmark],
                      "languages": [copy.deepcopy(next(l for l in catalog["languages"] if l["key"] == "matlab"))],
                      "archive_paths": {}, "reference_summary": [{"lang": "matlab", "fast": {"x": 1, "y": 1}, "small": {"x": 1, "y": 1}}],
                      "formatted_reference_summary": [{"lang": "matlab", "fast": None, "small": None}],
                      "historical_sentinel": {"keep": ["all previous observations", 1.23456789]}}
        cls.results = intake.reconcile()

    def append(self, results=None):
        return intake.append_catalog(self.before, results=self.results if results is None else results)

    def test_replays_exact_counts_full_samples_and_historical_flags(self):
        self.assertEqual([p["loc"] for p in self.results["programs"]], [16, 19])
        self.assertEqual(self.results["programs"][0]["samples_seconds"], [17.644398125, 14.853161459, 14.785282])
        self.assertEqual(self.results["programs"][1]["samples_seconds"], [14.901873791, 14.965484375, 14.720709792])
        self.assertEqual(self.results["new_observations"], 6)
        self.assertEqual(self.results["native_processes_run_by_intake"], 0)
        raw = [a for a in self.results["artifacts"] if "/attempts/" in a["path"]]
        self.assertEqual(len(raw), 54)
        for p in self.results["programs"]:
            self.assertEqual(p["median_seconds"], statistics.median(p["samples_seconds"]))
            self.assertTrue(all(a["chart_admission"] is False for a in p["sample_execution_metadata"]))

    def test_pure_deterministic_addition_preserves_parents_sources_and_baselines(self):
        before = copy.deepcopy(self.before)
        a, b = self.append(), self.append()
        self.assertEqual(a, b)
        self.assertEqual(self.before, before)
        self.assertEqual(a["historical_sentinel"], before["historical_sentinel"])
        self.assertEqual(a["languages"], before["languages"])
        self.assertEqual(a["formatted_reference_summary"], before["formatted_reference_summary"])
        for pool in ["programs", "program_inventory", "files"]:
            for key, value in before[pool].items():
                self.assertEqual(a[pool][key], value, key)
            self.assertEqual(len(a[pool]) - len(before[pool]), 2)
        for field in ["baseline_loc", "baseline_seconds", "baseline_formatted_loc"]:
            self.assertEqual(a["benchmarks"][0].get(field), before["benchmarks"][0].get(field))
        self.assertEqual((intake.ROOT / "data/benchmarks.json").read_bytes(), self.catalog_bytes)

    def test_new_source_cohorts_own_their_samples_and_do_not_claim_current_ai_model(self):
        after = self.append()
        for p in self.results["programs"]:
            row = after["programs"][p["key"]]
            old = after["programs"][p["original_program_key"]]
            self.assertEqual(row["files"][1:], old["files"][1:])
            self.assertNotEqual(row["files"][0], old["files"][0])
            self.assertEqual(row["samples"], p["samples_seconds"])
            self.assertNotEqual(row["samples"], old["samples"])
            self.assertEqual(row["native_observations"], 3)
            self.assertIsNone(row["timing_alias_of"])
            self.assertNotIn("source_alias_of", row)
            self.assertTrue(row["eligible_for_chart"])
            self.assertEqual(row["source_accounting"]["application_loc"], p["loc"])
            self.assertEqual(row["source_accounting"]["previous_loc"], p["loc"])
            self.assertIsNone(row["formatted_loc"])
            self.assertIsNone(row["authorship"]["ai"]["model_family"])
            self.assertIsNone(row["authorship"]["ai"]["tool"])
            self.assertEqual(row["authorship"]["kind"], "local-origin-unverified")
            self.assertEqual(row["authorship"]["ai"]["status"], "unverified")
            self.assertEqual(row["authorship"]["ai"]["models"], [])
            self.assertEqual(row["authorship"]["parent_programs"], [old["key"]])
            self.assertEqual({r["source_sha256"] for r in row["authorship"]["retained_sources"]}, set(row["files"]))
            source = after["files"][row["files"][0]]
            self.assertEqual(hashlib.sha256(source["code"].encode()).hexdigest(), row["files"][0])

    def test_rejects_changed_counts_samples_scope_and_duplicate_intake(self):
        bad = copy.deepcopy(self.results)
        bad["programs"][0]["samples_seconds"] = bad["programs"][0]["samples_seconds"][1:]
        with self.assertRaisesRegex(ValueError, "do not reproduce"):
            self.append(bad)
        bad = copy.deepcopy(self.results)
        bad["programs"][0]["loc"] = 13
        with self.assertRaisesRegex(ValueError, "do not reproduce"):
            self.append(bad)
        ledger = intake.load(intake.ROOT / intake.LEDGER)
        ledger["rows"][0]["normalized_loc"] = 13
        with self.assertRaisesRegex(ValueError, "Unreviewed MATLAB count"):
            intake.validate_ledger(ledger)
        after = self.append()
        with self.assertRaisesRegex(ValueError, "already applied"):
            intake.append_catalog(after, results=self.results)

    def test_wrong_parent_or_new_baseline_fails_closed(self):
        bad = copy.deepcopy(self.before)
        bad["programs"]["regexredux:matlab-compact"]["loc"] = 13
        with self.assertRaisesRegex(ValueError, "Wrong immutable MATLAB parent"):
            intake.append_catalog(bad, results=self.results)
        bad = copy.deepcopy(self.before)
        bad["benchmarks"][0]["baseline_seconds"] = 1000
        with self.assertRaisesRegex(ValueError, "New global baseline"):
            intake.append_catalog(bad, results=self.results)

    def test_support_tail_cannot_drift_from_the_sampled_launcher(self):
        bad = copy.deepcopy(self.before)
        parent = bad["programs"]["regexredux:matlab-compact"]
        parent["files"] = [parent["files"][0], parent["files"][0]]
        with self.assertRaisesRegex(ValueError, "Unreviewed MATLAB support boundary"):
            intake.append_catalog(bad, results=self.results)
        bad = copy.deepcopy(self.before)
        bad["files"][intake.LAUNCHER_SHA]["code"] += "\n"
        with self.assertRaisesRegex(ValueError, "Unreviewed MATLAB support boundary"):
            intake.append_catalog(bad, results=self.results)

    def test_authorship_hook_retains_archived_unknown_model_and_rejects_current_family(self):
        after = self.append()
        for p in self.results["programs"]:
            row = after["programs"][p["key"]]
            with mock.patch.object(intake, "load", side_effect=lambda path: self.results if str(path).endswith(intake.RESULTS) else json.loads(Path(path).read_text())), \
                 mock.patch.object(intake, "pin", side_effect=lambda root, path: {"path": path, "sha256": hashlib.sha256(intake.encoded(self.results)).hexdigest()} if path == intake.RESULTS else {"path": path, "sha256": intake.sha(root/path)}):
                self.assertEqual(intake.bound_authorship(after, row), row["authorship"])
                changed = copy.deepcopy(row)
                changed["source_provenance_record"]["author_context"]["model_family"] = "current reviewer"
                with self.assertRaisesRegex(ValueError, "authorship source identity"):
                    intake.bound_authorship(after, changed)

    def test_historical_replay_orders_matlab_after_nim(self):
        import source_accounting as accounting
        from qualification import import_ruby_zjit as ruby, import_bqn_knucleotide as bqn, import_nim_knucleotide as nim
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            original = {"historical": "unchanged"}
            corrected = {"source_accounting": True, "stage": "corrected"}
            stages = []
            prior = corrected
            for marker, stage in [("ruby_zjit_audit", "ruby"), ("bqn_knucleotide_audit", "bqn"), ("nim_knucleotide_audit", "nim"), ("matlab_regex_case_audit", "matlab")]:
                value = {**prior, marker: {}, "stage": stage}
                stages.append((prior, value)); prior = value
            packet = root / accounting.PACKET
            packet.mkdir(parents=True)
            raw, empty = intake.encoded(original), intake.encoded({})
            (packet / "before.json.gz").write_bytes(gzip.compress(raw, mtime=0))
            (root / "data").mkdir()
            (root / "data/source-size-review.json").write_bytes(empty)
            (packet / "partitions.json").write_bytes(empty)
            report = {"fixture": "transformation"}
            (packet / "receipt.json").write_bytes(intake.encoded({"before_catalog_sha256": hashlib.sha256(raw).hexdigest(),
                "review_sha256": hashlib.sha256(empty).hexdigest(), "partitions_sha256": hashlib.sha256(empty).hexdigest(), "transformation": report}))
            def checked(wanted, produced):
                def append(actual, _root):
                    self.assertEqual(actual, wanted)
                    return copy.deepcopy(produced)
                return append
            with mock.patch.object(accounting, "transform", return_value=(corrected, report)), \
                 mock.patch.object(ruby, "append_catalog", side_effect=checked(*stages[0])), \
                 mock.patch.object(bqn, "append_catalog", side_effect=checked(*stages[1])), \
                 mock.patch.object(nim, "append_catalog", side_effect=checked(*stages[2])), \
                 mock.patch.object(intake, "append_catalog", side_effect=checked(*stages[3])):
                self.assertEqual(accounting.historical_catalog(root, prior), original)
                with self.assertRaisesRegex(AssertionError, "validated source-accounting"):
                    accounting.historical_catalog(root, {**prior, "stage": "tampered"})

    def test_relocation_replays_without_old_runtime_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {r["path"] for r in self.results["artifacts"]}
            paths.update({intake.LEDGER, intake.LEDGER_TOOL, "tools/qualification/import_matlab_regex.py", intake.RESULTS})
            for row in intake.load(intake.ROOT / intake.LEDGER)["rows"]:
                paths.update([row["source"]["path"], row["parent_source"]["path"]])
            qualification = intake.load(intake.ROOT / intake.BASE / "qualification-v1/report.json")
            for path in qualification["case_pins"]:
                relative = intake.BASE + "/" + path.split("/matlab-comparison/20261012/regex-case-sensitive-v1/", 1)[1]
                if (intake.ROOT / relative).exists():
                    paths.add(relative)
            for path in paths:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                if path == intake.RESULTS:
                    target.write_bytes(intake.encoded(self.results))
                else:
                    shutil.copyfile(intake.ROOT / path, target)
            vendor = intake.load(intake.ROOT / intake.LEDGER)["lexer"]["source"]
            shutil.copytree(intake.ROOT / vendor / "pygments", root / vendor / "pygments", dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            code = "import sys;sys.path.insert(0,'tools');from qualification import import_matlab_regex as a;r=a.reconcile();assert r==a.load(a.ROOT/a.RESULTS);print(r['status'],r['native_processes_run_by_intake'])"
            process = subprocess.run([sys.executable, "-c", code], cwd=root, capture_output=True, text=True, timeout=15)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual(process.stdout.strip(), "RECONCILED 0")


if __name__ == "__main__":
    unittest.main()
