import copy
import json
import unittest
from pathlib import Path

from ruby_support_partitions import ROOT, CANDIDATES, build_review, stable, sha


class RubySupportProposalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ROOT / "data/benchmarks.json").read_bytes()
        cls.data = json.loads(cls.raw)

    def test_exact_sources_profiles_and_timing_records_preserved(self):
        before = copy.deepcopy(self.data)
        report = build_review(self.raw)
        self.assertEqual(before, self.data)
        self.assertEqual(report["status"], "candidate-not-applied")
        self.assertEqual((report["protected_ruby_profiles"], report["protected_source_files"], report["candidate_profiles"]), (42, 19, 10))
        pool = {**self.data["program_inventory"], **self.data["programs"]}
        for key, digest in report["protected_profile_sha256"].items():
            self.assertEqual(sha(stable(pool[key])), digest)
        self.assertEqual((ROOT / "data/benchmarks.json").read_bytes(), self.raw)

    def test_partitions_cover_each_original_byte_and_keep_workload_calls(self):
        report = build_review(self.raw)
        boundaries = {"binarytrees-ruby-5.rb": "def item_check", "mandelbrot-ruby-5.rb": "Size = ARGV", "fannkuchredux-ruby-2.rb": "class Fannkuch", "spectralnorm-ruby-5.rb": "def eval_a", "knucleotide-ruby-1.rb": "workers ="}
        for r in report["reviews"]:
            rows = self.data["files"][r["source_sha256"]]["code"].splitlines(keepends=True)
            a, b = r["support_line_ranges"][0]
            self.assertEqual(r["submitted"]["utf8_bytes"], r["candidate_application"]["utf8_bytes"] + r["candidate_excluded_support"]["utf8_bytes"])
            app = "".join(rows[:a - 1] + rows[b:])
            self.assertIn(boundaries[r["name"]], app)
            self.assertEqual([x["line"] for x in r["per_line_review"]], list(range(a, b + 1)))
            self.assertIsNone(r["normalized_loc"])

    def test_changed_source_fails_closed(self):
        data = copy.deepcopy(self.data)
        h = next(iter(CANDIDATES))
        data["files"][h]["code"] += "\n"
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            build_review(json.dumps(data).encode())

    def test_unreviewed_alias_fails_closed(self):
        data = copy.deepcopy(self.data)
        pools = [data["programs"], data["program_inventory"]]
        key = "knucleotide:knucleotide-ruby-1-zjit"
        for pool in pools:
            if key in pool:
                pool[key]["files"] = data["programs"]["knucleotide:knucleotide-ruby-2"]["files"]
        with self.assertRaisesRegex(ValueError, "alias coverage changed"):
            build_review(json.dumps(data).encode())


if __name__ == "__main__":
    unittest.main()
