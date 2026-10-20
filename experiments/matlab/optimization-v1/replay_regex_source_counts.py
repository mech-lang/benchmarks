#!/usr/bin/env python3
"""Exact archived MATLAB source accounting proposal; no runtime or catalog write."""
import argparse
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
BASE = "archive/comparisons/matlab-comparison/20261012/regex-case-sensitive-v1"
OLD = "archive/comparisons/matlab-comparison/20261010"
OUTPUT = "experiments/matlab/optimization-v1/regex-source-counts.json"
VENDOR = "archive/qualification/nim/records/formatted-nim-plan-v1/jobs/actual-plans-v1/imports"
IDENTITIES = {
    "compact": ("cefbed6d631f9cb83da8a3dde423ec666678fd6aec98a4a942fddcf172fbd483", "d41b8687b3661174be4b7c58014f0cfaaf331f6a11024135cc5dc8a561bced99", 16),
    "optimized": ("0a6b33da5a01bd571fabe43ede4a5dcce6e8a9a5e6e0d36ad8e501e21985cd01", "0a59dbb911fd4e4aaa0aac8edd7380c8d5c834f4f0f3338337850b7ee3ee0846", 19),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(root, path):
    return {"path": path, "sha256": sha(root / path)}


def load(path):
    return json.loads(Path(path).read_text())


def build(root=ROOT):
    root = Path(root)
    # Execute only the archived pure metrics function. Never import prepare.py,
    # its process launcher, or any native MATLAB/Mech module.
    vendor = root / VENDOR
    sys.path.insert(0, str(vendor))
    import pygments
    from pygments import lex
    from pygments.lexers import MatlabLexer
    from pygments.token import Comment, String
    require(Path(pygments.__file__).resolve().is_relative_to(vendor.resolve()), "Unexpected Pygments installation")
    counter = root / OLD / "audit_loc_final.py"
    counter_text = counter.read_text()
    function = next(n for n in ast.parse(counter_text).body if isinstance(n, ast.FunctionDef) and n.name == "metrics")
    namespace = {"lex": lex, "MatlabLexer": MatlabLexer, "Comment": Comment, "String": String}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(counter), "exec"), namespace)
    count = namespace["metrics"]
    old_counts_path = OLD + "/exports/20261010T192801960763Z/loc.json"
    old_counts = load(root / old_counts_path)
    require(old_counts["audit_script_sha256"] == sha(counter), "Parent source-count rule changed")
    require(old_counts["status"] == "passed", "Parent source-count audit failed")
    replay_path = root / "experiments/matlab/optimization-v1/replay_regex_admission.py"
    spec = importlib.util.spec_from_file_location("matlab_regex_historical_replay", replay_path)
    replay = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(replay)
    replay.ROOT = root
    replay.BASE = root / BASE
    execution = replay.replay()
    require(execution == load(replay_path.with_name("regex-admission-replay.json")), "Historical execution replay is stale")
    qualification = load(root / BASE / "qualification-v1/report.json")
    full = load(root / BASE / "studies/full-v1/regexredux/report.json")
    bounded_stdout = []
    for attempt in qualification["attempts"]:
        path = BASE + "/qualification-v1/cases/" + attempt["id"] + "/" + attempt["case"] + "/actual.stdout"
        require(sha(root / path) == attempt["stdout_sha256"] and (root / path).stat().st_size == attempt["stdout_bytes"], "Bounded actual stdout differs from native record")
        bounded_stdout.append(pin(root, path))
    rows = []
    for form, (old_sha, new_sha, expected_count) in IDENTITIES.items():
        parent_key = "regexredux:matlab-" + form
        identity = "matlab-case-" + form
        old_path = OLD + "/sources/regexredux_" + form + ".m"
        new_path = BASE + "/sources/regexredux_" + form + ".m"
        a, b = (root / old_path).read_bytes(), (root / new_path).read_bytes()
        require(sha(root / old_path) == old_sha and sha(root / new_path) == new_sha, "Reviewed MATLAB source bytes changed")
        old_header, old_body = a.split(b"function ", 1)
        new_header, new_body = b.split(b"function ", 1)
        require(old_body.count(b"regexpi(") == 1 and new_body.count(b"regexp(") == 1, "Unexpected count API inventory")
        require(old_body.replace(b"regexpi(", b"regexp(") == new_body, "Application change beyond the single API identifier")
        require(all(not line.strip() or line.lstrip().startswith(b"%") for line in old_header.splitlines() + new_header.splitlines()), "Noncomment header change")
        old_metric, metric = count(a.decode()), count(b.decode())
        parent = old_counts["rows"][parent_key]
        require(parent["source_sha256"] == old_sha and old_metric == {k: parent[k] for k in old_metric}, "Parent retained-rule count does not replay")
        require(metric == old_metric and metric["physical_loc"] == metric["normalized_loc"] == expected_count and metric["expansions"] == [], "Corrected retained statement count changed")
        timed = [p for p in full["attempts"] if p["id"] == identity]
        bounded = [p for p in qualification["attempts"] if p["id"] == identity]
        require(len(timed) == 3 and len(bounded) == 5 and all(p["source_sha256"] == new_sha for p in timed + bounded), "Wrong native exact-source acceptance coverage")
        rows.append({"key": "regexredux:" + identity, "parent_program": parent_key,
                     "source": pin(root, new_path), "parent_source": pin(root, old_path),
                     **metric, "application_line_ranges": [{"start": 1, "end": len(b.splitlines())}],
                     "all_application_code_included": True, "embedded_support_excluded": [],
                     "statement_inventory_unchanged": True, "body_change": "one regexpi identifier replaced by regexp",
                     "header_change": "comment text only", "count_call_line": 11 if form == "compact" else 13,
                     "literal_separator_rows": [14 if form == "compact" else 17],
                     "end_only_rows": [12, 17, 19] if form == "compact" else [15, 20, 22],
                     "native_source_acceptance": {"bounded_complete_outputs": 5, "full_complete_outputs": 3,
                         "method": "Retained successful native executions of this exact source hash; no new runtime or native AST traversal."}})
    evidence = {name: pin(root, path) for name, path in {
        "source_count_replay": str(Path(__file__).resolve().relative_to(root)),
        "parent_count_rule": OLD + "/audit_loc_final.py", "parent_count_report": old_counts_path,
        "execution_replay": "experiments/matlab/optimization-v1/replay_regex_admission.py",
        "execution_receipt": "experiments/matlab/optimization-v1/regex-admission-replay.json",
        "proposal": BASE + "/proposal-sealed-v1.json", "qualification": BASE + "/qualification-v1/report.json",
        "full_manifest": BASE + "/studies/full-v1/regexredux/manifest.json", "full": BASE + "/studies/full-v1/regexredux/report.json",
        "launcher": OLD + "/matlab-stdin.sh", "runtime_identity": BASE + "/runtime_identity.m",
        "pygments_package": VENDOR + "/pygments/__init__.py", "matlab_lexer": VENDOR + "/pygments/lexers/matlab.py",
        "pygments_tokens": VENDOR + "/pygments/token.py",
    }.items()}
    return {"schema": "matlab-regex-source-count-review.v1", "status": "reviewed-proposal-not-applied",
            "recommendation": "Ready for additive admission under the retained MATLAB statement-normalized rule after root review; no new timing is needed.",
            "metric": "statement-normalized", "policy": "application-loc-v1 / retained MATLAB physical-plus-packed-statements",
            "qualification_scope": "These two exact sources only; not a uniform logical-source or whole-language native-parser certificate.",
            "lexer": {"name": "Pygments MatlabLexer", "version": pygments.__version__, "source": VENDOR},
            "rows": rows, "evidence": evidence, "verified_bounded_actual_stdout": bounded_stdout,
            "native_processes_run": 0, "canonical_catalog_changed": False,
            "support_boundary": "All MATLAB application source counts. The unchanged generic matlab-stdin.sh launcher only routes fd0 to fd3 and remains separate runtime support.",
            "known_rule_limits": ["End-only rows still count under this retained rule.", "Matrix separators are not packed independent statements; actual matrix contents and source row layout are unchanged.", "No native AST-based logical ownership or qualified formatter measure is asserted."],
            "historical_evidence_limits": execution["archive_replay_limit"],
            "authorship": {"scope": "Archived 20261012 local correction of the retained MATLAB parent; source-writing tool and model unverified",
                           "tool": None, "model_family": None, "exact_model": None,
                           "source_written_in_current_review": False,
                           "instruction": "No exact-source tool/write evidence is retained for either corrected hash. Preserve parent origin uncertainty and do not attribute these writes to the current reviewing agent."}}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    encoded = (json.dumps(build(), indent=2, ensure_ascii=False) + "\n").encode()
    output = ROOT / OUTPUT
    if args.check:
        require(output.read_bytes() == encoded, "MATLAB source-count proposal is stale")
    else:
        output.write_bytes(encoded)
    print("MATLAB corrected-source ledger: compact 16, optimized 19; proposal only, no native execution")


if __name__ == "__main__":
    main()
