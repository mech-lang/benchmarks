"""Prepare two additive archived MATLAB regex candidates; never apply a catalog.

Offline source/output/receipt replay only. Historical native attempts keep their
chart_admission=false fields. A new intake binds their exact source-specific
count review and complete historical samples for root's separate approval.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import statistics

ROOT = Path(__file__).resolve().parents[2]
BASE = "archive/comparisons/matlab-comparison/20261012/regex-case-sensitive-v1"
PACKET = "experiments/matlab/optimization-v1"
LEDGER = PACKET + "/regex-source-counts.json"
LEDGER_TOOL = PACKET + "/replay_regex_source_counts.py"
RESULTS = PACKET + "/admission-v1/results.json"
SOURCE_REVISION = "4b3205d97c71017eb327c5a3dbeecd1a64d362dd"
ENGINE_SHA = "ed2d96026421bb1f5d0deed46b1cfefa6011e8f5e7eef678675abe64ae0df764"
LAUNCHER_SHA = "a517cc4d3838fc6a44c8075fa044701a2f87aa8d9169cd19d67718ae6effb084"
LAUNCHER_PATH = "archive/comparisons/matlab-comparison/20261010/matlab-stdin.sh"
TIMING_BOUNDARY = ("Historical fresh-process wall time includes stream routing, licensing/runtime initialization, "
                   "first-use JIT, complete input, all nine independent counts, five ordered substitutions, "
                   "complete output and process-group shutdown. Setup and validation are excluded.")
COUNTS = {"compact": 16, "optimized": 19}
AUTHOR_CONTEXT = {"tool": None, "exact_model": None, "model_family": None,
                  "scope": "Archived 20261012 local correction; source-writing tool and model unverified. Source not written by the current reviewing agent."}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def load(path):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, "Duplicate JSON key: " + key)
            out[key] = value
        return out
    def invalid(value):
        raise ValueError("Nonfinite JSON constant: " + value)
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs, parse_constant=invalid)


def pin(root, path):
    return {"path": path, "sha256": sha(root / path)}


def validate_ledger(value):
    require(value.get("schema") == "matlab-regex-source-count-review.v1" and
            value.get("status") == "reviewed-proposal-not-applied" and
            value.get("metric") == "statement-normalized" and
            value.get("native_processes_run") == 0, "Wrong source-count review scope")
    rows = value.get("rows", [])
    require(len(rows) == 2 and {r.get("key") for r in rows} == {"regexredux:matlab-case-" + form for form in COUNTS}, "Wrong corrected source inventory")
    for row in rows:
        form = row["key"].removeprefix("regexredux:matlab-case-")
        require(row.get("parent_program") == "regexredux:matlab-" + form and
                type(row.get("normalized_loc")) is int and
                row["normalized_loc"] == row.get("physical_loc") == COUNTS[form] and
                row.get("expansions") == [] and row.get("statement_inventory_unchanged") is True and
                row.get("all_application_code_included") is True and row.get("embedded_support_excluded") == [],
                "Unreviewed MATLAB count or source boundary")


def source_ledger(root):
    spec = importlib.util.spec_from_file_location("matlab_regex_source_count_replay", root / LEDGER_TOOL)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    actual = module.build(root)
    require(actual == load(root / LEDGER), "Stale or changed exact-source count ledger")
    validate_ledger(actual)
    return actual


def reconcile(root=ROOT):
    root = Path(root).resolve()
    ledger = source_ledger(root)
    require(ledger["evidence"]["launcher"] == {"path": LAUNCHER_PATH, "sha256": LAUNCHER_SHA}, "Unreviewed MATLAB stream launcher")
    full = load(root / BASE / "studies/full-v1/regexredux/report.json")
    manifest = load(root / BASE / "studies/full-v1/regexredux/manifest.json")
    qualification = load(root / BASE / "qualification-v1/report.json")
    proposal = load(root / BASE / "proposal-sealed-v1.json")
    require(full.get("chart_admission") is False and manifest.get("chart_admission") is False and
            qualification.get("chart_admission") is False and proposal.get("chart_admission") is False,
            "Historical admission fields must remain false")
    expected_order = [(order["round"], identity) for order in manifest["orders"] for identity in order["profiles"]]
    require([(a["round"], a["id"]) for a in full["attempts"]] == expected_order, "Historical rotated round order changed")
    manifest_profiles = {p["id"]: p for p in manifest["profiles"]}
    artifacts = {r["path"]: r for r in ledger["evidence"].values()}
    artifacts.update({r["path"]: r for r in ledger["verified_bounded_actual_stdout"]})
    for attempt in qualification["attempts"] + full["attempts"]:
        for field in ["result_path", "supervisor_result_path"]:
            marker = "/matlab-comparison/20261012/regex-case-sensitive-v1/"
            parts = attempt[field].split(marker)
            require(len(parts) == 2 and ".." not in Path(parts[1]).parts, "Unrecognized archived attempt path")
            path = BASE + "/" + parts[1]
            artifacts[path] = pin(root, path)
    programs = []
    for count in ledger["rows"]:
        identity = count["key"].split(":", 1)[1]
        profile = full["profiles"][identity]
        prepared = manifest_profiles[identity]
        require(profile["source_sha256"] == count["source"]["sha256"] and
                profile["source_sha256"] == prepared["source_sha256"] and
                profile["command"] == prepared["command"] and
                profile["runtime_environment"] == prepared["runtime_environment"], "Manifest/full profile identity changed")
        require(profile["support"] == prepared["support"] and
                prepared["support"].get("/Users/cim310/.codex/worktrees/clbg-nbody-v04/mech/benchmarks/clbg/matlab-comparison/20261010/matlab-stdin.sh") == LAUNCHER_SHA,
                "Recorded MATLAB support boundary changed")
        require(prepared["support"]["/Applications/MATLAB_R2026b.app/bin/maca64/MATLAB"] == ENGINE_SHA,
                "Different recorded MATLAB engine")
        attempts = [a for a in full["attempts"] if a["id"] == identity]
        require(len(attempts) == 3 and {a["round"] for a in attempts} == {1, 2, 3}, "Missing historical sample")
        samples = [a["seconds"] for a in attempts]
        require(all(type(s) in (int, float) and math.isfinite(s) and s > 0 for s in samples), "Invalid elapsed sample")
        require(samples == profile["samples_seconds"] and statistics.median(samples) == profile["median_seconds"] and
                statistics.stdev(samples) == profile["sample_stdev_seconds"], "Historical aggregation changed")
        for attempt in attempts:
            require(attempt.get("chart_admission") is False and attempt.get("full_performance_run") is True and
                    attempt.get("full_workload") is True and attempt.get("workload_n") == 5_000_000,
                    "Wrong full/diagnostic attempt")
            for field in ["source_sha256", "command", "runtime_environment", "cwd"]:
                require(attempt[field] == profile[field], "Historical execution identity changed: " + field)
        programs.append({"key": count["key"], "id": identity, "original_program_key": count["parent_program"],
                         "source": count["source"], "parent_source": count["parent_source"],
                         "loc": count["normalized_loc"], "physical_loc": count["physical_loc"],
                         "samples_seconds": samples, "median_seconds": statistics.median(samples),
                         "sample_sd_seconds": statistics.stdev(samples), "command": profile["command"],
                         "cwd": profile["cwd"], "runtime_environment": profile["runtime_environment"],
                         "binary_sha256": profile["binary_sha256"], "sample_execution_metadata": attempts,
                         "full_output_validation": profile["sample_validation"]})
    identity = next(a for a in qualification["attempts"] if a["id"] == "matlab-runtime-identity")
    require("CLBG_MATLAB_VERSION=26.2.0.3386108 (R2026b)" in identity["stderr"] and
            "CLBG_MATLAB_WORKERS=8" in identity["stderr"], "Runtime identity diagnostic differs")
    return {"schema": "matlab-regex-admission-results.v1", "status": "RECONCILED",
            "source_count_review": pin(root, LEDGER), "intake_controller": pin(root, "tools/qualification/import_matlab_regex.py"),
            "historical_execution_replay": ledger["evidence"]["execution_receipt"],
            "programs": programs, "recorded_at": full["finished_at"], "new_observations": 6,
            "historical_reports_unchanged": True, "native_processes_run_by_intake": 0,
            "timing_boundary": TIMING_BOUNDARY, "full_workload_n": 5_000_000,
            "expected_output": manifest["full_output_reference"], "artifacts": list(artifacts.values()),
            "toolchains": {"matlab": {"version": "MATLAB 26.2.0.3386108 (R2026b); maca64; maxNumCompThreads=8", "sha256": ENGINE_SHA}},
            "runtime_pin_scope": "Historical recorded pins and native identity/ownership attestations; old external executables are not freshly rehashed or rerun.",
            "author_context": copy.deepcopy(AUTHOR_CONTEXT),
            "limits": ledger["known_rule_limits"] + [ledger["historical_evidence_limits"]]}


def authorship_record(parent, row, evidence, data):
    value = copy.deepcopy(parent["authorship"])
    value.update(kind="local-origin-unverified", label="Local correction · origin unverified", source_sha256=row["files"],
                 parent_programs=[parent["key"]], parent_sources=[{"program_key": parent["key"], "relationship": "local predecessor", **ref}
                    for ref in parent["authorship"].get("retained_sources", [])],
                 retained_sources=[{"source_sha256": h, "url": "https://github.com/mech-lang/benchmarks/blob/" + SOURCE_REVISION + "/" + data["files"][h]["archive_path"]} for h in row["files"]],
                 ai={"tool": None, "models": [], "exact_model": None, "model_family": None,
                     "status": "unverified", "matched_source_files": [], "total_source_files": len(row["files"]), "evidence": []},
                 evidence=[LEDGER, RESULTS, PACKET + "/regex-admission-review.md"],
                 retained_source_note="Exact archived local correction; retained evidence identifies neither its source-writing tool nor its model. Parent origin remains unverified.")
    return value


def bound_authorship(data, profile, root=ROOT):
    """Optional narrow audit hook; does not infer the historical writing model."""
    root = Path(root)
    detail = profile.get("source_provenance_record", {})
    results = load(root / RESULTS)
    require(results.get("schema") == "matlab-regex-admission-results.v1" and results.get("status") == "RECONCILED" and
            results.get("author_context") == AUTHOR_CONTEXT and results["source_count_review"] == pin(root, LEDGER),
            "MATLAB archived authorship intake binding differs")
    matches = [r for r in results["programs"] if r["key"] == profile.get("key")]
    require(len(matches) == 1, "Unrecognized archived MATLAB candidate")
    r = matches[0]
    parent = {**data.get("program_inventory", {}), **data["programs"]}[r["original_program_key"]]
    require(detail.get("kind") == "archived-matlab-case-correction" and detail.get("author_context") == AUTHOR_CONTEXT and
            detail.get("original_program_key") == parent["key"] and detail.get("source_sha256") == r["source"]["sha256"] and
            detail.get("admission") == pin(root, RESULTS) and profile["files"] == [r["source"]["sha256"]] + parent["files"][1:] and
            sha(root / r["source"]["path"]) == r["source"]["sha256"] and
            hashlib.sha256(data["files"][r["source"]["sha256"]]["code"].encode()).hexdigest() == r["source"]["sha256"],
            "MATLAB archived authorship source identity differs")
    return authorship_record(parent, profile, {}, data)


def append_catalog(before, root=ROOT, results=None):
    """Pure reviewable candidate extension. This function writes no files."""
    root = Path(root).resolve()
    expected = reconcile(root)
    results = load(root / RESULTS) if results is None else results
    require(results == expected, "Intake results do not reproduce from archived evidence")
    data = copy.deepcopy(before)
    require("matlab_regex_case_audit" not in data, "MATLAB regex intake already applied")
    catalog = {**before.get("program_inventory", {}), **before["programs"]}
    bench = next(b for b in data["benchmarks"] if b["key"] == "regexredux")
    group = next(g for g in bench["groups"] if g["language"] == "matlab")
    evidence = {"source_counts": results["source_count_review"], "execution": results["historical_execution_replay"],
                "results": {"path": RESULTS, "sha256": hashlib.sha256(encoded(results)).hexdigest()},
                "controller": results["intake_controller"]}
    appended = []
    for r in results["programs"]:
        parent = catalog[r["original_program_key"]]
        require(parent["language"] == "matlab" and parent["benchmark"] == "regexredux" and
                parent["files"][0] == r["parent_source"]["sha256"] and parent["loc"] == r["loc"], "Wrong immutable MATLAB parent")
        require(parent["files"] == [r["parent_source"]["sha256"], LAUNCHER_SHA] and
                hashlib.sha256(data["files"][LAUNCHER_SHA]["code"].encode()).hexdigest() == LAUNCHER_SHA,
                "Unreviewed MATLAB support boundary")
        require(r["key"] not in catalog and r["source"]["sha256"] not in data["files"], "Candidate identity already exists")
        require(r["loc"] >= bench["baseline_loc"] and r["median_seconds"] >= bench["baseline_seconds"], "New global baseline requires separate normalization review")
        source = r["source"]
        data["files"][source["sha256"]] = {"name": Path(source["path"]).name, "path": source["path"], "archive_path": source["path"],
            "sha256": source["sha256"], "code": (root / source["path"]).read_text()}
        row = copy.deepcopy(parent)
        for field in ["authorship", "source_metrics", "publication_record", "source_alias_of", "aliased_sample_source", "timing_measurement", "timing_correction"]:
            row.pop(field, None)
        row.update(key=r["key"], id=r["id"], receipt_key=r["id"], original_program_key=parent["key"],
            loc=r["loc"], physical_loc=r["physical_loc"], loc_metric="statement-normalized", loc_expansions=[],
            loc_report=LEDGER, files=[source["sha256"]] + parent["files"][1:],
            seconds=r["median_seconds"], samples=r["samples_seconds"], timing_sd=r["sample_sd_seconds"],
            x=r["loc"] / bench["baseline_loc"], y=r["median_seconds"] / bench["baseline_seconds"],
            report=RESULTS, report_sha256=evidence["results"]["sha256"], source_report=LEDGER,
            command=r["command"], runtime_arguments=r["command"], cwd=r["cwd"], runtime_environment=r["runtime_environment"],
            binary_sha256=r["binary_sha256"], runtime_sha256=ENGINE_SHA, execution_mode="jit", native_observations=3,
            sample_execution_metadata=r["sample_execution_metadata"], timing_alias_of=None,
            formatted_loc=None, formatted_x=None, formatted_loc_status="pending", formatted_loc_complete=False, formatted_loc_evidence={},
            eligible_for_chart=True, retained_source_revision=SOURCE_REVISION, local_adaptation=True,
            source_provenance="Archived 20261012 local MATLAB correction: case-sensitive regexp replaces regexpi. All other application-body bytes and the original 20261010 parent records are preserved; source-writing tool and model unverified.",
            source_provenance_record={"kind": "archived-matlab-case-correction", "original_program_key": parent["key"],
                "source_sha256": source["sha256"], "admission": evidence["results"], "author_context": results["author_context"]},
            timing_boundary=TIMING_BOUNDARY, timing_summary="Three retained complete-process 20261012-cohort samples, independently reconciled for this exact corrected source. No old sample is transplanted or retimed.",
            algorithm={"strict": True, "status": "required-work-reviewed", "native_benchmark_kernel": False,
                "reason": "Nine independent case-sensitive non-overlapping regexp counts and five original ordered regexprep substitutions. Entire input, cleaned length and final length are validated; no native workload executor.",
                "full_work": {"input_bytes": 50833411, "count_patterns": 9, "ordered_substitutions": 5},
                "requirements_url": "https://benchmarksgame-team.pages.debian.net/benchmarksgame/description/regexredux.html"},
            full_output_validation=r["full_output_validation"],
            chart_admission={"historical_reports_unchanged": True, "historical_chart_admission": False, "separate_additive_intake": True, **evidence},
            source_accounting={"policy": "application-loc-v1", "application_loc": r["loc"], "physical_loc": r["physical_loc"],
                "previous_loc": r["loc"], "previous_physical_loc": r["physical_loc"], "support_loc": parent.get("source_accounting", {}).get("support_loc"),
                "removed_loc": 0, "lexical_correction": 0,
                "evidence": LEDGER, "review_sha256": evidence["source_counts"]["sha256"],
                "qualification": "Exact-source replay of retained MATLAB statement rule; no native AST/logical-LOC certificate.",
                "files": copy.deepcopy(parent.get("source_accounting", {}).get("files", []))})
        if "file_roles" in row:
            row["file_roles"].pop(parent["files"][0], None)
        row["measured_backend"] = {"key": "matlab", "execution": "jit", "label": "MATLAB (standard JIT)", "verified": True,
            "evidence": {"verified": True, "report": RESULTS, "report_sha256": evidence["results"]["sha256"],
                "command": r["command"], "source_sha256": row["files"],
                "runtime_receipt": {"verified": True, "report": RESULTS, "report_sha256": evidence["results"]["sha256"],
                    "field": "/toolchains/matlab/version", "value": results["toolchains"]["matlab"]["version"], "value_encoding": "literal-saved-string"}}}
        row["authorship"] = authorship_record(parent, row, evidence, data)
        data["programs"][r["key"]] = row
        data.setdefault("program_inventory", {})[r["key"]] = copy.deepcopy(row)
        appended.append(r["key"])
    candidates = [data["programs"][key] for key in group["programs"] + appended if data["programs"][key].get("eligible_for_chart") is not False]
    group.update(programs=group["programs"] + appended,
                 fast=min(candidates, key=lambda p: (p["seconds"], p["loc"], p["key"]))["key"],
                 small=min(candidates, key=lambda p: (p["loc"], p["seconds"], p["key"]))["key"])
    for summary in data.get("reference_summary", []):
        if summary["lang"] != "matlab":
            continue
        groups = [g for b in data["benchmarks"] for g in b["groups"] if g["language"] == "matlab"]
        for kind in ["fast", "small"]:
            selected = [data["programs"][g[kind]] for g in groups if g.get(kind)]
            summary[kind] = {"x": statistics.geometric_mean(p["x"] for p in selected), "y": statistics.geometric_mean(p["y"] for p in selected)}
    for ref in [*results["artifacts"], *evidence.values(), *(r["source"] for r in results["programs"])]:
        data.setdefault("archive_paths", {})[ref["path"]] = ref["path"]
    data["matlab_regex_case_audit"] = {"schema": "matlab-regex-catalog-extension.v1", "appended_programs": appended,
        "evidence": evidence, "measured_at": results["recorded_at"], "observations_admitted": 6,
        "source_files_added": 2, "old_profiles_unchanged": True, "old_baselines_unchanged": True}
    for pool in ["programs", "program_inventory", "files", "archive_paths"]:
        require(all(data[pool][key] == value for key, value in before.get(pool, {}).items()), "Historical " + pool + " changed")
    return data


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--prepare", action="store_true", required=True, help="Write a preview only; canonical data is never written")
    args = parser.parse_args()
    before_path = ROOT / "data/benchmarks.json"
    before = before_path.read_bytes()
    results = reconcile()
    output = ROOT / PACKET / "admission-v1"
    output.mkdir(parents=True, exist_ok=True)
    (ROOT / RESULTS).write_bytes(encoded(results))
    preview = output / "prepared.json"
    preview.write_bytes(encoded(append_catalog(json.loads(before), results=results)))
    require(before_path.read_bytes() == before, "Canonical data changed during preview preparation")
    print(json.dumps({"canonical_changed": False, "before_sha256": hashlib.sha256(before).hexdigest(),
                      "prepared_sha256": sha(preview), "results_sha256": sha(ROOT / RESULTS), "source_counts": pin(ROOT, LEDGER)}))


if __name__ == "__main__":
    main()
