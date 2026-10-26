import json
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parent / "source"

class HistoricalReceiptTests(unittest.TestCase):
    def test_benchmark_status_keeps_unique_keys_and_both_cli_records(self):
        def unique_object(pairs):
            result = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError(f"duplicate validation key: {key}")
                result[key] = value
            return result

        source = (ROOT / "docs/validation/benchmark-compiler-status-v1.json").read_text()
        document = json.loads(source, object_pairs_hook=unique_object)
        qualification = document["cli_payload_continuation"]
        for key in ("qualified_source_commit", "result", "remaining", "ci_wiring_source_commit"):
            self.assertIn(key, qualification)
        history = document["cli_payload_publication_history"]
        self.assertEqual(history["pull_request"], "https://github.com/mech-lang/mech/pull/903")
        self.assertEqual(history["status"], "INHERITED_PR903_IMPLEMENTATION_HISTORICAL_PUBLICATION_RECEIPT")
        self.assertNotIn("NOT composed", history["scope"])
        # Exercise real JSON parsing, including nested objects, rather than a
        # textual key count that could confuse strings with object members.
        mutants = (
            source.replace('"cli_payload_continuation": {',
                           '"cli_payload_continuation": {}, "cli_payload_continuation": {', 1),
            '{"outer": {"qualified_source_commit": "first", "qualified_source_commit": "lost"}}',
        )
        for mutant in mutants:
            with self.subTest(mutant=mutant[:100]):
                with self.assertRaisesRegex(ValueError, "duplicate validation key"):
                    json.loads(mutant, object_pairs_hook=unique_object)


if __name__ == "__main__":
    unittest.main()
