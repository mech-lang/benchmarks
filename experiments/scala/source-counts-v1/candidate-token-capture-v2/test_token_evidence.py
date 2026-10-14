"""Saved-evidence replay and focused rejection tests; no JVM or compiler launch."""

import copy
import importlib.util
import json
from pathlib import Path
import unittest


SPEC = importlib.util.spec_from_file_location("scala_saved_token_audit", Path(__file__).with_name("audit_token_evidence.py"))
audit_module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit_module)


class TokenEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.packet = audit_module.PACKET
        cls.report = json.loads((cls.packet / "report.json").read_text())
        contract = json.loads((cls.packet.parent / "candidate-token-capture-v1/fixtures.json").read_text())
        cls.constants = contract["native_token_constants"]
        cls.actual = audit_module.audit()

    def case(self, index):
        record = json.loads((self.packet / "native/parser-output" / f"{index:04d}.json").read_text())
        item = copy.deepcopy(self.report["inputs"][index])
        source = Path(item["source"]).read_bytes()
        return record, item, source

    def check(self, values):
        return audit_module.audit_case(*values, self.constants)

    def test_all_eighty_sources_accounted(self):
        summary = self.actual["summary"]
        self.assertEqual(summary["groups"], {"owner": 41, "capture": 29, "application": 10})
        self.assertEqual((summary["required_raw_lexeme_anchors"], summary["checked_intervals"],
                          summary["crlf_comment_overhangs"]), (48, 9030, 2))
        self.assertEqual((summary["intentional_negative_cases"], summary["parse_error_cases"],
                          summary["original_complete_candidates"], summary["graph_only_failures"]), (8, 6, 27, 45))
        self.assertEqual([c["index"] for c in self.actual["cases"]], list(range(80)))
        self.assertFalse(self.actual["physical_coverage_qualified"])
        self.assertFalse(self.actual["chart_admission"])
        json.dumps(self.actual)

    def test_xml_correction_keeps_original_contract_and_rejection(self):
        correction = self.actual["xml_expectation_correction"]
        self.assertEqual(correction["original_expected_parse"], "diagnostic")
        self.assertEqual(correction["source_supported_expected_parse"], "ok")
        self.assertEqual(correction["expected_capture_unchanged"], "reject-xml")
        self.assertFalse(correction["original_contract_modified"])
        case = self.actual["cases"][69]
        self.assertEqual(case["diagnostics"], [])
        self.assertEqual(case["uncovered_intervals"], [[12, 39]])
        self.assertFalse(case["original_candidate_coverage_complete"])
        self.assertFalse(case["coverage_qualified"])

    def test_terminal_su_retains_two_eof_observations_and_one_gap(self):
        case = self.actual["cases"][44]
        self.assertEqual([x["kind"] for x in case["non_graph_issues"]],
                         ["eof_before_source_end", "eof_before_source_end", "unexplained_source_gap"])
        self.assertEqual(case["uncovered_intervals"], [[9, 10]])
        self.assertFalse(case["parse_has_errors"])

    def test_unclosed_string_recovery_is_preserved_without_admission(self):
        record, item, source = self.case(67)
        recovery = [p for p in record["token_capture"]["physical_pieces"] if p["token"] == 71]
        self.assertEqual([p["source_text"] for p in recovery], ['"unfinished'])
        checked = self.check((record, item, source))
        self.assertTrue(checked["expected_negative_case"])
        self.assertFalse(checked["coverage_qualified"])

    def test_source_byte_corruption_is_rejected(self):
        record, item, source = self.case(43)
        record["source_bytes_base64"] = "AA=="
        with self.assertRaisesRegex(AssertionError, "source bytes differ"):
            self.check((record, item, source))

    def test_surrogate_boundary_map_corruption_is_rejected(self):
        record, item, source = self.case(62)
        boundaries = record["utf16_to_utf8_byte_boundaries"]
        boundaries[boundaries.index(-1)] = 0
        with self.assertRaisesRegex(AssertionError, "boundary map"):
            self.check((record, item, source))

    def test_parser_difference_is_not_normalized(self):
        record, item, source = self.case(43)
        record["observed_parser"]["final_scanner_state"]["char_offset"] += 1
        with self.assertRaisesRegex(AssertionError, "exact parser parity"):
            self.check((record, item, source))

    def test_unexpected_token_issue_is_rejected(self):
        record, item, source = self.case(43)
        record["token_capture"]["issues"].append({"kind": "unexplained_source_gap", "detail": "0:1"})
        with self.assertRaisesRegex(AssertionError, "unaccounted non-graph"):
            self.check((record, item, source))

    def test_missing_negative_issue_is_rejected(self):
        record, item, source = self.case(44)
        record["token_capture"]["issues"].pop(0)
        with self.assertRaisesRegex(AssertionError, "unaccounted non-graph"):
            self.check((record, item, source))

    def test_raw_anchor_requires_native_token_identity(self):
        record, item, source = self.case(43)
        piece = next(p for p in record["token_capture"]["physical_pieces"] if p["source_text"] == "val")
        piece["token"] = piece["native_state"]["token"] = 14
        with self.assertRaisesRegex(AssertionError, "required raw lexeme/token anchor"):
            self.check((record, item, source))

    def test_missing_physical_interval_is_rejected(self):
        record, item, source = self.case(0)
        pieces = record["token_capture"]["physical_pieces"]
        pieces.pop(0)
        for index, piece in enumerate(pieces):
            piece["id"] = index
        with self.assertRaisesRegex(AssertionError, "uncovered source intervals"):
            self.check((record, item, source))

    def test_overlapping_physical_intervals_are_rejected(self):
        record, item, source = self.case(43)
        pieces = record["token_capture"]["physical_pieces"]
        duplicate = copy.deepcopy(pieces[0])
        duplicate["id"] = len(pieces)
        pieces.append(duplicate)
        with self.assertRaisesRegex(AssertionError, "overlapping physical intervals"):
            self.check((record, item, source))

    def test_comment_adjustment_cannot_hide_unrelated_character(self):
        record, item, source = self.case(64)
        comment = next(c for c in record["token_capture"]["native_comments_with_physical_bounds"]
                       if c["crlf_lookahead_overhang_removed"])
        comment["physical_end"] -= 1
        with self.assertRaisesRegex(AssertionError, "native comment text"):
            self.check((record, item, source))

    def test_parser_errors_cannot_be_suppressed_on_both_sides(self):
        record, item, source = self.case(67)
        for parser in (record["stock_parser"], record["observed_parser"]):
            parser["incoming_diagnostics"] = parser["buffered_diagnostics"] = []
        with self.assertRaisesRegex(AssertionError, "diagnostic expectation"):
            self.check((record, item, source))

    def test_xml_cannot_be_promoted_to_complete(self):
        record, item, source = self.case(69)
        record["candidate_coverage_complete"] = record["token_capture"]["candidate_coverage_complete"] = True
        with self.assertRaisesRegex(AssertionError, "candidate coverage flag"):
            self.check((record, item, source))

    def test_no_qualification_is_inferred_from_audit(self):
        record, item, source = self.case(43)
        record["complete_token_coverage_qualified"] = True
        with self.assertRaisesRegex(AssertionError, "unexpected qualification"):
            self.check((record, item, source))

    def test_duplicate_json_keys_are_rejected(self):
        with self.assertRaisesRegex(AssertionError, "Duplicate JSON key"):
            json.loads('{"issues": [], "issues": []}', object_pairs_hook=audit_module._unique_object)


if __name__ == "__main__":
    unittest.main()
