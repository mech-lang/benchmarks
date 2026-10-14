"""Pure audit of the frozen 80-source v1 Scala parser/token capture.

This reads only the saved fixture contracts, input sources, report and parser
JSON. It does not launch a compiler, hash a runtime closure, edit evidence, count
LOC, or qualify the candidate. Graph problems are retained for a separate audit.

The pinned upstream commit is 25c18aaa21b6be202945e024cd5180d9d62d650f.
XML has no parser diagnostic at source=3.10: Parsers.scala:621-629 delegates to
report.errorOrMigrationWarning; config/MigrationVersion.scala:33 sets both XML
thresholds to future; report.scala:110-116 and SourceVersion.scala:22,27,39 leave
3.10 below those thresholds. Direct character-reader access in
parsing/xml/MarkupParsers.scala:74-88,324-338,359-362 still prevents token coverage.
See UPSTREAM below for exact public URLs and the other negative-case semantics.
The original XML fixture is never modified or silently treated as fulfilled.
"""

from __future__ import annotations

import base64
from collections import Counter
import hashlib
import json
from pathlib import Path


COMMIT = "25c18aaa21b6be202945e024cd5180d9d62d650f"
REPORT_SHA = "a72690ad68a0b2b1d0947cbe010811411739789584f18a4040e6e2a6fb293ac9"
OWNER_CONTRACT_SHA = "874dad522020c810beadbd6d019bd11a8d7378ea4226ba45e8df22db599c245d"
CAPTURE_CONTRACT_SHA = "aa075a277e52201f22e28aa5f44020d03b1b7b0d5a1b87e04468ab5bdf6435e0"
BASE_URL = f"https://github.com/scala/scala3/blob/{COMMIT}/compiler/src/dotty/tools/dotc/"
PACKET = Path(__file__).resolve().parent.parent / "native-token-capture-v1"
MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_SOURCE_BYTES = 1024 * 1024
APPLICATIONS = (
    "binarytrees", "fannkuchredux", "fasta", "knucleotide", "mandelbrot",
    "nbody", "pidigits", "regexredux", "revcomp", "spectralnorm",
)
PARSE_ERROR_CASES = (39, 40, 47, 48, 67, 68)
NEGATIVE_CASES = (*PARSE_ERROR_CASES, 44, 69)
PARSE_ISSUE = {
    "kind": "native_parse_not_clean",
    "detail": "Errors or exceptions prevent coverage admission",
}
EXPECTED_DIAGNOSTICS = {
    39: [(1, "Line is indented too far to the left, or a '}' is missing"),
         (2, "'}' expected, but eof found")],
    40: [(2, "')' expected, but ']' found")],
    47: [(2, "illegal character '\\u0000'"), (2, "Illegal start of toplevel definition")],
    48: [(2, "unclosed comment")],
    67: [(2, "unclosed string literal"), (2, "expression expected but ';' found")],
    68: [(2, "')' expected, but ']' found")],
}
UPSTREAM = {
    "xml_diagnostic_call": {
        "url": BASE_URL + "parsing/Parsers.scala#L621",
        "fact": "Lines 621-629 use errorOrMigrationWarning with MigrationVersion.XmlLiteral.",
    },
    "xml_diagnostic_threshold": {
        "url": BASE_URL + "config/MigrationVersion.scala#L33",
        "fact": "XmlLiteral has warnFrom=future and errorFrom=future.",
    },
    "migration_reporting": {
        "url": BASE_URL + "report.scala#L110",
        "fact": "Lines 110-116 emit a diagnostic only when the source reaches a migration threshold.",
    },
    "source_version_order": {
        "url": BASE_URL + "config/SourceVersion.scala#L22",
        "fact": "Lines 22, 27 and 39 order source 3.10 below future.",
    },
    "xml_character_reader": {
        "url": BASE_URL + "parsing/xml/MarkupParsers.scala#L74",
        "fact": "Lines 74-88 read characters directly; 359-362 use parser.in; 324-338 resume the scanner afterward.",
    },
    "terminal_su": {
        "url": BASE_URL + "parsing/Scanners.scala#L993",
        "fact": "Lines 993-998 treat SU as EOF when isAtEnd, including a physical terminal SU.",
    },
    "character_offsets": {
        "url": BASE_URL + "parsing/CharArrayReader.scala#L25",
        "fact": "Lines 25-29 define offsets; 40-50 read a physical character; 118 tests charOffset >= endIdx.",
    },
    "illegal_character": {
        "url": BASE_URL + "parsing/Scanners.scala#L1022",
        "fact": "Illegal characters report an error and advance; lines 120-124 set token=ERROR.",
    },
    "unterminated_comment": {
        "url": BASE_URL + "parsing/Scanners.scala#L1051",
        "fact": "An unfinished comment reports incomplete input; 1054-1073 retain its native span/raw text.",
    },
    "unterminated_string": {
        "url": BASE_URL + "parsing/Scanners.scala#L1218",
        "fact": "Lines 1218-1223 report an unclosed string and recover with synthesized SEMI.",
    },
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def _read_bytes(path: Path, limit: int) -> bytes:
    require(path.is_file() and not path.is_symlink(), f"Missing/nonregular evidence: {path}")
    require(path.stat().st_size <= limit, f"Evidence exceeds size bound: {path}")
    data = path.read_bytes()
    require(len(data) <= limit, f"Evidence grew beyond size bound: {path}")
    return data


def _read_json(path: Path):
    data = _read_bytes(path, MAX_JSON_BYTES)
    return json.loads(data, object_pairs_hook=_unique_object), hashlib.sha256(data).hexdigest()


def _boundaries(text: str) -> list[int]:
    boundaries, byte_offset = [0], 0
    for char in text:
        if ord(char) > 0xFFFF:
            boundaries.append(-1)
        byte_offset += len(char.encode("utf-8"))
        boundaries.append(byte_offset)
    return boundaries


def expected_issues(index: int) -> list[dict]:
    if index == 44:
        return [{"kind": "eof_before_source_end", "detail": "9"},
                {"kind": "eof_before_source_end", "detail": "9"},
                {"kind": "unexplained_source_gap", "detail": "9:10"}]
    if index == 47:
        return [{"kind": "invalid_physical_token", "detail": "1"}, dict(PARSE_ISSUE)]
    if index == 69:
        return [{"kind": "unsupported_xml_character_reader",
                 "detail": "XML reads source outside token hooks"},
                {"kind": "unexplained_source_gap", "detail": "12:39"}]
    return [dict(PARSE_ISSUE)] if index in PARSE_ERROR_CASES else []


def audit_case(record: dict, item: dict, source_bytes: bytes, constants: dict) -> dict:
    """Validate one saved case; callable independently for focused mutation tests."""
    index, case_id = item["index"], item["id"]
    require(record["schema"] == "scala310-parser-token-capture-candidate-v1", f"{case_id}: schema")
    require(record["expected_compiler_source_commit"] == COMMIT, f"{case_id}: compiler commit")
    text = source_bytes.decode("utf-8", errors="strict")
    require(record["decoded_text"] == text and
            base64.b64decode(record["source_bytes_base64"], validate=True) == source_bytes and
            record["source_byte_count"] == len(source_bytes), f"{case_id}: source bytes differ")
    digest = hashlib.sha256(source_bytes).hexdigest()
    require(record["source_sha256"] == item["source_sha256"] == digest, f"{case_id}: source digest")
    require(record["source_path"] == item["source"], f"{case_id}: source path")
    if "fixture" in item:
        require(text == item["fixture"]["text"], f"{case_id}: fixture text")
    boundaries = _boundaries(text)
    length = len(boundaries) - 1
    require(record["utf16_to_utf8_byte_boundaries"] == boundaries and
            record["utf16_length"] == length and record["offset_unit"] == "UTF-16 code units",
            f"{case_id}: UTF-16/UTF-8 boundary map")
    require(record["stock_parser_parity"] is True and
            record["stock_parser"] == record["observed_parser"], f"{case_id}: exact parser parity")
    parser, capture = record["stock_parser"], record["token_capture"]
    require(parser["failure"] is None, f"{case_id}: parser exception")
    require(parser["parse_has_errors"] is (index in PARSE_ERROR_CASES), f"{case_id}: parser error expectation")
    diagnostics = [(d["level"], d["message"]) for d in parser["incoming_diagnostics"]]
    require(diagnostics == EXPECTED_DIAGNOSTICS.get(index, []), f"{case_id}: diagnostic expectation")
    require(parser["buffered_diagnostics"] == parser["incoming_diagnostics"] and
            parser["unreported_warning_counts"] == {}, f"{case_id}: diagnostic preservation")
    require(parser["final_scanner_state"]["current"]["token"] == 2, f"{case_id}: final EOF")
    issues = capture["issues"]
    non_graph = [i for i in issues if i["kind"] != "native_graph_not_complete"]
    graph_issues = [i for i in issues if i["kind"] == "native_graph_not_complete"]
    require(non_graph == expected_issues(index), f"{case_id}: unaccounted non-graph issues")
    require(len(graph_issues) <= 1 and bool(graph_issues) == bool(parser["graph_problems"]),
            f"{case_id}: graph issue preservation")
    require(record["candidate_coverage_complete"] is (not issues) and
            capture["candidate_coverage_complete"] is (not issues), f"{case_id}: candidate coverage flag")
    for field in ("complete_token_coverage_qualified", "native_fixture_transport_verified", "chart_admission"):
        require(record[field] is False, f"{case_id}: unexpected qualification {field}")
    require(record["canonical_loc"] is None and record["formatted_loc"] is None, f"{case_id}: unexpected LOC")

    def interval(start, end):
        require(type(start) is int and type(end) is int and 0 <= start < end <= length,
                f"{case_id}: invalid physical interval")
        require(boundaries[start] >= 0 and boundaries[end] >= 0, f"{case_id}: split surrogate pair")
        return source_bytes[boundaries[start]:boundaries[end]].decode("utf-8")

    intervals, anchor_evidence = [], []
    pieces = capture["physical_pieces"]
    require([p["id"] for p in pieces] == list(range(len(pieces))), f"{case_id}: piece IDs")
    for piece in pieces:
        start, end = piece["start"], piece["end"]
        require(piece["source_text"] == interval(start, end), f"{case_id}: physical source slice")
        require(piece["kind"] in ("token", "comment"), f"{case_id}: physical piece kind")
        if piece["kind"] == "token":
            require(piece["native_state"]["token"] == piece["token"] and
                    piece["native_state"]["offset"] == start, f"{case_id}: native token identity")
            require(piece["token"] not in (0, 2), f"{case_id}: physical EMPTY/EOF token")
            require(piece["token"] != 1 or index == 47, f"{case_id}: unexpected ERROR token")
        else:
            require(piece["token"] == -1 and piece["native_state"] is None,
                    f"{case_id}: comment token identity")
        intervals.append((start, end))
    for space in capture["whitespace_intervals"]:
        value = interval(space["start"], space["end"])
        require(value == space["text"] and all(c in " \t\r\n\f" for c in value),
                f"{case_id}: unchecked whitespace")
        intervals.append((space["start"], space["end"]))
    cursor, gaps = 0, []
    for start, end in sorted(intervals):
        require(start >= cursor, f"{case_id}: overlapping physical intervals")
        if start > cursor:
            gaps.append([cursor, start])
        cursor = end
    if cursor < length:
        gaps.append([cursor, length])
    require(gaps == {44: [[9, 10]], 69: [[12, 39]]}.get(index, []), f"{case_id}: uncovered source intervals")

    comment_evidence = []
    comments = capture["native_comments_with_physical_bounds"]
    require(len(comments) == len(parser["parser_scanner_comments"]), f"{case_id}: comment inventory")
    for i, (comment, native) in enumerate(zip(comments, parser["parser_scanner_comments"])):
        require(comment["index"] == i and comment["native_span"] == native["span"] and
                comment["native_raw"] == native["native_raw"], f"{case_id}: native comment preservation")
        start, end = comment["physical_start"], comment["physical_end"]
        require(start == native["span"]["start"] and
                interval(start, end).replace("\r\n", "\n") == native["native_raw"],
                f"{case_id}: native comment text")
        overhang = comment["crlf_lookahead_overhang_removed"]
        native_end = native["span"]["end"]
        require(type(overhang) is bool, f"{case_id}: comment overhang flag")
        if overhang:
            require(native_end == end + 1 and interval(end, end + 2) == "\r\n",
                    f"{case_id}: unsupported comment span adjustment")
        else:
            require(native_end == end, f"{case_id}: unexplained comment span adjustment")
        matches = [p for p in pieces if p["kind"] == "comment" and (p["start"], p["end"]) == (start, end)]
        require(len(matches) == 1, f"{case_id}: comment physical event")
        comment_evidence.append({"index": i, "physical_interval": [start, end],
                                 "native_end": native_end, "crlf_overhang": overhang})
    require(sum(p["kind"] == "comment" for p in pieces) == len(comments), f"{case_id}: extra physical comment")

    for anchor in item.get("fixture", {}).get("required_raw_lexemes", []):
        needle, position, occurrences = anchor["text"], 0, []
        while True:
            position = text.find(needle, position)
            if position < 0:
                break
            occurrences.append(len(text[:position].encode("utf-16-le")) // 2)
            position += len(needle)
        require(0 <= anchor["occurrence"] < len(occurrences), f"{case_id}: missing source anchor")
        start = occurrences[anchor["occurrence"]]
        end = start + len(needle.encode("utf-16-le")) // 2
        matches = [p for p in pieces if p["kind"] == "token" and
                   (p["start"], p["end"], p["source_text"]) == (start, end, needle) and
                   ("native_token_constant" not in anchor or p["token"] == constants[anchor["native_token_constant"]])]
        require(len(matches) == 1, f"{case_id}: required raw lexeme/token anchor")
        anchor_evidence.append({**anchor, "interval": [start, end], "piece_id": matches[0]["id"]})
    return {
        "index": index, "id": case_id, "group": item["group"], "source_sha256": digest,
        "source_bytes": len(source_bytes), "utf16_length": length, "exact_parser_parity": True,
        "source_bytes_and_boundary_map_verified": True, "parse_has_errors": parser["parse_has_errors"],
        "diagnostics": [{"level": level, "message": message} for level, message in diagnostics],
        "expected_negative_case": index in NEGATIVE_CASES, "non_graph_issues": non_graph,
        "graph_issues_retained_for_separate_review": graph_issues,
        "original_candidate_coverage_complete": record["candidate_coverage_complete"],
        "physical_piece_count": len(pieces), "whitespace_interval_count": len(capture["whitespace_intervals"]),
        "checked_interval_count": len(intervals), "uncovered_intervals": gaps,
        "required_anchors_verified": anchor_evidence, "native_comments_verified": comment_evidence,
        "original_expected_parse": item.get("fixture", {}).get("expected_parse", "ok"),
        "observed_parse": "error" if parser["parse_has_errors"] else "ok",
        "xml_expectation_correction_applies": index == 69,
        "coverage_qualified": False, "canonical_loc": None, "formatted_loc": None, "chart_admission": False,
    }


def audit(packet: Path | None = None) -> dict:
    """Audit all original 70 fixtures and 10 applications; return serializable evidence."""
    packet = PACKET if packet is None else Path(packet)
    counts_root = packet.parent
    report, report_digest = _read_json(packet / "report.json")
    inputs, _ = _read_json(packet / "inputs.json")
    owner, owner_digest = _read_json(counts_root / "fixtures.json")
    capture_contract, capture_digest = _read_json(counts_root / "candidate-token-capture-v1/fixtures.json")
    require((report_digest, owner_digest, capture_digest) ==
            (REPORT_SHA, OWNER_CONTRACT_SHA, CAPTURE_CONTRACT_SHA), "Frozen report/fixture contract digest")
    require(len(owner["fixtures"]) == 41 and len(capture_contract["fixtures"]) == 29, "Fixture contract inventory")
    require(inputs == report["inputs"] and len(inputs) == 80 and len(report["results"]) == 80,
            "All 80 original input/report entries required")
    require([x["index"] for x in inputs] == list(range(80)) and len({x["id"] for x in inputs}) == 80,
            "Input order/identity")
    output = packet / "native/parser-output"
    require({p.name for p in output.iterdir()} ==
            {f"{i:04d}.json" for i in range(80)} | {"initialization-stock.json", "initialization-observed.json"},
            "Exact 80-source output inventory")
    for mode in ("stock", "observed"):
        init, _ = _read_json(output / f"initialization-{mode}.json")
        require(init["mode"] == mode and init["source_version"] == "3.10" and
                init["expected_compiler_source_commit"] == COMMIT and
                init["incoming_diagnostics"] == [] and init["failure"] is None, "Parser initialization")
        if mode == "stock":
            stock_init = init
        else:
            require({k: v for k, v in init.items() if k != "mode"} ==
                    {k: v for k, v in stock_init.items() if k != "mode"}, "Initialization parity")
    cases = []
    for index, item in enumerate(inputs):
        if index < 70:
            group, contract, ordinal = ("owner", owner, index) if index < 41 else ("capture", capture_contract, index - 41)
            fixture = contract["fixtures"][ordinal]
            require(item["group"] == group and item["id"] == f"{group}-{fixture['id']}" and
                    item["fixture"] == fixture, f"Fixture contract binding {index}")
            source = packet / "inputs" / f"{index:04d}-{item['id']}.scala"
        else:
            benchmark = APPLICATIONS[index - 70]
            require(item["group"] == "application" and item["id"] == f"scala-{benchmark}-jvm-v1" and
                    "fixture" not in item, f"Application binding {index}")
            source = counts_root.parent / "source-v1" / benchmark / "Main.scala"
        require(source.resolve() == Path(item["source"]).resolve(), f"Source path binding {index}")
        record, digest = _read_json(output / f"{index:04d}.json")
        result = report["results"][index]
        require(result["id"] == item["id"] and result["sha256"] == digest and
                Path(result["path"]).resolve() == (output / f"{index:04d}.json").resolve() and
                result["stock_parser_parity"] == record["stock_parser_parity"] and
                result["candidate_coverage_complete"] == record["candidate_coverage_complete"],
                f"Saved result binding {index}")
        case = audit_case(record, item, _read_bytes(source, MAX_SOURCE_BYTES), capture_contract["native_token_constants"])
        case["capture_sha256"] = digest
        cases.append(case)
    summary = {
        "cases": len(cases), "fixtures": 70, "applications": 10,
        "groups": dict(Counter(c["group"] for c in cases)), "exact_parser_parity": 80,
        "required_raw_lexeme_anchors": sum(len(c["required_anchors_verified"]) for c in cases),
        "checked_intervals": sum(c["checked_interval_count"] for c in cases),
        "crlf_comment_overhangs": sum(v["crlf_overhang"] for c in cases for v in c["native_comments_verified"]),
        "parse_error_cases": sum(c["parse_has_errors"] for c in cases),
        "intentional_negative_cases": sum(c["expected_negative_case"] for c in cases),
        "cases_without_token_or_parse_rejection": sum(not c["non_graph_issues"] for c in cases),
        "original_complete_candidates": sum(c["original_candidate_coverage_complete"] for c in cases),
        "graph_only_failures": sum(bool(c["graph_issues_retained_for_separate_review"]) and not c["non_graph_issues"] for c in cases),
        "non_graph_issue_occurrences": dict(Counter(i["kind"] for c in cases for i in c["non_graph_issues"])),
    }
    require((summary["required_raw_lexeme_anchors"], summary["checked_intervals"], summary["crlf_comment_overhangs"],
             summary["parse_error_cases"], summary["intentional_negative_cases"], summary["cases_without_token_or_parse_rejection"],
             summary["original_complete_candidates"], summary["graph_only_failures"]) == (48, 9030, 2, 6, 8, 72, 27, 45),
            "Original v1 token evidence accounting changed")
    return {
        "schema": "scala310-saved-token-evidence-audit-v1", "compiler_source_commit": COMMIT,
        "status": "all-original-cases-accounted-with-explicit-xml-expectation-correction",
        "original_report_sha256": report_digest, "summary": summary, "cases": cases,
        "xml_expectation_correction": {
            "case_index": 69, "id": "capture-xml-direct-reader-handoff", "original_expected_parse": "diagnostic",
            "source_supported_expected_parse": "ok", "actual_incoming_and_buffered_diagnostics": [],
            "expected_capture_unchanged": "reject-xml", "original_contract_modified": False,
            "reason": "Source 3.10 is below the future XML migration diagnostic threshold. Direct character-reader access still prevents token coverage.",
        },
        "upstream_rationale": UPSTREAM,
        "graph_semantics_reviewed": False, "physical_coverage_qualified": False,
        "canonical_loc": None, "formatted_loc": None, "chart_admission": False,
    }


if __name__ == "__main__":
    print(json.dumps(audit(), indent=2, ensure_ascii=True))
